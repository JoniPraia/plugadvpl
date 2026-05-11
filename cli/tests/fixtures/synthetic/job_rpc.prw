#Include "protheus.ch"

// Job de processamento batch — abre ambiente via RpcSetEnv.
Main Function ZJOBSYNC()
    Local cEmp := "01"
    Local cFil := "010101"
    RpcSetEnv(cEmp, cFil, "admin", "msadmin", "FAT", "ZJOBSYNC")
    MsRunInThread({|| U_ZTASK01() })
    MsRunInThread({|| U_ZTASK02() })
    RpcClearEnv()
Return Nil

User Function ZTASK01()
    ConOut("ZTASK01 iniciado")
Return Nil

User Function ZTASK02()
    ConOut("ZTASK02 iniciado")
Return Nil
