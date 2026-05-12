---
description: JOBs e RPC no Protheus — Main Function, RpcSetType(3)+RpcSetEnv(emp,fil,user,pwd,env,modulo), PREPARE/END ENVIRONMENT, StartJob, MsRunInThread, scheduler via appserver.ini. Funções proibidas em JOB (MsgInfo, Pergunte, Help, FwAlertHelp). FwLogMsg para log estruturado. Use ao trabalhar com processo agendado, integração batch ou RPC.
---

# advpl-jobs-rpc — Execução headless no Protheus

Quando o Protheus precisa executar código **sem usuário humano logado** (cron-like jobs, scheduler, integrações batch, RPC chamado por sistema externo), o entrypoint não é `User Function` — é **`Main Function`** disparada via configuração do `appserver.ini` ou via `StartJob`/`CallProc`/`MsRunInThread`.

Diferenças fundamentais para fluxo de UI:

- **Não há `cFilAnt`/`cEmpAnt` preenchidos** — você abre o ambiente explicitamente com `RpcSetEnv`.
- **Não pode chamar UI** (`MsgInfo`, `Aviso`, `Help`, `FwAlertHelp`, `MsgBox`, `Pergunte`) — trava o JOB para sempre esperando interação inexistente.
- **Erros precisam ser logados em arquivo/ConOut/FwLogMsg**, não em diálogo modal.
- **Em REST, `RpcSetEnv` é proibido** (veja `[[advpl-webservice]]` — SEC-001 impl). Em JOB, é mandatório.

## Quando usar

- Edit/criação de fonte com `Main Function`.
- Usuário menciona "JOB", "scheduler", "agendamento", "rotina batch", "integração em background", "thread", "RPC".
- Aparece `RpcSetEnv`, `PrepareIn`, `StartJob`, `CallProc`, `MsRunInThread`, `Sleep`, `FwSchedExec` em fonte.
- Investigação de "rotina rodou mas não fez nada" (provavelmente travada em `MsgInfo`/`Pergunte`).

## Estrutura mínima de JOB

```advpl
#include "TOTVS.CH"

/*/{Protheus.doc} XYZJob
JOB de integracao de pedidos diaria.
Disparado por scheduler do appserver.ini.

@type function
@author Equipe XYZ
@since 2026-05-12
@param cEmp, character, empresa (default 01)
@param cFil, character, filial (default 0101)
/*/
Main Function XYZJob(cEmp, cFil)
    Local cEmpDef := If(Empty(cEmp), "01",   AllTrim(cEmp))
    Local cFilDef := If(Empty(cFil), "0101", AllTrim(cFil))

    // Tipo 3 = JOB, nao consome licenca de UI (importante!)
    RpcSetType(3)
    RpcSetEnv(cEmpDef, cFilDef, "admin", "totvs", "FAT", "XYZJob",,, .F.)

    ConOut("[" + FwTimeStamp() + "] XYZJob iniciado em " + cEmpDef + "/" + cFilDef)
    FwLogMsg("INFO", , "XYZJob", "main", , 0, 0, "Iniciado em " + cEmpDef + "/" + cFilDef)

    Begin Sequence
        ProcessaPedidos()
    Recover Using oErr
        ConOut("[" + FwTimeStamp() + "] XYZJob ERRO: " + oErr:Description)
        ConOut(oErr:ErrorStack)
        FwLogMsg("ERROR", , "XYZJob", "main", , 0, 0, oErr:Description)
        // Notificar admin via email
        NotificaAdmin(oErr:Description)
    End Sequence

    ConOut("[" + FwTimeStamp() + "] XYZJob finalizado")
    RpcClearEnv()
Return Nil

Static Function ProcessaPedidos()
    // ... logica
Return Nil

Static Function NotificaAdmin(cMsg)
    // MailAuto + SendMail + DisconnectMail
Return Nil
```

## `RpcSetEnv` — assinatura completa

```advpl
RpcSetEnv(cEmpresa, cFilial, cUser, cPassword, cAmbiente, cModulo, ;
         aTables, lShowFin, lAbreExclusivo)
```

