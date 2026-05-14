---
description: Lista o que uma funcao/metodo chama (call graph direto)
disable-model-invocation: true
arguments: [funcao]
allowed-tools: [Bash]
---

# `/plugadvpl:callees`

Lista todas as funcoes/metodos chamadas por uma funcao (call graph direto).

## Uso

```
/plugadvpl:callees <funcao>
```

## Execucao

```bash
uvx plugadvpl@0.3.16 --format md callees $funcao
```

> **Para agente IA:** prefira `--format md`. Default `table` trunca colunas em terminais estreitos. Flag global, vem **antes** do subcomando.

## Exemplos

- `/plugadvpl:callees U_PLUG001` — tudo que `U_PLUG001` chama
- `/plugadvpl:callees MaXXXProcessa` — dependencias de `MaXXXProcessa`

## Saida

Para cada callee:
- nome da funcao chamada
- linha do call site
- tipo da chamada (nativa ERP, restrita, user function, externa)

## Casos de uso

- Mapear dependencias de uma funcao antes de extrair/mover
- Identificar uso de funcoes restritas/depreciadas
- Estimar superficie de impacto de uma refatoracao

## Proximos passos sugeridos

- `/plugadvpl:callers <funcao>` — o lado oposto (quem chama)
- `/plugadvpl:lint <arquivo>` — checa uso de restritas
