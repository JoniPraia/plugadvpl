---
description: SQL embarcado em ADVPL/TLPP — BeginSql/EndSql (preferido), TCQuery (legacy), TCSqlExec (DML), MPSysOpenQuery (autosetfield). Macros obrigatórias %notDel%, %xfilial%, %table%, %exp%, %Order%, %top%, %LIMIT%. Use ao gerar/editar query SQL embarcada, refatorar TCQuery+RetSqlName pra BeginSql, ou revisar regras PERF-001/002/003 e SEC-001 do lint.
---

# advpl-embedded-sql — SQL nativo em ADVPL/TLPP

ADVPL/TLPP suporta SQL embarcado direto no fonte com **substituição por macros** que garantem multi-empresa, multi-filial, anti-SQL-injection e portabilidade entre DBMS (Oracle, SQL Server, Postgres, DB2 via DBAccess).

Famílias de execução SQL no Protheus:

| Comando / Função      | Tipo     | Use quando                                              |
|-----------------------|----------|---------------------------------------------------------|
| **`BeginSql/EndSql`** | SELECT   | **Default pra novo código**, suporta macros             |
| `TCQuery`             | SELECT   | Legacy. Equivalente ao BeginSql mas string crua         |
| `TCGenQry`            | SELECT   | Internamente usado por `TCQuery`; raramente direto      |
| **`MPSysOpenQuery`**  | SELECT   | Como TCQuery mas com `TCSetField` automático dos campos dicionarizados |
| **`TCSqlExec`**       | DML/DDL  | UPDATE/DELETE/INSERT/CREATE direto no DBMS              |

## Quando usar

- Edit/criação de qualquer query SQL no fonte ADVPL.
- Refator de SQL legado (`TCQuery` + concatenação → `BeginSql`).
- Revisão de regra `PERF-001`/`PERF-002`/`PERF-003` ou `SEC-001` do lint.
- DML em massa (atualização cross-tabela) — usar `TCSqlExec` em vez de loop ADVPL com `RecLock`.
- Antes de testar performance — sem macros, queries dão problema em produção multi-empresa.

## Macros obrigatórias do `BeginSql`

| Macro                | O que faz                                            | Output           | Safe injection |
|----------------------|------------------------------------------------------|------------------|----------------|
| `%table:TABLE%`      | Resolve nome físico (`SA1010` em vez de `SA1`)       | identifier       | sim            |
| `%xfilial:TABLE%`    | Valor atual da filial, já entre aspas                | string literal   | sim            |
| `%notDel%`           | Filtro `D_E_L_E_T_ = ' '` (registros não-deletados)  | predicate        | sim            |
| `%exp:VAR%`          | Binda variável ADVPL com escaping automático         | scalar literal   | sim            |
| `%Order:TABLE%`      | Resolve `ORDER BY` da chave primária (índice 1)      | columns          | sim            |
| `%top:N%`            | `TOP N` / `ROWNUM <= N` / `LIMIT N` conforme DBMS     | clause           | sim            |
| `%LIMIT:N%`          | Variante explícita pra paginação (alguns DBMS)        | clause           | sim            |

**Concatenação com `+` para incluir variável é proibida** — viola `SEC-001` em código pré-v0.3.0 (catalog) e quebra `PERF-002`/`PERF-003` no impl atual quando não tem `%notDel%`/`%xfilial%`.

## Exemplo canônico — `BeginSql`

```advpl
Local cCodCli  := "000001"
Local cFilNF   := "01"

BeginSql Alias "QRY"
    SELECT SF2.F2_DOC, SF2.F2_SERIE, SF2.F2_EMISSAO,
           SD2.D2_COD, SD2.D2_QUANT, SD2.D2_TOTAL
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

// Tipagem de colunas — recomendado se a coluna nao bate o tipo default
TCSetField("QRY", "F2_EMISSAO", "D")
TCSetField("QRY", "D2_QUANT",   "N", 11, 2)
TCSetField("QRY", "D2_TOTAL",   "N", 14, 2)

While !QRY->(Eof())
    // ...processa
    QRY->(DbSkip())
EndDo
QRY->(DbCloseArea())
```

> **Quirk:** o `*` (asterisco) **não pode ser primeiro char de linha** dentro de `BeginSql` — o pré-processador ADVPL trata como comentário (`*` é comentário de linha em alguns dialetos). Use indentação ou move pro fim da linha anterior.

## `MPSysOpenQuery` — TCQuery com tipagem automática

Variante moderna do `TCQuery` que faz `TCSetField` automaticamente para colunas que estão no SX3 — elimina o esforço manual:

