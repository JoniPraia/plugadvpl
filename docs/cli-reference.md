# plugadvpl CLI — Referência completa

Esta página documenta cada subcomando da CLI `plugadvpl` v0.1.0. A CLI é construída com [Typer](https://typer.tiangolo.com/) e expõe **14 subcomandos** mais um callback global com opções compartilhadas.

Use `plugadvpl --help` para ver a lista completa em runtime e `plugadvpl <subcomando> --help` para ver opções específicas.

## Sumário

- [Opções globais](#opcoes-globais)
- [Subcomandos write-path (alteram o índice)](#subcomandos-write-path)
  - [`init`](#init)
  - [`ingest`](#ingest)
  - [`reindex`](#reindex)
- [Subcomandos read-only (consultas)](#subcomandos-read-only)
  - [`status`](#status)
  - [`find`](#find)
  - [`callers`](#callers)
  - [`callees`](#callees)
  - [`tables`](#tables)
  - [`param`](#param)
  - [`arch`](#arch)
  - [`lint`](#lint)
  - [`doctor`](#doctor)
  - [`grep`](#grep)
- [Utilitários](#utilitarios)
  - [`version`](#version)
- [Reservado para v0.2+](#reservado-para-v02)
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

## <a id="subcomandos-write-path"></a>Subcomandos write-path

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
plugadvpl 0.1.0
```

---

## <a id="reservado-para-v02"></a>Reservado para v0.2+

Os subcomandos abaixo já têm tabelas reservadas no schema mas **não estão implementados no MVP v0.1.0**:

- `plugadvpl impacto <tabela|campo>` — análise de impacto cross-fonte (Universo 3)
- `plugadvpl native <funcao>` — lookup em `funcoes_nativas` (já populada — 279 rows)
- `plugadvpl restricted <funcao>` — lookup em `funcoes_restritas` (já populada — 194 rows)
- `plugadvpl pe <nome>` — lookup em `pontos_entrada_padrao` (já populada — 15 rows)
- `plugadvpl modulo <codigo>` — lookup em `modulos_erp` (já populada — 8 rows)
- `plugadvpl dict <SX1|SX3|SXE|...>` — Universo 2 (dicionário SX) — schema migration 002

Roadmap detalhado em `docs/superpowers/specs/2026-05-11-plugadvpl-design.md` §15.

---

## <a id="exit-codes"></a>Exit codes

| Code | Significado |
|---|---|
| `0` | OK |
| `1` | Resultado vazio mas semanticamente esperado (ex: `arch` em arquivo não indexado) |
| `2` | Erro de pré-requisito (DB não existe, arquivo não encontrado, root inválido) |
| `>2` | Typer-level (opções inválidas, abort) |

Em scripts shell, `0` significa "comando rodou" — ausência de resultados ainda é `0` na maioria dos casos (callers/callees/lint/etc retornam linha vazia, não erro).
