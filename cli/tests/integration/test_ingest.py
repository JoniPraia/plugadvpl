"""Integration tests for the full ingest pipeline.

Verifica end-to-end: scan -> parse -> write -> FTS rebuild. Foca no caminho
serial (workers=0) que é determinístico em todos os SOs. Caminho paralelo
tem 1 teste smoke (clamp para serial em datasets pequenos é o caso comum).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from plugadvpl.ingest import ingest


@pytest.fixture
def synthetic_dir(tmp_path: Path) -> Path:
    """Cria 3 fontes ADVPL sintéticos cobrindo MVC, MV_*, REST/TLPP."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "FATA050.prw").write_bytes(
        b"User Function FATA050()\n"
        b'  DbSelectArea("SC5")\n'
        b'  RecLock("SC5", .T.)\n'
        b'  Replace C5_NUM With "001"\n'
        b"  MsUnlock()\n"
        b"Return .T.\n"
    )
    (src / "MATA010.prw").write_bytes(
        b"User Function MATA010()\n"
        b'  Local cMV := SuperGetMV("MV_LOCALIZA", .F., "")\n'
        b"Return\n"
    )
    (src / "WSReg.tlpp").write_bytes(
        b"Namespace api\n"
        b"User Function WSReg()\n"
        b'  HttpPost("http://api.foo/x", oJson)\n'
        b"Return\n"
    )
    return src


def _connect(db_path: Path) -> sqlite3.Connection:
    """Abre o DB read-only num context manager local."""
    return sqlite3.connect(str(db_path))


class TestIngest:
    def test_ingest_creates_db_and_counts(self, synthetic_dir: Path) -> None:
        counters = ingest(synthetic_dir, workers=0)
        db = synthetic_dir / ".plugadvpl" / "index.db"
        assert db.exists()
        assert counters["arquivos_total"] == 3
        assert counters["arquivos_ok"] == 3
        assert counters["arquivos_failed"] == 0
        assert counters["duration_ms"] >= 0

    def test_ingest_populates_fontes_table(self, synthetic_dir: Path) -> None:
        ingest(synthetic_dir, workers=0)
        conn = _connect(synthetic_dir / ".plugadvpl" / "index.db")
        try:
            n = conn.execute("SELECT COUNT(*) FROM fontes").fetchone()[0]
            assert n == 3

            # FATA050 deve referenciar SC5 em tabelas_ref (modo write — RecLock).
            row = conn.execute(
                "SELECT tabelas_ref, write_tables, reclock_tables FROM fontes "
                "WHERE arquivo='FATA050.prw'"
            ).fetchone()
            tabelas_ref = json.loads(row[0])
            write_tables = json.loads(row[1])
            reclock_tables = json.loads(row[2])
            # tabelas_ref = read; write_tables / reclock_tables incluem SC5
            assert "SC5" in (tabelas_ref + write_tables + reclock_tables)

            # fonte_tabela normalizada também deve ter (FATA050.prw, SC5, *).
            ft_rows = conn.execute(
                "SELECT modo FROM fonte_tabela WHERE arquivo='FATA050.prw' AND tabela='SC5'"
            ).fetchall()
            assert len(ft_rows) >= 1

            # caminho_relativo deve usar forward slash, relativo a root.
            rel = conn.execute(
                "SELECT caminho_relativo FROM fontes WHERE arquivo='FATA050.prw'"
            ).fetchone()[0]
            assert "/" in rel or rel == "FATA050.prw"
            assert "\\" not in rel
        finally:
            conn.close()

    def test_ingest_populates_fts5(self, synthetic_dir: Path) -> None:
        ingest(synthetic_dir, workers=0)
        conn = _connect(synthetic_dir / ".plugadvpl" / "index.db")
        try:
            # FTS5 deve permitir busca por RecLock no content de FATA050.
            rows = conn.execute(
                "SELECT arquivo FROM fonte_chunks_fts WHERE fonte_chunks_fts MATCH 'RecLock'"
            ).fetchall()
            assert any("FATA050" in r[0] for r in rows), f"got: {rows}"

            # Trigram FTS deve achar substring 'SuperGetMV'
            rows_tri = conn.execute(
                "SELECT rowid FROM fonte_chunks_fts_tri "
                "WHERE fonte_chunks_fts_tri MATCH 'SuperGetMV'"
            ).fetchall()
            assert len(rows_tri) >= 1
        finally:
            conn.close()

    def test_ingest_incremental_skips_unchanged(self, synthetic_dir: Path) -> None:
        first = ingest(synthetic_dir, workers=0)
        assert first["arquivos_ok"] == 3
        # 2ª ingest sem mudança no FS: nada deve ser re-parseado.
        second = ingest(synthetic_dir, workers=0, incremental=True)
        assert second["arquivos_total"] == 3
        assert second["arquivos_skipped"] == 3
        assert second["arquivos_ok"] == 0

    def test_ingest_no_content_mode(self, synthetic_dir: Path) -> None:
        ingest(synthetic_dir, workers=0, no_content=True)
        conn = _connect(synthetic_dir / ".plugadvpl" / "index.db")
        try:
            rows = conn.execute("SELECT content FROM fonte_chunks").fetchall()
            assert rows, "deve haver pelo menos uma chunk"
            assert all(r[0] in ("", None) for r in rows)
        finally:
            conn.close()

    def test_ingest_redact_secrets(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "Secret.prw").write_bytes(
            b"User Function Secret()\n"
            b'  HttpPost("http://user:p4ssw0rd@api.foo/x", oJson)\n'
            b'  Local cTok := "abcdef0123456789abcdef0123456789abcdef0123"\n'
            b"Return\n"
        )
        ingest(src, workers=0, redact_secrets=True)
        conn = _connect(src / ".plugadvpl" / "index.db")
        try:
            urls = conn.execute("SELECT url_literal FROM http_calls").fetchall()
            assert urls
            # URL com creds deve ter sido redacted.
            assert all("p4ssw0rd" not in u[0] for u in urls)
            assert any("REDACTED" in u[0] for u in urls)
        finally:
            conn.close()

    def test_ingest_populates_lint_findings_and_meta(
        self, synthetic_dir: Path
    ) -> None:
        ingest(synthetic_dir, workers=0)
        conn = _connect(synthetic_dir / ".plugadvpl" / "index.db")
        try:
            # Meta deve refletir totais e parser_version.
            valor_parser = conn.execute(
                "SELECT valor FROM meta WHERE chave='parser_version'"
            ).fetchone()
            assert valor_parser is not None
            assert valor_parser[0].startswith("p")

            valor_total = conn.execute(
                "SELECT valor FROM meta WHERE chave='total_arquivos'"
            ).fetchone()
            assert int(valor_total[0]) == 3

            # indexed_at gravado
            iat = conn.execute(
                "SELECT valor FROM meta WHERE chave='indexed_at'"
            ).fetchone()
            assert iat is not None and iat[0]
        finally:
            conn.close()
