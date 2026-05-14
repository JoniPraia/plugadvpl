---
description: Visao arquitetural de um arquivo ADVPL/TLPP (use ANTES de Read - economiza tokens)
disable-model-invocation: true
arguments: [arquivo]
allowed-tools: [Bash]
---

# `/plugadvpl:arch`

**Comando-chefe do plugadvpl.** Mostra a visao arquitetural condensada de um arquivo ADVPL/TLPP.

**Use ANTES de Read em qualquer `.prw` — economiza tokens drasticamente.**

Em vez de carregar 2000 linhas de fonte, voce recebe o "esqueleto":
- source_type (User Function, Rotina ERP, MVC, WS, Helper, ...)
- capabilities (acessa SQL, usa MVC, expoe WS, contem RecLock, ...)
- includes / includes_resolved
- defines
- namespace (TLPP)
- lista de simbolos (Function/Class/Method/Static)
- chamadas notaveis (restritas, ERP nativas)
- tabelas tocadas (read/write/reclock)
- params MV usados
- SQL embedado (BeginSql/TCQuery/TCSqlExec)
- WSSTRUCT / WSSERVICE / WSMETHOD
- MVC hooks (bCommit/bTudoOk/bLineOk/bPosVld/...)
- lint findings resumidos

## Uso

```
/plugadvpl:arch <arquivo>
```

## Execucao

```bash
uvx plugadvpl@0.3.18 --format md arch $arquivo
```

> **Para agente IA:** sempre passe `--format md` (ou `--format json` se for parsear). O default `table` usa Rich e trunca colunas em terminais estreitos (`ar...`, `ti...`). A flag `--format` vem **antes** do subcomando — eh global no callback.

## Exemplos

- `/plugadvpl:arch src/matxxx.prw` — visao de uma rotina MVC
- `/plugadvpl:arch src/wsxxx.prw` — visao de um WebService
- `/plugadvpl:arch include/totvs.ch` — visao de um include

## Workflow recomendado

1. **Antes** de Read: `/plugadvpl:arch <arquivo>` para entender a forma
2. Use `/plugadvpl:find`, `/plugadvpl:callers`, `/plugadvpl:tables` para navegar
3. So entao Read os trechos especificos que importam

## Proximos passos sugeridos

- `/plugadvpl:lint <arquivo>` — issues de qualidade/restritas
- `/plugadvpl:callers <funcao>` — onde simbolos do arquivo sao usados
- `/plugadvpl:callees <funcao>` — o que cada simbolo chama
