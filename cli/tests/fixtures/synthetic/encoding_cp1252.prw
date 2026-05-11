#Include "protheus.ch"

// Comentário com acentuação: ação, configuração, número, válido.
User Function ZENCCP()
    Local cMensagem := "Ação não permitida — veja seção"
    Local cTitulo   := "Atenção"
    MsgInfo(cMensagem, cTitulo)
Return Nil
