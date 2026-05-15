---
description: Lista execution_triggers indexados — workflow/schedule/job_standalone/mail_send (Universo 3 Rastreabilidade, v0.4.0+)
disable-model-invocation: true
arguments: [filtros]
allowed-tools: [Bash]
---

# `/plugadvpl:workflow`

**Killer feature do v0.4.0** (Universo 3 — Rastreabilidade). Lista os 4 mecanismos canônicos TOTVS de **execução não-direta** indexados pelo plugin:

| Kind | Detecção | Padrão TOTVS |
|------|----------|--------------|
| `workflow`       | `TWFProcess():New(...)`, `MsWorkflow(`, `WFPrepEnv(`, `:bReturn :=` | Aprovação por email com callback |
| `schedule`       | `Static Function SchedDef()` retornando `{cTipo,cPergunte,cAlias,aOrdem,cTitulo}` | Configurador SIGACFG |
| `job_standalone` | `Main Function` + `RpcSetEnv` + `Sleep` loop | Daemon ONSTART do AppServer |
| `mail_send`      | `MailAuto(`, `SEND MAIL` UDC, `TMailManager`/`TMailMessage` | Envio SMTP |

Antes do v0.4.0 era impossível responder via plugin "essa rotina é alvo de workflow ou apenas helper?", "que jobs do AppServer existem nesse projeto?", "qual schedule dispara `FATR020`?".

## Uso

```
/plugadvpl:workflow [--kind <kind>] [--target <nome>] [--arquivo <basename>]
```

## Opções

- `--kind` / `-k` — filtra por tipo (`workflow`/`schedule`/`job_standalone`/`mail_send`)
- `--target` / `-t` — filtra por nome alvo (callback, Main name, pergunte SX1, variant)
- `--arquivo` / `-a` — filtra por arquivo (basename, case-insensitive)

## Execução

```bash
uvx plugadvpl@0.4.3 --format md workflow $ARGUMENTS
```

> **Para agente IA:** prefira `--format md` (sem truncamento). Default `table` Rich trunca colunas em terminais estreitos. Flag global vem **antes** do subcomando.

## Exemplos

- `/plugadvpl:workflow` — lista todos os triggers do projeto
- `/plugadvpl:workflow --kind job_standalone` — só os jobs daemon
- `/plugadvpl:workflow --kind schedule` — relatórios e processos agendáveis (aponta pro pergunte SX1!)
- `/plugadvpl:workflow --target U_WfRetSN` — quem é callback de workflow
- `/plugadvpl:workflow --arquivo MGFCOM14.prw` — triggers desse fonte específico

## Saída

Por trigger:

| Campo | Significado |
|-------|-------------|
| `arquivo`  | fonte que tem o trigger |
| `funcao`   | função-pai onde foi detectado (resolved via chunks v0.3.15+) |
| `linha`    | linha exata da declaração |
| `kind`     | `workflow`/`schedule`/`job_standalone`/`mail_send` |
| `target`   | callback fn / Main name / pergunte / variant |
| `snippet`  | linha do match (truncada a 80 chars no display; use `--format json` pra ver completo) |

Detalhes específicos por kind ficam em `metadata` (acesse via `--format json`):

| kind | metadata |
|------|----------|
| `workflow`       | `process_id`, `description`, `template`, `to`, `subject`, `return_callback`, `timeout_callback`, `is_legacy` |
| `schedule`       | `sched_type` (P/R), `pergunte` (SX1!), `alias`, `ordens`, `titulo` |
| `job_standalone` | `main_name`, `empresa`, `filial`, `modulo`, `sleep_seconds`, `stop_flag`, `no_license` |
| `mail_send`      | `variant` (MailAuto/UDC/TMailManager), `has_attachment`, `uses_mv_rel` |

## Casos de uso pra análise de impacto

1. **"Esta User Function `XYZAprov` é alvo de workflow ou helper?"**
   → `/plugadvpl:workflow --target XYZAprov` — se aparecer com `kind=workflow`, é callback.

2. **"Que Main Functions deste projeto são jobs daemon?"**
   → `/plugadvpl:workflow --kind job_standalone` — lista todas com intervalo, módulo, flag de parada.

3. **"Esse `FATR020.prw` é agendável?"**
   → `/plugadvpl:workflow --arquivo FATR020.prw --kind schedule` — se sim, `metadata.pergunte` aponta o grupo SX1 que parametriza.

4. **"Onde envio email com anexo neste projeto?"**
   → `/plugadvpl:workflow --kind mail_send` + filtrar `metadata.has_attachment=True` no JSON.

5. **"Esse fonte usa configuração via SX6 ou hardcoded?"**
   → `mail_send` com `metadata.uses_mv_rel=True` = tá usando `MV_RELACNT`/`MV_RELPSW` (correto). False = tá hardcoded (cruzar com SEC-004 do lint).

## Cross-ref com outras features

- **`/plugadvpl:lint`** — SEC-004 detecta credenciais hardcoded em `RpcSetEnv`/`SMTPAuth`. Se `workflow` mostrar job e `lint` mostrar SEC-004, o job tem credencial leak.
- **`/plugadvpl:callers`** — depois de descobrir callback de workflow via `workflow --kind workflow`, use `callers` pra ver quem chama o callback diretamente (raro — geralmente só o motor de workflow).
- **`/plugadvpl:impacto`** (Universo 2) — pra schedule, `metadata.pergunte` referencia grupo SX1 que pode ser cruzado com `impacto`.
- **`/plugadvpl:arch`** — `arch` mostra capabilities do fonte; `workflow` complementa com "execução não-direta" que `arch` não cobre.

## Limitações conhecidas

- **Frequência de schedule** não é extraída — vive em `SCHTSK`/`SCHFIL`/`SCHSERV` (tabelas internas TOTVS Schedule, não SX). O `workflow` mostra que existe `SchedDef`, mas pra ver "roda diariamente às 02:00" precisa abrir o Configurador.
- **AppServer.ini não é cruzado** — se quiser confirmar que `Main JobX` está realmente em `[ONSTART] Jobs=JOB_X`, precisa abrir o INI. Plugin assume que toda Main+RpcSetEnv é candidata a job.
- **Workflow webview** (`TWebChannel`) não é detectado — raro, fora do escopo MVP.

## Próximos passos sugeridos

- `/plugadvpl:find <target>` — abre a função-callback/Main no índice
- `/plugadvpl:arch <arquivo>` — visão geral do fonte que tem o trigger
- `/plugadvpl:lint <arquivo> --severity critical,error` — checa se há SEC-004 (credencial hardcoded) no mesmo fonte
