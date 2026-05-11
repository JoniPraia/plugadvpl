# Arquitetura do plugadvpl

Documento overview da arquitetura do projeto em v0.1.0. Para o schema SQL, ver [schema.md](schema.md); para o CLI, ver [cli-reference.md](cli-reference.md).

---

## Visão geral

O plugadvpl é estruturado em **dois artefatos publicáveis** que vivem no mesmo repositório:

1. **Plugin Claude Code** (`.claude-plugin/`, `skills/`, `agents/`, `hooks/`) — markdown + Node.js, descobrível via marketplace
2. **CLI Python `plugadvpl`** (`cli/`) — pacote PyPI, instalado via `uvx`/`uv tool install`

O plugin não contém lógica de parsing. Cada slash command (`/plugadvpl:*`) é um arquivo `SKILL.md` curto que dispara, via `allowed-tools: [Bash]`, uma chamada CLI equivalente. Toda a inteligência fica no CLI Python — o que mantém o plugin simples e o CLI testável de forma isolada.

---

## Fluxo de execução

```
┌─────────────────────┐
│ usuário no Claude   │
│ "explique FATA050"  │
└──────────┬──────────┘
           │
           v
┌─────────────────────────────────────────────────────┐
│ Skill plugadvpl-index-usage (auto-load)             │
│ Regra: SEMPRE consultar índice antes de Read em .prw│
└──────────┬──────────────────────────────────────────┘
           │
           v
┌─────────────────────┐    Bash    ┌──────────────────────┐
│ /plugadvpl:arch     │ ─────────► │ plugadvpl arch FATA…│
│ (SKILL.md wrapper)  │            │ (Python CLI)         │
└─────────────────────┘            └──────────┬───────────┘
                                              │
                                              v
                              ┌───────────────────────────┐
                              │ open_db (read-only mode)  │
                              │ .plugadvpl/index.db       │
                              └──────────┬────────────────┘
                                         │
                                         v
                              ┌───────────────────────────┐
                              │ query.arch_summary()      │
                              │ JOIN fontes + fonte_chunks│
                              │ + fonte_tabela            │
                              └──────────┬────────────────┘
                                         │
                                         v
                              ┌───────────────────────────┐
                              │ output (table/json/md)    │
                              │ + next_steps suggestion   │
                              └──────────┬────────────────┘
                                         │
                                         v
                              ┌───────────────────────────┐
                              │ Claude lê o resumo        │
                              │ (~700 tokens em vez de 12k)│
                              └───────────────────────────┘
```

E o pipeline de ingest (write path):

```
.prw / .prx / .tlpp  ──►  scan_sources       (walks --root, filtra extensões,
                          (scan.py)           captura mtime/size, ordena estável)

       │                                              │
       │   tarefas em paralelo (ProcessPoolExecutor)  │
       │   ou single-thread (<200 arquivos)           │
       v                                              v

read_file_bytes ──► chardet decode ──► strip_advpl ──► parse_source
(preserve enc)      (cp1252|utf-8)      (comments+      (~25 regex extractors
                                         strings → ws)   sobre conteúdo strip-first)

                                              │
                                              v
                                ┌──────────────────────────┐
                                │ ParseResult (dict)       │
                                │ + lint_findings (regex)  │
                                └──────────────┬───────────┘
                                               │
                                               v (queue → main thread)
                                ┌──────────────────────────┐
                                │ write SQLite             │
                                │ (DELETE por arquivo +    │
                                │  INSERT em massa)        │
                                └──────────────┬───────────┘
                                               │
                                               v
                                ┌──────────────────────────┐
                                │ FTS5 rebuild (1× no fim) │
                                │ unicode61 + trigram      │
                                └──────────────────────────┘
```

---

## Componentes

### `cli/plugadvpl/scan.py` (~70 linhas)

Walks the project tree, filters por extensão (`.prw`, `.prx`, `.tlpp`, `.apw`, `.ptm`, `.aph`), retorna lista ordenada estável de tuplas `(path, mtime_ns, size_bytes)`. Sem parsing — apenas FS metadata. Usado em modo incremental para skip rápido.

