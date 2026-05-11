#Include "PROTHEUS.CH"
#Include "FWMVCDEF.CH"

//-------------------------------------------------------------------
/*/{Protheus.doc} A300STRU
Ponto de Entrada para customizar Model e View do CNTA300
Adiciona grid ZZ3 (Eventos Financeiros) como filha da CNB

PARÂMETROS RECEBIDOS:
aParam[1] = "MODELDEF" ou "VIEWDEF"
aParam[2] = "C" (Compra) ou "V" (Venda)
aParam[3] = @oModel ou @oView (passado por referência)

@type  User Function
@author J.Carmo
@since  20/10/2025
/*/
//-------------------------------------------------------------------
User Function A300STRU()
    Local aParam := PARAMIXB
    Local cTipo  := aParam[1]  // "MODELDEF" ou "VIEWDEF"
    Local cEspec := aParam[2]  // "C" = Compra, "V" = Venda
    Local xObj   := aParam[3]  // oModel ou oView
    
    If cEspec == "V"
        If cTipo == "MODELDEF"
            // Adicionar ZZ3 no Model
            xObj := AddZZ3Model(xObj)
        
        ElseIf cTipo == "VIEWDEF"
            // Adicionar ZZ3 na View
            xObj := AddZZ3View(xObj)
            
        EndIf
    EndIf
    // Retornar objeto modificado
    aParam[3] := xObj
    
Return


