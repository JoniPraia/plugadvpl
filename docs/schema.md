# plugadvpl — Schema SQLite

Este documento descreve o schema do `.plugadvpl/index.db` na versão MVP v0.1.0. O schema é **baseado** em projeto interno anterior do autor (validado em ampla base de fontes ADVPL) + deltas necessários para uso como plugin local Claude Code.

## Visão geral

```
v0.1.0 schema (migration 001_initial.sql):
  - 22 tabelas físicas (Universo 1 — Fontes)
  - 2 FTS5 virtuais (dual-index strategy)
  - 6 lookups pré-populadas (525+ rows total)
  - 1 tabela auxiliar normalizada (fonte_tabela)
  - 2 tabelas internas (meta, ingest_progress, _migrations)
```

**Reservado para v0.2+** (via migrations 002+):

- Universo 2: Dicionário SX (SX1, SX3, SXE, SX6, ...)
- Universo 3: Rastreabilidade cross-fonte e análise de impacto

---

## ER overview

```mermaid
erDiagram
    fontes ||--o{ fonte_chunks         : "1:N CASCADE"
    fontes ||--o{ fonte_tabela         : "1:N CASCADE"
    fontes ||--o{ funcao_docs          : "1:N logical"
    fontes ||--o{ chamadas_funcao      : "arquivo_origem"
    fontes ||--o{ parametros_uso       : "MV_* usage"
    fontes ||--o{ perguntas_uso        : "SX1 groups"
    fontes ||--o{ operacoes_escrita    : "RecLock/SQL DML"
    fontes ||--o{ sql_embedado         : "BeginSql/TCQuery"
    fontes ||--o{ rest_endpoints       : "WSSERVICE/@Get"
    fontes ||--o{ http_calls           : "HttpGet outbound"
    fontes ||--o{ env_openers          : "RpcSetEnv/Open"
    fontes ||--o{ log_calls            : "FwLogMsg/conout"
    fontes ||--o{ defines              : "#DEFINE"
    fontes ||--o{ lint_findings        : "BP/SEC/PERF/MOD"
    fonte_chunks ||--|| fonte_chunks_fts     : "external content"
    fonte_chunks ||--|| fonte_chunks_fts_tri : "trigram view"

    fontes {
        TEXT arquivo PK
        TEXT caminho_relativo UK
        TEXT modulo
        TEXT capabilities
        INTEGER mtime_ns
        TEXT encoding
    }
    fonte_chunks {
        TEXT id PK
        TEXT arquivo FK
        TEXT funcao
        TEXT funcao_norm
        INTEGER linha_inicio
        INTEGER linha_fim
        TEXT content
    }
    chamadas_funcao {
        INTEGER id PK
        TEXT arquivo_origem
        TEXT funcao_origem
        TEXT destino
        TEXT destino_norm
        TEXT tipo
    }
    fonte_tabela {
        TEXT arquivo PK
        TEXT tabela PK
        TEXT modo PK
    }
```

Resumo textual:

```
                            +----------------+
                            |     fontes     | (PRIMARY KEY: arquivo)
                            +----------------+
                                    ^
                            FK CASCADE ON DELETE
                |-------------------|-------------------|
                |                   |                   |
        +---------------+   +---------------+   +---------------+
        | fonte_chunks  |   | fonte_tabela  |   |  funcao_docs  |
        +---------------+   +---------------+   +---------------+
                |
                | (content='fonte_chunks', content_rowid='rowid')
                v
        +---------------------+
        |  fonte_chunks_fts   | (FTS5 - unicode61 + tokenchars '_-')
        | fonte_chunks_fts_tri| (FTS5 - trigram para substring exata)
        +---------------------+

  Tabelas-satelite (FK logica via arquivo, sem CASCADE):
    chamadas_funcao, parametros_uso, perguntas_uso, operacoes_escrita,
    sql_embedado, rest_endpoints, http_calls, env_openers, log_calls,
    defines, lint_findings

  Lookups embarcadas (WITHOUT ROWID, pre-populadas no init):
    funcoes_nativas, funcoes_restritas, lint_rules,
    sql_macros, modulos_erp, pontos_entrada_padrao

  Internas:
    meta, ingest_progress, _migrations
```