### `cli/plugadvpl/parsing/stripper.py` (~140 linhas)

Mini-tokenizer que substitui comentários (`//`, `/* */`, `*` em start-of-line, `&&`) e strings literais por espaços, **preservando offsets** (`len(output) == len(input)`). Roda antes das regex de extração — padrão da indústria (ProLeap COBOL faz idem).

**Por quê:** ADVPL aceita strings em aspas simples ou duplas e comentários posicionalmente sensíveis. Sem stripping, regexes ingênuos casam dentro de strings literais e dentro de comentários, gerando falso-positivos crônicos.

### `cli/plugadvpl/parsing/parser.py` (~1.400 linhas)

Coração do projeto. ~25 regex compilados em module-level (importáveis por workers do ProcessPool) + a função pública `parse_source(content_or_path) -> dict`. Cada extração tem:

- Um regex module-level (`_FUNCTION_RE`, `_DBSELECT_RE`, ...)
- Uma função privada `_foo_from_stripped(stripped: str) -> list[X]`
- Inclusão na agregação dentro de `parse_source`

Extrai: funções/métodos/PEs, includes, calls (`U_*`, ExecBlock, FwExecView, métodos), tabelas (DbSelectArea, xFilial, alias->, RecLock, DbAppend, DbDelete), MV_* (GetMV/SuperGetMV/PutMV), perguntas SX1, SQL embarcado (BeginSql/TCQuery/TCSqlExec — com extração de tabelas via FROM/JOIN/UPDATE/DELETE), REST endpoints (WSMETHOD clássico + `@Get/@Post` TLPP), HTTP outbound, RpcSetEnv, FwLogMsg, ConOut, #DEFINE, namespace TLPP, hooks MVC (bCommit/bTudoOk/...).

### `cli/plugadvpl/parsing/lint.py` (~700 linhas)

13 regras single-file ativas (BP-*, SEC-*, PERF-*, MOD-*). Cada regra é uma função `lint_BP_001(stripped, raw) -> list[Finding]`. Catálogo de 24 regras totais em `lookups/lint_rules.json` — as 11 restantes precisam de análise cross-file e ficam para v0.2.

### `cli/plugadvpl/db.py` (~310 linhas)

`open_db()` aplica os PRAGMAs init-time (page_size 8KB, WAL com fallback DELETE em network share, cache 64 MiB), `apply_migrations()` lê `migrations/*.sql` em ordem e pula os já registrados em `_migrations`, `seed_lookups()` carrega os 6 JSONs em massa via `executemany`.

### `cli/plugadvpl/ingest.py` (~730 linhas)

Orquestrador. Decide single-thread vs ProcessPool conforme número de arquivos e flag `--workers`. SQLite só suporta um writer por DB — o worker pool faz apenas o parsing, e a thread principal centraliza a escrita.

### `cli/plugadvpl/query.py` (~420 linhas)

Implementação das queries dos subcomandos read-only (`status`, `find`, `callers`, `callees`, `tables`, `param`, `arch`, `lint`, `doctor`, `grep`). Cada função retorna uma lista de dicts + metadata (`total`, `truncated`).

### `cli/plugadvpl/output.py` (~170 linhas)

Renderização table (Rich) / JSON / Markdown. Honra `--limit`, `--offset`, `--compact`, `--quiet`.

### `cli/plugadvpl/cli.py` (~730 linhas)

Entrypoint Typer. Define o callback global (com as opções compartilhadas `--root`, `--format`, etc.) e os 14 subcomandos. Cada subcomando é fino — só faz parsing de args, chama uma função em `query.py` ou `ingest.py`, e roteia o resultado por `output.py`.

### Hook `hooks/session-start.mjs` (Node.js, ~140 linhas)

SessionStart hook cross-platform. Detecta `.plugadvpl/`, valida que o índice existe, lista contagens rapidamente via `sqlite3` (se disponível) ou via leitura direta do header. Onboarding silencioso quando tudo está OK.

---

## Decisões-chave

### Strip-first em vez de tokenizer real

