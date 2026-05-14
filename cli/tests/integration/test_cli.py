"""Integration tests do typer CLI (plugadvpl/cli.py).

Usamos ``typer.testing.CliRunner`` para invocar subcomandos contra um
diretório temporário com 3 fontes ADVPL sintéticos. Cada teste cobre
1 subcomando ponta-a-ponta (parser -> DB -> render).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from plugadvpl import __version__
from plugadvpl.cli import app


@pytest.fixture
def synthetic_project(tmp_path: Path) -> Path:
    """Cria 3 fontes ADVPL em ``tmp_path/src``."""
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
        b"  U_FATA050()\n"
        b"Return\n"
    )
    (src / "WSReg.tlpp").write_bytes(
        b"Namespace api\n"
        b"User Function WSReg()\n"
        b'  HttpPost("http://api.foo/x", oJson)\n'
        b"Return\n"
    )
    return src


@pytest.fixture
def runner() -> CliRunner:
    """Click >=8.2 já separa stdout/stderr por padrão."""
    return CliRunner()


@pytest.fixture
def indexed_project(synthetic_project: Path, runner: CliRunner) -> Path:
    """Project já passou por ``init`` + ``ingest``."""
    r1 = runner.invoke(app, ["--root", str(synthetic_project), "init"])
    assert r1.exit_code == 0, r1.stderr or r1.stdout
    r2 = runner.invoke(app, ["--root", str(synthetic_project), "ingest"])
    assert r2.exit_code == 0, r2.stderr or r2.stdout
    return synthetic_project


class TestVersion:
    def test_version_subcommand(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_global_flag_long(self, runner: CliRunner) -> None:
        """v0.3.12: `plugadvpl --version` (eager, padrão UNIX) — funciona sem subcomando."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_global_flag_short(self, runner: CliRunner) -> None:
        """v0.3.12: short `-V` também (não conflita com `-v` se algum subcomando usar)."""
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestHelp:
    def test_help_lists_all_subcommands(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # 14 comandos do MVP + 4 novos do v0.3.0 (ingest-sx, impacto, gatilho, sx-status) = 18.
        for cmd in (
            "version", "init", "ingest", "reindex", "status",
            "find", "callers", "callees", "tables", "param",
            "arch", "lint", "doctor", "grep",
            "ingest-sx", "impacto", "gatilho", "sx-status",
        ):
            assert cmd in result.stdout


class TestInit:
    def test_init_creates_db_and_claude_md(
        self, synthetic_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, ["--root", str(synthetic_project), "init"])
        assert result.exit_code == 0, result.stderr or result.stdout
        db = synthetic_project / ".plugadvpl" / "index.db"
        assert db.exists()
        claude_md = synthetic_project / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text(encoding="utf-8")
        assert "<!-- BEGIN plugadvpl -->" in content
        assert "<!-- END plugadvpl -->" in content

    def test_init_is_idempotent(
        self, synthetic_project: Path, runner: CliRunner
    ) -> None:
        runner.invoke(app, ["--root", str(synthetic_project), "init"])
        runner.invoke(app, ["--root", str(synthetic_project), "init"])
        claude_md = synthetic_project / "CLAUDE.md"
        content = claude_md.read_text(encoding="utf-8")
        # Não deve duplicar o fragment.
        assert content.count("<!-- BEGIN plugadvpl -->") == 1

    def test_init_updates_gitignore_when_exists(
        self, synthetic_project: Path, runner: CliRunner
    ) -> None:
        gi = synthetic_project / ".gitignore"
        gi.write_text("*.pyc\n", encoding="utf-8")
        runner.invoke(app, ["--root", str(synthetic_project), "init"])
        assert ".plugadvpl/" in gi.read_text(encoding="utf-8")


class TestIngest:
    def test_ingest_after_init(
        self, synthetic_project: Path, runner: CliRunner
    ) -> None:
        runner.invoke(app, ["--root", str(synthetic_project), "init"])
        result = runner.invoke(
            app, ["--root", str(synthetic_project), "--format", "json", "ingest"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["total"] == 1  # 1 summary row
        assert payload["rows"][0]["ok"] == 3

    def test_ingest_incremental_warns_when_lookups_changed(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """v0.3.13 — pegadinha do feedback real: após `uv tool upgrade` com novas
        regras de lint, `ingest --incremental` pula arquivos cujo mtime não mudou
        e essas regras NÃO são re-aplicadas. Avisa em stderr orientando
        `--no-incremental`. Simulamos forçando um lookup_bundle_hash antigo."""
        db = indexed_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            conn.execute(
                "UPDATE meta SET valor='hash-from-old-version' WHERE chave='lookup_bundle_hash'"
            )
            conn.commit()
        finally:
            conn.close()

        # Re-ingest incremental — todos os 3 arquivos têm mtime antigo, serão skipped.
        result = runner.invoke(
            app, ["--root", str(indexed_project), "ingest"]
        )
        assert result.exit_code == 0
        assert "Lookups" in result.stderr
        assert "--no-incremental" in result.stderr
        assert "ingest" in result.stderr

    def test_ingest_no_incremental_no_warning_even_with_hash_change(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """Em --no-incremental tudo é re-parseado de qualquer jeito → não há
        pegadinha pra avisar."""
        db = indexed_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            conn.execute(
                "UPDATE meta SET valor='hash-from-old-version' WHERE chave='lookup_bundle_hash'"
            )
            conn.commit()
        finally:
            conn.close()

        result = runner.invoke(
            app, ["--root", str(indexed_project), "ingest", "--no-incremental"]
        )
        assert result.exit_code == 0
        assert "--no-incremental" not in result.stderr  # sem aviso

    def test_ingest_incremental_no_warning_when_hash_unchanged(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """Caso normal: nada mudou → sem aviso amarelo."""
        result = runner.invoke(
            app, ["--root", str(indexed_project), "ingest"]
        )
        assert result.exit_code == 0
        assert "Lookups" not in result.stderr

    def test_ingest_warning_suppressed_by_quiet(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """`--quiet` suprime o aviso de divergência de lookups (consistente com
        a política de outras decorações)."""
        db = indexed_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            conn.execute(
                "UPDATE meta SET valor='hash-from-old-version' WHERE chave='lookup_bundle_hash'"
            )
            conn.commit()
        finally:
            conn.close()

        result = runner.invoke(
            app, ["--root", str(indexed_project), "--quiet", "ingest"]
        )
        assert result.exit_code == 0
        assert "Lookups" not in result.stderr


class TestFind:
    def test_find_function(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            ["--root", str(indexed_project), "--format", "json", "find", "FATA050"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Pode ter múltiplos chunks (header + main); pelo menos 1.
        assert payload["total"] >= 1
        assert any("FATA050" in (r.get("arquivo") or "") for r in payload["rows"])


class TestCallers:
    def test_callers_of_fata050(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            ["--root", str(indexed_project), "--format", "json", "callers", "FATA050"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert any(r["arquivo"] == "MATA010.prw" for r in payload["rows"])


class TestTables:
    def test_tables_sc5(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            ["--root", str(indexed_project), "--format", "json", "tables", "SC5"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert any(r["arquivo"] == "FATA050.prw" for r in payload["rows"])


class TestParam:
    def test_param_mv_localiza(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_project), "--format", "json",
                "param", "MV_LOCALIZA",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert any(r["arquivo"] == "MATA010.prw" for r in payload["rows"])


class TestArch:
    def test_arch_fata050(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_project), "--format", "json",
                "arch", "FATA050.prw",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["rows"][0]["arquivo"] == "FATA050.prw"

    def test_arch_missing_exits_1(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            ["--root", str(indexed_project), "arch", "naoexiste.prw"],
        )
        assert result.exit_code == 1


class TestStatus:
    def test_status_reports_indexed_files(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app, ["--root", str(indexed_project), "--format", "json", "status"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["rows"][0]["total_arquivos"] == "3"

    def test_status_includes_runtime_version(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """v0.3.12: status sempre traz `runtime_version` = __version__ do binário."""
        result = runner.invoke(
            app, ["--root", str(indexed_project), "--format", "json", "status"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["rows"][0]["runtime_version"] == __version__

    def test_status_warns_when_binary_diverges_from_index(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """v0.3.12: feedback real (índice 0.2.0, binário 0.3.11) → aviso amarelo
        em stderr orientando `ingest --incremental`. Simulamos forçando um valor
        antigo em meta.plugadvpl_version."""
        # Adultera o meta direto via sqlite — simula índice criado em versão antiga.
        db = indexed_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            conn.execute(
                "UPDATE meta SET valor='0.0.1-old' WHERE chave='plugadvpl_version'"
            )
            conn.commit()
        finally:
            conn.close()

        result = runner.invoke(app, ["--root", str(indexed_project), "status"])
        assert result.exit_code == 0
        # Aviso vai pra stderr (não polui stdout JSON quando rodado com --format json).
        assert "0.0.1-old" in result.stderr
        assert "ingest --incremental" in result.stderr

    def test_status_no_warning_when_versions_match(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """Sem divergência: nenhum aviso amarelo poluindo stderr."""
        result = runner.invoke(app, ["--root", str(indexed_project), "status"])
        assert result.exit_code == 0
        assert "ingest --incremental" not in result.stderr

    def test_status_warning_suppressed_by_quiet(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """`--quiet` suprime o aviso (consistente com a política das outras decorações)."""
        db = indexed_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            conn.execute(
                "UPDATE meta SET valor='0.0.1-old' WHERE chave='plugadvpl_version'"
            )
            conn.commit()
        finally:
            conn.close()

        result = runner.invoke(
            app, ["--root", str(indexed_project), "--quiet", "status"]
        )
        assert result.exit_code == 0
        assert "0.0.1-old" not in result.stderr


class TestDoctor:
    def test_doctor_returns_diagnostics(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app, ["--root", str(indexed_project), "--format", "json", "doctor"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        checks = {r["check"] for r in payload["rows"]}
        assert "fts_sync" in checks


class TestGrep:
    def test_grep_fts_default(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            ["--root", str(indexed_project), "--format", "json", "grep", "RecLock"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["total"] >= 1


class TestLint:
    def test_lint_global(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app, ["--root", str(indexed_project), "--format", "json", "lint"]
        )
        assert result.exit_code == 0, result.stderr
        # Pode estar vazio mas tem que retornar JSON válido.
        json.loads(result.stdout)


class TestMissingDb:
    def test_query_without_db_exits_2(
        self, synthetic_project: Path, runner: CliRunner
    ) -> None:
        # Sem init nem ingest, find deve falhar com saída amigável.
        result = runner.invoke(
            app, ["--root", str(synthetic_project), "find", "FATA050"]
        )
        assert result.exit_code == 2


class TestReindex:
    def test_reindex_single_file(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_project), "--format", "json",
                "reindex", "FATA050.prw",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["rows"][0]["arquivo"] == "FATA050.prw"
        assert payload["rows"][0]["ok"] == 1
