"""Testes de cli/plugadvpl/parsing/parser.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from plugadvpl.parsing.parser import (
    add_function_ranges,
    extract_calls_execauto,
    extract_calls_execblock,
    extract_calls_fwexecview,
    extract_calls_fwloadmodel,
    extract_calls_method,
    extract_calls_user_func,
    extract_defines,
    extract_env_openers,
    extract_fields_ref,
    extract_functions,
    extract_http_calls,
    extract_includes,
    extract_log_calls,
    extract_mvc_hooks,
    extract_namespace,
    extract_params,
    extract_perguntas,
    extract_rest_endpoints,
    extract_sql_embedado,
    extract_tables,
    extract_ws_structures,
    read_file,
)


class TestReadFile:
    def test_cp1252_fast_path(self, tmp_path: Path) -> None:
        f = tmp_path / "test.prw"
        f.write_bytes("cNome := \"João\"".encode("cp1252"))
        content, encoding = read_file(f)
        assert content == 'cNome := "João"'
        assert encoding == "cp1252"

    def test_utf8_fallback(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tlpp"
        # 字 (caracter chinês) não cabe em cp1252
        f.write_text('cNome := "字"', encoding="utf-8")
        content, encoding = read_file(f)
        assert "字" in content
        assert encoding == "utf-8"

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.prw"
        f.write_bytes(b"")
        content, encoding = read_file(f)
        assert content == ""


class TestExtractFunctions:
    def test_user_function(self) -> None:
        src = "User Function FATA050()\nReturn .T."
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "FATA050" in names

    def test_static_function(self) -> None:
        src = "Static Function ValidaCampo(cCpo)\nReturn .T."
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "ValidaCampo" in names

    def test_main_function(self) -> None:
        src = "Main Function JobX()\nReturn"
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "JobX" in names

    def test_wsmethod(self) -> None:
        src = "WSMETHOD GET clientes WSSERVICE Vendas\nReturn"
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "clientes" in names

    def test_method_class(self) -> None:
        src = "METHOD New(cArg) CLASS Pedido\nReturn Self"
        result = extract_functions(src)
        funs = [(f["nome"], f.get("classe")) for f in result]
        assert ("New", "Pedido") in funs

    def test_ignores_function_in_comment(self) -> None:
        # Confirma que strip_advpl está sendo aplicado antes
        src = "// User Function CommentedOut()\nUser Function Real()\nReturn"
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "Real" in names
        assert "CommentedOut" not in names

    def test_returns_line_numbers(self) -> None:
        src = "// linha 1\nUser Function Foo()\nReturn .T.\n\nUser Function Bar()\nReturn .F."
        result = extract_functions(src)
        by_name = {f["nome"]: f for f in result}
        assert by_name["Foo"]["linha_inicio"] == 2
        assert by_name["Bar"]["linha_inicio"] == 5


class TestAddFunctionRanges:
    def test_ranges_set_from_next_function(self) -> None:
        src = (
            "User Function A()\n"        # linha 1
            "  Local x := 1\n"            # 2
            "Return x\n"                  # 3
            "\n"                          # 4
            "User Function B()\n"        # 5
            "Return .T.\n"                # 6
        )
        funcs = extract_functions(src)
        funcs = add_function_ranges(funcs, src)
        by_name = {f["nome"]: f for f in funcs}
        assert by_name["A"]["linha_inicio"] == 1
        assert by_name["A"]["linha_fim"] == 4  # antes do header de B
        assert by_name["B"]["linha_inicio"] == 5
        assert by_name["B"]["linha_fim"] == 6  # última linha do arquivo


class TestExtractTables:
    def test_dbselectarea(self) -> None:
        src = 'DbSelectArea("SA1")'
        tables = extract_tables(src)
        assert "SA1" in tables["read"]

    def test_alias_arrow_read(self) -> None:
        src = "cNome := SA1->A1_NOME"
        tables = extract_tables(src)
        assert "SA1" in tables["read"]

    def test_xfilial_read(self) -> None:
        src = 'cFil := xFilial("SC5")'
        tables = extract_tables(src)
        assert "SC5" in tables["read"]

    def test_reclock_write(self) -> None:
        src = 'RecLock("SA1", .T.)\nReplace A1_NOME With "X"\nMsUnlock()'
        tables = extract_tables(src)
        assert "SA1" in tables["reclock"]
        assert "SA1" in tables["write"]

    def test_dbappend_write(self) -> None:
        src = "SA1->(dbAppend())"
        tables = extract_tables(src)
        assert "SA1" in tables["write"]

    def test_custom_table_za1(self) -> None:
        src = "DbSelectArea('ZA1')"
        tables = extract_tables(src)
        assert "ZA1" in tables["read"]

    def test_ignores_invalid_table_codes(self) -> None:
        src = 'cFoo := "ABC"->bar'
        tables = extract_tables(src)
        assert "ABC" not in tables["read"]  # ABC não é código Protheus válido

    def test_table_in_string_literal_not_captured_via_alias_arrow(self) -> None:
        """Alias->Field dentro de string literal não deve ser capturado como tabela referenciada."""
        src = 'cMsg := "Erro ao gravar SA1->A1_NOME"'
        tables = extract_tables(src)
        assert "SA1" not in tables["read"]  # SA1 estava só dentro da string

    def test_dbselectarea_still_captured_from_string(self) -> None:
        """DbSelectArea("SA1") usa o nome literal — deve ser capturado mesmo em string."""
        src = 'DbSelectArea("SA1")'
        tables = extract_tables(src)
        assert "SA1" in tables["read"]


class TestExtractParams:
    def test_supergetmv(self) -> None:
        src = 'cVal := SuperGetMV("MV_LOCALIZA", .F., "01")'
        params = extract_params(src)
        names = {(p["nome"], p["modo"]) for p in params}
        assert ("MV_LOCALIZA", "read") in names

    def test_getmv(self) -> None:
        src = 'cMoeda := GetMv("MV_SIMB1")'
        params = extract_params(src)
        names = {p["nome"] for p in params}
        assert "MV_SIMB1" in names

    def test_getnewpar(self) -> None:
        src = 'cVal := GetNewPar("MV_FOO", "default")'
        params = extract_params(src)
        names = {(p["nome"], p["default_decl"]) for p in params}
        assert ("MV_FOO", "default") in names

    def test_putmv_write(self) -> None:
        src = 'PutMV("MV_X", "newvalue")'
        params = extract_params(src)
        names = {(p["nome"], p["modo"]) for p in params}
        assert ("MV_X", "write") in names


class TestExtractPerguntas:
    def test_pergunte(self) -> None:
        src = 'Pergunte("FAT050", .F.)'
        assert "FAT050" in extract_perguntas(src)

    def test_fwgetsx1(self) -> None:
        src = 'aGrp := FWGetSX1("FIN001")'
        assert "FIN001" in extract_perguntas(src)

    def test_ignores_in_comment(self) -> None:
        src = '// Pergunte("FAKE")\nPergunte("REAL", .F.)'
        result = extract_perguntas(src)
        assert "REAL" in result
        assert "FAKE" not in result


class TestExtractIncludes:
    def test_basic_include(self) -> None:
        src = '#Include "protheus.ch"\n#include \'topconn.ch\''
        result = extract_includes(src)
        assert "protheus.ch" in result
        assert "topconn.ch" in result

    def test_ignores_in_comment(self) -> None:
        src = '// #Include "fake.ch"\n#Include "real.ch"'
        result = extract_includes(src)
        assert "real.ch" in result
        assert "fake.ch" not in result


class TestExtractCallsUserFunc:
    def test_basic_call(self) -> None:
        src = "U_FATA060()"
        calls = extract_calls_user_func(src)
        names = [c["destino"] for c in calls]
        assert "FATA060" in names

    def test_records_line(self) -> None:
        src = "Function X()\n  U_FOO()\nReturn"
        calls = extract_calls_user_func(src)
        assert calls[0]["linha_origem"] == 2

    def test_ignores_in_string(self) -> None:
        src = 'cMsg := "U_FAKE() blocked"'
        assert extract_calls_user_func(src) == []


class TestExtractCallsExecAuto:
    def test_execauto_with_rotina(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCabec, aItens, 3)'
        result = extract_calls_execauto(src)
        assert any(c["destino"] == "MATA410" for c in result)


class TestExtractCallsExecBlock:
    def test_execblock(self) -> None:
        src = 'ExecBlock("MT410GRV", .F., .F.)'
        result = extract_calls_execblock(src)
        assert any(c["destino"] == "MT410GRV" for c in result)


class TestExtractCallsFWLoadModel:
    def test_fwloadmodel(self) -> None:
        src = 'oModel := FWLoadModel("MATA010")'
        result = extract_calls_fwloadmodel(src)
        assert any(c["destino"] == "MATA010" for c in result)


class TestExtractCallsFWExecView:
    def test_fwexecview(self) -> None:
        src = 'FWExecView("Cadastro Cliente", "MATA010", MODEL_OPERATION_INSERT, , {})'
        result = extract_calls_fwexecview(src)
        assert any(c["destino"] == "MATA010" for c in result)


class TestExtractCallsMethod:
    def test_obj_method(self) -> None:
        src = "oModel:Activate()"
        result = extract_calls_method(src)
        assert any(c["destino"] == "oModel:Activate" for c in result)

    def test_self_method(self) -> None:
        src = "::Init()"
        result = extract_calls_method(src)
        assert any("Init" in c["destino"] for c in result)

    def test_method_does_not_match_digit_start(self) -> None:
        src = "obj:9invalid()"
        result = extract_calls_method(src)
        assert result == []


class TestExtractFieldsRef:
    def test_alias_arrow_field(self) -> None:
        src = "cNome := SA1->A1_NOME"
        assert "A1_NOME" in extract_fields_ref(src)

    def test_replace_field(self) -> None:
        src = 'Replace A1_NOME With "X"'
        assert "A1_NOME" in extract_fields_ref(src)

    def test_ignores_invalid_field_pattern(self) -> None:
        src = "x := abc_def"  # não é padrão XX_NOME ADVPL
        assert "ABC_DEF" not in extract_fields_ref(src)


class TestExtractRestEndpoints:
    def test_wsmethod_classic(self) -> None:
        src = "WSMETHOD GET clientes WSSERVICE Vendas\nReturn"
        result = extract_rest_endpoints(src)
        assert any(
            e["verbo"] == "GET"
            and e["funcao"] == "clientes"
            and e["classe"] == "Vendas"
            and e["annotation_style"] == "wsmethod_classico"
            for e in result
        )

    def test_wsmethod_post(self) -> None:
        src = "WSMETHOD POST criar WSSERVICE Pedidos\nReturn"
        result = extract_rest_endpoints(src)
        assert any(
            e["verbo"] == "POST" and e["funcao"] == "criar" and e["classe"] == "Pedidos"
            for e in result
        )

    def test_tlpp_annotation(self) -> None:
        src = (
            '@Get("/api/clientes")\n'
            'Function getClientes()\n'
            'Return\n'
        )
        result = extract_rest_endpoints(src)
        assert any(
            e["verbo"] == "GET"
            and e["path"] == "/api/clientes"
            and e["annotation_style"] == "@verb_tlpp"
            for e in result
        )

    def test_ignores_in_comment(self) -> None:
        src = '// @Get("/api/fake")\n@Post("/api/real")\nFunction x()\nReturn'
        result = extract_rest_endpoints(src)
        paths = [e["path"] for e in result]
        assert "/api/real" in paths
        assert "/api/fake" not in paths


class TestExtractHttpCalls:
    def test_httppost(self) -> None:
        src = 'HttpPost("https://api.example.com/v1/x", "", cBody, 30, aHeaders, @cRet)'
        result = extract_http_calls(src)
        assert any(
            c["metodo"] == "HttpPost"
            and c["url_literal"] == "https://api.example.com/v1/x"
            for c in result
        )

    def test_httpsget(self) -> None:
        src = 'cRet := HttpsGet("https://api.x.com/y")'
        result = extract_http_calls(src)
        assert any(
            c["metodo"] == "HttpsGet" and c["url_literal"] == "https://api.x.com/y"
            for c in result
        )

    def test_msageturl(self) -> None:
        src = 'cRet := MsAGetUrl("http://server/data.txt")'
        result = extract_http_calls(src)
        assert any(c["metodo"] == "MsAGetUrl" for c in result)

    def test_ignores_in_comment(self) -> None:
        src = '// HttpPost("http://fake.com", "")\nHttpGet("http://real.com")'
        result = extract_http_calls(src)
        urls = [c["url_literal"] for c in result]
        assert "http://real.com" in urls
        assert "http://fake.com" not in urls


class TestExtractEnvOpeners:
    def test_rpcsetenv_all_literals(self) -> None:
        src = 'RpcSetEnv("01", "01", "user", "pwd", "PRODUCAO", "FIN")'
        result = extract_env_openers(src)
        assert len(result) == 1
        e = result[0]
        assert e["empresa"] == "01"
        assert e["filial"] == "01"
        assert e["environment"] == "PRODUCAO"
        assert e["modulo"] == "FIN"

    def test_rpcsetenv_with_variables(self) -> None:
        src = 'RpcSetEnv(cEmp, cFil, "user", "pwd", "PROD", cMod)'
        result = extract_env_openers(src)
        assert len(result) == 1
        e = result[0]
        # Variáveis viram string vazia, literais preservados
        assert e["empresa"] == ""
        assert e["filial"] == ""
        assert e["environment"] == "PROD"
        assert e["modulo"] == ""

    def test_ignores_in_comment(self) -> None:
        src = '// RpcSetEnv("99", "99")\nRpcSetEnv("01", "01", "x", "y", "P", "F")'
        result = extract_env_openers(src)
        assert len(result) == 1
        assert result[0]["empresa"] == "01"


class TestExtractLogCalls:
    def test_fwlogmsg_info(self) -> None:
        src = 'FwLogMsg("INFO", "msg here", "service-x", "categ-y", 100)'
        result = extract_log_calls(src)
        assert any(c["nivel"] == "INFO" and c["categoria"] == "categ-y" for c in result)

    def test_fwlogmsg_error_no_categ(self) -> None:
        src = 'FwLogMsg("ERROR", "fail")'
        result = extract_log_calls(src)
        assert any(c["nivel"] == "ERROR" and c["categoria"] == "" for c in result)

    def test_conout(self) -> None:
        src = 'ConOut("debug here")'
        result = extract_log_calls(src)
        assert any(c["nivel"] == "conout" for c in result)

    def test_ignores_in_comment(self) -> None:
        src = '// ConOut("fake")\nConOut("real")'
        result = extract_log_calls(src)
        assert len(result) == 1


class TestExtractDefines:
    def test_simple_define(self) -> None:
        src = "#DEFINE MAX_ITEMS 100\n"
        result = extract_defines(src)
        assert any(d["nome"] == "MAX_ITEMS" and d["valor"] == "100" for d in result)

    def test_define_string_value(self) -> None:
        src = '#DEFINE PREFIX "PRF_"\n'
        result = extract_defines(src)
        assert any(d["nome"] == "PREFIX" and '"PRF_"' in d["valor"] for d in result)

    def test_define_records_line(self) -> None:
        src = "// comment\n#DEFINE X 1\n#DEFINE Y 2\n"
        result = extract_defines(src)
        by_name = {d["nome"]: d for d in result}
        assert by_name["X"]["linha"] == 2
        assert by_name["Y"]["linha"] == 3

    def test_ignores_in_comment(self) -> None:
        src = "// #DEFINE FAKE 99\n#DEFINE REAL 1\n"
        result = extract_defines(src)
        names = {d["nome"] for d in result}
        assert "REAL" in names
        assert "FAKE" not in names


class TestExtractMvcHooks:
    def test_bcommit_hook(self) -> None:
        src = "bCommit := {|| MyCommit()}"
        result = extract_mvc_hooks(src)
        assert any(c["destino"] == "bCommit" and c["tipo"] == "mvc_hook" for c in result)

    def test_btudook_hook(self) -> None:
        src = "bTudoOk := { || ValidaTudo() }"
        result = extract_mvc_hooks(src)
        assert any(c["destino"] == "bTudoOk" for c in result)

    def test_blineok_with_equals(self) -> None:
        # Aceita := e = (atribuição clássica e short)
        src = "bLineOk = {|| .T.}"
        result = extract_mvc_hooks(src)
        assert any(c["destino"] == "bLineOk" for c in result)

    def test_ignores_in_comment(self) -> None:
        src = "// bCommit := { || .T. }\nbCancel := { || .F. }"
        result = extract_mvc_hooks(src)
        names = [c["destino"] for c in result]
        assert "bCancel" in names
        assert "bCommit" not in names


class TestExtractWsStructures:
    def test_wsstruct(self) -> None:
        src = (
            "WSSTRUCT Cliente\n"
            "  WSDATA codigo AS String\n"
            "  WSDATA nome AS String\n"
            "ENDWSSTRUCT\n"
        )
        result = extract_ws_structures(src)
        assert any(
            s["nome"] == "Cliente"
            and {"nome": "codigo", "tipo": "String"} in s["campos"]
            and {"nome": "nome", "tipo": "String"} in s["campos"]
            for s in result["ws_structs"]
        )

    def test_wsservice(self) -> None:
        src = (
            "WSSERVICE Vendas\n"
            "  WSMETHOD listar\n"
            "  WSMETHOD criar\n"
            "ENDWSSERVICE\n"
        )
        result = extract_ws_structures(src)
        assert any(
            sv["nome"] == "Vendas" and "listar" in sv["metodos"] and "criar" in sv["metodos"]
            for sv in result["ws_services"]
        )

    def test_wsmethod_full(self) -> None:
        src = "WSMETHOD criar WSRECEIVE Cliente WSSEND Resposta WSSERVICE Vendas\nReturn"
        result = extract_ws_structures(src)
        assert any(
            mm["nome"] == "criar"
            and mm["receive"] == "Cliente"
            and mm["send"] == "Resposta"
            and mm["service"] == "Vendas"
            for mm in result["ws_methods"]
        )


class TestExtractNamespace:
    def test_basic_namespace(self) -> None:
        src = "Namespace com.empresa.modulo\nFunction X()\nReturn"
        assert extract_namespace(src) == "com.empresa.modulo"

    def test_no_namespace_returns_empty(self) -> None:
        src = "Function X()\nReturn"
        assert extract_namespace(src) == ""

    def test_first_match_wins(self) -> None:
        # Strip-strings=True, então namespace dentro de string não deveria contar
        src = 'cMsg := "Namespace fake.x"\nNamespace real.module'
        assert extract_namespace(src) == "real.module"


class TestExtractSqlEmbedado:
    def test_beginsql_select(self) -> None:
        src = (
            "BeginSql Alias 'TRB'\n"
            "  SELECT A1_COD FROM SA1010\n"
            "  WHERE A1_FILIAL = 'FIL'\n"
            "EndSql\n"
        )
        result = extract_sql_embedado(src)
        assert len(result) == 1
        e = result[0]
        assert e["operacao"] == "select"
        assert "SA1010" in e["tabelas"]
        assert "SELECT" in e["snippet"].upper()

    def test_tcquery(self) -> None:
        src = "TCQuery(\"SELECT * FROM SA1010 WHERE A1_FILIAL = '01'\", aArea, 'TRB')"
        result = extract_sql_embedado(src)
        assert any(e["operacao"] == "select" and "SA1010" in e["tabelas"] for e in result)

    def test_tcsqlexec_update(self) -> None:
        src = "TCSqlExec(\"UPDATE SA1010 SET A1_NOME = 'X' WHERE A1_COD = '001'\")"
        result = extract_sql_embedado(src)
        assert any(e["operacao"] == "update" and "SA1010" in e["tabelas"] for e in result)

    def test_snippet_capped(self) -> None:
        long_sql = "SELECT * FROM SA1010 WHERE " + ("X = 'a' AND " * 100)
        src = f'TCQuery("{long_sql}")'
        result = extract_sql_embedado(src)
        assert len(result) == 1
        assert len(result[0]["snippet"]) <= 300


class TestDeriveCapabilities:
    def _empty_parsed(self) -> dict[str, object]:
        return {
            "funcoes": [],
            "namespace": "",
            "rest_endpoints": [],
            "http_calls": [],
            "env_openers": [],
            "log_calls": [],
            "defines": [],
            "ws_structures": {"ws_structs": [], "ws_services": [], "ws_methods": []},
            "sql_embedado": [],
            "chamadas": [],
            "campos_ref": [],
            "tabelas_ref": {"read": [], "write": [], "reclock": []},
        }

    def test_mvc_from_hook(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        p["chamadas"] = [{"destino": "bCommit", "tipo": "mvc_hook"}]
        caps = derive_capabilities(p, "")
        assert "MVC" in caps

    def test_ws_rest_and_soap(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p_rest = self._empty_parsed()
        p_rest["rest_endpoints"] = [
            {"verbo": "GET", "path": "/x", "annotation_style": "@verb_tlpp"}
        ]
        assert "WS-REST" in derive_capabilities(p_rest, "")

        p_soap = self._empty_parsed()
        p_soap["rest_endpoints"] = [
            {"verbo": "GET", "path": "", "annotation_style": "wsmethod_classico"}
        ]
        assert "WS-SOAP" in derive_capabilities(p_soap, "")

    def test_job_requires_main_and_rpc(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        p["funcoes"] = [{"nome": "JobX", "kind": "main_function"}]
        p["env_openers"] = [{"empresa": "01", "filial": "01"}]
        caps = derive_capabilities(p, "")
        assert "JOB" in caps
        assert "RPC" in caps
        assert "ENV_OPENER" in caps

    def test_rest_client_only(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        p["http_calls"] = [{"metodo": "HttpPost", "url_literal": "http://x.com"}]
        caps = derive_capabilities(p, "")
        assert "REST_CLIENT" in caps

    def test_pe_user_function_pattern(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        p["funcoes"] = [{"nome": "MT410GRV", "kind": "user_function"}]
        caps = derive_capabilities(p, "")
        assert "PE" in caps

    def test_compatibilizador_u_upd(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        p["funcoes"] = [{"nome": "U_UPDFIN", "kind": "user_function"}]
        caps = derive_capabilities(p, "")
        assert "COMPATIBILIZADOR" in caps

    def test_dialog_browse_workflow_json_multifilial(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        # Content-driven caps need content passed explicitly
        content = (
            "oDlg := MsDialog():New()\n"
            "oBrw := FWFormBrowse():New()\n"
            "WFPrepEnv()\n"
            "oJson := JsonObject():New()\n"
            "cFil := xFilial('SA1')\n"
        )
        caps = derive_capabilities(p, content)
        assert "DIALOG" in caps
        assert "BROWSE" in caps
        assert "WORKFLOW" in caps
        assert "JSON_AWARE" in caps
        assert "MULTI_FILIAL" in caps

    def test_exec_auto_caller(self) -> None:
        from plugadvpl.parsing.parser import derive_capabilities
        p = self._empty_parsed()
        p["chamadas"] = [{"destino": "MATA410", "tipo": "execauto"}]
        assert "EXEC_AUTO_CALLER" in derive_capabilities(p, "")


class TestParseSource:
    def test_parse_returns_dict_with_all_fields(self, tmp_path: Path) -> None:
        f = tmp_path / "FATA050.prw"
        f.write_bytes(
            b'#Include "protheus.ch"\n'
            b'User Function FATA050()\n'
            b'  Local cMV := SuperGetMV("MV_LOCALIZA", .F., "")\n'
            b'  DbSelectArea("SC5")\n'
            b'  RecLock("SC5", .T.)\n'
            b'  Replace C5_NUM With "001"\n'
            b'  MsUnlock()\n'
            b'  U_FATA060()\n'
            b'Return .T.'
        )
        from plugadvpl.parsing.parser import parse_source
        result = parse_source(f)
        assert result["arquivo"] == "FATA050.prw"
        assert result["encoding"] == "cp1252"
        assert "FATA050" in [fn["nome"] for fn in result["funcoes"]]
        assert "SC5" in result["tabelas_ref"]["read"]
        assert "SC5" in result["tabelas_ref"]["write"]
        assert "MV_LOCALIZA" in [p["nome"] for p in result["parametros_uso"]]
        assert any(c["destino"] == "FATA060" for c in result["chamadas"])
        assert "protheus.ch" in result["includes"]
        # Hash deve estar populado (usado para stale detection — spec §11.2 #23)
        assert result["hash"]
        assert len(result["hash"]) == 40  # SHA-1 hex

    def test_hash_is_stable_for_same_content(self, tmp_path: Path) -> None:
        """Mesmo bytes → mesmo hash (necessário para incremental e UPSERT WHERE hash != old)."""
        from plugadvpl.parsing.parser import parse_source
        f1 = tmp_path / "a.prw"
        f2 = tmp_path / "b.prw"
        bytes_ = b'User Function X()\nReturn .T.'
        f1.write_bytes(bytes_)
        f2.write_bytes(bytes_)
        r1 = parse_source(f1)
        r2 = parse_source(f2)
        assert r1["hash"] == r2["hash"]

    def test_hash_differs_for_different_content(self, tmp_path: Path) -> None:
        from plugadvpl.parsing.parser import parse_source
        f1 = tmp_path / "a.prw"
        f2 = tmp_path / "b.prw"
        f1.write_bytes(b"User Function A()\nReturn")
        f2.write_bytes(b"User Function B()\nReturn")
        assert parse_source(f1)["hash"] != parse_source(f2)["hash"]

    def test_pe_paramixb_in_string_or_comment_does_not_trigger(self, tmp_path: Path) -> None:
        """v0.3.22 — Bug #8 do QA round 2: `PARAMIXB[...]` em comentario ou
        string literal disparava classificacao como PE. Deve usar stripped
        (sem strings/comentarios) pra evitar falso positivo."""
        from plugadvpl.parsing.parser import parse_source
        f = tmp_path / "FakeP.prw"
        f.write_text(
            "User Function FakeP()\n"
            '    Local cMsg := "Use PARAMIXB[1] na implementacao"\n'
            "    // PARAMIXB[2] tambem funciona\n"
            "    ConOut(cMsg)\n"
            "Return\n",
            encoding="cp1252",
        )
        result = parse_source(f)
        assert "PE" not in result["capabilities"], (
            "PARAMIXB em string/comentario nao deve disparar classificacao PE; "
            f"capabilities={result['capabilities']}"
        )
        assert "FakeP" not in result["pontos_entrada"]

    def test_pe_canonical_paramixb_detected(self) -> None:
        """v0.3.16 — Bug #6/#10 do QA report: nome canonico TOTVS como
        ANCTB102GR nao casa o regex `_PE_NAME_RE` (que exige <letras><digitos>
        <letras>; ANCTB102GR tem letras-letras-digitos-letras). Heuristica nova:
        se o corpo da funcao usa PARAMIXB[N], eh PE — independente do nome.
        Pega o caso canonico Protheus + qualquer PE custom escrito sem padrao
        de nome obvio."""
        from plugadvpl.parsing.parser import parse_source
        fixture = (
            Path(__file__).parent.parent
            / "fixtures" / "synthetic" / "pe_paramixb.prw"
        )
        result = parse_source(fixture)
        assert "PE" in result["capabilities"], (
            f"PE deveria estar em capabilities (PARAMIXB usado), "
            f"tem {result['capabilities']}"
        )
        assert "ANCTB102GR" in result["pontos_entrada"], (
            f"ANCTB102GR deveria estar em pontos_entrada, "
            f"tem {result['pontos_entrada']}"
        )

    def test_wsrestful_methods_appear_in_funcoes(self) -> None:
        """v0.3.21 — Bug #13/#14 do QA round 2: WSRESTFUL verb-only
        (`WSMETHOD GET WSSERVICE PortaldeViagem`) ficava fora de `funcoes`
        porque `_WSMETHOD_RE` exige `<name>` antes de `WS...`. Cascata
        quebrava call graph dos metodos REST: `find function GET`,
        `callees GET`, `callers SetResponse` ficavam cegos.

        Fix: capturar via _WSMETHOD_REST_BARE_RE em paralelo, com
        nome=`<Classe>.<VERB>` pra ser identificavel."""
        from plugadvpl.parsing.parser import parse_source
        fixture = (
            Path(__file__).parent.parent
            / "fixtures" / "synthetic" / "ws_restful_classic.prw"
        )
        result = parse_source(fixture)
        nomes = [f["nome"] for f in result["funcoes"]]
        # Fixture tem 2 metodos: GET e POST de PortaldeViagem.
        assert any("PortaldeViagem.GET" in n or "PortaldeViagem:GET" in n
                   for n in nomes), (
            f"Esperado funcao 'PortaldeViagem.GET' (ou similar) em funcoes, "
            f"recebido {nomes}"
        )
        assert any("PortaldeViagem.POST" in n or "PortaldeViagem:POST" in n
                   for n in nomes), (
            f"Esperado funcao 'PortaldeViagem.POST' em funcoes, recebido {nomes}"
        )

    def test_wsrestful_classic_classified_as_webservice(self) -> None:
        """v0.3.16 — Bug #5/#7 do QA report: classes WSRESTFUL clássicas
        (com `WSMETHOD GET WSSERVICE <Class>` em vez de `WSMETHOD GET <name>
        WSSERVICE <Class>`) caíam pra `source_type=user_function` em vez de
        `webservice`, e capability `WS-REST` ficava ausente. Detector novo
        captura `WSRESTFUL <Name>` como ws_service + style 'wsrestful'."""
        from plugadvpl.parsing.parser import parse_source
        fixture = (
            Path(__file__).parent.parent
            / "fixtures" / "synthetic" / "ws_restful_classic.prw"
        )
        result = parse_source(fixture)
        assert result["source_type"] == "webservice", (
            f"WSRESTFUL deveria virar webservice, virou {result['source_type']!r}"
        )
        assert "WS-REST" in result["capabilities"], (
            f"capabilities deveria incluir WS-REST, tem {result['capabilities']}"
        )
        # WSSERVICE não deve aparecer aqui (é WSRESTFUL puro).
        assert "WS-SOAP" not in result["capabilities"]

    def test_parse_source_includes_advanced_extractors(self, tmp_path: Path) -> None:
        from plugadvpl.parsing.parser import parse_source
        f = tmp_path / "MVCExemplo.prw"
        f.write_bytes(
            b"User Function MVCExemplo()\n"
            b"Local bCommit := {|| .T.}\n"
            b"Return .T.\n"
        )
        result = parse_source(f)
        assert "namespace" in result
        assert "rest_endpoints" in result
        assert "http_calls" in result
        assert "env_openers" in result
        assert "log_calls" in result
        assert "defines" in result
        assert "ws_structures" in result
        assert "sql_embedado" in result
        assert "capabilities" in result
        assert "source_type" in result
        # mvc_hook bCommit detectado
        assert any(
            c.get("tipo") == "mvc_hook" and c["destino"] == "bCommit"
            for c in result["chamadas"]
        )
        # capabilities includes MVC (porque tem hook)
        assert "MVC" in result["capabilities"]

    def test_parse_source_avoids_redundant_stripping(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """parse_source must call strip_advpl at most 2 times (one per mode)."""
        from plugadvpl.parsing import stripper

        call_count = [0]
        original = stripper.strip_advpl

        def counting_strip(content: str, *, strip_strings: bool = True) -> str:
            call_count[0] += 1
            return original(content, strip_strings=strip_strings)

        monkeypatch.setattr("plugadvpl.parsing.parser.strip_advpl", counting_strip)

        f = tmp_path / "test.prw"
        f.write_bytes(b"User Function X()\nReturn .T.")
        from plugadvpl.parsing.parser import parse_source
        parse_source(f)
        assert call_count[0] <= 2, (
            f"strip_advpl called {call_count[0]} times, expected <=2"
        )
