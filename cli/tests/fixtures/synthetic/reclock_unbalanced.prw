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
