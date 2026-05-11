---
description: Padrões MVC em ADVPL — MenuDef/ModelDef/ViewDef, aRotina, MODEL_OPERATION_*, hooks bCommit/bTudoOk/bLineOk/bPosVld/bPreVld, FWFormStruct1/2. Use ao trabalhar com cadastros MVC.
---

# advpl-mvc — Framework MVC do Protheus

A partir do release 11 da TOTVS, cadastros e processos no Protheus passaram a usar o framework **MVC** (FWMVC). Antes era `AxCadastro`/`Modelo2`/`Modelo3` — hoje deprecado (`MOD-004`).

Uma rotina MVC tem **3 funções estáticas obrigatórias** + um menu:

- `MenuDef()` → retorna `aRotina` (entradas de menu, ações disponíveis).
- `ModelDef()` → retorna `oModel` (estrutura de dados, validações, hooks).
- `ViewDef()` → retorna `oView` (interface gráfica, vinculação ao model).

## Quando usar

- Usuário pede para criar/editar cadastro Protheus (CRUD).
- Edit em arquivo cujo nome bate com pattern de cadastro novo (rotina nova) ou usuário menciona "MVC", "ModelDef", "ViewDef".
- Adicionar validação a cadastro existente — quase sempre via hook do model.
- Consultar `/plugadvpl:tables` retornou um cadastro MVC.

## Estrutura mínima

```advpl
#include "TOTVS.CH"

User Function XYZCAD()
    Local oBrowse := FWMBrowse():New()
    oBrowse:SetAlias("ZZZ")
    oBrowse:SetMenuDef("XYZCAD")
    oBrowse:SetDescription("Cadastro XYZ")
    oBrowse:Activate()
Return Nil

Static Function MenuDef()
    Local aRotina := {}
    aAdd(aRotina, {"Pesquisar",  "AxPesqui",          0, 1, 0, .F.})
    aAdd(aRotina, {"Visualizar", "VIEWDEF.XYZCAD",    0, 2, 0, .F.})
    aAdd(aRotina, {"Incluir",    "VIEWDEF.XYZCAD",    0, 3, 0, .F.})
    aAdd(aRotina, {"Alterar",    "VIEWDEF.XYZCAD",    0, 4, 0, .F.})
    aAdd(aRotina, {"Excluir",    "VIEWDEF.XYZCAD",    0, 5, 0, .F.})
Return aRotina

Static Function ModelDef()
    Local oModel    := MPFormModel():New("XYZCADMD", , {|oModel| MyTudoOk(oModel)}, {|oModel| MyCommit(oModel)})
    Local oStruZZZ  := FWFormStruct(1, "ZZZ")

    oModel:AddFields("ZZZMASTER", , oStruZZZ)
    oModel:GetModel("ZZZMASTER"):SetPrimaryKey({"ZZZ_FILIAL", "ZZZ_COD"})

    oModel:SetVldActivate({|oModel| MyPreVld(oModel)})
    oModel:GetModel("ZZZMASTER"):SetPosValidation({|oModel| MyPosVld(oModel)})

Return oModel

Static Function ViewDef()
    Local oModel  := FWLoadModel("XYZCAD")
    Local oView   := FWFormView():New()
    Local oStruZZZ := FWFormStruct(2, "ZZZ")

    oView:SetModel(oModel)
    oView:AddField("VIEW_ZZZ", oStruZZZ, "ZZZMASTER")
    oView:CreateHorizontalBox("PRINCIPAL", 100)
    oView:SetOwnerView("VIEW_ZZZ", "PRINCIPAL")

Return oView
```

## `aRotina` — formato de cada linha

```advpl
{Descricao, FuncaoAcionada, Reservado, OPERACAO, Acesso, Pula}
```

Campo **OPERACAO** (4ª posição):