| Pos | Parâmetro       | Tipo | Default        | O que faz                                  |
|-----|-----------------|------|----------------|--------------------------------------------|
| 1   | `cEmpresa`      | C    | obrig          | Código da empresa (2 caracteres)           |
| 2   | `cFilial`       | C    | obrig          | Filial (4 caracteres)                      |
| 3   | `cUser`         | C    | `""`           | Usuário Protheus                           |
| 4   | `cPassword`     | C    | `""`           | Senha (pode usar `EncryptPwd` pra criptografar) |
| 5   | `cAmbiente`     | C    | env do appsv   | Ambiente (`PRODUCAO`, `HOMOL`)             |
| 6   | `cModulo`       | C    | `""`           | Sigla do módulo (`FAT`, `EST`, `FIN`)      |
| 7   | `aTables`       | A    | `{}`           | Tabelas a abrir (vazio = abre conforme módulo) |
| 8   | `lShowFin`      | L    | `.F.`          | Mostra dialog financeiro (NÃO usar em JOB) |
| 9   | `lAbreExclusivo`| L    | `.F.`          | Abre tabelas em modo exclusivo             |

**Sempre chame `RpcClearEnv()` no fim** para liberar conexão e contexto.

## `RpcSetType` — tipo de conexão

| Valor | Significado                                                          |
|-------|----------------------------------------------------------------------|
| 1     | Default — consome licença "advpl/protheus" (UI-like) — **EVITAR em JOB** |
| 2     | RPC web service — também consome licença                             |
| 3     | JOB — **não consome licença de UI** (recomendado p/ batch)           |

**Em JOB sempre use `RpcSetType(3)` ANTES do `RpcSetEnv`.** Inverter a ordem ou esquecer faz o JOB consumir uma licença caríssima desnecessariamente.

## `GetEnvServer()` — ambiente atual

Quando precisar do nome do ambiente onde o AppServer está rodando (`PRODUCAO`, `HOMOL`, etc.):

```advpl
StartJob("XYZJob", GetEnvServer(), .T., "01", "0101")
//                  retorna o ENVIRONMENT= do [GENERAL] do ini
```

Útil pra não hardcoded o ambiente quando o mesmo fonte roda em diferentes instâncias.

## `PREPARE ENVIRONMENT` / `END ENVIRONMENT` (alternativa)

Sintaxe declarativa equivalente com cleanup automático:

```advpl
PREPARE ENVIRONMENT EMPRESA cEmp FILIAL cFil MODULO "FAT" TABLES "SA1","SC5","SF2"
    // codigo com ambiente aberto
    ProcessaPedidos()
END ENVIRONMENT
// ambiente fechado automaticamente aqui
```

Útil para escopo curto. Para JOBs longos com hooks/transações, prefira `RpcSetEnv`/`RpcClearEnv` por controle explícito.

## Disparando jobs

### Via appserver.ini (scheduler do Protheus — tradicional)

```ini
[ONSTART]
JOBS=XYZJob_Diario,ABCJob_NF

[XYZJob_Diario]
TYPE=job                        ; tipo de slot
MAIN=XYZJob                     ; Main Function a chamar
ENVIRONMENT=PRODUCAO
NPARMS=2                        ; quantos PARMs passa
PARM1=01                        ; PARAMS posicionais que viram args
PARM2=0101
DAYS=1,2,3,4,5                  ; segunda a sexta
HOUR=02:00                      ; 2h da manha
INSTANCES=1
ONSTART=                        ; hook adicional
```

### Via `FwSchedExec` (scheduler programático, mais moderno)

```advpl
FwSchedExec("ZJOB001", "XYZJob", "PRODUCAO", "01", "0101")
//          id_unico   main      ambiente   emp   fil
// Cria entrada no scheduler interno do Protheus
```

### Via `StartJob` em código

```advpl
StartJob("XYZJob", GetEnvServer(), .T., "01", "0101")
//        main      ambiente,      lWait, ...args
// lWait = .T. espera o job terminar antes de retornar
// lWait = .F. dispara assincrono
```

### Via `CallProc` (RPC entre slots)

```advpl
CallProc("XYZJob", "01", "0101")   // executa SINCRONO no mesmo processo
```

### Threads paralelas — `MsRunInThread`

```advpl
MsRunInThread(0, "XYZParteParalela", aDados)
//             slot, funcao,         args
```