//-------------------------------------------------------------------
/*/{Protheus.doc} AddZZ3Model
Adiciona grid ZZ3 no Model do CNTA300
@param oModel - Model original
@return oModel - Model modificado
/*/
//-------------------------------------------------------------------
Static Function AddZZ3Model(oModel)

    Local oModelCNB     := oModel:GetModel('CNBDETAIL')
    Local oModelZZ3     := Nil
    Local oStruZZ3      := FWFormStruct(1, 'ZZ3') // Criar estrutura da ZZ3
    Local oStruCNB      := oModel:GetModel('CNBDETAIL'):GetStruct()

    Local bLinePostOld := Nil
    Local cSituacao    := ""
    Local nOperation   := oModel:GetOperation()

    oStruZZ3:SetProperty('ZZ3_PERCEN',MODEL_FIELD_OBRIGAT,.T.)//percentual
    oStruZZ3:SetProperty('ZZ3_DTPREV',MODEL_FIELD_OBRIGAT,.T.)//dt Previsão
    
    oStruZZ3:SetProperty('ZZ3_PERCEN', MODEL_FIELD_VALID,FwBuildFeature(STRUCT_FEATURE_VALID, "U_Z3VldEdit('ZZ3_PERCEN')"))
    oStruZZ3:SetProperty('ZZ3_DTPREV', MODEL_FIELD_VALID,FwBuildFeature(STRUCT_FEATURE_VALID, "U_Z3VldEdit('ZZ3_DTPREV')"))
    
    //Gatilhos ZZ3
    // =====================================================
    // GATILHO 1: ZZ3_PERCEN ? ZZ3_VLBASE
    // Calcula valor base proporcional ao percentual
    // =====================================================
    oStruZZ3:AddTrigger(;
        'ZZ3_PERCEN',;                                          // Campo origem
        'ZZ3_VLBASE',;                                          // Campo destino
        {|| .T. },;                                             // bPre - sempre executa
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;           // bSetValue
            U_xA3VlBase(oMdlGrid, cId, xValue, nLine, xCurValue)})

    // =====================================================
    // GATILHO 2: ZZ3_VLBASE ? ZZ3_VLFRET
    // Calcula frete do evento (rateio em cascata)
    // =====================================================
    oStruZZ3:AddTrigger(;
        'ZZ3_VLBASE',;
        'ZZ3_VLFRET',;
        {|| .T. },;
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;
            U_xA3CalcFrete(oMdlGrid, cId, xValue, nLine, xCurValue)})

    // =====================================================
    // GATILHO 3: ZZ3_VLBASE ? ZZ3_VLIMP
    // Calcula impostos (ICMS+PIS+COFINS) sobre o valor base
    // =====================================================
    oStruZZ3:AddTrigger(;
        'ZZ3_VLBASE',;                                          // Campo origem
        'ZZ3_VLIMP',;                                           // Campo destino
        {|| .T. },;                                             // bPre - sempre executa
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;           // bSetValue
            U_xA3CalcImp(xValue)})  // xValue = ZZ3_VLBASE

    // =====================================================
    // GATILHO 4: ZZ3_VLBASE ? ZZ3_VLLIQ 
    // Calcula impostos (ICMS+PIS+COFINS) sobre o valor base
    // =====================================================
    oStruZZ3:AddTrigger(;
        'ZZ3_VLBASE',;                                          // Campo origem
        'ZZ3_VLLIQ',;                                           // Campo destino
        {|| .T. },;                                             // bPre - sempre executa
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;           // bSetValue
            U_xA3ValLiq(oMdlGrid, cId, xValue, nLine, xCurValue)})  // xValue = ZZ3_VLBASE

    //Gatilhos CNB
       // Adiciona gatilho na CNB para recalcular ZZ3
    oStruCNB:AddTrigger('CNB_VLTOT',; // Campo origem
                        'CNB_VLTOT',; // Campo destino
                         {|| .T. }, ; // bPre - sempre executa
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ; // bSetValue
            U_xA3RecZZ3(oMdlGrid, cId, xValue, nLine, xCurValue), xValue})    

    oStruCNB:AddTrigger('CNB_TS', 'CNB_TS', {|| .T. }, ;
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;
            U_xA3RecTS(oMdlGrid, cId, xValue, nLine, xCurValue), xValue})

    oStruCNB:AddTrigger('CNB_ZTRANS', 'CNB_ZTRANS', {|| .T. }, ;
        {|oMdlGrid, cId, xValue, nLine, xCurValue| ;
            U_xA3RecFrete(oMdlGrid, cId, xValue, nLine, xCurValue), xValue})

    // ADICIONAR GRID ZZ3 COMO FILHA DA CNB
    oModel:AddGrid('ZZ3DETAIL',  ;    // ID do Model
                   'CNBDETAIL',  ;    // ID do PAI (CNB = Itens)
                   oStruZZ3)          // Estrutura
    
    // RELACIONAMENTO: ZZ3 x CNB
    oModel:SetRelation('ZZ3DETAIL', {;
        {'ZZ3_FILIAL', 'xFilial("CNB")'},;
        {'ZZ3_CONTRA', 'CN9_NUMERO'},;
        {'ZZ3_PLANIL', 'CNA_NUMERO'},;
        {'ZZ3_ITEMCO', 'CNB_ITEM'},;
        {'ZZ3_PRODUT', 'CNB_PRODUT'};
    }, ZZ3->(IndexKey(1)))
    
    // PROPRIEDADES DA GRID
    oModelZZ3 := oModel:GetModel('ZZ3DETAIL')
    oModelZZ3:SetDescription('Eventos Financeiros')
    oModelZZ3:SetOptional(.T.)      // Grid opcional
    //oModel:GetModel('ZZ3DETAIL'):SetMaxLine(99)        // Máximo 99 linhas
    oModelZZ3:SetUniqueLine({'ZZ3_ITEM'})  

    // =====================================================
    // CONTROLE DE REVISÃO - IMPEDIR DUPLICAÇÃO DA ZZ3
    // A ZZ3 não deve ser copiada quando criar nova revisão
    // Apenas consulta os dados existentes, sem gravar
    // =====================================================
    If !Empty(A300GTpRev())
        // Em processo de revisão: ZZ3 vira somente consulta
        // Isso impede que o MVC duplique os registros
        oModelZZ3:SetOnlyQuery(.T.)
    EndIf

    // =====================================================
    // BLOQUEAR ZZ3 SE NÃO ESTIVER EM ELABORAÇÃO/REVISÃO
    // Só permite editar em: 02-Elaboração ou 09-Revisão
    // =====================================================
    If !(nOperation == 1/*MODEL_OPERATION_INSERT*/) .and. FwIsInCallStack("CN300InVEN")
        cSituacao := AllTrim(CN9->CN9_SITUAC)
    
        If !(cSituacao $ "02|09")  // NÃO é Elaboração nem Revisão RETIRAR 05
            oModelZZ3:SetNoInsertLine(.T.)
            oModelZZ3:SetNoUpdateLine(.T.)
            oModelZZ3:SetNoDeleteLine(.T.)
        EndIf
    Endif

    // =====================================================
    // ADICIONAR VALIDAÇÃO NO CNBDETAIL
    // Mantém validação existente + adiciona nova
    // =====================================================
 
    // Captura validação existente (se houver)
    bLinePostOld := oModelCNB:bLinePost

    // Adiciona nova validação mantendo a antiga
    oModelCNB:bLinePost := {|oMdlCNB| ;
        IIf(ValType(bLinePostOld) == "B", Eval(bLinePostOld, oMdlCNB), .T.) .And. ;
        VldPercZZ3Item(oMdlCNB) ;  
    }

Return oModel


