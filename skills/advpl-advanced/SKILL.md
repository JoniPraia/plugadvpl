---
description: Tópicos avançados ADVPL — transações ACID (Begin Transaction + DisarmTransaction), relatórios TReport (TRSection/TRCell/TRFunction), FWTemporaryTable, manipulação de arquivos (FT_F* família 2 para SPED/EDI), MsNewGetDados, threads (MsRunInThread), OOP em ADVPL clássico (Class/Method/Self), reflection via Type/ValType, NoRound financeiro, anti-padrões legados (AxCadastro/Modelo2/Modelo3). Use quando contexto sair do escopo básico de cadastros/MVC.
---

# advpl-advanced — Tópicos avançados ADVPL

ADVPL avançado cobre o que vai além do CRUD MVC básico: transações ACID, relatórios estruturados (TReport), manipulação de arquivos em massa (SPED, EDI), captura de informações multi-linha (grids dinâmicas fora de MVC), threads paralelas, OOP clássico, e técnicas de programação eficiente.

## Quando usar

- Usuário pede "relatório", "TReport", "impressão", "PDF", "Excel".
- Necessidade de `Begin Transaction` / `BeginTran` (gravações atômicas multi-tabela).
- Manipulação de arquivos texto (`.csv`, `.txt`, layouts SPED/EDI/SEFAZ) com `FCreate`/`FOpen`/`FRead`/`FWrite` ou `FT_FUse`/`FT_FReadLn` (família 2).
- Telas com grids dinâmicas (`MsNewGetDados`, `TCBrowse`) fora do contexto MVC.
- Performance de loops, arredondamento financeiro (`NoRound`), I/O bulk.
- Threads paralelas com `MsRunInThread` (cuidado com WorkArea por thread).
- OOP em ADVPL clássico (`Class ... Method ... EndClass`).
- Migrações de código `Modelo1`/`Modelo2`/`Modelo3`/`AxCadastro` (legacy) → MVC moderno.

## Transações — Begin Transaction × BeginTran

```advpl
Begin Transaction
    RecLock("SC5", .T.)
    SC5->C5_NUM     := cNumPed
    SC5->C5_FILIAL  := xFilial("SC5")
    SC5->C5_CLIENTE := cCli
    SC5->(MsUnlock())

    RecLock("SC6", .T.)
    SC6->C6_FILIAL := xFilial("SC6")
    SC6->C6_NUM    := cNumPed
    SC6->C6_ITEM   := "01"
    SC6->(MsUnlock())

    If lErroNaValidacao
        DisarmTransaction()   // forca rollback explicito
        Break                  // sai do bloco
    EndIf
End Transaction
```

- `Begin Transaction` é multi-tabela ACID — garante atomicidade.
- `BeginTran`/`EndTran` é forma alternativa (mais rara).
- `DisarmTransaction()` antes do `Break` força rollback explícito.
- **NUNCA** abra UI (`MsgInfo`, `Pergunte`, `MsgBox`) dentro de transação — trava o banco com lock segurando.

Veja `[[advpl-code-review]]` regra BP-002 (impl: BEGIN TRANSACTION sem END) e `[[advpl-refactoring]]` padrão 6.

## TReport — relatórios estruturados (substitui SetPrint/RptStatus legacy)

```advpl
#include "TOTVS.CH"
#include "TBICONN.CH"
#include "TOPCONN.CH"
#include "RPTDEF.CH"

User Function ZRel01()
    Local oReport := Nil

    oReport := TReport():New( ;
        "ZREL01",;                                 // ID
        "Relatorio de Clientes",;                  // titulo
        "ZREL01",;                                 // pergunta SX1 (opcional)
        {|oReport| ReportPrint(oReport)},;         // callback
        "Lista clientes por grupo")                 // descricao

    DefineSecoes(oReport)
    oReport:PrintDialog()                          // abre dialog de impressao
Return Nil

Static Function DefineSecoes(oReport)
    Local oSec1 := TRSection():New(oReport, "Clientes", {"SA1"})
    TRCell():New(oSec1, "A1_COD",    "SA1", "Codigo", "@!", 6)
    TRCell():New(oSec1, "A1_NOME",   "SA1", "Nome",   "@!", 30)
    TRCell():New(oSec1, "A1_GRUPO",  "SA1", "Grupo",  "@!", 6)
Return Nil

Static Function ReportPrint(oReport)
    Local oSec1 := oReport:Section(1)
    oSec1:Init()
    DbSelectArea("SA1")
    DbGoTop()
    While !Eof()
        oSec1:PrintLine()
        SA1->(DbSkip())
    EndDo
    oSec1:Finish()
Return Nil
```

Saída: PDF / Excel / CSV / TXT / HTML nativo (usuário escolhe no dialog).

