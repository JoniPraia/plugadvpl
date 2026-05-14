---
description: Lista usos de uma tabela ERP (leitura/escrita/reclock) no projeto
disable-model-invocation: true
arguments: [tabela]
allowed-tools: [Bash]
---

# `/plugadvpl:tables`

Lista usos de uma tabela ERP (Protheus) no projeto indexado.

## Uso

```
/plugadvpl:tables <tabela> [--read | --write | --reclock]
```

## Opcoes

- `--read` — filtra apenas usos de leitura (DbSeek, DbGoTop, While !Eof, ...)
- `--write` — filtra apenas usos de escrita (RecLock+Replace+MsUnlock, ...)
- `--reclock` — filtra apenas operacoes de RecLock/MsUnlock

Sem flags: lista todos os usos (leitura + escrita + reclock + SQL).

## Execucao

```bash
uvx plugadvpl@0.3.20 --format md tables $ARGUMENTS
```

> **Para agente IA:** prefira `--format md`. Default `table` trunca colunas (`fonte_path` longo vira `ca...`). Flag eh global, vem **antes** do subcomando.

## Exemplos

- `/plugadvpl:tables SA1` — todos os usos da SA1 (clientes)
- `/plugadvpl:tables SC5 --write` — onde SC5 e gravada
- `/plugadvpl:tables SE1 --reclock` — operacoes de RecLock em SE1
- `/plugadvpl:tables SB1 --read` — leituras de SB1

## Saida

Para cada uso:
- alias/tabela
- arquivo:linha
- tipo de operacao (read/write/reclock/sql)
- funcao que contem o uso

## Proximos passos sugeridos

- `/plugadvpl:lint <arquivo>` — checa padrao RecLock correto
- `/plugadvpl:arch <arquivo>` — contexto arquitetural do arquivo
