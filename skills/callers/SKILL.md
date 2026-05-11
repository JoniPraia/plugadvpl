---
description: Lista quem chama uma funcao/metodo (call graph reverso)
disable-model-invocation: true
arguments: [funcao]
allowed-tools: [Bash]
---

# `/plugadvpl:callers`

Lista todos os call sites que chamam a funcao/metodo informada (call graph reverso).

## Uso

```
/plugadvpl:callers <funcao>
```

## Execucao

```bash
uvx plugadvpl@0.1.0 callers $funcao
```

## Exemplos

- `/plugadvpl:callers U_PLUG001` — todos os fontes que chamam `U_PLUG001`
- `/plugadvpl:callers MaXXXGrava` — quem invoca `MaXXXGrava`

## Saida

Para cada caller:
- nome da funcao chamadora
- arquivo:linha do call site
- contexto da chamada

## Casos de uso

- Avaliar impacto de mudancas em uma funcao
- Encontrar pontos de entrada (callers raiz)
- Investigar bugs analisando quem invoca

## Proximos passos sugeridos

- `/plugadvpl:callees <funcao>` — o lado oposto (o que essa funcao chama)
- `/plugadvpl:arch <arquivo>` — visao arquitetural dos arquivos chamadores
