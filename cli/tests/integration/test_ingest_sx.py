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

    def test_sxb_consultas_preserves_all_tipos(
        self, sx_project: Path, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.14 — SXB tem 6 tipos (header/indice/permissao/coluna/retorno/filtro)
        que coexistem para um mesmo (alias, seq, coluna). Sem `tipo` no PK, eles
        se sobrescrevem mutuamente — bug real reportado em dump 58k → 46k consultas.

        Fixture: 1 alias 'USRGRP' com 6 linhas, 1 por tipo, todas (seq='01', coluna='').
        Esperado: 6 rows distintas em `consultas` após ingest.
        """
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        (csv_dir / "sxb.csv").write_bytes(
            (SX_FIXTURES / "sxb_with_collisions.csv").read_bytes()
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        counters = ingest_sx(csv_dir, db)
        assert counters["per_table"]["consultas"] == 6, (
            "parser leu as 6 linhas do CSV (cada uma com tipo distinto)"
        )
        conn = _connect(db)
        try:
            n = conn.execute("SELECT COUNT(*) FROM consultas").fetchone()[0]
            assert n == 6, (
                f"DB deveria ter 6 rows (uma por tipo), mas tem {n}. "
                "PK (alias, seq, coluna) sem `tipo` faz colidir as 6 paginas SXB."
            )
            tipos = {
                row[0] for row in conn.execute(
                    "SELECT tipo FROM consultas WHERE alias='USRGRP'"
                )
            }
            assert tipos == {"1", "2", "3", "4", "5", "6"}, (
                f"Esperado {{'1'..'6'}}, recebido {tipos}"
            )
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

    def test_ingest_sx_per_table_reflects_db_count_not_csv_count(
        self,
        sx_project: Path,
        tmp_path: Path,
        runner: CliRunner,
    ) -> None:
        """v0.3.21 — Bug #15 do QA round 2: counters['per_table'][table] guardava
        len(rows) processadas do CSV, NAO COUNT(*) real do DB apos dedup. Resultado
        bizarro: summary mostrava 1918 pastas, sx-status mostrava 1833 (caso real
        do cliente). v0.3.14 ja avisava no stderr mas o numero do summary mentia.

        Agora per_table[table] === SELECT COUNT(*) FROM <table> apos dedup."""
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        # Mesma fixture do warning test: 3 rows colapsam em 1.
        (csv_dir / "sxa.csv").write_text(
            '"XA_ALIAS","XA_ORDEM","XA_DESCRIC","XA_AGRUP","XA_PROPRI","D_E_L_E_T_"\n'
            '"SA1","01","Geral","","",""\n'
            '"SA1","01","Outro","","",""\n'
            '"SA1","01","Mais um","","",""\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        counters = ingest_sx(csv_dir, db)
        # Antes do fix: per_table["pastas"] == 3 (mente). Depois: == 1.
        assert counters["per_table"]["pastas"] == 1, (
            f"per_table['pastas'] deveria refletir DB count (1) apos dedup, "
            f"recebido {counters['per_table']['pastas']}. v0.3.14 warning ja "
            "mostra a perda; agora o number do summary tambem deve estar correto."
        )

    def test_ingest_sx_warns_when_dedup_lost_rows(
        self,
        sx_project: Path,
        tmp_path: Path,
        runner: CliRunner,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """v0.3.14 — transparencia de deduplicacao. CSV com 3 rows que colidem
        em (alias, ordem) deve avisar quanto sumiu apos INSERT OR REPLACE."""
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        # 3 rows pra alias=SA1, ordem=01 → vira 1 row no DB (perda = 2/3 = 66%)
        (csv_dir / "sxa.csv").write_text(
            '"XA_ALIAS","XA_ORDEM","XA_DESCRIC","XA_AGRUP","XA_PROPRI","D_E_L_E_T_"\n'
            '"SA1","01","Geral","","",""\n'
            '"SA1","01","Outro","","",""\n'
            '"SA1","01","Mais um","","",""\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(csv_dir, db)
        captured = capsys.readouterr()
        # Aviso deve citar a tabela 'pastas', quantos foram perdidos e o motivo.
        assert "pastas" in captured.err.lower()
        assert "2" in captured.err  # 2 rows perdidos
        # Pista pra IA/usuario entender o que aconteceu.
        assert "duplicad" in captured.err.lower() or "pk" in captured.err.lower()

    def test_ingest_sx_no_dedup_warning_when_clean(
        self,
        sx_project: Path,
        sx_csv_dir: Path,
        runner: CliRunner,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Sem colisoes nos fixtures sinteticos limpos — nao deve poluir stderr."""
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(sx_csv_dir, db)
        captured = capsys.readouterr()
        # Sem aviso de dedup (pode haver outras coisas em stderr — ex: SXG mislabel
        # se o fixture tiver header X3_*; checamos especificamente o de dedup).
        assert "duplicad" not in captured.err.lower()
        assert "deduplicados" not in captured.err.lower()

    def test_ingest_sx_preserves_project_root(
        self,
        sx_project: Path,
        sx_csv_dir: Path,
        runner: CliRunner,
    ) -> None:
        """v0.3.15 — Bug #13 do QA report: `ingest-sx` chamava
        `init_meta(project_root=str(csv_dir))` que sobrescrevia o
        `project_root` original (raiz do projeto) com o caminho do CSV dir.
        Sintoma observado: apos `ingest-sx D:\\...\\CSV`, status mostrava
        `project_root=D:\\...\\CSV` em vez da raiz do projeto."""
        # Step 1: init grava project_root = sx_project.
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        conn = _connect(db)
        try:
            row = conn.execute(
                "SELECT valor FROM meta WHERE chave='project_root'"
            ).fetchone()
            project_root_before = row[0]
        finally:
            conn.close()
        assert project_root_before == str(sx_project)

        # Step 2: ingest-sx com csv_dir != project_root.
        ingest_sx(sx_csv_dir, db)

        # Step 3: project_root deve continuar igual; sx_csv_dir vai pra slot proprio.
        conn = _connect(db)
        try:
            project_root_after = conn.execute(
                "SELECT valor FROM meta WHERE chave='project_root'"
            ).fetchone()[0]
            sx_csv_dir_meta = conn.execute(
                "SELECT valor FROM meta WHERE chave='sx_csv_dir'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert project_root_after == project_root_before, (
            f"project_root sobrescrito! antes={project_root_before!r}, "
            f"depois={project_root_after!r}"
        )
        assert sx_csv_dir_meta == str(sx_csv_dir.resolve())

    def test_sxg_mislabel_emits_warning(
        self,
        sx_project: Path,
        tmp_path: Path,
        runner: CliRunner,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """v0.3.14 — quando `sxg.csv` eh na verdade um dump SX3 (header X3_*),
        `parse_sxg` historicamente retornava `[]` silenciosamente. Agora avisa
        em stderr pra IA/usuario nao ficar adivinhando por que grupos_campo=0."""
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        (csv_dir / "sxg.csv").write_text(
            '"X3_ARQUIVO","X3_ORDEM","X3_CAMPO","D_E_L_E_T_"\n'
            '"A02","01","A02_FILIAL",""\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(csv_dir, db)
        captured = capsys.readouterr()
        assert "sxg" in captured.err.lower()
        assert "SX3" in captured.err or "sx3" in captured.err.lower()

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

    def test_impacto_uses_word_boundary_no_substring_false_positives(
        self,
        sx_project: Path,
        tmp_path: Path,
        runner: CliRunner,
    ) -> None:
        """v0.3.17 — Bug #3 do QA report: `impacto A1_COD` retornava >100KB
        de output com gatilhos de campos `BA1_CODEMP`, `DA1_CODPRO`, etc.
        cujo nome apenas CONTEM 'A1_COD' como substring. SQL usa
        `LIKE '%A1_COD%'` sem boundary. Fix: re-validar cada match em Python
        com regex `\\bA1_COD\\b` antes de devolver.

        Fixture: SX7 com 3 gatilhos:
          - A1_COD->A1_NREDUZ (regra=SA1->A1_NREDUZ) — match REAL (campo eh A1_COD)
          - BA1_CODEMP->X (regra=SBA->BA1_CODEMP) — substring fake
          - A1_CODFAT->Y (origem=A1_CODFAT, A1_COD eh prefixo) — fake
        Esperado: impacto('A1_COD') so retorna o primeiro."""
        from plugadvpl.ingest_sx import ingest_sx

        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        # SX3 minimal pra ter pelo menos 1 row no banco.
        (csv_dir / "sx3.csv").write_text(
            '"X3_ARQUIVO","X3_CAMPO","X3_TIPO","X3_TAMANHO","X3_DECIMAL",'
            '"X3_TITULO","X3_DESCRIC","X3_VALID","X3_VLDUSER","X3_WHEN",'
            '"X3_INIT","D_E_L_E_T_"\n'
            '"SA1","A1_COD","C",6,0,"Codigo","","","","","",""\n',
            encoding="cp1252",
        )
        # SX7 com 3 gatilhos: 1 real + 2 substring-fake.
        (csv_dir / "sx7.csv").write_text(
            '"X7_CAMPO","X7_SEQUENC","X7_CDOMIN","X7_REGRA","X7_TIPO",'
            '"X7_ALIAS","X7_CONDIC","X7_PROPRI","X7_SEEK","X7_ORDEM","X7_CHAVE","D_E_L_E_T_"\n'
            # REAL: origem eh A1_COD literal
            '"A1_COD","01","A1_NREDUZ","SA1->A1_NREDUZ","P","SA1","","S","S","1","",""\n'
            # FAKE 1: origem eh BA1_CODEMP, regra contem "A1_COD" como substring
            '"BA1_CODEMP","01","BA1_VALOR","SBA->BA1_CODEMP","P","","","U","","","",""\n'
            # FAKE 2: origem eh A1_CODFAT (A1_COD eh prefixo), regra contem A1_CODFAT
            '"A1_CODFAT","01","A1_TIPO","M->A1_CODFAT","P","","","U","","","",""\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(csv_dir, db)

        result = runner.invoke(
            app,
            [
                "--root", str(sx_project),
                "--format", "json",
                "impacto", "A1_COD",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        sx7_locals = [r["local"] for r in payload["rows"] if r["tipo"] == "SX7"]
        # SO o gatilho REAL deve aparecer.
        assert any("A1_COD#" in loc and "BA1_CODEMP" not in loc and "A1_CODFAT" not in loc
                   for loc in sx7_locals), (
            f"Gatilho real A1_COD->A1_NREDUZ deveria aparecer. SX7 locals: {sx7_locals}"
        )
        # FAKES nao devem aparecer.
        assert not any("BA1_CODEMP" in loc for loc in sx7_locals), (
            f"FALSE POSITIVE: BA1_CODEMP nao eh A1_COD (substring). SX7 locals: {sx7_locals}"
        )
        assert not any("A1_CODFAT" in loc for loc in sx7_locals), (
            f"FALSE POSITIVE: A1_CODFAT nao eh A1_COD (prefixo). SX7 locals: {sx7_locals}"
        )

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

    def test_gatilho_bidirectional_traversal_depth2(
        self,
        sx_project: Path,
        tmp_path: Path,
        runner: CliRunner,
    ) -> None:
        """v0.3.22 — Bug #6 do QA round 2: ate v0.3.21 a query expandia OR
        campo_destino mas o frontier so seguia downstream (cd → ...). Quem
        casa via campo_destino=X tem co (upstream) nunca expandido. Cadeia
        upstream morre em level 1.

        Fixture:
          Z → Y  (Z eh upstream de Y)
          Y → X  (Y eh upstream de X)
        gatilho X --depth 2 deve retornar:
          level 1: Y → X (origem Y casa via destino)
          level 2: Z → Y (Y agora deve estar em frontier de level 2)
        """
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        (csv_dir / "sx7.csv").write_text(
            '"X7_CAMPO","X7_SEQUENC","X7_CDOMIN","X7_REGRA","X7_TIPO",'
            '"X7_ALIAS","X7_CONDIC","X7_PROPRI","X7_SEEK","X7_ORDEM",'
            '"X7_CHAVE","D_E_L_E_T_"\n'
            # Z → Y
            '"Z_FLD","01","Y_FLD","Upper(Z_FLD)","P","","","U","","","",""\n'
            # Y → X
            '"Y_FLD","01","X_FLD","Upper(Y_FLD)","P","","","U","","","",""\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(csv_dir, db)

        result = runner.invoke(
            app,
            [
                "--root", str(sx_project), "--format", "json",
                "gatilho", "X_FLD", "--depth", "2",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Esperado: Y→X (level 1, via destino) E Z→Y (level 2, via upstream).
        pairs = {(r["origem"].upper(), r["destino"].upper()) for r in payload["rows"]}
        assert ("Y_FLD", "X_FLD") in pairs, f"Y→X falta. pairs={pairs}"
        assert ("Z_FLD", "Y_FLD") in pairs, (
            f"Z→Y (upstream traversal level 2) deveria aparecer. pairs={pairs}"
        )

    def test_gatilho_includes_destination_matches(
        self, indexed_with_sx: Path, runner: CliRunner
    ) -> None:
        """v0.3.15 — Bug #4 do QA report: help diz `originados/destinados`
        mas query so casava `WHERE upper(campo_origem) = ?`. Agora deve achar
        gatilhos onde o campo aparece como destino.

        Fixture tem: A1_COD->A1_NREDUZ, A1_COD->A1_FANTASMA, A1_NREDUZ->A1_XCUSTOM.
        Query por A1_NREDUZ deve retornar AMBOS (origem A1_COD, e A1_NREDUZ
        como origem indo pra A1_XCUSTOM)."""
        result = runner.invoke(
            app,
            [
                "--root", str(indexed_with_sx),
                "--format", "json",
                "gatilho", "A1_NREDUZ", "--depth", "1",
            ],
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        # Origem A1_NREDUZ → destino A1_XCUSTOM (gatilho onde A1_NREDUZ é origem).
        # Origem A1_COD → destino A1_NREDUZ (gatilho onde A1_NREDUZ é destino).
        origens = {r["origem"] for r in payload["rows"]}
        destinos = {r["destino"] for r in payload["rows"]}
        assert "A1_NREDUZ" in origens, "campo como origem deve aparecer"
        assert "A1_NREDUZ" in destinos, (
            f"campo como destino deveria aparecer (gatilho A1_COD->A1_NREDUZ). "
            f"destinos={destinos}"
        )


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

    def test_sx_status_schema_consistent_before_and_after_ingest(
        self,
        sx_project: Path,
        sx_csv_dir: Path,
        runner: CliRunner,
    ) -> None:
        """v0.3.22 — Bug #16 do QA round 2: schema instavel (2 keys quando
        ausente, 14 quando presente) forcava caller a branchear no
        --format json. Agora sempre o mesmo set de keys."""
        # Antes do ingest-sx
        runner.invoke(app, ["--root", str(sx_project), "init"])
        before = runner.invoke(
            app, ["--root", str(sx_project), "--format", "json", "sx-status"]
        )
        assert before.exit_code == 0
        keys_before = set(json.loads(before.stdout)["rows"][0].keys())

        # Depois do ingest-sx
        runner.invoke(
            app, ["--root", str(sx_project), "ingest-sx", str(sx_csv_dir)]
        )
        after = runner.invoke(
            app, ["--root", str(sx_project), "--format", "json", "sx-status"]
        )
        assert after.exit_code == 0
        keys_after = set(json.loads(after.stdout)["rows"][0].keys())

        # Mesmo schema nos 2 cenarios.
        assert keys_before == keys_after, (
            f"Schema sx-status inconsistente. Before: {keys_before}, "
            f"After: {keys_after}. Diff: {keys_before ^ keys_after}"
        )
        # Counts zerados na ausencia.
        before_row = json.loads(before.stdout)["rows"][0]
        # Migration 002 aplicada no init, entao sx_ingerido pode ser True.
        # Em ambos os casos as 11 tabelas SX devem ter int (count) — nao None.
        for tbl in ("tabelas", "campos", "indices", "gatilhos", "consultas"):
            assert isinstance(before_row[tbl], int), (
                f"{tbl} deve ser int sempre. before={before_row[tbl]!r}"
            )


class TestLintCrossFile:
    def test_lint_cross_file_sx009_detects_dot_F_dot_init(
        self, sx_project: Path, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.28 — Audit V4 #5 (MEDIA): SX-009 prometia detectar campo
        obrigatorio com X3_INIT='.F.' mas regex `\\b\\.F\\.\\b` nunca casava
        (`.` eh non-word, boundary impossivel). Drift silencioso entre
        catalogo e impl. Fix: lookarounds em vez de \\b."""
        csv_dir = tmp_path / "csv"
        csv_dir.mkdir()
        # SX3 com campo obrigatorio + X3_INIT = .F.
        (csv_dir / "sx3.csv").write_text(
            '"X3_ARQUIVO","X3_CAMPO","X3_TIPO","X3_TAMANHO","X3_DECIMAL",'
            '"X3_TITULO","X3_DESCRIC","X3_VALID","X3_VLDUSER","X3_WHEN",'
            '"X3_INIT","X3_OBRIGAT","D_E_L_E_T_"\n'
            '"SA1","A1_XOBRIG","L",1,0,"Obr","","","","",".F.","x",""\n',
            encoding="cp1252",
        )
        runner.invoke(app, ["--root", str(sx_project), "init"])
        db = sx_project / ".plugadvpl" / "index.db"
        ingest_sx(csv_dir, db)

        result = runner.invoke(
            app, ["--root", str(sx_project), "--format", "json", "lint", "--cross-file"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        sx009 = [r for r in payload["rows"] if r["regra_id"] == "SX-009"]
        assert any(r.get("funcao") == "A1_XOBRIG" for r in sx009), (
            f"SX-009 deveria disparar pra A1_XOBRIG (obrigatorio + init=.F.). "
            f"sx009={sx009}"
        )
        # Mensagem fix nao deve mais citar X3_RELACAO (#6 do audit V4)
        assert all("X3_RELACAO" not in r.get("sugestao_fix", "") for r in sx009)
        assert any("X3_INIT" in r.get("sugestao_fix", "") for r in sx009)

    def test_lint_cross_file_perf006_where_orderby_no_index(
        self,
        sx_project: Path,
        sx_csv_dir: Path,
        runner: CliRunner,
    ) -> None:
        """v0.3.27 — PERF-006 (info): WHERE/ORDER BY em coluna que NAO esta
        em nenhum indice SIX da tabela. Force full table scan.

        Fixture sx_synthetic/six.csv tem SA1 indexada por A1_COD e A1_NREDUZ.
        Adicionamos fonte com BeginSql usando A1_NOME (NAO indexado) em WHERE
        — deve disparar PERF-006. WHERE em A1_COD nao deve disparar.
        """
        # Reusa sx_csv_dir + adiciona fonte com SQL pra testar.
        src = sx_project
        bad_fonte = src / "QrySemIdx.prw"
        bad_fonte.write_bytes(
            b'#include "totvs.ch"\n'
            b'/*/{Protheus.doc} ZQry/*/\n'
            b'User Function ZQry()\n'
            b'    BeginSql Alias "QRY"\n'
            b'        SELECT A1_COD, A1_NOME FROM %table:SA1% SA1\n'
            b'         WHERE SA1.A1_NOME = %Exp:cNome%\n'
            b'           AND SA1.%notDel%\n'
            b'    EndSql\n'
            b'Return\n'
        )
        good_fonte = src / "QryComIdx.prw"
        good_fonte.write_bytes(
            b'#include "totvs.ch"\n'
            b'/*/{Protheus.doc} ZQryOk/*/\n'
            b'User Function ZQryOk()\n'
            b'    BeginSql Alias "QRY2"\n'
            b'        SELECT A1_COD FROM %table:SA1% SA1\n'
            b'         WHERE SA1.A1_COD = %Exp:cCod%\n'
            b'           AND SA1.%notDel%\n'
            b'    EndSql\n'
            b'Return\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])
        runner.invoke(app, ["--root", str(src), "ingest-sx", str(sx_csv_dir)])

        result = runner.invoke(
            app, ["--root", str(src), "--format", "json", "lint", "--cross-file"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        perf = [r for r in payload["rows"] if r["regra_id"] == "PERF-006"]
        # Esperado: pelo menos 1 finding pra A1_NOME (fonte ruim), 0 pra A1_COD.
        # Snippets dos findings devem ter "A1_NOME", e arquivos só com QrySemIdx.
        assert any("A1_NOME" in r.get("snippet", "") for r in perf), (
            f"PERF-006 deveria disparar pra A1_NOME (nao indexado). perf={perf}"
        )
        assert not any("QryComIdx" in r["arquivo"] for r in perf), (
            f"QryComIdx usa A1_COD (indexado), nao deve disparar. perf={perf}"
        )

    def test_lint_cross_file_persist_does_not_accumulate_mod003(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.28 — Audit V4 #1 (CRITICO): persist_cross_file_findings
        apagava so `regra_id LIKE 'SX-%'`. MOD-003 (v0.3.26) e PERF-006
        (v0.3.27) acumulavam duplicados a cada execucao."""
        src = tmp_path / "src"
        src.mkdir()
        # Fixture com grupo MOD-003 (4 _AppCalc*).
        (src / "AppHelper.prw").write_bytes(
            b'#include "totvs.ch"\n'
            b'/*/{Protheus.doc} _AppCalcSum/*/\n'
            b'Static Function _AppCalcSum(a, b)\n'
            b'    Return a + b\n'
            b'/*/{Protheus.doc} _AppCalcAvg/*/\n'
            b'Static Function _AppCalcAvg(a, b)\n'
            b'    Return (a + b) / 2\n'
            b'/*/{Protheus.doc} _AppCalcMax/*/\n'
            b'Static Function _AppCalcMax(a, b)\n'
            b'    Return Max(a, b)\n'
            b'/*/{Protheus.doc} _AppCalcMin/*/\n'
            b'Static Function _AppCalcMin(a, b)\n'
            b'    Return Min(a, b)\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])

        # 1a execucao
        runner.invoke(app, ["--root", str(src), "lint", "--cross-file"])
        # 2a execucao — deve substituir, nao acumular
        runner.invoke(app, ["--root", str(src), "lint", "--cross-file"])
        # 3a execucao — pra confirmar
        runner.invoke(app, ["--root", str(src), "lint", "--cross-file"])

        db = src / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(str(db))
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM lint_findings WHERE regra_id='MOD-003'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n == 1, (
            f"MOD-003 deveria ter exatamente 1 finding apos 3 execucoes "
            f"(persist deve substituir, nao acumular). Tem {n}."
        )

    def test_lint_cross_file_mod003_groups_static_functions_by_prefix(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """v0.3.26 — MOD-003 (info): grupos de Static Function com mesmo
        prefixo no mesmo arquivo sao candidatos a virar Class. Threshold: 3+
        functions com prefixo comum (>=3 chars) no mesmo arquivo dispara 1
        finding por grupo."""
        src = tmp_path / "src"
        src.mkdir()
        # 4 Static Function com prefixo `_AppCalc*` no mesmo arquivo → MOD-003.
        (src / "AppHelper.prw").write_bytes(
            b'#include "totvs.ch"\n'
            b'Static Function _AppCalcSum(a, b)\n'
            b'    Return a + b\n'
            b'Static Function _AppCalcAvg(a, b)\n'
            b'    Return (a + b) / 2\n'
            b'Static Function _AppCalcMax(a, b)\n'
            b'    Return Max(a, b)\n'
            b'Static Function _AppCalcMin(a, b)\n'
            b'    Return Min(a, b)\n'
            b'User Function ZAppEntry()\n'
            b'    Return _AppCalcSum(1, 2)\n'
        )
        # Arquivo com so 2 Statics mesmo prefixo — NAO atinge threshold.
        (src / "BelowThreshold.prw").write_bytes(
            b'#include "totvs.ch"\n'
            b'Static Function _XyzA()\n'
            b'    Return Nil\n'
            b'Static Function _XyzB()\n'
            b'    Return Nil\n'
        )
        runner.invoke(app, ["--root", str(src), "init"])
        runner.invoke(app, ["--root", str(src), "ingest"])

        result = runner.invoke(
            app, ["--root", str(src), "--format", "json", "lint", "--cross-file"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        mod003 = [r for r in payload["rows"] if r["regra_id"] == "MOD-003"]
        assert len(mod003) == 1, (
            f"Esperado 1 finding MOD-003 (grupo _AppCalc com 4 fns); "
            f"recebido {len(mod003)}: {mod003}"
        )
        # Arquivo do achado bate com AppHelper, NAO BelowThreshold.
        assert "AppHelper" in mod003[0]["arquivo"]

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
