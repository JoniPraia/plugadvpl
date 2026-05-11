---
description: Tópicos avançados ADVPL — transações com Begin Transaction, relatórios TReport, FWTemporaryTable, manipulação de arquivos texto, MsNewGetDados, TCBrowse, OOP em ADVPL clássico, arredondamento NoRound, técnicas de programação eficiente. Use quando contexto sair do escopo básico de cadastros/MVC.
---

# advpl-advanced — Tópicos avançados ADVPL

ADVPL avançado cobre o que vai além do CRUD MVC básico: transações ACID, relatórios estruturados (TReport), manipulação de arquivos em massa, captura de informações multi-linha (grids dinâmicas), legacy `Modelo2`/`Modelo3`, e técnicas de programação eficiente.

## Quando usar

- Usuário pede "relatório", "TReport", "impressão", "PDF".
- Necessidade de `Begin Transaction` / `BeginTran` (gravações atômicas multi-tabela).
- Manipulação de arquivos texto (`.csv`, `.txt`, layouts EDI/SEFAZ) com `FCreate`/`FOpen`/`FRead`/`FWrite` ou `FT_FUse`/`FT_FReadLn`.
- Telas com grids dinâmicas (`MsNewGetDados`, `TCBrowse`) fora do contexto MVC.
- Performance de loops, arredondamento financeiro (`NoRound`), I/O bulk.
- Migrações de código `Modelo1`/`Modelo2`/`Modelo3`/`AxCadastro` (legacy) → MVC moderno.

## Transações — Begin Transaction × BeginTran

```advpl
Begin Transaction
    RecLock("SC5", .T.)
    SC5->C5_NUM := cNumPed
    MsUnlock()

    RecLock("SC6", .T.)
    SC6->C6_NUM := cNumPed
    MsUnlock()

    If lErro
        DisarmTransaction()
        Break
    EndIf
End Transaction
```

`Begin Transaction` é multi-tabela ACID. `BeginTran`/`EndTran` é forma alternativa. **Nunca** abra UI dentro de transação (trava o banco).

## TReport — relatórios estruturados

```advpl
oReport := TReport():New("XYZREL", "Relatorio XYZ", "XYZREL", {|oReport| ReportPrint(oReport)}, "Relatorio de demonstracao")
oSecao  := TRSection():New(oReport, "Itens", {"SA1"})
TRCell():New(oSecao, "A1_COD",  "SA1")
TRCell():New(oSecao, "A1_NOME", "SA1")
oReport:PrintDialog()
```

TReport substitui legacy `SetPrint`/`RptStatus`. Sai em PDF/Excel/CSV nativo.

## FWTemporaryTable — tabelas temporárias

Para queries complexas que precisam de tabela intermediária sem poluir SQL nativo:

```advpl
oTmp := FWTemporaryTable():New("TMP")
oTmp:SetFields({{"COD", "C", 6, 0}, {"VLR", "N", 14, 2}})
oTmp:AddIndex("01", {"COD"})
oTmp:Create()
// usa "TMP" como alias normal
oTmp:Delete()
```

## Manipulação de arquivos texto

Duas famílias:

- **Família 1**: `FCreate`/`FOpen`/`FRead`/`FWrite`/`FClose` — manipulação binária/baixo-nível.
- **Família 2**: `FT_FUse`/`FT_FReadLn`/`FT_FGoTop`/`FT_FEof` — leitura linha-a-linha eficiente (até GB).

Use Família 2 para layouts SEFAZ, SPED, EDI. Use Família 1 para arquivos binários ou pequenos.

## MsNewGetDados — grid dinâmica fora de MVC

```advpl
aHeader := {{"Codigo", "COD", "@!", 6, 0, "", "", "C", "", ""}, ...}
aCols   := {{"", "", .F.}}  // linha vazia inicial
oGrid := MsNewGetDados():New(0, 0, 200, 400, GD_INSERT+GD_UPDATE+GD_DELETE, ;
    "AllwaysTrue", "AllwaysTrue", "", , 999, , , , oDlg, aHeader, aCols)
```

Padrão para dialogs ad-hoc onde MVC seria over-engineering.

## OOP em ADVPL clássico — Class … Method

```advpl
Class TMyClass
    Data cAtributo
    Method New() Constructor
    Method DoSomething()
EndClass

Method New() Class TMyClass
    ::cAtributo := ""
Return Self

Method DoSomething() Class TMyClass
    ConOut("hello")
Return
```

Em TLPP, sintaxe é mais moderna (ver skill `advpl-tlpp`).

## Boas práticas de eficiência

- Use `For Each` em vez de `For/Next` com índice quando possível.
- Evite `+` em loop para construir strings — use array + `Array2String`.
- `NoRound(nValor, nCasas)` para arredondamento financeiro determinístico.
- Capitulação de palavras-chave: `Local`, `If`, `EndIf` em PascalCase (convenção).
- Evite `Public` global — use `Static` no fonte ou `Local` na função.

## Anti-padrões

- `AxCadastro`/`Modelo2`/`Modelo3` em código novo → `MOD-004` (deprecado).
- `MsgInfo`/`Alert` em JOB → bloqueia execução.
- `Begin Transaction` com UI dentro → deadlock garantido.
- Concatenar string em loop com `+` em vez de `Array2String`.
- Não tratar erros de `FOpen`/`FRead` (retornam `-1`).

## Referência profunda

Para detalhes completos (~2.3k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Apostila ADVPL II completa (TOTVS) com programação de atualização, browses, transações.
- Catálogo de relatórios TReport com TRSection, TRCell, TRPosition, fórmulas, agrupamentos.
- Família completa de manipulação de arquivos (Famílias 1 e 2, FwTemporary*, FWFileReader/Writer).
- Componentes de interface visual (TDialog, TGet, TButton, TFolder, TPanel, TBitmap, TScrollBox).
- Boas práticas: arredondamento, identação, capitulação, técnicas de programação eficiente.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function TReport` — relatórios indexados.
- `/plugadvpl:find function Begin Transaction` — transações no projeto.
- `/plugadvpl:lint <arq>` — detecta MOD-004 (rotina legacy).
