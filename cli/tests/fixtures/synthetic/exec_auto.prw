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
