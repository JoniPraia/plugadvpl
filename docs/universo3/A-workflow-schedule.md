# Universo 3 / Feature A — Workflow + Schedule + Job + Mail trigger indexing

**Status:** spec — aguardando aprovação antes de implementar
**Release alvo:** v0.4.0
**Tipo:** feature nova (schema migration + parser + comando + cross-file)
**Pesquisa:** subagent rodou pesquisa em TDN + GitHub + 16+ blogs/fóruns (resumo abaixo)

---

## 1. Problema

O índice atual (`Universo 1` fontes + `Universo 2` SX) responde "o que existe" e "qual a estrutura do dado", mas não responde **"quem dispara essa rotina e quando?"**. Quatro mecanismos canônicos TOTVS hoje ficam invisíveis no índice:

1. **Workflow** (`TWFProcess` / `MsWorkflow`) — emails com callback de aprovação
2. **Schedule** (`SchedDef` + Configurador SIGACFG) — agendamento periódico
3. **Job standalone** (`Main Function` + `RpcSetEnv` + `Sleep` loop) — daemon em ONSTART do AppServer
4. **Mail send** (`MailAuto` / `SEND MAIL` UDC / `TMailManager`) — envio SMTP

Hoje é **impossível** responder via plugin perguntas como:
- "Esta User Function `XYZAprov` é alvo de workflow ou apenas helper?"
- "Quais Main Functions deste projeto são jobs no AppServer?"
- "Qual schedule dispara `FATR020`?"
- "Onde envio email com anexo?"

**Impacto pra IA/usuário:** análise de impacto incompleta. Se mudo `XYZAprov`, sem saber que é callback de `TWFProcess`, posso quebrar workflow em produção sem warning.

## 2. O que sai dessa feature (escopo MVP v0.4.0)

**Capacidade nova:** indexar e expor as 4 categorias de "execution trigger" via comando dedicado.

**Não-objetivos** (deixar pra v0.4.x):
- Resolver chain "workflow → ExecAuto → tabela" (isso é Feature B)
- Cruzar com `appserver.ini` real do cliente (precisaria parser INI + ingest)
- Configurações persistidas em SCHTSK/SCHFIL/SCHSERV (tabelas internas Schedule, não SX)

## 3. Padrões TOTVS canônicos (resumo da pesquisa)

### 3.1 Workflow (`TWFProcess` moderno + `MsWorkflow` legado)

| Aspecto | Detalhe |
|---|---|
| Classe canônica | `TWFProcess():New(cId, cDesc)` |
| Legacy | `MsWorkflow(...)` (ainda existe em código antigo) |
| Helper de ambiente | `WFPrepEnv(cEmp, cFil, ...)` em callbacks (chamado quando email volta) |
| Callbacks | `oWF:bReturn := {|o| U_WfRetXxx(o)}`, `oWF:bTimeOut := {|o| U_WfTOXxx(o)}` |
| Disparo | `oWF:Start()` |
| Convenção nome | `WfXxx` ou `U_WF*` |

**Regex de detecção:**
- `\bTWFProcess\s*\(\s*\)\s*:\s*New\b`
- `\bMsWorkflow\s*\(`
- `\bWFPrepEnv\s*\(`
- `:\s*b(Return|TimeOut)\s*:=` (props de callback)

**Metadados extraíveis:** ID processo (1º arg), template HTML (2º arg de `NewTask`), destinatário (`cTo`), subject (`cSubject`), funções callback (resolved name).

### 3.2 Schedule (`SchedDef` + Configurador)

| Aspecto | Detalhe |
|---|---|
| Definição alvo | `Static Function SchedDef()` retorna array `{cTipo, cPergunte, cAlias, aOrdem, cTitulo}` |
| Tipos | `"P"` Process, `"R"` Report |
| Disparo programático | `StartSchedTask(...)`, `FwGetRunSchedule(...)` |
| Conexão SX | array[2] = pergunte SX1 (cross-ref com `perguntas` table) |

