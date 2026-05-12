---
description: Indexa fontes ADVPL/TLPP do projeto em SQLite + FTS5
disable-model-invocation: true
arguments: [paths]
allowed-tools: [Bash]
---

# `/plugadvpl:ingest`

Indexa fontes ADVPL/TLPP (.prw, .prx, .tlpp, .ch, .aph) em `.plugadvpl/index.db`.

## Uso

```
/plugadvpl:ingest [paths...] [opcoes]
```

Quando `paths` for omitido, indexa o diretorio do projeto atual.

## Opcoes

- `--workers N` — numero de workers paralelos (default: auto-adaptativo segundo CPUs)
- `--no-content` — nao armazena conteudo bruto dos fontes (apenas metadados/AST)
- `--redact-secrets` — redige strings sensiveis (senhas, tokens) antes de indexar
- `--no-incremental` — forca reindex completo ignorando hash/mtime

## Execucao

```bash
uvx plugadvpl@0.3.0 ingest $ARGUMENTS
```

## Exemplos

- `/plugadvpl:ingest` — indexa todo o projeto
- `/plugadvpl:ingest src/` — indexa apenas `src/`
- `/plugadvpl:ingest --workers 8` — usa 8 workers paralelos
- `/plugadvpl:ingest --redact-secrets --no-content` — modo seguro (compliance)
- `/plugadvpl:ingest --no-incremental` — reindex completo

## Proximos passos sugeridos

- `/plugadvpl:status` — verifica contagem de fontes/simbolos indexados
- `/plugadvpl:find <termo>` — pesquisa simbolos
- `/plugadvpl:arch <arquivo>` — visao arquitetural antes de Read
