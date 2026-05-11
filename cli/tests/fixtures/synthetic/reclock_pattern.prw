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
