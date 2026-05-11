# MATXFIS – Guia de Utilização (TOTVS 2013)

> Motor de cálculo de impostos do ERP Protheus. Centraliza todos os cálculos fiscais em um único ponto do sistema.

---

## Índice

- [1. Introdução](#1-introdução)
- [2. Funções](#2-funções)
  - [2.1 MaFisFound](#21-mafisfound)
  - [2.2 MaFisSave](#22-mafissave)
  - [2.3 MaFisRestore](#23-mafisrestore)
  - [2.4 MaFisClear](#24-mafisclear)
  - [2.5 MaFisEnd](#25-mafisend)
  - [2.6 MaFisNFCab](#26-mafisfcab)
  - [2.7 MaFisIni](#27-mafisini)
  - [2.8 MaFisIniLoad](#28-mafisiniload)
  - [2.9 MaFisAdd](#29-mafisadd)
  - [2.10 MaFisLoad](#210-mafisload)
  - [2.11 MaFisEndLoad](#211-mafisendload)
  - [2.12 MaFisRet](#212-mafisret)
  - [2.13 MaFisSXRef](#213-mafissxref)
  - [2.14 MaFisRelImp](#214-mafisrelimp)
  - [2.15 MaFisRef](#215-mafisref)
  - [2.16 MaFisAlt](#216-mafisalt)
  - [2.17 MaFisDel](#217-mafisdel)
  - [2.18 MaColsToFis](#218-macolstofis)
  - [2.19 MaFisToCols](#219-mafistocols)
  - [2.20 MaFisRecal](#220-mafisrecal)
  - [2.21 MaFisWrite](#221-mafiswrite)
  - [2.22 MaFisAtuSF3](#222-mafisatusf3)
  - [2.23 MaFisIniNF](#223-mafisininf)
  - [2.24 MaFisBrwLivro](#224-mafisbrwlivro)
  - [2.25 MaFisRodape](#225-mafisrodape)

---

## 1. Introdução

A `MATXFIS.PRX` é um programa que possui um conjunto de funções que administram arrays `STATICS` para calcular todos os impostos do ERP Protheus.

Com a centralização foi possível atualizar a legislação dos impostos de todo o sistema em apenas um ponto. Para isso foram criados recursos chamados de **REFERÊNCIA FISCAL**: uma `DEFINE` contida no fonte `MATXDEF.CH`, onde cada referência leva um nome com prefixo e sufixo que facilitam a identificação do conteúdo.

**Exemplos de referências fiscais:**
- `NF_DESCONTO` – valor do desconto no cabeçalho da nota
- `IT_BASEIPI` – valor da base de IPI no item da nota
- `LF_VALCONT` – Valor Contábil da nota gravado no Livro Fiscal

Este guia explica como desenvolver e dar manutenção em aplicações que utilizem o motor de impostos MATXFIS, garantindo que o desenvolvimento seja realizado de forma correta e com melhor desempenho possível.

---

## 2. Funções

Cada função é apresentada com:
- **Descrição** — contexto e objetivo
- **Parâmetros** — tabela com ordem, nome, tipo e descrição
- **Retorno** — o que a função retorna
- **Como e Onde Usar** — orientações práticas
- **Exemplos de Uso** — trechos de código ADVPL

---

### 2.1 MaFisFound

**Assinatura:** `MaFisFound(cReferencia, nItem)`

#### Descrição

Verifica a existência de elementos nos arrays `aNFCab` e `aNFItem` da MATXFIS. Conforme o parâmetro `cReferencia` ("NF" ou "IT"), a função retorna `.T.` ou `.F.` se houver elementos nos arrays.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cReferencia | Caracter | `"NF"` – pesquisa no array `aNFCab` (cabeçalho); `"IT"` – pesquisa no array `aNFItem` (itens) |
| 02 | nItem | Numérico | Verifica se o item passado existe no `aNFItem` (só quando `cReferencia = "IT"`) |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | lFound | Lógico | `.T.` se encontrado; `.F.` se não encontrado |

#### Como e Onde Usar

Utilizar **ANTES** de iniciar a carga dos dados do documento fiscal via `MaFisIni`, `MaFisAdd` e `MaFisIniLoad`, para evitar que o mesmo item seja carregado mais de uma vez.

> **ATENÇÃO:** NUNCA utilizar dentro de laços (`While`, `For/Next`, `aEval()`) onde mais de uma verificação seja necessária — o custo é alto.

#### Exemplos de Uso

```advpl
If !MaFisFound("NF")
    MaFisIni( cFornecedor, cLoja, "F", "N", Nil, aRelImp,, .T. )
EndIf

// Validando a alteração de um item da MsGetDados() via valid ou gatilho
If MaFisFound("IT", N)
    MaFisAlt("IT_PRCUNI", aCols[n][nPPreco], n)
EndIf
```

---

### 2.2 MaFisSave

**Assinatura:** `MaFisSave()`

#### Descrição

Salva o estado atual (todos os dados do documento fiscal carregado na MATXFIS) para uma área temporária. Permite liberar os arrays internos para uso de outro processo e restaurá-los depois.

> A MATXFIS trabalha com **apenas um documento fiscal por vez**.

#### Parâmetros

Não são necessários parâmetros.

#### Retorno

Não há retorno.

#### Como e Onde Usar

Usar quando for necessário carregar um novo documento fiscal por um instante, realizar um cálculo fiscal à parte, e depois retornar ao documento original. Exemplo: consulta de histórico de produtos ao incluir um pedido de compras.

#### Exemplos de Uso

```advpl
// Função utilizada no pedido de compras para consultar os últimos pedidos para o produto
Function A120ComView()
    Local nPosCod := aScan(aHeader, {|x| AllTrim(x[2]) == "C7_PRODUTO"})

    MaFisSave()  // Salva todos os arrays internos em área temporária
    MaFisEnd()

    If !AtIsRotina("MACOMVIEW")
        If !Empty(aCols[n][nPosCod])
            MaComView(aCols[n][nPosCod])  // Abre outra MATXFIS internamente
        EndIf
    EndIf

    MaFisRestore()  // Restaura os dados do pedido atual
Return
```

---

### 2.3 MaFisRestore

**Assinatura:** `MaFisRestore()`

#### Descrição

Restaura os arrays internos da MATXFIS com o estado salvo pela função `MaFisSave()`. Deve ser usada em conjunto com `MaFisSave()`.

#### Parâmetros

Não são necessários parâmetros.

#### Retorno

Não há retorno.

#### Como e Onde Usar

Usar após `MaFisSave()` para retornar ao documento fiscal original. Ver exemplo em `MaFisSave()`.

---

### 2.4 MaFisClear

**Assinatura:** `MaFisClear()`

#### Descrição

Limpa todos os itens e zera todos os totalizadores do cabeçalho dos arrays internos da MATXFIS. O array `aNFCab` preserva dados como Cliente, Loja, Tipo da NF, UF etc. — apenas os totalizadores são zerados.

#### Parâmetros

Não são necessários parâmetros.

#### Retorno

Não há retorno.

#### Como e Onde Usar

Usar quando for necessário recomeçar a incluir itens no mesmo documento fiscal sem reiniciar toda a MATXFIS. Exemplo: na carga do pedido de compras para o documento de entrada (MATA103), onde os itens são limpos a cada nova carga de pedidos.

#### Exemplos de Uso

```advpl
Function NfeTipo(cTipo, cFornece, cLoja, oSay, oFornece, oLoja)
    // Verifica se o tipo da NF foi alterado
    If MaFisFound("NF") .And. cTipo <> MaFisRet(, "NF_TIPONF")
        MaFisAlt("NF_CLIFOR", IIf(cTipo $ "DB", "C", "F"))
        MaFisAlt("NF_TIPONF", cTipo)
        aCols := {}       // Limpa os itens no Documento de Entrada
        MaFisClear()      // Limpa os itens no aNFItem e atualiza totais no aNFCab
        Eval(bRefresh)
    EndIf
Return
```

---

### 2.5 MaFisEnd

**Assinatura:** `MaFisEnd()`

#### Descrição

Finaliza todo o uso da MATXFIS limpando **TODOS** os seus arrays internos. Diferente da `MaFisClear()`, esta função encerra completamente o mecanismo.

#### Parâmetros

Não são necessários parâmetros.

#### Retorno

Não há retorno.

#### Como e Onde Usar

Usar **sempre** que todo o processo de cálculo, inclusão, alteração, exclusão, visualização e geração de impostos for finalizado. Seu uso é praticamente obrigatório para liberar a memória utilizada pelos arrays internos.

#### Exemplos de Uso

```advpl
// Trecho para obter o valor total do item com incidência de impostos
MaFisIni(cFORNECE, cLOJA, "F", "N", "R", aRefImp)  // Inicia a MATXFIS
MaFisIniLoad(1)                                      // Carrega o item 1 vazio

For nX := 1 To Len(aRefImp)
    // Carrega os dados fiscais do item a partir de uma tabela
    MaFisLoad(aRefImp[nX][3], FieldGet(FieldPos(aRefImp[nX][2])), 1)
Next nX

MaFisEndLoad(1)                          // Finaliza a carga e atualiza totalizadores
nTotItem := MaFisRet(1, "IT_TOTAL")     // Obtém o valor total do item calculado
MaFisEnd()                               // Finaliza e limpa todos os arrays internos
```

---

### 2.6 MaFisNFCab

**Assinatura:** `MaFisNFCab()`

#### Descrição

Retorna um array contendo todos os impostos calculados na MATXFIS no momento da chamada, com quebra por impostos + alíquotas.

#### Parâmetros

Não são necessários parâmetros.

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | aImpostosCalculados | Array | Array com TODOS os impostos calculados até o momento |

#### Como e Onde Usar

Usar quando a aplicação precisar apresentar ou utilizar como referência para cálculos os valores totalizados dos impostos calculados pela MATXFIS. Prefira `MaFisRet(,'NF_VALICM')` quando possível — use esta função quando `MaFisRet` não for viável.

#### Exemplos de Uso

```advpl
Function ImpostosdaNF()
    Local aImpostos := {}
    If MaFisFound("NF")
        aTodosImpostos := MaFisNFCab()
    EndIf
Return (aTodosImpostos)
```

---

### 2.7 MaFisIni

**Assinatura:**
```
MaFisIni(cCodCliFor, cLoja, cCliFor, cTipoNF, cTpCliFor, aRelImp, cTpComp, lInsere,
         cAliasP, cRotina, cTipoDoc, cEspecie, cCodProsp, cGrpCliFor, cRecolheISS,
         cCliEnt, cLojEnt, aTransp, lEmiteNF, lCalcIPI, cPedido, cCliFat, cLojcFat)
```

#### Descrição

Responsável por iniciar todo o processo da MATXFIS. Forma o array `aNFCab` (Cabeçalho do Documento Fiscal) através dos dados informados nos parâmetros, dados de SX6, tabelas SA1/SA2 e SED.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cCodCliFor | Caracter | Código Cliente/Fornecedor |
| 02 | cLoja | Caracter | Loja do Cliente/Fornecedor |
| 03 | cCliFor | Caracter | `C` = Cliente, `F` = Fornecedor |
| 04 | cTipoNF | Caracter | Tipo da NF: `"N"`, `"D"`, `"B"`, `"C"`, `"P"`, `"I"` |
| 05 | cTpCliFor | Caracter | Tipo do Cliente/Fornecedor |
| 06 | aRelImp | Array | Relação de Impostos suportados no arquivo |
| 07 | cTpComp | Caracter | Tipo de complemento |
| 08 | lInsere | Lógico | Permite incluir impostos no rodapé `.T.`/`.F.` |
| 09 | cAliasP | Caracter | Alias do Cadastro de Produtos (`"SBI"` p/ Front Loja) |
| 10 | cRotina | Caracter | Nome da rotina que está utilizando a função |
| 11 | cTipoDoc | Caracter | Tipo de documento |
| 12 | cEspecie | Caracter | Espécie do documento |
| 13 | cCodProsp | Caracter | Código e Loja do Prospect |
| 14 | cGrpCliFor | Caracter | Grupo Cliente |
| 15 | cRecolheISS | Caracter | Recolhe ISS |
| 16 | cCliEnt | Caracter | Código do cliente de entrega na NF de saída |
| 17 | cLojEnt | Caracter | Loja do cliente de entrega na NF de saída |
| 18 | aTransp | Array | Informações do transportador: `[01]` UF, `[02]` TPTRANS |
| 19 | lEmiteNF | Lógico | Se está emitindo NF ou cupom fiscal (SIGALOJA) |
| 20 | lCalcIPI | Lógico | Define se calcula IPI (SIGALOJA) |
| 21 | cPedido | Caracter | Pedido de Venda |
| 22 | cCliFat | Caracter | Cliente do Faturamento |
| 23 | cLojcFat | Caracter | Loja do Cliente do Faturamento |

> Novos parâmetros podem ser acrescentados — verificar o código fonte.

#### Retorno

Não há retorno.

#### Como e Onde Usar

Deve ser usada **obrigatoriamente** em qualquer operação com a MATXFIS, **sempre ANTES** da carga de qualquer item. Deve ser chamada **apenas uma vez** por documento fiscal.

Quando dados do cabeçalho precisarem ser alterados (ex: UF de origem), use `MaFisAlt()`:

```advpl
MaFisAlt("NF_UFORIGEM", cNovoUF)
```

#### Exemplos de Uso

```advpl
// 1) Geração de nota fiscal de saída – SIGAFAT – MATA461.PRX
dbSelectArea("SC5")
If nItem == 1
    MaFisIni(cCliEnt, SC5->C5_LOJAENT, If(SC5->C5_TIPO $ 'DB', "F", "C"),
             SC5->C5_TIPO, SC5->C5_TIPOCLI, aRelImp,,, 'MATA461',,,,
             cGrpCliTrb,,,, aTransp,,, SC6->C6_NUM, SC5->C5_CLIENTE, SC5->C5_LOJACLI)
EndIf
MaFisLoad("NF_ESPECIE", SF2->F2_ESPECIE)  // Complementa o cabeçalho
```

```advpl
// 2) Visualização de pedido de compras – SIGACOM – MATA120.PRX
MaFisIni(ca120Forn, ca120Loj, "F", "N", Nil, aRefImpos,, .T.,,,,,,,)
```

```advpl
// 3) Documento de entrada – SIGACOM – MATA103.PRW
If !MaFisFound("NF")
    MaFisIni(cA100For, cLoja, IIf(cTipo $ 'DB', "C", "F"), cTipo, Nil,
             MaFisRelImp("MT100", {"SF1","SD1"}),,!lVisual, NIL, NIL, NIL)
    If !Empty(cUfOrig)
        MaFisAlt("NF_UFORIGEM", cUfOrig)
    Endif
Else
    If !Empty(cUfOrig)
        MaFisAlt("NF_UFORIGEM", cUfOrig)
    Endif
EndIf
```

---

### 2.8 MaFisIniLoad

**Assinatura:** `MaFisIniLoad(nItem, aItemLoad, lEstorno)`

#### Descrição

Acrescenta um **NOVO item** no array interno `aNFItem` da MATXFIS. O item pode ser acrescentado em branco ou com dados básicos via `aItemLoad`. Pode também ser usado para estornar valores do item dos totalizadores do cabeçalho.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nItem | Numérico | Item do array `aNFItem` que deve ser inicializado |
| 02 | aItemLoad | Array | Array de otimização com dados básicos do item (ver abaixo) |
| 03 | lEstorno | Lógico | Se o item já existir, se deve estornar o valor dos totalizadores do `aNFCab` |

**Estrutura do aItemLoad:**

| Posição | Tipo | Conteúdo |
|---------|------|----------|
| [01] | Caracter | Código do produto |
| [02] | Caracter | Código da TES |
| [03] | Numérico | Valor do ISS do item |
| [04] | Numérico | Quantidade do item |
| [05] | Caracter | Número da NF Original |
| [06] | Caracter | Série da NF Original |
| [07] | Numérico | RecNo do SB1 |
| [08] | Numérico | RecNo do SF4 |
| [09] | Numérico | RecNo da NF Original (SD1/SD2) |
| [10] | Caracter | Lote do Produto |
| [11] | Caracter | Sub-Lote Produto |

#### Retorno

Não há retorno.

#### Como e Onde Usar

É a **melhor forma** de acrescentar um item na MATXFIS — prefira sempre em relação à `MaFisAdd()`, pois é mais rápida (não executa recálculo a cada item).

> Os itens gerados por `MaFisIniLoad()` devem estar **na mesma ordem** do `aCols`.

#### Exemplos de Uso

```advpl
// 1) Visualização de pedido de compras – SIGACOM – MATA120.PRX
MaFisIni(ca120Forn, ca120Loj, "F", "N", Nil, aRefImpos,, .T.,,,,,,,)

For nX := 1 to Len(aCols)
    MaFisIniLoad(nX,, .T.)  // Acrescenta item em branco no aNFItem
    For nY := 1 To Len(aHeader)
        cValid    := AllTrim(UPPER(aHeader[nY][6]))
        cRefCols  := MaFisGetRf(cValid)[1]
        If !Empty(cRefCols) .And. MaFisFound("IT", nX)
            MaFisLoad(cRefCols, aCols[nX][nY], nX)
        EndIf
    Next nY
    MaFisEndLoad(nX, 2)
Next nX
```

```advpl
// 2) Carregando item a partir de SD2
Local aRefImpos := MaFisRelImp('MT100', {"SD2"})
MaFisIniLoad(Len(aCols))
For nX := 1 To Len(aRefImpos)
    MaFisLoad(aRefImpos[nX][3], SD2->(FieldGet(FieldPos(aRefImpos[nX][2]))), Len(aColsX))
Next nX
MaFisEndLoad(Len(aCols), 2)
```

```advpl
// 3) Geração da NF de Saída – SIGAFAT – MATA461.PRX
MaFisIniLoad(nItem, { SC6->C6_PRODUTO,;   //IT_PRODUTO
                      SC6->C6_TES,;        //IT_TES
                      If(SF4->F4_ISS=="S", SC6->C6_CODISS, " "),; //IT_CODISS
                      aPvlNfs[nItem][4],;  //IT_QUANT
                      SC6->C6_NFORI,;      //IT_NFORI
                      SC6->C6_SERIORI,;    //IT_SERIORI
                      SB1->(RecNo()),;     //IT_RECNOSB1
                      SF4->(RecNo()),;     //IT_RECNOSF4
                      nRecOri,;            //IT_RECORI
                      SC6->C6_LOTECTL,;    //IT_LOTECTL
                      SC6->C6_NUMLOTE })   //IT_NUMLOTE
```

---

### 2.9 MaFisAdd

**Assinatura:**
```
MaFisAdd(cProduto, cTes, nQtd, nPrcUnit, nDesconto, cNFOri, cSEROri, nRecOri,
         nFrete, nDespesa, nSeguro, nFretAut, nValMerc, nValEmb, nRecSB1, nRecSF4,
         cNItem, nDesNTrb, nTara, cCfo, aNfOri, cConcept, nBaseVeic, nPLote, nPSubLot, nAbatIss)
```

#### Descrição

Inclui um novo item no `aNFItem` da MATXFIS **e** dispara o cálculo de TODOS os impostos, atualizando cabeçalho e folders a cada chamada. Por isso é mais lenta que `MaFisIniLoad()`.

> **Use apenas** quando documentos com 1 item ou quando atualização item a item for obrigatória. Para laços com múltiplos itens, **prefira `MaFisIniLoad()`**.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cProduto | Caracter | Código do Produto (**Obrigatório**) |
| 02 | cTes | Caracter | Código do TES (Opcional) |
| 03 | nQtd | Numérico | Quantidade (**Obrigatório**) |
| 04 | nPrcUnit | Numérico | Preço Unitário (**Obrigatório**) |
| 05 | nDesconto | Numérico | Valor do Desconto (Opcional) |
| 06 | cNFOri | Caracter | Número da NF Original (Devolução/Benef) |
| 07 | cSEROri | Caracter | Série da NF Original (Devolução/Benef) |
| 08 | nRecOri | Numérico | RecNo da NF Original no arq SD1/SD2 |
| 09 | nFrete | Numérico | Valor do Frete do Item (Opcional) |
| 10 | nDespesa | Numérico | Valor da Despesa do item (Opcional) |
| 11 | nSeguro | Numérico | Valor do Seguro do item (Opcional) |
| 12 | nFretAut | Numérico | Valor do Frete Autônomo (Opcional) |
| 13 | nValMerc | Numérico | Valor da Mercadoria (**Obrigatório**) |
| 14 | nValEmb | Numérico | Valor da Embalagem (Opcional) |
| 15 | nRecSB1 | Numérico | RecNo do SB1 |
| 16 | nRecSF4 | Numérico | RecNo do SF4 |
| 17 | cNItem | Caracter | Número do item (Ex: `"01"`) |
| 18 | nDesNTrb | Numérico | Despesas não tributadas (Portugal) |
| 19 | nTara | Numérico | Tara (Portugal) |
| 20 | cCfo | Caracter | CFOP |
| 21 | aNfOri | Array | Array para cálculo do IVA Ajustado (opcional) |
| 22 | cConcept | Caracter | Concepto |
| 23 | nBaseVeic | Numérico | Base Veículo |
| 24 | nPLote | Numérico | Lote Produto |
| 25 | nPSubLot | Numérico | Sub-Lote Produto |
| 26 | nAbatIss | Numérico | Valor do Abatimento ISS |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | nItem | Numérico | Número do item incluído no `aNFItem` da MATXFIS |

#### Exemplos de Uso

```advpl
// PMSA203.PRW – obtendo impostos calculados de um produto
SA1->(MsSeek(xFilial("SA1") + AF8->AF8_CLIENT + AF8->AF8_LOJA))
If SB1->(MsSeek(xFilial("SB1") + cCodProd))
    cTESProd  := SB1->(B1_TS)
    nQtdPeso  := nQtdVend * SB1->B1_PESO
Endif

MaFisIni(AF8->AF8_CLIENT,;   // 1-Código Cliente/Fornecedor
         AF8->AF8_LOJA,;      // 2-Loja
         "C",;                // 3-C:Cliente
         "N",;                // 4-Tipo da NF
         SA1->A1_TIPO,;       // 5-Tipo do Cliente
         Nil, Nil, Nil, Nil, "MATA461")

MaFisAdd(cCodProd,;       // 1-Código do Produto
         cTESProd,;        // 2-Código do TES
         nQtdVend,;        // 3-Quantidade
         nPrecoUnit,;      // 4-Preço Unitário
         0,;               // 5-Desconto
         "",;              // 6-NF Original
         "",;              // 7-Série Original
         0,;               // 8-RecNo NF Original
         0,;               // 9-Frete
         0,;               // 10-Despesa
         0,;               // 11-Seguro
         0,;               // 12-Frete Autônomo
         nValTotItem,;     // 13-Valor da Mercadoria
         0)                // 14-Embalagem

MaFisAlt("IT_PESO", nQtdPeso, nItem)
nValICM := MaFisRet(nItem, "IT_VALICM")
nValIPI := MaFisRet(nItem, "IT_VALIPI")
MaFisEnd()
```

---

### 2.10 MaFisLoad

**Assinatura:** `MaFisLoad(cCampo, xValor, nItem)`

#### Descrição

Carrega valores de impostos e demais conteúdos para os arrays internos da MATXFIS. **Não realiza nenhum cálculo** — apenas atualiza os valores nos arrays.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cCampo | Caracter | Referência do campo (ex: `"IT_VALMERC"`, `"NF_NATUREZA"`) |
| 02 | xValor | Todos | Conteúdo da referência fiscal a ser atualizada |
| 03 | nItem | Numérico | Número do item — obrigatório somente para referências `"IT_"` |

#### Retorno

Não há retorno.

#### Como e Onde Usar

Use para alimentar os arrays internos com dados das tabelas. Útil em interfaces de visualização de documentos e para carregar dados que não constam nos parâmetros de `MaFisIni()`, `MaFisIniLoad()` e `MaFisAdd()`.

> **Atenção:** Qualquer função que disparar novo cálculo após a chamada poderá descartar o valor carregado e substituir pelo calculado.

#### Exemplos de Uso

```advpl
// MATA461.PRX – após MaFisIniLoad(), carregando valores do item
MaFisLoad("IT_VALMERC", aRateio[RT_PRECOIT][3] + aRateio[RT_PRECOIT][4], nItem)
MaFisLoad("IT_PRCUNI",  aRateio[RT_PRECOIT][1], nItem)
MaFisLoad("IT_VLR_FRT", aRateio[RT_VLR_FRT],    nItem)
MaFisLoad("IT_FRETE",   aRateio[RT_FRETE],       nItem)
MaFisLoad("IT_SEGURO",  aRateio[RT_SEGURO],      nItem)
MaFisLoad("IT_DESPESA", aRateio[RT_DESPESA],     nItem)
```

---

### 2.11 MaFisEndLoad

**Assinatura:** `MaFisEndLoad(nItem, nTipo)`

#### Descrição

Finaliza a carga do item do documento fiscal na MATXFIS e atualiza os totalizadores do cabeçalho conforme o tipo informado.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nItem | Numérico | Número do item a ser finalizado |
| 02 | nTipo | Numérico | Tipo da atualização (ver abaixo) |

**Valores de nTipo:**

| Valor | Comportamento |
|-------|---------------|
| 1 (DEFAULT) | Limpa os totalizadores do cabeçalho, refaz a soma de **todos** os itens do `aNFItem` e atualiza o cabeçalho — **muito lento em laços** |
| 2 | Executa apenas a soma do item passado em `nItem` para atualização do cabeçalho — **recomendado em laços** |
| 3 | Não executa a atualização do cabeçalho |

> **ATENÇÃO:** Usar `nTipo = 1` dentro de laços de itens degrada a performance de forma exponencial. **Use sempre `nTipo = 2` em laços.**

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
For nX := 1 to Len(aCols)
    MaFisIniLoad(nX,, .T.)
    For nY := 1 To Len(aHeader)
        cValid   := AllTrim(UPPER(aHeader[nY][6]))
        cRefCols := MaFisGetRf(cValid)[1]
        If !Empty(cRefCols) .And. MaFisFound("IT", nX)
            MaFisLoad(cRefCols, aCols[nX][nY], nX)
        EndIf
    Next nY
    MaFisEndLoad(nX, 2)  // nTipo=2: soma apenas o item atual no cabeçalho
Next nX
```

---

### 2.12 MaFisRet

**Assinatura:** `MaFisRet(nItem, cCampo)`

#### Descrição

Retorna o conteúdo (valores já calculados) da referência fiscal informada. Para referências `"IT_"` e `"LF_"`, retorna valores do item informado em `nItem`. Para referências `"NF_"`, dispensa a passagem do `nItem`.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nItem | Numérico | Número do item no `aNFItem` — obrigatório para `"IT_"` e `"LF_"` |
| 02 | cCampo | Caracter | Referência fiscal: `"NF_??????"` para cabeçalho, `"IT_??????"` e `"LF_??????"` para itens |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | xConteúdo | Todos | Conteúdo da referência fiscal no momento da chamada |

#### Exemplos de Uso

```advpl
// Obtendo impostos calculados do item
If MaFisFound("IT", nItem)
    nValICM   := MaFisRet(nItem, "IT_VALICM")
    nValSOL   := MaFisRet(nItem, "IT_VALSOL")
    nValIPI   := MaFisRet(nItem, "IT_VALIPI")
    nValISS   := MaFisRet(nItem, "IT_VALISS")
    nValIRR   := MaFisRet(nItem, "IT_VALIRR")
    nValINSS  := MaFisRet(nItem, "IT_VALINS")
    nVlCofins := MaFisRet(nItem, "IT_VALCOF")
    nValCSL   := MaFisRet(nItem, "IT_VALCSL")
    nValPIS   := MaFisRet(nItem, "IT_VALPIS")
EndIf

// Obtendo valores do cabeçalho (sem nItem)
@ 070,050 MSGET MaFisRet(, "NF_FRETE")   PICTURE PesqPict("SF2","F2_FRETE",16,2)   SIZE 50,07 OF oFolder:aDlg
@ 070,150 MSGET MaFisRet(, "NF_SEGURO")  PICTURE PesqPict("SF2","F2_SEGURO",16,2)  SIZE 50,07 OF oFolder:aDlg
@ 070,250 MSGET MaFisRet(, "NF_DESCONTO") PICTURE PesqPict("SF2","F2_DESCONTO",16,2) SIZE 50,07 OF oFolder:aDlg
```

```advpl
// Refresh no folder de Despesas Acessórias do Pedido de Compras
Function A120Refresh(aValores)
    Local aArea := GetArea()
    aValores[VALMERC]   := MaFisRet(, "NF_VALMERC")
    aValores[VALDESC]   := MaFisRet(, "NF_DESCONTO")
    aValores[FRETE]     := MaFisRet(, "NF_FRETE")
    aValores[TOTPED]    := MaFisRet(, "NF_TOTAL")
    aValores[SEGURO]    := MaFisRet(, "NF_SEGURO")
    aValores[VALDESP]   := MaFisRet(, "NF_DESPESA")
    aValores[IMPOSTOS]  := aClone(MaFisRet(, "NF_IMPOSTOS"))
    RestArea(aArea)
Return .T.
```

---

### 2.13 MaFisSXRef

**Assinatura:** `MaFisSXRef(cAlias)`

#### Descrição

Pesquisa a tabela informada em `cAlias` no dicionário de dados SX3, buscando no `X3_VALID` de todos os campos a expressão `"MaFisRef"`. Retorna um array com o nome do campo e a referência fiscal ligada a ele.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cAlias | Caracter | Tabela do dicionário de dados |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | aReferencias | Array | `[nX][1]` = Campo da tabela (ex: `D1_COD`); `[nX][2]` = Referência fiscal (ex: `IT_PRODUTO`) |

#### Exemplos de Uso

```advpl
// MATA103.PRW – carregando documento fiscal via SD1
Static Function MontaaCols(...)
    Local aAuxRefSD1 := MaFisSXRef("SD1")
    MaFisIniLoad(Len(aCols))
    For nX := 1 To Len(aAuxRefSD1)
        // aAuxRefSD1[nX][2] = referência fiscal (ex: "IT_PRODUTO")
        // aAuxRefSD1[nX][1] = campo da tabela (ex: D1_COD)
        MaFisLoad(aAuxRefSD1[nX][2],
                  (cAliasSD1)->(FieldGet(FieldPos(aAuxRefSD1[nX][1]))),
                  Len(aCols))
    Next nX
    MaFisEndLoad(Len(aCols), 2)
```

```advpl
// MATA103x.prx – carregando pedidos de compras para NF de Entrada
Function FePC2Acol(nRecSC7, nItem, nSalPed, cItem, lPreNota, aRateio, ...)
    Local aRefSC7 := MaFisSXRef("SC7")
    If MaFisFound()
        MaFisIniLoad(nItem)
        For nX := 1 To Len(aRefSc7)
            Do Case
                Case aRefSC7[nX][2] == "IT_QUANT"
                    MaFisLoad(aRefSc7[nX][2], nSalPed, nItem)
                Case aRefSC7[nX][2] == "IT_PRCUNI"
                    MaFisLoad(aRefSc7[nX][2], NfePcReaj(SC7->C7_REAJUST, lReajuste), nItem)
                OtherWise
                    MaFisLoad(aRefSc7[nX][2], SC7->(FieldGet(FieldPos(aRefSc7[nX][1]))), nItem)
            EndCase
        Next nX
        MaFisEndLoad(nItem)
    EndIf
```

---

### 2.14 MaFisRelImp

**Assinatura:** `MaFisRelImp(cProg, aAlias)`

#### Descrição

Aplicação idêntica à `MaFisSXRef()`, porém pode ser usada para **mais de um Alias ao mesmo tempo**, retornando um array com as referências fiscais separadas por Alias.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cProg | Caracter | Reservado, sem uso no momento — não precisa ser informado |
| 02 | aAlias | Array | Array com os aliases dos arquivos (ex: `{"SF1","SD1"}`) |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | aReferencias | Array | `[nX][1]` = Alias (ex: `SD1`); `[nX][2]` = Campo (ex: `D1_COD`); `[nX][3]` = Referência fiscal (ex: `IT_PRODUTO`) |

#### Como e Onde Usar

Prefira esta função em relação à `MaFisSXRef()` quando for tratar mais de uma tabela (cabeçalho + itens), como `SF1/SD1` ou `SF2/SD2`.

#### Exemplos de Uso

```advpl
If aRelImp == Nil
    aRelImp := MaFisRelImp("MT100", {"SF2","SD2"})
EndIf

dbSelectArea("SF2")
For nY := 1 To Len(aRelImp)
    If aRelImp[nY][1] == "SF2"
        MaFisLoad(aRelImp[nY][3], SF2->(FieldGet(FieldPos(aRelImp[nY][2]))))
    EndIf
Next nY

MaFisIniLoad(nItemNf2, Nil, .T.)
For nZ := 1 To Len(aRelImp)
    If aRelImp[nZ][1] == "SD2"
        MaFisLoad(aRelImp[nZ][3], SD2->(FieldGet(FieldPos(aRelImp[nZ][2]))), nItemNF2)
    EndIf
Next nZ
MaFisEndLoad(nItemNf2, 2)
```

---

### 2.15 MaFisRef

**Assinatura:** `MaFisRef(cReferencia, cProg, xValor)`

#### Descrição

Integra a MATXFIS com programas que possuam interface para manipulação de dados do documento fiscal. Localiza a referência fiscal nos arrays internos, compara com o valor passado, e havendo divergência: altera, recalcula e sincroniza o `aCols`.

> Uso convencional no `X3_VALID` dos campos do dicionário de dados SX3. Exemplo: `X3_VALID` do campo `D1_VALIPI` com `MaFisRef("IT_VALIPI","MT100",M->D1_VALIPI)`.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cReferencia | Caracter | Referência fiscal (`"NF_"` ou `"IT_"`) do `MATXDEF.CH` |
| 02 | cProg | Caracter | `"MT100"` |
| 03 | xValor | Car/Num/Array/Lóg | Conteúdo a ser carregado para a referência fiscal |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | lOk | Lógico | `.T.` = referência encontrada e atualizada; `.F.` = não encontrada |

#### Como e Onde Usar

Usar preferencialmente no `X3_VALID` dos campos das tabelas de cabeçalho e itens da aplicação. Deve ser chamada em **todos** os campos de impostos que tenham uma referência fiscal compatível no `MATXDEF.CH`.

> **Regra importante:** NENHUM imposto deve ser calculado dentro da própria aplicação — TODOS devem obrigatoriamente ser calculados dentro da MATXFIS.

**Fluxo interno de MaFisRef():**
1. `MaFisRef()` — verifica se a alteração é possível e se o item existe
2. `MaFisAlt()` — verifica divergência e dispara recálculo
3. `MaFisRecal()` — recalcula todos os impostos ligados à referência alterada

---

### 2.16 MaFisAlt

**Assinatura:** `MaFisAlt(cCampo, nValor, nItem, lNoCabec, nItemNao, lDupl, cRotina, lRecal)`

#### Descrição

Altera o conteúdo da referência fiscal informada nos arrays `aNFCab` e `aNFItem` e dispara o recálculo de todos os impostos relacionados.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cCampo | Caracter | Referência fiscal a ser alterada |
| 02 | nValor | Numérico | Conteúdo |
| 03 | nItem | Numérico | Número do item (apenas quando `cCampo = "IT_"`) |
| 04 | lNoCabec | Lógico | `.T.` = limpa totalizadores do `aNFCab` e refaz soma de TODOS os itens — **usar só em casos de extrema necessidade** |
| 05 | nItemNao | Numérico | Reservado MATXFIS |
| 06 | lDupl | Lógico | `.T.` = força recálculo mesmo que o conteúdo seja o mesmo (só para `"NF_"`) |
| 07 | cRotina | Caracter | Nome da rotina |
| 08 | lRecal | Lógico | Executa o recálculo dos impostos (DEFAULT = `.T.`) |

#### Retorno

Não há retorno.

#### Como e Onde Usar

> **Performance:** Esta operação é muito mais custosa que `MaFisLoad()`. Minimize o uso ao máximo. Parâmetros `lNoCabec = .T.` e `lRecal = .T.` dentro de laços de itens podem causar degradação exponencial de performance.

#### Exemplos de Uso

```advpl
// 1) Alterando frete, despesa e seguro no cabeçalho
MaFisAlt("NF_FRETE",   avalores[FRETE])
MaFisAlt("NF_DESPESA", avalores[VALDESP])
MaFisAlt("NF_SEGURO",  avalores[SEGURO])

// 2) Alterando valores do item com base em tabela gravada
If (cAliasSD1)->D1_BASEICM > 0
    MaFisAlt("IT_BASEICM", (cAliasSD1)->D1_BASEICM, Len(aCols))
    MaFisAlt("IT_ALIQICM", (cAliasSD1)->D1_PICM,    Len(aCols))
    MaFisAlt("IT_VALICM",  (cAliasSD1)->D1_VALICM,  Len(aCols))
EndIf

// 3) Ponto de Entrada do MATA461.PRX para alterar valor do IPI
If (aEntry[EP_M460IPT])
    VALORIPI := MaFisRet(nItem, "IT_VALIPI")
    BASEIPI  := MaFisRet(nItem, "IT_BASEIPI")
    // lNoCabec = .T. força reconstrução dos totalizadores do aNFCab
    MaFisAlt("IT_VALIPI", ExecTemplate("M460IPI", .F., .F., {SC9->(RecNo()), nItem}), nItem, .T.)
    MaFisLoad("IT_BASEIPI", BASEIPI, nItem)
    MaFisLoad("IT_ALIQIPI", ALIQIPI, nItem)
EndIf
```

---

### 2.17 MaFisDel

**Assinatura:** `MaFisDel(nItem, lDelete)`

#### Descrição

Marca ou desmarca como deletado o item no array `aNFItem`. Usada para **sincronizar** o `aCols` com o `aNFItem` quando itens são deletados/restaurados na interface.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nItem | Numérico | Número do item no `aCols` e no `aNFItem` |
| 02 | lDelete | Lógico | `.T.` = deleta o item; `.F.` = ativa o item (desmarca a deleção) |

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
// MATA920.PRW – montando MsGetDados com função de deleção
oGetDados := MSGetDados():New(aPosObj[2,1], aPosObj[2,2], aPosObj[2,3], aPosObj[2,4],
                               nOpcx, 'A920LinOk', 'A920TudOk', '+D2_ITEM', (!l920Visual),
                               ,,,, 300, 'A920FieldOk',,, 'A920Del')

// Função que chama MaFisDel para sincronismo
Function A920Del()
    MaFisDel(n, aCols[n][Len(aCols[n])])  // N = linha editada; última pos do aCols = .T./.F.
    Eval(bRefresh)
Return .T.
```

---

### 2.18 MaColsToFis

**Assinatura:** `MaColsToFis(aHeader, aCols, nItem, cProg, lRecalc, lVisual, lDel, lSOItem)`

#### Descrição

Carrega TODOS os dados do `aCols` para o `aNFItem`. Pode carregar um único item ou todos. Altamente flexível, deve ser usada com cautela para não comprometer a performance.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | aHeader | Array | Estrutura dos campos da tabela |
| 02 | aCols | Array | Conteúdo dos campos |
| 03 | nItem | Numérico | Número do item a carregar. **Se não informado, carrega TODOS os itens do aCols** |
| 04 | cProg | Caracter | Nome da rotina (ex: `"MT100"`) |
| 05 | lRecalc | Lógico | Executa recálculo dos impostos (DEFAULT: `.F.`) |
| 06 | lVisual | Lógico | Apenas visual — não atualiza totalizadores do cabeçalho (DEFAULT: `.F.`) |
| 07 | lDel | Lógico | Considera itens deletados no processamento (DEFAULT: `.F.`) |
| 08 | lSoItem | Lógico | `nTipo=2` em `MaFisEndLoad()` — soma apenas o item informado (DEFAULT: `.F.`) |

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
// ✅ USO CORRETO — carregando item a item
For nItem := 1 to Len(aCols)
    MaColsToFis(aHeader, aCols, nItem, "MT100", .T., .F.,, .T.)
Next nItem
```

```advpl
// ❌ USO ERRADO — sem informar nItem dentro do laço
// Com 100 itens: 100 x 100 x 100 = 1.000.100 operações!
For nItem := 1 to Len(aCols)
    MaColsToFis(aHeader, aCols,, "MT100", .T., .F.,, .F.)
Next nItem
```

```advpl
// ✅ USO CORRETO — chamada fora do laço para carregar TODOS
For nItem := 1 to Len(aCols)
    // ... processos da aplicação
Next nItem
MaColsToFis(aHeader, aCols,, "MT100", .T.)
```

---

### 2.19 MaFisToCols

**Assinatura:** `MaFisToCols(aHeader, aCols, nItem, cProg)`

#### Descrição

Atualiza o `aCols` com os dados das referências fiscais já calculadas no `aNFItem` da MATXFIS.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | aHeader | Array | Estrutura dos campos da tabela |
| 02 | aCols | Array | Conteúdo dos campos a ser atualizado |
| 03 | nItem | Numérico | Número do item. **Se não informado, atualiza TODOS os itens** |
| 04 | cProg | Caracter | Nome da rotina (ex: `"MT100"`) |

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
// Atualizando o item atual após cálculos
MaFisToCols(aHeader, aCols, Len(aCols), "MT100")

// Atualizando TODOS os itens após alteração de UF de Origem no cabeçalho
If (MaFisFound("NF") .And. !(MaFisRet(, cReferencia) == xValor)) .Or. lPedPre
    MaFisAlt(cReferencia, xValor)
    If cReferencia == "NF_NATUREZA"
        MaFisAlt("NF_UFORIGEM", cUfOri)
    Endif
    MaFisToCols(aHeader, aCols,, "MT100")  // Atualiza TODOS os itens
EndIf
Eval(bGDRefresh)
Eval(bRefresh)
```

---

### 2.20 MaFisRecal

**Assinatura:** `MaFisRecal(cCampo, nItem)`

#### Descrição

Executa a pilha de funções do cálculo de impostos, item a item. É chamada internamente pelas funções `MaFisRef()`, `MaFisAlt()`, `MaFisAdd()` e `MaColsToFis()`.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | cCampo | Caracter | Referência do campo, ou `" "` (vazio) para recalcular todos os impostos |
| 02 | nItem | Numérico | Número do item do documento |

#### Retorno

Não há retorno.

#### Como e Onde Usar

> Use com extrema parcimônia. É função de uso **interno** da MATXFIS. Use somente quando precisar calcular TODOS os impostos em uma ordem específica e obter os resultados **antes** do término do processo.

#### Exemplos de Uso

```advpl
// MATA461.PRX – calculando todos os impostos do item antes de pontos de entrada
MaFisIniLoad(nItem, {SC6->C6_PRODUTO, SC6->C6_TES, ...})
MaFisLoad("IT_VALMERC", aRateio[RT_PRECOIT][3] + aRateio[RT_PRECOIT][4], nItem)
MaFisLoad("IT_PRCUNI",  aRateio[RT_PRECOIT][1], nItem)
MaFisRecal("", nItem)  // Calcula TODOS os impostos do item

// Após o recálculo, aplica ajustes via pontos de entrada
If (aEntry[EP_M460VISS])
    MaFisLoad("IT_VALISS", ExecBlock("M460VISS", .F., .F., MaFisRet(nItem, "IT_VALISS")), nItem)
EndIf
```

---

### 2.21 MaFisWrite

**Assinatura:** `MaFisWrite(nOpc, cArea, nItem, lImpostos, lRemito)`

#### Descrição

Grava os campos das tabelas do documento fiscal com o conteúdo das referências fiscais calculadas pela MATXFIS. Também ajusta arredondamentos antes da gravação.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nOpc | Numérico | `1` = ajusta arredondamentos de TODAS as referências fiscais; `2` = grava nos campos da tabela informada em `cArea` |
| 02 | cArea | Caracter | Alias da tabela a ser gravada |
| 03 | nItem | Numérico | Número do item (apenas quando `nOpc = 2` e gravando itens) |
| 04 | lImpostos | Lógico | `DEFAULT .F.` = grava TODAS as refs. fiscais; `.T.` = grava apenas refs. com `BASIMP`, `ALQIMP`, `VALIMP` |
| 05 | lRemito | Lógico | `DEFAULT .F.` = grava TODAS as refs; `.T.` = grava apenas refs. sem `BASIMP`, `ALQIMP`, `VALIMP` |

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
// MATA103.PRW – após confirmar inclusão do documento
If nOpc == 1
    MaFisWrite(1)  // Ajusta arredondamentos
    Begin Transaction
        a103Grava(Params...)
    End Transaction
EndIf

Function a103Grava(...)
    // Gravando cabeçalho SF1
    SF1->F1_FILIAL  := xFilial("SF1")
    SF1->F1_DOC     := cNFiscal
    SF1->F1_STATUS  := "A"
    SF1->F1_FORNECE := cA100For
    SF4->(MaFisWrite(2, "SF1"))  // Grava refs. fiscais na tabela SF1

    // Gravando itens SD1
    For nX := 1 to Len(aCols)
        SD1->D1_FILIAL  := xFilial("SD1")
        SD1->D1_FORNECE := cA100For
        SF4->(MaFisWrite(2, "SD1", nX))  // Grava refs. fiscais do item na SD1
    Next nX
Return
```

---

### 2.22 MaFisAtuSF3

**Assinatura:** `MaFisAtuSF3(nCaso, cTpOper, nRecNF, cAlias, cPDV, cCnae, cFunOrig, nCD2)`

#### Descrição

Grava/exclui as tabelas `SF3` (Livro Fiscal), `SFT` (Livro Fiscal por Item) e `CD2` (SPED Fiscal) após a gravação ou exclusão do documento fiscal.

> **NUNCA** grave SF3, SFT e CD2 diretamente na rotina — use sempre esta função.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nCaso | Numérico | `1` = Inclusão; `2` = Exclusão |
| 02 | cTPOper | Caracter | `E` = Entrada; `S` = Saída |
| 03 | nRecNF | Numérico | RecNo do cabeçalho da nota fiscal |
| 04 | cAlias | Caracter | Alias da tabela principal |
| 05 | cPDV | Caracter | Identificação do PDV (uso SIGALOJA) |
| 06 | cCNAE | Caracter | Código CNAE |
| 07 | cFunOrig | Caracter | Nome da rotina original que chamou a função |
| 08 | nCD2 | Numérico | `DEFAULT 0` = grava SF3, SFT e CD2; `1` = atualiza SOMENTE CD2 |

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
Function a103Grava(...)
    If INCLUI
        // ... gravação das tabelas SF1 e SD1 ...
        MaFisAtuSF3(1, "E", 0, "SF1")  // Inclusão: grava SF3, SFT e CD2
    Else
        // ... código para exclusão ...
        MaFisAtuSF3(2, "E", SF1->(RecNo()))  // Exclusão: remove SF3, SFT e CD2
    EndIf
Return
```

---

### 2.23 MaFisIniNF

**Assinatura:** `MaFisIniNF(nTipoNF, nRecSF, aOtimizacao, cAlias, lReprocess, cFunOrig)`

#### Descrição

Carrega notas fiscais de entrada e saída para a MATXFIS a partir das tabelas `SF2/SD2` (Saída) ou `SF1/SD1` (Entrada), lendo as referências fiscais do dicionário de dados SX3.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nTipoNF | Numérico | `1` = NF de Entrada; `2` = NF de Saída |
| 02 | nRecSF | Numérico | RecNo do registro de cabeçalho da NF (SF1/SF2) |
| 03 | aOtimizacao | Array | Cache interno para `MaFisSXRef()` |
| 04 | cAlias | Caracter | Alias da tabela de cabeçalho (`"SF1"` ou `"SF2"`) |
| 05 | lReprocess | Lógico | `.T.` = recalcula base dos impostos fiscais (MATA930) |
| 06 | cFunOrig | Caracter | Nome da rotina original |

#### Retorno

Não há retorno.

#### Exemplos de Uso

```advpl
// Função para obter valores calculados de um item de NF
Function xMagValFis(nEntSai, nRecSF, cAliasSf, nItem, cReferencia)
    Local nRet := 0
    Default nRecSF := 0
    MaFisIniNf(nEntSai, nRecSf,, cAliasSf, .F.)
    nRet := MaFisRet(nItem, cReferencia)
    MaFisEnd()
Return (nRet)
```

```advpl
// MATA930.PRX – Reprocessamento dos Livros Fiscais
MaFisIniNF(1, IIf(lQuery, (cAlias)->SF1RECNO, SF1->(RecNo())), @aOtimizacao, cAlias,
           ((cAlias)->F1_IMPORT <> "S"))
Begin Transaction
    // Exclui registros SF3/SFT para regravação com novos cálculos
    dbSelectArea("SF3")
    RecLock('SF3', .F., .T.)
    dbDelete()
    MsUnlock()
    FkCommit()
    // ... exclui SFT ...
    MaFisWrite()
    MaFisAtuSF3(1, "E", IIf(lQuery, (cAlias)->SF1RECNO, SF1->(RecNo())),, "", cCNAE)
```

---

### 2.24 MaFisBrwLivro

**Assinatura:** `MaFisBrwLivro(oWnd, aPosWnd, lVisual, aRecSF3, lOpcVisual)`

#### Descrição

Cria um objeto browse para exibição dos demonstrativos de livros fiscais, disponível em um Folder ou panel da dialog de digitação do documento fiscal.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | oWnd | Objeto | Objeto Listbox que será montado |
| 02 | aPosWnd | Array | Coordenadas do objeto |
| 03 | lVisual | Lógico | `.F.` = editável; `.T.` = somente visualização |
| 04 | aRecSF3 | Array | Registros da tabela SF3 - Livro Fiscal |
| 05 | lOpcVisual | Lógico | DEFAULT `.F.` — uso reservado da MATXFIS |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | oLivro | Objeto | Objeto browse com os dados do Livro Fiscal (SF3) |

#### Exemplos de Uso

```advpl
// MATA103.PRW – Folder Livros Fiscais
DEFINE MSDIALOG oDlg FROM aSizeAut[7],0 TO aSizeAut[6],aSizeAut[5] TITLE STR0009 Of oMainWnd PIXEL

oGetDados := MSGetDados():New(aPosObj[2,1], aPosObj[2,2], aPosObj[2,3], aPosObj[2,4],
                               nOpcx, 'A103LinOk', 'A103TudOk', '+D1_ITEM', !l103Visual,
                               ,,,, IIf(l103Class, Len(aCols), 999),,,,
                               IIf(l103Class, 'AllwaysFalse()', "NfeDelItem"))

oLivro := MaFisBrwLivro(oFolder:aDialogs[4],
                          {5, 4, (aPosObj[3,4] - aPosObj[3,2]) - 10, 53},
                          .T.,
                          IIf(!l103Class, aRecSF3, Nil),
                          IIf(!lWhenGet, IIf(l103Class, .T., l103Visual), .T.))

aFldCBAtu[4] := {|| oLivro:Refresh()}
ACTIVATE MSDIALOG oDlg ON INIT (IIf(lWhenGet, oGetDados:oBrowse:Refresh(), Nil),...)
```

---

### 2.25 MaFisRodape

**Assinatura:**
```
MaFisRodape(nTipo, oJanela, aImpostos, apos, bValidPrg, lVisual, cFornIss,
            cLojaIss, aRecSE2, cDirf, cCodRet, oCodRet, nCombo, oCombo,
            dVencIss, aCodR, cRecIss, oRecIss)
```

#### Descrição

Cria um objeto com o demonstrativo dos impostos calculados (Base, Alíquota e Valor). Quando `lVisual = .F.`, permite editar os valores totais de cada imposto — a MATXFIS rateia os valores editados entre os itens. Também permite incluir novos impostos via double-click.

#### Parâmetros

| Ordem | Parâmetro | Tipo | Descrição |
|-------|-----------|------|-----------|
| 01 | nTipo | Numérico | Quebra: `1` = Imposto+Alíquota; `2` = Imposto |
| 02 | oJanela | Objeto | Tela onde será montado o rodapé |
| 03 | aImpostos | Array | Relação dos impostos a apresentar (opcional) |
| 04 | aPos | Array | Posição e tamanho da tela |
| 05 | bValidPrg | B. Cód. | Bloco de código com validação na edição dos campos |
| 06 | lVisual | Lógico | `.T.` = somente visualização; `.F.` = permite editar os impostos |
| 07 | cFornIss | Caracter | Código do Fornecedor para ISS (quando diferente do fornecedor da nota) |
| 08 | cLojaIss | Caracter | Loja do Fornecedor para ISS |
| 09 | aRecSE2 | Array | RecNo do SE2 (Títulos a Pagar) |
| 10 | cDirf | Caracter | Gera DIRF para o título (`SE2->E2_DIRF`) |
| 11 | cCodRet | Caracter | Código da retenção para DIRF (`SE2->E2_CODRET`) |
| 12 | oCodRet | Objeto | Objeto para refresh |
| 13 | nCombo | Numérico | Conteúdo de aOpcoes de oCombo |
| 14 | oCombo | Objeto | Combo de opções: Gera DIRF = 1-SIM / 2-NÃO |
| 15 | dVencIss | Data | Vencimento do ISS |
| 16 | aCodR | Array | Códigos de retenções relacionados na nota |
| 17 | cRecIss | Caracter | DEFAULT `"1"` — recolhe ISS: `1` = NÃO; `2` = SIM |
| 18 | oRecIss | Objeto | Objeto de Recolhimento de ISS |

#### Retorno

| Ordem | Retorno | Tipo | Descrição |
|-------|---------|------|-----------|
| 01 | oImpostos | Objeto | Objeto com todos os impostos calculados no documento |

#### Como e Onde Usar

Recomendado em **toda** aplicação de digitação/visualização de documentos fiscais. Permite acompanhar os valores calculados em tempo real e editar/incluir impostos diretamente no browse.

#### Exemplos de Uso

```advpl
// MATA103.PRW – Folder Impostos
If l103Visual .And. Empty(SF1->F1_RECBMTO)
    oFisRod := A103Rodape(oFolder:aDialogs[5])
Else
    oFisRod := MaFisRodape(nTpRodape,
                            oFolder:aDialogs[5],,
                            {5, 4, (aPosObj[3,4] - aPosObj[3,2]) - 10, 53},
                            @bIPRefresh, l103Visual,
                            @cFornIss, @cLojaIss,
                            aRecSE2, @cDirf, @cCodRet, @oCodRet,
                            @nCombo, @oCombo, @dVencIss, @aCodR,
                            @cRecIss, @oRecIss)
EndIf
aFldCBAtu[4] := {|| oLivro:Refresh()}
ACTIVATE MSDIALOG oDlg ON INIT (IIf(lWhenGet, oGetDados:oBrowse:Refresh(), Nil),...)
```

---

## Informações de Versão

| Rotina/Fonte | Data/Hora | ChangeSet |
|---|---|---|
| MatxFis.prw | 24/01/2013 – 17:01:51 | 136306 |
| MatxDef.ch | 17/12/2012 – 11:40:00 | 130348 |

**Elaborado por:** Alexandre Inacio Lemes, Demetrio Fontes De Los Rios