**Regex:** `(?im)^\s*Static\s+Function\s+SchedDef\s*\(`

**Metadados:** tipo (P/R), pergunte SX1, alias do relatório, título. Frequência **NÃO** está no fonte (vive em SCHTSK).

### 3.3 Job standalone (Main Function + RpcSetEnv)

| Aspecto | Detalhe |
|---|---|
| Entry point | `Main Function JobXxx()` (NÃO User Function) |
| Prep ambiente | `RpcSetEnv("01","01",,,"FAT","JobXxx")` |
| Sem licença | `RpcSetType(3)` |
| Loop daemon | `While lContinua` + `Sleep(N*1000)` + flag de stop |
| Cleanup | `RpcClearEnv()` |
| Config externa | AppServer.ini `[ONSTART] Jobs=JOB_X` + `[JOB_X] Main=JobXxx` |

**Regex combinado:** `Main Function` + presença de `RpcSetEnv` ou `RpcSetType(3)` no body.

**Metadados:** nome Main, empresa/filial hardcoded, módulo, intervalo (`Sleep(N)`), flag de parada (`File(...)`).

### 3.4 Mail send (`MailAuto` / UDC `SEND MAIL` / `TMailManager`)

| Variante | Sintaxe |
|---|---|
| ExecAuto | `MailAuto(cFrom, cTo, cSubj, cMsg, aAttach)` |
| UDC commands | `CONNECT SMTP SERVER ... ACCOUNT ... PASSWORD ...` + `SEND MAIL FROM ... TO ... SUBJECT ... BODY ...` |
| Classes | `TMailManager():New() + :Init() + :SmtpAuth() + :SmtpConnect()` + `TMailMessage():New() + :Send()` |

**Regex:**
- `\bMailAuto\s*\(`
- `(?im)\b(SEND\s+MAIL|CONNECT\s+SMTP)\b`
- `\bTMail(Manager|Message)\s*\(`

**Metadados:** From, To, Subject, presença de anexo, params SX6 referenciados (`MV_RELACNT`/`MV_RELPSW`/`MV_RELSERV`).

## 4. Schema proposto

### Migration `005_universo3_execution_triggers.sql`

```sql
CREATE TABLE IF NOT EXISTS execution_triggers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT DEFAULT '',          -- função onde foi detectado
    linha           INTEGER DEFAULT 0,
    kind            TEXT NOT NULL,            -- workflow | schedule | job_standalone | mail_send
    target          TEXT DEFAULT '',          -- callback function / Main name / etc
    metadata_json   TEXT DEFAULT '{}',        -- detalhes específicos por kind
    snippet         TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_exec_arquivo ON execution_triggers(arquivo);
CREATE INDEX IF NOT EXISTS idx_exec_kind    ON execution_triggers(kind);
CREATE INDEX IF NOT EXISTS idx_exec_target  ON execution_triggers(target);
```

**Campo `metadata_json` por kind:**

| kind | metadata fields (JSON) |
|---|---|
| `workflow` | `{"process_id": str, "template": str, "to": str, "subject": str, "return_callback": str, "timeout_callback": str, "is_legacy": bool}` |
| `schedule` | `{"sched_type": "P"\|"R", "pergunte": str, "alias": str, "ordens": [int], "titulo": str}` |
| `job_standalone` | `{"main_name": str, "empresa": str, "filial": str, "modulo": str, "sleep_seconds": int, "stop_flag": str, "no_license": bool}` |
| `mail_send` | `{"variant": "MailAuto"\|"UDC"\|"TMailManager", "from": str, "to": str, "subject": str, "has_attachment": bool, "uses_mv_rel": bool}` |

**Bump SCHEMA_VERSION:** 4 → 5.

## 5. Parser (cli/plugadvpl/parsing/triggers.py — módulo novo)

Novo módulo dedicado a triggers (separado de `lint.py`/`parser.py` pra não inflar). Função pública: `extract_execution_triggers(content) → list[dict]`.