//-------------------------------------------------------------------
/*/{Protheus.doc} AddZZ3View
Adiciona grid ZZ3 na View do CNTA300
@param oView - View original
@return oView - View modificada
/*/
//-------------------------------------------------------------------
Static Function AddZZ3View(oView)
    Local oStruZZ3 := FWFormStruct(2, 'ZZ3')
    Local nX       := 0

    // Remover campos
    oStruZZ3:RemoveField('ZZ3_FILIAL')
    oStruZZ3:RemoveField('ZZ3_CONTRA')
    oStruZZ3:RemoveField('ZZ3_REVISA')
    oStruZZ3:RemoveField('ZZ3_PLANIL')
    oStruZZ3:RemoveField('ZZ3_ITEMCO')
    oStruZZ3:RemoveField('ZZ3_PRODUT')
    oStruZZ3:RemoveField('ZZ3_TITPR')
    oStruZZ3:RemoveField('ZZ3_TITRA')

    // MODIFICAR GRDITS para 70%
    
    If AttIsMemberOf(oView, "AUSERBOXS")
        For nX := 1 To Len(oView:AUSERBOXS)
            If ValType(oView:AUSERBOXS[nX]) == "O"
                If AttIsMemberOf(oView:AUSERBOXS[nX], "CCLIENTID")
                    If oView:AUSERBOXS[nX]:CCLIENTID == "GRDITS"
                        oView:AUSERBOXS[nX]:NPERCETUAL := 55
                        Exit
                    EndIf
                EndIf
            EndIf
        Next
    EndIf

    // ADICIONAR GRID ZZ3
    oView:AddGrid('VIEW_ZZ3', oStruZZ3, 'ZZ3DETAIL')
    
    // CRIAR BOX ZZ3 com 30% DENTRO de PLANITS (não como nova aba!)
    oView:CreateHorizontalBox('BOX_ZZ3',45,/*owner*/,/*lUsePixel*/,"FLDPLAN",'ABAITS')
    //oView:CreateHorizontalBox('BOX_ZZ3', 30, 'PLANITS')
    oView:SetOwnerView('VIEW_ZZ3', 'BOX_ZZ3')
    
    // PROPRIEDADES
    oView:EnableTitleView('VIEW_ZZ3', 'Eventos Financeiros do Item')
    oView:AddIncrementField('VIEW_ZZ3', 'ZZ3_ITEM')
   
Return oView

//-------------------------------------------------------------------
/*/{Protheus.doc} xA3VlBase
Calcula ZZ3_VLBASE com base no percentual informado
Gatilho: ZZ3_PERCEN ? ZZ3_VLBASE

Fórmula: ZZ3_VLBASE = CNB_VLTOT * (ZZ3_PERCEN / 100)

@param oMdlGrid     - Model da grid ZZ3DETAIL
@param cId          - ID do campo que disparou o gatilho
@param xValue       - Novo valor digitado (ZZ3_PERCEN)
@param nLine        - Linha atual da grid
@param xCurValue    - Valor anterior do campo

@return nVlBase - Valor base calculado

@author J.Carmo
@since 20/10/2025
/*/
//-------------------------------------------------------------------
User Function xA3VlBase(oMdlGrid, cId, xValue, nLine, xCurValue)
    Local oModel    := oMdlGrid:GetModel()
    Local oModelCNB := oModel:GetModel('CNBDETAIL')
    Local nVlTotCNB := oModelCNB:GetValue('CNB_VLTOT')
    Local nPercen   := xValue
    Local nVlBase   := 0
    
    // Calcula Valor Base proporcional ao percentual
    nVlBase := nVlTotCNB * (nPercen / 100)
    
Return nVlBase

