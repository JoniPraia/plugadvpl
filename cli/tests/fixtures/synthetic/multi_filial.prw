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
