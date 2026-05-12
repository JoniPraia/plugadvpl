---
description: 6 padrões de refactor comuns em ADVPL/TLPP — DbSeek loop, Posicione repetido, IFs hardcoded, AxCadastro→MVC, string concat em loop, RecLock sem Begin Transaction. Inclui before/after e quando NÃO aplicar. Use quando o usuário pede "melhorar", "refatorar" ou "está lento" um fonte ADVPL.
---

# advpl-refactoring — Padrões de refactor com before/after

Esses 6 padrões cobrem ~80% das oportunidades de refactor em fontes ADVPL legados
(Protheus R10/R11) ou customizações novas escritas sem o conhecimento dos idiomas
modernos. Cada um tem **gatilho de detecção** (como achar via `plugadvpl`),
**before/after** lado-a-lado e **quando NÃO refatorar** (custo pode superar valor).

## Workflow

1. **Antes de propor refactor**: rode `/plugadvpl:arch <arquivo>` pra entender escopo,
   `/plugadvpl:callers <funcao>` pra impacto downstream, e `/plugadvpl:lint <arquivo>`
   pra confirmar que há findings.
2. **Critical/error do lint geralmente é refactor candidato** — comece pelos worst offenders.
3. **Refactor um padrão por commit**. Misturar 3 refactors num diff só gera review impossível
   e bug oculto.
4. **Depois do refactor**: `/plugadvpl:reindex <arquivo>` + `/plugadvpl:lint <arquivo>` pra
   confirmar que não introduziu regressão (findings que não existiam antes).

---

## 1. DbSeek em loop → SQL embarcado (anti-N+1)

**Gatilho** — `/plugadvpl:lint --regra PERF-002`. Ou simplesmente: vê `DbSeek` dentro
de `For/While`/iteração em alias com muitas linhas, isso é N round-trips no banco.

**Por que refatorar:** N consultas DbSeek viram N idas ao DBAccess. Reescrever como JOIN
em SQL embarcado faz 1 ida só. Em produção típica (1.000 itens), reduz tempo de minutos
para segundos.

**Before**

```advpl
DbSelectArea("SC6")
DbSetOrder(1)
DbSeek(xFilial("SC6") + cPedido)
While !Eof() .And. SC6->C6_NUM == cPedido
    // Pra cada item, busca preço/saldo na SB1
    DbSelectArea("SB1")
    DbSetOrder(1)
    If DbSeek(xFilial("SB1") + SC6->C6_PRODUTO)
        nPreco := SB1->B1_PRV1
        cDesc  := SB1->B1_DESC
    EndIf
    DbSelectArea("SC6")
    SC6->(DbSkip())
EndDo
```

**After**

```advpl
BeginSql Alias "QRY"
    SELECT SC6.C6_PRODUTO, SC6.C6_QTDVEN,
           SB1.B1_PRV1, SB1.B1_DESC
      FROM %table:SC6% SC6
      LEFT JOIN %table:SB1% SB1
             ON SB1.B1_FILIAL  = %xfilial:SB1%
            AND SB1.B1_COD     = SC6.C6_PRODUTO
            AND SB1.%notDel%
     WHERE SC6.C6_FILIAL = %xfilial:SC6%
       AND SC6.C6_NUM    = %exp:cPedido%
       AND SC6.%notDel%
EndSql
TCSetField("QRY", "B1_PRV1", "N", 12, 4)

While !QRY->(Eof())
    nPreco := QRY->B1_PRV1
    cDesc  := QRY->B1_DESC
    QRY->(DbSkip())
EndDo
QRY->(DbCloseArea())
```

**Quando NÃO refatorar:**
- Loop tem **menos de 10 iterações** garantidas — overhead de escrever SQL não compensa.
- Lógica entre DbSeeks é **muito complexa** (15+ ramificações) — fica ilegível em SQL.

---

## 2. `Posicione()` repetido → cache em variável

**Gatilho** — `/plugadvpl:grep "Posicione\("`. Procure múltiplos `Posicione()` na MESMA
função buscando o MESMO alias/chave.

**Por que refatorar:** `Posicione()` é uma função-wrapper que faz SaveArea + DbSelectArea
+ DbSetOrder + DbSeek + RestArea por baixo. Cada chamada custa ~5-10ms. 3 chamadas iguais
= 30ms desperdiçados. Pior em loop.

