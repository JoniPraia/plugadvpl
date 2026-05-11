---
description: JOBs e RPC no Protheus — Main Function, RpcSetEnv(emp,fil,user,pwd,env,modulo), PREPARE/END ENVIRONMENT, StartJob, MsRunInThread. Funções proibidas em JOB (MsgInfo, Aviso, Help, FwAlertHelp). Use ao trabalhar com processo agendado, scheduler ou job assíncrono.
---

# advpl-jobs-rpc — Execução headless no Protheus

Quando o Protheus precisa executar código **sem usuário humano logado** (cron-like jobs, scheduler, integrações batch, RPC chamado por sistema externo), o entrypoint não é `User Function` — é **`Main Function`** disparada via configuração do `appserver.ini` ou via `StartJob`/`CallProc`/`MsRunInThread`.

Diferenças fundamentais para fluxo de UI:

- **Não há `cFilAnt`/`cEmpAnt` preenchidos** — você abre o ambiente explicitamente com `RpcSetEnv`.
- **Não pode chamar UI** (`MsgInfo`, `Aviso`, `Help`, `FwAlertHelp`, `MsgBox`) — trava o JOB para sempre.
- **Erros precisam ser logados em arquivo/ConOut**, não em diálogo modal.

## Quando usar

- Edit/criação de fonte com `Main Function`.
- Usuário menciona "JOB", "scheduler", "agendamento", "rotina batch", "integração em background", "thread", "RPC".
- Aparece `RpcSetEnv`, `PrepareIn`, `StartJob`, `CallProc`, `MsRunInThread`, `Sleep` em fonte legacy.
- Investigação de "rotina rodou mas não fez nada" (provavelmente travada em `MsgInfo`).

## Estrutura mínima de JOB

```advpl
#include "TOTVS.CH"

/*/{Protheus.doc} XYZJob
JOB de integracao de pedidos diaria.
Disparado por scheduler do appserver.ini.
/*/
Main Function XYZJob(cEmp, cFil)
    Local cEmpDef := If(Empty(cEmp), "01",   AllTrim(cEmp))
    Local cFilDef := If(Empty(cFil), "0101", AllTrim(cFil))

    // Abre ambiente Protheus
    RpcSetType(3)              // 3 = job sem licenca de UI
    RpcSetEnv(cEmpDef, cFilDef, "admin", "totvs", "FAT", "XYZJob",,, .F.)

    ConOut("[" + Time() + "] XYZJob iniciado em " + cEmpDef + "/" + cFilDef)

    Begin Sequence
        // Lógica do job
        ProcessaPedidos()
    Recover Using oErr
        ConOut("[" + Time() + "] XYZJob ERRO: " + oErr:Description)
        ConOut(oErr:ErrorStack)
    End Sequence

    ConOut("[" + Time() + "] XYZJob finalizado")
    RpcClearEnv()
Return Nil

Static Function ProcessaPedidos()
    // ...
Return Nil
```

## `RpcSetEnv` — assinatura completa

```advpl
RpcSetEnv(cEmpresa, cFilial, cUser, cPassword, cAmbiente, cModulo, ;
         aTables, lShowFin, lAbreExclusivo)
```

| Posição | Parâmetro      | Tipo | Default        | O que faz                                  |
|---------|----------------|------|----------------|--------------------------------------------|
| 1       | `cEmpresa`     | C    | obrig          | Código da empresa (2 caracteres)           |
| 2       | `cFilial`      | C    | obrig          | Filial (4 caracteres)                      |
| 3       | `cUser`        | C    | `""`           | Usuário Protheus                           |
| 4       | `cPassword`    | C    | `""`           | Senha (criptografada com `EncryptPwd`)     |
| 5       | `cAmbiente`    | C    | env do appsv   | Ambiente (`PRODUCAO`, etc.)                |
| 6       | `cModulo`      | C    | `""`           | Sigla do módulo (`FAT`, `EST`, `FIN`)      |
| 7       | `aTables`      | A    | `{}`           | Tabelas a abrir (vazio = abre conforme módulo) |
| 8       | `lShowFin`     | L    | `.F.`          | Mostra dialog financeiro                   |
| 9       | `lAbreExclusivo` | L  | `.F.`          | Abre tabelas em modo exclusivo             |

**Sempre chame `RpcClearEnv()` no fim** para liberar conexão.

## `RpcSetType` — tipo de conexão

| Valor | Significado                                                   |
|-------|---------------------------------------------------------------|
| 1     | Default — consome licença "advpl/protheus" (UI-like)          |
| 2     | RPC web service                                               |
| 3     | JOB — **não consome licença de UI** (recomendado p/ batch)    |

**Em JOB sempre use `RpcSetType(3)` antes do `RpcSetEnv`.**

## `PREPARE ENVIRONMENT` / `END ENVIRONMENT` (alternativa)

Sintaxe declarativa equivalente:

```advpl
PREPARE ENVIRONMENT EMPRESA cEmp FILIAL cFil MODULO "FAT" TABLES "SA1","SC5","SF2"
    // código com ambiente aberto
END ENVIRONMENT
```

Cleanup automático no `END ENVIRONMENT`. Útil para escopo curto. Para JOBs longos, prefira `RpcSetEnv`/`RpcClearEnv` por controle explícito.

