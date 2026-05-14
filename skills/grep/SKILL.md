---
description: Pesquisa texto/identificador/FTS no conteudo dos fontes indexados
disable-model-invocation: true
arguments: [pattern]
allowed-tools: [Bash]
---

# `/plugadvpl:grep`

Pesquisa por padrao no conteudo dos fontes indexados. Mais barato que `Grep` do Claude porque opera sobre SQLite + FTS5.

## Uso

```
/plugadvpl:grep <pattern> [--fts | --literal | --identifier]
```

## Modos

- `--fts` (default) — full-text search no FTS5 (tokens, prefixos)
- `--literal` — substring literal exata (LIKE)
- `--identifier` — casa identificadores ADVPL (respeitando boundaries de simbolos)

## Execucao

```bash
uvx plugadvpl@0.3.17 grep $ARGUMENTS
```

## Exemplos

- `/plugadvpl:grep "TCQuery"` — onde aparece TCQuery (FTS)
- `/plugadvpl:grep "RecLock" --literal` — substring exata
- `/plugadvpl:grep "U_PLUG001" --identifier` — identificador (evita falsos positivos)
- `/plugadvpl:grep "BeginSql alias"` — frase no FTS

## Saida

Para cada hit:
- arquivo:linha
- snippet com destaque do match

## Quando preferir vs Claude `Grep`

- Sempre que voce ja rodou `/plugadvpl:ingest` no projeto
- Para queries multi-termo (FTS5 faz boolean barato)
- Quando quer hits ordenados por relevancia

## Proximos passos sugeridos

- `/plugadvpl:arch <arquivo>` no arquivo mais relevante
- `/plugadvpl:find <termo>` se busca um simbolo (mais preciso)
