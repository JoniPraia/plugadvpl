---
description: MVC avançado via PE (Pontos de Entrada) — adicionar grids customizadas em telas MVC padrão (CNTA300/MATA070/MATA440/MATA460/FINA040 via *STRU), AddTrigger em cascata, validações preservando original (bLinePost), SetErrorMessage estruturado, FWSaveRows/FWRestRows para navegação segura, integração MATXFIS dentro de gatilhos MVC, controle de comportamento por status. Use quando customizar MVC TOTVS padrão sem alterar fonte original.
---

# advpl-mvc-avancado — Customização MVC avançada via PE

A skill `[[advpl-mvc]]` cobre criar cadastros MVC do zero. **Esta skill cobre o cenário muito mais comum**: customizar uma rotina MVC padrão TOTVS via Ponto de Entrada (`A300STRU`, `MA440STRU`, etc.) — adicionando grids filhas, gatilhos em cascata, validações preservando as originais, e controle de comportamento por status.

## Quando usar

- Usuário pede "adicionar grid em tela padrão", "customizar cadastro TOTVS sem mexer no fonte", "PE estrutura MVC", "PE STRU".
- Necessidade de injetar comportamento em rotina como `CNTA300`, `MATA440`, `MATA460`, `MATA103`, `FINA040`, `MATA070`.
- Validação cruzada entre grids pai/filha em cadastro padrão.
- Cálculo fiscal (`[[advpl-matxfis]]`) dentro de gatilho MVC.
- Bloqueio condicional de edição baseado em status do registro mestre.
- Refactor de `MsNewGetDados` ad-hoc dentro de MVC para grid nativa.

## Lista de PE STRU comuns (rotina padrão → PE)

| Rotina padrão                      | PE STRU      | Módulo            |
|------------------------------------|--------------|-------------------|
| `MATA010` — Produtos               | `MA010STRU`  | Estoque (EST)     |
| `MATA070` — Fornecedores           | `MA070STRU`  | Compras (COM)     |
| `MATA103` — NF Entrada             | `MT103STRU`  | Estoque/Compras   |
| `MATA440` — Pedido de Compra       | `MA440STRU`  | Compras           |
| `MATA460` — Faturamento            | `M460STRU`   | Faturamento (FAT) |
| `CNTA300` — Contratos              | `A300STRU`   | Logística (LOG)   |
| `FINA040` — Títulos                | `FA040STRU`  | Financeiro (FIN)  |
| `FINA050` — Baixa                  | `FA050STRU`  | Financeiro        |

Para descobrir o PE certo de uma rotina, busque no projeto: `/plugadvpl:grep "<ROT>STRU"` ou `/plugadvpl:find function <ROT>STRU`.

### Outras famílias de PE MVC (não-STRU)

| Sufixo PE          | Quando dispara                                          |
|--------------------|---------------------------------------------------------|
| `<Rot>MOD`         | Injeta lógica no `ModelDef` (estrutura, validações)     |
| `<Rot>VLD`         | Validação extra antes de gravar (cruzada entre campos)  |
| `<Rot>COMMIT`      | Depois do commit (notificações, integração externa)     |
| `<Rot>BLOQ`        | Bloqueia operação condicionalmente (retorna `.F.`)      |
| `<Rot>MARK`        | Validação de marcação (em browses tipo `MarkBrowse`)    |
| `<Rot>SEEK`        | Customiza filtro/ordem do browse                        |
| `<Rot>BTN`         | Adiciona botão na barra de ferramentas                  |

## O PE bifurcado MODELDEF + VIEWDEF

PEs `*STRU` recebem três parâmetros via `PARAMIXB`:

