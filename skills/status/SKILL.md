---
description: Mostra status do indice plugadvpl (contagem de fontes, simbolos, tamanho do DB, ultima ingest)
disable-model-invocation: true
allowed-tools: [Bash]
---

# `/plugadvpl:status`

Mostra status do indice plugadvpl no projeto atual.

## Uso

```
/plugadvpl:status [--check-stale]
```

## Opcoes

- `--check-stale` — verifica fontes cujo hash/mtime divergem do indice (detecta defasagem)

## Execucao

```bash
uvx plugadvpl@0.3.1 status $ARGUMENTS
```

## Saida

- Numero de fontes indexadas
- Numero de simbolos (Function/Class/Method/Static Function/User Function)
- Numero de calls, tabelas, params, includes, sql_refs
- Tamanho do `.plugadvpl/index.db`
- Versao do schema e timestamp da ultima ingest
- Quando `--check-stale`: lista de arquivos defasados

## Exemplos

- `/plugadvpl:status` — visao geral rapida
- `/plugadvpl:status --check-stale` — detecta arquivos defasados para reindex

## Proximos passos sugeridos

- Se houver arquivos stale, rode `/plugadvpl:ingest` (incremental) ou `/plugadvpl:reindex <arquivo>`
- `/plugadvpl:doctor` — diagnostico do ambiente
