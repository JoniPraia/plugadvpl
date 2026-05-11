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
