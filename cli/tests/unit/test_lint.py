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
        src = (
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
