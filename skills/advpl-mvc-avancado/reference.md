# MVC – Customização Avançada via Ponto de Entrada

> Guia prático para adicionar grids, gatilhos, validações e controle de comportamento em telas MVC padrão do Protheus via Ponto de Entrada. Baseado em experiência real de customização do módulo de Contratos (CNTA300).

---

## Sumário

- [1. O Problema](#1-o-problema)
- [2. O PE A300STRU — Anatomia Completa](#2-o-pe-a300stru--anatomia-completa)
  - [2.1 Como o PE é chamado pelo MVC](#21-como-o-pe-é-chamado-pelo-mvc)
  - [2.2 Estrutura do PE bifurcado (MODELDEF + VIEWDEF)](#22-estrutura-do-pe-bifurcado-modeldef--viewdef)
- [3. Adicionando uma Grid Filha ao Model](#3-adicionando-uma-grid-filha-ao-model)
  - [3.1 Criar a estrutura via FWFormStruct](#31-criar-a-estrutura-via-fwformstruct)
  - [3.2 Configurar propriedades dos campos](#32-configurar-propriedades-dos-campos)
  - [3.3 Adicionar gatilhos na estrutura](#33-adicionar-gatilhos-na-estrutura)
  - [3.4 Registrar a grid no Model com AddGrid](#34-registrar-a-grid-no-model-com-addgrid)
  - [3.5 Definir o relacionamento com SetRelation](#35-definir-o-relacionamento-com-setrelation)
  - [3.6 Configurar propriedades da grid](#36-configurar-propriedades-da-grid)
- [4. Adicionando a Grid na View](#4-adicionando-a-grid-na-view)
  - [4.1 Criar estrutura visual](#41-criar-estrutura-visual)
  - [4.2 Remover campos de chave da tela](#42-remover-campos-de-chave-da-tela)
  - [4.3 Redimensionar grid existente](#43-redimensionar-grid-existente)
  - [4.4 Criar box e vincular a grid](#44-criar-box-e-vincular-a-grid)
- [5. Gatilhos em Cascata no MVC](#5-gatilhos-em-cascata-no-mvc)
  - [5.1 AddTrigger — sintaxe e comportamento](#51-addtrigger--sintaxe-e-comportamento)
  - [5.2 Cadeia de gatilhos entre grids (pai → filha)](#52-cadeia-de-gatilhos-entre-grids-pai--filha)
  - [5.3 Gatilho com MATXFIS dentro do MVC](#53-gatilho-com-matxfis-dentro-do-mvc)
- [6. Validações Avançadas](#6-validações-avançadas)
  - [6.1 Injetar validação preservando a original (bLinePost)](#61-injetar-validação-preservando-a-original-blinepost)
  - [6.2 SetErrorMessage — mensagens estruturadas](#62-seterrormessage--mensagens-estruturadas)
  - [6.3 Validação condicional com FwIsInCallStack](#63-validação-condicional-com-fwisincallstack)
- [7. Controle de Comportamento por Status](#7-controle-de-comportamento-por-status)
  - [7.1 Bloquear edição por situação do registro](#71-bloquear-edição-por-situação-do-registro)
  - [7.2 SetOnlyQuery — modo consulta forçado](#72-setonlyquery--modo-consulta-forçado)
- [8. Navegação Segura entre Grids](#8-navegação-segura-entre-grids)
  - [8.1 FWSaveRows e FWRestRows](#81-fwsaverows-e-fwrestrows)
  - [8.2 Padrão para percorrer grid filha](#82-padrão-para-percorrer-grid-filha)
- [9. Armadilhas e Lições Aprendidas](#9-armadilhas-e-lições-aprendidas)
- [10. Template Completo — Adicionar Grid em Tela MVC Padrão](#10-template-completo--adicionar-grid-em-tela-mvc-padrão)

---

## 1. O Problema

O MVC padrão do Protheus expõe o PE `A300STRU` (e similares em outros módulos) que permite customizar o Model e a View. Mas a documentação oficial cobre apenas cenários simples: adicionar campo, esconder campo, mudar validação.

**O cenário real é muito mais complexo:**
- Adicionar uma **grid filha** (tabela customizada) dentro de uma tela padrão
- Fazer essa grid se **relacionar** com a grid existente (pai → filha)
- Criar **gatilhos em cascata** entre campos da grid pai e da grid filha
- **Calcular impostos** (MATXFIS) dentro de gatilhos MVC
- **Preservar validações** existentes ao adicionar novas
- **Controlar edição** baseado no status do registro mestre
- **Redimensionar** a tela padrão para caber a nova grid

Este guia mostra como resolver cada um desses desafios com código real e funcional.

---

## 2. O PE A300STRU — Anatomia Completa

### 2.1 Como o PE é chamado pelo MVC

Quando o MVC carrega a rotina `CNTA300`, ele procura por um PE com o nome da rotina + sufixo `STRU`. O framework chama o PE em **dois momentos**: uma vez para o Model, outra para a View.

O PE recebe via `PARAMIXB`:

| Posição | Conteúdo | Descrição |
|---------|----------|-----------|
| `[1]` | `"MODELDEF"` ou `"VIEWDEF"` | Qual definição está sendo montada |
| `[2]` | Variável — ex: `"C"` ou `"V"` | Contexto da rotina (depende de cada PE) |
| `[3]` | Objeto `oModel` ou `oView` | **Passado por referência** — é o que você modifica |

> **Ponto crítico:** O `PARAMIXB[3]` é passado por referência. Você modifica o objeto e devolve via `aParam[3] := xObj`. Se não fizer isso, suas alterações se perdem.

### 2.2 Estrutura do PE bifurcado (MODELDEF + VIEWDEF)

```advpl
#Include "PROTHEUS.CH"
#Include "FWMVCDEF.CH"

User Function A300STRU()
    Local aParam := PARAMIXB
    Local cTipo  := aParam[1]  // "MODELDEF" ou "VIEWDEF"
    Local cEspec := aParam[2]  // Contexto da rotina
    Local xObj   := aParam[3]  // oModel ou oView

    If cEspec == "V"  // Só para Venda
        If cTipo == "MODELDEF"
            xObj := AddMinhaGridModel(xObj)
        ElseIf cTipo == "VIEWDEF"
            xObj := AddMinhaGridView(xObj)
        EndIf
    EndIf

    // OBRIGATÓRIO: devolver o objeto modificado
    aParam[3] := xObj
Return
```

> **Atenção:** Cada parte (Model e View) vai numa `Static Function` separada. Isso mantém o código organizado e evita que variáveis de Model vazem para View.

---

## 3. Adicionando uma Grid Filha ao Model

### 3.1 Criar a estrutura via FWFormStruct

`FWFormStruct(1, cTabela)` cria a estrutura do Model lendo o dicionário SX3. O parâmetro `1` indica Model (use `2` para View).

```advpl
Static Function AddMinhaGridModel(oModel)
    Local oStruZZ3 := FWFormStruct(1, 'ZZ3')  // Estrutura do Model
```

> A tabela `ZZ3` deve existir no dicionário (SX2/SX3) com todos os campos configurados. O `FWFormStruct` vai ler tipos, tamanhos, obrigatoriedades, validações do SX3.

### 3.2 Configurar propriedades dos campos

Após criar a estrutura, você pode alterar propriedades de campos em runtime:

```advpl
    // Tornar campos obrigatórios (mesmo que no SX3 não sejam)
    oStruZZ3:SetProperty('ZZ3_PERCEN', MODEL_FIELD_OBRIGAT, .T.)
    oStruZZ3:SetProperty('ZZ3_DTPREV', MODEL_FIELD_OBRIGAT, .T.)

    // Adicionar validação customizada via FwBuildFeature
    oStruZZ3:SetProperty('ZZ3_PERCEN', MODEL_FIELD_VALID, ;
        FwBuildFeature(STRUCT_FEATURE_VALID, "U_MinhaValidacao('ZZ3_PERCEN')"))
```

**Constantes úteis para SetProperty (include FWMVCDEF.CH):**

| Constante | O que controla |
|-----------|---------------|
| `MODEL_FIELD_OBRIGAT` | Campo obrigatório `.T.`/`.F.` |
| `MODEL_FIELD_VALID` | Expressão de validação |
| `MODEL_FIELD_INIT` | Valor inicial do campo |
| `MODEL_FIELD_WHEN` | Expressão de habilitação |

### 3.3 Adicionar gatilhos na estrutura

Gatilhos no MVC são adicionados via `AddTrigger` na estrutura, não no SX7:

```advpl
    oStruZZ3:AddTrigger(;
        'ZZ3_PERCEN',;         // Campo ORIGEM (quem dispara)
        'ZZ3_VLBASE',;         // Campo DESTINO (quem recebe o valor)
        {|| .T. },;            // bPre — condição para executar (.T. = sempre)
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;  // bSetValue
            MinhaFuncaoCalculo(oMdlGrid, cId, xValue, nLine, xCurValue) ;
        })
```

**Parâmetros do bSetValue:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `oMdlGrid` | Objeto | Model da grid onde o gatilho disparou |
| `cId` | Caracter | ID do campo origem |
| `xValue` | Qualquer | **Novo valor** digitado pelo usuário |
| `nLine` | Numérico | Linha atual da grid |
| `xCurValue` | Qualquer | Valor **anterior** do campo destino |

> **O retorno do bSetValue é gravado no campo destino.** Se a função retorna `nVlBase`, o campo `ZZ3_VLBASE` recebe esse valor.

### 3.4 Registrar a grid no Model com AddGrid

```advpl
    // Adiciona a grid ZZ3 como FILHA da grid CNB
    oModel:AddGrid('ZZ3DETAIL',;  // ID único do componente Model
                   'CNBDETAIL',;  // ID do PAI (grid existente)
                   oStruZZ3)      // Estrutura criada
```

> **O ID do pai** é o ID que a rotina padrão já usa. Para descobrir, leia o fonte da rotina (ex: `CNTA300`) ou use `oModel:GetModel('CNBDETAIL')` para testar se existe.

### 3.5 Definir o relacionamento com SetRelation

O `SetRelation` define quais campos da grid filha se vinculam aos campos do pai:

```advpl
    oModel:SetRelation('ZZ3DETAIL', {;
        {'ZZ3_FILIAL', 'xFilial("CNB")'},;    // Filial
        {'ZZ3_CONTRA', 'CN9_NUMERO'},;         // Contrato (vem do master)
        {'ZZ3_PLANIL', 'CNA_NUMERO'},;         // Planilha (vem do detalhe)
        {'ZZ3_ITEMCO', 'CNB_ITEM'},;           // Item (vem do pai direto)
        {'ZZ3_PRODUT', 'CNB_PRODUT'};          // Produto (vem do pai direto)
    }, ZZ3->(IndexKey(1)))
```

> **O segundo parâmetro** (após o array de campos) é a **chave de índice** da tabela filha. Ele determina a ordem de leitura dos registros.

**Dica:** Os campos à direita (`CN9_NUMERO`, `CNA_NUMERO`, etc.) podem ser de **qualquer nível acima** na hierarquia — o MVC navega automaticamente até o componente correto.

### 3.6 Configurar propriedades da grid

```advpl
    Local oModelZZ3 := oModel:GetModel('ZZ3DETAIL')

    oModelZZ3:SetDescription('Eventos Financeiros')
    oModelZZ3:SetOptional(.T.)            // Grid pode ficar vazia
    oModelZZ3:SetUniqueLine({'ZZ3_ITEM'}) // Campo único por linha
```

**Propriedades mais usadas:**

| Método | O que faz |
|--------|-----------|
| `SetOptional(.T.)` | Grid pode ficar sem linhas |
| `SetMaxLine(99)` | Máximo de linhas permitidas |
| `SetUniqueLine({campos})` | Campos que não podem repetir |
| `SetOnlyQuery(.T.)` | Modo somente consulta (bloqueia tudo) |
| `SetNoInsertLine(.T.)` | Impede inserir novas linhas |
| `SetNoUpdateLine(.T.)` | Impede editar linhas existentes |
| `SetNoDeleteLine(.T.)` | Impede deletar linhas |

---

## 4. Adicionando a Grid na View

### 4.1 Criar estrutura visual

```advpl
Static Function AddMinhaGridView(oView)
    Local oStruZZ3 := FWFormStruct(2, 'ZZ3')  // 2 = View
```

### 4.2 Remover campos de chave da tela

Campos de chave composta (filial, contrato, item) não devem aparecer na grid — o MVC preenche automaticamente via `SetRelation`:

```advpl
    oStruZZ3:RemoveField('ZZ3_FILIAL')
    oStruZZ3:RemoveField('ZZ3_CONTRA')
    oStruZZ3:RemoveField('ZZ3_PLANIL')
    oStruZZ3:RemoveField('ZZ3_ITEMCO')
    oStruZZ3:RemoveField('ZZ3_PRODUT')
```

### 4.3 Redimensionar grid existente

**Este é um dos passos mais difíceis.** A tela padrão já ocupa 100% do espaço. Para caber a nova grid, você precisa reduzir a grid existente.

```advpl
    // Hack: navegar nos boxes internos da View e mudar o percentual
    If AttIsMemberOf(oView, "AUSERBOXS")
        For nX := 1 To Len(oView:AUSERBOXS)
            If ValType(oView:AUSERBOXS[nX]) == "O"
                If AttIsMemberOf(oView:AUSERBOXS[nX], "CCLIENTID")
                    If oView:AUSERBOXS[nX]:CCLIENTID == "GRDITS"
                        oView:AUSERBOXS[nX]:NPERCETUAL := 55  // era 100%, agora 55%
                        Exit
                    EndIf
                EndIf
            EndIf
        Next
    EndIf
```

> **Atenção:** Este é um acesso direto à estrutura interna do objeto View. É a única forma conhecida de redimensionar um box existente via PE. Pode quebrar em atualizações — monitore após aplicar pacotes.

**Como descobrir o ID do box:** Use o debugger ou adicione `ConOut` temporário listando `oView:AUSERBOXS[nX]:CCLIENTID` para cada box.

### 4.4 Criar box e vincular a grid

```advpl
    // Registrar grid na View
    oView:AddGrid('VIEW_ZZ3', oStruZZ3, 'ZZ3DETAIL')  // view, struct, model

    // Criar um box horizontal dentro da aba existente
    oView:CreateHorizontalBox('BOX_ZZ3', 45,,,, "FLDPLAN", 'ABAITS')
    //                         ID       %          folder   aba

    // Vincular a grid ao box
    oView:SetOwnerView('VIEW_ZZ3', 'BOX_ZZ3')

    // Título e campo auto-incremento
    oView:EnableTitleView('VIEW_ZZ3', 'Eventos Financeiros do Item')
    oView:AddIncrementField('VIEW_ZZ3', 'ZZ3_ITEM')
Return oView
```

**Parâmetros do CreateHorizontalBox:**

| Posição | Parâmetro | Descrição |
|---------|-----------|-----------|
| 1 | cId | ID único do box |
| 2 | nPercentual | % do espaço disponível |
| 3 | cOwner | Box pai (opcional) |
| 4 | lUsePixel | Usar pixels em vez de % |
| 5 | — | Reservado |
| 6 | cFolder | ID do folder onde encaixar |
| 7 | cAba | ID da aba dentro do folder |

> Para descobrir os IDs do folder e aba da tela padrão, examine o fonte original da rotina ou use debugger.

---

## 5. Gatilhos em Cascata no MVC

### 5.1 AddTrigger — sintaxe e comportamento

No MVC, gatilhos são definidos na **estrutura** (`oStru`), não no SX7. O MVC dispara automaticamente quando o campo origem é alterado.

```advpl
oStru:AddTrigger(;
    cCampoOrigem,;    // Campo que quando alterado dispara o gatilho
    cCampoDestino,;   // Campo que vai receber o valor calculado
    bPre,;            // Bloco de código — condição (.T. = sempre)
    bSetValue)        // Bloco de código — cálculo do novo valor
```

> **O retorno do bSetValue vai direto no campo destino.** Você não precisa chamar `SetValue` manualmente.

### 5.2 Cadeia de gatilhos entre grids (pai → filha)

O cenário real: quando o campo da grid **pai** (CNB) muda, precisa recalcular toda a grid **filha** (ZZ3).

```
CNB_VLTOT (valor total do item)
    └──→ Gatilho na CNB recalcula toda a ZZ3
         Para cada linha ZZ3:
             ZZ3_PERCEN mantém ou recalcula
             ZZ3_VLBASE = CNB_VLTOT * ZZ3_PERCEN / 100
                 ├──→ ZZ3_VLFRET (frete rateado)
                 ├──→ ZZ3_VLIMP  (impostos via MATXFIS)
                 └──→ ZZ3_VLLIQ  (líquido)
```

**O gatilho na grid pai que propaga para a filha:**

```advpl
// Gatilho na estrutura da CNB (grid pai)
oStruCNB:AddTrigger(;
    'CNB_VLTOT',;        // Quando valor total do item mudar
    'CNB_VLTOT',;        // Campo destino = mesmo (truque: não altera nada na CNB)
    {|| .T. },;
    {|oMdlGrid, cId, xValue, nLine, xCurValue| ;
        U_xA3RecZZ3(oMdlGrid, cId, xValue, nLine, xCurValue), xValue})
```

> **Truque importante:** Quando campo origem = campo destino e o bSetValue retorna `xValue` (o próprio valor), o campo da CNB não muda. O efeito colateral (recalcular a ZZ3) acontece dentro da User Function chamada.

**A função que percorre a grid filha:**

```advpl
User Function xA3RecZZ3(oMdlGrid, cId, xValue, nLine, xCurValue)
    Local oModel      := oMdlGrid:GetModel()
    Local oModelZZ3   := oModel:GetModel('ZZ3DETAIL')
    Local aSaveLines  := FWSaveRows()  // OBRIGATÓRIO: salvar posição

    Local nNovoVlTotal := xValue  // Novo CNB_VLTOT

    // Percorrer todas as linhas da grid filha
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)

        If !oModelZZ3:IsDeleted()
            // Lógica de recálculo aqui
            oModelZZ3:SetValue('ZZ3_VLBASE', nNovoValor)
            // Os gatilhos de ZZ3_VLBASE disparam automaticamente
        EndIf
    Next

    FWRestRows(aSaveLines)  // OBRIGATÓRIO: restaurar posição
Return .T.
```

### 5.3 Gatilho com MATXFIS dentro do MVC

Quando precisa calcular impostos em tempo real dentro de um gatilho MVC:

```advpl
User Function xA3CalcImp(nVlBase)
    Local oModel      := FWModelActive()
    Local oModelCNA   := oModel:GetModel('CNADETAIL')
    Local oModelCNB   := oModel:GetModel('CNBDETAIL')

    Local aArea       := GetArea()
    Local aAreaSA1    := SA1->(GetArea())
    Local aAreaSB1    := SB1->(GetArea())
    Local aAreaSF4    := SF4->(GetArea())

    Local cCliente    := oModelCNA:GetValue('CNA_CLIENT')
    Local cLoja       := oModelCNA:GetValue('CNA_LOJACL')
    Local cProduto    := oModelCNB:GetValue('CNB_PRODUT')
    Local cTes        := oModelCNB:GetValue('CNB_TS')
    Local aRelImp     := MaFisRelImp("MT100", {"SF2","SD2"})
    Local lBkpFis     := .F.
    Local nVlImp      := 0

    // Validações iniciais — se dados incompletos, retorna 0
    If Empty(cCliente) .Or. Empty(cProduto) .Or. Empty(cTes)
        RestArea(aAreaSF4)
        RestArea(aAreaSB1)
        RestArea(aAreaSA1)
        RestArea(aArea)
        Return 0
    EndIf

    // Posicionar tabelas obrigatórias para MATXFIS
    DbSelectArea("SF4")
    SF4->(DbSetOrder(1))
    If !SF4->(DbSeek(xFilial("SF4") + cTes))
        // ... RestArea e return 0
    EndIf

    DbSelectArea("SB1")
    SB1->(DbSetOrder(1))
    If !SB1->(DbSeek(xFilial("SB1") + cProduto))
        // ... RestArea e return 0
    EndIf

    DbSelectArea("SA1")
    SA1->(DbSetOrder(1))
    SA1->(DbSeek(xFilial("SA1") + cCliente + cLoja))

    // ============================================
    // PASSO CRÍTICO: Salvar MATXFIS se já existir
    // ============================================
    If MaFisFound("NF")
        MaFisSave()      // Salva contexto fiscal existente
        MaFisEnd()       // Limpa arrays para novo uso
        lBkpFis := .T.
    EndIf

    // Inicializa MATXFIS
    MaFisIni(cCliente, cLoja, "C", "N", SA1->A1_TIPO, aRelImp,,,, "CNTA300")

    // Usa MaFisAdd (item único — OK neste contexto)
    nItem := MaFisAdd(cProduto, cTes, 1, nVlBase, 0, '', '', 0, ;
                      0, 0, 0, 0, nVlBase, 0, SB1->(Recno()), SF4->(Recno()))

    // Busca impostos calculados
    If nItem > 0
        nVlImp := MaFisRet(nItem, "IT_VALICM") + ;
                  MaFisRet(nItem, "IT_VALPS2") + ;
                  MaFisRet(nItem, "IT_VALCF2")
    EndIf

    // Finaliza MATXFIS
    MaFisEnd()

    // Restaura contexto fiscal anterior se existia
    If lBkpFis
        MaFisRestore()
    EndIf

    // Restaura áreas de trabalho
    RestArea(aAreaSF4)
    RestArea(aAreaSB1)
    RestArea(aAreaSA1)
    RestArea(aArea)
Return nVlImp
```

**Pontos críticos desta integração:**

| Passo | Por que é obrigatório |
|-------|----------------------|
| `GetArea()` de SA1, SB1, SF4 | MATXFIS posiciona essas tabelas internamente |
| `MaFisFound("NF")` + `MaFisSave()` | Pode haver contexto fiscal ativo na rotina pai |
| `MaFisEnd()` antes de `MaFisIni()` | MATXFIS só trabalha com 1 documento por vez |
| `MaFisRestore()` ao final | Restaura o contexto fiscal que a rotina pai estava usando |
| `MaFisAdd` (e não `MaFisIniLoad`) | Para item único, `MaFisAdd` é adequado e mais simples |

---

## 6. Validações Avançadas

### 6.1 Injetar validação preservando a original (bLinePost)

A rotina padrão pode já ter uma validação no `bLinePost`. Se você simplesmente sobrescrever, perde a validação original.

**Padrão correto — preservar + adicionar:**

```advpl
    // Captura validação existente (se houver)
    Local bLinePostOld := oModelCNB:bLinePost

    // Adiciona nova validação mantendo a antiga
    oModelCNB:bLinePost := {|oMdlCNB| ;
        IIf(ValType(bLinePostOld) == "B", Eval(bLinePostOld, oMdlCNB), .T.) .And. ;
        MinhaValidacao(oMdlCNB) ;
    }
```

> **O `IIf(ValType(...) == "B", ...)` é fundamental.** Se não existir validação anterior, o bloco retorna `.T.` e só roda a sua. Se existir, roda ambas com `.And.`.

### 6.2 SetErrorMessage — mensagens estruturadas

No MVC, **não use MsgStop ou Help** para validações de Model. Use `SetErrorMessage`:

```advpl
oModel:SetErrorMessage(;
    "CNBDETAIL",;    // cModelID — componente que originou o erro
    "CNB_ITEM",;     // cFieldID — campo relacionado
    "CNBDETAIL",;    // cModelErrID — componente onde mostrar o erro
    "CNB_ITEM",;     // cFieldErrID — campo onde mostrar o erro
    "MEU_ERRO_01",;  // cError — código único do erro
    "Soma dos percentuais deve ser 100%.",;  // cErrorMsg — mensagem principal
    "Soma atual: " + cValToChar(nPercTotal) + "%" ;  // cSolution — sugestão
)
lRet := .F.
```

### 6.3 Validação condicional com FwIsInCallStack

Quando um campo é alterado por gatilho, a validação do `X3_VALID` ou `MODEL_FIELD_VALID` dispara. Mas às vezes a validação deve ser diferente se veio de gatilho vs edição manual:

```advpl
User Function Z3VldEdit(cCampo)
    Local lGatilho := .F.

    // Verifica se a chamada veio de um gatilho (recálculo automático)
    lGatilho := FwIsInCallStack('xA3RecZZ3') .Or. ;
                FwIsInCallStack('U_XA3RECZZ3')

    // Se veio de gatilho, sempre permite
    If lGatilho
        Return .T.
    EndIf

    // Se veio do usuário, aplica as regras de validação
    // ... validações de status, data, etc.
Return lValid
```

> `FwIsInCallStack(cFuncao)` verifica se uma função específica está na pilha de chamadas. Útil para distinguir contexto automático vs manual.

---

## 7. Controle de Comportamento por Status

### 7.1 Bloquear edição por situação do registro

```advpl
    Local nOperation := oModel:GetOperation()
    Local cSituacao  := ""

    // Só verifica status em alteração/visualização (não em inclusão)
    If !(nOperation == 1) .And. FwIsInCallStack("CN300InVEN")
        cSituacao := AllTrim(CN9->CN9_SITUAC)

        If !(cSituacao $ "02|09")  // Não é Elaboração nem Revisão
            oModelZZ3:SetNoInsertLine(.T.)   // Bloqueia incluir
            oModelZZ3:SetNoUpdateLine(.T.)   // Bloqueia alterar
            oModelZZ3:SetNoDeleteLine(.T.)   // Bloqueia deletar
        EndIf
    Endif
```

### 7.2 SetOnlyQuery — modo consulta forçado

Para cenários como revisão de contrato, onde a grid deve mostrar dados mas não permitir alteração:

```advpl
    If !Empty(A300GTpRev())
        // Em processo de revisão: ZZ3 vira somente consulta
        // Isso impede que o MVC duplique os registros
        oModelZZ3:SetOnlyQuery(.T.)
    EndIf
```

---

## 8. Navegação Segura entre Grids

### 8.1 FWSaveRows e FWRestRows

**Regra de ouro:** Sempre que navegar entre linhas de uma grid dentro de uma função (gatilho, validação, etc.), salve e restaure a posição.

```advpl
Local aSaveLines := FWSaveRows()   // Salva posição de TODAS as grids

// ... navegar, ler, alterar valores ...

FWRestRows(aSaveLines)             // Restaura posição original
```

> Se não fizer isso, ao retornar da sua função a grid pode estar posicionada na linha errada — causando bugs invisíveis.

### 8.2 Padrão para percorrer grid filha

```advpl
Local aSaveLines := FWSaveRows()

For nX := 1 To oModelZZ3:Length()
    oModelZZ3:GoLine(nX)

    If !oModelZZ3:IsDeleted()
        // Ler valores
        nValor := oModelZZ3:GetValue('ZZ3_VLBASE')

        // Alterar valores
        oModelZZ3:SetValue('ZZ3_PERCEN', nNovoPerc)
    EndIf
Next

FWRestRows(aSaveLines)

// Se precisar atualizar a tela
Local oView := FWViewActive()
If oView != NIL
    oView:Refresh('VIEW_ZZ3')
EndIf
```

---

## 9. Armadilhas e Lições Aprendidas

### Erros que aconteceram na prática

| Armadilha | O que acontece | Solução |
|-----------|---------------|---------|
| Esquecer `aParam[3] := xObj` no PE | Todas as alterações se perdem — tela não muda | Sempre devolver o objeto no final |
| Não usar `FWSaveRows/FWRestRows` | Grid fica na linha errada — valores vão para linha errada | Sempre salvar/restaurar em funções que navegam grid |
| Sobrescrever `bLinePost` sem preservar | Perde validação padrão da TOTVS — erros de gravação | Usar padrão de `IIf(ValType(bOld)=="B", Eval(...), .T.)` |
| Chamar MATXFIS sem salvar/restaurar | Contexto fiscal da rotina pai é destruído | Sempre `MaFisSave` + `MaFisEnd` antes, `MaFisRestore` depois |
| Usar `MsgStop` dentro de validação de Model | Trava a tela, conflita com o framework MVC | Usar `oModel:SetErrorMessage()` |
| AddGrid com ID igual ao de outro componente | Erro silencioso — grid não aparece | IDs devem ser únicos em todo o Model |
| CreateHorizontalBox sem folder/aba corretos | Box aparece fora da tela ou em lugar errado | Depure IDs do folder/aba com debugger |
| SetRelation com campos fora de ordem | Registros errados aparecem na grid filha | Ordem dos campos deve bater com o índice |
| Grid filha vazia retornando erro | Validação obrigatória impede salvar | Use `SetOptional(.T.)` se a grid pode ficar vazia |
| `FWViewActive()` retornando NIL | Crash ao tentar `oView:Refresh()` | Sempre validar `oView != NIL` antes de chamar Refresh |

### Performance

| Problema | Impacto | Solução |
|----------|---------|---------|
| MATXFIS em gatilho de grid com muitas linhas | Lento — abre/fecha MATXFIS por linha | Cachear resultado por produto+TES |
| `SetValue` disparando gatilhos em cascata | Cada SetValue pode disparar N gatilhos | Minimizar SetValues dentro de laços |
| `oView:Refresh` dentro de laço | Redesenha a tela a cada iteração | Chamar Refresh apenas 1 vez, fora do laço |

---

## 10. Template Completo — Adicionar Grid em Tela MVC Padrão

Use este template como ponto de partida para qualquer customização similar:

```advpl
#Include "PROTHEUS.CH"
#Include "FWMVCDEF.CH"

//-------------------------------------------------------------------
// PONTO DE ENTRADA — bifurca para Model e View
//-------------------------------------------------------------------
User Function XYZSTRU()
    Local aParam := PARAMIXB
    Local cTipo  := aParam[1]  // "MODELDEF" ou "VIEWDEF"
    Local xObj   := aParam[3]  // oModel ou oView

    If cTipo == "MODELDEF"
        xObj := MeuModel(xObj)
    ElseIf cTipo == "VIEWDEF"
        xObj := MinhaView(xObj)
    EndIf

    aParam[3] := xObj  // DEVOLVER OBJETO MODIFICADO
Return

//-------------------------------------------------------------------
// MODEL — Adiciona grid ZZx como filha de GRID_PAI
//-------------------------------------------------------------------
Static Function MeuModel(oModel)
    Local oStruZZx  := FWFormStruct(1, 'ZZx')
    Local oModelPai := oModel:GetModel('GRID_PAI')
    Local oStruPai  := oModelPai:GetStruct()
    Local bOldValid := oModelPai:bLinePost

    // 1. Propriedades dos campos
    oStruZZx:SetProperty('ZZx_CAMPO', MODEL_FIELD_OBRIGAT, .T.)
    oStruZZx:SetProperty('ZZx_CAMPO', MODEL_FIELD_VALID, ;
        FwBuildFeature(STRUCT_FEATURE_VALID, "U_MeuValid()"))

    // 2. Gatilhos na grid filha
    oStruZZx:AddTrigger('ZZx_ORIGEM', 'ZZx_DESTINO', ;
        {|| .T. }, ;
        {|oMdl, cId, xVal, nLin, xCur| MeuCalculo(oMdl, xVal)})

    // 3. Gatilhos na grid pai (propagar para filha)
    oStruPai:AddTrigger('PAI_CAMPO', 'PAI_CAMPO', ;
        {|| .T. }, ;
        {|oMdl, cId, xVal, nLin, xCur| U_RecalcFilha(oMdl, xVal), xVal})

    // 4. Adicionar grid
    oModel:AddGrid('ZZxDETAIL', 'GRID_PAI', oStruZZx)

    // 5. Relacionamento
    oModel:SetRelation('ZZxDETAIL', {;
        {'ZZx_FILIAL', 'xFilial("PAI")'},;
        {'ZZx_CHAVE1', 'PAI_CHAVE1'},;
        {'ZZx_CHAVE2', 'PAI_CHAVE2'};
    }, ZZx->(IndexKey(1)))

    // 6. Propriedades da grid
    Local oModelZZx := oModel:GetModel('ZZxDETAIL')
    oModelZZx:SetDescription('Minha Grid')
    oModelZZx:SetOptional(.T.)
    oModelZZx:SetUniqueLine({'ZZx_ITEM'})

    // 7. Preservar validação existente + adicionar nova
    oModelPai:bLinePost := {|oMdl| ;
        IIf(ValType(bOldValid) == "B", Eval(bOldValid, oMdl), .T.) .And. ;
        MinhaValidacaoExtra(oMdl) ;
    }

Return oModel

//-------------------------------------------------------------------
// VIEW — Adiciona grid ZZx na interface
//-------------------------------------------------------------------
Static Function MinhaView(oView)
    Local oStruZZx := FWFormStruct(2, 'ZZx')

    // 1. Remover campos de chave
    oStruZZx:RemoveField('ZZx_FILIAL')
    oStruZZx:RemoveField('ZZx_CHAVE1')
    oStruZZx:RemoveField('ZZx_CHAVE2')

    // 2. Redimensionar grid existente (se necessário)
    If AttIsMemberOf(oView, "AUSERBOXS")
        For nX := 1 To Len(oView:AUSERBOXS)
            If ValType(oView:AUSERBOXS[nX]) == "O"
                If AttIsMemberOf(oView:AUSERBOXS[nX], "CCLIENTID")
                    If oView:AUSERBOXS[nX]:CCLIENTID == "ID_GRID_EXISTENTE"
                        oView:AUSERBOXS[nX]:NPERCETUAL := 55
                        Exit
                    EndIf
                EndIf
            EndIf
        Next
    EndIf

    // 3. Registrar grid
    oView:AddGrid('VIEW_ZZx', oStruZZx, 'ZZxDETAIL')

    // 4. Criar box e vincular
    oView:CreateHorizontalBox('BOX_ZZx', 45,,,, "FOLDER_ID", 'ABA_ID')
    oView:SetOwnerView('VIEW_ZZx', 'BOX_ZZx')

    // 5. Propriedades visuais
    oView:EnableTitleView('VIEW_ZZx', 'Minha Grid')
    oView:AddIncrementField('VIEW_ZZx', 'ZZx_ITEM')

Return oView
```

---

## Referência Rápida

### Fonte de exemplo completo

O arquivo `Exemplos/A300STRU.prw` implementa todos os conceitos deste guia na prática:
- Grid filha ZZ3 (Eventos Financeiros) dentro do contrato de venda CNTA300
- 4 gatilhos em cascata na ZZ3 + 3 gatilhos na CNB propagando para ZZ3
- Cálculo de impostos via MATXFIS dentro de gatilho
- Validação de soma de percentuais (= 100%) e evento obrigatório para NF
- Controle de edição por status do contrato e por evento já pago
- Proteção contra duplicação em revisão de contrato

---

## 11. Padrão: MVC Completo com TLPP e Namespaces

Os exemplos da pasta `Exemplos/` mostram um padrão real de **monitores de integração** escritos em TLPP com MVC do zero (não via PE em tela padrão). Todos usam a mesma tabela de fila (`ZZ0`) com tabelas de detalhe específicas por entidade.

### 11.1 Arquitetura dos Monitores

Todos os monitores seguem a mesma estrutura:

```
ZZ0 (Fila de Integração — Master)
  ├── ZZ3 (Clientes — SA1)
  ├── ZZQ → ZZR → ZZS (Pedidos/Cotações — SLQ: cabeçalho → itens → pagamentos)
  ├── ZZV → ZZX (Confirmação de Recebimento)
  └── ZZT → ZZU (Ordem de Transferência)
```

Cada monitor filtra `ZZ0` por entidade (`ZZ0_ENTIDA`) e mostra apenas os registros relevantes.

### 11.2 Estrutura padrão de um Monitor TLPP

```tlpp
#include "totvs.ch"
#include "fwmvcdef.ch"
#include "tlpp-core.th"
#include "tlpp-rest.th"

static cTitulo := "Monitor de Integração - Minha Entidade"

namespace custom.mvc.minhaEntidade

//-------------------------------------------------------------------
// BROWSE — tela principal com filtro e legendas
//-------------------------------------------------------------------
User Function meuMonitor()
    local aArea   := GetArea()
    local oBrowse := nil

    oBrowse := FWMBrowse():New()
    oBrowse:SetAlias("ZZ0")
    oBrowse:SetDescription(cTitulo)
    oBrowse:SetFilterDefault("ZZ0_ENTIDA == 'XXX'")  // Filtra por entidade

    oBrowse:addLegend("ZZ0_STATUS == 'P'", "YELLOW", "Aguardando processamento")
    oBrowse:addLegend("ZZ0_STATUS == 'R'", "BLUE",   "Aguardando Reprocessamento")
    oBrowse:addLegend("ZZ0_STATUS == 'I'", "GREEN",  "Processado")
    oBrowse:addLegend("ZZ0_STATUS == 'E'", "RED",    "Erro de processamento")

    oBrowse:Activate()
    RestArea(aArea)
Return nil
```

**Pontos chave:**
- `namespace` organiza o fonte — evita conflito de nomes entre monitores
- `static` para variáveis compartilhadas dentro do namespace
- `FWMBrowse` com `SetFilterDefault` filtra a mesma tabela ZZ0 para cada entidade
- Legendas por status padronizadas (P/R/I/E)

### 11.3 MenuDef com namespace

No TLPP, as actions do menu referenciam funções pelo **namespace completo**:

```tlpp
User Function MenuDef() as array
    local aRotina := {} as array

    // Visualizar usa ViewDef — referência pelo namespace completo
    ADD OPTION aRotina TITLE 'Visualizar'  ;
        ACTION 'ViewDef.custom.mvc.minhaEntidade.meuMonitor' ;
        OPERATION MODEL_OPERATION_VIEW ACCESS 0

    // Ações customizadas — funções do mesmo namespace
    ADD OPTION aRotina TITLE 'Reprocessar' ;
        ACTION 'custom.mvc.minhaEntidade.u_reprocessar()' ;
        OPERATION 6 ACCESS 0

Return aRotina
```

> **Padrão de referência:** `ViewDef.namespace.funcao` para visualizar, `namespace.u_funcao()` para ações.

### 11.4 ModelDef — Master + Múltiplas Grids

Exemplo com 3 níveis de hierarquia (Pedido → Itens → Pagamentos):

```tlpp
User Function ModelDef()
    Local oStruZZ0 := FWFormStruct(1, 'ZZ0')  // Fila
    Local oStruZZQ := FWFormStruct(1, 'ZZQ')  // Cabeçalho do Pedido
    Local oStruZZR := FWFormStruct(1, 'ZZR')  // Itens do Pedido
    Local oStruZZS := FWFormStruct(1, 'ZZS')  // Pagamentos
    Local oModel

    // Cria o Model
    oModel := MPFormModel():New('QUOTEMOD')

    // Master (campos)
    oModel:AddFields('ZZ0MASTER', /*cOwner*/, oStruZZ0)

    // Grid nível 1: filha do master
    oModel:AddGrid('ZZQDETAIL', 'ZZ0MASTER', oStruZZQ)

    // Grid nível 2: filha da grid nível 1
    oModel:AddGrid('ZZRDETAIL', 'ZZQDETAIL', oStruZZR)

    // Grid nível 3: filha da grid nível 2
    oModel:AddGrid('ZZSDETAIL', 'ZZRDETAIL', oStruZZS)

    oModel:SetPrimaryKey({})

    // Relacionamentos
    oModel:SetRelation('ZZQDETAIL', ;
        {{'ZZQ_FILIAL', 'FWxFilial("ZZQ")'}, {'ZZQ_ID', 'ZZ0_ID'}}, ;
        ZZQ->(IndexKey(1)))

    oModel:SetRelation('ZZRDETAIL', ;
        {{'ZZR_FILIAL', 'FWxFilial("ZZR")'}, {'ZZR_ID', 'ZZ0_ID'}}, ;
        ZZR->(IndexKey(1)))

    oModel:SetRelation('ZZSDETAIL', ;
        {{'ZZS_FILIAL', 'FWxFilial("ZZS")'}, {'ZZS_ID', 'ZZ0_ID'}}, ;
        ZZS->(IndexKey(1)))

    // Descrições
    oModel:SetDescription('Monitor de Integração de Pedido')
    oModel:GetModel('ZZQDETAIL'):SetDescription('Cabeçalho do Pedido')
    oModel:GetModel('ZZRDETAIL'):SetDescription('Itens do Pedido')
    oModel:GetModel('ZZSDETAIL'):SetDescription('Dados de Pagamento')

Return oModel
```

### 11.5 ViewDef — Distribuição de espaço entre grids

```tlpp
User Function ViewDef()
    Local oView := FwFormView():New()
    Local oStruZZ0 := FwFormStruct(2, "ZZ0")
    Local oStruZZQ := FwFormStruct(2, "ZZQ")
    Local oStruZZR := FwFormStruct(2, "ZZR")
    Local oStruZZS := FwFormStruct(2, "ZZS")

    // Carrega o Model pelo namespace completo
    Local oModel := FwLoadModel("custom.mvc.quote.quoteMonitor")

    oView:SetModel(oModel)

    // Registra componentes visuais
    oView:AddField("VIEW_ZZ0", oStruZZ0, "ZZ0MASTER")
    oView:AddGrid("VIEW_ZZQ", oStruZZQ, "ZZQDETAIL")
    oView:AddGrid("VIEW_ZZR", oStruZZR, "ZZRDETAIL")
    oView:AddGrid("VIEW_ZZS", oStruZZS, "ZZSDETAIL")

    // Distribui espaço vertical (soma = 100%)
    oView:CreateHorizontalBox("PARTE1", 20)  // Master
    oView:CreateHorizontalBox("PARTE2", 20)  // Cabeçalho
    oView:CreateHorizontalBox("PARTE3", 40)  // Itens (maior)
    oView:CreateHorizontalBox("PARTE4", 20)  // Pagamentos

    // Vincula cada componente ao seu box
    oView:SetOwnerView("VIEW_ZZ0", "PARTE1")
    oView:SetOwnerView("VIEW_ZZQ", "PARTE2")
    oView:SetOwnerView("VIEW_ZZR", "PARTE3")
    oView:SetOwnerView("VIEW_ZZS", "PARTE4")

    // Títulos
    oView:EnableTitleView("VIEW_ZZ0")
    oView:EnableTitleView("VIEW_ZZQ", "Cabeçalho do Pedido", 0)
    oView:EnableTitleView("VIEW_ZZR", "Itens do Pedido", 0)
    oView:EnableTitleView("VIEW_ZZS", "Dados de Pagamento", 0)

Return oView
```

### 11.6 Ações: Reprocessamento e Reenfileiramento

**Reprocessamento simples** — muda status e dispara job:

```tlpp
User Function reprocessar()
    If ZZ0->ZZ0_STATUS <> "E"
        fwAlertError("Status não permite reprocessamento", "Não permitido")
    Else
        If recLock("ZZ0", .F.)
            ZZ0->ZZ0_STATUS := "R"
            ZZ0->(msUnlock())
        EndIf

        If ZZ0->ZZ0_STATUS == "R"
            startJob("u_reprocessQuote", getEnvServer(), .F., ;
                     "01", ZZ0->ZZ0_FILIAL, ZZ0->ZZ0_ID)
            fwAlertSuccess("Reprocessamento acionado.", "Reprocessando")
        EndIf
    EndIf
Return
```

**Reenfileiramento em massa** — usa `FWExecStatement` para consulta eficiente:

```tlpp
User Function reenfileirar()
    Local aAreaX    := fwGetArea()
    Local cQueryZZ0 := ""
    Local cAliasZZ0 := ""
    Local oStatement := nil
    Local lContinua  := .F.

    // Conta registros com erro
    cQueryZZ0 := "SELECT COUNT(*) QTDEERRO "
    cQueryZZ0 += "FROM " + retSQLName("ZZ0") + " ZZ0 "
    cQueryZZ0 += "WHERE ZZ0.ZZ0_FILIAL <> ' ' "
    cQueryZZ0 += "  AND ZZ0.D_E_L_E_T_ = ' ' "
    cQueryZZ0 += "  AND ZZ0.ZZ0_ENTIDA = 'SLQ' "
    cQueryZZ0 += "  AND ZZ0.ZZ0_STATUS = 'E' "

    oStatement := FWExecStatement():New(cQueryZZ0)
    cAliasZZ0 := oStatement:openAlias()
    oStatement:Destroy()

    If !(cAliasZZ0)->(EOF())
        lContinua := FWAlertNoYes( ;
            "Existem " + cValToChar((cAliasZZ0)->QTDEERRO) + ;
            " registros com erro. Recolocar na fila?", "Prosseguir?")
    EndIf
    (cAliasZZ0)->(DBCloseArea())

    If lContinua
        // Busca registros para atualizar
        cQueryZZ0 := "SELECT ZZ0.R_E_C_N_O_ ZZ0RECNO "
        cQueryZZ0 += "FROM " + retSQLName("ZZ0") + " ZZ0 "
        cQueryZZ0 += "WHERE ZZ0.ZZ0_FILIAL <> ' ' "
        cQueryZZ0 += "  AND ZZ0.D_E_L_E_T_ = ' ' "
        cQueryZZ0 += "  AND ZZ0.ZZ0_ENTIDA = 'SLQ' "
        cQueryZZ0 += "  AND ZZ0.ZZ0_STATUS = 'E' "

        oStatement := FWExecStatement():New(cQueryZZ0)
        cAliasZZ0 := oStatement:openAlias()
        oStatement:Destroy()

        DBSelectArea("ZZ0")
        While !(cAliasZZ0)->(EOF())
            ZZ0->(DBGoTo((cAliasZZ0)->ZZ0RECNO))
            If ZZ0->ZZ0_STATUS == "E"
                If recLock("ZZ0", .F.)
                    ZZ0->ZZ0_STATUS := "P"
                    ZZ0->ZZ0_MENSAG := AllTrim(ZZ0->ZZ0_MENSAG) + CRLF + ;
                        fwTimeStamp(2) + CRLF + ;
                        "Recolocado em fila por " + AllTrim(usrFullName(retCodUsr()))
                    ZZ0->(msUnLock())
                EndIf
            EndIf
            (cAliasZZ0)->(DBSkip())
        EndDo
        (cAliasZZ0)->(DBCloseArea())
        FWAlertWarning("Registros recolocados na fila.", "Concluído")
    EndIf

    fwRestArea(aAreaX)
Return
```

### 11.7 Padrões e técnicas observados nos exemplos

| Técnica | Onde usar | Exemplo |
|---------|----------|---------|
| `namespace` | Organizar fontes por domínio | `custom.mvc.quote`, `custom.mvc.customer` |
| `FWMBrowse` + `SetFilterDefault` | 1 tabela, N monitores | `ZZ0_ENTIDA == 'SA1'` |
| `FwLoadModel("namespace.funcao")` | ViewDef carregando Model pelo namespace | `FwLoadModel("custom.mvc.quote.quoteMonitor")` |
| `startJob()` | Reprocessamento assíncrono | `startJob("u_reprocessQuote", getEnvServer(), .F., ...)` |
| `FWExecStatement` | Query segura (evita injection) | Reenfileiramento em massa |
| `fwAlertError/Success/Warning` | Feedback visual padronizado | Substituem `MsgStop/MsgInfo` |
| `fwGetArea/fwRestArea` | Versão TLPP do GetArea/RestArea | Mais limpo que o padrão clássico |
| `usrFullName(retCodUsr())` | Rastreabilidade de quem fez a ação | Log no campo `ZZ0_MENSAG` |
| `fwTimeStamp(2)` | Timestamp formatado para log | Data+hora no log de mensagens |
| `retSQLName()` | Nome real da tabela no SQL | Evita hard-code do schema |
| `FWAlertNoYes` | Confirmação estilizada | Substitui `MsgYesNo()` |

### 11.8 Comparativo: MVC customizado do zero vs PE em tela padrão

| Aspecto | MVC do zero (exemplos TLPP) | PE em tela padrão (A300STRU) |
|---------|----------------------------|------------------------------|
| Controle | Total — você define tudo | Parcial — modifica o que o PE permite |
| Complexidade | Menor — código limpo e previsível | Maior — precisa entender IDs internos |
| Manutenção | Independente de pacotes TOTVS | Pode quebrar com atualizações |
| Quando usar | Telas 100% customizadas, integrações | Adicionar funcionalidade em tela padrão |
| Namespace | Usa nativamente | Não se aplica (ADVPL clássico) |
| `FwLoadModel` | Referência por namespace | Referência por nome da rotina |

---

### Checklist antes de entregar

- [ ] PE retorna `aParam[3] := xObj` no final
- [ ] `FWSaveRows/FWRestRows` em toda função que navega grid
- [ ] `GetArea/RestArea` em toda função que posiciona tabelas
- [ ] `MaFisSave/MaFisRestore` se usar MATXFIS dentro de contexto MVC
- [ ] `bLinePost` original preservado com `IIf(ValType...)`
- [ ] `SetOptional(.T.)` se a grid pode ficar vazia
- [ ] Campos de chave removidos da View
- [ ] IDs únicos para AddGrid, CreateHorizontalBox, AddGrid na View
- [ ] `oView:Refresh()` com verificação de `oView != NIL`
- [ ] Testado em inclusão, alteração, visualização e exclusão