//-------------------------------------------------------------------
/*/{Protheus.doc} xA3CalcImp
Calcula o valor de impostos (ICMS, PIS, COFINS) sobre o valor base
do evento financeiro usando MaFis

Gatilho: ZZ3_VLBASE ? ZZ3_VLIMP

@param nVlBase - Valor base do evento (ZZ3_VLBASE)

@return nVlImp - Valor total dos impostos

@author J.Carmo
@since 20/10/2025
/*/
//-------------------------------------------------------------------
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
    Local nItem       := 0
    Local nVlImp      := 0
    Local nVlICMS     := 0
    Local nVlPIS      := 0
    Local nVlCOFINS   := 0
    
    // =====================================================
    // VALIDAÇÕES INICIAIS
    // =====================================================
    If Empty(cCliente) .Or. Empty(cLoja) .Or. Empty(cProduto) .Or. Empty(cTes)
        RestArea(aAreaSF4)
        RestArea(aAreaSB1)
        RestArea(aAreaSA1)
        RestArea(aArea)
        Return 0
    EndIf
    
    // =====================================================
    // POSICIONA TABELAS
    // =====================================================
    DbSelectArea("SF4")
    SF4->(DbSetOrder(1)) // F4_FILIAL+F4_CODIGO
    If !SF4->(DbSeek(xFilial("SF4") + cTes))
        RestArea(aAreaSF4)
        RestArea(aAreaSB1)
        RestArea(aAreaSA1)
        RestArea(aArea)
        Return 0
    EndIf
    
    DbSelectArea("SB1")
    SB1->(DbSetOrder(1)) // B1_FILIAL+B1_COD
    If !SB1->(DbSeek(xFilial("SB1") + cProduto))
        RestArea(aAreaSF4)
        RestArea(aAreaSB1)
        RestArea(aAreaSA1)
        RestArea(aArea)
        Return 0
    EndIf
    
    DbSelectArea("SA1")
    SA1->(DbSetOrder(1)) // A1_FILIAL+A1_COD+A1_LOJA
    If !SA1->(DbSeek(xFilial("SA1") + cCliente + cLoja))
        RestArea(aAreaSF4)
        RestArea(aAreaSB1)
        RestArea(aAreaSA1)
        RestArea(aArea)
        Return 0
    EndIf
    
    // =====================================================
    // SALVA E ENCERRA MAFIS SE JÁ EXISTIR
    // =====================================================
    If MaFisFound("NF")
        MaFisSave()
        MaFisEnd()
        lBkpFis := .T.
    EndIf
    
    // =====================================================
    // INICIALIZA MAFIS PARA VENDA
    // =====================================================
    MaFisIni(;
        cCliente,;              // 1-Codigo Cliente
        cLoja,;                 // 2-Loja do Cliente
        "C",;                   // 3-C:Cliente (VENDA)
        "N",;                   // 4-Tipo da NF
        SA1->A1_TIPO,;          // 5-Tipo do Cliente
        aRelImp,;               // 6-Relacao de Impostos
        ,;                      // 7-Tipo de complemento
        ,;                      // 8-Permite Incluir Impostos no Rodape
        "SB1",;                 // 9-Alias do Cadastro de Produtos
        "CNTA300")              // 10-Nome da rotina
    
    // =====================================================
    // ADICIONA ITEM NO MAFIS
    // =====================================================
    nItem := MaFisAdd(;
        cProduto,;              // 1-Codigo do Produto
        cTes,;                  // 2-Codigo do TES (CNB_TS)
        1,;                     // 3-Quantidade
        nVlBase,;               // 4-Preco Unitario
        0,;                     // 5-Valor do Desconto
        '',;                    // 6-Numero da NF Original
        '',;                    // 7-Serie da NF Original
        0,;                     // 8-RecNo da NF Original
        0,;                     // 9-Valor do Frete do Item
        0,;                     // 10-Valor da Despesa do item
        0,;                     // 11-Valor do Seguro do item
        0,;                     // 12-Valor do Frete Autonomo
        nVlBase,;               // 13-Valor da Mercadoria
        0,;                     // 14-Valor da Embalagem
        SB1->(Recno()),;        // 15-RecNo do SB1
        SF4->(Recno()))         // 16-RecNo do SF4
    
    // =====================================================
    // BUSCA VALORES DOS IMPOSTOS
    // =====================================================
    If nItem > 0
        nVlICMS     := MaFisRet(nItem, "IT_VALICM")
        nVlPIS      := MaFisRet(nItem, "IT_VALPS2")
        nVlCOFINS   := MaFisRet(nItem, "IT_VALCF2")
        
        // Total de Impostos
        nVlImp := nVlICMS + nVlPIS + nVlCOFINS
    EndIf
    
    // =====================================================
    // FINALIZA MAFIS
    // =====================================================
    MaFisEnd()
    
    // Restaura MaFis se havia backup
    If lBkpFis
        MaFisRestore()
    EndIf
    
    // =====================================================
    // RESTAURA ÁREAS
    // =====================================================
    RestArea(aAreaSF4)
    RestArea(aAreaSB1)
    RestArea(aAreaSA1)
    RestArea(aArea)
    
Return nVlImp

User Function xA3ValLiq(oMdlGrid, cId, xValue, nLine, xCurValue)

    Local nRet := 0
    Local nValBrut := xValue
    Local nValImp := oMdlGrid:GetValue("ZZ3_VLIMP")
    Local nValFret := oMdlGrid:GetValue("ZZ3_VLFRET")

    nRet := nValBrut - nValImp - nValFret 

Return nRet

