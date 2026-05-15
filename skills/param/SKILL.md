---
description: Lista usos de um parametro MV_ (GetMv/PutMv/SuperGetMv) no projeto
disable-model-invocation: true
arguments: [mv]
allowed-tools: [Bash]
---

# `/plugadvpl:param`

Lista usos de um parametro MV_ (Protheus) no projeto indexado.

## Uso

```
/plugadvpl:param <mv>
```

## Execucao

```bash
uvx plugadvpl@0.3.22 param $mv
```

## Exemplos

- `/plugadvpl:param MV_MOEDA1` — usos da MV_MOEDA1
- `/plugadvpl:param MV_PAR01` — usos de MV_PAR01 (parametros de pergunte)

## Saida

Para cada uso:
- nome do MV
- arquivo:linha
- tipo de chamada (GetMv, PutMv, SuperGetMv, SuperGetMV)
- funcao que contem o uso

## Casos de uso

- Avaliar impacto de mudanca em parametro
- Encontrar configuracoes ausentes/quebradas
- Mapear dependencias de configuracao

## Proximos passos sugeridos

- `/plugadvpl:callers <funcao>` — quem chama a funcao que usa esse MV
- `/plugadvpl:arch <arquivo>` — visao do arquivo dono