```advpl
User Function A300STRU()
    Local aParam := PARAMIXB
    Local cTipo  := aParam[1]   // "MODELDEF" ou "VIEWDEF"
    Local cEspec := aParam[2]   // contexto: "C"=Compra, "V"=Venda, etc.
    Local xObj   := aParam[3]   // oModel OU oView (por referencia)

    If cEspec == "V"
        If cTipo == "MODELDEF"
            xObj := AddMinhaGridModel(xObj)
        ElseIf cTipo == "VIEWDEF"
            xObj := AddMinhaGridView(xObj)
        EndIf
    EndIf

    aParam[3] := xObj   // OBRIGATORIO — devolve via referencia
Return
```

**Sem o `aParam[3] := xObj` no fim, alterações se perdem.** É o erro #1 em PE STRU.

## Adicionando grid filha ao Model

```advpl
Static Function AddMinhaGridModel(oModel)
    Local oStruZZ3 := FWFormStruct(1, "ZZ3", /*bAvalCampo*/, .F.)

    // Configurar propriedades dos campos
    oStruZZ3:SetProperty("ZZ3_CODEVT", MODEL_FIELD_OBRIGAT, .T.)
    oStruZZ3:SetProperty("ZZ3_DESCRI", MODEL_FIELD_NOUPD,   .T.)

    // Gatilho intra-estrutura: campo CODEVT preenchido -> DESCRI lookup SX5
    oStruZZ3:AddTrigger( ;
        "ZZ3_CODEVT", ;     // campo gatilho
        "ZZ3_DESCRI", ;     // campo destino
        {|| .T.}, ;         // condicao
        {|oM| Posicione("SX5", 1, ;
            xFilial("SX5") + "Z1" + oM:GetValue("ZZ3_CODEVT"), ;
            "X5_DESCRI") } )

    oModel:AddGrid("ZZ3DETAIL", "CNAMASTER", oStruZZ3, ;
        /*bLinePre*/, /*bLinePost*/, /*bPre*/, /*bPost*/, /*bLoad*/)

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

    // Remover campos de chave da tela (vem via SetRelation, nao precisam de input)
    oStruZZ3:RemoveField("ZZ3_FILIAL")
    oStruZZ3:RemoveField("ZZ3_CODCNT")

    oView:AddGrid("VIEW_ZZ3", oStruZZ3, "ZZ3DETAIL")

    // Redimensionar layout — caso original tinha 1 grid 100%, agora vamos pra 3 boxes
    oView:CreateHorizontalBox("CABEC",   30)
    oView:CreateHorizontalBox("GRIDCNC", 40)   // grid principal redimensionada
    oView:CreateHorizontalBox("GRIDZZ3", 30)   // nova grid

    oView:SetOwnerView("VIEW_CAB", "CABEC")
    oView:SetOwnerView("VIEW_CNC", "GRIDCNC")
    oView:SetOwnerView("VIEW_ZZ3", "GRIDZZ3")
Return oView
```

## Hierarquia pai/filho/neto (multi-grid)

Cadastros mais complexos (ex: Ordem de Produção → Operações → Recursos) usam 3 níveis:

```advpl
oModel:AddFields("OPMASTER", /*parent*/, oStruOP)      // 1. Pai: Ordem de Producao

oModel:AddGrid("OPITEM",     "OPMASTER", oStruIT)      // 2. Filho: Operacoes
oModel:SetRelation("OPITEM", { ;
    {"OP1_FILIAL", "xFilial('OP1')"}, ;
    {"OP1_NUMOP",  "OP->OP_NUM"} ;
}, OP1->(IndexKey(1)))

oModel:AddGrid("OPRECURS",   "OPITEM",   oStruRC)      // 3. Neto: Recursos de cada operacao
oModel:SetRelation("OPRECURS", { ;
    {"OP2_FILIAL", "xFilial('OP2')"}, ;
    {"OP2_NUMOP",  "OP1->OP1_NUMOP"}, ;
    {"OP2_ITEM",   "OP1->OP1_ITEM"} ;
}, OP2->(IndexKey(1)))

oModel:GetModel("OPITEM"):SetUniqueLine({"OP1_ITEM"})
oModel:GetModel("OPRECURS"):SetUniqueLine({"OP2_RECURS"})
```