//-------------------------------------------------------------------
/*/{Protheus.doc} VldPercZZ3Item
Valida percentual ZZ3 apenas do item (CNB) atual
Validação de linha do CNB

REGRAS:
1. Soma dos percentuais deve ser 100% (exceto eventos residuais)
2. Deve existir exatamente UM evento com ZZ3_EVENF = "S" (libera NF)

@param oModelCNB - Grid de itens (CNB)

@return lRet - .T. se válido, .F. se inválido

@author J.Carmo
@since 21/10/2025
@history 09/12/2025 - J.Carmo - Adicionada validação de evento NF obrigatório (apenas 1)
/*/
//-------------------------------------------------------------------
Static Function VldPercZZ3Item(oModelCNB)
    Local lRet        := .T.
    Local oModel      := oModelCNB:GetModel()
    Local oModelZZ3   := oModel:GetModel('ZZ3DETAIL')
    Local aSaveLines  := FWSaveRows()
    Local nPercTotal  := 0
    Local nX          := 0
    Local lTemDados   := .F.
    Local nQtdEventoNF := 0
    
    // Percorre apenas os eventos do item atual
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)
        
        If !oModelZZ3:IsDeleted()
            // Só considera na soma se NÃO for evento residual (ZZ3_TITOR vazio)
            If Empty(oModelZZ3:GetValue('ZZ3_TITOR'))
                nPercTotal += oModelZZ3:GetValue('ZZ3_PERCEN')
                lTemDados := .T.
            EndIf
            
            // Conta quantos eventos estão liberados para NF
            If AllTrim(oModelZZ3:GetValue('ZZ3_EVENF')) == "S"
                nQtdEventoNF++
            EndIf
        EndIf
    Next
    
    // =====================================================
    // VALIDAÇÃO 1: Soma dos percentuais deve ser 100%
    // =====================================================
    If lTemDados .And. nPercTotal != 100
       oModel:SetErrorMessage(;
            "CNBDETAIL",                                           ; // cModelID
            "CNB_ITEM",                                            ; // cFieldID
            "CNBDETAIL",                                           ; // cModelErrID
            "CNB_ITEM",                                            ; // cFieldErrID
            "A300PERCZ3",                                          ; // cError
            "A soma dos percentuais dos Eventos Financeiros " + ;
            "deve ser igual a 100%.",                            ;
            "Soma atual: " + AllTrim(Transform(nPercTotal, "@E 999.99")) + "%";
        )
        lRet := .F.
    EndIf
    
    // =====================================================
    // VALIDAÇÃO 2: Deve ter exatamente UM evento para NF
    // =====================================================
    If lRet .And. lTemDados .And. nQtdEventoNF == 0
       oModel:SetErrorMessage(;
            "CNBDETAIL",                                           ;
            "CNB_ITEM",                                            ;
            "CNBDETAIL",                                           ;
            "CNB_ITEM",                                            ;
            "A300EVNFOB",                                          ;
            "É obrigatório que um Evento Financeiro esteja " + ;
            "marcado  NF igual a Sim (ZZ3_EVENF = 'S').",         ;
            "Marque exatamente UM evento Nota Fiscal." ;
        )
        lRet := .F.
    ElseIf lRet .And. lTemDados .And. nQtdEventoNF > 1
       oModel:SetErrorMessage(;
            "CNBDETAIL",                                           ;
            "CNB_ITEM",                                            ;
            "CNBDETAIL",                                           ;
            "CNB_ITEM",                                            ;
            "A300EVNFDUP",                                         ;
            "Apenas UM Evento Financeiro pode estar marcado " + ;
            "para  NF igual a Sim (ZZ3_EVENF = 'S').",                 ;
            "Quantidade atual: " + cValToChar(nQtdEventoNF) + ". Mantenha apenas um marcado." ;
        )
        lRet := .F.
    EndIf
    
    FWRestRows(aSaveLines)
    
Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} xA3RecZZ3
Recalcula todos os eventos financeiros (ZZ3) quando CNB_VLTOT é alterado

REGRAS:
1. Eventos PAGOS (ZZ3_DTPGTO preenchido): MANTÉM valor, recalcula %
2. Eventos NÃO PAGOS: Recalcula valor mantendo proporção relativa
3. Soma final dos percentuais = 100%

Gatilho: CNB_VLTOT ? Recalcula toda a ZZ3

@param oMdlGrid  - Model da grid CNBDETAIL
@param cId       - ID do campo (CNB_VLTOT)
@param xValue    - Novo valor total (CNB_VLTOT)
@param nLine     - Linha atual
@param xCurValue - Valor anterior

@return .T. - Sempre retorna verdadeiro

