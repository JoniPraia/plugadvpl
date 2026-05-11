---
description: SQL embarcado em ADVPL — BeginSql/EndSql, TCQuery, macros obrigatórias %notDel%, %xfilial%, %table%, %exp%, %Order%, 6 restrições de performance e segurança.
---

# advpl-embedded-sql — SQL nativo em ADVPL

ADVPL/TLPP suporta SQL embarcado direto no fonte com **substituição por macros** que garantem multi-empresa, multi-filial, anti-SQL-injection e portabilidade entre DBMS (Oracle, SQL Server, Postgres, DB2).

Existem duas formas principais:

1. **`BeginSql alias <ALIAS> ... EndSql`** — recomendado, suporta macros.
2. **`TCQuery cSql NEW ALIAS <ALIAS>`** — antigo, sem macros (string crua).

## Quando usar

- Edit/criação de qualquer query SQL no fonte ADVPL.
- Refator de SQL legado (`TCQuery` → `BeginSql`).
- Revisão de regra `PERF-001..006` ou `SEC-001`.
- Antes de testar performance — sem macros, queries dão problema em produção multi-empresa.

## As 5 macros obrigatórias

| Macro                | O que faz                                            | Output           | Safe injection |
|----------------------|------------------------------------------------------|------------------|----------------|
| `%table:TABLE%`      | Resolve nome físico (`SA1010` em vez de `SA1`)       | identifier       | sim            |
| `%xfilial:TABLE%`    | Valor atual da filial, já entre aspas                | string literal   | sim            |
| `%notDel%`           | Filtro `D_E_L_E_T_ <> '*'` (registros não-deletados) | predicate        | sim            |
| `%exp:VAR%`          | Binda variável ADVPL com escaping automático         | scalar literal   | sim            |
| `%Order:TABLE%`      | Resolve `ORDER BY` da chave primária da tabela       | columns          | sim            |

**Concatenação com `+` para incluir variável é proibida** — viola `SEC-001` (crítico, SQL injection).

## Exemplo correto — BeginSql

```advpl
Local cCodCli := "000001"
Local cFilNF  := "01"

BeginSql Alias "QRY"
    SELECT SF2.F2_DOC, SF2.F2_SERIE, SF2.F2_EMISSAO, SD2.D2_COD, SD2.D2_QUANT
      FROM %table:SF2% SF2
      JOIN %table:SD2% SD2
        ON SD2.D2_FILIAL = SF2.F2_FILIAL
       AND SD2.D2_DOC    = SF2.F2_DOC
       AND SD2.D2_SERIE  = SF2.F2_SERIE
       AND SD2.D2_CLIENTE= SF2.F2_CLIENTE
       AND SD2.%notDel%
     WHERE SF2.F2_FILIAL = %xfilial:SF2%
       AND SF2.F2_CLIENTE= %exp:cCodCli%
       AND SF2.%notDel%
     ORDER BY %Order:SF2%
EndSql

// Tipagem de colunas — recomendado (PERF-003)
TCSetField("QRY", "F2_EMISSAO", "D")
TCSetField("QRY", "D2_QUANT",   "N", 11, 2)

While QRY->(!Eof())
    // ...processa
    QRY->(DbSkip())
EndDo
QRY->(DbCloseArea())
```

## As 6 restrições de SQL embarcado (regras de lint)

| Regra      | Severidade | O que não fazer                                                          |
|------------|------------|--------------------------------------------------------------------------|
| `PERF-001` | critical   | `SELECT *` em BeginSql ou TCQuery — fetcha colunas inúteis, memo fields  |
| `PERF-002` | warning    | `DbSeek` dentro de `While`/`For` quando JOIN/IN resolveria               |
| `PERF-003` | warning    | Faltar `TCSetField` para datas/numéricos pós-query                       |
| `PERF-004` | warning    | Concatenação de string com `+`/`+=` em loop (use array + `Array2String`) |
| `PERF-005` | warning    | `RecCount()` para checar existência — use `!Eof()` (full scan)           |
| `PERF-006` | info       | `WHERE`/`ORDER BY` em colunas sem índice (consulte SIX)                  |
| `SEC-001`  | critical   | SQL com `+ cVar +` em vez de `%exp:cVar%` — SQL injection                |

## TCQuery (legacy) — quando aparece