## Gatilhos em cascata (pai → filha)

Quando campo da grid pai muda, recalcula colunas da filha:

```advpl
oStruCNC:AddTrigger( ;
    "CNC_VALOR", ;
    "CNC_VLRREL", ;
    {|| .T.}, ;
    {|oM| RecalcZZ3(oM) } )

Static Function RecalcZZ3(oModel)
    Local oZZ3 := oModel:GetModel("ZZ3DETAIL")
    Local nI

    FWSaveRows()    // salva positioning de TODAS as grids ativas
    For nI := 1 To oZZ3:Length()
        oZZ3:GoLine(nI)
        oZZ3:SetValue("ZZ3_VALOR", oModel:GetValue("CNCMASTER", "CNC_VALOR") * 0.1)
    Next nI
    FWRestRows()    // restaura positioning original

Return oModel:GetValue("CNCMASTER", "CNC_VLRREL")
```

**Sem `FWSaveRows`/`FWRestRows`, mudanças de positioning corrompem a row corrente** — bug clássico que aparece como "valor sobrescrevendo errado" no grid.

### Anti-pattern `AddCalc` sem FWSaveRows

`AddCalc()` (cálculo de totalizador) também mexe em positioning. Se você combina `AddCalc` com `AddTrigger` que percorre grid, embrulha em `FWSaveRows`/`FWRestRows`:

```advpl
{|oM| ;
    Local nTotal := 0 ;
    FWSaveRows() ;
    nTotal := SomaTotalGrid(oM) ;
    FWRestRows() ;
    Return nTotal }
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

> **Crítico:** sempre `MaFisEnd()` ao final pra liberar contexto fiscal. Sem isso o estado vaza pro próximo registro e gera ICMS errado. Veja `[[advpl-matxfis]]`.

## Validações preservando a original (bLinePost / bPosVld)

A grid padrão TOTVS pode já ter `SetLinePost`. **Substituir cego** quebra o comportamento original (que valida coisas como código de produto válido, qtd > 0, etc.). Pattern correto: capturar o bloco original, **chamar antes** da sua validação, e só prosseguir se passou.

```advpl
// Captura o bloco original
Local bOrigVld := oStruZZ3:bLinePost

oModel:GetModel("ZZ3DETAIL"):SetLinePost({|oM| ;
    Local lOk := .T. ;
    If bOrigVld != Nil ;
        lOk := Eval(bOrigVld, oM) ;  // chama original primeiro
    EndIf ;
    If lOk ;
        lOk := U_XYZMinhaValid(oM) ;  // só valida custom se original passou
    EndIf ;
    Return lOk })
```

## SetErrorMessage — feedback estruturado

Sempre use `SetErrorMessage` em vez de `MsgInfo`/`Alert`/`Help` — MVC formata a mensagem na janela padrão de erros e pode ser capturada em ExecAuto:

```advpl
Static Function MyValid(oModel)
    If oModel:GetValue("ZZ3DETAIL", "ZZ3_VALOR") <= 0
        oModel:SetErrorMessage( ;
            "ZZ3DETAIL", ;          // id do sub-model
            "ZZ3_VALOR", ;          // campo
            "ZZ3DETAIL", ;          // id de exibicao
            "ZZ3_VALOR", ;          // campo de exibicao
            "VALOR_INVALIDO", ;     // codigo do erro
            "Valor deve ser maior que zero", ;     // mensagem PT
            "Confira o valor digitado") ;          // solucao sugerida
        Return .F.
    EndIf
Return .T.
```

## Validação condicional por contexto: `FwIsInCallStack`

Para validar diferente conforme onde a rotina foi chamada (interativo × ExecAuto × scheduler):

```advpl
If FwIsInCallStack("U_XYZAJUS")
    // chamado de ajuste em lote — pula validacao interativa
    Return .T.
EndIf
If FwIsInCallStack("MATA460")
    // chamado dentro do faturamento — usa regra fiscal alternativa
    cRegraAlt := "FAT"