@author J.Carmo
@since 21/10/2025
/*/
//-------------------------------------------------------------------
User Function xA3RecZZ3(oMdlGrid, cId, xValue, nLine, xCurValue)
    Local oModel      := oMdlGrid:GetModel()
    Local oModelZZ3   := oModel:GetModel('ZZ3DETAIL')
    Local aSaveLines  := FWSaveRows()
    
    Local nNovoVlTotal := xValue  // Novo CNB_VLTOT
    Local nVlPagos     := 0       // Soma dos valores já pagos
    Local nVlRestante  := 0       // Valor disponível para não pagos
    Local nPercNaoPago := 0       // Soma % dos não pagos (original)
    
    Local aEventos     := {}      // Array com todos eventos
    Local nX           := 0
    Local nNovoValor   := 0
    Local nNovoPerc    := 0

    // =====================================================
    // ETAPA 1: Coletar informações dos eventos
    // =====================================================
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)
        
        If !oModelZZ3:IsDeleted()
            aAdd(aEventos, {;
                nX,;                                    // [1] Linha
                oModelZZ3:GetValue('ZZ3_DTPGTO'),;     // [2] Data pagamento
                oModelZZ3:GetValue('ZZ3_VLBASE'),;     // [3] Valor atual
                oModelZZ3:GetValue('ZZ3_PERCEN'),;     // [4] % atual
                !Empty(oModelZZ3:GetValue('ZZ3_DTPGTO'));  // [5] Está pago?
            })
            
            // Se já foi pago, soma no valor de pagos
            If !Empty(oModelZZ3:GetValue('ZZ3_DTPGTO'))
                nVlPagos += oModelZZ3:GetValue('ZZ3_VLBASE')
            Else
                // Soma percentual dos não pagos (proporção relativa)
                nPercNaoPago += oModelZZ3:GetValue('ZZ3_PERCEN')
            EndIf
        EndIf
    Next
    
    // =====================================================
    // ETAPA 2: Calcular valor disponível
    // =====================================================
    nVlRestante := nNovoVlTotal - nVlPagos
    
    // =====================================================
    // ETAPA 3: Recalcular cada evento
    // =====================================================
    For nX := 1 To Len(aEventos)
        oModelZZ3:GoLine(aEventos[nX][1])
        
        If aEventos[nX][5]  // Está PAGO?
            // ============================================
            // EVENTO PAGO: Mantém valor, recalcula %
            // ============================================
            nNovoValor := aEventos[nX][3]  // Mantém valor original
            nNovoPerc  := (nNovoValor / nNovoVlTotal) * 100
            
        Else
            // ============================================
            // EVENTO NÃO PAGO: Recalcula valor mantendo proporção
            // ============================================
            If nPercNaoPago > 0
                // Calcula novo valor baseado na proporção relativa
                nNovoValor := nVlRestante * (aEventos[nX][4] / nPercNaoPago)
                nNovoPerc  := (nNovoValor / nNovoVlTotal) * 100
            Else
                nNovoValor := 0
                nNovoPerc  := 0
            EndIf
        EndIf
        
        // ============================================
        // ATUALIZAR VALORES NO MODEL
        // ============================================
        If nNovoValor > 0 .and. nNovoPerc > 0
            oModelZZ3:setValue('ZZ3_PERCEN', nNovoPerc)
            oModelZZ3:setValue('ZZ3_VLBASE', nNovoValor)
        EndIf
        
        // Os gatilhos de ZZ3_VLBASE vão disparar automaticamente:
        // ? ZZ3_VLIMP (impostos)
        // ? ZZ3_VLLIQ (líquido)
    Next

    // =====================================================
    // RESTAURAR POSICIONAMENTO
    // =====================================================
    FWRestRows(aSaveLines)
    
Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc} xA3CalcFrete
Calcula o valor de frete do evento financeiro (ZZ3_VLFRET)
Rateio em cascata: Contrato ? Planilhas ? Itens ? Eventos

LÓGICA:
1. Divide CN9_ZTRANS entre planilhas proporcionalmente ao CNA_VLTOT
2. Divide frete da planilha entre itens proporcionalmente ao CNB_VLTOT
3. Divide frete do item entre eventos proporcionalmente ao ZZ3_PERCEN

Gatilho: ZZ3_PERCEN ? ZZ3_VLFRET

@param oMdlGrid  - Model da grid ZZ3DETAIL
@param cId       - ID do campo
@param xValue    - Percentual do evento (ZZ3_PERCEN)
@param nLine     - Linha atual
@param xCurValue - Valor anterior

@return nVlFrete - Valor do frete calculado

@author J.Carmo
@since 21/10/2025
/*/
//-------------------------------------------------------------------
User Function xA3CalcFrete(oMdlGrid, cId, xValue, nLine, xCurValue)

    Local oModel      := oMdlGrid:GetModel()
    Local oModelCNB   := oModel:GetModel('CNBDETAIL')
    Local aSaveLines  := FWSaveRows()
    
    Local nFreteItem     := 0  // CNB_ZTRANS - Valor do frete do item
    Local nPercEvento    := 0  // ZZ3_PERCEN - Percentual do evento
    Local nVlFrete       := 0  // Valor do frete proporcional ao evento
    
    // =====================================================
    // PASSO 1: Obter frete do item atual
    // =====================================================
    nFreteItem := oModelCNB:GetValue('CNB_ZTRANS')
    
    // Se não tem frete no item, retorna 0
    If nFreteItem <= 0
        FWRestRows(aSaveLines)
        Return 0
    EndIf
    
    // =====================================================
    // PASSO 2: Obter percentual do evento
    // =====================================================
    nPercEvento := oMdlGrid:GetValue("ZZ3_PERCEN")
    
    // =====================================================
    // PASSO 3: Calcular frete proporcional ao evento
    // =====================================================
    nVlFrete := nFreteItem * (nPercEvento / 100)
    
    // =====================================================
    // RESTAURAR POSICIONAMENTO
    // =====================================================
    FWRestRows(aSaveLines)
    
