"""Tests do extrator de chamadas MsExecAuto (Universo 3 / Feature B v0.4.1)."""
from __future__ import annotations

from plugadvpl.parsing.execauto import (
    extract_execauto_calls,
    load_execauto_catalog,
)


def _routines(calls: list[dict]) -> list[str | None]:
    return [c["routine"] for c in calls]


# --- Resolucao de rotina --------------------------------------------------


class TestRoutineResolution:
    def test_basic_3args_mata410(self) -> None:
        """3 args (cab+itens+opc) — MATA410 resolve com SC5/SC6."""
        src = (
            'User Function MGFCOMBO()\n'
            '   MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCab, aIt, 3)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        c = calls[0]
        assert c["routine"] == "MATA410"
        assert c["module"] == "SIGAFAT"
        assert c["op_code"] == 3
        assert c["op_label"] == "inclusao"
        assert c["dynamic_call"] is False
        assert "SC5" in c["tables_resolved"]
        assert "SC6" in c["tables_resolved"]

    def test_2args_no_items(self) -> None:
        """2 args (sem itens) — FINA040."""
        src = (
            'User Function ZFin()\n'
            '   MsExecAuto({|x,y| FINA040(x,y)}, aArr, 3)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        assert calls[0]["routine"] == "FINA040"
        assert calls[0]["module"] == "SIGAFIN"
        assert "SE1" in calls[0]["tables_resolved"]

    def test_4args_named(self) -> None:
        """4 args com bool no fim."""
        src = (
            'User Function ZAlt()\n'
            '   MsExecAuto({|a,b,c,d| MATA410(a,b,c,d)}, aCab, aIt, 4, .F.)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        # op_code deve ser 4 (penultimo arg, ja que ultimo eh .F.)
        assert calls[0]["op_code"] == 4
        assert calls[0]["op_label"] == "alteracao"

    def test_ntipo_prefix_mata120(self) -> None:
        """Variante com nTipo prefixo antes de aCab."""
        src = (
            'User Function MGFCOM28()\n'
            '   MsExecAuto({|v,x,y,z,w,a| Mata120(v,x,y,z,w,a)}, 2, aCab, aItens, 3)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        assert calls[0]["routine"].upper() == "MATA120"
        assert calls[0]["op_code"] == 3

    def test_skip_args_with_empty_commas(self) -> None:
        """Codeblock com virgulas vazias passando args nil."""
        src = (
            'User Function MGFCOMBM()\n'
            '   MSExecAuto({|x,y,z,k,a,b| MATA103(x,y,z,,,,k,a,,,b)}, _aSF1, _aSD1, 4,,,_aCodRet)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        assert calls[0]["routine"] == "MATA103"
        assert "SF1" in calls[0]["tables_resolved"]
        assert "SD1" in calls[0]["tables_resolved"]

    def test_routine_not_in_catalog(self) -> None:
        """Rotina detectada mas nao no catalogo — module/tables vazios."""
        src = (
            'User Function ZUnknown()\n'
            '   MsExecAuto({|x,y,z| MATAXYZ(x,y,z)}, aCab, aIt, 3)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        c = calls[0]
        assert c["routine"] == "MATAXYZ"
        assert c["module"] is None
        assert c["routine_type"] is None
        assert c["tables_resolved"] == []
        assert c["dynamic_call"] is False  # rotina existe, so nao no catalogo


# --- Op codes --------------------------------------------------------------


class TestOpCodeDetection:
    def test_op3_inclusao(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
        c = extract_execauto_calls(src)[0]
        assert c["op_code"] == 3
        assert c["op_label"] == "inclusao"

    def test_op4_alteracao(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 4)\n'
        c = extract_execauto_calls(src)[0]
        assert c["op_code"] == 4
        assert c["op_label"] == "alteracao"

    def test_op5_exclusao(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 5)\n'
        c = extract_execauto_calls(src)[0]
        assert c["op_code"] == 5
        assert c["op_label"] == "exclusao"

    def test_op_nonstandard(self) -> None:
        """op_code fora de 3/4/5 — preserva valor, label=None."""
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 9)\n'
        c = extract_execauto_calls(src)[0]
        assert c["op_code"] == 9
        assert c["op_label"] is None

    def test_op_missing(self) -> None:
        """Sem op_code (ex: rotina sem cab/itens) — None."""
        src = 'MsExecAuto({|| CN121Encerr(.T.)})\n'
        c = extract_execauto_calls(src)[0]
        assert c["op_code"] is None
        assert c["op_label"] is None


# --- Dynamic / nao-resolvivel ---------------------------------------------


class TestDynamicCall:
    def test_macro_substitution(self) -> None:
        """&(cVar)... — dynamic, routine None."""
        src = (
            'User Function ZDyn()\n'
            '   MsExecAuto({|x,y,z| &(cRot).(x,y,z)}, aCab, aIt, 3)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        c = calls[0]
        assert c["routine"] is None
        assert c["dynamic_call"] is True

    def test_no_routine_in_block(self) -> None:
        """Codeblock vazio ou so com Nil — dynamic."""
        src = 'MsExecAuto({|| Nil}, a, b, 3)\n'
        c = extract_execauto_calls(src)[0]
        assert c["routine"] is None
        assert c["dynamic_call"] is True


# --- Edge cases (case/comments/strings) -----------------------------------


class TestEdgeCases:
    def test_case_insensitive_uppercase(self) -> None:
        """MSEXECAUTO maiusculo total."""
        src = 'MSEXECAUTO({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        assert calls[0]["routine"] == "MATA410"

    def test_execauto_without_ms_prefix(self) -> None:
        """ExecAuto sem prefixo Ms (legacy raro)."""
        src = 'ExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        assert calls[0]["routine"] == "MATA410"

    def test_in_line_comment_ignored(self) -> None:
        """MsExecAuto em // comentario — NAO detectar."""
        src = (
            'User Function ZOk()\n'
            '   // antes era MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
            '   ConOut("nada")\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert calls == []

    def test_in_string_ignored(self) -> None:
        """MsExecAuto dentro de string literal — NAO detectar."""
        src = (
            'User Function ZOk()\n'
            '   cTexto := "MsExecAuto eh uma funcao TOTVS"\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert calls == []

    def test_nested_in_msaguarde(self) -> None:
        """MsExecAuto aninhado em MsAguarde."""
        src = (
            'User Function MGFEEC83()\n'
            '   MsAguarde({|| MsExecAuto({|a,b,c,d| EECAP100(a,b,c,d)}, aCab, aIt, 3)}, "msg")\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 1
        assert calls[0]["routine"] == "EECAP100"
        assert calls[0]["module"] == "SIGAEEC"

    def test_multiple_calls_in_one_source(self) -> None:
        """Dois MsExecAuto no mesmo fonte — 2 rows."""
        src = (
            'User Function ZMulti()\n'
            '   MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
            '   MsExecAuto({|x,y| FINA050(x,y)}, c, 3)\n'
            'Return\n'
        )
        calls = extract_execauto_calls(src)
        assert len(calls) == 2
        routines = sorted(_routines(calls))
        assert routines == ["FINA050", "MATA410"]


# --- Catalogo --------------------------------------------------------------


class TestCatalog:
    def test_catalog_loads(self) -> None:
        cat = load_execauto_catalog()
        assert cat["schema_version"] == 1
        assert len(cat["routines"]) >= 25

    def test_catalog_has_required_fields(self) -> None:
        cat = load_execauto_catalog()
        for r in cat["routines"]:
            assert "routine" in r
            assert "module" in r
            assert "type" in r
            assert "tables_primary" in r
            assert isinstance(r["tables_primary"], list)
            assert "verified" in r
            assert isinstance(r["verified"], bool)

    def test_catalog_has_mata410(self) -> None:
        """Sanity check do catalogo basico."""
        cat = load_execauto_catalog()
        mata410 = next(r for r in cat["routines"] if r["routine"] == "MATA410")
        assert mata410["module"] == "SIGAFAT"
        assert "SC5" in mata410["tables_primary"]
        assert "SC6" in mata410["tables_primary"]

    def test_catalog_no_duplicate_routines(self) -> None:
        """v0.4.3 (I5): nome de rotina deve ser unico no catalogo.

        Permite o lookup determinístico (`_routines_index` faz dict[upper_name]).
        Duplicata silenciosa faria a 2a entrada sobrescrever a 1a sem warning.
        """
        cat = load_execauto_catalog()
        names = [r["routine"].upper() for r in cat["routines"]]
        dups = [n for n in set(names) if names.count(n) > 1]
        assert not dups, f"Rotinas duplicadas no catalogo: {dups}"

    def test_catalog_has_v043_additions(self) -> None:
        """v0.4.3 (I5): novas rotinas comuns adicionadas — 6 entradas extras."""
        cat = load_execauto_catalog()
        names = {r["routine"] for r in cat["routines"]}
        for novo in ("MATA020", "MATA040", "MATA112", "FATA010", "FATA050"):
            assert novo in names, f"Esperado {novo} no catalogo v0.4.3"


# --- arg_count + linha + snippet ------------------------------------------


class TestMetadataFields:
    def test_arg_count_3(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
        c = extract_execauto_calls(src)[0]
        assert c["arg_count"] == 3

    def test_arg_count_zero(self) -> None:
        src = 'MsExecAuto({|| CN121Encerr(.T.)})\n'
        c = extract_execauto_calls(src)[0]
        assert c["arg_count"] == 0

    def test_linha_correct(self) -> None:
        src = (
            'User Function Z()\n'
            '   ConOut("a")\n'
            '   MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
            'Return\n'
        )
        c = extract_execauto_calls(src)[0]
        assert c["linha"] == 3

    def test_snippet_present(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, a, b, 3)\n'
        c = extract_execauto_calls(src)[0]
        assert "MATA410" in c["snippet"]
