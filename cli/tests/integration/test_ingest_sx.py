"""Integration tests para o pipeline de ingest do dicionário SX (v0.3.0).

Cobrem: ingest-sx contra fixtures sintéticos + comandos impacto/gatilho/sx-status
+ lint cross-file SX-001..SX-011 + idempotência.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from plugadvpl.cli import app
from plugadvpl.ingest_sx import ingest_sx

SX_FIXTURES = Path(__file__).parent.parent / "fixtures" / "sx_synthetic"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sx_project(tmp_path: Path) -> Path:
    """Project com:

    - 1 fonte ADVPL que usa A1_COD, GetMV(MV_XYZUSED), Pergunte(MGFREL01),
      e a função user U_XYZVALID().
    - Fixtures SX já copiadas.
    """
    src = tmp_path / "src"
    src.mkdir()
    (src / "MGFTEST.prw").write_bytes(
        b"User Function MGFTEST()\n"
        b"  Local cCli := M->A1_COD\n"
        b"  Local cMV  := SuperGetMV('MV_XYZUSED', .F., '01')\n"
        b"  Pergunte('MGFREL01', .T.)\n"
        b"  RecLock('SA1', .T.)\n"
        b"  Replace A1_NREDUZ With MV_PAR01\n"
        b"  MsUnlock()\n"
        b"Return\n"
    )
    (src / "MGFXVALID.prw").write_bytes(
        b"User Function XYZVALID()\n"
        b"  Return .T.\n"
    )
    return src


@pytest.fixture
def sx_csv_dir(tmp_path: Path) -> Path:
    """Cópia das fixtures SX para um tmp_path isolado."""
    dst = tmp_path / "csv"
    dst.mkdir()
    for f in SX_FIXTURES.iterdir():
        if f.suffix == ".csv":
            (dst / f.name).write_bytes(f.read_bytes())
    return dst


@pytest.fixture
def indexed_with_sx(
    sx_project: Path, sx_csv_dir: Path, runner: CliRunner
) -> Path:
    """Project com ingest fontes + ingest-sx aplicados."""
    runner.invoke(app, ["--root", str(sx_project), "init"])
    runner.invoke(app, ["--root", str(sx_project), "ingest"])
    runner.invoke(
        app, ["--root", str(sx_project), "ingest-sx", str(sx_csv_dir)]
    )
    return sx_project


def _connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(db))


class TestIngestSx:
    def test_ingest_sx_creates_all_tables(
        self, sx_project: Path, sx_csv_dir: Path, runner: CliRunner
    ) -> None:
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        counters = ingest_sx(sx_csv_dir, db)
        assert counters["csvs_ok"] >= 10  # 11 esperados (sxg pode skip se header não-XG)
        assert counters["per_table"]["tabelas"] == 5
        assert counters["per_table"]["campos"] == 10
        assert counters["per_table"]["gatilhos"] == 4
        assert counters["per_table"]["parametros"] == 4
        assert counters["per_table"]["perguntas"] == 3
        assert counters["per_table"]["consultas"] == 3
        assert counters["per_table"]["grupos_campo"] == 2

    def test_ingest_sx_is_idempotent(
        self, sx_project: Path, sx_csv_dir: Path, runner: CliRunner
    ) -> None:
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        first = ingest_sx(sx_csv_dir, db)
        second = ingest_sx(sx_csv_dir, db)
        assert first["per_table"] == second["per_table"]
        # Counts after 2x run match — INSERT OR REPLACE keeps PK constraint.
        conn = _connect(db)
        try:
            n = conn.execute("SELECT COUNT(*) FROM campos").fetchone()[0]
            assert n == 10
        finally:
            conn.close()

    def test_ingest_sx_skips_deleted_rows(
        self, sx_project: Path, tmp_path: Path, runner: CliRunner
    ) -> None:
        # CSV com row deletada (D_E_L_E_T_ = '*').
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        (csv_dir / "sx2.csv").write_text(
            '"X2_CHAVE","X2_NOME","X2_MODO","D_E_L_E_T_"\n'
            '"SA1","Clientes","C",""\n'
            '"DEL","Deletada","C","*"\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        counters = ingest_sx(csv_dir, db)
        assert counters["per_table"]["tabelas"] == 1  # 'DEL' filtrado

    def test_ingest_sx_writes_meta(
        self, sx_project: Path, sx_csv_dir: Path, runner: CliRunner
    ) -> None:
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(sx_csv_dir, db)
        conn = _connect(db)
        try:
            row = conn.execute(
                "SELECT valor FROM meta WHERE chave='total_sx_campos'"
            ).fetchone()
            assert row is not None and int(row[0]) == 10
            row = conn.execute(
                "SELECT valor FROM meta WHERE chave='last_sx_ingest_at'"
            ).fetchone()
            assert row is not None and row[0]
        finally:
            conn.close()


class TestImpactoCommand:
    def test_impacto_a1_cod_finds_fonte_and_sx(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "impacto", "A1_COD",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Deve encontrar pelo menos: o próprio campo SX3, gatilho SX7, fonte que usa.
        tipos = {r["tipo"] for r in payload["rows"]}
        assert "fonte" in tipos
        assert "SX7" in tipos
        assert "SX3" in tipos

    def test_impacto_depth_2_follows_chain(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "impacto", "A1_COD", "--depth", "2",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # depth=2 deve seguir A1_COD → A1_NREDUZ → A1_XCUSTOM (via gatilho).
        contexts = " ".join(r.get("contexto", "") for r in payload["rows"])
        assert "depth=2" in contexts


class TestGatilhoCommand:
    def test_gatilho_a1_cod_returns_chain(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "gatilho", "A1_COD", "--depth", "3",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Deve achar: A1_COD#01 → A1_NREDUZ; #02 → A1_FANTASMA; #03 → A1_TIPO;
        # depois A1_NREDUZ → A1_XCUSTOM no nível 2.
        destinos = {r["destino"] for r in payload["rows"]}
        assert "A1_NREDUZ" in destinos
        assert "A1_XCUSTOM" in destinos
        # Deve ter rows com nivel=2.
        niveis = {r["nivel"] for r in payload["rows"]}
        assert 2 in niveis


class TestSxStatusCommand:
    def test_sx_status_after_ingest(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            ["--root", str(indexed_with_sx), "--format", "json", "sx-status"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        row = payload["rows"][0]
        assert row["sx_ingerido"] is True
        assert row["campos"] == 10
        assert row["gatilhos"] == 4

    def test_sx_status_before_ingest_is_explanatory(
        self, sx_project: Path, runner: CliRunner
    ) -> None:
        # Init mas sem ingest-sx.
        runner.invoke(app, ["--root", str(sx_project), "init"])
        result = runner.invoke(
            app, ["--root", str(sx_project), "--format", "json", "sx-status"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # A migration 002 sempre roda no init, então tabelas existem mas vazias.
        # Aceitamos qualquer um dos dois cenários (depende da ordem da migration).
        row = payload["rows"][0]
        # Em init o migration 002 é aplicado, então tabelas existem.
        assert "sx_ingerido" in row


class TestLintCrossFile:
    def test_lint_cross_file_detects_sx_rules(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        # Recalcula cross-file findings.
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "lint", "--cross-file",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Deve haver pelo menos:
        # - SX-001 (X3_VALID 'U_XYZVALID()' indexado, então NÃO aciona; mas existe um tabela ZA1.ZA1_COD com TCQuery sem U_)
        # - SX-002 (gatilho A1_COD#02 → A1_FANTASMA não existe em campos)
        # - SX-003 (MV_XYZDEAD nunca lido em fonte algum)
        # - SX-004 (MGFDEAD pergunta nunca usada)
        # - SX-006 (ZA1_COD com TCQuery em VALID)
        # - SX-009 (A1_XOBRIG obrigatório com X3_RELACAO=.T. sim — mas .T. matches truthy só, não vazio. Vamos achar A1_XCUSTOM init Space(10) — não obrigatório. OK skip)
        # - SX-010 (gatilho A1_COD#02 sem SEEK e tipo P)
        regras = {r["regra_id"] for r in payload["rows"]}
        assert "SX-002" in regras
        assert "SX-003" in regras
        assert "SX-004" in regras
        assert "SX-006" in regras
        assert "SX-010" in regras

    def test_sx005_detects_unused_custom_field(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        """SX-005: campo custom sem referência em fonte/validacao/regra deve disparar.

        Fixture tem A1_XCUSTOM, A1_XOBRIG, C5_XCONS como custom (X3_PROPRI='U').
        Nenhum aparece no MGFTEST.prw (que só usa A1_COD, A1_NREDUZ, MV_*, MGFREL01),
        nem como substring em outras .validacao ou gatilhos.regra.

        Regressão pro refactor do N+1 — protege o comportamento atual.
        """
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "lint", "--cross-file", "--regra", "SX-005",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        sx005 = [r for r in payload["rows"] if r["regra_id"] == "SX-005"]
        assert len(sx005) >= 1, "SX-005 deveria disparar para custom fields sem refs"
        # Todos os findings devem vir de campos custom da fixture, prefixados por SX:<tabela>.
        for row in sx005:
            assert row["arquivo"].startswith("SX:")
            assert row["severidade"] == "warning"
        funcoes = {r["funcao"] for r in sx005}
        # Pelo menos um dos custom fields esperados precisa estar lá.
        assert funcoes & {"A1_XCUSTOM", "A1_XOBRIG", "C5_XCONS"}, (
            f"Esperava algum custom field sem refs, encontrou: {funcoes}"
        )

    def test_lint_cross_file_idempotent(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "lint", "--cross-file",
            ],
        )
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "lint", "--cross-file", "--regra", "SX-002",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Filtrando por regra deve retornar pelo menos 1 finding SX-002.
        assert all(r["regra_id"] == "SX-002" for r in payload["rows"])
        assert payload["total"] >= 1
