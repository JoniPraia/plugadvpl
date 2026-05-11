#Include "protheus.ch"

User Function ZBROWSE()
    Local oBrowse := FWFormBrowse():New()
    oBrowse:SetAlias("SA1")
    oBrowse:SetDescription("Cadastro de Clientes (clássico)")
    oBrowse:DisableDetails()
    oBrowse:Activate()
Return Nil

Static Function MenuDef()
    Local aRotina := {}
    aAdd(aRotina, {"Pesquisar", "AxPesqui", 0, 1})
    aAdd(aRotina, {"Incluir",   "AxInclui", 0, 3})
Return aRotina
