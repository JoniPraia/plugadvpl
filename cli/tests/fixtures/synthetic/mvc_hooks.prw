#Include "protheus.ch"
#Include "fwmvcdef.ch"

Static Function ModelDef()
    Local oModel  := MPFormModel():New("ZHKM")
    Local oStruct := FWFormStruct(1, "SA1")
    Local bCommit := {|oM| ZGravar(oM)}
    Local bTudoOk := {|oM| ZValidar(oM)}
    Local bLineOk := {|oM| .T.}
    oModel:AddFields("SA1MASTER", , oStruct)
    oModel:SetCommit(bCommit)
    oModel:SetVldActivate(bTudoOk)
Return oModel

Static Function ZGravar(oModel)
Return .T.

Static Function ZValidar(oModel)
Return .T.
