---
description: MVC avançado via PE — adicionar grids customizadas em telas MVC padrão (CNTA300/MATA460/etc), AddTrigger em cascata, validações preservando original (bLinePost), SetErrorMessage estruturado, FWSaveRows/FWRestRows para navegação segura, integração MATXFIS dentro de gatilhos MVC, controle de comportamento por status. Use ao customizar MVC além do CRUD básico.
---

# advpl-mvc-avancado — Customização MVC avançada via PE

A skill `advpl-mvc` cobre criar cadastros MVC do zero. **Esta skill cobre o cenário muito mais comum**: customizar um MVC padrão TOTVS via PE (`A300STRU`, `MA440STRU`, etc.) — adicionando grids filhas, gatilhos em cascata, validações preservando as originais, e controle de comportamento por status.

## Quando usar

- Usuário pede "adicionar grid em tela padrão", "customizar cadastro TOTVS", "MVC com PE", "PE STRU".
- Necessidade de injetar comportamento em rotina como `CNTA300`, `MATA460`, `MATA103`, `FINA040`.
- Validação cruzada entre grids pai/filha em cadastro padrão.
- Cálculo fiscal (MATXFIS) dentro de gatilho MVC.
- Bloqueio condicional de edição baseado em status do registro mestre.

## O PE bifurcado MODELDEF + VIEWDEF

PEs `*STRU` recebem três parâmetros via `PARAMIXB`:

```advpl
User Function A300STRU()
    Local aParam := PARAMIXB
    Local cTipo  := aParam[1]  // "MODELDEF" ou "VIEWDEF"
    Local cEspec := aParam[2]  // contexto: "C"=Compra, "V"=Venda, etc.
    Local xObj   := aParam[3]  // oModel OU oView (por referência)

    If cEspec == "V"
        If cTipo == "MODELDEF"
            xObj := AddMinhaGridModel(xObj)
        ElseIf cTipo == "VIEWDEF"
            xObj := AddMinhaGridView(xObj)
        EndIf
    EndIf

    aParam[3] := xObj  // OBRIGATÓRIO — devolve via referência
Return
```

**Sem o `aParam[3] := xObj` no fim, alterações se perdem.**

## Adicionando grid filha ao Model

```advpl
Static Function AddMinhaGridModel(oModel)
    Local oStruZZ3 := FWFormStruct(1, "ZZ3", /*bAvalCampo*/, .F.)

    // Configurar propriedades dos campos
    oStruZZ3:SetProperty("ZZ3_CODEVT", MODEL_FIELD_OBRIGAT, .T.)
    oStruZZ3:SetProperty("ZZ3_DESCRI", MODEL_FIELD_NOUPD,  .T.)

    // Adicionar gatilho na estrutura
    oStruZZ3:AddTrigger( ;
        "ZZ3_CODEVT", ;     // campo gatilho
        "ZZ3_DESCRI", ;     // campo destino
        {|| .T.}, ;         // condição
        {|oM| Posicione("SX5", 1, xFilial("SX5") + "Z1" + oM:GetValue("ZZ3_CODEVT"), "X5_DESCRI") } )

    oModel:AddGrid("ZZ3DETAIL", "CNAMASTER", oStruZZ3, /*bLinePre*/, /*bLinePost*/, /*bPre*/, /*bPost*/, /*bLoad*/)

    oModel:SetRelation("ZZ3DETAIL", { ;
        {"ZZ3_FILIAL", "xFilial('ZZ3')"}, ;
        {"ZZ3_CODCNT", "CNB->CNB_NUMERO"} ;
    }, ZZ3->(IndexKey(1)))

    oModel:GetModel("ZZ3DETAIL"):SetUniqueLine({"ZZ3_ITEM"})
    oModel:GetModel("ZZ3DETAIL"):SetOptional(.T.)
Return oModel
```

## Adicionando a grid na View

```advpl
Static Function AddMinhaGridView(oView)
    Local oStruZZ3 := FWFormStruct(2, "ZZ3", /*bAvalCampo*/, .F.)

    // Remover campos de chave da tela (vêm via SetRelation)
    oStruZZ3:RemoveField("ZZ3_FILIAL")
    oStruZZ3:RemoveField("ZZ3_CODCNT")

    // Adicionar a grid em box novo
    oView:AddGrid("VIEW_ZZ3", oStruZZ3, "ZZ3DETAIL")

    // Redimensionar grid existente para dar espaço
    oView:CreateHorizontalBox("CABEC",     30)
    oView:CreateHorizontalBox("GRIDCNC",   40)  // grid principal redimensionada
    oView:CreateHorizontalBox("GRIDZZ3",   30)  // nova grid

    oView:SetOwnerView("VIEW_CAB",   "CABEC")
    oView:SetOwnerView("VIEW_CNC",   "GRIDCNC")
    oView:SetOwnerView("VIEW_ZZ3",   "GRIDZZ3")
Return oView
```