```advpl
Local cSql := "SELECT F2_DOC, F2_EMISSAO, F2_VALMERC " + ;
              "  FROM " + RetSqlName("SF2") + " " + ;
              " WHERE F2_FILIAL = '" + xFilial("SF2") + "'"

MPSysOpenQuery(cSql, "QRY")
// F2_EMISSAO ja vem como Date (D), F2_VALMERC como Numeric (N, 14, 2)
// Nao precisa de TCSetField manual

While !QRY->(Eof())
    // ...
    QRY->(DbSkip())
EndDo
QRY->(DbCloseArea())
```

Quando usar `MPSysOpenQuery` vs `BeginSql`:
- `BeginSql` se vai escrever SQL novo limpo (preferido).
- `MPSysOpenQuery` se está mantendo legacy que usa string concat — pelo menos automatiza TCSetField.

## `TCSqlExec` — DML direto no banco

Para UPDATE/DELETE/INSERT em massa (mais rápido que loop ADVPL com `RecLock`):

```advpl
Local cSql := ""
Local nRet := 0

// IMPORTANTE: monte a query com aspas e filial via xFilial — TCSqlExec NÃO tem macros
cSql := "UPDATE " + RetSqlName("SA1") + " " + ;
        "   SET A1_BLOQ = 'S' " + ;
        " WHERE A1_FILIAL = '" + xFilial("SA1") + "' " + ;
        "   AND A1_RISCO  = 'E' " + ;
        "   AND D_E_L_E_T_ = ' '"

Begin Transaction
    nRet := TCSqlExec(cSql)
    If nRet < 0
        // erro — TCSqlExec retorna negativo em falha
        DisarmTransaction()
        ConOut("UPDATE falhou: " + TCSqlError())
        Break
    EndIf
End Transaction
```

> **Anti-pattern:** `TCSqlExec` sem `Begin Transaction` quando faz múltiplos updates relacionados → estado inconsistente em caso de falha.

> **Crítico:** `TCSqlExec` **não tem macros** (`%notDel%`/`%xfilial%`). Você precisa expandir manualmente. **Esquecer `%xfilial%` aqui causa cross-filial corruption** — UPDATE pode atingir todas as filiais.

## Limitações do cursor de query

Um cursor aberto por `BeginSql`/`TCQuery`/`MPSysOpenQuery` é **read-only** e tem navegação limitada:

| Operação                                   | Funciona?   |
|--------------------------------------------|-------------|
| `QRY->(DbSkip())`  (avança)                | ✓           |
| `QRY->(DbGoTop())` (volta pro início)      | ✓           |
| `QRY->(DbSkip(-1))` (volta uma linha)      | ❌ não      |
| `QRY->(DbGoBottom())` (vai pra última)     | ❌ não      |
| `QRY->(RecLock())` ou `Replace`/`FieldPut` | ❌ não      |
| `QRY->(LastRec)` / `QRY->(RecCount())`     | ❌ retorna 0 (use `Count(*)` no SQL) |

Pra contar linhas, use `SELECT COUNT(*) ...` em vez de `RecCount()` sobre o cursor.

## Macros equivalentes — `BeginSql` vs ADVPL puro

| Macro `BeginSql`        | Equivalente ADVPL                | Notas                                    |
|-------------------------|----------------------------------|------------------------------------------|
| `%table:T%`             | `RetSqlName("T")`                | Nome físico da tabela                    |
| `%xfilial:T%`           | `"'" + xFilial("T") + "'"`       | Valor atual da filial (com aspas)        |
| `%notDel%`              | `D_E_L_E_T_ = ' '`               | Filtro soft-delete                       |
| `%exp:cVar%`            | (NÃO use concat — `SEC-001`)     | Bind seguro                              |
| `%Order:T%`             | `IndexKey()` da chave 1          | Order by chave primária                  |
| `%top:N%`               | `TOP N` / `ROWNUM<=N` / `LIMIT N`| Limite cross-DBMS                        |
| `%LIMIT:N%`             | `LIMIT N` (Postgres/MySQL)       | Variante explícita                       |

## Regras de lint relacionadas (impl real v0.3.3)

| Regra      | Severidade | Comportamento real (impl)                                              |
|------------|------------|------------------------------------------------------------------------|
| `PERF-001` | warning    | `SELECT *` em `BeginSql`/`TCQuery`                                     |
| `PERF-002` | error      | SQL contra tabela Protheus **sem `%notDel%`** (registros deletados)    |
| `PERF-003` | error      | SQL contra tabela Protheus **sem `%xfilial%`** (cross-filial leak)     |
| `SEC-001`  | critical   | `RpcSetEnv` dentro de REST (não é SQL injection — veja `[[advpl-code-review]]`) |
| `SX-006`   | warning    | `X3_VALID` no SX3 com `BeginSql`/`TCQuery` (query a cada validação)    |

