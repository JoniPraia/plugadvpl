"""Gera os 20 fixtures sintéticos do Chunk 13.

Rode UMA vez: ``python tests/fixtures/synthetic/_generate.py``. Os arquivos
.prw/.tlpp ficam commitados no repo. Encoding default é cp1252 (padrão
Protheus); exceções: ``encoding_utf8.prw`` e ``tlpp_namespace.tlpp`` em UTF-8.

Cada fixture exercita um cenário distinto do parser/lint:
    01 mvc_complete         MVC completo (MenuDef+ModelDef+ViewDef + hooks)
    02 classic_browse       FWFormBrowse sem MVC (TELA_CLASSICA)
    03 pe_simple            User Function MT100LOK no padrão PE Protheus
    04 ws_rest              TLPP @Get/@Post (WS-REST)
    05 ws_soap              WSSERVICE/WSMETHOD/WSDATA clássico (WS-SOAP)
    06 job_rpc              Main Function + RpcSetEnv + MsRunInThread (JOB+RPC)
    07 reclock_pattern      RecLock + Replace + MsUnlock balanceado
    08 reclock_unbalanced   RecLock sem MsUnlock (lint BP-001)
    09 exec_auto            MsExecAuto sem lMsErroAuto check (lint BP-003)
    10 sql_embedded         BeginSql/EndSql + SELECT * + sem %notDel% (lint PERF-001/PERF-002)
    11 encoding_cp1252      Acentos em cp1252 (default Protheus)
    12 encoding_utf8        Acentos em utf-8 multi-byte
    13 empty                0 bytes (deve ser pulado pelo scan)
    14 huge                 >5MB (deve ser pulado pelo scan)
    15 corrupted            sufixo .bak (deve ser pulado pelo scan)
    16 tlpp_namespace       Namespace com.client.module + User Function
    17 http_outbound        HttpPost/HttpGet/MsAGetUrl (REST_CLIENT)
    18 mvc_hooks            bCommit/bTudoOk/bLineOk como atribuições
    19 multi_filial         xFilial/cFilAnt/FwxFilial (MULTI_FILIAL)
    20 pubvars              PUBLIC declarado (lint MOD-002)
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent

# (nome, encoding, conteúdo)
FIXTURES: list[tuple[str, str, str]] = [
    (
        "mvc_complete.prw",
        "cp1252",
        """\
#Include "protheus.ch"
#Include "fwmvcdef.ch"

User Function ZACADEMP()
    Local oBrowse := FWmBrowse():New()
    oBrowse:SetAlias("SA1")
    oBrowse:SetMenuDef("ZACADEMP")
    oBrowse:Activate()
Return Nil

Static Function MenuDef()
    Local aRotina := {}
    aAdd(aRotina, {"Pesquisar", "AxPesqui", 0, 1})
    aAdd(aRotina, {"Visualizar", "VIEWDEF.ZACADEMP", 0, 2})
    aAdd(aRotina, {"Incluir",   "VIEWDEF.ZACADEMP", 0, 3})
    aAdd(aRotina, {"Alterar",   "VIEWDEF.ZACADEMP", 0, 4})
    aAdd(aRotina, {"Excluir",   "VIEWDEF.ZACADEMP", 0, 5})
Return aRotina

Static Function ModelDef()
    Local oModel   := MPFormModel():New("ZACADEMPM")
    Local oStruct  := FWFormStruct(1, "SA1")
    Local bCommit  := {|oM| .T.}
    Local bTudoOk  := {|oM| .T.}
    oModel:AddFields("SA1MASTER", , oStruct)
    oModel:SetCommitWhenActive(.T.)
    oModel:SetVldActivate({|oM| .T.})
Return oModel

Static Function ViewDef()
    Local oModel := FWLoadModel("ZACADEMP")
    Local oStruct := FWFormStruct(2, "SA1")
    Local oView   := FWFormView():New()
    oView:SetModel(oModel)
    oView:AddField("SA1MASTER", oStruct)
Return oView
""",
    ),
    (
        "classic_browse.prw",
        "cp1252",
        """\
#Include "protheus.ch"

User Function ZBROWSE()
    Local oBrowse := FWFormBrowse():New()
    oBrowse:SetAlias("SA1")
    oBrowse:SetDescription("Cadastro de Clientes (clássico)")
    oBrowse:DisableDetails()
    oBrowse:Activate()
Return Nil

Static Function MenuDef()
    Local aRotina := {}
    aAdd(aRotina, {"Pesquisar", "AxPesqui", 0, 1})
    aAdd(aRotina, {"Incluir",   "AxInclui", 0, 3})
