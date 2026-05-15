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
uvx plugadvpl@0.3.27 --format md callers $funcao
```

> **Para agente IA:** prefira `--format md`. Default `table` trunca colunas em terminais estreitos. Flag global, vem **antes** do subcomando. Resultado vazio nao eh bug — pode ser endpoint exposto que ninguem chama internamente (ex: WS SOAP).

## Exemplos

- `/plugadvpl:callers U_PLUG001` — todos os fontes que chamam `U_PLUG001`
- `/plugadvpl:callers MaXXXGrava` — quem invoca `MaXXXGrava`

## Saida

Para cada caller:
- nome da funcao chamadora
- arquivo:linha do call site
- contexto da chamada
- **`is_self_call: bool`** (v0.3.18+) — `True` quando a chamada origina do
  mesmo simbolo (`funcao_origem == nome` OU `basename(arquivo_origem) == nome`).
  Util pra filtrar self-references — `FwLoadModel('X')` de dentro de `X.prw`,
  recursao, ou metodo chamando outro metodo da mesma classe.

### Exemplo: filtrar so callers externos

```bash
plugadvpl --format json callers MGFCOM14 | jq '.rows[] | select(.is_self_call == false)'
```

Pra ver tudo (incluindo self): `--format md` direto.

## Casos de uso

- Avaliar impacto de mudancas em uma funcao
- Encontrar pontos de entrada (callers raiz)
- Investigar bugs analisando quem invoca

## Proximos passos sugeridos

- `/plugadvpl:callees <funcao>` — o lado oposto (o que essa funcao chama)
- `/plugadvpl:arch <arquivo>` — visao arquitetural dos arquivos chamadores