```advpl
// Estilo antigo — funciona, mas sem macros
Local cSql := "SELECT F2_DOC FROM " + RetSqlName("SF2") + " "
cSql += "WHERE F2_FILIAL = '" + xFilial("SF2") + "' "
cSql += "  AND F2_CLIENTE = '" + cCodCli + "' "
cSql += "  AND D_E_L_E_T_ <> '*'"

TCQuery cSql NEW ALIAS "QRY"
```

**Migrate para `BeginSql`** sempre que possível. Se manter `TCQuery`, **NUNCA** concatene variável de input — use `%exp:` em string template do `BeginSql`.

## `RetSqlName`, `xFilial` (equivalentes ADVPL)

Quando precisar de SQL fora de `BeginSql` (ex: query dinâmica complexa):

- `RetSqlName("SA1")` ↔ `%table:SA1%` (retorna nome físico).
- `xFilial("SA1")` ↔ `%xfilial:SA1%` (retorna filial atual, sem aspas — precisa adicionar).
- `D_E_L_E_T_ <> '*'` ↔ `%notDel%`.

## Workflow recomendado

1. Antes de escrever SQL, rode `/plugadvpl:sql --op select --table SF2` para ver exemplos existentes no projeto.
2. Use sempre `BeginSql ... EndSql` para queries novas.
3. Liste **explicitamente** as colunas (`SELECT F2_DOC, F2_SERIE, ...`) — nunca `SELECT *`.
4. Adicione `%notDel%` em **toda** tabela ADVPL que aparecer no `FROM`/`JOIN`.
5. Adicione `%xfilial:TABLE%` no `WHERE` para filtro multi-filial.
6. Bind variáveis com `%exp:` — nunca concatene.
7. Após `EndSql`, chame `TCSetField` para `D` (data) e `N` (numérico).
8. Sempre `DbCloseArea()` no fim ou em `Recover`.

## Anti-padrões

```advpl
// SEC-001 — SQL injection
cSql := "SELECT * FROM SA1010 WHERE A1_COD = '" + cCod + "'"

// PERF-001 — SELECT *
BeginSql Alias "QRY"
    SELECT * FROM %table:SA1% SA1 WHERE SA1.%notDel%
EndSql

// PERF-002 — DbSeek em loop
While SC5->(!Eof())
    DbSelectArea("SA1")
    DbSetOrder(1)
    DbSeek(xFilial("SA1") + SC5->C5_CLIENTE)  // N seeks; melhor um JOIN
    SC5->(DbSkip())
EndDo

// PERF-005 — RecCount para checar existência
If RecCount() > 0   // full scan; melhor !Eof()
```

## Referência rápida

| Macro / função          | Equivalente                | Quando                  |
|-------------------------|----------------------------|-------------------------|
| `%table:T%`             | `RetSqlName("T")`          | FROM/JOIN               |
| `%xfilial:T%`           | `"'" + xFilial("T") + "'"` | WHERE T_FILIAL =        |
| `%notDel%`              | `D_E_L_E_T_ <> '*'`        | Todo predicate de tabela|
| `%exp:cVar%`            | `"'" + cVar + "'"` (NÃO)   | Bind seguro de variável |
| `%Order:T%`             | `IndexKey()` da chave 1    | ORDER BY                |
| `TCSetField`            | —                          | Pós-query, tipagem      |

## Comandos plugadvpl relacionados

- `/plugadvpl:sql --op {select|insert|update|delete} --table <T>` — busca SQL existente.
- `/plugadvpl:lint <arq>` — executa PERF-001..006 e SEC-001.
- `/plugadvpl:tables <T>` — lista quem usa a tabela.

## Referência profunda

Para detalhes completos (~1.6k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Catálogo completo de macros `%`-prefixed (`%table%`, `%notDel%`, `%xfilial%`, `%exp%`, `%Order%`, `%Limit%`, `%top%`, `%FieldsList%`).
- Diferenças entre `BeginSql`/`TCQuery`/`TCGenQry` e quando usar cada uma.
- Padrões de paginação (LIMIT/OFFSET por DBMS — Oracle rownum × SQL Server TOP × Postgres LIMIT).
- Uso correto de `TCSetField` para tipagem pós-query e implicações de performance.
- Exemplos de queries complexas com JOIN multi-tabela + filtros de filial + tratamento de NULL.