Cada thread herda o ambiente do thread pai. **Mas cuidado com WorkArea**: cada thread deve fazer seu próprio `GetArea`/`RestArea`. Sem isso, threads disputam o ponteiro do alias e geram bug "qual registro tô vendo?".

## Funções proibidas em JOB

Estas chamadas **travam o JOB** porque tentam abrir modal/diálogo num processo sem display:

| Função          | Por quê quebra                          | Substituto                             |
|-----------------|------------------------------------------|----------------------------------------|
| `MsgInfo`       | Modal dialog                             | `ConOut("INFO: ...")` / `FwLogMsg`     |
| `MsgAlert`      | Modal                                    | `ConOut("WARN: ...")` / `FwLogMsg`     |
| `MsgStop`       | Modal                                    | `ConOut("ERROR: ...")` + return        |
| `Aviso`         | Modal                                    | `ConOut`                               |
| `Help`          | Modal Protheus de erro                   | `ConOut(...)` + flag de erro           |
| `FwAlertHelp`   | Wrap do Help (mesma coisa)               | `ConOut`/`FwLogMsg`                    |
| `MsgYesNo`      | Modal com resposta                       | Lógica pré-decidida via parâmetro      |
| `MsgBox`        | Modal                                    | `ConOut`                               |
| `Pergunte`      | Tela de parâmetros (interativa)          | Parâmetros via `PARM1`/`PARM2` no INI  |
| `oTela:Activate`| Qualquer ativação de tela                | Rotina headless equivalente            |
| `MsgRun`        | Tela de progresso modal                  | Log estruturado de progresso           |

> Para **logging estruturado em JOB**, prefira `FwLogMsg` sobre `ConOut`. Veja `[[advpl-code-review]]` regra MOD-001 (impl) — ConOut é flagged em Code Analysis.

## E-mail em JOB — `FwSendMail` / `MailAuto`

```advpl
// Padrao moderno (TLS/SSL friendly)
Local oMail := FwSendMail():New()
oMail:SetServer("smtp.empresa.com.br", 587)
oMail:SetCredential("noreply@empresa.com", "senha_aqui")
oMail:SetTimeout(30)
oMail:SetEnableTLS(.T.)
oMail:Connect()
oMail:Send("destino@cliente.com", "Job falhou", cCorpo, "anexo.pdf")
oMail:Disconnect()

// Padrao legado (ainda funciona)
MailAuto("smtp.empresa.com.br", "noreply@empresa.com", "totvs", , .F.)
SendMail("destinatario@cliente.com", "Assunto", "Corpo", "anexo.pdf")
DisconnectMail()
```

Em JOB, e-mail é a forma comum de "notificar admin" quando algo falha — combine com `Begin Sequence`/`Recover`.

## Anti-padrões

- **`MsgInfo("Iniciou")` no começo do JOB** → **trava para sempre** no scheduler. Use `ConOut`/`FwLogMsg`.
- **Esquecer `RpcClearEnv` no fim** → conexão SX vazada, RPO segura recursos.
- **`RpcSetEnv` sem `RpcSetType(3)` antes** → consome licença de UI cara desnecessariamente.
- **Hardcode de senha** (`"totvs"`) no fonte → catalogado como `SEC-004` (não detectado pelo lint hoje, mas é problema real). Use SuperGetMV/SX6 ou variável de ambiente, ou `EncryptPwd` armazenado em arquivo seguro.
- **Job sem `Begin Sequence`/`Recover`** → erro derruba ele silenciosamente, ninguém fica sabendo.
- **Não logar início/fim/falha** → impossível debug de "rodou ou não rodou".
- **`Pergunte` em JOB** → trava (não há quem responder). Use PARM1/PARM2 do INI ou parâmetros da `Main Function`.
- **`MsRunInThread` sem `GetArea`/`RestArea`** em cada uma → corrompe WorkArea do thread pai.
- **Job longo sem `Sleep`/`SX_Sleep` em loop apertado** → consome 100% CPU desnecessariamente. Coloque `Sleep(100)` em loop de polling.
- **`StartJob(...., .T., ...)` em web request** → bloqueia o request HTTP esperando o job terminar; use `.F.` (async) ou separe.
- **Conflito de licença em produção**: `RpcSetType(1)` herda dialog/UI → consome `LicenseOk()` quando JOB roda em massa → outros usuários ficam sem licença.

