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
uvx plugadvpl@0.3.0 --help
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

Alem de flags globais (`--db-path`, `--format`, `--limit`, `--quiet`, ...).

## Slashes equivalentes

Cada subcomando tem um slash:
- `/plugadvpl:init` ... `/plugadvpl:grep`

## Proximos passos sugeridos

- Primeira vez? `/plugadvpl:init` e em seguida `/plugadvpl:ingest`
- Ja indexado? `/plugadvpl:status` para conferir
