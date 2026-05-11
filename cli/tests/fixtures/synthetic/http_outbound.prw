#Include "protheus.ch"

// Cliente HTTP saída — exercita HttpPost/HttpGet/MsAGetUrl (REST_CLIENT).
User Function ZHTTPCLI()
    Local cBody := '{"id":"000001"}'
    Local cResp := ""
    cResp := HttpPost("https://api.cliente.com.br/v1/clientes", "", cBody, 30, {})
    cResp := HttpGet("https://api.cliente.com.br/v1/clientes/1", "", 30, {})
    cResp := MsAGetUrl("https://api.cliente.com.br/v1/health")
Return cResp
