#Include "protheus.ch"

// Anti-padrão: declaração PUBLIC — deve disparar lint MOD-002.
User Function ZPUBVAR()
    PUBLIC cGlobalNome := "ANTONIO"
    PUBLIC nGlobalNum  := 42
    ConOut(cGlobalNome)
Return Nil