## Gatilhos em cascata (pai → filha)

Quando campo da grid pai muda, atualiza colunas da filha:

```advpl
oStruCNC:AddTrigger( ;
    "CNC_VALOR", ;
    "CNC_VLRREL", ;
    {|| .T.}, ;
    {|oM| RecalcZZ3(oM) } )

Static Function RecalcZZ3(oModel)
    Local oZZ3 := oModel:GetModel("ZZ3DETAIL")
    Local nI

    FWSaveRows()  // salva contexto de grids
    For nI := 1 To oZZ3:Length()
        oZZ3:GoLine(nI)
        oZZ3:SetValue("ZZ3_VALOR", oModel:GetValue("CNCMASTER", "CNC_VALOR") * 0.1)
    Next nI
    FWRestRows()  // restaura contexto

Return oModel:GetValue("CNCMASTER", "CNC_VLRREL")
```

## Cálculo MATXFIS dentro de gatilho MVC

```advpl
{|oM| ;
    Local nValor ;
    MaFisIni(.F., .F., "MT", "M") ;
    MaFisRef("IT_VALMERC", "M", oM:GetValue("ZZ4_VALOR")) ;
    MaFisCalc("IT_VALMERC", "M") ;
    nValor := MaFisRet(, "IT_VALICM") ;
    MaFisEnd() ;
    Return nValor }
```

## Validações preservando a original (bLinePost)

```advpl
// Captura o bloco original
Local bOrigVld := oStructZZ3:bLinePost

oModel:GetModel("ZZ3DETAIL"):SetLinePost({|oM| ;
    Local lOk := .T. ;
    If bOrigVld != Nil ;
        lOk := Eval(bOrigVld, oM) ;
    EndIf ;
    If lOk ;
        lOk := U_XYZMinhaValid(oM) ;
    EndIf ;
    Return lOk })
```

## SetErrorMessage — feedback estruturado

```advpl
Static Function MyValid(oModel)
    If oModel:GetValue("ZZ3_VALOR") <= 0
        oModel:SetErrorMessage( ;
            "ZZ3DETAIL", ;          // id do sub-model
            "ZZ3_VALOR", ;          // campo
            "ZZ3DETAIL", ;          // id de exibição
            "ZZ3_VALOR", ;          // campo de exibição
            "VALOR_INVALIDO", ;     // código do erro
            "Valor deve ser maior que zero", ;  // mensagem PT
            "Confira o valor digitado") ;       // solução
        Return .F.
    EndIf
Return .T.
```

## Validação condicional via FwIsInCallStack

Para validar diferente conforme onde a rotina foi chamada (interativo × ExecAuto × scheduler):

```advpl
If FwIsInCallStack("U_XYZAJUS")
    // chamado de ajuste em lote — não valida
    Return .T.
EndIf
// validação normal
```

## Controle de comportamento por status

```advpl
Static Function SetStatusBlocks(oModel)
    Local cStatus := oModel:GetValue("CNBMASTER", "CNB_SITUAC")

    If cStatus $ "F|E"  // Finalizado ou Encerrado
        oModel:GetModel("ZZ3DETAIL"):SetOnlyView(.T.)   // view-only
        // ou:
        oModel:GetModel("ZZ3DETAIL"):SetOnlyQuery(.T.)  // modo consulta forçado
    EndIf
Return Nil
```

## Anti-padrões

- Esquecer `aParam[3] := xObj` no fim do PE → alterações perdidas.
- Sobrescrever validação original sem capturar antes (`bOrigVld`) → quebra comportamento padrão.
- Mexer em grid filha sem `FWSaveRows`/`FWRestRows` → corrompe row corrente.
- Hardcode de campo customer no PE sem checar `FieldPos` → quebra em outro cliente.
- Validar com `MsgInfo`/`Alert` em vez de `SetErrorMessage` → confunde MVC.
- Cálculo fiscal sem `MaFisEnd()` → contexto fiscal vaza para próximo registro.
- Renderizar grid via `MsNewGetDados` dentro do View MVC → MVC perde controle.

## Referência profunda

Para detalhes completos (~1k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Anatomia completa do PE `A300STRU` (caso real CNTA300 — contratos).
- Cadeia de gatilhos entre grids com diagrama de execução.
- Lista exaustiva de erros comuns ao adicionar grid (índice, relação, owner-view).
- Padrão de migração de customização "MsNewGetDados ad-hoc" → grid MVC nativa.
- Template completo para "adicionar grid em tela MVC padrão".

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <rotina>STRU` — localiza PEs de estrutura.
- `/plugadvpl:callers FWFormStruct` — uso de FWFormStruct no projeto.
- `/plugadvpl:tables <ZZ*>` — lista campos da grid customer.
- A tabela `mvc_hooks` cataloga todos os bLinePost/bPost/AddTrigger.