Cada detector é função privada `_detect_<kind>(content) → list[dict]`. Convenção: retorna dict com `kind`/`target`/`metadata`/`linha`/`snippet`.

**Heurística de cascata** (decidir kind quando padrões sobrepõem):
1. `Static Function SchedDef` → `schedule`
2. `Main Function` + `RpcSetEnv` no body → `job_standalone`
3. `TWFProcess` ou `MsWorkflow` ou `WFPrepEnv` → `workflow`
4. `MailAuto` ou `SEND MAIL` ou `TMailMessage:Send` → `mail_send`

Mesmo fonte pode ter múltiplos triggers (job que envia email + workflow callback). 1 row por detecção.

## 6. Ingest

`ingest.py` chama `extract_execution_triggers(content)` no parse de cada fonte e popula `execution_triggers` (com DELETE+INSERT por arquivo, mesmo padrão de `lint_findings`).

Adicionar em `_clear_for_arquivo`: `DELETE FROM execution_triggers WHERE arquivo=?`.

## 7. Comando novo `plugadvpl workflow`

```
plugadvpl workflow [--kind {workflow,schedule,job_standalone,mail_send}] [--target <funcao>]
```

Lista triggers indexados. Filtros opcionais. Output (table/json/md):

```
arquivo          | funcao        | linha | kind            | target           | snippet
WFSalNeg.prw     | WfSalNeg      | 7     | workflow        | U_WfRetSN        | TWFProcess():New("SALNEG"...)
JobMonNFe.prw    | JobMonNFe     | 1     | job_standalone  | JobMonNFe        | Main Function...
FATR020.prw      | SchedDef      | 12    | schedule        | FATR020          | aParam := {"R","FAT020",...}
EnvMailAnex.prw  | EnvMailAnex   | 5     | mail_send       | (multiplo)       | TMailManager():New()...
```

**Skill nova:** `skills/workflow/SKILL.md` (similar a `find`, `tables`).

## 8. Edge cases / falsos positivos

| Caso | Mitigação |
|---|---|
| `TWFProcess` em comentário/string | `strip_advpl(strip_strings=True)` |
| `Main Function MyExe()` SEM RpcSetEnv (não é job) | exigir RpcSetEnv ou RpcSetType no body |
| `MailAuto` em script desabilitado (comentado) | comentários removidos |
| `SchedDef` com nome similar mas não exato | `^\s*Static\s+Function\s+SchedDef\s*\(\s*\)` (boundary) |
| `MailAuto` mock em test fixture | aceitar (info severity, sem bloquear) |
| Workflow callback sem `oProcess` arg | aceitar — heurística é melhor que regra estrita |

## 9. Plano de implementação (TDD red→green)

1. **Migration 005** — criar tabela `execution_triggers` + bump SCHEMA_VERSION.
2. **Módulo parser triggers.py** — 4 detectores + função pública.
3. **Tests unit** — 1 fixture por kind, positivo + negativo (8 tests mín).
4. **Ingest** — chamar extractor + popular tabela.
5. **Query** — função `query.execution_triggers_query(conn, kind=?, target=?)`.
6. **Comando** — `cli.py` add `workflow` subcomando + skill.
7. **Test integration** — fixture multi-trigger + assert query.
8. **CHANGELOG** + bump 0.3.30 → 0.4.0 + release.

**Testes esperados:** ~12-15 novos. Suite total ~404+.

## 10. Trade-offs aceitos

- **Não cruza com appserver.ini real** — assumir que projeto não tem o INI no DB. Se quiser cruzar, é nova feature `ingest-appserver` (out of scope MVP).
- **Não detecta workflow webview** (`TWebChannel`) — raro, fora do escopo "rastreabilidade tradicional".
- **Frequência de schedule não extraída** — vive em SCHTSK no banco TOTVS, não no fonte. Documentar como limitação conhecida.
- **MailAuto fire-and-forget vs callback workflow** — diferenciar por contexto (heurística pode errar; aceitar).