| Valor | Operação      | Constante `MODEL_OPERATION_*` |
|-------|---------------|-------------------------------|
| 1     | Pesquisar     | —                             |
| 2     | Visualizar    | `MODEL_OPERATION_VIEW` (1)    |
| 3     | Incluir       | `MODEL_OPERATION_INSERT` (3)  |
| 4     | Alterar       | `MODEL_OPERATION_UPDATE` (4)  |
| 5     | Excluir       | `MODEL_OPERATION_DELETE` (5)  |
| 8     | Imprimir      | —                             |
| 9     | Copiar        | `MODEL_OPERATION_INSERT`      |

Nota: em código de hooks use as **constantes** (mais legível): `if oModel:GetOperation() == MODEL_OPERATION_INSERT`.

## `FWFormStruct(1, alias)` × `FWFormStruct(2, alias)`

- `FWFormStruct(1, "ZZZ")` → estrutura para **MODEL** (campos, validações, gatilhos).
- `FWFormStruct(2, "ZZZ")` → estrutura para **VIEW** (apresentação, ordem visual, agrupamentos).

A estrutura é lida do **SX3** (dicionário). Customizações ad-hoc (esconder campo, mudar default) usam métodos `:AddField()`, `:SetProperty()`, `:RemoveField()` na estrutura.

## Hooks — o coração da customização

Hooks são code blocks (`{|oModel| ...}`) executados em momentos específicos do ciclo de vida. Para customizar comportamento sem alterar fontes TOTVS, **adicione hooks via PE** (`<Rotina>MOD` ou similar) ou no próprio model.

| Hook                    | Quando executa                                | Onde plugar                                   |
|-------------------------|-----------------------------------------------|-----------------------------------------------|
| `SetVldActivate`        | Antes do model abrir                          | Validação prévia (ex: usuário tem acesso?)    |
| `bPreVld` / `SetPreValidation` | Antes de validar o sub-model           | Bloquear edição condicional                   |
| `bLineOk` / `SetLinePre/PostValidation` | Linha (grids) validada               | Validação por linha em grid                   |
| `bPosVld` / `SetPosValidation` | Depois de validar o sub-model           | Validação cross-campo do sub-model            |
| `bTudoOk`               | Validação geral do model inteiro              | Validação que cruza todos os sub-models       |
| `bCommit`               | Imediatamente antes do COMMIT no banco        | Atualizar tabelas auxiliares, log de auditoria|
| `OnAfterCommit`         | Depois do COMMIT bem sucedido                 | Notificações, e-mails, integrações externas   |

Exemplo de hook de commit:

```advpl
Static Function MyCommit(oModel)
    Local lOk := .T.
    Local cCod := oModel:GetValue("ZZZMASTER", "ZZZ_COD")

    Begin Sequence
        // Grava log de auditoria
        RecLock("ZZL", .T.)
        ZZL->ZZL_FILIAL := xFilial("ZZL")
        ZZL->ZZL_COD    := cCod
        ZZL->ZZL_DTHR   := DtoS(Date()) + Time()
        MsUnlock()
    Recover
        lOk := .F.
    End Sequence

Return lOk
```

## MVC + sub-modelos (cabeçalho/itens)

Cadastros com cabeçalho + grid de itens (ex: pedido de venda) usam **sub-modelos**:

```advpl
oModel:AddFields("ZZ1MASTER", , oStruZZ1)       // Cabeçalho
oModel:AddGrid("ZZ2DETAIL",   "ZZ1MASTER", oStruZZ2)  // Itens
oModel:SetRelation("ZZ2DETAIL", {{"ZZ2_FILIAL", "xFilial('ZZ2')"}, {"ZZ2_COD", "ZZ1_COD"}}, ZZ2->(IndexKey(1)))
oModel:GetModel("ZZ2DETAIL"):SetUniqueLine({"ZZ2_ITEM"})
```

## FWMVCRotAuto — execução headless

Para automatizar inclusão/alteração/exclusão sem UI (importação em lote, web service):

