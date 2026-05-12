"""Testes de cli/plugadvpl/db.py."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from plugadvpl.db import (
    SCHEMA_VERSION,
    _is_network_share,
    apply_migrations,
    close_db,
    get_meta,
    init_meta,
    open_db,
    seed_lookups,
    set_meta,
)


class TestIsNetworkShare:
    def test_local_drive_windows(self) -> None:
        assert _is_network_share(Path("C:/Users/foo")) is False
        assert _is_network_share(Path("C:/Users/user/proj")) is False

    def test_unc_path_windows(self) -> None:
        assert _is_network_share(Path(r"\\server\share\folder")) is True
        assert _is_network_share(Path("//server/share/folder")) is True

    def test_local_unix(self) -> None:
        assert _is_network_share(Path("/home/user/project")) is False
        assert _is_network_share(Path("/var/tmp")) is False


class TestOpenDb:
    def test_open_db_creates_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        assert db_path.exists()
        conn.close()

    def test_open_db_applies_pragmas(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert conn.execute("PRAGMA synchronous").fetchone()[0] == 1  # NORMAL
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            assert conn.execute("PRAGMA temp_store").fetchone()[0] == 2   # MEMORY
            assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        finally:
            conn.close()

    def test_open_db_page_size_8192_on_new_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            assert conn.execute("PRAGMA page_size").fetchone()[0] == 8192
        finally:
            conn.close()

    def test_open_db_uses_delete_journal_on_network_share(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Forçar detecção como network share
        from plugadvpl import db as db_module
        monkeypatch.setattr(db_module, "_is_network_share", lambda _: True)

        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode in ("delete", "persist")
        finally:
            conn.close()


class TestApplyMigrations:
    def test_apply_migrations_creates_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            expected_core = {
                "fontes", "fonte_chunks", "chamadas_funcao", "parametros_uso",
                "perguntas_uso", "operacoes_escrita", "sql_embedado", "funcao_docs",
                "rest_endpoints", "http_calls", "env_openers", "log_calls", "defines",
                "lint_findings", "fonte_tabela",
                "funcoes_nativas", "funcoes_restritas", "lint_rules", "sql_macros",
                "modulos_erp", "pontos_entrada_padrao",
                "meta", "ingest_progress",
            }
            missing = expected_core - tables
            assert not missing, f"Tabelas faltando: {missing}"
        finally:
            conn.close()

    def test_apply_migrations_creates_fts5(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            # FTS5 aparece em sqlite_master como type='table' com sql que contém 'fts5'
            fts = list(conn.execute(
                "SELECT name FROM sqlite_master WHERE sql LIKE '%fts5%' AND type='table'"
            ))
            names = {r[0] for r in fts}
            assert "fonte_chunks_fts" in names
            assert "fonte_chunks_fts_tri" in names
        finally:
            conn.close()

    def test_apply_migrations_is_idempotent(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            apply_migrations(conn)  # 2a vez nao pode dar erro
            count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            # Sabemos que há exatamente 23 tabelas de dados; FTS5 cria shadow tables
            # (>= permite essas extras).
            assert count >= 23
        finally:
            conn.close()

    def test_apply_migrations_skips_already_applied(self, tmp_path: Path) -> None:
        """2ª chamada não deve reexecutar SQL (registrado em _migrations)."""
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            applied_first = list(conn.execute("SELECT filename FROM _migrations"))
            apply_migrations(conn)
            applied_second = list(conn.execute("SELECT filename FROM _migrations"))
            assert applied_first == applied_second
            assert ("001_initial.sql",) in applied_first
        finally:
            close_db(conn)

    def test_apply_migrations_sets_schema_version_in_meta(self, tmp_path: Path) -> None:
        """meta.schema_version deve refletir última migration aplicada."""
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            version = conn.execute(
                "SELECT valor FROM meta WHERE chave='schema_version'"
            ).fetchone()
            assert version == ("2",)
        finally:
            close_db(conn)


class TestMeta:
    def test_init_meta_writes_defaults(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            init_meta(conn, project_root=str(tmp_path), cli_version="0.1.0")
            assert get_meta(conn, "plugadvpl_version") == "0.1.0"
            assert get_meta(conn, "project_root") == str(tmp_path)
            assert get_meta(conn, "encoding_policy") == "preserve"
        finally:
            conn.close()

    def test_schema_version_after_apply_migrations_and_init_meta(
        self, tmp_path: Path
    ) -> None:
        """Após apply_migrations + init_meta, schema_version deve ser '2'
        (gravado por apply_migrations, NÃO por init_meta — v0.3.0 = migration 002)."""
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            init_meta(conn, project_root=str(tmp_path), cli_version="0.1.0")
            assert get_meta(conn, "schema_version") == "2"
            # SCHEMA_VERSION (constante informacional) ainda existe e bate.
            assert SCHEMA_VERSION == "2"
        finally:
            conn.close()

    def test_get_meta_returns_none_for_missing(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            assert get_meta(conn, "nonexistent") is None
        finally:
            conn.close()

    def test_set_meta_upserts(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            set_meta(conn, "test_key", "value1")
            set_meta(conn, "test_key", "value2")  # upsert
            assert get_meta(conn, "test_key") == "value2"
        finally:
            conn.close()


class TestSeedLookups:
    def test_seed_lookups_populates_all_six_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            counts = seed_lookups(conn)
            assert counts["funcoes_nativas"] > 0
            assert counts["funcoes_restritas"] > 0
            assert counts["lint_rules"] > 0
            assert counts["sql_macros"] > 0
            assert counts["modulos_erp"] > 0
            assert counts["pontos_entrada_padrao"] > 0
            # E os dados realmente foram persistidos
            for table in (
                "funcoes_nativas", "funcoes_restritas", "lint_rules",
                "sql_macros", "modulos_erp", "pontos_entrada_padrao",
            ):
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                assert n > 0, f"{table} should have rows"
        finally:
            close_db(conn)

    def test_seed_lookups_is_idempotent(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            seed_lookups(conn)
            count_first = conn.execute(
                "SELECT COUNT(*) FROM funcoes_restritas"
            ).fetchone()[0]
            seed_lookups(conn)  # 2x — UPSERT idempotente
            count_second = conn.execute(
                "SELECT COUNT(*) FROM funcoes_restritas"
            ).fetchone()[0]
            assert count_first == count_second
            assert count_first > 0
        finally:
            close_db(conn)

    def test_seed_lookups_sets_bundle_hash_in_meta(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            seed_lookups(conn)
            bundle_hash = get_meta(conn, "lookup_bundle_hash")
            assert bundle_hash is not None
            assert len(bundle_hash) == 64  # SHA-256 hex
            # Determinístico: rodar de novo dá o mesmo hash
            seed_lookups(conn)
            assert get_meta(conn, "lookup_bundle_hash") == bundle_hash
        finally:
            close_db(conn)

    def test_seed_lookups_with_explicit_dir(self, tmp_path: Path) -> None:
        """``lookup_dir`` parameter permite isolar o dataset de testes."""
        custom_dir = tmp_path / "custom_lookups"
        custom_dir.mkdir()
        for fname in (
            "funcoes_nativas.json", "funcoes_restritas.json", "lint_rules.json",
            "sql_macros.json", "modulos_erp.json", "pontos_entrada_padrao.json",
        ):
            (custom_dir / fname).write_text("[]", encoding="utf-8")

        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            counts = seed_lookups(conn, lookup_dir=custom_dir)
            assert all(c == 0 for c in counts.values())
            # E nenhuma linha foi inserida
            n = conn.execute("SELECT COUNT(*) FROM funcoes_nativas").fetchone()[0]
            assert n == 0
        finally:
            close_db(conn)

    def test_seed_lookups_serializes_json_list_columns(
        self, tmp_path: Path
    ) -> None:
        """``prefixos_tabelas`` etc. são gravadas como JSON string."""
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            seed_lookups(conn)
            row = conn.execute(
                "SELECT prefixos_tabelas FROM modulos_erp WHERE codigo='COM'"
            ).fetchone()
            assert row is not None
            import json as _json
            tabelas = _json.loads(row[0])
            assert isinstance(tabelas, list)
            assert "SC1" in tabelas
        finally:
            close_db(conn)


class TestCloseDb:
    def test_close_db_truncates_wal(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            conn.execute(
                "INSERT INTO meta (chave, valor) VALUES ('test', 'data')"
            )
            conn.commit()
        finally:
            close_db(conn)
        # Depois de fechar com checkpoint TRUNCATE, .db-wal deve estar
        # pequeno ou ausente
        wal_path = db_path.with_suffix(".db-wal")
        if wal_path.exists():
            assert wal_path.stat().st_size < 100  # apenas header (ou zero)

    def test_close_db_does_not_raise_with_uncommitted_writes(
        self, tmp_path: Path
    ) -> None:
        """Regression: close_db must commit pending writes before WAL checkpoint."""
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            # Insert mas NÃO commit
            conn.execute(
                "INSERT INTO meta (chave, valor) VALUES ('uncommitted', 'data')"
            )
        finally:
            close_db(conn)  # deve não levantar OperationalError
        # Verifica que o INSERT foi persistido (close_db committed before truncate)
        conn2 = sqlite3.connect(str(db_path))
        val = conn2.execute(
            "SELECT valor FROM meta WHERE chave='uncommitted'"
        ).fetchone()
        conn2.close()
        assert val == ("data",)
