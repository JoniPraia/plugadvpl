"""Integration tests do typer CLI (plugadvpl/cli.py).

Usamos ``typer.testing.CliRunner`` para invocar subcomandos contra um
diretório temporário com 3 fontes ADVPL sintéticos. Cada teste cobre
1 subcomando ponta-a-ponta (parser -> DB -> render).
"""
from __future__ import annotations

import json
import re
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


class TestGlobalFlagPositioning:
    def test_misplaced_global_flag_shows_helpful_hint(
        self, indexed_project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """v0.3.15 — Bug #2 do QA report: usuario rodava
        `plugadvpl status --limit 20` e recebia "No such option: --limit"
        sem indicacao de que a flag eh global e precisa vir antes do
        subcomando. Agora `main()` detecta o caso comum e adiciona hint
        amarelo em stderr APOS o erro do click.

        Testamos via main() (nao runner.invoke) porque o wrapper da hint
        vive em main(), nao em app — o runner bypassa main()."""
        from plugadvpl.cli import main as cli_main

        monkeypatch.setattr(
            "sys.argv",
            ["plugadvpl", "--root", str(indexed_project), "status", "--limit", "20"],
        )
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        # Hint vai pra stderr APOS o erro nativo do click.
        assert "--limit" in captured.err
        assert "global" in captured.err.lower() or "antes" in captured.err.lower()

    def test_misplaced_subcommand_flag_shows_inverse_hint(
        self,
        indexed_project: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """v0.3.22 — Bug #18 do QA round 2: caso inverso. Usuario roda
        `plugadvpl --workers 8 ingest` (achando que --workers eh global)
        e recebe `No such option: --workers` cru. Agora detectamos e
        sugerimos posicionar DEPOIS do subcomando."""
        from plugadvpl.cli import main as cli_main

        monkeypatch.setattr(
            "sys.argv",
            ["plugadvpl", "--root", str(indexed_project), "--workers", "8", "ingest"],
        )
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "--workers" in captured.err
        assert "subcomando" in captured.err.lower() or "depois" in captured.err.lower()


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

    def test_status_warns_when_claude_md_fragment_is_stale(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """v0.3.23 — Bug #1 do QA round 3: usuario com projeto init'd numa
        versao antiga (ex: v0.3.0) tem fragment do CLAUDE.md desatualizado
        (cita `--fts/--literal/--identifier` em vez de `-m fts|literal|identifier`).
        Status agora detecta marker de versao no fragment e avisa quando
        nao bate com runtime_version, orientando re-rodar `init`."""
        # Simula fragment de versao antiga: re-grava CLAUDE.md com marker velho.
        claude_md = indexed_project / "CLAUDE.md"
        content = claude_md.read_text(encoding="utf-8")
        # Substitui o marker pra versao antiga.
        content = re.sub(
            r"<!-- plugadvpl-fragment-version: [^>]+ -->",
            "<!-- plugadvpl-fragment-version: 0.0.1-old -->",
            content,
        )
        claude_md.write_text(content, encoding="utf-8")

        result = runner.invoke(app, ["--root", str(indexed_project), "status"])
        assert result.exit_code == 0
        assert "fragment" in result.stderr.lower()
        assert "0.0.1-old" in result.stderr or "init" in result.stderr.lower()

    def test_status_no_fragment_warning_when_marker_matches(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """Marker fresh do init recente — nao avisa."""
        result = runner.invoke(app, ["--root", str(indexed_project), "status"])
        assert result.exit_code == 0
        assert "fragment" not in result.stderr.lower()

    def test_status_warns_when_claude_md_has_no_fragment_marker(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """Fragment pre-v0.3.23 nao tem marker. Status deve avisar tambem."""
        claude_md = indexed_project / "CLAUDE.md"
        content = claude_md.read_text(encoding="utf-8")
        # Remove marker simulando fragment antigo (sem versionamento).
        content = re.sub(
            r"<!-- plugadvpl-fragment-version: [^>]+ -->\n?", "", content,
        )
        claude_md.write_text(content, encoding="utf-8")

        result = runner.invoke(app, ["--root", str(indexed_project), "status"])
        assert result.exit_code == 0
        assert "fragment" in result.stderr.lower()

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

    def test_callers_flags_is_self_call(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.18 — Bug #12 do QA report: `callers <nome>` misturava
        callsites externos com self-calls (FwLoadModel('X') dentro de X.prw)
        sem distincao. Agora cada row tem `is_self_call: bool` baseado em
        `funcao_origem == nome` OR `basename(arquivo_origem) == nome`."""
        src = tmp_path / "src"
        src.mkdir()
        # Self-call: dentro de SelfCall.prw, funcao SelfCall chama propria via FwLoadModel.
        (src / "SelfCall.prw").write_bytes(
            b'#include "totvs.ch"\n'
            b'User Function SelfCall()\n'
            b'  Local oModel := FwLoadModel("SelfCall")\n'
            b'Return\n'
        )
        # External: outro fonte chama SelfCall.
        (src / "Caller.prw").write_bytes(
            b'#include "totvs.ch"\n'
            b'User Function Caller()\n'
            b'  U_SelfCall()\n'
            b'Return\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])
        result = runner.invoke(
            app,
            ["--root", str(src), "--format", "json", "callers", "SelfCall"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        rows = payload["rows"]
        # Esperado: 1 self (FwLoadModel) + 1 external (U_SelfCall)
        self_calls = [r for r in rows if r.get("is_self_call") is True]
        external = [r for r in rows if r.get("is_self_call") is False]
        assert len(self_calls) >= 1, f"esperado >=1 self_call, rows={rows}"
        assert len(external) >= 1, f"esperado >=1 external, rows={rows}"
        # Self deve vir de SelfCall.prw; external de Caller.prw.
        assert all("SelfCall" in r["arquivo"] for r in self_calls)
        assert all("Caller" in r["arquivo"] for r in external)

    def test_arch_flags_tabelas_via_execauto(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.18 — Bug #11 do QA report: programas que usam MsExecAuto
        delegam acesso a tabelas pra rotina chamada — `tabelas_*` do parser
        ficam vazias mesmo o programa "tocando" SC5/SC6/SF4 etc. Sem flag,
        usuario tira conclusao errada confiando so na lista. Agora `arch`
        expoe `tabelas_via_execauto: bool` quando `EXEC_AUTO_CALLER` esta
        em capabilities."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "ExecAutoCaller.prw").write_bytes(
            b'#include "totvs.ch"\n'
            b'User Function ExecAutoCaller()\n'
            b'  Local aCab := {{"C5_NUM", "001", Nil}}\n'
            b'  Local aIt  := {{{"C6_NUM", "001", Nil}}}\n'
            b'  Private lMsErroAuto := .F.\n'
            b'  MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCab, aIt, 3)\n'
            b'  If lMsErroAuto\n'
            b'    MostraErro()\n'
            b'  EndIf\n'
            b'Return\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])
        result = runner.invoke(
            app,
            ["--root", str(src), "--format", "json", "arch", "ExecAutoCaller.prw"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        row = payload["rows"][0]
        assert "EXEC_AUTO_CALLER" in row["capabilities"], (
            f"Caso de teste deve ter EXEC_AUTO_CALLER. caps={row['capabilities']}"
        )
        assert row.get("tabelas_via_execauto") is True, (
            f"Esperado tabelas_via_execauto=True quando EXEC_AUTO_CALLER, "
            f"recebido {row.get('tabelas_via_execauto')!r}"
        )

    def test_arch_no_execauto_flag_when_no_capability(
        self, indexed_project: Path, runner: CliRunner
    ) -> None:
        """Caso negativo: fonte sem MsExecAuto deve ter tabelas_via_execauto=False."""
        result = runner.invoke(
            app,
            ["--root", str(indexed_project), "--format", "json", "arch", "FATA050.prw"],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        row = payload["rows"][0]
        assert row.get("tabelas_via_execauto") is False

    def test_lint_findings_no_duplicates_alias_reclock(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.18 — Bug #9 do QA report: BP-001 reportava o mesmo RecLock
        2x quando vinha em forma `<alias>->(RecLock(...))` — casava com
        AMBOS _RECLOCK_OPEN_RE (literal) E _RECLOCK_VIA_ALIAS_RE (alias).
        Fixture forca o cenario; teste assegura unicidade no DB."""
        src = tmp_path / "src"
        src.mkdir()
        fixture = (
            Path(__file__).parent.parent
            / "fixtures" / "synthetic" / "reclock_alias_dup_trigger.prw"
        )
        (src / "ZH3DupTrigger.prw").write_bytes(fixture.read_bytes())
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])
        db = src / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            dups = conn.execute(
                """
                SELECT arquivo, linha, regra_id, COUNT(*) AS n
                FROM lint_findings
                WHERE regra_id='BP-001'
                GROUP BY arquivo, linha, regra_id
                HAVING n > 1
                """
            ).fetchall()
        finally:
            conn.close()
        assert dups == [], (
            f"BP-001 duplicado em (arquivo, linha): {dups}. "
            "ZH3->(RecLock(...)) deveria gerar 1 finding, nao 2."
        )


class TestWorkflow:
    """v0.4.0 — Universo 3 / Feature A: comando `workflow` lista execution_triggers."""

    @pytest.fixture
    def triggers_project(self, tmp_path: Path, runner: CliRunner) -> Path:
        """Projeto com 4 fontes cobrindo cada kind + 1 multi-trigger."""
        src = tmp_path / "src"
        src.mkdir()
        # 1) workflow (TWFProcess)
        (src / "WFSalNeg.prw").write_bytes(
            b'User Function WfSalNeg()\n'
            b'  Local oWF := TWFProcess():New("SALNEG", "Saldo Negativo")\n'
            b'  oWF:bReturn := {|o| U_WfRetSN(o)}\n'
            b'  oWF:Start()\n'
            b'Return\n'
        )
        # 2) schedule (SchedDef)
        (src / "FATR020.prw").write_bytes(
            b'User Function FATR020()\n'
            b'Return\n'
            b'\n'
            b'Static Function SchedDef()\n'
            b'  Local a := { "R", "FAT020", "SF2", {1,2}, "Faturamento" }\n'
            b'Return a\n'
        )
        # 3) multi-trigger: job_standalone + mail_send no mesmo fonte
        (src / "JobAviso.prw").write_bytes(
            b'Main Function JobAviso()\n'
            b'  RpcSetEnv("01","01",,,"FAT","JobAviso")\n'
            b'  While !File("/stop_aviso.flg")\n'
            b'    MailAuto("a@x", "b@y", "Aviso", "msg", {})\n'
            b'    Sleep(60000)\n'
            b'  EndDo\n'
            b'  RpcClearEnv()\n'
            b'Return\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])
        return src

    def test_workflow_lists_all_kinds(
        self, triggers_project: Path, runner: CliRunner
    ) -> None:
        """Sem filtro: lista os 4 kinds (workflow/schedule/job_standalone/mail_send)."""
        result = runner.invoke(
            app, ["--root", str(triggers_project), "--format", "json", "workflow"]
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        kinds = {r["kind"] for r in rows}
        assert kinds == {"workflow", "schedule", "job_standalone", "mail_send"}, (
            f"esperado os 4 kinds, recebido {kinds}"
        )

    def test_workflow_filter_by_kind(
        self, triggers_project: Path, runner: CliRunner
    ) -> None:
        """`--kind job_standalone` retorna só jobs daemon."""
        result = runner.invoke(
            app,
            [
                "--root", str(triggers_project), "--format", "json",
                "workflow", "--kind", "job_standalone",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["kind"] == "job_standalone"
        assert rows[0]["target"] == "JobAviso"

    def test_workflow_filter_by_arquivo(
        self, triggers_project: Path, runner: CliRunner
    ) -> None:
        """`--arquivo JobAviso.prw` retorna 2 triggers (job + mail) do multi-source."""
        result = runner.invoke(
            app,
            [
                "--root", str(triggers_project), "--format", "json",
                "workflow", "--arquivo", "JobAviso.prw",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        kinds = {r["kind"] for r in rows}
        assert kinds == {"job_standalone", "mail_send"}, (
            f"esperado job+mail no mesmo fonte, recebido {kinds}"
        )

    def test_workflow_filter_by_target(
        self, triggers_project: Path, runner: CliRunner
    ) -> None:
        """`--target FAT020` (pergunte SX1) localiza o schedule."""
        result = runner.invoke(
            app,
            [
                "--root", str(triggers_project), "--format", "json",
                "workflow", "--target", "FAT020",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["kind"] == "schedule"

    def test_workflow_persisted_in_db(
        self, triggers_project: Path
    ) -> None:
        """Sanity check: execution_triggers tabela existe e tem rows do ingest."""
        db = triggers_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM execution_triggers"
            ).fetchone()[0]
        finally:
            conn.close()
        assert count >= 4, f"esperado >=4 triggers, encontrado {count}"


class TestExecauto:
    """v0.4.1 — Universo 3 / Feature B: comando `execauto` lista chamadas resolvidas."""

    @pytest.fixture
    def execauto_project(self, tmp_path: Path, runner: CliRunner) -> Path:
        """Projeto com 3 fontes cobrindo MATA410 (inc), FINA050 (inc), e dynamic."""
        src = tmp_path / "src"
        src.mkdir()
        # MATA410 inclusao — SC5/SC6 + secundarias.
        (src / "MGFCOMBO.prw").write_bytes(
            b'User Function MGFCOMBO()\n'
            b'   MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCab, aIt, 3)\n'
            b'Return\n'
        )
        # FINA050 inclusao — SE2.
        (src / "MGFFIN50.prw").write_bytes(
            b'User Function MGFFIN50()\n'
            b'   MsExecAuto({|x,y| FINA050(x,y)}, aArr, 3)\n'
            b'Return\n'
        )
        # Dynamic — &(cVar).
        (src / "MGFDYN.prw").write_bytes(
            b'User Function MGFDYN()\n'
            b'   MsExecAuto({|x,y,z| &(cRot).(x,y,z)}, aCab, aIt, 3)\n'
            b'Return\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])
        return src

    def test_execauto_lists_all(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """Sem filtro: lista as 3 chamadas (MATA410, FINA050, dynamic)."""
        result = runner.invoke(
            app, ["--root", str(execauto_project), "--format", "json", "execauto"]
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 3
        routines = {r["routine"] or "(dynamic)" for r in rows}
        assert routines == {"MATA410", "FINA050", "(dynamic)"}

    def test_execauto_filter_by_routine(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """`--routine MATA410` retorna só a chamada com SC5/SC6."""
        result = runner.invoke(
            app,
            [
                "--root", str(execauto_project), "--format", "json",
                "execauto", "--routine", "MATA410",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["routine"] == "MATA410"
        assert rows[0]["module"] == "SIGAFAT"
        assert "SC5" in rows[0]["tabelas"]
        assert "SC6" in rows[0]["tabelas"]
        assert rows[0]["op"] == "inclusao"

    def test_execauto_filter_by_modulo(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """`--modulo SIGAFIN` localiza só FINA050."""
        result = runner.invoke(
            app,
            [
                "--root", str(execauto_project), "--format", "json",
                "execauto", "--modulo", "SIGAFIN",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["routine"] == "FINA050"

    def test_execauto_filter_dynamic_only(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """`--dynamic` retorna só calls não-resolvíveis."""
        result = runner.invoke(
            app,
            [
                "--root", str(execauto_project), "--format", "json",
                "execauto", "--dynamic",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["routine"] == "(dynamic)"

    def test_execauto_filter_op_inc(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """`--op inc` retorna só inclusões (op_code=3)."""
        result = runner.invoke(
            app,
            [
                "--root", str(execauto_project), "--format", "json",
                "execauto", "--op", "inc",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        # Todas as 3 fixtures usam op=3, então 3 rows
        assert len(rows) == 3
        for r in rows:
            assert r["op"] == "inclusao"

    def test_arch_exposes_tabelas_via_execauto_resolvidas(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """v0.4.1 enrichment: `arch` mostra tabelas inferidas via ExecAuto."""
        result = runner.invoke(
            app,
            [
                "--root", str(execauto_project), "--format", "json",
                "arch", "MGFCOMBO.prw",
            ],
        )
        assert result.exit_code == 0, result.stderr
        row = json.loads(result.stdout)["rows"][0]
        # Bool antigo continua
        assert row.get("tabelas_via_execauto") is True
        # Novo campo: lista de tabelas resolvidas
        resolved = row.get("tabelas_via_execauto_resolvidas", [])
        assert "SC5" in resolved
        assert "SC6" in resolved

    def test_arch_resolved_empty_when_dynamic_only(
        self, execauto_project: Path, runner: CliRunner
    ) -> None:
        """Fonte com só call dynamic → resolved = []."""
        result = runner.invoke(
            app,
            [
                "--root", str(execauto_project), "--format", "json",
                "arch", "MGFDYN.prw",
            ],
        )
        assert result.exit_code == 0, result.stderr
        row = json.loads(result.stdout)["rows"][0]
        assert row.get("tabelas_via_execauto_resolvidas", []) == []

    def test_execauto_persisted_in_db(self, execauto_project: Path) -> None:
        """Sanity: tabela execauto_calls existe e tem rows."""
        db = execauto_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            count = conn.execute("SELECT COUNT(*) FROM execauto_calls").fetchone()[0]
        finally:
            conn.close()
        assert count == 3


class TestDocs:
    """v0.4.2 — Universo 3 / Feature C: comando `docs` agrega Protheus.doc."""

    @pytest.fixture
    def docs_project(self, tmp_path: Path, runner: CliRunner) -> Path:
        """Projeto com 3 fontes: 1 doc completo, 1 deprecated, 1 órfão (sem doc)."""
        src = tmp_path / "src" / "SIGAFAT"
        src.mkdir(parents=True)
        # 1) Doc completo
        (src / "MT460FIM.tlpp").write_bytes(
            b'/*/{Protheus.doc} MT460FIM\n'
            b'Ponto de Entrada apos faturamento.\n'
            b'@type user function\n'
            b'@author Fernando Vernier\n'
            b'@since 18/10/2025\n'
            b'@version 2.0\n'
            b'@param cNumNF, character, "Numero da NF"\n'
            b'@return logical, ".T. se sucesso"\n'
            b'/*/\n'
            b'User Function MT460FIM(cNumNF)\n'
            b'Return .T.\n'
        )
        # 2) Deprecated
        (src / "MT460OLD.tlpp").write_bytes(
            b'/*/{Protheus.doc} MT460OLD\n'
            b'Versao antiga do PE.\n'
            b'@type user function\n'
            b'@author Joao\n'
            b'@deprecated Use MT460FIM no lugar\n'
            b'/*/\n'
            b'User Function MT460OLD()\n'
            b'Return\n'
        )
        # 3) Órfão (sem doc) — gera BP-007.
        (src / "MT460NEW.tlpp").write_bytes(
            b'User Function MT460NEW()\n'
            b'   ConOut("sem doc")\n'
            b'Return\n'
        )
        runner.invoke(app, ["--root", str(tmp_path / "src"), "init"])
        runner.invoke(app, ["--root", str(tmp_path / "src"), "ingest"])
        return tmp_path / "src"

    def test_docs_lists_all(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """Sem filtro: lista 2 docs (MT460FIM + MT460OLD; órfão NÃO aparece aqui)."""
        result = runner.invoke(
            app, ["--root", str(docs_project), "--format", "json", "docs"]
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 2
        funcs = {r["funcao"] for r in rows}
        assert funcs == {"MT460FIM", "MT460OLD"}

    def test_docs_filter_by_modulo(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """Path `src/SIGAFAT/...` infere SIGAFAT."""
        result = runner.invoke(
            app,
            [
                "--root", str(docs_project), "--format", "json",
                "docs", "SIGAFAT",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 2
        for r in rows:
            assert r["modulo"] == "SIGAFAT"

    def test_docs_filter_deprecated(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """`--deprecated` retorna só MT460OLD."""
        result = runner.invoke(
            app,
            [
                "--root", str(docs_project), "--format", "json",
                "docs", "--deprecated",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["funcao"] == "MT460OLD"
        assert rows[0]["deprecated"] == "sim"

    def test_docs_filter_author(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """`--author Fernando` LIKE match localiza só MT460FIM."""
        result = runner.invoke(
            app,
            [
                "--root", str(docs_project), "--format", "json",
                "docs", "--author", "Fernando",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        assert len(rows) == 1
        assert rows[0]["funcao"] == "MT460FIM"

    def test_docs_show_renders_markdown(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """`--show MT460FIM` retorna Markdown estruturado."""
        result = runner.invoke(
            app, ["--root", str(docs_project), "docs", "--show", "MT460FIM"]
        )
        assert result.exit_code == 0, result.stderr
        out = result.stdout
        assert "## MT460FIM" in out
        assert "SIGAFAT" in out
        assert "Fernando Vernier" in out
        assert "### Parâmetros" in out
        assert "cNumNF" in out
        assert "### Retorno" in out

    def test_docs_show_not_found_exits_1(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """`--show <inexistente>` retorna exit 1."""
        result = runner.invoke(
            app, ["--root", str(docs_project), "docs", "--show", "FnInexistente"]
        )
        assert result.exit_code == 1

    def test_docs_orphans_lists_bp007(
        self, docs_project: Path, runner: CliRunner
    ) -> None:
        """`--orphans` lista funções sem header (cross-ref BP-007)."""
        result = runner.invoke(
            app,
            [
                "--root", str(docs_project), "--format", "json",
                "docs", "--orphans",
            ],
        )
        assert result.exit_code == 0, result.stderr
        rows = json.loads(result.stdout)["rows"]
        # MT460NEW deve aparecer como órfão
        funcs = {r["funcao"] for r in rows}
        assert "MT460NEW" in funcs

    def test_docs_persisted_in_db(self, docs_project: Path) -> None:
        """Sanity: tabela protheus_docs existe e tem 2 rows."""
        db = docs_project / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(db)
        try:
            count = conn.execute("SELECT COUNT(*) FROM protheus_docs").fetchone()[0]
        finally:
            conn.close()
        assert count == 2


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
