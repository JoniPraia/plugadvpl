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
uvx plugadvpl@0.3.14 --help
```

## Saida

Lista os 13 subcomandos com descricao curta:
- `init` — inicializa indice no projeto
- `ingest` — indexa fontes
- `reindex` — re-indexa um arquivo
- `status` — status do indice
- `find` — pesquisa simbolos
- `callers` — quem chama uma funcao
- `callees` — o que uma funcao chama
- `tables` — usos de uma tabela ERP
- `param` — usos de um MV_
- `arch` — visao arquitetural (comando-chefe)
- `lint` — lint de um arquivo
- `doctor` — diagnostico do ambiente
- `grep` — busca texto/FTS no conteudo

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