ADVPL não tem grammar oficial pública nem AST estável. Construir um parser top-down levaria meses e quebraria com cada construção esotérica que aparecesse em fontes legados. Em vez disso, plugadvpl segue o que ProLeap COBOL e tree-sitter-makefile fazem: pre-processa o source (stripper) e aplica regexes ancorados em `^` (MULTILINE) com `tokenchars` defensivos (`[ \t]*` em vez de `\s*` para não cruzar linhas).

Trade-off: parser é "good enough" para 95%+ das extrações, mas falha em macros pré-processadas complexas. Aceito explicitamente — alternativa custaria 10× o esforço para ganho marginal.

### ProcessPool adaptive

Spawn de processos no Windows custa ~200ms cada (fork no Linux é mais barato, mas ainda mensurável). Para projetos pequenos (<200 arquivos), o overhead do pool ultrapassa o ganho do paralelismo. O ingest detecta e roda single-thread nesse caso. Acima do threshold, usa `min(8, cpu_count())` workers com `mp_context='spawn'` (Windows/macOS) ou `'fork'` (Linux).

Regex são pré-compilados em **module-level** justamente para serem carregados uma vez por worker e não a cada arquivo.

### FTS5 external content + dual-index (unicode61 + trigram)

Schema mantém `fonte_chunks.content` como source-of-truth e expõe **dois** índices FTS5 sobre o mesmo conteúdo (`external content`):

- **`fonte_chunks_fts`** (unicode61 com `tokenchars '_-'`) — busca por palavras/identifiers. `A1_COD` é um único token. Casa com `plugadvpl grep MaCnt`.
- **`fonte_chunks_fts_tri`** (trigram, disponível desde SQLite 3.34) — busca substring exata. Casa `SA1->A1_COD`, `%xfilial%`, `::New`, `PARAMIXB[1]` — coisas que unicode61 quebraria em tokens.

Custo: ~2× espaço de FTS, mas é a única forma de cobrir pontuação ADVPL sem cair em LIKE full-scan. Rebuild é feito uma vez ao final do ingest (mais barato em batch que insert-by-insert).

### Encoding preserve-by-default

ADVPL clássico (`.prw`) é cp1252; TLPP moderno (`.tlpp`) é utf-8. Em vez de forçar uma re-encode, plugadvpl detecta com `chardet`, registra o encoding em `fontes.encoding` e preserva. Edit/Write devem reabrir com o mesmo encoding (skill `advpl-encoding` instrui o Claude).

### Read-only por default em queries

Todos os subcomandos exceto `init`, `ingest`, `reindex` abrem o DB com `mode=ro` (URI SQLite). Não há risco de hot-write corromper estado durante consulta concorrente.

### `.plugadvpl/` é dado do usuário, não responsabilidade do projeto

O índice contém literais do código do cliente (nomes de tabelas, queries, possivelmente credenciais hardcoded em projetos legados). `init` adiciona `.plugadvpl/` ao `.gitignore` por default. Para projetos sensíveis, `ingest --no-content` persiste apenas metadata, e `--redact-secrets` mascara URLs com user:pwd e tokens hex longos antes de gravar.

---

## Como contribuir com uma nova extração

Cenário: você quer indexar mais um padrão ADVPL — digamos, chamadas a `WSExecAuto`. Roteiro:

1. **Adicione o regex module-level em `parsing/parser.py`**:

   ```python
   _WSEXECAUTO_RE = re.compile(
       r'\bWSExecAuto\s*\(\s*["\'](\w+)["\']',
       re.IGNORECASE,
   )
   ```

   Use `[ \t]` em vez de `\s` se quiser ancorar em start-of-line. Sempre `re.IGNORECASE` para ADVPL.

2. **Crie uma função privada `_wsexec_from_stripped(stripped: str) -> list[str]`**:

   ```python
   def _wsexec_from_stripped(stripped: str) -> list[str]:
       return list(dict.fromkeys(m.group(1) for m in _WSEXECAUTO_RE.finditer(stripped)))
   ```

   Dedup mantendo ordem (`dict.fromkeys`) é o pattern usado em todo o parser.