```advpl
Local aCab := {{"ZZZ_COD", "000001", Nil}, {"ZZZ_NOME", "Cliente X", Nil}}
Local aItens := {}  // se houver grid

FWMVCRotina("XYZCAD", aCab, aItens, MODEL_OPERATION_INSERT)
// Verifica erro via FWGetErrors()
```

## Anti-padrões

- Esquecer de retornar `oModel`/`oView`/`aRotina` da função → erro de inicialização.
- Hook lento (`bTudoOk` faz query pesada) → trava UX do usuário.
- `RecLock` dentro de `bCommit` sem `MsUnlock` → registro fica preso (lint `BP-001` crítico).
- Mutar `oModel` no `bCommit` (já é tarde) — use `bTudoOk` para mutar.
- Hook que faz validação cross-banco síncrono → mate transação se rede cair; envolva em `Begin Sequence`/`Recover` (lint `BP-005`).
- Usar `AxCadastro`, `Modelo2`, `Modelo3` em código novo → `MOD-004`.

## Referência rápida

| Função/método                          | Para que serve                            |
|----------------------------------------|-------------------------------------------|
| `MPFormModel():New(id, , bTudoOk, bCommit)` | Cria model raiz                      |
| `FWFormStruct(1, alias)`               | Estrutura para model                      |
| `FWFormStruct(2, alias)`               | Estrutura para view                       |
| `oModel:AddFields(id, parent, struct)` | Adiciona sub-model "form" (registro único)|
| `oModel:AddGrid(id, parent, struct)`   | Adiciona sub-model "grid" (1..N)          |
| `oModel:SetRelation(child, aRel, idx)` | Vincula filho ao pai via chaves           |
| `oModel:GetOperation()`                | Retorna `MODEL_OPERATION_*`               |
| `oModel:GetValue(submdl, campo)`       | Lê valor atual                            |
| `oModel:SetValue(submdl, campo, val)`  | Escreve valor                             |
| `oModel:LoadValue(submdl, campo, val)` | Escreve sem disparar gatilhos             |
| `FWLoadModel("XYZCAD")`                | Carrega model definido em outra rotina    |
| `FWMVCRotina(rot, aCab, aIt, op)`      | Executa rotina MVC headless               |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function ModelDef` — lista todas as `ModelDef` indexadas.
- `/plugadvpl:callers <rotina>` — descobre quem aciona o cadastro.
- `/plugadvpl:tables <T>` — vê qual MVC usa a tabela.
- A tabela `mvc_hooks` do índice cataloga todos os hooks declarados.

## Referência profunda

Para detalhes completos (~2.3k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Anatomia completa de `MPFormModel`/`MPFormFields`/`MPFormGrid` com todas as propriedades configuráveis.
- Tabela exaustiva de métodos de `oModel`/`oView` (LoadValue, SetUniqueLine, SetOptional, SetNoInsertLine, SetDescription).
- Catálogo de eventos do ciclo de vida MVC (Activate/Deactivate, Pre/PostValidation, LineActivate).
- Padrões para grids dependentes (cabeçalho/itens, multi-nível) com `SetRelation` e `SetUniqueLine`.
- Integração com FWMBrowse, MarkBrowse e MsDialog para casos onde a UI saí do `FWFormView` padrão.

## Exemplos práticos

Veja a pasta [`exemplos/`](exemplos/) ao lado deste SKILL.md para fontes reais TLPP de produção (MVC moderno via classes):

- `custom.mvc.customers.tlpp` — cadastro de monitor de integração de clientes (FWMBrowse + namespace TLPP).
- `custom.mvc.monitors.tlpp` — monitor genérico de processos de integração.
- `custom.mvc.quote.tlpp` — fluxo de cotação com cabeçalho + itens (sub-models).
- `custom.mvc.transferOrder.tlpp` — ordem de transferência com validações cruzadas.
- `custom.mvc.confirmationOfReceipt.tlpp` — confirmação de recebimento com hooks de commit.
