---
description: Conta linhas por tabela do Dicionario SX (apos ingest-sx)
disable-model-invocation: true
allowed-tools: [Bash]
---

# `/plugadvpl:sx-status`

Mostra contadores por tabela do Dicionário SX no índice:
`tabelas` (SX2), `campos` (SX3), `indices` (SIX), `gatilhos` (SX7),
`parametros` (SX6), `perguntas` (SX1), `tabelas_genericas` (SX5),
`relacionamentos` (SX9), `pastas` (SXA), `consultas` (SXB),
`grupos_campo` (SXG).

Sanity check rápido depois de `/plugadvpl:ingest-sx` — confere que cada CSV
foi ingerido com contagem razoável.

## Uso

```
/plugadvpl:sx-status
```

Sem argumentos.

## Execucao

```bash
uvx plugadvpl@0.3.0 sx-status
```

## Saida

Uma linha por tabela com `rows`. Se nenhum SX foi ingerido ainda
(`sx_ingerido=false` no meta), a saída sugere rodar `ingest-sx`.

## Proximos passos sugeridos

- `/plugadvpl:ingest-sx <pasta-csv>` — se contagens zeradas ou desatualizadas
- `/plugadvpl:impacto A1_COD` — killer feature contra um campo conhecido
- `/plugadvpl:doctor` — diagnóstico geral do índice