---

## Universo 1 — Fontes (8 tabelas)

### `fontes`

Linha por arquivo `.prw`/`.tlpp`/`.prx`/`.apw`/`.ptm`/`.aph` indexado.

| Coluna | Tipo | Origem | Notas |
|---|---|---|---|
| `arquivo` | TEXT PK | basename | "FATA050.prw" |
| `caminho` | TEXT | FS path original | "D:/Projeto/src/.../FATA050.prw" |
| `caminho_relativo` | TEXT UNIQUE | normalizado | lowercase, forward slashes, relativo ao `--root` |
| `tipo` | TEXT | parser | "custom" \| "padrao" |
| `modulo` | TEXT | parser | "FAT", "CTB", "EST", ... |
| `funcoes` | TEXT (JSON) | parser | lista de top-level functions |
| `user_funcs` | TEXT (JSON) | parser | lista de `User Function` |
| `pontos_entrada` | TEXT (JSON) | parser | PEs detectados (cruzar com `pontos_entrada_padrao`) |
| `tabelas_ref` | TEXT (JSON) | parser | tabelas lidas |
| `write_tables` | TEXT (JSON) | parser | tabelas escritas (RecLock+Replace, Tcsqlexec INSERT/UPDATE/DELETE) |
| `reclock_tables` | TEXT (JSON) | parser | apenas RecLock (subset de write) |
| `includes` | TEXT (JSON) | parser | .ch usados |
| `calls_u` | TEXT (JSON) | parser | chamadas a `U_xxx` (custom functions) |
| `calls_execblock` | TEXT (JSON) | parser | ExecBlock("FUNC", ...) calls |
| `fields_ref` | TEXT (JSON) | parser | campos referenciados (SA1->A1_COD) |
| `lines_of_code` | INTEGER | scanner | total lines |
| `hash` | TEXT | scanner | SHA-256 do conteúdo |
| `source_type` | TEXT | parser | "rotina" \| "fonte_classe" \| "wsservice" \| "include" \| ... |
| `capabilities` | TEXT (JSON) | parser | ["mvc", "rest", "job", "pe", "sx_dict"] |
| `ws_structures` | TEXT (JSON) | parser | WSCLIENT/WSDATA hierarquia |
| `encoding` | TEXT | scanner | "cp1252" \| "utf-8" |
| `mtime_ns` | INTEGER | scanner | mtime do FS em nanoseconds (delta plugin) |
| `size_bytes` | INTEGER | scanner | tamanho em bytes (delta plugin) |
| `indexed_at` | TEXT | DEFAULT now() | timestamp da última ingestão |
| `namespace` | TEXT | parser | TLPP namespace (vazio para PRW) |
| `tipo_arquivo` | TEXT | scanner | "prw" \| "tlpp" \| "prx" \| "apw" \| ... |
| `parser_version` | TEXT | ingester | versão do parser usado nesta ingestão |

**Índices:** `idx_fontes_modulo`, `idx_fontes_source_type`, `idx_fontes_caminho_rel`.

---

### `fonte_chunks`

Linha por **função** (ou método/PE/header) extraída. ID composto: `<arquivo>::<funcao>`.

| Coluna | Tipo | Notas |
|---|---|---|
| `id` | TEXT PK | `"FATA050.prw::FATA050"` |
| `arquivo` | TEXT FK → fontes.arquivo | ON DELETE CASCADE |
| `funcao` | TEXT | nome original (case preserved) |
| `funcao_norm` | TEXT | uppercase + trim (case-insensitive lookup) |
| `tipo_simbolo` | TEXT | function \| static_function \| user_function \| main_function \| method \| ws_method \| mvc_hook \| class \| header |
| `classe` | TEXT | preenchido se `METHOD ... CLASS X` |
| `linha_inicio` / `linha_fim` | INTEGER | range no arquivo |
| `assinatura` | TEXT | linha do header (parametros, return) |
| `content` | TEXT | corpo (pode ser NULL se `ingest --no-content`) |
| `modulo` | TEXT | herdado de `fontes.modulo` |