3. **Inclua na função pública `parse_source`**:

   No `result` dict, adicione `"ws_execauto": _wsexec_from_stripped(stripped)`.

4. **Se o dado vai pra SQLite, adicione coluna ou tabela**:

   - Se for ≤10 valores, persiste como JSON list em `fontes`.
   - Se for ≥10 ou precisar lookup reverso, crie tabela satélite com índice (modelo `chamadas_funcao`/`fonte_tabela`).
   - Se for nova migration: arquivo novo `cli/plugadvpl/migrations/002_ws_execauto.sql`, registrado automaticamente por `_migrations`.

5. **Adicione testes em `cli/tests/unit/parsing/test_parser.py`**:

   ```python
   def test_wsexec_basic():
       src = 'WSExecAuto("MATA010", aParams)'
       result = parse_source(src, "test.prw")
       assert result["ws_execauto"] == ["MATA010"]
   ```

   - Teste positive (casa o esperado)
   - Teste em comentário (`// WSExecAuto(...)` — não deve casar)
   - Teste em string literal (`'WSExecAuto("X")'` — não deve casar)
   - Snapshot test em `cli/tests/integration/test_parser_snapshots.py` se cobrir caso fronteira

6. **Se for exposto via CLI**:

   - Acrescente query function em `query.py`
   - Acrescente subcommand em `cli.py` (Typer command, `--help` em pt-BR)
   - Skill wrapper em `skills/wsexec/SKILL.md` (copiar template de `skills/grep/`)
   - Update [docs/cli-reference.md](cli-reference.md) e [docs/schema.md](schema.md)

7. **Rode os testes e o lint**:

   ```bash
   cd cli
   uv run pytest tests/unit tests/integration -q
   uv run ruff check
   uv run mypy plugadvpl
   ```

8. **Conventional Commit**:

   ```
   feat(parser): extract WSExecAuto callee names

   - Add _WSEXECAUTO_RE module-level regex
   - Persist as fontes.ws_execauto JSON list (no new table needed)
   - Test coverage 4 cases (positive, comment, string, multi-call)
   ```

Pre-commit roda ruff format + mypy automaticamente.

---

## Tecnologias

| Camada | Tech | Notas |
|---|---|---|
| CLI Python | [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) | CLI declarativa + rendering bonito |
| Parser | regex stdlib | Strip-first + `re.MULTILINE` ancorado |
| Concorrência | `concurrent.futures.ProcessPoolExecutor` | Adaptive single/parallel |
| Storage | SQLite ≥3.34 | FTS5 trigram requer 3.34+ |
| Encoding | [chardet](https://pypi.org/project/chardet/) | Detecção de cp1252/utf-8 |
| Process info | [psutil](https://pypi.org/project/psutil/) | CPU count, mem para adaptive workers |
| Build | [hatchling](https://hatch.pypa.io/) + hatch-vcs | Versão via git tag |
| Test | [pytest](https://docs.pytest.org/) + hypothesis + syrupy + pytest-benchmark | 239 tests, 87% coverage |
| Lint Python | [ruff](https://docs.astral.sh/ruff/) (format + check) + [mypy](https://mypy.readthedocs.io/) strict | line-length 100 |
| Plugin host | Node.js (hook único) | hooks/session-start.mjs, sem deps externos |
| CI | GitHub Actions matrix 3 OS × 3 Python | + benchmark-action + PyPI Trusted Publisher OIDC |

---

## Onde olhar primeiro

Se você está clonando o repo agora:

1. [docs/superpowers/specs/2026-05-11-plugadvpl-design.md](superpowers/specs/) — design original com decisões e trade-offs documentados
2. `cli/plugadvpl/parsing/parser.py` — onde a mágica acontece
3. `cli/plugadvpl/migrations/001_initial.sql` — schema completo, comentado
4. `cli/tests/fixtures/synthetic/` — 20 fontes `.prw` cobrindo todos os cenários parseáveis
5. `skills/plugadvpl-index-usage/SKILL.md` — a "skill-chefe" que orienta o Claude a usar o índice

PRs são bem-vindos. Veja [CONTRIBUTING.md](../CONTRIBUTING.md) para setup local.
