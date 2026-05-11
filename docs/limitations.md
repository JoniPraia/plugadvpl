# Limitações conhecidas — plugadvpl v0.1.0

Documento honesto do que ainda não funciona ou tem cobertura parcial nesta release.
Use como referência antes de abrir bugs e como roadmap implícito de v0.2.

## Parser

- Macros runtime (`&var.`) não são resolvidos (impossível estaticamente).
- Métodos OO podem ter falso-positivos para `obj:method()` em certos contextos
  (encadeamento, ambiguidade entre acesso a campo e chamada de método).
- SQL string-concatenado (`cQry := "SELECT" + cFiltro`) não é detectado — apenas
  literais contíguos passam pela heurística de extração.
- Parity test contra baseline interno: counters de `parametros_uso`,
  `perguntas_uso`, `sql_embedado` e `fonte_chunks` divergem ~40-80% — o parser
  do plugadvpl é mais conservador que o gerador original. `chamadas_funcao` e
  `fontes` ficam dentro de ±10%. Investigação refinada planejada para v0.2.

## Lint

- 13 regras single-file detectáveis via regex estão ativas. As 11 restantes
  (cross-file, semantic) ficam catalogadas em `lint_rules` mas inativas — entram
  em v0.2.
- BP-005 (>6 parâmetros) pode inflar contagem com defaults complexos como
  `cFoo := "a,b"` (vírgula dentro de string).
- SEC-002 (User Function sem prefixo cliente) tem heurística limitada — pode
  flagar PEs legítimos como `MTA710` se o prefixo não estiver no allowlist.

## Schema

- Universo 2 (Dicionário SX — `tabelas`, `campos`, `gatilhos`, `perguntas`,
  `parametros`, etc.) e Universo 3 (Rastreabilidade — `expressoes_dicionario`,
  `rastreabilidade_unificada`) **não existem fisicamente** no DB v0.1.
  Tabelas serão criadas via migrations em v0.2+.
- Comandos que dependem (`impacto`, `ingest-sx`) retornam mensagem orientando
  a aguardar v0.2.

## Performance

- WAL não funciona em network share (SMB/CIFS) — `init` detecta UNC paths
  (`\\server\...`) e cai automaticamente para `journal_mode=DELETE`. Mapped
  drives em Windows (`Z:\`) não são detectados automaticamente — mover o
  diretório `.plugadvpl/` para disco local ou aceitar journal=DELETE manual.
- ProcessPool em macOS usa `spawn` (mais lento que `fork` do Linux). Para
  projetos pequenos (<200 fontes), o threshold automaticamente cai para
  single-thread.

## Plataforma

- Hook `session-start.mjs` requer Node.js (já é dependência do Claude Code,
  sem custo extra).
- CLI requer Python 3.11+ via `uvx`. Em ambientes corporativos sem internet,
  usar `uv tool install plugadvpl@<v>` em máquina com acesso + transferir
  o wheel resultante.
- `CLAUDE_PLUGIN_ROOT` env var tem bug conhecido em SessionStart
  ([Anthropic/claude-code#27145](https://github.com/anthropics/claude-code/issues/27145))
  — o hook usa `CLAUDE_PROJECT_DIR` como fallback.

## O que NÃO está no MVP

- Embeddings semânticos (somente FTS5 lexical).
- Análise de impacto cruzada (campo → user function via SX3 `X3_VALID`) —
  requer Universo 2/3.
- Editor LSP (este projeto é um indexer/CLI, não LSP).