## 11. Comparação com features existentes

| Feature | Cobre o quê | Lacuna que A preenche |
|---|---|---|
| `find <fn>` | Onde a função está declarada | Não diz "quem chama em runtime" |
| `callers <fn>` | Chamadas estáticas via `U_*`/`ExecBlock` | Não pega callbacks de workflow nem disparo programático |
| `arch <arq>` | Resumo arquitetural do fonte | Não tem categoria "tipo de execução" |
| `tables <T>` | Quem CRUD a tabela | Não diz "quem CRUD em workflow vs job vs UI" |
| **`workflow` (NOVO)** | **Triggers de execução** | — |

## 12. Fontes consultadas (research)

- [BlackTDN — RPCSetEnv vs WFPrepEnv](https://www.blacktdn.com.br/2010/09/protheus-rpcsetenv-vs-prepare.html)
- [TDN — TWFProcess oficial](https://tdn.totvs.com/display/public/PROT/TWFProcess)
- [TDN — Schedule overview](https://tdn.totvs.com/pages/viewpage.action?pageId=271167961)
- [TDN — SchedDef estrutura](https://tdn.totvs.com/pages/viewpage.action?pageId=36800166)
- [Central TOTVS — SchedDef oficial](https://centraldeatendimento.totvs.com/hc/pt-br/articles/21895227246871)
- [Terminal de Informação — RpcSetEnv](https://terminaldeinformacao.com/2024/05/20/preparando-o-ambiente-com-a-rpcsetenv-maratona-advpl-e-tl-426/)
- [Terminal de Informação — StartJob](https://terminaldeinformacao.com/2022/03/30/como-usar-o-startjob-para-atualizar-informacoes/)
- [Terminal de Informação — Disparo de e-Mail via AdvPL](https://terminaldeinformacao.com/2020/04/10/exemplo-de-disparo-de-e-mail-via-advpl/)
- [Terminal de Informação — Função e-mail vários anexos](https://terminaldeinformacao.com/2017/10/17/funcao-dispara-e-mail-varios-anexos-em-advpl/)
- [Master Advpl — Customização ao iniciar AppServer](http://www.masteradvpl.com.br/index.php/forum/2-advpl/11719-rodar-customizacao-ao-iniciar-o-appserver)
- [GitHub ndserra/advpl — WFSalNeg.prw real example](https://github.com/ndserra/advpl/blob/master/_Material_Herold/WorkFlow/Diversos%20NET/WFSalNeg.prw)
- [GitHub ndserra/advpl — Schedule.prw real example](https://github.com/ndserra/advpl/blob/master/ADVPL/resources/Schedule.prw)
- [Central TOTVS — TMailMessage compromisso de agenda](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360027554151)
- [VDASoft — SCHEDDEF estrutura](https://vdasoftblog.wordpress.com/2016/08/04/scheddef/)
- [FBSolutions — Parâmetros SX6 envio email](http://www.fbsolutions.com.br/erp-totvs-protheus/parametros-para-envio-de-e-mail-protheus/)

---

## Decisão pendente — preciso da sua aprovação em:

1. **Schema** — `execution_triggers` com `metadata_json` flexível por kind, ou tabelas separadas (`workflows`/`schedules`/`jobs`/`mail_sends`) com colunas tipadas?
2. **Comando** — `plugadvpl workflow` cobre tudo, ou prefere comandos separados (`plugadvpl schedule`, `plugadvpl job`, etc)?
3. **Versão** — vai pra v0.4.0 (bump major do v0.3.30) ou v0.3.31 → v0.4.0 só quando A+B+C estiverem prontos?
4. **Severidade migration** — schema 4→5 é breaking pra usuários antigos (precisa re-init OU `ingest --no-incremental`). Aceitável?

Recomendação minha: **schema unificado + comando único + v0.4.0 agora + breaking aceitável** (já estabelecemos pattern de warning de migration drift na v0.3.13/v0.3.23).