Return aRotina
""",
    ),
    (
        "pe_simple.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Ponto de Entrada MT100LOK do MATA100 (Documento de Entrada).
User Function MT100LOK()
    Local lRet := .T.
    Local aArea := GetArea()
    If SF1->F1_TIPO == "D"
        lRet := .F.
    EndIf
    RestArea(aArea)
Return lRet
""",
    ),
    (
        "ws_rest.tlpp",
        "cp1252",
        """\
#include "tlpp-core.th"
#include "tlpp-rest.th"

Namespace api.clientes

@Get("/clientes")
User Function ListarClientes()
    Local oResp := JsonObject():New()
    oResp["status"] := "ok"
Return oResp

@Post("/clientes")
User Function GravarCliente()
    Local oReq := oRest:GetJsonRequest()
    Local oResp := JsonObject():New()
    oResp["id"] := oReq["id"]
Return oResp
""",
    ),
    (
        "ws_soap.prw",
        "cp1252",
        """\
#Include "protheus.ch"
#Include "apwebsrv.ch"

WSSERVICE WSVendas DESCRIPTION "Servico de Vendas"
    WSDATA cCodigo  AS String
    WSDATA cNome    AS String
    WSMETHOD Listar  DESCRIPTION "Lista vendas"
    WSMETHOD Gravar  DESCRIPTION "Grava venda"
ENDWSSERVICE

WSMETHOD Listar WSRECEIVE cCodigo WSSEND cNome WSSERVICE WSVendas
    ::cNome := "Cliente " + ::cCodigo
Return .T.

WSMETHOD Gravar WSRECEIVE cCodigo WSSEND cNome WSSERVICE WSVendas
    ::cNome := "Gravado " + ::cCodigo
Return .T.
""",
    ),
    (
        "job_rpc.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Job de processamento batch — abre ambiente via RpcSetEnv.
Main Function ZJOBSYNC()
    Local cEmp := "01"
    Local cFil := "010101"
    RpcSetEnv(cEmp, cFil, "admin", "msadmin", "FAT", "ZJOBSYNC")
    MsRunInThread({|| U_ZTASK01() })
    MsRunInThread({|| U_ZTASK02() })
    RpcClearEnv()
Return Nil

User Function ZTASK01()
    ConOut("ZTASK01 iniciado")
Return Nil

User Function ZTASK02()
    ConOut("ZTASK02 iniciado")
Return Nil
""",
    ),
    (
        "reclock_pattern.prw",
        "cp1252",
        """\
#Include "protheus.ch"

User Function ZRECOK()
    Local aArea := GetArea()
    DbSelectArea("SA1")
    SA1->(DbSetOrder(1))
    If SA1->(MsSeek(xFilial("SA1") + "000001"))
        RecLock("SA1", .F.)
        Replace A1_NOME WITH "ATUALIZADO"
        Replace A1_NREDUZ WITH "ATU"
        SA1->(MsUnlock())
    EndIf
    RestArea(aArea)
Return Nil
""",
    ),
    (
        "reclock_unbalanced.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Anti-padrão: RecLock sem MsUnlock — deve disparar lint BP-001.
User Function ZRECBAD()
    Local aArea := GetArea()
    DbSelectArea("SA1")
    If SA1->(MsSeek(xFilial("SA1") + "000002"))
        RecLock("SA1", .F.)
        Replace A1_NOME WITH "ESQUECEU UNLOCK"
        // FALTA MsUnlock() aqui
    EndIf
    RestArea(aArea)
Return Nil
""",
    ),
    (
        "exec_auto.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Anti-padrão: chama MsExecAuto sem checar lMsErroAuto/MostraErro depois.
User Function ZEXAUTO()
    Local aCabec := {}
    Local aItens := {}
    aAdd(aCabec, {"F1_DOC", "000001", Nil})
    aAdd(aCabec, {"F1_SERIE", "UNI", Nil})
    aAdd(aItens, {{"D1_COD", "P0001", Nil}})
    MsExecAuto({|x,y,z| MATA103(x, y, z)}, aCabec, aItens, 3)
    // BUG: nenhum check de lMsErroAuto aqui — disparar lint BP-003.
Return Nil
""",
    ),
    (
        "sql_embedded.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// 3 BeginSql blocks: 1 OK, 1 com SELECT * (PERF-001), 1 sem %notDel% (PERF-002).
User Function ZSQLMIX()
    Local cAliasOk  := GetNextAlias()
    Local cAliasBad := GetNextAlias()
    Local cAliasSb1 := GetNextAlias()

    // OK: campos explícitos + %notDel%
    BeginSql Alias cAliasOk
        SELECT A1_COD, A1_NOME
          FROM %table:SA1% SA1
         WHERE SA1.A1_FILIAL = %xFilial:SA1%
           AND %notDel%
    EndSql
    (cAliasOk)->(DbCloseArea())

    // BAD: SELECT * (lint PERF-001)
    BeginSql Alias cAliasBad
        SELECT *
          FROM %table:SA1% SA1
         WHERE SA1.A1_FILIAL = %xFilial:SA1%
           AND %notDel%
    EndSql
    (cAliasBad)->(DbCloseArea())

    // BAD: sem %notDel% (lint PERF-002)
    BeginSql Alias cAliasSb1
        SELECT B1_COD, B1_DESC
          FROM %table:SB1% SB1
         WHERE SB1.B1_FILIAL = %xFilial:SB1%
    EndSql
    (cAliasSb1)->(DbCloseArea())
Return Nil
""",
    ),
    (
        "encoding_cp1252.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Comentário com acentuação: ação, configuração, número, válido.
User Function ZENCCP()
    Local cMensagem := "Ação não permitida — veja seção"
    Local cTitulo   := "Atenção"
    MsgInfo(cMensagem, cTitulo)
Return Nil
""",
    ),
    (
        "encoding_utf8.prw",
        "utf-8",
        """\
#Include "protheus.ch"

// Comentário UTF-8 com multi-byte: configuração, número, validação, ação, êxito.
User Function ZENCU8()
    Local cMensagem := "Operação concluída — verificação OK"
    Local cTitulo   := "Êxito"
    MsgInfo(cMensagem, cTitulo)
Return Nil
""",
    ),
    # empty.prw → tratado fora do laço (write_bytes b"")
    # huge.prw  → tratado fora do laço (write_bytes b"// padding\n" * 500_000 ≈ 5MB)
    # corrupted.bak → tratado fora do laço (sufixo .bak deve ser ignorado)
    (
        "tlpp_namespace.tlpp",
        "utf-8",
        """\
#include "tlpp-core.th"

Namespace com.client.module

User Function ZNAMESP()
    Local cTexto := "TLPP namespaced module"
    ConOut(cTexto)
Return Nil
""",
    ),
    (
        "http_outbound.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Cliente HTTP saída — exercita HttpPost/HttpGet/MsAGetUrl (REST_CLIENT).
User Function ZHTTPCLI()
    Local cBody := '{"id":"000001"}'
    Local cResp := ""
    cResp := HttpPost("https://api.cliente.com.br/v1/clientes", "", cBody, 30, {})
    cResp := HttpGet("https://api.cliente.com.br/v1/clientes/1", "", 30, {})
    cResp := MsAGetUrl("https://api.cliente.com.br/v1/health")
Return cResp
""",
    ),
    (
        "mvc_hooks.prw",
        "cp1252",
        """\
#Include "protheus.ch"
#Include "fwmvcdef.ch"

Static Function ModelDef()
    Local oModel  := MPFormModel():New("ZHKM")
    Local oStruct := FWFormStruct(1, "SA1")
    Local bCommit := {|oM| ZGravar(oM)}
    Local bTudoOk := {|oM| ZValidar(oM)}
    Local bLineOk := {|oM| .T.}
    oModel:AddFields("SA1MASTER", , oStruct)
    oModel:SetCommit(bCommit)
    oModel:SetVldActivate(bTudoOk)
Return oModel

Static Function ZGravar(oModel)
Return .T.

Static Function ZValidar(oModel)
Return .T.
""",
    ),
    (
        "multi_filial.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Acessos a múltiplas filiais — exercita MULTI_FILIAL.
User Function ZMULTFIL()
    Local cFilOri := cFilAnt
    DbSelectArea("SA1")
    SA1->(DbSetOrder(1))
    If SA1->(MsSeek(xFilial("SA1") + "000001"))
        ConOut(SA1->A1_NOME)
    EndIf
    DbSelectArea("SB1")
    If SB1->(MsSeek(FwxFilial("SB1") + "PROD01"))
        ConOut(SB1->B1_DESC)
    EndIf
    cFilAnt := cFilOri
Return Nil
""",
    ),
    (
        "pubvars.prw",
        "cp1252",
        """\
#Include "protheus.ch"

// Anti-padrão: declaração PUBLIC — deve disparar lint MOD-002.
User Function ZPUBVAR()
    PUBLIC cGlobalNome := "ANTONIO"
    PUBLIC nGlobalNum  := 42
    ConOut(cGlobalNome)
Return Nil
""",
    ),
]


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    for nome, enc, conteudo in FIXTURES:
        out = HERE / nome
        # Escreve com encoding explícito para garantir bytes corretos
        # (cp1252 vs utf-8 é o que o parser detecta).
        out.write_bytes(conteudo.encode(enc))
        print(f"wrote {nome:32s} ({enc:7s} {out.stat().st_size:6d} bytes)")

    # empty.prw — 0 bytes, scan deve pular
    (HERE / "empty.prw").write_bytes(b"")
    print(f"wrote {'empty.prw':32s} (0       0 bytes)")

    # huge.prw — > 5MB, scan deve pular (MAX_FILE_BYTES = 5_000_000)
    huge = HERE / "huge.prw"
    huge.write_bytes(b"// padding\n" * 500_000)  # 500_000 * 11 = 5_500_000 bytes
    print(f"wrote {'huge.prw':32s} (cp1252  {huge.stat().st_size} bytes)")

    # corrupted.bak — sufixo .bak, scan deve pular
    corr = HERE / "corrupted.bak"
    corr.write_bytes(b"// arquivo corrompido com sufixo .bak - deve ser ignorado\n")
    print(f"wrote {'corrupted.bak':32s} (cp1252  {corr.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