## Disparando jobs

### Via appserver.ini (scheduler do Protheus)

```ini
[ONSTART]
JOBS=XYZJob_Diario,ABCJob_NF

[XYZJob_Diario]
MAIN=XYZJob
ENVIRONMENT=PRODUCAO
NPARMS=2
PARM1=01
PARM2=0101
DAYS=1,2,3,4,5         ; segunda a sexta
HOUR=02:00             ; 2h da manhã
INSTANCES=1
ONSTART=
```

### Via `StartJob` em código

```advpl
StartJob("XYZJob", GetEnvServer(), .T., "01", "0101")
//                 ambiente,      lWait, ...args
```

### Via `CallProc` (RPC entre slots)

```advpl
CallProc("XYZJob", "01", "0101")  // executa síncrono no mesmo processo
```

### Threads paralelas — `MsRunInThread` / `MsExecAuto`

```advpl
MsRunInThread(0, "XYZParteParalela", aDados)
```

Cada thread herda o ambiente do thread pai. **Mas cuidado com WorkArea**: cada thread deve fazer seu próprio `GetArea/RestArea` (`BP-003`).

## Funções proibidas em JOB

Estas chamadas **travam o JOB** porque tentam abrir modal/diálogo num processo sem display:

| Função          | Por quê quebra                                     | Substituto                             |
|-----------------|----------------------------------------------------|----------------------------------------|
| `MsgInfo`       | Modal dialog                                       | `ConOut("INFO: ...")`                  |
| `MsgAlert`      | Modal                                              | `ConOut("WARN: ...")`                  |
| `MsgStop`       | Modal                                              | `ConOut("ERROR: ...")` + return        |
| `Aviso`         | Modal                                              | `ConOut`                               |
| `Help`          | Modal Protheus de erro                             | `ConOut(...)` + flag de erro           |
| `FwAlertHelp`   | Wrap do Help (mesma coisa)                         | `ConOut`/`FWLogMsg`                    |
| `MsgYesNo`      | Modal com resposta                                 | Lógica pré-decidida via parâmetro      |
| `MsgBox`        | Modal                                              | `ConOut`                               |
| `Pergunte`      | Tela de parâmetros (interativa)                    | Parâmetros via `PARM1`/`PARM2` no INI  |
| `oTela:Activate`| Qualquer ativação de tela                          | Rotina headless equivalente            |

**Recomenda-se `FWLogMsg`** para logging estruturado em JOB:

```advpl
FWLogMsg("INFO", , "XYZJob", "ProcessaPedidos", "PED001", 0, 0, "Processado")
```

## E-mail em JOB — `MailAuto` / `FwSendMail`

```advpl
MailAuto("smtp.empresa.com.br", "noreply@empresa.com", "totvs", , .F.)
SendMail("destinatario@cliente.com", "Assunto", "Corpo", "anexo.pdf")
DisconnectMail()
```

Em ambientes novos use `FwSendMail` (mesma família, mais opções TLS/SSL). Em JOB, e-mail é a forma comum de "notificar admin" quando algo falha.

## Anti-padrões

- `MsgInfo("Iniciou")` no começo do JOB → **trava para sempre** no scheduler.
- Esquecer `RpcClearEnv` no fim → conexão SX vazada.
- `RpcSetEnv` sem `RpcSetType(3)` → consome licença de UI cara.
- Hardcode de senha (`"totvs"`) no fonte → `SEC-004`. Use credencial criptografada via SX6/SuperGet ou variável de ambiente.
- Job sem `Begin Sequence`/`Recover` → erro derruba ele silenciosamente.
- Não logar início/fim → não tem como debug de "rodou ou não rodou".
- `Pergunte` em job → trava (não há quem responder).
- Threads (`MsRunInThread`) sem `GetArea`/`RestArea` em cada uma → corrompe WorkArea do thread pai.

## Referência rápida

| Item                          | Como                                              |
|-------------------------------|---------------------------------------------------|
| Entrypoint                    | `Main Function NOME(arg1, arg2, ...)`             |
| Abre ambiente                 | `RpcSetType(3) ; RpcSetEnv(emp, fil, ...)`        |
| Fecha ambiente                | `RpcClearEnv()`                                   |
| Logging                       | `ConOut(...)` ou `FWLogMsg(...)`                  |
| Tratamento de erro            | `Begin Sequence ... Recover Using oErr ... End`   |
| Disparar outro job            | `StartJob("nome", env, lWait, ...args)`           |
| Thread paralela               | `MsRunInThread(slot, "func", ...args)`            |
| E-mail                        | `MailAuto` + `SendMail` + `DisconnectMail`        |
| Sleep                         | `Sleep(ms)`                                       |
| Em JOB **não** use            | `MsgInfo`, `MsgAlert`, `Aviso`, `Help`, `FwAlertHelp`, `Pergunte`, `MsgBox`, `MsgYesNo`, `oTela:Activate` |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <Main>` — localiza `Main Function`.
- `/plugadvpl:callers <fn>` — vê quem é chamada por `StartJob`/`CallProc`.
- `/plugadvpl:lint <arq>` — verifica `SEC-004` (credencial hardcoded), `BP-005` (sem `Begin Sequence`).
