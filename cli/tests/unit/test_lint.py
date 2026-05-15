"""Testes de cli/plugadvpl/parsing/lint.py.

Para cada uma das 13 regras: positivo (sinaliza) + negativo (não sinaliza).
Plus 2 integration tests (multiple violations sorted by linha; clean code = []).
"""
from __future__ import annotations

from typing import Any

from plugadvpl.parsing.lint import lint_source
from plugadvpl.parsing.parser import (
    add_function_ranges,
    extract_functions,
    extract_sql_embedado,
)


def _parsed_for(content: str, arquivo: str = "test.prw") -> dict[str, Any]:
    """Helper: monta um parsed dict mínimo com funcoes (com ranges) e sql_embedado.

    Os check functions consultam principalmente `funcoes` e `sql_embedado`; outros
    campos podem ficar em default.
    """
    funcs = add_function_ranges(extract_functions(content), content)
    sql_blocks = extract_sql_embedado(content)
    return {
        "arquivo": arquivo,
        "funcoes": funcs,
        "sql_embedado": sql_blocks,
    }


def _ids(findings: list[dict[str, Any]]) -> list[str]:
    return [f["regra_id"] for f in findings]


# --- BP-001: RecLock sem MsUnlock ---------------------------------------------


class TestBP001RecLockUnbalanced:
    def test_positive_reclock_without_msunlock(self) -> None:
        src = (
            "User Function MTA010()\n"
            "  DbSelectArea('SA1')\n"
            "  If RecLock('SA1', .F.)\n"
            "    SA1->A1_NOME := 'X'\n"
            "  EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp001 = [f for f in findings if f["regra_id"] == "BP-001"]
        assert len(bp001) == 1
        assert bp001[0]["severidade"] == "critical"
        assert bp001[0]["funcao"] == "MTA010"

    def test_negative_reclock_with_msunlock(self) -> None:
        src = (
            "User Function MTA011()\n"
            "  If RecLock('SA1', .F.)\n"
            "    SA1->A1_NOME := 'X'\n"
            "    MsUnlock()\n"
            "  EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-001" not in _ids(findings)

    def test_reclock_via_alias_arrow_also_counts(self) -> None:
        src = (
            "User Function MTA012()\n"
            "  SA1->(RecLock('SA1', .F.))\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-001" in _ids(findings)


# --- BP-002: BEGIN TRANSACTION sem END --------------------------------------


class TestBP002TransactionUnbalanced:
    def test_positive_begin_without_end(self) -> None:
        src = (
            "User Function MTA020()\n"
            "  BEGIN TRANSACTION\n"
            "    DbSelectArea('SA1')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp002 = [f for f in findings if f["regra_id"] == "BP-002"]
        assert len(bp002) == 1
        assert bp002[0]["severidade"] == "critical"

    def test_negative_begin_with_end(self) -> None:
        src = (
            "User Function MTA021()\n"
            "  BEGIN TRANSACTION\n"
            "    DbSelectArea('SA1')\n"
            "  END TRANSACTION\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002" not in _ids(findings)


# --- BP-003: MsExecAuto sem lMsErroAuto -------------------------------------


class TestBP003MsExecAutoNoCheck:
    def test_positive_no_check(self) -> None:
        src = (
            "User Function MTA030()\n"
            "  Local aDados := {}\n"
            "  MsExecAuto({|x, y| MATA010(x, y)}, aDados, 3)\n"
            "  // Nao verifica lMsErroAuto\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp003 = [f for f in findings if f["regra_id"] == "BP-003"]
        assert len(bp003) == 1
        assert bp003[0]["severidade"] == "error"

    def test_negative_with_check(self) -> None:
        src = (
            "User Function MTA031()\n"
            "  Local aDados := {}\n"
            "  MsExecAuto({|x, y| MATA010(x, y)}, aDados, 3)\n"
            "  If lMsErroAuto\n"
            "    Return .F.\n"
            "  EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-003" not in _ids(findings)


# --- BP-004: Pergunte sem MV_PAR* logo a seguir -----------------------------


class TestBP004PergunteNoCheck:
    def test_positive_pergunte_no_mv_par(self) -> None:
        src = (
            "User Function MTA040()\n"
            "  Pergunte('MTA040', .F.)\n"
            "  // Nao usa MV_PARx\n"
            "  Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp004 = [f for f in findings if f["regra_id"] == "BP-004"]
        assert len(bp004) == 1
        assert bp004[0]["severidade"] == "warning"

    def test_negative_pergunte_with_mv_par(self) -> None:
        src = (
            "User Function MTA041()\n"
            "  Pergunte('MTA041', .F.)\n"
            "  cFil := MV_PAR01\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-004" not in _ids(findings)


# --- BP-005: função com >6 parâmetros ---------------------------------------


class TestBP005TooManyParams:
    def test_positive_seven_params(self) -> None:
        src = (
            "Static Function _Fn7(a, b, c, d, e, f, g)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp005 = [f for f in findings if f["regra_id"] == "BP-005"]
        assert len(bp005) == 1
        assert bp005[0]["severidade"] == "warning"

    def test_negative_six_or_fewer(self) -> None:
        src = (
            "Static Function _Fn6(a, b, c, d, e, f)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-005" not in _ids(findings)


# --- BP-006: mistura RecLock + DbRLock/dbAppend() raw -----------------------


class TestBP006MixedReclockRawApi:
    def test_positive_reclock_and_dbappend_raw(self) -> None:
        src = (
            "User Function MTA060()\n"
            "  RecLock('SA1', .T.)\n"
            "  SA1->A1_NOME := 'X'\n"
            "  MsUnlock()\n"
            "  dbAppend()\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-006" in _ids(findings)

    def test_positive_reclock_and_dbrlock(self) -> None:
        src = (
            "User Function MTA061()\n"
            "  RecLock('SA1', .T.)\n"
            "  MsUnlock()\n"
            "  DbRLock(123)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-006" in _ids(findings)

    def test_negative_only_reclock(self) -> None:
        src = (
            "User Function MTA062()\n"
            "  RecLock('SA1', .T.)\n"
            "  MsUnlock()\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-006" not in _ids(findings)


# --- SEC-001: RpcSetEnv dentro de WSRESTFUL ---------------------------------


class TestSec001RpcSetEnvInRestful:
    def test_positive_rpcsetenv_in_wsrestful(self) -> None:
        src = (
            "CLASS API_Clientes FROM WSRESTFUL DESCRIPTION 'API'\n"
            "  METHOD GetClientes()\n"
            "ENDCLASS\n"
            "METHOD GetClientes() CLASS API_Clientes\n"
            "  RpcSetEnv('99', '01')\n"
            "Return Self\n"
        )
        findings = lint_source(_parsed_for(src), src)
        # Nota: classe declarada acima — o RpcSetEnv aqui está FORA do bloco
        # CLASS...ENDCLASS. Inserir RpcSetEnv DENTRO:
        src2 = (
            "CLASS API_Clientes FROM WSRESTFUL DESCRIPTION 'API'\n"
            "  Data lOk\n"
            "  RpcSetEnv('99', '01')\n"
            "ENDCLASS\n"
        )
        findings2 = lint_source(_parsed_for(src2), src2)
        sec001 = [f for f in findings2 if f["regra_id"] == "SEC-001"]
        assert len(sec001) == 1
        assert sec001[0]["severidade"] == "critical"
        # Sanity: src original (fora da classe) NÃO deveria sinalizar SEC-001
        assert "SEC-001" not in _ids(findings)

    def test_negative_rpcsetenv_outside_wsrestful(self) -> None:
        src = (
            "User Function MTA070()\n"
            "  RpcSetEnv('99', '01')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-001" not in _ids(findings)


# --- SEC-002: User Function sem prefixo -------------------------------------


class TestSec002UserFunctionNoPrefix:
    def test_positive_no_prefix(self) -> None:
        src = "User Function Foo()\nReturn\n"
        findings = lint_source(_parsed_for(src), src)
        sec002 = [f for f in findings if f["regra_id"] == "SEC-002"]
        assert len(sec002) == 1
        assert sec002[0]["funcao"] == "FOO"

    def test_negative_pe_pattern(self) -> None:
        # MTA010 casa com ^[A-Z]{2,4}\d{2,4}[A-Z_]*$
        src = "User Function MTA010()\nReturn\n"
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-002" not in _ids(findings)

    def test_negative_client_prefix(self) -> None:
        src = "User Function MGFFOO()\nReturn\n"
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-002" not in _ids(findings)


# --- PERF-001: SELECT * ------------------------------------------------------


class TestPerf001SelectStar:
    def test_positive_select_star(self) -> None:
        src = (
            "User Function MGFP01()\n"
            "  TCQuery('SELECT * FROM SA1010')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        perf001 = [f for f in findings if f["regra_id"] == "PERF-001"]
        assert len(perf001) == 1
        assert perf001[0]["severidade"] == "warning"

    def test_negative_explicit_columns(self) -> None:
        src = (
            "User Function MGFP02()\n"
            "  TCQuery('SELECT A1_COD FROM SA1010 WHERE %notDel% AND SA1010.A1_FILIAL = %xfilial:SA1%')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-001" not in _ids(findings)


# --- PERF-002: sem %notDel% --------------------------------------------------


class TestPerf002NoNotDel:
    def test_positive_no_notdel_on_protheus_table(self) -> None:
        src = (
            "User Function MGFP10()\n"
            "  TCQuery('SELECT A1_COD FROM SA1010 WHERE A1_COD = X')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        perf002 = [f for f in findings if f["regra_id"] == "PERF-002"]
        assert len(perf002) == 1
        assert perf002[0]["severidade"] == "error"

    def test_negative_with_notdel(self) -> None:
        src = (
            "User Function MGFP11()\n"
            "  TCQuery('SELECT A1_COD FROM SA1010 WHERE %notDel% AND %xfilial:SA1%')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-002" not in _ids(findings)


# --- PERF-003: sem %xfilial% -------------------------------------------------


class TestPerf003NoXfilial:
    def test_positive_no_xfilial_on_protheus_table(self) -> None:
        src = (
            "User Function MGFP20()\n"
            "  TCQuery('SELECT A1_COD FROM SA1010 WHERE %notDel%')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        perf003 = [f for f in findings if f["regra_id"] == "PERF-003"]
        assert len(perf003) == 1
        assert perf003[0]["severidade"] == "error"

    def test_negative_with_xfilial(self) -> None:
        src = (
            "User Function MGFP21()\n"
            "  TCQuery('SELECT A1_COD FROM SA1010 WHERE %notDel% AND %xfilial:SA1%')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-003" not in _ids(findings)


# --- MOD-001: ConOut em vez de FwLogMsg -------------------------------------


class TestMod001ConOut:
    def test_positive_conout(self) -> None:
        src = (
            "User Function MGFM01()\n"
            "  ConOut('debug aqui')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        mod001 = [f for f in findings if f["regra_id"] == "MOD-001"]
        assert len(mod001) == 1
        assert mod001[0]["severidade"] == "warning"

    def test_negative_fwlogmsg(self) -> None:
        src = (
            "User Function MGFM02()\n"
            "  FwLogMsg('DEBUG', 'msg', 'service', 'cat')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-001" not in _ids(findings)


# --- MOD-002: PUBLIC declaration --------------------------------------------


class TestMod002Public:
    def test_positive_public(self) -> None:
        src = (
            "User Function MGFM10()\n"
            "  PUBLIC cGlobal := ''\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        mod002 = [f for f in findings if f["regra_id"] == "MOD-002"]
        assert len(mod002) == 1
        assert mod002[0]["severidade"] == "warning"

    def test_negative_local_or_static(self) -> None:
        src = (
            "User Function MGFM11()\n"
            "  Local cLocal := ''\n"
            "  Static cStat := ''\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-002" not in _ids(findings)


# --- Integration -------------------------------------------------------------


class TestLintSourceIntegration:
    def test_multiple_violations_sorted_by_line(self) -> None:
        src = (
            "User Function Foo()\n"  # SEC-002 (no prefix) on linha 1
            "  ConOut('a')\n"  # MOD-001 on linha 2
            "  PUBLIC cX := ''\n"  # MOD-002 on linha 3
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        # Garante ordenação por linha
        linhas = [f["linha"] for f in findings]
        assert linhas == sorted(linhas)
        ids = _ids(findings)
        assert "SEC-002" in ids
        assert "MOD-001" in ids
        assert "MOD-002" in ids

    def test_clean_code_returns_empty(self) -> None:
        # v0.3.24: BP-007 ativa exige Protheus.doc — adicionado pra manter
        # contrato "clean code = zero findings".
        src = (
            "/*/{Protheus.doc} MGFC01\n"
            "@type function\n"
            "/*/\n"
            "User Function MGFC01(a, b)\n"
            "  Local cMsg := 'ok'\n"
            "  FwLogMsg('INFO', cMsg, 'svc', 'cat')\n"
            "  If RecLock('SA1', .F.)\n"
            "    SA1->A1_NOME := cMsg\n"
            "    MsUnlock()\n"
            "  EndIf\n"
            "  BEGIN TRANSACTION\n"
            "    DbCommit()\n"
            "  END TRANSACTION\n"
            "  TCQuery('SELECT A1_COD FROM SA1010 WHERE %notDel% AND %xfilial:SA1%')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert findings == []


# --- BP-008: shadowing de variável reservada framework ----------------------


class TestBP008ShadowedReserved:
    """BP-008 (critical): Local/Static/Private/Public com nome de reservada TOTVS."""

    def test_positive_local_cFilAnt(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    Local cFilAnt := '01'\n"   # shadow!
            "    ConOut(cFilAnt)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp008 = [f for f in findings if f["regra_id"] == "BP-008"]
        assert len(bp008) == 1
        assert bp008[0]["severidade"] == "critical"
        assert "cFilAnt" in bp008[0]["snippet"] or "cFilAnt" in bp008[0]["sugestao_fix"]

    def test_positive_static_cEmpAnt_case_insensitive(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    static CEMPANT := ''\n"   # ADVPL is case-insensitive
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)

    def test_positive_private_lMsErroAuto(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    Private lMsErroAuto := .F.\n"   # reserved exec auto flag
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)

    def test_positive_public_PARAMIXB(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    Public PARAMIXB := {}\n"   # PE arg array, never override
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)

    def test_positive_multi_var_decl(self) -> None:
        """Local cVar1, cFilAnt, cVar2 := ... — BP-008 pega o cFilAnt no meio."""
        src = (
            "User Function XYZBad()\n"
            "    Local cVar1, cFilAnt, cVar2 := 'x'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)

    def test_positive_tlpp_typed_decl(self) -> None:
        """Local cFilAnt as character — TLPP type annotation, ainda shadow."""
        src = (
            "User Function XYZBad()\n"
            "    Local cFilAnt as character\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)

    def test_negative_similar_name(self) -> None:
        """cFilAntiga não é cFilAnt — não deve match."""
        src = (
            "User Function XYZGood()\n"
            "    Local cFilAntiga := '01'\n"
            "    Local cFilAntx   := '02'\n"
            "    Local nProgAntx  := 0\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" not in _ids(findings)

    def test_negative_reserved_in_string(self) -> None:
        """'cFilAnt' dentro de string literal não deve match."""
        src = (
            "User Function XYZGood()\n"
            "    Local cMsg := 'cFilAnt is reserved'\n"
            "    ConOut(cMsg)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" not in _ids(findings)

    def test_negative_reserved_in_comment(self) -> None:
        """// Local cFilAnt não deve match."""
        src = (
            "User Function XYZGood()\n"
            "    // Local cFilAnt — comentario explicativo\n"
            "    Local cMinhaVar := '01'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" not in _ids(findings)

    def test_negative_use_without_declare(self) -> None:
        """Usar cFilAnt sem declarar como Local NÃO é shadow — é uso correto."""
        src = (
            "User Function XYZGood()\n"
            "    ConOut('Filial atual: ' + cFilAnt)\n"
            "    DbSelectArea('SA1')\n"
            "    DbSeek(xFilial('SA1') + cFilAnt)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" not in _ids(findings)

    def test_positive_reports_correct_line(self) -> None:
        """Snippet/linha apontam pra linha correta."""
        src = (
            "User Function XYZBad()\n"   # 1
            "    Local cVarOk := '01'\n" # 2
            "    Local cEmpAnt := '99'\n"  # 3 — shadow aqui
            "Return\n"                   # 4
        )
        findings = lint_source(_parsed_for(src), src)
        bp008 = [f for f in findings if f["regra_id"] == "BP-008"]
        assert len(bp008) == 1
        assert bp008[0]["linha"] == 3

    # --- v0.3.10 audit: novas reservadas adicionadas ---

    def test_positive_dDataBase_shadow(self) -> None:
        """dDataBase é a data sistema — shadowing dela quebra qualquer date logic."""
        src = (
            "User Function XYZBad()\n"
            "    Local dDataBase := Date() + 30\n"   # shadow CRITICO
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)

    def test_positive_INCLUI_ALTERA_shadow(self) -> None:
        """INCLUI/ALTERA são flags MVC preenchidas pelo framework."""
        src = (
            "User Function XYZBad()\n"
            "    Local INCLUI := .T.\n"
            "    Local ALTERA := .F.\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp008 = [f for f in findings if f["regra_id"] == "BP-008"]
        assert len(bp008) == 2

    def test_positive_cFunName_cFunBkp_shadow(self) -> None:
        """cFunName/cFunBkp — backup de FunName(), reservadas framework."""
        src = (
            "User Function XYZBad()\n"
            "    Local cFunName := 'XYZ'\n"
            "    Local cFunBkp := FunName()\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp008 = [f for f in findings if f["regra_id"] == "BP-008"]
        assert len(bp008) == 2

    def test_positive_lAutoErrNoFile_shadow(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    Private lAutoErrNoFile := .T.\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-008" in _ids(findings)


# --- PERF-005: RecCount() para checar existência ---------------------------


class TestPERF005ReccountForExistence:
    """PERF-005 (warning): RecCount() > 0 / >= 1 / != 0 / <> 0 — use !Eof()."""

    def test_positive_reccount_gt_zero(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    DbSelectArea('SA1')\n"
            "    DbGoTop()\n"
            "    If RecCount() > 0\n"   # full scan
            "        ConOut('tem')\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        perf = [f for f in findings if f["regra_id"] == "PERF-005"]
        assert len(perf) == 1
        assert perf[0]["severidade"] == "warning"

    def test_positive_reccount_gte_one(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    If RecCount() >= 1\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" in _ids(findings)

    def test_positive_reccount_neq_zero(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    If RecCount() != 0\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" in _ids(findings)

    def test_positive_reccount_diff_legacy(self) -> None:
        """ADVPL legacy != é <> — também detecta."""
        src = (
            "User Function XYZBad()\n"
            "    If RecCount() <> 0\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" in _ids(findings)

    def test_positive_alias_call(self) -> None:
        """SA1->(RecCount()) > 0 também é o anti-pattern."""
        src = (
            "User Function XYZBad()\n"
            "    If SA1->(RecCount()) > 0\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" in _ids(findings)

    def test_negative_reccount_specific_threshold(self) -> None:
        """RecCount() > 100 (limite de business, intencional) NÃO é PERF-005."""
        src = (
            "User Function XYZGood()\n"
            "    If RecCount() > 100\n"
            "        ConOut('muitos')\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" not in _ids(findings)

    def test_negative_reccount_assignment(self) -> None:
        """nTotal := RecCount() — só armazena, não checa existência."""
        src = (
            "User Function XYZGood()\n"
            "    Local nTotal := RecCount()\n"
            "    ConOut(cValToChar(nTotal))\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" not in _ids(findings)

    def test_negative_reccount_in_string(self) -> None:
        """'RecCount() > 0' dentro de string não match."""
        src = (
            "User Function XYZGood()\n"
            "    Local cMsg := 'Use RecCount() > 0 com cuidado'\n"
            "    ConOut(cMsg)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" not in _ids(findings)

    def test_negative_reccount_in_comment(self) -> None:
        """// RecCount() > 0 — comentário não match."""
        src = (
            "User Function XYZGood()\n"
            "    // RecCount() > 0 era usado em codigo legado\n"
            "    If !Eof()\n"
            "        ConOut('tem')\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" not in _ids(findings)

    def test_positive_reports_correct_line(self) -> None:
        src = (
            "User Function XYZBad()\n"   # 1
            "    DbSelectArea('SA1')\n"  # 2
            "    DbGoTop()\n"             # 3
            "    If RecCount() > 0\n"     # 4 — match
            "    EndIf\n"                 # 5
            "Return\n"                    # 6
        )
        findings = lint_source(_parsed_for(src), src)
        perf = [f for f in findings if f["regra_id"] == "PERF-005"]
        assert len(perf) == 1
        assert perf[0]["linha"] == 4
        assert "Eof" in perf[0]["sugestao_fix"]

    # --- v0.3.10 audit: LastRec adicionada (idêntica a RecCount per TDN) ---

    def test_positive_lastrec_gt_zero(self) -> None:
        """LastRec é idêntica a RecCount, mesmo anti-pattern."""
        src = (
            "User Function XYZBad()\n"
            "    If LastRec() > 0\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" in _ids(findings)

    def test_positive_lastrec_alias_call(self) -> None:
        src = (
            "User Function XYZBad()\n"
            "    If SA1->(LastRec()) > 0\n"
            "    EndIf\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" in _ids(findings)

    def test_negative_lastrec_assignment(self) -> None:
        src = (
            "User Function XYZGood()\n"
            "    Local nUlt := LastRec()\n"
            "    ConOut(cValToChar(nUlt))\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-005" not in _ids(findings)


# --- SEC-005: uso de função TOTVS restrita -----------------------------------


class TestSEC005RestrictedFunctionCall:
    """SEC-005 (critical): chamada a função catalogada em funcoes_restritas (lookup)."""

    def test_positive_staticcall_blocked(self) -> None:
        """StaticCall é bloqueada desde 12.1.33 — uso explícito é critical."""
        src = (
            "User Function XYZBad()\n"
            "    StaticCall('SOMEFONTE', 'someFunc', 'arg')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        sec = [f for f in findings if f["regra_id"] == "SEC-005"]
        assert len(sec) == 1
        assert sec[0]["severidade"] == "critical"
        assert "StaticCall" in sec[0]["sugestao_fix"] or "StaticCall" in sec[0]["snippet"]

    def test_positive_case_insensitive(self) -> None:
        """ADVPL é case-insensitive — STATICCALL e staticcall match igual."""
        src = (
            "User Function XYZBad()\n"
            "    STATICCALL('A', 'B')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" in _ids(findings)

    def test_positive_internal_function(self) -> None:
        """PTInternal é uma das funções internas blocked."""
        src = (
            "User Function XYZBad()\n"
            "    nVal := PTInternal(1, 2)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" in _ids(findings)

    def test_negative_user_function_call(self) -> None:
        """Chamada U_XYZFoo() é custom, não restrita."""
        src = (
            "User Function XYZGood()\n"
            "    U_XYZHelper('arg')\n"
            "    Local x := MyFunction()\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" not in _ids(findings)

    def test_negative_native_function(self) -> None:
        """Função built-in TOTVS pública (DbSelectArea, AllTrim) NÃO é restrita."""
        src = (
            "User Function XYZGood()\n"
            "    DbSelectArea('SA1')\n"
            "    DbSetOrder(1)\n"
            "    DbSeek(xFilial('SA1') + cCod)\n"
            "    Local cNome := AllTrim(SA1->A1_NOME)\n"
            "    ConOut(cNome)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" not in _ids(findings)

    def test_negative_function_definition(self) -> None:
        """`User Function StaticCall()` definindo é a própria função custom — não match."""
        src = (
            "User Function StaticCall()\n"   # nome custom homônimo, não invoke
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        # No call to StaticCall here — só a definição; não deve disparar
        assert "SEC-005" not in _ids(findings)

    def test_negative_method_call(self) -> None:
        """oObj:StaticCall() — method call em objeto, não chamada de função."""
        src = (
            "User Function XYZGood()\n"
            "    Local oObj := MyClass():New()\n"
            "    oObj:StaticCall()\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" not in _ids(findings)

    def test_negative_in_string(self) -> None:
        src = (
            "User Function XYZGood()\n"
            "    Local cMsg := 'Nao use StaticCall em codigo novo'\n"
            "    ConOut(cMsg)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" not in _ids(findings)

    def test_negative_in_comment(self) -> None:
        src = (
            "User Function XYZGood()\n"
            "    // StaticCall foi removido em 2024\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-005" not in _ids(findings)

    def test_positive_includes_alternative_in_fix(self) -> None:
        """Se a entrada do catálogo tem `alternativa`, sugestao_fix deve mencionar."""
        src = (
            "User Function XYZBad()\n"
            "    StaticCall('A', 'B', 'C')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        sec = [f for f in findings if f["regra_id"] == "SEC-005"]
        # StaticCall tem alternativa cadastrada
        assert any("User Function" in s["sugestao_fix"] or "TLPP" in s["sugestao_fix"]
                   for s in sec)


# --- MOD-004: AxCadastro/Modelo2/Modelo3 em vez de MVC -----------------------


class TestMOD004LegacyCadastro:
    """MOD-004 (info): chamada a AxCadastro/Modelo2/Modelo3 (legacy, deve migrar pra MVC)."""

    def test_positive_axcadastro(self) -> None:
        src = (
            "User Function ZCAD()\n"
            "    AxCadastro('SA1', 'Cadastro')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        mod = [f for f in findings if f["regra_id"] == "MOD-004"]
        assert len(mod) == 1
        assert mod[0]["severidade"] == "info"
        assert "AxCadastro" in mod[0]["sugestao_fix"] or "MVC" in mod[0]["sugestao_fix"]

    def test_positive_modelo2(self) -> None:
        src = (
            "User Function ZCAD2()\n"
            "    Modelo2('Titulo', aCabec, aRodape, aGd, 3)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        mod = [f for f in findings if f["regra_id"] == "MOD-004"]
        assert len(mod) == 1
        assert "Modelo2" in mod[0]["sugestao_fix"] or "MVC" in mod[0]["sugestao_fix"]

    def test_positive_modelo3(self) -> None:
        src = (
            "User Function ZCAD3()\n"
            "    Modelo3('Titulo', 'SC5', 'SC6', aCpoEnchoice, 'cLinOk', 'cTudOk', 3, 3, 'cFieldOk')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" in _ids(findings)

    def test_positive_case_insensitive(self) -> None:
        src = (
            "User Function ZCAD()\n"
            "    AXCADASTRO('SA1', 'Cad')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" in _ids(findings)

    def test_positive_multiple_calls_separate_findings(self) -> None:
        src = (
            "User Function ZCAD()\n"
            "    AxCadastro('SA1', 'A')\n"
            "    Modelo2('B', a, b, c, 3)\n"
            "    Modelo3('C', 'SC5', 'SC6', a, 'l', 't', 3, 3, 'f')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        mod = [f for f in findings if f["regra_id"] == "MOD-004"]
        assert len(mod) == 3

    def test_negative_in_string(self) -> None:
        src = (
            "User Function ZGood()\n"
            "    Local cMsg := 'Substituiu AxCadastro por MVC em 2024'\n"
            "    ConOut(cMsg)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" not in _ids(findings)

    def test_negative_in_comment(self) -> None:
        src = (
            "User Function ZGood()\n"
            "    // AxCadastro foi removido — agora usa MVC\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" not in _ids(findings)

    def test_negative_function_definition(self) -> None:
        """User Function AxCadastro() definindo — não é uso, é definição própria."""
        src = (
            "User Function AxCadastro()\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        # Definição da própria função — não conta como uso do legacy
        assert "MOD-004" not in _ids(findings)

    def test_negative_similar_name(self) -> None:
        src = (
            "User Function ZGood()\n"
            "    Local x := AxCadastrox('arg')\n"
            "    Local y := MyModelo2('arg')\n"
            "    Local z := Modelo30('arg')\n"   # 30, not 3 — não match
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" not in _ids(findings)

    def test_negative_method_call(self) -> None:
        """oObj:AxCadastro() — method call, não chamada de função."""
        src = (
            "User Function ZGood()\n"
            "    Local oObj := MyClass():New()\n"
            "    oObj:Modelo3('arg')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" not in _ids(findings)

    def test_positive_reports_correct_line_and_function(self) -> None:
        src = (
            "User Function ZCAD()\n"      # 1
            "    Local cTit := 'Test'\n"  # 2
            "    AxCadastro('SA1', cTit)\n"   # 3
            "Return\n"                    # 4
        )
        findings = lint_source(_parsed_for(src), src)
        mod = [f for f in findings if f["regra_id"] == "MOD-004"]
        assert len(mod) == 1
        assert mod[0]["linha"] == 3

    # --- v0.3.10 audit: MsNewGetDados deprecada desde 12.1.17 ---

    def test_positive_msnewgetdados(self) -> None:
        """MsNewGetDados — classe deprecada, TOTVS recomenda MVC AddGrid."""
        src = (
            "User Function ZGrid()\n"
            "    Local oGrid := MsNewGetDados():New(0, 0, 200, 400, 0)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        mod = [f for f in findings if f["regra_id"] == "MOD-004"]
        assert len(mod) == 1
        assert "MsNewGetDados" in mod[0]["sugestao_fix"] or "12.1.17" in mod[0]["sugestao_fix"]

    def test_negative_msnewgetdados_in_string(self) -> None:
        src = (
            "User Function ZGood()\n"
            "    Local cMsg := 'MsNewGetDados foi removida em 12.1.17'\n"
            "    ConOut(cMsg)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "MOD-004" not in _ids(findings)


# --- PERF-004: string concat com +/+= em loop --------------------------------


class TestPERF004StringConcatInLoop:
    """PERF-004 (warning): cVar += ou cVar := cVar + ... dentro de While/For (O(n²))."""

    def test_positive_compound_assign_in_while(self) -> None:
        src = (
            "User Function ZBad()\n"
            "    Local cBuf := ''\n"
            "    Local nI := 1\n"
            "    While nI < 1000\n"
            "        cBuf += 'linha ' + cValToChar(nI)\n"   # O(n²)!
            "        nI++\n"
            "    EndDo\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        perf = [f for f in findings if f["regra_id"] == "PERF-004"]
        assert len(perf) == 1
        assert perf[0]["severidade"] == "warning"

    def test_positive_compound_assign_in_for(self) -> None:
        src = (
            "User Function ZBad()\n"
            "    Local cMsg := ''\n"
            "    Local nI\n"
            "    For nI := 1 To 100\n"
            "        cMsg += 'item' + cValToChar(nI) + Chr(13)\n"
            "    Next nI\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" in _ids(findings)

    def test_positive_long_form_in_while(self) -> None:
        """cVar := cVar + ... (long form, mesmo nome via backreference)."""
        src = (
            "User Function ZBad()\n"
            "    Local cAcc := ''\n"
            "    While !Eof()\n"
            "        cAcc := cAcc + AllTrim(SA1->A1_NOME) + ';'\n"
            "        DbSkip()\n"
            "    EndDo\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" in _ids(findings)

    def test_positive_nested_loop(self) -> None:
        """Concat no loop interno deve disparar."""
        src = (
            "User Function ZBad()\n"
            "    Local cOut := ''\n"
            "    Local i, j\n"
            "    For i := 1 To 10\n"
            "        For j := 1 To 10\n"
            "            cOut += cValToChar(i*j)\n"
            "        Next j\n"
            "    Next i\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" in _ids(findings)

    def test_positive_multiple_concats_separate_findings(self) -> None:
        src = (
            "User Function ZBad()\n"
            "    Local cA := ''\n"
            "    Local cB := ''\n"
            "    While !Eof()\n"
            "        cA += AllTrim(SA1->A1_NOME)\n"
            "        cB += AllTrim(SA1->A1_CGC)\n"
            "        DbSkip()\n"
            "    EndDo\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        perf = [f for f in findings if f["regra_id"] == "PERF-004"]
        assert len(perf) == 2

    def test_negative_numeric_accumulator(self) -> None:
        """nTotal += 1 — accumulator numérico, não string concat."""
        src = (
            "User Function ZGood()\n"
            "    Local nTotal := 0\n"
            "    Local nI\n"
            "    For nI := 1 To 100\n"
            "        nTotal += nI\n"   # nTotal começa com n, hungarian = numeric
            "    Next nI\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" not in _ids(findings)

    def test_negative_concat_outside_loop(self) -> None:
        """cVar += fora de loop (init ou single-shot) NÃO é PERF-004."""
        src = (
            "User Function ZGood()\n"
            "    Local cMsg := 'header'\n"
            "    cMsg += ' - body'\n"   # 1 concat, fora de loop, OK
            "    cMsg += ' - footer'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" not in _ids(findings)

    def test_negative_concat_in_string(self) -> None:
        src = (
            "User Function ZGood()\n"
            "    Local cMsg := 'cVar += \"x\" eh anti-pattern'\n"
            "    ConOut(cMsg)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" not in _ids(findings)

    def test_negative_concat_in_comment(self) -> None:
        src = (
            "User Function ZGood()\n"
            "    // While ... cBuf += deve ser refatorado\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" not in _ids(findings)

    def test_negative_long_form_different_vars(self) -> None:
        """cBuf := cFoo + cBar (não é o mesmo nome dos dois lados — não accumulator)."""
        src = (
            "User Function ZGood()\n"
            "    Local cBuf := ''\n"
            "    While !Eof()\n"
            "        cBuf := cFoo + cBar\n"   # diferente, não accumulator
            "        DbSkip()\n"
            "    EndDo\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "PERF-004" not in _ids(findings)

    def test_positive_reports_correct_line(self) -> None:
        src = (
            "User Function ZBad()\n"      # 1
            "    Local cBuf := ''\n"      # 2
            "    Local nI\n"              # 3
            "    For nI := 1 To 10\n"     # 4
            "        cBuf += '.'\n"       # 5 — match
            "    Next nI\n"               # 6
            "Return\n"                    # 7
        )
        findings = lint_source(_parsed_for(src), src)
        perf = [f for f in findings if f["regra_id"] == "PERF-004"]
        assert len(perf) == 1
        assert perf[0]["linha"] == 5


# --- SEC-004: credenciais hardcoded em codigo fonte ---------------------------


class TestSEC004HardcodedCreds:
    """SEC-004 (warning): credenciais hardcoded em RpcSetEnv/PREPARE ENV/SMTPAuth/Encode64."""

    def test_positive_rpcsetenv_with_user_pwd_literals(self) -> None:
        """RpcSetEnv com user e pwd em strings literais (caso classico)."""
        src = (
            "User Function ZJob()\n"
            '    RpcSetEnv("01", "0101", "admin", "totvs", "FAT")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        sec = [f for f in findings if f["regra_id"] == "SEC-004"]
        assert len(sec) == 1
        assert sec[0]["severidade"] == "warning"
        assert sec[0]["linha"] == 2

    def test_positive_rpcsetenv_default_pwd_totvs(self) -> None:
        """Senha default 'totvs' no slot 4 do RpcSetEnv eh sempre flagged."""
        src = (
            "User Function ZJob()\n"
            '    RpcSetEnv("01","01","fulano","totvs")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" in _ids(findings)

    def test_positive_prepare_environment_with_password(self) -> None:
        """PREPARE ENVIRONMENT ... PASSWORD '<literal>' eh hardcoded creds."""
        src = (
            "User Function ZJob()\n"
            "    PREPARE ENVIRONMENT EMPRESA '01' FILIAL '01' "
            "USER 'admin' PASSWORD 'totvs' MODULO 'FAT'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" in _ids(findings)

    def test_positive_smtpauth_literal(self) -> None:
        """oMail:SMTPAuth('user','pwd') com literais."""
        src = (
            "User Function ZMail()\n"
            "    Local oMail := TMailManager():New()\n"
            '    oMail:SMTPAuth("noreply@x.com","minhasenha123")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" in _ids(findings)

    def test_positive_basic_auth_encode64(self) -> None:
        """Encode64('user:pwd') = Basic Auth literal."""
        src = (
            "User Function ZApi()\n"
            '    Local cAuth := "Basic " + Encode64("apiuser:abc123")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" in _ids(findings)

    # --- Negativos ---

    def test_negative_rpcsetenv_with_supergetmv(self) -> None:
        """SuperGetMV no slot da senha eh leitura segura do SX6 — NAO flag."""
        src = (
            "User Function ZJob()\n"
            "    Local cUser := SuperGetMV('MV_XYZUSR',.F.,'')\n"
            "    Local cPwd  := SuperGetMV('MV_XYZPWD',.F.,'')\n"
            "    RpcSetEnv('01','01', cUser, cPwd, 'FAT')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" not in _ids(findings)

    def test_negative_rpcsetenv_empty_user_pwd(self) -> None:
        """RpcSetEnv('01','01','','') usa admin default por convencao — nao eh leak."""
        src = (
            "User Function ZJob()\n"
            "    RpcSetEnv('01','01','','','FAT')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" not in _ids(findings)

    def test_negative_in_comment(self) -> None:
        """Comentario citando exemplo nao deve disparar."""
        src = (
            "User Function ZJob()\n"
            '    // Exemplo errado: RpcSetEnv("01","01","admin","totvs")\n'
            "    RpcSetEnv('01','01', GetMV('MV_USR'), GetMV('MV_PWD'))\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" not in _ids(findings)

    def test_positive_prepare_environment_multiline_continuation(self) -> None:
        """v0.3.22 — Bug #3 do QA round 2: PREPARE ENVIRONMENT em multiplas
        linhas via `;` (continuation ADVPL) escapava o detector porque o
        regex usava `[^\\n]*?` que para no `\\n` real."""
        src = (
            "User Function ZJob()\n"
            "    PREPARE ENVIRONMENT EMPRESA cEmp FILIAL cFil ;\n"
            "        USER 'admin' ;\n"
            "        PASSWORD 'minhasenha' ;\n"
            "        MODULO 'FAT'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" in _ids(findings), (
            "PREPARE ENV multilinha com PASSWORD literal deve disparar SEC-004"
        )

    def test_positive_rpcsetenv_var_emp_fil_literal_user_pwd(self) -> None:
        """v0.3.21 — Bug #4 do QA round 2: caso real comum eh emp/fil virem
        de variaveis (cEmp, cFil, vindos de parametro/argv) e user/pwd
        ficarem literais hardcoded. Antes do fix o regex exigia literal nos
        4 slots — o caso mais leak (var nos 2 primeiros) escapava."""
        src = (
            "User Function ZJob(cEmp, cFil)\n"
            '    RpcSetEnv(cEmp, cFil, "admin", "totvs", "FAT")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-004" in _ids(findings), (
            "RpcSetEnv com user/pwd literal deve disparar mesmo com var nos slots 1+2"
        )


# --- SEC-003: PII / dados sensiveis em logs -----------------------------------


class TestSEC003PIIInLogs:
    """SEC-003 (warning): variavel/campo PII passado a ConOut/FwLogMsg/MsgLog."""

    def test_positive_csenha_in_conout(self) -> None:
        """cSenha sendo logado eh leak claro."""
        src = (
            "User Function ZAuth()\n"
            "    Local cSenha := SuperGetMV('MV_XYZ',.F.,'')\n"
            '    ConOut("Senha=" + cSenha)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        sec = [f for f in findings if f["regra_id"] == "SEC-003"]
        assert len(sec) == 1
        assert sec[0]["severidade"] == "warning"

    def test_positive_ccpf_in_fwlogmsg(self) -> None:
        """cCpf passado a FwLogMsg eh PII em log."""
        src = (
            "User Function ZCli()\n"
            "    Local cCpf := M->A1_CGC\n"
            '    FwLogMsg("INFO","TX","GRP","CAT","STEP","M","cpf="+cCpf)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" in _ids(findings)

    def test_positive_a1_cpf_field_in_log(self) -> None:
        """Campo SX3 sensivel (A1_CGC/A1_CPF) concatenado em log."""
        src = (
            "User Function ZCli()\n"
            '    ConOut("CPF=" + SA1->A1_CGC)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" in _ids(findings)

    def test_positive_cpf_literal_in_log(self) -> None:
        """CPF formatado literal em log (debug esquecido)."""
        src = (
            "User Function ZDbg()\n"
            '    ConOut("Testando com CPF 123.456.789-00")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" in _ids(findings)

    # --- Negativos ---

    def test_negative_safe_log_no_pii(self) -> None:
        """ConOut com mensagem generica — sem PII."""
        src = (
            "User Function ZOk()\n"
            '    ConOut("Processo iniciado em " + DToC(Date()))\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings)

    def test_negative_msgbox_is_ui_not_log(self) -> None:
        """MsgInfo/MsgBox/Aviso eh UI, nao log — nao deve disparar SEC-003.

        Esses sao mostrados em modal pra usuario autenticado, nao vao pro
        console.log do servidor. (Outro tipo de exposicao, fora do escopo SEC-003.)
        """
        src = (
            "User Function ZAuth()\n"
            "    Local cSenha := 'x'\n"
            '    MsgInfo("Senha incorreta: " + cSenha)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings)

    def test_negative_label_only_no_var(self) -> None:
        """Label literal sem variavel PII."""
        src = (
            "User Function ZAuth()\n"
            '    ConOut("CPF invalido")\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings)

    def test_positive_a2_fornecedor_field_in_log(self) -> None:
        """v0.3.22 — Bug #5 do QA round 2: A2_* (fornecedores) eh equivalente
        PII a A1_* (clientes). Antes do fix nao era detectado."""
        src = (
            "User Function ZForn()\n"
            '    ConOut("CGC=" + SA2->A2_CGC)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" in _ids(findings), (
            "A2_CGC (fornecedor) eh PII equivalente a A1_CGC — deve disparar"
        )

    def test_positive_rh_funcionario_field_in_log(self) -> None:
        """RH_* (folha/dependentes) tambem PII."""
        src = (
            "User Function ZFolha()\n"
            '    ConOut("Dep CPF=" + SRH->RH_CPFDEP)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" in _ids(findings)

    def test_negative_help_is_ui_not_log(self) -> None:
        """v0.3.20 — Bug #1 do QA round 2: Help() em ADVPL eh dialogo modal de
        erro/validacao (igual MsgInfo), NAO log do servidor. Universal em MVC
        para validacao de campo (X3_VLDUSER, X7_REGRA). Antes do fix, qualquer
        Help( ,, 'Erro',, 'Cliente ' + cNome, 1, 0) disparava SEC-003."""
        src = (
            "User Function ZVld()\n"
            "    Local cCpf := M->A1_CGC\n"
            '    Help(,,"Erro",,"CPF invalido para " + cCpf, 1, 0)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings), (
            "Help() eh UI modal, nao log — nao deve disparar SEC-003"
        )

    def test_negative_var_passagem_not_password(self) -> None:
        """v0.3.20 — Bug #2 do QA round 2: regex `Pass\\w*` casava palavras
        comuns PT-BR como `cPassagem`, `cPasso`. Falso positivo massivo em
        projetos de turismo/TMS."""
        src = (
            "User Function ZTms()\n"
            "    Local cPassagem := 'BSB-GRU'\n"
            '    ConOut("Bilhete: " + cPassagem)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings), (
            "cPassagem nao eh password — regex curto Pass\\w* eh ambiguo demais"
        )

    def test_negative_var_pintar_not_pin(self) -> None:
        """`cPintar`, `cPintor` (verbo/profissao PT-BR) nao eh PIN."""
        src = (
            "User Function ZArt()\n"
            "    Local cPintar := 'paredes'\n"
            '    ConOut("Atividade: " + cPintar)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings)

    def test_negative_var_cardapio_not_card(self) -> None:
        """`cCardapio` (food-service PT-BR) nao eh credit card."""
        src = (
            "User Function ZRest()\n"
            "    Local cCardapio := 'Menu Almoco'\n"
            '    ConOut("Item: " + cCardapio)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" not in _ids(findings)

    def test_positive_password_long_form_still_works(self) -> None:
        """Garantia que apertar a regra de Pass nao quebra cPassword (forma longa)."""
        src = (
            "User Function ZAuth()\n"
            "    Local cPassword := 'admin123'\n"
            '    ConOut("Pwd=" + cPassword)\n'
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "SEC-003" in _ids(findings), (
            "cPassword (forma longa) ainda deve disparar SEC-003"
        )


# --- BP-007: funcao sem header Protheus.doc ----------------------------------


class TestBP007NoProtheusDoc:
    """BP-007 (info): funcao sem cabecalho Protheus.doc nas linhas anteriores."""

    def test_positive_user_function_without_doc(self) -> None:
        """User Function sem nenhum doc-comment antes — sinaliza."""
        src = (
            "User Function XYZNoDoc()\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp = [f for f in findings if f["regra_id"] == "BP-007"]
        assert len(bp) == 1
        assert bp[0]["severidade"] == "info"
        assert bp[0]["funcao"].upper() == "XYZNODOC"

    def test_positive_static_function_without_doc(self) -> None:
        """Static Function tambem deve ter doc."""
        src = (
            "Static Function helper()\n"
            "    Return Nil\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-007" in _ids(findings)

    def test_positive_method_without_doc(self) -> None:
        """Method tambem qualifica."""
        src = (
            "Method M1() Class A\n"
            "    Return Nil\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-007" in _ids(findings)

    def test_positive_multiple_undocumented_functions(self) -> None:
        """3 funcoes sem doc = 3 findings."""
        src = (
            "User Function ZA()\n"
            "    Return .T.\n"
            "Static Function helper()\n"
            "    Return Nil\n"
            "User Function ZB()\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp = [f for f in findings if f["regra_id"] == "BP-007"]
        assert len(bp) == 3

    # --- Negativos ---

    def test_negative_protheus_doc_present(self) -> None:
        """User Function com header Protheus.doc completo — nao sinaliza."""
        src = (
            "/*/{Protheus.doc} XYZGood\n"
            "Faz alguma coisa importante.\n"
            "@type function\n"
            "@author Equipe ABC\n"
            "@since 2026-05-15\n"
            "@param cArg, character, descricao\n"
            "@return logical, .T. se ok\n"
            "/*/\n"
            "User Function XYZGood(cArg)\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-007" not in _ids(findings)

    def test_negative_doc_is_minimal_but_present(self) -> None:
        """Doc minimo (so opening + closing) ja conta."""
        src = (
            "/*/{Protheus.doc} XYZmin\n"
            "/*/\n"
            "User Function XYZmin()\n"
            "    Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-007" not in _ids(findings)

    def test_negative_mvc_hook_skipped(self) -> None:
        """MVC hooks (bCommit/bTudoOk/bLineOk) NAO sao funcoes reais — skip."""
        src = (
            "/*/{Protheus.doc} XYZModel\n"
            "/*/\n"
            "Static Function ModelDef()\n"
            "    Local oModel := MPFormModel():New('M')\n"
            "    oModel:SetCommit({|oM| .T.}, .T.)\n"
            "Return oModel\n"
        )
        findings = lint_source(_parsed_for(src), src)
        # Hook anonimo nao deve gerar BP-007 (so a Static Function que tem doc).
        assert "BP-007" not in _ids(findings)

    def test_negative_doc_for_each_of_multiple_functions(self) -> None:
        """3 funcoes, todas com doc = 0 findings."""
        src = (
            "/*/{Protheus.doc} ZA\n"
            "/*/\n"
            "User Function ZA()\n"
            "    Return .T.\n"
            "/*/{Protheus.doc} helper\n"
            "/*/\n"
            "Static Function helper()\n"
            "    Return Nil\n"
            "/*/{Protheus.doc} ZB\n"
            "/*/\n"
            "User Function ZB()\n"
            "    Return .T.\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-007" not in _ids(findings)


# --- BP-002b: variavel Private quando Local resolveria ----------------------


class TestBP002bPrivateWhenLocal:
    """BP-002b (warning): `Private <var>` em vez de `Local`, exceto em casos
    legitimos (MV_PAR*, lMsErroAuto, framework reservadas)."""

    def test_positive_private_simple_var(self) -> None:
        """Private comum sem motivo aparente — sinaliza."""
        src = (
            "User Function ZBad()\n"
            "    Private cVal := 'x'\n"
            "    Private nCount := 0\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp = [f for f in findings if f["regra_id"] == "BP-002b"]
        assert len(bp) == 2
        assert bp[0]["severidade"] == "warning"

    def test_positive_private_multivar(self) -> None:
        """Multi-var: cada nome conta como 1 finding."""
        src = (
            "User Function ZBad()\n"
            "    Private cA, cB, nC\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        bp = [f for f in findings if f["regra_id"] == "BP-002b"]
        assert len(bp) == 3

    def test_positive_private_with_assign(self) -> None:
        """Private cVar := valor — flagged."""
        src = (
            "User Function ZBad()\n"
            "    Private oModel := FwLoadModel('X')\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002b" in _ids(findings)

    # --- Negativos (whitelist) ---

    def test_negative_private_mv_par(self) -> None:
        """Private MV_PAR01..MV_PAR99 = convencao Pergunte()."""
        src = (
            "User Function ZGood()\n"
            "    Private MV_PAR01 := ''\n"
            "    Private MV_PAR02 := 0\n"
            "    Pergunte('MGFREL01', .F.)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002b" not in _ids(findings)

    def test_negative_private_msexecauto_state(self) -> None:
        """Private lMsErroAuto/lMsHelpAuto = convencao MsExecAuto."""
        src = (
            "User Function ZGood()\n"
            "    Private lMsErroAuto := .F.\n"
            "    Private lMsHelpAuto := .F.\n"
            "    MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCab, aIt, 3)\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002b" not in _ids(findings)

    def test_negative_local_decl_not_flagged(self) -> None:
        """Local correto — nao dispara."""
        src = (
            "User Function ZGood()\n"
            "    Local cVal := 'x'\n"
            "    Local nCount := 0\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002b" not in _ids(findings)

    def test_negative_static_decl_not_flagged(self) -> None:
        """Static (constante por fonte) tambem ok — nao dispara."""
        src = (
            "Static cCache := ''\n"
            "User Function ZGood()\n"
            "    cCache := 'novo'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002b" not in _ids(findings)

    def test_negative_public_not_flagged_handled_by_mod002(self) -> None:
        """Public eh coberto por MOD-002 — BP-002b foca em Private."""
        src = (
            "User Function ZBad()\n"
            "    Public cGlobal := 'x'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        ids = _ids(findings)
        assert "MOD-002" in ids
        assert "BP-002b" not in ids

    def test_negative_in_comment(self) -> None:
        """Private em comentario nao dispara."""
        src = (
            "User Function ZGood()\n"
            "    // Antes era: Private cVal := 'x'\n"
            "    Local cVal := 'x'\n"
            "Return\n"
        )
        findings = lint_source(_parsed_for(src), src)
        assert "BP-002b" not in _ids(findings)