**Before**

```advpl
cNomeCli := Posicione("SA1", 1, xFilial("SA1") + cCodigo, "A1_NOME")
nLimite  := Posicione("SA1", 1, xFilial("SA1") + cCodigo, "A1_LC")
cTipo    := Posicione("SA1", 1, xFilial("SA1") + cCodigo, "A1_TIPO")
```

**After**

```advpl
// Faz 1 posicionamento, lê todos os campos da MEMÓRIA do alias.
cNomeCli := ""
nLimite  := 0
cTipo    := ""
DbSelectArea("SA1")
DbSetOrder(1)
If MsSeek(xFilial("SA1") + cCodigo)
    cNomeCli := SA1->A1_NOME
    nLimite  := SA1->A1_LC
    cTipo    := SA1->A1_TIPO
EndIf
```

**Variante com `FwFwmGetValueByID` / FWFormStruct (MVC):** se você está em ModelDef,
prefira `oModel:GetValue(...)` em vez de `Posicione`.

**Quando NÃO refatorar:**
- Você precisa **APENAS UM** campo e está em código que não é hotpath.
- Lógica intermediária pode invalidar o alias (outra função muda WorkArea no meio).

---

## 3. Lista de `If` hardcoded → tabela SX5/SX6 ou User Function central

**Gatilho** — `/plugadvpl:grep "^\s*If\s.*=="` em arquivo com 10+ matches; ou ramificações
do tipo `If cCod == 'A' .Or. cCod == 'B' .Or. ...` com listas de literais.

**Por que refatorar:** Hardcoded é doloroso pra mudar (precisa de compilação + deploy).
Em Protheus a infraestrutura **SX5** (tabela genérica) e **SX6** (parâmetros MV_*)
existem exatamente pra isso.

**Before**

```advpl
// 47 IFs hardcoded pra descobrir grupo do produto
Static Function _GrupoProduto(cCod)
    Local cGrupo := ""
    If Left(cCod, 2) == "01"
        cGrupo := "ELETRO"
    ElseIf Left(cCod, 2) == "02"
        cGrupo := "MOVEIS"
    ElseIf Left(cCod, 2) == "03"
        cGrupo := "ROUPAS"
    // ... mais 44 ramificações
    EndIf
Return cGrupo
```

**After** — opção A: SX5 (tabela genérica)

```advpl
// Cadastra na SX5 (Configurador) tabela "ZG" = grupos por prefixo
// X5_CHAVE = '01' → X5_DESCRI = 'ELETRO', etc.
Static Function _GrupoProduto(cCod)
    Local cPrefixo := Left(cCod, 2)
    Local cGrupo   := ""
    DbSelectArea("SX5")
    DbSetOrder(1)
    If MsSeek(xFilial("SX5") + "ZG" + cPrefixo)
        cGrupo := AllTrim(SX5->X5_DESCRI)
    EndIf
Return cGrupo
```

**After** — opção B: User Function central + DEFINE

```advpl
// Em ZUTILS.prw — função compartilhada, mudança em 1 lugar
User Function GrpProd(cCod)
    Local cPrefixo := Left(cCod, 2)
    Local cGrupo   := ""
    Do Case
        Case cPrefixo == "01"  ; cGrupo := "ELETRO"
        Case cPrefixo == "02"  ; cGrupo := "MOVEIS"
        // ...
    EndCase
Return cGrupo
```

**Quando NÃO refatorar:**
- Lista tem **5 entradas ou menos** que **nunca mudam** — hardcoded é OK.
- Performance crítica em hotpath de loop massivo — `Do Case` é mais rápido que `DbSeek` em SX5.

---

## 4. `AxCadastro` / `Modelo2` / `Modelo3` → MVC (MenuDef/ModelDef/ViewDef)

**Gatilho** — `/plugadvpl:lint --regra MOD-004`.

**Por que refatorar:** AxCadastro e Modelo2/3 são wrappers procedurais legados que
não plugam no framework MVC moderno (eventos, validações cruzadas, FWMVCRotAuto pra
testes automatizados, multi-camada Tela/Modelo/View). Customizações novas em R12+
**devem** ser MVC.

**Before**