**Índices:** `idx_chunks_arquivo`, `idx_chunks_funcao` (NOCASE), `idx_chunks_funcao_norm`, `idx_chunks_tipo`.

---

### `chamadas_funcao`

Edges do call graph. Uma row por call site.

| Coluna | Notas |
|---|---|
| `arquivo_origem` + `funcao_origem` + `linha_origem` | onde a chamada acontece |
| `tipo` | "U_" \| "static" \| "method" \| "execblock" \| "wsmethod" |
| `destino` | nome original chamado |
| `destino_norm` | uppercase + sem prefixo `U_` (lookup case-insensitive) |
| `arquivo_destino` / `funcao_destino` | resolved post-ingest (NULL se externo) |
| `contexto` | snippet curto |

**Índices:** `idx_cf_origem`, `idx_cf_destino` (NOCASE), `idx_cf_destino_norm`.

---

### `parametros_uso`

Uso de parâmetros MV_* via GetMV/SuperGetMV/PutMV.

| Coluna | Notas |
|---|---|
| `arquivo` | source |
| `parametro` | "MV_LOCALIZA" |
| `modo` | "read" \| "write" \| "read_write" |
| `default_decl` | default declarado |

**Índices:** `idx_pu_param`, `idx_pu_arquivo`.

---

### `perguntas_uso`

Grupos de perguntas SX1 referenciados (Pergunte/SXBuscaPerg).

| Coluna | Notas |
|---|---|
| `arquivo`, `grupo` | "FAT050", "CTB100", ... |

---

### `operacoes_escrita`

Operações de escrita em tabelas (RecLock+Replace, MsExecAuto INSERT, TCSqlExec mutativo).

| Coluna | Notas |
|---|---|
| `arquivo` + `funcao` | onde |
| `tipo` | "reclock_replace" \| "msexecauto" \| "sql_insert" \| "sql_update" \| "sql_delete" |
| `tabela` | nome da tabela (3 chars + filial) |
| `campos` | JSON list |
| `origens` | JSON map {campo: origem (literal/var)} |
| `condicao` | snippet do WHERE |

---

### `sql_embedado`

SQL nativo dentro do .prw (BeginSql/EndSql, TCSqlExec/TCQuery).

| Coluna | Notas |
|---|---|
| `arquivo`, `funcao`, `linha` | onde |
| `operacao` | "select" \| "insert" \| "update" \| "delete" |
| `tabelas` | JSON list (com macros `%xfilial%`, `%table:SX1%` resolvidas) |
| `snippet` | primeiras N chars |

---

### `funcao_docs`

Docstrings/comentários estruturados extraídos de cabeçalhos de função.

| Coluna | Notas |
|---|---|
| `arquivo` + `funcao` | PK composta |
| `tipo`, `assinatura`, `resumo`, `params`, `retorno` | extraídos |
| `tabelas_ref`, `campos_ref`, `chama`, `chamada_por` | listas extraídas do header |
| `fonte` | "auto" (extracted) vs "manual" |
| `resumo_auto` | gerado se header não tem comentário (v0.2+) |

---

## Nível 2 — Extrações novas (5 tabelas)

Extrações novas (não estavam no baseline interno), valiosas para análise moderna.

### `rest_endpoints`

WSSERVICE + WSMETHOD GET/POST + TLPP `@Get/@Post/@Put/@Delete`.

| Coluna | Notas |
|---|---|
| `arquivo`, `classe`, `funcao`, `verbo`, `path` | endpoint info |
| `annotation_style` | "wsmethod_classico" \| "@verb_tlpp" |

