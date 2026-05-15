---
description: Lista comandos plugadvpl disponiveis (help do CLI)
disable-model-invocation: true
allowed-tools: [Bash]
---

# `/plugadvpl:help`

Mostra a lista de comandos plugadvpl disponiveis e suas opcoes globais.

## Uso

```
/plugadvpl:help
```

## Execucao

```bash
uvx plugadvpl@0.4.3 --help
```

## Saida

Lista os 19 subcomandos com descricao curta.

**Universo 1 — fontes (14 cmds):**
- `version` — imprime versao do binario (mesmo de `--version` global)
- `init` — inicializa indice no projeto + injeta fragment em CLAUDE.md
- `ingest` — indexa fontes (`--workers`/`--no-incremental`/`--no-content`/`--redact-secrets`)
- `reindex <arq>` — re-indexa um arquivo apos editar
- `status` — versoes (runtime + indice), counters, opcoes `--check-stale`
- `find <termo>` — busca simbolo (exato/prefixo/FTS)
- `callers <fn>` — quem chama (cada row tem `is_self_call` v0.3.18+)
- `callees <fn>` — o que chama (resolve fn-pai via chunks v0.3.15+)
- `tables <T>` — usos da tabela ERP (`--mode read|write|reclock`)
- `param <MV_*>` — usos de parametro
- `arch <arq>` — visao arquitetural (comando-chefe; flag `tabelas_via_execauto` v0.3.18+)
- `lint [arq]` — 20 regras single-file (`--severity`, `--regra`, `--cross-file` p/ SX-*)
- `doctor` — diagnostico do indice (encoding/orfaos/FTS sync)
- `grep <termo>` — texto/FTS no conteudo (`-m fts|literal|identifier`)

**Universo 2 — Dicionario SX (5 cmds, v0.3.0+):**
- `ingest-sx <pasta-csv>` — indexa SX1..SXG do dump CSV
- `sx-status` — counts por tabela SX
- `impacto <campo>` — cruza referencias campo em fontes ↔ SX3 ↔ SX7 ↔ SX1 (v0.3.17+ word boundary)
- `gatilho <campo> [--depth N]` — cadeia SX7 (origem OU destino, v0.3.15+)

Alem de flags globais (definidas no callback, **vem antes do subcomando**):

- `--version` / `-V` — imprime a versao do binario rodando AGORA e sai (eager — nao requer subcomando). v0.3.12+.
- `--root <path>` / `-r` — raiz do projeto cliente (default: cwd).
- `--db <path>` — DB explicito (default: `<root>/.plugadvpl/index.db`).
- `--format {table,md,json}` / `-f` — formato de saida. **Para agente IA: `md`** (sem truncamento, vai pra stdout). `table` (default) usa Rich em stderr e trunca colunas em terminais estreitos.
- `--limit N` — max linhas (default 20, `0` = ilimitado).
- `--offset N` — pula N linhas antes do limit.
- `--compact` — JSON sem indent / table sem `show_lines`.
- `--quiet` / `-q` — sem titulos/decoracoes (e suprime warnings de divergencia versao no `status`).
- `--no-next-steps` — desliga sugestoes "Proximo passo recomendado:".

> **Aviso:** flags como `--json`, `--vertical`, `--wide`, `--no-table` **nao existem**. Use `--format json` ou `--format md`.

## "Qual versao esta instalada?"

3 caminhos:

- `plugadvpl --version` (ou `-V`) — binario rodando AGORA. v0.3.12+.
- `plugadvpl version` — idem, via subcomando antigo (continua funcionando).
- `plugadvpl status` — mostra **as duas**: `runtime_version` (binario AGORA) + `plugadvpl_version` (que gravou o indice). Avisa em amarelo se divergirem (sintoma de `uv tool upgrade` sem `ingest --incremental` posterior).

## Slashes equivalentes

Cada subcomando tem um slash:
- `/plugadvpl:init` ... `/plugadvpl:grep`

## Proximos passos sugeridos

- Primeira vez? `/plugadvpl:init` e em seguida `/plugadvpl:ingest`
- Ja indexado? `/plugadvpl:status` para conferir