```advpl
User Function ZA1CAD()
    Local cAlias := "ZA1"
    Local aRotina := { ...; }
    DbSelectArea(cAlias)
    DbSetOrder(1)
    AxCadastro(cAlias, "Cadastro Customizado", "AllwaysTrue()", "AllwaysTrue()")
Return
```

**After** (esqueleto MVC — três Static Functions)

```advpl
#Include 'Protheus.ch'
#Include 'FWMVCDef.ch'

User Function ZA1MVC()
    Local oBrw := FWMBrowse():New()
    oBrw:SetAlias("ZA1")
    oBrw:SetDescription("Cadastro Customizado")
    oBrw:Activate()
Return

Static Function MenuDef()
    Local aRotina := {}
    aAdd(aRotina, {"Pesquisar"  , "PesqBrw"        , 0, 1})
    aAdd(aRotina, {"Visualizar" , "FWVIEWMODELO('VIEWDEF.ZA1MVC')", 0, 2})
    aAdd(aRotina, {"Incluir"    , "FWEXECVIEW('Inclusao', 'VIEWDEF.ZA1MVC', 3)", 0, 3})
    aAdd(aRotina, {"Alterar"    , "FWEXECVIEW('Alteracao', 'VIEWDEF.ZA1MVC', 4)", 0, 4})
    aAdd(aRotina, {"Excluir"    , "FWEXECVIEW('Exclusao', 'VIEWDEF.ZA1MVC', 5)", 0, 5})
Return aRotina

Static Function ModelDef()
    Local oStru := FWFormStruct(1, "ZA1")
    Local oModel := MPFormModel():New("ZA1MVC", /*bPre*/, /*bPos*/, /*bCommit*/)
    oModel:AddFields("ZA1MASTER", /*cOwner*/, oStru)
    oModel:SetDescription("Cadastro Customizado ZA1")
Return oModel

Static Function ViewDef()
    Local oModel := FWLoadModel("ZA1MVC")
    Local oStru  := FWFormStruct(2, "ZA1")
    Local oView  := FWFormView():New()
    oView:SetModel(oModel)
    oView:AddField("ZA1MASTER_VIEW", oStru, "ZA1MASTER")
    oView:CreateHorizontalBox("MAIN", 100)
    oView:SetOwnerView("ZA1MASTER_VIEW", "MAIN")
Return oView
```

Veja `[[advpl-mvc-avancado]]` pra padrões avançados (eventos, FWMVCRotAuto).

**Quando NÃO refatorar:**
- Cadastro **já está em produção** há anos sem queixa e ninguém pediu mudança — refactor
  cego pode introduzir bug numa rotina estável. Espere o próximo bug/feature pra fazer
  junto.

---

## 5. Concatenação de string em loop → array + `Array2String`

**Gatilho** — `/plugadvpl:lint --regra PERF-004`. Ou: `+=` ou `+` aplicado a string
dentro de While/For com 100+ iterações.

**Por que refatorar:** Em ADVPL, string é imutável. Cada `cVar += "x"` aloca string nova,
copia conteúdo antigo + "x", e descarta o anterior. 1.000 concatenações = 1.000 alocações,
500.000 chars copiados. Acumular em array e fazer 1 join no final é O(n) em vez de O(n²).

**Before**

```advpl
Local cCsv := ""
DbSelectArea("SA1")
DbGoTop()
While !Eof()
    cCsv += AllTrim(SA1->A1_COD) + ";"
    cCsv += AllTrim(SA1->A1_NOME) + ";"
    cCsv += DtoC(SA1->A1_DTCAD) + Chr(13) + Chr(10)
    SA1->(DbSkip())
EndDo
```

**After**

```advpl
Local aLinhas := {}
DbSelectArea("SA1")
DbGoTop()
While !Eof()
    aAdd(aLinhas, AllTrim(SA1->A1_COD)  + ";" + ;
                  AllTrim(SA1->A1_NOME) + ";" + ;
                  DtoC(SA1->A1_DTCAD))
    SA1->(DbSkip())
EndDo
cCsv := FwArrayJoin(aLinhas, Chr(13) + Chr(10))
// (em versões anteriores ao FwArrayJoin existir, usar aJoin ou loop com Replace)
```

**Quando NÃO refatorar:**
- Loop com **< 50 iterações** — diferença é imperceptível.
- Você precisa do **estado parcial** da string a cada iteração — array não te dá isso barato.