## Cross-references com outras skills

- `[[advpl-webservice]]` — `RpcSetEnv` é PROIBIDO em REST (SEC-001 impl); use `PrepareIn`+`TenantId`.
- `[[advpl-web]]` — `RpcSetEnv` é OK em ADVPL Web (diferente de REST 2.0).
- `[[advpl-fundamentals]]` — `Main Function` (entrypoint de JOB, sem prefixo cliente).
- `[[advpl-code-review]]` — MOD-001 (ConOut → FwLogMsg).
- `[[advpl-debugging]]` — diagnosticar "JOB não rodou" / travado.
- `[[advpl-mvc]]` — `FWMVCRotAuto` em JOB para inclusão em lote via MVC.
- `[[advpl-embedded-sql]]` — `TCSqlExec` em JOB para DML em massa.
- `[[advpl-pontos-entrada]]` — PE não usa `Main Function`, mas conceito de "sem UI" se aplica.
- `[[plugadvpl-index-usage]]` — `/plugadvpl:find function <Main>` lista jobs.

## Referência rápida

| Item                          | Como                                              |
|-------------------------------|---------------------------------------------------|
| Entrypoint                    | `Main Function NOME(arg1, arg2, ...)`             |
| Tipo de conexão               | `RpcSetType(3)` ANTES do RpcSetEnv (JOB sem UI)   |
| Abre ambiente                 | `RpcSetEnv(emp, fil, user, pwd, ambiente, mod)`   |
| Fecha ambiente                | `RpcClearEnv()`                                   |
| Alternativa declarativa       | `PREPARE ENVIRONMENT ... END ENVIRONMENT`         |
| Ambiente atual                | `GetEnvServer()` (lê `ENVIRONMENT=` do ini)       |
| Logging                       | `ConOut(...)` (simples) / `FwLogMsg(...)` (estruturado) |
| Tratamento de erro            | `Begin Sequence ... Recover Using oErr ... End`   |
| Disparar outro job (async)    | `StartJob("nome", env, .F., ...args)`             |
| Disparar outro job (sync)     | `StartJob("nome", env, .T., ...args)`             |
| Disparar via scheduler        | `FwSchedExec(id, main, env, ...)`                 |
| RPC sincrono mesmo processo   | `CallProc("nome", ...args)`                       |
| Thread paralela               | `MsRunInThread(slot, "func", ...args)`            |
| E-mail moderno                | `FwSendMail():New()` (TLS/SSL)                    |
| E-mail legado                 | `MailAuto` + `SendMail` + `DisconnectMail`        |
| Pausa                         | `Sleep(ms)` (millisegundos)                       |
| **NUNCA em JOB**              | `MsgInfo`, `MsgAlert`, `Aviso`, `Help`, `FwAlertHelp`, `Pergunte`, `MsgBox`, `MsgYesNo`, `MsgRun`, `oTela:Activate` |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <Main>` — localiza `Main Function`.
- `/plugadvpl:grep "RpcSetEnv\|StartJob\|FwSchedExec"` — descobre jobs no projeto.
- `/plugadvpl:callers <fn>` — vê quem é chamada por `StartJob`/`CallProc`.
- `/plugadvpl:lint <arq>` — checa MOD-001 (ConOut → FwLogMsg).
- Tabela `env_openers` do índice cataloga todos `RpcSetEnv`/`PrepareEnv` no projeto.

## Sources

- [RpcSetEnv e RpcClearEnv - Tudo em AdvPL](https://siga0984.wordpress.com/category/rpc/)
- [Pontos de Entrada em JOB - Terminal de Informação](https://terminaldeinformacao.com/knowledgebase/jobs-em-advpl/)
- [FwSchedExec - TDN](https://tdn.totvs.com/display/tec/FWSchedExec)
- [Boas práticas em Webservices e jobs - LinkedIn](https://pt.linkedin.com/pulse/boas-pr%C3%A1ticas-em-webservices-e-jobs-advpl-josu%C3%A9-danich)
- [Job, Threads, Sleep - Tudo em AdvPL Tag JOB](https://siga0984.wordpress.com/tag/job/)
- [appserver.ini examples - ndserra/advpl GitHub](https://github.com/ndserra/advpl/blob/master/_AULAS/appserver.ini)
