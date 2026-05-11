#Include "protheus.ch"
#Include "fwmvcdef.ch"

User Function ZACADEMP()
    Local oBrowse := FWmBrowse():New()
    oBrowse:SetAlias("SA1")
    oBrowse:SetMenuDef("ZACADEMP")
    oBrowse:Activate()
Return Nil

Static Function MenuDef()
    Local aRotina := {}
    aAdd(aRotina, {"Pesquisar", "AxPesqui", 0, 1})
    aAdd(aRotina, {"Visualizar", "VIEWDEF.ZACADEMP", 0, 2})
    aAdd(aRotina, {"Incluir",   "VIEWDEF.ZACADEMP", 0, 3})
    aAdd(aRotina, {"Alterar",   "VIEWDEF.ZACADEMP", 0, 4})
    aAdd(aRotina, {"Excluir",   "VIEWDEF.ZACADEMP", 0, 5})
Return aRotina

Static Function ModelDef()
    Local oModel   := MPFormModel():New("ZACADEMPM")
    Local oStruct  := FWFormStruct(1, "SA1")
    Local bCommit  := {|oM| .T.}
    Local bTudoOk  := {|oM| .T.}
    oModel:AddFields("SA1MASTER", , oStruct)
    oModel:SetCommitWhenActive(.T.)
    oModel:SetVldActivate({|oM| .T.})
Return oModel

Static Function ViewDef()
    Local oModel := FWLoadModel("ZACADEMP")
    Local oStruct := FWFormStruct(2, "SA1")
    Local oView   := FWFormView():New()
    oView:SetModel(oModel)
    oView:AddField("SA1MASTER", oStruct)
Return oView
