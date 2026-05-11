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
