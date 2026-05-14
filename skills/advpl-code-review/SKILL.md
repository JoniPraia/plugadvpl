---
description: 24 regras de code review ADVPL/TLPP implementadas (13 single-file via regex + 11 cross-file SX que requerem ingest-sx). Mais 11 regras catalogadas porém ainda não detectadas. Use após gerar/editar fonte ADVPL, antes de marcar tarefa como concluída, ou quando o usuário pede "revise este código".
---

# advpl-code-review — As regras de code review do plugadvpl

`plugadvpl` cataloga **35 regras de code review** para ADVPL/TLPP. Destas, **29 são efetivamente detectadas** (v0.3.9+): **18 single-file** via regex/AST/lookup sobre o conteúdo do fonte, e **11 cross-file `SX-*`** que cruzam o dicionário SX com os fontes (requer `/plugadvpl:ingest-sx` rodado antes). As outras 6 ficam **catalogadas como `status='planned'`** — sem detecção automática hoje, mas servem como roadmap + checklist mental.

> **Catálogo alinhado com a impl** desde v0.3.4. Antes (v0.3.0..v0.3.3), o
> `lookups/lint_rules.json` tinha 25 itens em drift com `parsing/lint.py`
> (10 severidades + 15 títulos diferentes pro mesmo `regra_id`). [Issue #1](https://github.com/JoniPraia/plugadvpl/issues/1) corrigida em v0.3.4
> + teste `test_lint_catalog_consistency.py` impede regressão futura.
> O catálogo agora carrega 2 campos extras: `status` (`active`/`planned`) e
> `impl_function` (nome da `_check_*` em `lint.py` que implementa a regra).

## Quando usar

- Logo após gerar/editar qualquer fonte ADVPL/TLPP.
- Antes de marcar tarefa como "concluída" ou propor PR/commit.
- Quando usuário pede "revise este código" / "tem boa prática aqui?".
- Em conjunto com `[[advpl-refactoring]]` (refatorar) e `[[advpl-debugging]]` (investigar bug).

Rode `/plugadvpl:lint <arq>` para resultado de fato — esta skill é o **guia mental** das regras.

## As 24 regras detectadas — quick reference

### Single-file (18) — `lint.py`, regex/AST/lookup sobre conteúdo

| ID         | Sev      | Comportamento real implementado                                                |
|------------|----------|-------------------------------------------------------------------------------|
| `BP-001`   | critical | `RecLock` sem `MsUnlock` pareado no mesmo escopo de função                    |
| `BP-002`   | critical | `BEGIN TRANSACTION` sem `END TRANSACTION` pareado                              |
| `BP-003`   | error    | `MsExecAuto` sem checar `lMsErroAuto` nas linhas seguintes                     |
| `BP-004`   | warning  | `Pergunte("GRUPO", .F.)` sem uso subsequente de `MV_PAR*`                      |
| `BP-005`   | warning  | Função declarada com **mais de 6 parâmetros**                                  |
| `BP-006`   | error    | Mistura `RecLock` + `dbAppend()`/`DbRLock` raw na mesma função                  |
| `BP-008`   | critical | Shadowing de variável reservada framework (`cFilAnt`, `cEmpAnt`, `dDataBase`, `PARAMIXB`, `lMsErroAuto`, `INCLUI`, etc. — **20 reservadas** cobertas) — novo em v0.3.5, expandido em v0.3.10 |
| `SEC-001`  | critical | `RpcSetEnv` dentro de classe que herda de `WSRESTFUL`                          |
| `SEC-002`  | warning  | `User Function` sem prefixo cliente (2-3 letras) ou nome de PE oficial         |
| `SEC-003`  | warning  | PII/credenciais em log (`ConOut`/`FwLogMsg`/`MsgLog`) — variável `cCpf`/`cSenha`/`cToken`, campo `A1_CGC`/`A1_CPF`/`RA_CIC`, ou CPF/CNPJ literal — **novo em v0.3.19** |
| `SEC-004`  | warning  | Credenciais hardcoded — `RpcSetEnv("01","01","admin","totvs")`, `PREPARE ENVIRONMENT ... PASSWORD '...'`, `:SMTPAuth("user","pwd")`, `Encode64("user:pwd")` — **novo em v0.3.19** |
| `SEC-005`  | critical | Chamada de função TOTVS restrita (lookup `funcoes_restritas`, ~194 entries) — **novo em v0.3.7** |
| `PERF-001` | warning  | `SELECT *` em `BeginSql`/`TCQuery`                                             |
| `PERF-002` | error    | SQL contra tabela Protheus **sem `%notDel%`** (traz registros deletados)       |
| `PERF-003` | error    | SQL contra tabela Protheus **sem `%xfilial%`** (cross-filial data leak)        |
| `PERF-004` | warning  | `cVar += ...` ou `cVar := cVar + ...` em loop While/For (O(n²)) — **novo em v0.3.9** |
| `PERF-005` | warning  | `RecCount() > 0` ou `LastRec() > 0` (e variantes) pra checar existência — use `!Eof()` — novo em v0.3.6, expandido em v0.3.10 |
| `MOD-001`  | warning  | `ConOut(...)` em vez de `FwLogMsg(...)` (Code Analysis acusa)                  |
| `MOD-002`  | warning  | Declaração `Public` (polui escopo global)                                      |
| `MOD-004`  | info     | Chamada a `AxCadastro`/`Modelo2`/`Modelo3`/`MsNewGetDados` (legacy) em vez de MVC — novo em v0.3.8, expandido em v0.3.10 |

### Cross-file SX (11) — `lint --cross-file`, requer `ingest-sx`

Disponíveis após `/plugadvpl:ingest-sx <pasta-csv>`. Acionadas com `--cross-file`. Veja `[[advpl-dicionario-sx-validacoes]]`.

| ID        | Sev      | Comportamento                                                                  |
|-----------|----------|--------------------------------------------------------------------------------|
| `SX-001`  | warning  | `X3_VALID = "U_XYZVALID()"` mas a User Function não existe nos fontes          |
| `SX-002`  | error    | Gatilho SX7 `X7_CDOMIN` aponta pra campo que não existe em `campos` (SX3)      |
| `SX-003`  | warning  | Parâmetro SX6 (`MV_*`) declarado mas zero referências em fonte                 |
| `SX-004`  | warning  | Grupo SX1 sem `Pergunte("GRUPO")` em nenhum fonte                              |
| `SX-005`  | info     | Campo SX3 custom (`X3_PROPRI='U'`) sem referência em fonte/SX/SX7              |
| `SX-006`  | warning  | `X3_VALID` faz `BeginSql`/`TCQuery` (anti-pattern — query a cada validação)    |
| `SX-007`  | critical | `X3_VALID` chama função listada em `funcoes_restritas` TOTVS                   |
| `SX-008`  | warning  | Tabela `X2_MODO='C'` (compartilhada) usa `xFilial` em `X3_VALID`               |
| `SX-009`  | warning  | Campo obrigatório (`X3_OBRIGAT='X'`) com `X3_INIT` vazio/zero                  |
| `SX-010`  | error    | Gatilho `X7_TIPO='P'` (Pesquisar) sem `X7_SEEK='S'` válido                      |
| `SX-011`  | error    | `X3_F3` aponta pra alias SXB que não existe                                    |

## As 4 regras catalogadas mas não detectadas (v0.3.19)

Aparecem em `lookups/lint_rules.json` com `status="planned"`. Use como checklist mental.

| ID         | Sev      | Título do catálogo                                                            |
|------------|----------|-------------------------------------------------------------------------------|
| `BP-002b`  | warning  | Variável declarada como `Private`/`Public` em vez de `Local`                  |
| `BP-007`   | info     | Função sem header Protheus.doc                                                |
| `PERF-006` | info     | Query sem hint de índice ou ORDER BY não casando índice                       |
| `MOD-003`  | info     | Grupos de funções com prefixo comum candidatas a classe                       |

## Severidades — política de bloqueio

| Severidade | Significado                                       | Bloqueia merge?              |
|------------|---------------------------------------------------|------------------------------|
| `critical` | Bug grave / falha de segurança / cross-filial leak | **SIM** (corrigir antes)     |
| `error`    | Erro de compilação ou runtime provável            | **SIM**                      |
| `warning`  | Funciona, mas má prática                          | Corrigir; pode flagged em PR |
| `info`     | Estilo / sugestão                                 | Não bloqueia                 |

## Workflow

### Single-file

1. Termine de editar o fonte.
2. `/plugadvpl:lint <arquivo>` — roda as 13 regras single-file.
3. Filtre por severidade pra triagem rápida: `/plugadvpl:lint <arq> --severity critical,error`.
4. Pra cada `critical`/`error`: corrija **antes** de prosseguir.
5. Pra `warning`: corrija; justifique se não der (comentar no PR).
6. Pra `info`: trate como TODO de longo prazo.

### Cross-file SX

1. **Pré-requisito**: `/plugadvpl:ingest-sx <pasta-csv>` (popula tabelas SX no índice).
2. `/plugadvpl:lint --cross-file` — roda as 11 regras SX-001..SX-011 contra TODO o projeto.
3. Filtre por regra específica: `/plugadvpl:lint --cross-file --regra SX-005`.
4. SX-001 e SX-002 são tipicamente os primeiros que aparecem em base nova — começar por eles.

### Filtros úteis

```bash
plugadvpl lint <arq>                              # tudo do arquivo
plugadvpl lint <arq> --severity critical          # só críticos
plugadvpl lint <arq> --regra BP-001               # só uma regra
plugadvpl lint --cross-file                       # SX-001..SX-011 no projeto
plugadvpl lint --cross-file --regra SX-005        # uma regra cross-file
plugadvpl lint <arq> --format json                # output JSON pra parsear
plugadvpl lint <arq> --format md                  # output markdown (default em chat)
```

## Exemplos de fix (regras críticas/error)

### BP-001 — RecLock sem MsUnlock

```advpl
// ERRADO
RecLock("SA1", .F.)
SA1->A1_NOME := "novo"
// faltou MsUnlock — lock fica orfao ate session morrer

// CORRETO (simples)
RecLock("SA1", .F.)
SA1->A1_NOME := "novo"
SA1->(MsUnlock())

// MELHOR (em fluxo com erro possivel)
Begin Transaction
    RecLock("SA1", .F.)
    SA1->A1_NOME := "novo"
    SA1->(MsUnlock())
    // Se erro ocorrer aqui, rollback automatico + unlock
End Transaction
```

### BP-002 — BEGIN TRANSACTION sem END

```advpl
// ERRADO
Begin Transaction
    RecLock("SC5", .T.)
    SC5->C5_NUM := cNum
    SC5->(MsUnlock())
    // erro aqui = transacao fica aberta, processo trava recursos
// FALTOU End Transaction

// CORRETO + protecao Begin Sequence
Begin Sequence
    Begin Transaction
        RecLock("SC5", .T.)
        SC5->C5_NUM := cNum
        SC5->(MsUnlock())
    End Transaction
Recover Using oErr
    DisarmTransaction()  // forca rollback explicito
    ConOut("Falha: " + oErr:Description)
    Break oErr
End Sequence
```

### BP-003 — MsExecAuto sem checar erro

```advpl
// ERRADO
MsExecAuto({|x,y| MATA030(x,y)}, aCab, 3)
// se falhou, ninguem fica sabendo

// CORRETO
Private lMsErroAuto := .F.

MsExecAuto({|x,y| MATA030(x,y)}, aCab, 3)
If lMsErroAuto
    MostraErro()    // ou: aErros := GetAutoGRLog(); ... pra logar
    DisarmTransaction()
    Return .F.
EndIf
```

### SEC-001 — RpcSetEnv em REST

```advpl
// ERRADO
WSMETHOD GET listaClientes WSSERVICE zClientes
    RpcSetEnv("99", "01")    // bypassa controle de empresa/filial!
    // ... consulta
WSEND

// CORRETO
// 1. appserver.ini define PrepareIn pra cada grupo de empresa:
//    [HTTPREST]
//    PrepareIn=01
//    Security=1
// 2. Cliente passa empresa/filial no header TenantId
// 3. Method nao chama RpcSetEnv — recebe ambiente pronto
WSMETHOD GET listaClientes WSSERVICE zClientes
    // cFilAnt/cEmpAnt ja estao setados pelo framework
    Self:SetResponse('{"filial":"' + cFilAnt + '","ok":true}')
WSEND
```

### PERF-002 — SQL sem %notDel%

```advpl
// ERRADO — Protheus usa soft-delete em D_E_L_E_T_
BeginSql Alias "QRY"
    SELECT A1_COD, A1_NOME
      FROM %table:SA1% SA1
     WHERE SA1.A1_FILIAL = %xfilial:SA1%
       AND SA1.A1_GRUPO  = %exp:cGrupo%
EndSql
// traz registros LOGICAMENTE deletados — bug em totais/contagens

// CORRETO
BeginSql Alias "QRY"
    SELECT A1_COD, A1_NOME
      FROM %table:SA1% SA1
     WHERE SA1.A1_FILIAL = %xfilial:SA1%
       AND SA1.A1_GRUPO  = %exp:cGrupo%
       AND SA1.%notDel%      -- expande pra SA1.D_E_L_E_T_ = ' '
EndSql
```

### PERF-003 — SQL sem %xfilial%

```advpl
// ERRADO — vaza dados entre filiais
BeginSql Alias "QRY"
    SELECT C5_NUM, C5_CLIENTE
      FROM %table:SC5% SC5
     WHERE SC5.C5_EMISSAO >= %exp:dInicio%
       AND SC5.%notDel%
EndSql
// usuario da filial 01 ve pedidos da filial 02!

// CORRETO
BeginSql Alias "QRY"
    SELECT C5_NUM, C5_CLIENTE
      FROM %table:SC5% SC5
     WHERE SC5.C5_FILIAL  = %xfilial:SC5%   -- filtra filial atual
       AND SC5.C5_EMISSAO >= %exp:dInicio%
       AND SC5.%notDel%
EndSql
```

### PERF-004 — Concat de string em loop (O(n²) → O(n))

```advpl
// ERRADO — strings ADVPL imutáveis, cada iteração aloca + copia (O(n²))
// Caso real reportado por NG Informática: 1+ hora de execução
Local cBuf := ''
Local nI
For nI := 1 To 100000
    cBuf += Str(nI) + ';'   // 100k allocs, ~5GB chars copiados
Next nI
ConOut(cBuf)

// CORRETO opção 1: array + FwArrayJoin (R26+) ou Array2String (legacy) — O(n)
Local aBuf := {}
Local nI
For nI := 1 To 100000
    aAdd(aBuf, Str(nI))   // O(1) por iteração
Next nI
Local cBuf := FwArrayJoin(aBuf, ';')   // single join no final, O(n)

// CORRETO opção 2: file buffer (FCreate/FWrite) — pra strings muito grandes
Local nFp := FCreate('\system\buf.tmp')
For nI := 1 To 100000
    FWrite(nFp, Str(nI) + ';')
Next nI
FClose(nFp)
Local cBuf := MemoRead('\system\buf.tmp')
FErase('\system\buf.tmp')

// CORRETO opção 3: StringBuilder (NG Informática reporta ~240x faster)
// Ver github.com/nginformatica/string-builder-advpl
```

**Long form também detecta** (mesmo nome via backreference): `cAcc := cAcc + AllTrim(SA1->A1_NOME)` em loop.
**Não detecta** accumulator numérico: `nTotal += 1` (n-prefix indica numeric, não string).

### MOD-004 — AxCadastro/Modelo2/Modelo3/MsNewGetDados → MVC

```advpl
// LEGACY 1: AxCadastro (Modelo 1) — cadastro simples
User Function ZA1Cad()
    AxCadastro("ZA1", "Cadastro de Conhecimento", "AllwaysTrue", "AllwaysTrue")
Return

// MIGRADO: MVC com FWMBrowse + MenuDef + ModelDef + ViewDef
User Function ZA1Cad()
    Local oBrw := FWMBrowse():New()
    oBrw:SetAlias("ZA1")
    oBrw:SetDescription("Cadastro de Conhecimento")
    oBrw:Activate()
Return

Static Function MenuDef()
    Return FWMVCMenu("ZA1Cad")
End

Static Function ModelDef()
    Local oModel    := MPFormModel():New("ZA1MD")
    Local oStruZA1  := FWFormStruct(1, "ZA1")
    oModel:AddFields("ZA1MASTER", , oStruZA1)
    oModel:GetModel("ZA1MASTER"):SetPrimaryKey({"ZA1_FILIAL", "ZA1_COD"})
Return oModel

// (ViewDef análogo, omitido — veja [[advpl-mvc]])

// LEGACY 2: Modelo3 (cabeçalho + itens pai/filho)
User Function ZPedCad()
    Modelo3("Pedido", "ZP1", "ZP2", aCpoEnchoice, "AllwaysTrue", "AllwaysTrue", 3, 3, "")
Return

// LEGACY 3: MsNewGetDados (grid editavel standalone) — deprecated desde 12.1.17
User Function ZItens()
    Local oGrid := MsNewGetDados():New(0, 0, 200, 400, , , , , , , , , , , oDlg, aHeader, aCols)
Return

// MIGRADO: MVC com AddFields master + AddGrid detail + SetRelation
Static Function ModelDef()
    Local oModel    := MPFormModel():New("ZPEDMD")
    Local oStruZP1  := FWFormStruct(1, "ZP1")
    Local oStruZP2  := FWFormStruct(1, "ZP2")
    oModel:AddFields("ZP1MASTER", , oStruZP1)
    oModel:AddGrid("ZP2DETAIL", "ZP1MASTER", oStruZP2)
    oModel:SetRelation("ZP2DETAIL", { ;
        {"ZP2_FILIAL", "xFilial('ZP2')"}, ;
        {"ZP2_NUMPED", "ZP1->ZP1_NUMPED"} ;
    }, ZP2->(IndexKey(1)))
    oModel:GetModel("ZP2DETAIL"):SetUniqueLine({"ZP2_ITEM"})
Return oModel
```

Veja `[[advpl-refactoring]]` padrão 4 pra walkthrough completo + `[[advpl-mvc]]`/`[[advpl-mvc-avancado]]`.

### PERF-005 — RecCount()/LastRec() para checar existência

```advpl
// ERRADO — RecCount() (ou LastRec(), identico per TDN) forca full scan da tabela inteira
DbSelectArea("SA1")
DbGoTop()
If RecCount() > 0
    ConOut("Tem cliente")
EndIf

// ERRADO tambem — LastRec eh alias de RecCount, mesmo problema
If LastRec() > 0
    ConOut("Tem cliente")
EndIf

// CORRETO — !Eof() é O(1) após DbGoTop/DbSeek
DbSelectArea("SA1")
DbGoTop()
If !Eof()
    ConOut("Tem cliente")
EndIf

// CORRETO em alias-call
If !SA1->(Eof())
    ConOut("Tem cliente")
EndIf

// Em SQL embarcado, EXISTS é melhor que COUNT(*)
BeginSql Alias "QRY"
    SELECT 1 FROM %table:SA1% SA1
     WHERE SA1.A1_FILIAL = %xfilial:SA1%
       AND SA1.%notDel%
EndSql
If !QRY->(Eof())
    // tem pelo menos 1 cliente
EndIf
QRY->(DbCloseArea())
```

Padrões detectados (não confundir com limites de business como `RecCount() > 100`):
`RecCount() > 0`, `RecCount() >= 1`, `RecCount() != 0`, `RecCount() <> 0`, e variantes com alias-call (`SA1->(RecCount()) > 0`). Idem para `LastRec()` em qualquer dos formatos acima — TDN documenta `LastRec` como alias funcional de `RecCount`, então mesmo problema de full scan.

### BP-008 — Shadowing de variável reservada framework

```advpl
// ERRADO — shadow da reservada cFilAnt (Public que TOTVS preenche com filial atual)
User Function XYZBad()
    Local cFilAnt := "01"           // shadow! agora cFilAnt vale "01" dentro desta funcao
    DbSelectArea("SA1")
    DbSeek(xFilial("SA1") + cFilAnt)   // cFilAnt aqui é "01", nao a filial real
Return

// CORRETO — usar nome distinto
User Function XYZGood()
    Local cMinhaFilial := "01"      // sem colisao
    DbSelectArea("SA1")
    DbSeek(xFilial("SA1") + cMinhaFilial)
Return

// CORRETO — quando voce REALMENTE quer a filial atual, NAO declare cFilAnt local
User Function XYZGood2()
    DbSelectArea("SA1")
    DbSeek(xFilial("SA1") + cFilAnt)   // cFilAnt vem do framework (Public)
Return
```

Reservadas cobertas pela detecção (case-insensitive, **20 nomes**):
- **Sessao/empresa:** `cFilAnt`, `cEmpAnt`, `cUserName`, `cModulo`, `cTransac`, `nProgAnt`, `oMainWnd`, `__cInternet`, `__Language`, `nUsado`.
- **Data sistema (CRITICO — shadow quebra toda logica de competencia):** `dDataBase`.
- **Pontos de entrada / state runtime:** `PARAMIXB`, `aRotina`, `lMsErroAuto`, `lMsHelpAuto`, `INCLUI`, `ALTERA`.
- **Backup / introspecao:** `cFunBkp`, `cFunName`, `lAutoErrNoFile`.

Quando voce shadow `dDataBase`, qualquer `MV_DATABASE` do Protheus passa a usar a sua data local — saldos, competencias e movimentacoes saem todas erradas e a falha eh silenciosa. `INCLUI`/`ALTERA` shadow quebra detecao de modo de operacao em rotinas de gatilho. `lMsErroAuto` shadow esconde erros de `MsExecAuto`.

### SX-005 — campo custom não-referenciado

Detectado por `/plugadvpl:lint --cross-file --regra SX-005`:

```
arquivo=SX:SA1 funcao=A1_XGHOST severidade=warning
  sugestao_fix: Campo custom SA1.A1_XGHOST nao e referenciado em fonte algum
                nem em outras entradas SX. Provavel legado — considerar remocao.
```

Decisão: **remover** do SX3 + script de delete, OU implementar uso pendente.

## Checklist mental (ao gerar código)

**Antes de devolver código para o usuário, mentalmente percorra:**

### Critical (não passar com isso)

- [ ] Todo `RecLock` tem `MsUnlock` pareado, inclusive em branch de erro (`BP-001`).
- [ ] Todo `Begin Transaction` tem `End Transaction` pareado (`BP-002`).
- [ ] Nenhuma reservada (`cFilAnt`/`cEmpAnt`/`PARAMIXB`/`lMsErroAuto`/etc.) declarada como Local/Static/Private/Public (`BP-008`).
- [ ] Nenhum REST API tem `RpcSetEnv` (`SEC-001`) — use `PrepareIn`/`TenantId`.
- [ ] Nenhuma chamada a função TOTVS restrita (`StaticCall`/`PTInternal`/etc.) (`SEC-005`) — substitua por equivalente público.

### Error

- [ ] `MsExecAuto` sempre seguido de `If lMsErroAuto MostraErro()` (`BP-003`).
- [ ] Não há mistura `RecLock`+`dbAppend` raw (`BP-006`).
- [ ] Toda query tem `%xfilial%` em tabela filializada (`PERF-003`).
- [ ] Toda query tem `%notDel%` em tabela Protheus (`PERF-002`).

### Warning

- [ ] Função tem <= 6 parâmetros (`BP-005`).
- [ ] `Pergunte` é seguido por uso de `MV_PAR*` (`BP-004`).
- [ ] `User Function` tem prefixo cliente (`SEC-002`).
- [ ] Sem `SELECT *` em `BeginSql` (`PERF-001`).
- [ ] `ConOut` substituído por `FwLogMsg` em código novo (`MOD-001`).
- [ ] Sem declaração `Public` (`MOD-002`).

### Info / Checklist mental (não detectadas automaticamente)

- [ ] Notação húngara em todas as variáveis (`BP-006` catalog).
- [ ] Header Protheus.doc em todas as funções (`BP-007`).
- [ ] Sem shadowing de reservadas — `cFilAnt`/`cEmpAnt`/`PARAMIXB`/etc. (`BP-008`).
- [ ] Sem PII/senha em logs (`SEC-003`).
- [ ] Sem credenciais hardcoded (`SEC-004`).
- [ ] Sem função restrita TOTVS (`SEC-005`) — checar via `/plugadvpl:find function`.
- [ ] String concat em loop usa array + `FwArrayJoin` (`PERF-004`) — veja `[[advpl-refactoring]]`.
- [ ] Existência testada com `!Eof()`, não `RecCount() > 0` (`PERF-005`).
- [ ] Sem `AxCadastro`/`Modelo2`/`Modelo3` em código novo — usar MVC (`MOD-004`).

## Anti-padrões gerais

- **Aplicar fix automático cego sem entender a regra** → pode quebrar lógica.
- **Suprimir warning sem comentário justificativo** → conhecimento perdido em 6 meses.
- **Tratar `info` como ruído** → no agregado, é o que diferencia código mantível.
- **Não rodar lint antes de PR** → ciclo de review fica longo desnecessariamente.
- **Misturar transação básica `dbAppend` com Framework `RecLock`** → semântica de lock conflita, integridade quebra.
- **Salvar/restaurar `MV_PAR*` ao chamar `Pergunte` aninhado** — Private compartilhada, sobrescreve facilmente.

## Cross-references com outras skills

- `[[advpl-fundamentals]]` — convenções de variáveis/funções que estas regras assumem.
- `[[advpl-refactoring]]` — padrões pra resolver violações (DbSeek loop, AxCadastro→MVC, etc.).
- `[[advpl-debugging]]` — quando lint detecta algo, debugar a causa raiz.
- `[[advpl-dicionario-sx-validacoes]]` — detalhe das regras SX-001..SX-011 (expressões em X3_VALID/X7_REGRA/etc.).
- `[[advpl-embedded-sql]]` — macros `%xfilial%`, `%notDel%`, `%exp:%`, `%table:%`.
- `[[advpl-webservice]]` — padrão correto pra REST sem `RpcSetEnv`.
- `[[advpl-jobs-rpc]]` — onde `RpcSetEnv` É correto (Jobs, não REST).
- `[[plugadvpl-index-usage]]` — workflow completo plugadvpl.

## Comandos plugadvpl relacionados

- `/plugadvpl:lint <arq>` — roda as 13 regras single-file no arquivo.
- `/plugadvpl:lint` (sem arg) — roda no projeto inteiro.
- `/plugadvpl:lint --cross-file` — roda as 11 regras SX-001..SX-011 (requer `ingest-sx`).
- `/plugadvpl:lint <arq> --severity critical,error` — filtro por severidade.
- `/plugadvpl:lint <arq> --regra BP-001` — filtro por regra.
- `/plugadvpl:lint <arq> --format json` — output programático.
- `/plugadvpl:find function <restrita>` — descobre se função é proibida (SEC-005).
- Tabela `lint_findings` no índice armazena histórico — útil pra dashboard.

## Sources

- [Embedded SQL - Guia de Boas Práticas - TDN](https://tdn.totvs.com/pages/viewpage.action?pageId=27675608)
- [Embedded SQL - Frameworksp - TDN](https://tdn.totvs.com/display/framework/Embedded+SQL)
- [Controle de transações - TDN](https://tdn.totvs.com/pages/viewpage.action?pageId=271843449)
- [REST com segurança - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/8919254403735)
- [PrepareIn / TenantId - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/4410465974167)
- [Como distinguir erros ExecAuto - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360020737352)
- [ParamBox vs SX1 - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360026045651)
- [Boas Práticas em Transações ADVPL](https://www.scribd.com/document/390059884/Boas-Praticas-Transacoes-em-ADVPL)
- [ConOut → FwLogMsg - Terminal de Informação](https://terminaldeinformacao.com/2024/02/11/exibindo-mensagens-no-console-log-com-a-fwlogmsg-maratona-advpl-e-tl-228/)
- [NG Informática ADVPL Coding Standards (GitHub)](https://github.com/nginformatica/advpl-coding-standards)
- [Escopo de variáveis ADVPL - PH Cardoso](https://paulohcc.com/escopo-variaveis-advpl/)