**Índices:** `idx_rest_verb`, `idx_rest_path`.

### `http_calls`

Chamadas HTTP outbound (HttpGet/HttpPost/HttpsPost/MsAGetUrl).

### `env_openers`

`RpcSetType` + `RpcSetEnv` + `OpenEnv` — pontos de entrada em jobs e processos batch.

### `log_calls`

`FwLogMsg` + `conout` para mapeamento de telemetria.

### `defines`

Macros `#DEFINE NOME VALOR` para resolução de identifiers em queries.

---

## Nível 3 — Lint (1 tabela)

### `lint_findings`

| Coluna | Notas |
|---|---|
| `arquivo` + `funcao` + `linha` | localização |
| `regra_id` | FK lógica → `lint_rules.regra_id` (BP-001, SEC-002, ...) |
| `severidade` | "critical" \| "error" \| "warning" |
| `snippet` | linha exata |
| `sugestao_fix` | herdado de `lint_rules.fix_guidance` |

**Índices:** `idx_lint_arquivo`, `idx_lint_regra`, `idx_lint_sev`.

---

## Tabela auxiliar normalizada

### `fonte_tabela`

`(arquivo, tabela, modo)` denormalizado para lookup reverso O(log N). Sem essa tabela, `plugadvpl tables SA1` precisaria fazer full-scan em `fontes.tabelas_ref` (JSON).

| Coluna | Notas |
|---|---|
| `arquivo` | FK → fontes.arquivo CASCADE |
| `tabela` | "SA1" (uppercase) |
| `modo` | "read" \| "write" \| "reclock" |

PRIMARY KEY composta `(arquivo, tabela, modo)`, WITHOUT ROWID.
Índice: `idx_ft_tabela (tabela NOCASE, modo)`.

---

## Lookups embarcadas (6 tabelas)