EndIf
// validacao normal pra UI direta
```

## Controle de comportamento por status

`SetOnlyView` × `SetOnlyQuery` — diferença sutil mas importante:

| Método                  | Efeito                                                  |
|-------------------------|---------------------------------------------------------|
| `SetOnlyView(.T.)`      | Sub-model **read-only** — usuário não consegue alterar  |
| `SetOnlyQuery(.T.)`     | Usuário pode **alterar mas não grava** — dados em memória só |
| `SetNoInsertLine(.T.)`  | Bloqueia adicionar nova linha (grid)                    |
| `SetNoDeleteLine(.T.)`  | Bloqueia deletar linha (grid)                           |

```advpl
Static Function SetStatusBlocks(oModel)
    Local cStatus := oModel:GetValue("CNBMASTER", "CNB_SITUAC")

    If cStatus $ "F|E"  // Finalizado ou Encerrado
        oModel:GetModel("ZZ3DETAIL"):SetOnlyView(.T.)
    ElseIf cStatus == "B"  // Bloqueado
        oModel:GetModel("ZZ3DETAIL"):SetNoInsertLine(.T.)
        oModel:GetModel("ZZ3DETAIL"):SetNoDeleteLine(.T.)
    EndIf
Return Nil
```

## `FWModelActive()` — acessar model ativo de outro contexto

Quando uma User Function genérica é chamada de um PE sem receber `oModel` como parâmetro:

```advpl
User Function XYZGeneric(cCampo)
    Local oModel := FWModelActive()   // pega o model que estah na pilha
    Local cValor := ""
    If oModel != Nil
        cValor := oModel:GetValue("ZZ1MASTER", cCampo)
    EndIf
