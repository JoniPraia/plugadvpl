---
description: Lista a cadeia de gatilhos SX7 (origem -> destino) a partir de um campo
disable-model-invocation: true
arguments: [campo]
allowed-tools: [Bash]
---

# `/plugadvpl:gatilho`

Lista a cadeia de gatilhos SX7 (BFS por padrão até 3 níveis) a partir de um
campo SX3. Mostra origem, sequência, destino, regra ADVPL e tipo
(P=Primário, S=Secundário).

Útil para responder "o que acontece quando eu mudo `A1_COD`?" — qual cascata
de campos é recalculada via SX7.

Requer `/plugadvpl:ingest-sx` rodado antes.

## Uso

```
/plugadvpl:gatilho <campo> [--depth 1..3]
```

## Argumento + opcao

- `<campo>` — nome do campo SX3 (case-insensitive).
- `--depth N` (default `3`) — profundidade da BFS (1..3). Sequências curtas
  pra cadeia direta; 3 pra ver gatilho-de-gatilho-de-gatilho.

## Execucao

```bash
uvx plugadvpl@0.3.27 gatilho $ARGUMENTS
```

## Exemplos

- `/plugadvpl:gatilho A1_COD` — cadeia até 3 níveis a partir do código
- `/plugadvpl:gatilho B1_GRUPO --depth 1` — só os gatilhos imediatos
- `/plugadvpl:gatilho C5_NUM -d 2` — 2 níveis

## Saida

Colunas: `nivel`, `via`, `origem`, `sequencia`, `destino`, `regra`, `tipo`.

- `nivel` — 1 a `depth` (BFS)
- `via` — `origem→destino` (campo modificado é o `destino`)
- `regra` — expressão ADVPL do `X7_REGRA`
- `tipo` — `P`/`S`

## Proximos passos sugeridos

- `/plugadvpl:impacto <campo>` — visão completa (não só SX7)
- `/plugadvpl:lint --cross-file --regra SX-002` — gatilhos com destino
  inexistente
- `/plugadvpl:lint --cross-file --regra SX-010` — gatilhos sem SEEK