> **TReport** (singular) é a API canônica. **TReports** (plural) era uma classe anterior, hoje em desuso. Veja [diferença TReports vs TReport](https://terminaldeinformacao.com/2023/09/15/qual-a-diferenca-entre-treports-e-treport/).

## FWTemporaryTable — tabelas temporárias

Para queries complexas que precisam de tabela intermediária sem poluir SQL nativo (e sem `CREATE TABLE` direto que viola padrão):

```advpl
Local oTmp := FWTemporaryTable():New("TMP")
oTmp:SetFields({ ;
    {"COD",  "C", 6,  0}, ;
    {"DESC", "C", 30, 0}, ;
    {"VLR",  "N", 14, 2}, ;
    {"DT",   "D", 8,  0} ;
})
oTmp:AddIndex("01", {"COD"})
oTmp:Create()

// usa "TMP" como alias normal
DbSelectArea("TMP")
RecLock("TMP", .T.)
TMP->COD  := "001"
TMP->VLR  := 100.50
TMP->(MsUnlock())

// no fim, sempre limpar
oTmp:Delete()
```

Tabela existe só durante a sessão. Garbage collection automático no `:Delete()`.

## Manipulação de arquivos texto

Duas famílias:

### Família 1 — `FCreate`/`FOpen`/`FRead`/`FWrite`/`FClose` (baixo nível)

```advpl
Local nHnd := FCreate("\system\out.txt")
If nHnd < 0
    ConOut("Erro FCreate: " + cValToChar(FError()))
    Return
EndIf
FWrite(nHnd, "Linha 1" + Chr(13) + Chr(10))
FWrite(nHnd, "Linha 2" + Chr(13) + Chr(10))
FClose(nHnd)
```

Use Família 1 para arquivos binários ou pequenos. **Sempre cheque retorno < 0** (erro).

### Família 2 — `FT_FUse`/`FT_FReadLn`/`FT_FGoTop`/`FT_FEof` (eficiente, GB-scale)

```advpl
Local nHnd := FT_FUse("\system\sped.txt")
If nHnd < 0
    ConOut("Erro abrir arquivo")
    Return
EndIf

FT_FGoTop()
While !FT_FEof()
    cLinha := FT_FReadLn()
    ProcessaLinha(cLinha)
    FT_FSkip()
EndDo

FT_FUse()    // libera handle (FT_FUse sem args = close)
```

Use Família 2 para **SPED, EDI, layouts SEFAZ, arquivos > 100MB** — buffered, não carrega tudo em memória. Família 1 carrega o arquivo inteiro pra RAM.

### `MemoWrite` / `MemoRead` — atalho pra escrita rápida

```advpl
// Grava string em arquivo (sobrescreve)
MemoWrite("\system\debug.txt", cStr)

// Grava com append
MemoWrite("\system\debug.txt", cStr, .T.)

// Le inteiro
cContent := MemoRead("\system\debug.txt")
```

Útil para debug em JOB ou serialização rápida. **Não use** pra arquivos > 10MB (carrega tudo em memória).

## MsNewGetDados — grid dinâmica fora de MVC

```advpl
Local aHeader := {}
Local aCols   := {}
Local oGrid   := Nil

// aHeader: {titulo, campo, picture, tamanho, decimal, valid, usado, tipo, F3, when}
aAdd(aHeader, {"Codigo", "COD",  "@!",          6,  0, "", "", "C", "",       ""})
aAdd(aHeader, {"Nome",   "NOME", "@!",          30, 0, "", "", "C", "",       ""})
aAdd(aHeader, {"Valor",  "VLR",  "@E 999.999.999,99", 14, 2, "", "", "N", "", ""})

// aCols: array de arrays — cada linha é um array com 1 valor por coluna + flag deletado
aAdd(aCols, {"001", "Cliente A", 100.50, .F.})
aAdd(aCols, {"002", "Cliente B", 200.00, .F.})

oGrid := MsNewGetDados():New( ;
    0, 0, 200, 400,;                           // nTop, nLeft, nBottom, nRight
    GD_INSERT + GD_UPDATE + GD_DELETE,;        // operacoes permitidas
    "AllwaysTrue",;                            // bLineValid
    "AllwaysTrue",;                            // bTudoOk
    "",;                                       // cIniCpos
    ,;
    999,;                                      // max linhas
    , , ,;
    oDlg,;
    aHeader,;
    aCols)
```

Padrão para dialogs ad-hoc onde MVC seria over-engineering (ex: rotina de importação custom, popup de selecionar registros).

## OOP em ADVPL clássico

```advpl
#include "TOTVS.CH"

Class TCliente
    Data cCodigo
    Data cNome
    Data nLimite
    Data lAtivo

    Method New(cCodigo) Constructor
    Method GetNome()           // public
    Method SetLimite(nValor)   // public
    Method Save()              // public
EndClass

Method New(cCodigo) Class TCliente
    ::cCodigo := cCodigo
    ::cNome   := ""
    ::nLimite := 0
    ::lAtivo  := .T.
    If !Empty(cCodigo) .And. DbSelectArea("SA1") .And. DbSeek(xFilial("SA1") + cCodigo)
        ::cNome   := AllTrim(SA1->A1_NOME)
        ::nLimite := SA1->A1_LC
    EndIf
Return Self

Method GetNome() Class TCliente
Return ::cNome

Method SetLimite(nValor) Class TCliente
    If nValor < 0
        Return .F.
    EndIf
    ::nLimite := nValor
Return .T.

Method Save() Class TCliente
    DbSelectArea("SA1")
    DbSetOrder(1)
    If DbSeek(xFilial("SA1") + ::cCodigo)
        RecLock("SA1", .F.)
    Else
        RecLock("SA1", .T.)
        SA1->A1_FILIAL := xFilial("SA1")
        SA1->A1_COD    := ::cCodigo
    EndIf
    SA1->A1_NOME := ::cNome
    SA1->A1_LC   := ::nLimite
    SA1->(MsUnlock())
Return .T.
```

Uso:

```advpl
Local oCli := TCliente():New("000001")
oCli:SetLimite(5000)
oCli:Save()
ConOut(oCli:GetNome())
```

> ADVPL clássico não tem `private`/`protected` — todos os Data/Method são essencialmente públicos. TLPP corrige isso (veja `[[advpl-tlpp]]`).

## Threads — `MsRunInThread`

```advpl
// Dispara funcao XYZProcParalelo numa nova thread Protheus
Local lOk := MsRunInThread(0, "XYZProcParalelo", aDados)
// nSlot = 0 (qualquer); 2o param = nome da funcao; 3o em diante = args

Static Function XYZProcParalelo(aDados)
    Local aArea := GetArea()     // sempre saveArea por thread!
    Local nI

    For nI := 1 To Len(aDados)
        // processa item aDados[nI]
    Next nI

    RestArea(aArea)               // sempre restArea no fim
Return Nil
```

> **Crítico em thread:**
> - **Cada thread herda o ambiente do pai** (cFilAnt, cEmpAnt, RpcSetEnv state).
> - **Cada thread DEVE fazer seu próprio `GetArea`/`RestArea`** — sem isso, threads disputam o ponteiro do alias e geram bug "qual registro tô vendo?".
> - **Cada thread DEVE ter seu próprio `DbSelectArea`/`DbSetOrder`** — não confie no estado do pai.
> - **Limite prático**: pool default do AppServer aceita ~10-50 threads simultâneas. Acima disso, lentidão.

Veja `[[advpl-jobs-rpc]]` para mais detalhes em contexto JOB.

## Reflection — `Type`, `ValType`, `Eval`

```advpl
// Type retorna tipo de uma EXPRESSAO como string
cTipo := Type("nValor")              // "N", "C", "D", "L", "A", "O", "U" (undefined)

// ValType retorna tipo de um VALOR
cTipo := ValType(uValor)             // mesmo retorno

// Eval avalia codeblock em runtime
bBloco := {|x| x * 2}
nRet   := Eval(bBloco, 10)            // 20

// __ClassName retorna nome da classe (ADVPL OO)
cClasse := __ClassName(oObj)         // "TCliente"

// __ClassMethArr lista métodos da classe
aMtds := __ClassMethArr(oObj)
```

> Em TLPP, use `FwReflection` que é mais estruturado (veja `[[advpl-tlpp]]`).

## Boas práticas de eficiência

- **`NoRound(nValor, nCasas)`** para arredondamento financeiro determinístico (evita banker's rounding implícito).
- **`For Each`** em vez de `For/Next` com índice quando possível (mais legível).
- **Evite `+` em loop** para construir strings — use array + `FwArrayJoin` (em TOTVS R26+) ou `Array2String` (legacy).
- **Capitulação**: `Local`, `If`, `EndIf` em PascalCase (convenção TOTVS).
- **`Static`** no fonte ou **`Local`** na função em vez de `Public` global — escopo limpo.
- **`AScan`** em vez de loop manual para busca em array.
- **`aSize(arr, n)`** para redimensionar em vez de criar novo.
- **`FwTimeStamp()`** em vez de concat `Date() + Time()` (mais rápido + formato ISO).

## Anti-padrões legados (referenciados pelo lint)

- **`AxCadastro`/`Modelo2`/`Modelo3`** em código novo → catalogado `MOD-004` (não detectado pelo lint atual, mas é warning conceitual). Veja `[[advpl-refactoring]]` padrão 4.
- **`MsgInfo`/`Alert` em JOB** → bloqueia execução. Veja `[[advpl-jobs-rpc]]`.
- **`Begin Transaction` com UI dentro** → deadlock garantido. BP-002 (impl).
- **Concatenar string em loop com `+`** em vez de array + `FwArrayJoin` (PERF-004 catalog).
- **Não tratar erros** de `FOpen`/`FRead`/`FT_FUse` (retornam `-1` ou `< 0`) → exception silenciosa.
- **Thread sem `GetArea`/`RestArea`** → corrompe contexto do pai.
- **`MemoRead` em arquivo > 10MB** → carrega tudo em RAM, pode estourar memória.
- **TReport sem `:Finish()`** na seção → última linha não imprime.
- **OOP clássico assumindo encapsulamento** — ADVPL não tem private/protected, tudo é público.

## Cross-references com outras skills

- `[[advpl-tlpp]]` — OOP moderno com private/protected/static + namespaces.
- `[[advpl-refactoring]]` — `AxCadastro` → MVC, concat em loop → array.
- `[[advpl-fundamentals]]` — Static/Local/Private/Public scopes; reservadas.
- `[[advpl-code-review]]` — BP-002 (Transaction), BP-005 (>6 params), PERF-001/002/003.
- `[[advpl-embedded-sql]]` — SQL em transação, MPSysOpenQuery.
- `[[advpl-mvc]]` — quando preferir MVC vs MsNewGetDados ad-hoc.
- `[[advpl-jobs-rpc]]` — threads e RpcSetEnv em background.
- `[[advpl-encoding]]` — arquivos cp1252 vs UTF-8 quando ler/escrever texto.
- `[[advpl-debugging]]` — debug de transação travada, lock órfão.
- `[[plugadvpl-index-usage]]` — `/plugadvpl:find function TReport`, etc.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function TReport` — relatórios indexados no projeto.
- `/plugadvpl:grep "Begin Transaction\|BeginTran"` — transações.
- `/plugadvpl:grep "MsRunInThread\|StartJob"` — threading.
- `/plugadvpl:grep "FT_FUse\|FCreate"` — manipulação de arquivos.
- `/plugadvpl:grep "Class.*Method\|EndClass"` — OOP clássico.
- `/plugadvpl:lint <arq>` — checa BP-001 (RecLock+MsUnlock), BP-002 (Transaction), BP-005 (>6 params), BP-006 (RecLock raw mix), MOD-001/002 (ConOut, Public).
- Tabela `operacoes_escrita` cataloga todos os `RecLock`+`MsUnlock` patterns do projeto.

## Referência profunda

Para detalhes completos (~2.3k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Apostila ADVPL II completa (TOTVS) com programação de atualização, browses, transações.
- Catálogo de relatórios TReport com TRSection, TRCell, TRPosition, TRFunction, fórmulas, agrupamentos.
- Família completa de manipulação de arquivos (Famílias 1 e 2, FWTemporary*, FWFileReader/Writer).
- Componentes de interface visual (TDialog, TGet, TButton, TFolder, TPanel, TBitmap, TScrollBox).
- Boas práticas: arredondamento, identação, capitulação, técnicas de programação eficiente.
- Padrões de OOP em ADVPL clássico — singleton, factory, observer (com workarounds para falta de private).

## Sources

- [Criação de relatórios em 10 minutos AdvPL - Terminal de Informação](https://terminaldeinformacao.com/2017/01/29/criacao-de-relatorios-em-10-minutos-em-advpl/)
- [TReport TRFunction TRSection TRCell - Maratona AdvPL TL++ 505](https://terminaldeinformacao.com/2024/06/28/criando-relatorios-com-treport-trfunction-trsection-e-trcell-maratona-advpl-e-tl-505/)
- [Diferença entre TReports e TReport - Terminal de Informação](https://terminaldeinformacao.com/2023/09/15/qual-a-diferenca-entre-treports-e-treport/)
- [Criando arquivos com MemoWrite - Maratona AdvPL 345](https://terminaldeinformacao.com/2024/04/09/criando-arquivos-com-a-memowrite-maratona-advpl-e-tl-345/)
- [Boas Práticas em Transações ADVPL (PDF)](https://www.scribd.com/document/390059884/Boas-Praticas-Transacoes-em-ADVPL)
- [Controle de transações - TDN](https://tdn.totvs.com/pages/viewpage.action?pageId=271843449)
- [Classes em AdvPL - Tudo em AdvPL](https://siga0984.wordpress.com/2014/12/02/classes-em-advpl-parte-02/)
- [Acelerando o AdvPL - Importação de tabelas](https://siga0984.wordpress.com/2018/12/20/acelerando-o-advpl-importacao-de-tabelas/)
