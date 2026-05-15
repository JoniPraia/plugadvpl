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
uvx plugadvpl@0.3.21 ingest-sx $ARGUMENTS
```

## Exemplos

- `/plugadvpl:ingest-sx D:/Clientes/CSV` — ingere o dicionário do cliente
- `/plugadvpl:ingest-sx ./sx-export` — pasta relativa ao projeto

## Saida

Counts por tabela após o ingest (linhas inseridas), tempo total, e
`sx_ingerido=true` no meta. Re-rodar é idempotente (`INSERT OR REPLACE`).

## Avisos em stderr (v0.3.14)

Dois diagnósticos novos aparecem em stderr quando relevantes:

### 1. `sxg.csv` mal-rotulado (dump SX3 disfarçado)

```
WARN: 'sxg.csv' nao parece SXG (1a coluna='X3_ARQUIVO', esperado XG_*) —
provavelmente dump SX3 disfarcado. Tabela grupos_campo ficara vazia.
Solicite o SXG correto ao DBA (deve ter colunas XG_GRUPO/XG_DESCRIC/XG_TAMANHO).
```

Em alguns exports do Configurador, `sxg.csv` traz na verdade um dump SX3 (mesmo header `X3_*`). O parser detecta e pula a ingestão pra evitar dados sujos — `grupos_campo` fica vazia. Antes era silencioso e a IA/usuário ficava adivinhando.

### 2. Dedup silencioso por colisão de PK

```
WARN: tabela 'pastas': 1918 linhas CSV → 1833 distintas após PK dedup
(85 duplicada(s) na PK ('alias', 'ordem') foram sobrescrita(s)).
```

Quando o dump SX tem duplicatas na chave natural, `INSERT OR REPLACE` sobrescreve silenciosamente. O aviso surge **por tabela** com diff > 0, mostrando exatamente quantas linhas foram colapsadas e em qual PK — útil pra distinguir bug do parser (PK incompleta) de dados duplicados no dump real.

> **Histórico:** até v0.3.13 a PK de `consultas` (SXB) era `(alias, sequencia, coluna)` sem `tipo`, fazendo as 6 "páginas" da consulta padrão (header/índice/permissão/coluna/retorno/filtro) colidirem. Dump real de cliente: 58.796 → 46.669 (perda de 20,6%). **v0.3.14 corrige a PK** para `(alias, tipo, sequencia, coluna)` espelhando a chave natural TOTVS (TDN: XB_FILIAL+XB_ALIAS+XB_TIPO+XB_SEQ+XB_COLUNA). Usuários existentes precisam re-rodar `ingest-sx` pra ganhar os ~20% de rows antes perdidos.

## Proximos passos sugeridos

- `/plugadvpl:sx-status` — confere counts por tabela
- `/plugadvpl:impacto A1_COD` — killer feature: cruza referências do campo
  em fontes ↔ SX3 ↔ SX7 ↔ SX1
- `/plugadvpl:lint --cross-file` — roda as 11 regras SX-001..SX-011

## Observacao

Indexa **apenas** o dicionário custom do cliente. Por design, padrão TOTVS é
ignorado — auditoria de customização não precisa dele.
