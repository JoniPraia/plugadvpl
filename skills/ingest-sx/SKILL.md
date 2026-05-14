---
description: Indexa o Dicionário SX (Universo 2) a partir de CSVs exportados do RPO
disable-model-invocation: true
arguments: [csv_dir]
allowed-tools: [Bash]
---

# `/plugadvpl:ingest-sx`

Indexa o Dicionário SX (SX1..SXG) a partir de uma pasta com CSVs exportados via
Configurador → Misc → Exportar Dicionário. Popula 11 tabelas (`tabelas`,
`campos`, `indices`, `gatilhos`, `parametros`, `perguntas`, `tabelas_genericas`,
`relacionamentos`, `pastas`, `consultas`, `grupos_campo`) no índice SQLite.

Pré-requisito: rodar `/plugadvpl:init` antes (cria `.plugadvpl/index.db`).

## Uso

```
/plugadvpl:ingest-sx <pasta-csv>
```

## Argumento

- `<pasta-csv>` — diretório com `sx1.csv`, `sx2.csv`, ..., `sxg.csv` (auto-detect
  de encoding cp1252/utf-8-sig e separador `,`/`;`). Arquivos faltantes são
  tolerados; rows com `D_E_L_E_T_='*'` são filtradas.

## Execucao

```bash
uvx plugadvpl@0.3.13 ingest-sx $ARGUMENTS
```

## Exemplos

- `/plugadvpl:ingest-sx D:/Clientes/CSV` — ingere o dicionário do cliente
- `/plugadvpl:ingest-sx ./sx-export` — pasta relativa ao projeto

## Saida

Counts por tabela após o ingest (linhas inseridas), tempo total, e
`sx_ingerido=true` no meta. Re-rodar é idempotente (`INSERT OR REPLACE`).

## Proximos passos sugeridos

- `/plugadvpl:sx-status` — confere counts por tabela
- `/plugadvpl:impacto A1_COD` — killer feature: cruza referências do campo
  em fontes ↔ SX3 ↔ SX7 ↔ SX1
- `/plugadvpl:lint --cross-file` — roda as 11 regras SX-001..SX-011

## Observacao

Indexa **apenas** o dicionário custom do cliente. Por design, padrão TOTVS é
ignorado — auditoria de customização não precisa dele.