Return cValor
```

> Útil em funções utilitárias chamadas a partir de PEs de SX3 (X3_VALID, X3_INIT) que não passam `oModel`.

## Quando usar PE × FWModelEvent?

| Cenário                                              | Use                       |
|------------------------------------------------------|---------------------------|
| Customizar rotina TOTVS padrão (não posso mexer fonte) | **PE `<Rot>STRU/MOD/VLD/COMMIT`** |
| Cadastro próprio do cliente, novo                   | `FWModelEvent` + `InstallEvent` (veja `[[advpl-mvc]]`) |
| Adicionar validação cross-banco em cadastro padrão  | PE `<Rot>VLD`             |
| Adicionar grid filha em cadastro padrão             | PE `<Rot>STRU`            |
| Mexer no commit de cadastro TOTVS (auditoria, log)  | PE `<Rot>COMMIT`          |

PE pattern preserva a possibilidade de TOTVS atualizar a rotina padrão sem perder customização. FWModelEvent é melhor pra cadastros que você é dono do código todo.

## Anti-padrões

- **Esquecer `aParam[3] := xObj`** no fim do PE STRU → alterações perdidas silenciosamente.
- **Sobrescrever validação original** sem capturar antes (`bOrigVld := oStruct:bLinePost`) → quebra comportamento padrão TOTVS, gera bug em produção difícil de rastrear.
- **Mexer em grid filha sem `FWSaveRows`/`FWRestRows`** → corrompe row corrente, valor sobrescreve campo errado.
- **`AddCalc` sem `FWSaveRows`** ao redor → mesmo problema.
- **Hardcode de campo customer** no PE sem checar `FieldPos`/`Type` → quebra em cliente sem o campo.
- **Validar com `MsgInfo`/`Alert`** em vez de `SetErrorMessage` → MVC perde controle do fluxo, ExecAuto não captura erro.
- **Cálculo fiscal sem `MaFisEnd()`** → contexto fiscal vaza para próximo registro (ICMS, IPI, PIS errado).
- **Renderizar grid via `MsNewGetDados` dentro do View MVC** → MVC perde controle, validações nativas não disparam.
- **Esquecer `RemoveField` dos campos de chave na View** → tela fica com inputs duplicados de FILIAL/CHAVE.

## Cross-references com outras skills

- `[[advpl-mvc]]` — fundamentos MVC: MenuDef/ModelDef/ViewDef, FWMVCMenu, FWModelEvent + InstallEvent.
- `[[advpl-pontos-entrada]]` — pattern geral de PE: `User Function NOME(PARAMIXB)`, retorno via `PARAMIXB[última]`.
- `[[advpl-fundamentals]]` — `User Function` sem prefixo cliente em PE (exceção justificada).
- `[[advpl-dicionario-sx]]` — estrutura SX3/SX7 que alimenta `FWFormStruct`.
- `[[advpl-dicionario-sx-validacoes]]` — X3_VALID dentro do `FWFormStruct(1)`.
- `[[advpl-matxfis]]` — cálculo fiscal em gatilhos MVC (`MaFisIni`/`MaFisCalc`/`MaFisEnd`).
- `[[advpl-code-review]]` — regras BP-001 (RecLock), BP-006 (mistura raw + framework).
- `[[advpl-embedded-sql]]` — queries dentro de validações (com `%xfilial%`, `%notDel%`).
- `[[plugadvpl-index-usage]]` — `/plugadvpl:find function <ROT>STRU`, `/plugadvpl:callers FWFormStruct`.

## Referência profunda

Para detalhes completos (~1k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Anatomia completa do PE `A300STRU` (caso real CNTA300 — contratos).
- Cadeia de gatilhos entre grids com diagrama de execução.
- Lista exaustiva de erros comuns ao adicionar grid (índice, relação, owner-view).
- Padrão de migração de customização "MsNewGetDados ad-hoc" → grid MVC nativa.
- Template completo para "adicionar grid em tela MVC padrão".

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <ROT>STRU` — localiza PE de estrutura no projeto.
- `/plugadvpl:find function <ROT>MOD` — PE de model.
- `/plugadvpl:find function <ROT>VLD` — PE de validação.
- `/plugadvpl:callers FWFormStruct` — uso de `FWFormStruct` no projeto.
- `/plugadvpl:tables <ZZ*>` — lista campos da grid customer.
- `/plugadvpl:lint <arq>` — checa `BP-001`/`BP-002` no PE.
- `/plugadvpl:impacto <campo>` — vê quem mais usa o campo da grid custom.

## Sources

- [Lista de Pontos de Entrada em MVC - Terminal de Informação](https://terminaldeinformacao.com/2015/02/09/lista-de-pontos-de-entrada-em-mvc/)
- [Pontos de Entrada em MVC - YouTube + GitHub](https://github.com/dan-atilio/AdvPL/tree/master/Exemplos/V%C3%ADdeo%20Aulas/023%20-%20Pontos%20de%20Entrada%20em%20MVC)
- [Ponto de Entrada MATA070 MVC - Terminal de Informação](https://terminaldeinformacao.com/knowledgebase/ponto-de-entrada-mata070-mvc/)
- [Pontos de entrada MVC MATA010 - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360000351188-Cross-Segmento-TOTVS-Backoffice-Linha-Protheus-ADVPL-Pontos-de-entrada-MVC-da-rotina-MATA010)
- [Pontos de entrada do Faturamento - Código Expresso](https://codigoexpresso.com/2025/07/06/pontos-de-entrada-do-faturamento-protheus/)
- [Grid MVC sobrescrevendo valores - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360051846753)
- [Como percorrer uma grid em MVC - Terminal de Informação](https://terminaldeinformacao.com/2022/08/15/como-percorrer-uma-grid-em-mvc-ti-responde-017/)
- [ADVPL MVC - Comandos - Universo do Desenvolvedor](https://udesenv.com.br/post/advpl-mvc-comandos)
- [Manual ADVPL com MVC TOTVS (PDF)](https://www.academia.edu/17040592/Manual_ADVPL_com_MVC_TOTVS)