Catalogadas mas **não implementadas** (use como checklist mental):

- `PERF-004` — Concatenação de string com `+` em loop
- `PERF-005` — `RecCount() > 0` para checar existência (use `!Eof()`)
- `PERF-006` — `WHERE`/`ORDER BY` em coluna sem índice

## Workflow recomendado

1. Antes de escrever SQL, busque exemplos no projeto:
   - `/plugadvpl:grep "BeginSql"` — queries existentes
   - `/plugadvpl:tables <T> --mode read` — quem lê a tabela
2. Use sempre `BeginSql ... EndSql` para queries novas.
3. **Liste explicitamente** as colunas (`SELECT F2_DOC, F2_SERIE, ...`) — nunca `SELECT *`.
4. Adicione `%notDel%` em **toda** tabela ADVPL que aparecer no `FROM`/`JOIN`.
5. Adicione `%xfilial:TABLE%` no `WHERE` para filtro multi-filial.
6. Bind variáveis com `%exp:` — nunca concatene.
7. Após `EndSql`, chame `TCSetField` para `D` (data) e `N` (numérico) se a coluna não for dicionarizada. Em legacy com `MPSysOpenQuery`, isso é automático.
8. Sempre `DbCloseArea()` no fim ou em `Recover` (proteção contra leak de cursor).
9. Para DML em massa, use `TCSqlExec` dentro de `Begin Transaction`, com check de retorno (`nRet < 0` indica erro).
10. Rode `/plugadvpl:lint <arq>` pra confirmar — pega `PERF-001/002/003`.

## Anti-padrões

```advpl
// SEC-001 catalog (impl: outra coisa, mas ainda vulnerabilidade real)
// — SQL injection
cSql := "SELECT * FROM " + RetSqlName("SA1") + " WHERE A1_COD = '" + cCod + "'"

// PERF-001 — SELECT *
BeginSql Alias "QRY"
    SELECT * FROM %table:SA1% SA1 WHERE SA1.%notDel%
EndSql

// PERF-002 — sem %notDel% (impl real)
BeginSql Alias "QRY"
    SELECT A1_COD FROM %table:SA1% SA1
     WHERE SA1.A1_FILIAL = %xfilial:SA1%
       AND SA1.A1_GRUPO  = %exp:cGrupo%
       -- esqueceu SA1.%notDel% — traz registros DELETADOS
EndSql

// PERF-003 — sem %xfilial% (impl real)
BeginSql Alias "QRY"
    SELECT C5_NUM FROM %table:SC5% SC5
     WHERE SC5.C5_EMISSAO >= %exp:dInicio%
       AND SC5.%notDel%
       -- esqueceu SC5.C5_FILIAL = %xfilial:SC5% — vaza dados de OUTRAS FILIAIS
EndSql

// Pseudo-PERF-002 (legacy, não detectado mas crítico):
//   DbSeek dentro de While quando JOIN/IN resolveria
While !SC5->(Eof())
    DbSelectArea("SA1")
    DbSetOrder(1)
    DbSeek(xFilial("SA1") + SC5->C5_CLIENTE)  // N seeks
    SC5->(DbSkip())
EndDo
// Refactor em [[advpl-refactoring]] padrão 1.

// Cursor mal-fechado — leak
BeginSql Alias "QRY"
    SELECT ... FROM ...
EndSql
While !QRY->(Eof())
    // ...
    If alguma_condicao
        Return                    // ESQUECEU DbCloseArea!
    EndIf
    QRY->(DbSkip())
EndDo
// Use Begin Sequence / Recover ou QRY->(DbCloseArea()) antes do Return

// TCSqlExec cross-filial leak — esquece WHERE filial
TCSqlExec("UPDATE " + RetSqlName("SA1") + " SET A1_BLOQ='S' WHERE A1_GRUPO='X'")
// CORRETO: incluir A1_FILIAL = '" + xFilial("SA1") + "'"

// TCSqlExec em transação sem check de retorno
Begin Transaction
    TCSqlExec(cSql1)      // se falhou, nROllback não acontece
    TCSqlExec(cSql2)      // continua executando
End Transaction
// CORRETO: nRet := TCSqlExec(...); If nRet < 0; DisarmTransaction(); Break; EndIf

// Loop sobre cursor com DbGoTop várias vezes
While !QRY->(Eof())
    QRY->(DbGoTop())      // só funciona porque é o ÚNICO movimento back; muito ineficiente
EndDo
```

## Cross-references com outras skills