Return nVlFrete

//-------------------------------------------------------------------
/*/{Protheus.doc} Z3VldEdit
Valida se pode editar os campos da ZZ3

REGRAS:
- Se vier de GATILHO (reajuste): SEMPRE permite
- Se vier do USUÁRIO:
  - Status deve ser "E" (Elaboração)
  - Data de pagamento (ZZ3_DTPGTO) deve estar vazia
  - Data prevista (ZZ3_DTPREV) deve ser >= data atual

Campos controlados: ZZ3_PERCEN, ZZ3_DTPREV, ZZ3_PGNET

@param cCampo - Nome do campo sendo validado

@return lValid - .T. permite, .F. bloqueia

@author J.Carmo
@since 21/10/2025
@history 09/12/2025 - J.Carmo - Adicionada validação de data prevista >= data atual
/*/
//-------------------------------------------------------------------
User Function Z3VldEdit(cCampo)
    Local oModel     := FWModelActive()
    Local oModelZZ3  := oModel:GetModel('ZZ3DETAIL')
    Local cStatus    := AllTrim(oModelZZ3:GetValue('ZZ3_STATUS'))
    Local dDtPgto    := oModelZZ3:GetValue('ZZ3_DTPGTO')
    Local dDtPrev    := Nil
    Local lValid     := .T.
    Local lGatilho   := .F.
    
    // =====================================================
    // VERIFICAR SE ESTÁ VINDO DE UM GATILHO
    // =====================================================
    lGatilho := FwIsInCallStack('xA3RecZZ3') .Or. ;  // Gatilho de reajuste CNB_VLTOT
                FwIsInCallStack('U_XA3RECZZ3')       // User Function do gatilho
    
    // Se vier de gatilho, SEMPRE permite
    If lGatilho
        Return .T.
    EndIf
    
    // =====================================================
    // VALIDAR EDIÇÃO MANUAL DO USUÁRIO
    // =====================================================
    
    // Regra 1: Status deve ser "E" (Elaboração)
    If cStatus != "E"
        Help(" ", 1, "Z3STATUSBLOQ",, ;
             "Evento financeiro não está em Elaboração!" + CRLF + ;
             "Status atual: " + cStatus + CRLF + CRLF + ;
             "Apenas eventos com Status 'E' podem ser editados.", ;
             1, 0)
        lValid := .F.
    EndIf
    
    // Regra 2: Data de pagamento deve estar vazia
    If lValid .And. !Empty(dDtPgto)
        Help(" ", 1, "Z3PAGOBLOQ",, ;
             "Evento financeiro já possui pagamento!" + CRLF + ;
             "Data Pagamento: " + DToC(dDtPgto) + CRLF + CRLF + ;
             "Eventos pagos não podem ser editados.", ;
             1, 0)
        lValid := .F.
    EndIf
    
    // =====================================================
    // Regra 3: Data prevista deve ser >= data atual
    // Apenas valida quando o campo editado for ZZ3_DTPREV
    // =====================================================
    If lValid .And. Upper(AllTrim(cCampo)) == "ZZ3_DTPREV"
        dDtPrev := oModelZZ3:GetValue('ZZ3_DTPREV')
        
        If !Empty(dDtPrev) .And. dDtPrev < Date()
            Help(" ", 1, "Z3DTPREVINV",, ;
                 "Data Prevista inválida!" + CRLF + CRLF + ;
                 "Data informada: " + DToC(dDtPrev) + CRLF + ;
                 "Data atual: " + DToC(Date()) + CRLF + CRLF + ;
                 "A Data Prevista não pode ser anterior à data de hoje.", ;
                 1, 0)
            lValid := .F.
        EndIf
    EndIf
    
Return lValid

