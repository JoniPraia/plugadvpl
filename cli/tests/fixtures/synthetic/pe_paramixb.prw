#include "totvs.ch"

/*/{Protheus.doc} ANCTB102GR
O ponto de entrada ANCTB102GR utilizado Antes a gravacao dos dados da
tabela de lancamento. Nome canonico TOTVS — http://tdn.totvs.com/...
/*/
User Function ANCTB102GR()
    Local cAlias  := PARAMIXB[1]
    Local nOpc    := PARAMIXB[2]
    Local lAlt    := PARAMIXB[3]
    Local cFonte  := PARAMIXB[4]
    Local aDados  := PARAMIXB[5]
    ConOut("Antes da gravacao da tabela de lancamento.")
Return .T.