Todas `WITHOUT ROWID`, populadas no `init` a partir de `cli/plugadvpl/lookups/*.json`. Esses dados foram **extraídos do projeto [advpl-specialist](https://github.com/thalysjuvenal/advpl-specialist)** (Thalys Augusto, MIT) via `scripts/extract_lookups.py` — crédito completo em [NOTICE](../NOTICE).

| Tabela | Rows | Conteúdo |
|---|---|---|
| `funcoes_nativas` | 279 | Funções nativas do TOTVS Protheus com categoria, assinatura, params_count, requer_unlock, requer_close_area, deprecated, alternativa |
| `funcoes_restritas` | 194 | Funções bloqueadas/proibidas com data de bloqueio e alternativa recomendada |
| `lint_rules` | 24 | Regras de lint catalogadas (BP-*, SEC-*, PERF-*, MOD-*) com severidade, descrição, fix_guidance |
| `sql_macros` | 5 | Macros TOTVS SQL: `%xfilial%`, `%table:XXX%`, `%notdel%`, etc. — descrição + safe_for_injection flag |
| `modulos_erp` | 8 | Módulos ERP Protheus (FAT, CTB, EST, FIN, COM, GPE, ...) com prefixos de tabelas/funções típicos |
| `pontos_entrada_padrao` | 15 | PEs catalogados (M460FIM, MT100GRV, MA040FIM, ...) com paramixb_count, retorno_tipo, link_tdn |

---

## Internas (3 tabelas)

### `meta`

Key-value store para metadados do índice.

```
schema_version    -> "001"
cli_version       -> "0.1.0"
parser_version    -> "p1.0.0"
project_root      -> "/caminho/do/projeto"
ingested_at       -> "2026-05-11T13:00:00Z"
```

### `ingest_progress`

Tracking de progresso por arquivo (status: pending\|ingesting\|done\|failed). Usado pelo runner paralelo para recuperar de crash.

### `_migrations`

Tracking de migrations aplicadas. `WITHOUT ROWID`.

```
filename         | applied_at
-----------------+--------------------
001_initial.sql  | 2026-05-11 13:00:00
```

A função `apply_migrations(conn)` lê os `.sql` files em `cli/plugadvpl/migrations/` em ordem alfabética, pula os já registrados em `_migrations`, executa o resto em transações separadas. Idempotente.

---

## FTS5 dual-index strategy

Duas tabelas virtuais FTS5 sobre o mesmo "external content" (`fonte_chunks.content`, indexado por `rowid`):

### `fonte_chunks_fts` — Índice A (unicode61 com tokenchars)

```sql
USING fts5(
    arquivo, funcao, content,
    content='fonte_chunks',
    content_rowid='rowid',
    tokenize = "unicode61 remove_diacritics 2 tokenchars '_-'"
)
```

**Para que serve:** busca por palavras inteiras e identifiers ADVPL com underscore/hífen.

- `tokenchars '_-'` faz `A1_COD` e `FW-Browse` serem **um único token** (sem o flag, FTS5 quebra em `A1` + `COD`).
- `remove_diacritics 2` ajuda em comentários em português.

**Uso típico:** `plugadvpl grep MaCnt` ou `plugadvpl find termo`.

### `fonte_chunks_fts_tri` — Índice B (trigram)

```sql
USING fts5(
    content,
    content='fonte_chunks',
    content_rowid='rowid',
    tokenize = 'trigram'
)
```

**Para que serve:** substring exata com pontuação ADVPL.

- `SA1->A1_COD` (operador `->`) não é tokenizável pelo Índice A.
- `%xfilial%` (macros SQL com `%`) idem.
- `::New`, `PARAMIXB[1]`, `oModel:Activate()` idem.

Trigram (disponível desde SQLite 3.34) indexa qualquer substring de 3+ chars. Custa mais espaço, mas é a única forma de pesquisar pontuação literal sem fallback a LIKE.

**Uso típico:** `plugadvpl grep "SA1->A1_COD" --mode literal`.

### Sincronização

O ingest não usa triggers automáticos — em vez disso, faz `INSERT INTO fonte_chunks_fts(fonte_chunks_fts) VALUES('rebuild')` ao final de cada ingest/reindex. Trade-off: simplicidade e performance de bulk ingest vs latência de rebuild (~2s para 11k chunks).

---

## Padrões de PRAGMA

Os PRAGMAs init-time são aplicados programaticamente em `open_db()`, NÃO no SQL da migration (porque `page_size` só vale em DB vazio e `journal_mode` depende de detecção de network share):

```python
PRAGMA page_size = 8192;               # Optimal para text-heavy workloads
PRAGMA journal_mode = WAL;             # WAL em local; DELETE em network share
PRAGMA journal_size_limit = 67108864;  # 64 MiB
PRAGMA synchronous = NORMAL;           # WAL + NORMAL = boa durabilidade
PRAGMA temp_store = MEMORY;
PRAGMA cache_size = -64000;            # 64 MiB cache
PRAGMA foreign_keys = ON;
```

A detecção de WAL-incompatibilidade (network drives, SMB) é feita no momento de abrir o DB — se detectar, faz fallback a `journal_mode=DELETE`.

---

## Reservado para v0.2+

Schema futuro (não implementado na migration 001):

**Universo 2 — Dicionário SX**

- `sx1_perguntas` (grupos do Pergunte)
- `sx3_campos` (estrutura das tabelas: tipo, tamanho, validações)
- `sx6_parametros` (catálogo de MV_*)
- `sxe_sxf_sequencias` (sequenciadores)
- `sx2_tabelas` (catálogo geral)

**Universo 3 — Rastreabilidade cross-fonte**

- `impacto_funcao` (cruza chamadas + tabelas + PEs)
- `impacto_tabela` (todos os fontes que tocam uma tabela)
- `impacto_campo` (cruza com sx3_campos para análise field-level)

Detalhes em `docs/superpowers/specs/2026-05-11-plugadvpl-design.md` §11–§13.

---

## Queries úteis

Exemplos prontos para colar em `sqlite3 .plugadvpl/index.db` ou em scripts ad-hoc. Estes mesmos padrões alimentam internamente os subcomandos do CLI.

### Quem chama uma função (call graph reverso)

```sql
-- Equivalente a: plugadvpl callers MaFisRef
SELECT arquivo_origem, funcao_origem, linha_origem, tipo
FROM chamadas_funcao
WHERE destino_norm = UPPER('MaFisRef')
ORDER BY arquivo_origem, linha_origem;
```

### Quais fontes leem/gravam uma tabela

```sql
-- Equivalente a: plugadvpl tables SA1 --mode read
SELECT arquivo, modo
FROM fonte_tabela
WHERE tabela = 'SA1' COLLATE NOCASE
ORDER BY modo, arquivo;

-- Apenas RecLock (escrita posicionada — costuma indicar negócio crítico)
SELECT arquivo FROM fonte_tabela
WHERE tabela = 'SA1' AND modo = 'reclock';
```

### Top 10 funções mais chamadas

```sql
SELECT destino_norm AS funcao, COUNT(*) AS n_chamadas
FROM chamadas_funcao
GROUP BY destino_norm
ORDER BY n_chamadas DESC
LIMIT 10;
```

### Fontes com mais lint findings críticos

```sql
SELECT arquivo, COUNT(*) AS n_critical
FROM lint_findings
WHERE severidade = 'critical'
GROUP BY arquivo
ORDER BY n_critical DESC
LIMIT 20;
```

### REST endpoints expostos no projeto

```sql
SELECT arquivo, classe, funcao, verbo, path, annotation_style
FROM rest_endpoints
ORDER BY verbo, path;
```

### SQL embarcado com UPDATE/DELETE em tabela específica

```sql
SELECT arquivo, funcao, linha, operacao, snippet
FROM sql_embedado
WHERE operacao IN ('update','delete')
  AND tabelas LIKE '%"SC5"%'
ORDER BY arquivo, linha;
```

### Onde um parâmetro MV é lido

```sql
SELECT arquivo, modo, default_decl
FROM parametros_uso
WHERE parametro = 'MV_LOCALIZA'
ORDER BY arquivo;
```

### Cruzar findings com regra catalogada

```sql
SELECT lf.arquivo, lf.linha, lf.regra_id, lr.titulo, lr.severidade, lr.fix_guidance
FROM lint_findings lf
JOIN lint_rules lr USING (regra_id)
WHERE lf.severidade = 'critical'
ORDER BY lf.arquivo, lf.linha;
```

### FTS5 — busca textual ponderada

```sql
-- Índice lógico (tokens com '_' e '-')
SELECT arquivo, funcao, snippet(fonte_chunks_fts, 2, '«', '»', '…', 10) AS hit
FROM fonte_chunks_fts
WHERE fonte_chunks_fts MATCH 'MaFisRef OR FATA050'
ORDER BY rank
LIMIT 20;

-- Trigram (substring exata com pontuação ADVPL)
SELECT fc.arquivo, fc.funcao
FROM fonte_chunks_fts_tri t
JOIN fonte_chunks fc ON fc.rowid = t.rowid
WHERE t.content MATCH '"SA1->A1_COD"'
LIMIT 20;
```

### Sanity check do índice

```sql
-- Conferir versões e contadores (também via: plugadvpl status)
SELECT chave, valor FROM meta;

-- FTS sincronizado com fonte_chunks?
SELECT
  (SELECT COUNT(*) FROM fonte_chunks)            AS chunks,
  (SELECT COUNT(*) FROM fonte_chunks_fts)        AS fts_unicode,
  (SELECT COUNT(*) FROM fonte_chunks_fts_tri)    AS fts_trigram;

-- Órfãos (chamadas para arquivo que não foi ingestado)
SELECT DISTINCT arquivo_origem
FROM chamadas_funcao
WHERE arquivo_origem NOT IN (SELECT arquivo FROM fontes);
```
