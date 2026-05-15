# plugadvpl CLI — Referência completa

Esta página documenta cada subcomando da CLI `plugadvpl` (atualizada para v0.4.3). A CLI é construída com [Typer](https://typer.tiangolo.com/) e expõe **21 subcomandos** mais um callback global com opções compartilhadas.

Use `plugadvpl --help` para ver a lista completa em runtime e `plugadvpl <subcomando> --help` para ver opções específicas.

## Sumário

- [Opções globais](#opcoes-globais)
- [Universo 1 — Fontes (v0.1)](#universo-1)
  - **write-path**: [`init`](#init), [`ingest`](#ingest), [`reindex`](#reindex)
  - **read-only**: [`status`](#status), [`find`](#find), [`callers`](#callers), [`callees`](#callees), [`tables`](#tables), [`param`](#param), [`arch`](#arch), [`lint`](#lint), [`doctor`](#doctor), [`grep`](#grep)
  - **utilitários**: [`version`](#version), [`help`](#help)
- [Universo 2 — Dicionário SX (v0.3)](#universo-2)
  - [`ingest-sx`](#ingest-sx), [`impacto`](#impacto), [`gatilho`](#gatilho), [`sx-status`](#sx-status)
- [Universo 3 — Rastreabilidade (v0.4)](#universo-3)
  - [`workflow`](#workflow), [`execauto`](#execauto), [`docs`](#docs)
- [Exit codes](#exit-codes)

---

## <a id="opcoes-globais"></a>Opções globais

Todas as opções abaixo aparecem ANTES do nome do subcomando: `plugadvpl --root D:/projeto --format json arch FATA050.prw`.

| Opção | Alias | Default | Descrição |
|---|---|---|---|
| `--root <path>` | `-r` | `.` (cwd) | Raiz do projeto cliente. Caminhos relativos são resolvidos a partir daqui. |
| `--format <fmt>` | `-f` | `table` | Formato de saída: `table` (rich), `json` (estruturado, machine-readable), `md` (markdown para colar no Claude). |
| `--quiet` | `-q` | `false` | Suprime títulos decorativos. JSON fica "puro" (sem títulos). |
| `--db <path>` | — | `<root>/.plugadvpl/index.db` | Caminho explícito do DB. Útil para testes ou múltiplos índices. |
| `--limit <N>` | — | `20` | Máximo de linhas no output. `0` = sem limite. |
| `--offset <N>` | — | `0` | Pular N linhas antes do limit. Paginação manual. |
| `--compact` | — | `false` | Output compacto: JSON sem indentação, tabelas sem bordas. |
| `--no-next-steps` | — | `false` | Desliga as sugestões de próximo comando (úteis para humano, ruído para Claude). |

**Read-only**: todos os subcomandos exceto `init`, `ingest` e `reindex` abrem o DB em modo `mode=ro` (URI SQLite). Não há risco de hot-write durante queries.

---

## <a id="universo-1"></a>Universo 1 — Fontes (v0.1)

Comandos clássicos pra indexar/consultar fontes ADVPL/TLPP do projeto.

### Subcomandos write-path

### <a id="init"></a>`init`

Cria o índice vazio em `<root>/.plugadvpl/index.db`, escreve o fragment plugadvpl em `CLAUDE.md` (idempotente, com marcadores `BEGIN/END plugadvpl`) e adiciona `.plugadvpl/` ao `.gitignore` se já existir.

```
plugadvpl init
```

**Faz:**

1. Aplica migration 001 (cria 22 tabelas + 2 FTS5 + indices).
2. Popula `meta` (project_root, cli_version, schema_version).
3. Carrega os 6 JSONs de `lookups/` (279+194+24+5+8+15 = 525 rows).
4. Escreve fragment em `CLAUDE.md` (cria se não existe).
5. Adiciona `.plugadvpl/` a `.gitignore` se o arquivo existir.

**Idempotente** — pode rodar várias vezes sem corromper estado.

---

### <a id="ingest"></a>`ingest`

Indexa todos os fontes `.prw`/`.prx`/`.tlpp`/`.apw`/`.ptm`/`.aph` em `--root`.

```
plugadvpl ingest [--workers N] [--incremental/--no-incremental]
                 [--no-content] [--redact-secrets]
```

**Opções:**

| Opção | Default | Descrição |
|---|---|---|
| `--workers <N>` / `-w` | `None` (adaptive) | Workers paralelos. `0`=single-thread; `None`=auto (<200 arquivos single, >=200 ProcessPool com `min(8, cpu_count())`). |
| `--incremental` / `--no-incremental` | `true` | Pula arquivos cujo `mtime` no DB é >= ao do filesystem. `--no-incremental` força reindex completo. |
| `--no-content` | `false` | Não persiste o corpo dos chunks — apenas metadata (funções, tabelas, calls). Reduz DB em ~80% e elimina risco de credenciais literais. |
| `--redact-secrets` | `false` | Mascara URLs com credenciais (`http://user:pwd@...`) e tokens hex longos (≥32 chars) antes de gravar `content`. |

**Pipeline interno**: scan → strip comentários/strings (preserve linhas) → parse (parser.py) → lint single-file (lint.py) → write em transação por arquivo → rebuild FTS5 ao final.

**Output (table)**:

```
                     Ingest summary
┌──────────────┬─────┬─────────┬────────┬────────┬───────────┬───────────────┬─────────────┐
│ arquivos_total│ ok  │ skipped │ failed │ chunks │ chamadas  │ lint_findings │ duration_ms │
├──────────────┼─────┼─────────┼────────┼────────┼───────────┼───────────────┼─────────────┤
│ 2000         │1997 │ 0       │ 3      │ 11243  │ 47892     │ 412           │ 38214       │
└──────────────┴─────┴─────────┴────────┴────────┴───────────┴───────────────┴─────────────┘
```

**Output (json --compact):**

```json
[{"arquivos_total":2000,"ok":1997,"skipped":0,"failed":3,"chunks":11243,"chamadas":47892,"lint_findings":412,"duration_ms":38214}]
```

---

### <a id="reindex"></a>`reindex <arq>`

Re-indexa UM arquivo após edição. Resolve `<arq>` por basename case-insensitive ou caminho relativo.

```
plugadvpl reindex FATA050.prw
plugadvpl reindex src/custom/MEUMOD.tlpp
```

Força `incremental=False` para esse arquivo, atualiza `parser_version` e dá rebuild nos dois índices FTS5.

---

## <a id="subcomandos-read-only"></a>Subcomandos read-only

### <a id="status"></a>`status`

Resumo do índice. Mostra contadores e metadata.

```
plugadvpl status [--check-stale]
```

**Output:**

```
              Status do índice
┌──────────────────┬──────────────────────────┐
│ chave            │ valor                    │
├──────────────────┼──────────────────────────┤
│ schema_version   │ 001                      │
│ cli_version      │ 0.1.0                    │
│ parser_version   │ p1.0.0                   │
│ fontes           │ 1987                     │
│ chunks           │ 11243                    │
│ chamadas         │ 47892                    │
│ lint_findings    │ 412                      │
│ project_root     │ /caminho/do/projeto      │
└──────────────────┴──────────────────────────┘
```

`--check-stale` adiciona uma segunda tabela com arquivos cujo mtime de filesystem é mais recente que o DB (precisa de `ingest --incremental`).

---

### <a id="find"></a>`find <termo>`

Busca composta: tenta resolver `<termo>` primeiro como nome de função (case-insensitive contra `fonte_chunks.funcao_norm`), depois como fragmento de arquivo (LIKE em `fontes.arquivo`), por último como conteúdo via FTS5.

```
plugadvpl find FATA050
plugadvpl find MaCntSA1
plugadvpl find "RECLOCK SA1"
```

Retorna até `--limit` resultados, ordenados por categoria (função > arquivo > FTS).

---

### <a id="callers"></a>`callers <funcao>`

Lista quem chama `<funcao>` consultando `chamadas_funcao.destino_norm` (uppercase, sem prefixo `U_`).

```
plugadvpl callers MaCntSA1
plugadvpl callers FATA050
```

**Output (json):**

```json
[
  {"arquivo_origem":"FATA060.prw","funcao_origem":"FATA060","linha_origem":234,"tipo":"U_"},
  {"arquivo_origem":"CTBA100.prw","funcao_origem":"GeraConta","linha_origem":89,"tipo":"static"}
]
```

---

### <a id="callees"></a>`callees <funcao>`

Lista quem `<funcao>` chama (espelho de `callers`).

```
plugadvpl callees FATA050
```

---

### <a id="tables"></a>`tables <T>`

Lista quem usa a tabela ADVPL `<T>` (ex: SA1, SC5, ZA1). Consulta `fonte_tabela` (tabela normalizada).

```
plugadvpl tables SA1
plugadvpl tables ZA1 --mode write
plugadvpl tables SC5 --mode reclock
```

**Opção:** `--mode {read|write|reclock}` filtra por tipo de uso. Sem filtro retorna todos.

---

### <a id="param"></a>`param <MV_*>`

Lista quem usa o parâmetro `<MV_*>` (GetMV/SuperGetMV/PutMV).

```
plugadvpl param MV_LOCALIZA
plugadvpl param MV_PAR01
```

---

### <a id="arch"></a>`arch <arquivo>`

**O comando mais importante.** Resumo arquitetural de UM fonte. Use ANTES de `Read` no Claude — economiza ~10× tokens.

```
plugadvpl arch FATA050.prw
plugadvpl arch FATA050 --format md
```

**Retorna em uma única "row" estruturada:**

- `arquivo`, `modulo`, `tipo`, `encoding`, `lines_of_code`
- `capabilities` (list: mvc, rest, job, pe, sx_dict, ...)
- `funcoes` + `user_funcs` + `pontos_entrada`
- `tabelas_ref` (read) + `write_tables` + `reclock_tables`
- `includes` (.ch usados)
- `calls_u` (chamadas a U_ funcs)
- Counters: número de chunks, chamadas, SQL embedados, lint findings

**Saída em md** é o formato preferido para enviar ao Claude — pronto para colar em contexto.

---

### <a id="lint"></a>`lint [arquivo]`

Lista findings (filtros opcionais).

```
plugadvpl lint                              # todos
plugadvpl lint FATA050.prw                  # apenas um arquivo
plugadvpl lint --severity critical          # filtra severidade
plugadvpl lint --regra BP-001               # filtra regra
plugadvpl lint --severity error --regra SEC-001
```

**Regras catalogadas (24 no `lint_rules`)** com categorias: `BP-*` (best practice), `SEC-*` (security), `PERF-*` (performance), `MOD-*` (modernization). O parser implementa 13 regras single-file ativas; restantes vêm em v0.2+.

---

### <a id="doctor"></a>`doctor`

Diagnósticos do índice. Cada check retorna `status ∈ {ok, warn, error}`.

```
plugadvpl doctor
```

Checks rodados:

- `encoding`: fontes sem encoding detectado
- `orphans`: chunks sem fonte (ou vice-versa)
- `fts_sync`: contagem FTS vs `fonte_chunks`
- `lookups`: as 6 lookup tables estão populadas?
- `migrations`: 001 aplicada?

Saída sugere próxima ação (`plugadvpl ingest --no-incremental`) se houver `error`/`warn`.

---

### <a id="grep"></a>`grep <pattern> [--mode]`

Busca textual sobre `fonte_chunks.content`.

```
plugadvpl grep "RECLOCK SA1"
plugadvpl grep "SA1->A1_COD" --mode literal
plugadvpl grep "MaCnt" --mode identifier
```

**Modos:**

| Modo | Engine | Para que serve |
|---|---|---|
| `fts` (default) | `fonte_chunks_fts` (unicode61 + tokenchars `_-`) | Busca por palavras/identifiers. `MaCnt*` casa com `MaCntSA1`. |
| `literal` | `fonte_chunks_fts_tri` (trigram) | Substring exata, inclusive pontuação ADVPL como `SA1->A1_COD`, `::New`, `%xfilial%`. |
| `identifier` | LIKE com `\b` em SQLite | Match por identifier exato (case-insensitive). |

---

## <a id="utilitarios"></a>Utilitários

### <a id="version"></a>`version`

Imprime a versão da CLI. Útil em scripts de validação e em `doctor`.

```
$ plugadvpl version
plugadvpl 0.4.3
```

### <a id="help"></a>`help`

Atalho equivalente a `plugadvpl --help`. Lista todos os 21 subcomandos.

---

## <a id="universo-2"></a>Universo 2 — Dicionário SX (v0.3)

Comandos pra indexar e consultar o dicionário SX exportado do Configurador
(SIGACFG → Misc → Exportar Dicionário em CSV).

### <a id="ingest-sx"></a>`ingest-sx <pasta-csv>`

Ingere os arquivos `sx1.csv`, `sx2.csv`, …, `sxg.csv` (formato exportação TOTVS)
em 11 tabelas: `tabelas` (SX2), `campos` (SX3), `gatilhos` (SX7),
`parametros` (SX6), `perguntas` (SX1), `consultas` (SXB), `pastas` (SXA),
`relacionamentos` (SX9), `indices` (SIX), `tabelas_genericas` (SX5),
`grupos_campo` (SXG).

```
plugadvpl ingest-sx <pasta-csv> [--no-incremental]
```

Apenas customizações do cliente — campos/parâmetros padrão TOTVS são
ignorados por design.

### <a id="impacto"></a>`impacto <campo>` — killer feature

Cruza referências a um campo SX3 em fontes ↔ SX3 ↔ SX7 (gatilhos) ↔ SX1
(perguntas/parâmetros). Resposta inclui chain expandido até `--depth 3`.

```
plugadvpl impacto A1_COD [--depth 1..3] [--format json]
```

Use quando precisar avaliar impacto de mudança em campo (rename, mudança
de tipo, deprecation).

### <a id="gatilho"></a>`gatilho <campo>`

Cadeia de gatilhos SX7 origem → destino, com `--depth 1..3` pra atravessar
gatilhos transitivos (campo X dispara gatilho que mexe em Y, que dispara
gatilho que mexe em Z).

### <a id="sx-status"></a>`sx-status`

Counts por tabela do dicionário SX ingerido. Sanity check de cobertura.

---

## <a id="universo-3"></a>Universo 3 — Rastreabilidade (v0.4)

Comandos pra indexar mecanismos de execução não-direta (workflow/schedule/
job/mail), chamadas indiretas via `MsExecAuto`, e documentação inline
Protheus.doc.

### <a id="workflow"></a>`workflow` (v0.4.0)

Lista os 4 mecanismos canônicos TOTVS de execução não-direta indexados:

```
plugadvpl workflow [--kind <kind>] [--target <nome>] [--arquivo <basename>]
```

| `--kind` | Detecção |
|---|---|
| `workflow` | `TWFProcess():New(...)`, `MsWorkflow(`, `WFPrepEnv(`, `:bReturn :=` |
| `schedule` | `Static Function SchedDef()` retornando `{cTipo,cPergunte,cAlias,aOrdem,cTitulo}` |
| `job_standalone` | `Main Function` + `RpcSetEnv` + `Sleep` loop (daemon ONSTART) |
| `mail_send` | `MailAuto(`, `SEND MAIL` UDC, `TMailManager`/`TMailMessage` |

Metadados específicos por `kind` (process_id, sched_type/pergunte/alias,
main_name/empresa/filial/modulo/sleep_seconds, variant/has_attachment/
uses_mv_rel) ficam em `metadata` no `--format json`.

### <a id="execauto"></a>`execauto` (v0.4.1)

Resolve a indireção do `MsExecAuto({|x,y,z| MATA410(x,y,z)}, ...)` cruzando
com catálogo TOTVS (31 rotinas em `lookups/execauto_routines.json`) pra
inferir tabelas tocadas indiretamente, módulo, e operação (3/4/5 →
inclusão/alteração/exclusão).

```
plugadvpl execauto [--routine <nome>] [--modulo <SIGAFAT>]
                   [--arquivo <basename>] [--op inc|alt|exc]
                   [--dynamic|--no-dynamic]
```

Enrichment do `arch`: campo `tabelas_via_execauto_resolvidas: list[str]`
agrega tabelas inferidas (campo bool antigo `tabelas_via_execauto` continua,
não-breaking).

Calls não-resolvíveis (`&(cVar)`, codeblock vazio, variável armazenada)
ficam com `routine=null, dynamic_call=true` — use `--dynamic` pra revisão.

### <a id="docs"></a>`docs [modulo]` (v0.4.2)

Catálogo de Protheus.doc agregado por módulo/autor/tipo/deprecação.

```
plugadvpl docs [<modulo>] [--author <nome>] [--funcao <nome>]
               [--arquivo <basename>] [--deprecated|--no-deprecated]
               [--tipo <type>] [--show <funcao>] [--orphans]
```

Modos:

- **Lista**: `docs SIGAFAT` ou `docs --author "Fernando" --deprecated`
- **Show formatado**: `docs --show MT460FIM` → Markdown estruturado completo
  (cabeçalho + tabela params + sections retorno/exemplos/histórico).
  Aceita `--arquivo` pra desambiguar homônimos (v0.4.3).
- **Orphans**: `docs --orphans` → cross-ref BP-007 do lint (funções sem header)

16 tags canônicas TOTVS extraídas estruturadamente: `@type`, `@author`,
`@since`, `@version`, `@description`, `@language`, `@deprecated`, `@param`,
`@return`, `@example`, `@history`, `@see`, `@table`, `@todo`, `@obs`,
`@link`. Tags fora do whitelist vão pro `raw_tags` catch-all (zero perda).

Inferência de módulo dual: path-based (`SIGA\w{3,4}` no path) +
routine-prefix (reaproveita catálogo do `execauto`).

---

## <a id="exit-codes"></a>Exit codes

| Code | Significado |
|---|---|
| `0` | OK |
| `1` | Resultado vazio mas semanticamente esperado (ex: `arch` em arquivo não indexado) |
| `2` | Erro de pré-requisito (DB não existe, arquivo não encontrado, root inválido) |
| `>2` | Typer-level (opções inválidas, abort) |

Em scripts shell, `0` significa "comando rodou" — ausência de resultados ainda é `0` na maioria dos casos (callers/callees/lint/etc retornam linha vazia, não erro).