---

## 6. `RecLock` solto → `Begin Transaction` block

**Gatilho** — `/plugadvpl:lint --regra BP-001` e `BP-005`. RecLocks em múltiplos aliases
sem proteção transacional.

**Por que refatorar:** Sem `Begin Transaction/End Transaction`, se a primeira gravação
commitar e a segunda falhar, fica estado inconsistente (ex.: pedido sem item). Begin
Transaction garante atomicidade — se algo dá erro no meio, faz rollback automático.

**Before**

```advpl
RecLock("SC5", .T.)
SC5->C5_FILIAL := xFilial("SC5")
SC5->C5_NUM    := cNumPed
SC5->C5_CLIENTE := cCliente
SC5->(MsUnlock())   // já commitou

// Se ZErrEnter() der erro aqui, SC5 ficou orfao
ZErrEnter()

RecLock("SC6", .T.)
SC6->C6_FILIAL := xFilial("SC6")
SC6->C6_NUM    := cNumPed
SC6->C6_ITEM   := "01"
SC6->(MsUnlock())
```

**After**

```advpl
Begin Transaction
    RecLock("SC5", .T.)
    SC5->C5_FILIAL  := xFilial("SC5")
    SC5->C5_NUM     := cNumPed
    SC5->C5_CLIENTE := cCliente
    SC5->(MsUnlock())

    ZErrEnter()   // se der erro aqui, transaction faz rollback de SC5 tambem

    RecLock("SC6", .T.)
    SC6->C6_FILIAL := xFilial("SC6")
    SC6->C6_NUM    := cNumPed
    SC6->C6_ITEM   := "01"
    SC6->(MsUnlock())
End Transaction
```

**Combinado com `Begin Sequence/Recover/End`** para captura de erro:

```advpl
Begin Sequence
    Begin Transaction
        // ... gravações
    End Transaction
Recover Using oErr
    ConOut("Erro: " + oErr:Description)
    DisarmTransaction()  // garante rollback explicito
End Sequence
```

**Quando NÃO refatorar:**
- Apenas **1 alias** sendo gravado e o erro é tratado em VALID — RecLock+MsUnlock simples basta.
- Função roda dentro de transaction maior (chamadora já abriu) — `Begin Transaction`
  aninhado tem semântica diferente em alguns DBs; verifique.

---

## Workflow de proposta de refactor

Quando o usuário pede "melhorar" / "está lento" / "tem boa prática aqui?":

1. `/plugadvpl:arch <arquivo>` — entende a função, tabelas, deps.
2. `/plugadvpl:lint <arquivo> --severity warning` — colhe candidatos.
3. Para cada finding, identifique qual dos 6 padrões aplica.
4. Mostre o **diff curto** (não reescreva o arquivo inteiro) com antes/depois.
5. Liste **caveats**: testes a rodar, impacto em callers, deps.
6. Após aplicar, `/plugadvpl:reindex` + `/plugadvpl:lint` pra confirmar.

## Anti-padrões de refactor

- **Refactor sem benchmark / sem caso de teste:** "achei que ia ser melhor" não é refactor,
  é mudança gratuita.
- **Refactor com 5 padrões num diff só:** review impossível, bug oculto certo.
- **Modernizar AxCadastro em rotina estável sem demanda:** se está em produção e funciona,
  espere o próximo trigger (bug, nova feature) pra fazer junto.
- **Substituir Posicione por DbSeek sem testar `eof`:** Posicione protege contra alias
  inválido; DbSeek bruto não.

## Comandos plugadvpl relacionados

- `/plugadvpl:lint <arquivo> --severity warning` — colhe candidatos de refactor.
- `/plugadvpl:arch <arquivo>` — contexto antes de propor mudanças.
- `/plugadvpl:callers <funcao>` — impacto downstream de mudar a assinatura.
- `/plugadvpl:grep "Posicione\("` — busca uso de funções a refatorar.
- `[[advpl-code-review]]` — as 24 regras que disparam refactor candidate.
- `[[advpl-mvc]]` / `[[advpl-mvc-avancado]]` — padrão MVC pra modernização.
- `[[advpl-embedded-sql]]` — SQL embarcado pra refactor de DbSeek loops.
