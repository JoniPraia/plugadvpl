#include "totvs.ch"
#include "restful.ch"

WSRESTFUL PortaldeViagem DESCRIPTION "API REST clássica de viagens"
    WSDATA cTipo  AS STRING
    WSDATA nLimit AS INTEGER OPTIONAL

    WSMETHOD GET    DESCRIPTION "Lista viagens"   WSSYNTAX "/viagem"
    WSMETHOD POST   DESCRIPTION "Cria viagem"     WSSYNTAX "/viagem"
END WSRESTFUL

WSMETHOD GET WSSERVICE PortaldeViagem
    Local oResp := JsonObject():New()
    oResp["status"] := "ok"
    ::SetResponse(oResp:ToJson())
Return .T.

WSMETHOD POST WSSERVICE PortaldeViagem
    Local oReq := JsonObject():New()
    oReq:FromJson(::GetContent())
    ::SetResponse('{"ok":true}')
Return .T.
