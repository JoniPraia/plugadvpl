---
description: Pesquisa simbolos (funcoes, classes, metodos) no indice plugadvpl
disable-model-invocation: true
arguments: [termo]
allowed-tools: [Bash]
---

# `/plugadvpl:find`

Pesquisa simbolos (Function/Class/Method/Static Function/User Function) no indice.

## Uso

```
/plugadvpl:find <termo>
```

## Modos de busca

A query funciona em 3 modos automaticos:

1. **Exato** — quando `termo` casa exatamente com um nome de simbolo
2. **Prefixo** — quando `termo` casa com inicio de nomes (ex: `MaXXX` casa `MaXXX001`, `MaXXX002`)
3. **FTS** — pesquisa fulltext em nomes/assinaturas/comentarios (FTS5)

## Execucao

```bash
uvx plugadvpl@0.3.21 --format md find $termo
```

> **Para agente IA:** prefira `--format md`. Default `table` trunca colunas (`signature` larga vira `ti...`). Flag eh global, vem **antes** do subcomando.

## Exemplos

- `/plugadvpl:find U_PLUG001` — busca exata de funcao de usuario
- `/plugadvpl:find MaXXX` — busca por prefixo
- `/plugadvpl:find "atualiza cliente"` — busca FTS em comentarios/assinaturas

## Saida

Para cada match:
- nome do simbolo, tipo (Function/Class/Method/...)
- arquivo:linha
- assinatura quando disponivel

## Proximos passos sugeridos

- `/plugadvpl:callers <funcao>` — quem chama
- `/plugadvpl:callees <funcao>` — o que chama
- `/plugadvpl:arch <arquivo>` — visao arquitetural do arquivo dono
