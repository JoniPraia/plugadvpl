---
description: Cruza referencias de um campo SX3 entre fontes, SX3, SX7 e SX1 (killer feature v0.3.0)
disable-model-invocation: true
arguments: [campo]
allowed-tools: [Bash]
---

# `/plugadvpl:impacto`

**Killer feature do v0.3.0.** Em segundos, para um campo SX3 arbitrário, lista
TODA a cadeia de impacto:

- Fontes `.prw`/`.tlpp` que mencionam o campo (com alias `A1_COD` ou `SA1->A1_COD`)
- Validações SX3 que dependem dele (X3_VALID, X3_WHEN, X3_VLDUSER, X3_RELACAO)
- Gatilhos SX7 onde aparece como origem ou destino
- Perguntas SX1 que o referenciam (X1_VALID, X1_DEF01..X1_DEF99)

Requer `/plugadvpl:ingest-sx` rodado antes.

## Uso

```
/plugadvpl:impacto <campo> [--depth 1..3]
```

## Argumento + opcao

- `<campo>` — nome do campo SX3 (ex: `A1_COD`, `B1_GRUPO`, `D2_ITEM`).
  Case-insensitive.
- `--depth N` (default `1`) — quantos níveis de cadeia SX7 seguir
  (1 = só os gatilhos diretos; 3 = cascata completa). `1..3`.

## Execucao

```bash
uvx plugadvpl@0.3.15 impacto $ARGUMENTS
```

## Exemplos

- `/plugadvpl:impacto A1_COD` — todo o impacto direto do código do cliente
- `/plugadvpl:impacto B1_GRUPO --depth 3` — cadeia completa de gatilhos a partir
  do grupo de produto
- `/plugadvpl:impacto D2_QUANT -d 2` — quantidade da nota saída, 2 níveis

## Saida

Linhas com colunas `tipo`, `local`, `contexto`, `severidade`:

- `tipo` ∈ {`fonte`, `sx3-valid`, `sx3-init`, `sx3-when`, `sx7-origem`,
  `sx7-destino`, `sx1-pergunta`, ...}
- `local` — arquivo:linha ou `SX:<tabela>` ou `SX1:<grupo>`
- `contexto` — snippet curto do trecho que casou
- `severidade` — `info`, `warning`, `critical` quando aplicável

## Proximos passos sugeridos

- `/plugadvpl:gatilho <campo>` — só a cadeia SX7 (mais focada)
- `/plugadvpl:tables <tabela>` — usos da tabela onde o campo vive
- `/plugadvpl:callers U_XYZVALID` — se um VALID chama uma user-function
