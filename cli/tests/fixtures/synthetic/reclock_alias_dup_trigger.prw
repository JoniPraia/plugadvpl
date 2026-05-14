#include "totvs.ch"

User Function ZH3DupTrigger()
    // Bug #9 do QA report: ZH3->(RecLock("ZH3",.t.)) casava com AMBOS
    // _RECLOCK_OPEN_RE (literal RecLock) E _RECLOCK_VIA_ALIAS_RE (alias->RecLock),
    // gerando 2 opens pra 1 RecLock real → BP-001 reporta a linha 2x.
    ZH3->(RecLock("ZH3",.t.))
    Replace ZH3->ZH3_FILIAL With "01"
    // Sem MsUnlock — gera BP-001. Antes: 2 findings na mesma linha. Depois: 1.
Return
