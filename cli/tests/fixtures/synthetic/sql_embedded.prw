#Include "protheus.ch"

// 3 BeginSql blocks: 1 OK, 1 com SELECT * (PERF-001), 1 sem %notDel% (PERF-002).
User Function ZSQLMIX()
    Local cAliasOk  := GetNextAlias()
    Local cAliasBad := GetNextAlias()
    Local cAliasSb1 := GetNextAlias()

    // OK: campos explícitos + %notDel%
    BeginSql Alias cAliasOk
        SELECT A1_COD, A1_NOME
          FROM %table:SA1% SA1
         WHERE SA1.A1_FILIAL = %xFilial:SA1%
           AND %notDel%
    EndSql
    (cAliasOk)->(DbCloseArea())

    // BAD: SELECT * (lint PERF-001)
    BeginSql Alias cAliasBad
        SELECT *
          FROM %table:SA1% SA1
         WHERE SA1.A1_FILIAL = %xFilial:SA1%
           AND %notDel%
    EndSql
    (cAliasBad)->(DbCloseArea())

    // BAD: sem %notDel% (lint PERF-002)
    BeginSql Alias cAliasSb1
        SELECT B1_COD, B1_DESC
          FROM %table:SB1% SB1
         WHERE SB1.B1_FILIAL = %xFilial:SB1%
    EndSql
    (cAliasSb1)->(DbCloseArea())
Return Nil