//-------------------------------------------------------------------
/*/{Protheus.doc} xA3RecTS
Recalcula impostos (ZZ3_VLIMP) quando TES muda

REGRAS:
- Só recalcula se situação = "02" (Elaboração)
- Só recalcula se NÃO tiver nenhum evento pago
- Se tiver evento pago: NÃO FAZ NADA

@author J.Carmo
@since 24/10/2025
/*/
//-------------------------------------------------------------------
User Function xA3RecTS(oMdlGrid, cId, xValue, nLine, xCurValue)
    Local oModel     := oMdlGrid:GetModel()
    Local oModelCN9  := oModel:GetModel('CN9MASTER')
    Local oModelZZ3  := oModel:GetModel('ZZ3DETAIL')
    Local oView      := FWViewActive()
    Local aSaveLines := FWSaveRows()
    
    Local cSituacao    := ""
    Local nX           := 0
    Local lTemPago     := .F.
    Local dDtPgto      := CToD("")
    Local nNovoVlImp   := 0
    Local nVlBase      := 0
    Local nValLiq      := 0    
    // =====================================================
    // VALIDAÇÃO 1: Verificar situação do contrato
    // =====================================================
    cSituacao := AllTrim(oModelCN9:GetValue('CN9_SITUAC'))
    
    If cSituacao != "02"  // Não é Elaboração
        FWRestRows(aSaveLines)
        Return .T.
    EndIf
    
    // =====================================================
    // VALIDAÇÃO 2: Verificar se tem algum evento pago
    // =====================================================
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)
        
        If !oModelZZ3:IsDeleted()
            dDtPgto := oModelZZ3:GetValue('ZZ3_DTPGTO')
            
            If !Empty(dDtPgto)
                lTemPago := .T.
                Exit
            EndIf
        EndIf
    Next
    
    // Se tem evento pago, não faz nada
    If lTemPago
        FWRestRows(aSaveLines)
        Return .T.
    EndIf
    
    // =====================================================
    // RECALCULAR: Só chega aqui se Elaboração E sem pagos
    // =====================================================
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)
        
        If !oModelZZ3:IsDeleted()
            nVlBase := oModelZZ3:GetValue('ZZ3_VLBASE')
            nNovoVlImp := U_xA3CalcImp(nVlBase)
            oModelZZ3:SetValue('ZZ3_VLIMP', nNovoVlImp)
            nValLiq := U_xA3ValLiq(oModelZZ3, /*cId*/,  oModelZZ3:GetValue('ZZ3_VLBASE'), /*nLine*/, /*xCurValue*/)
            oModelZZ3:SetValue('ZZ3_VLLIQ', nValLiq)
        EndIf
    Next
    
    FWRestRows(aSaveLines)
    oView:Refresh('VIEW_ZZ3')
Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc} xA3RecFrete
Recalcula frete (ZZ3_VLFRET) quando frete do item muda

REGRAS:
- Só recalcula se situação = "02" (Elaboração)
- Só recalcula se NÃO tiver nenhum evento pago
- Se tiver evento pago: NÃO FAZ NADA

@author J.Carmo
@since 24/10/2025
/*/
//-------------------------------------------------------------------
User Function xA3RecFrete(oMdlGrid, cId, xValue, nLine, xCurValue)
    Local oModel     := oMdlGrid:GetModel()
    Local oModelCN9  := oModel:GetModel('CN9MASTER')
    Local oModelZZ3  := oModel:GetModel('ZZ3DETAIL')
    Local oView      := FWViewActive()
    Local aSaveLines := FWSaveRows()
    
    Local cSituacao     := ""
    Local nX            := 0
    Local lTemPago      := .F.
    Local dDtPgto       := CToD("")
    Local nFreteItem    := xValue
    Local nPercEvento   := 0
    Local nNovoVlFrete  := 0
    Local nValLiq      := 0
    // =====================================================
    // VALIDAÇÃO 1: Verificar situação do contrato
    // =====================================================
    cSituacao := AllTrim(oModelCN9:GetValue('CN9_SITUAC'))
    
    If cSituacao != "02"  // Não é Elaboração
        FWRestRows(aSaveLines)
        Return .T.
    EndIf
    
    // =====================================================
    // VALIDAÇÃO 2: Verificar se tem algum evento pago
    // =====================================================
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)
        
        If !oModelZZ3:IsDeleted()
            dDtPgto := oModelZZ3:GetValue('ZZ3_DTPGTO')
            
            If !Empty(dDtPgto)
                lTemPago := .T.
                Exit
            EndIf
        EndIf
    Next
    
    // Se tem evento pago, não faz nada
    If lTemPago
        FWRestRows(aSaveLines)
        Return .T.
    EndIf
    
    // =====================================================
    // RECALCULAR: Só chega aqui se Elaboração E sem pagos
    // =====================================================
    For nX := 1 To oModelZZ3:Length()
        oModelZZ3:GoLine(nX)
        
        If !oModelZZ3:IsDeleted()
            nPercEvento := oModelZZ3:GetValue('ZZ3_PERCEN')
            
            If nFreteItem > 0 .And. nPercEvento > 0
                nNovoVlFrete := nFreteItem * (nPercEvento / 100)
            Else
                nNovoVlFrete := 0
            EndIf
            
            oModelZZ3:SetValue('ZZ3_VLFRET', nNovoVlFrete)

            nValLiq := U_xA3ValLiq(oModelZZ3, /*cId*/,  oModelZZ3:GetValue('ZZ3_VLBASE'), /*nLine*/, /*xCurValue*/)
            oModelZZ3:SetValue('ZZ3_VLLIQ', nValLiq)

        EndIf
    Next
    
    FWRestRows(aSaveLines)
    oView:Refresh('VIEW_ZZ3')
Return .T.