- `[[advpl-code-review]]` — regras PERF-001/002/003 (lint) e SX-006 (cross-file).
- `[[advpl-refactoring]]` — padrão 1: DbSeek em loop → SQL embarcado.
- `[[advpl-fundamentals]]` — tipos de variável, declaração `Local` antes de query.
- `[[advpl-dicionario-sx-validacoes]]` — `X3_VALID` com `BeginSql` é anti-pattern SX-006.
- `[[advpl-mvc]]` / `[[advpl-mvc-avancado]]` — queries dentro de hooks MVC.
- `[[advpl-debugging]]` — quando query "trava" ou "retorna 0 linhas" (cursor read-only).
- `[[advpl-jobs-rpc]]` — `TCSqlExec` em jobs de manutenção em massa.
- `[[plugadvpl-index-usage]]` — `/plugadvpl:tables`, `/plugadvpl:grep "BeginSql"`.

## Referência rápida

| Função / Comando        | Para que serve                                                  |
|-------------------------|-----------------------------------------------------------------|
| `BeginSql / EndSql`     | SELECT com macros (preferido)                                   |
| `TCQuery` (legacy)      | SELECT sem macros — migrate pra BeginSql                        |
| `MPSysOpenQuery`        | SELECT que aplica `TCSetField` automático nos campos SX3        |
| `TCSqlExec`             | DML/DDL — UPDATE/DELETE/INSERT/CREATE                           |
| `TCSqlError`            | Mensagem de erro da última operação SQL                         |
| `TCGetLastQuery`        | Retorna a última query executada (debug)                        |
| `TCSetField`            | Define tipo de coluna pós-query (D, N, C, L)                    |
| `RetSqlName("T")`       | Nome físico da tabela (uso fora de BeginSql)                    |
| `ChangeQuery(cSql)`     | Aplica conversões cross-DBMS na string                          |
| `DbCloseArea()`         | Fecha cursor — SEMPRE no final ou em Recover                    |

## Comandos plugadvpl relacionados

- `/plugadvpl:grep "BeginSql\|TCQuery"` — busca queries existentes.
- `/plugadvpl:tables <T> --mode read` — quem lê a tabela.
- `/plugadvpl:tables <T> --mode write` — quem grava (Replace, UPDATE, TCSqlExec).
- `/plugadvpl:lint <arq>` — executa PERF-001/002/003 e SEC-001.
- `/plugadvpl:lint --cross-file --regra SX-006` — X3_VALID com SQL no dicionário.

## Referência profunda

Para detalhes completos (~1.6k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Catálogo completo de macros (`%table%`, `%notDel%`, `%xfilial%`, `%exp%`, `%Order%`, `%Limit%`, `%top%`, `%FieldsList%`).
- Diferenças entre `BeginSql`/`TCQuery`/`TCGenQry`/`MPSysOpenQuery`/`PLSQuery` e quando usar cada.
- Padrões de paginação (LIMIT/OFFSET por DBMS — Oracle ROWNUM × SQL Server TOP × Postgres LIMIT).
- Uso correto de `TCSetField` para tipagem pós-query e implicações de performance.
- Exemplos de queries complexas com JOIN multi-tabela + filtros de filial + tratamento de NULL.

## Sources

- [Embedded SQL - Guia de Boas Práticas - TDN](https://tdn.totvs.com/pages/viewpage.action?pageId=27675608)
- [Embedded SQL - Frameworksp - TDN](https://tdn.totvs.com/display/framework/Embedded+SQL)
- [Comandos DML em SQL: DBAccess - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360024805754)
- [Como Executar Queries com BeginSQL e EndSQL - ProtheusAdvpl](https://protheusadvpl.com.br/como-utilizar-beginsql-endsql-no-advpl/)
- [Executando Instruções SQL com TCSQLExec - ProtheusAdvpl](https://protheusadvpl.com.br/como-executar-instrucoes-sql-com-tcsqlexec-no-advpl/)
- [Diferença entre TCQuery e PLSQuery - Terminal de Informação](https://terminaldeinformacao.com/2020/08/27/qual-a-diferenca-entre-tcquery-e-plsquery/)
- [Desenvolvendo queries no Protheus - TDN Homolog](https://tdn-homolog.totvs.com/display/public/framework/Desenvolvendo+queries+no+Protheus)
- [TCSQLExec x TCQuery - BlackTDN](https://www.blacktdn.com.br/2025/12/dnatech-tcsqlexec-x-tcquery-quando-o.html)
- [Vários TcSqlExec dentro de mesma transação - TOTVS Dev Forum](https://devforum.totvs.com.br/377-varios-tcsqlexec-dentro-de-uma-mesma-transacao)
