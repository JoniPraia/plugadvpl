# Apostila ADVPL II – Programação Avançada

> **TOTVS S.A.** — Todos os direitos autorais reservados. Proibida a reprodução total ou parcial sem prévia autorização por escrito da proprietária. Conforme artigos 122 e 130 da LEI n.º 5.988 de 14 de Dezembro de 1973.
>
> **Protheus – Versão 12**

---

## Sumário

1. [Objetivo](#1-objetivo)
2. [Programação de Atualização](#2-programação-de-atualização)
   - 2.1 [Modelo1() ou AxCadastro()](#21-modelo1-ou-axcadastro)
   - 2.2 [Mbrowse()](#22-mbrowse)
     - 2.2.1 [AxFunctions()](#221-axfunctions)
     - 2.2.2 [FilBrowse()](#222-filbrowse)
     - 2.2.3 [EndFilBrw()](#223-endfilbrw)
     - 2.2.4 [PesqBrw()](#224-pesqbrw)
     - 2.2.5 [BrwLegenda()](#225-brwlegenda)
   - 2.3 [MarkBrowse()](#23-markbrowse)
   - 2.4 [Enchoice](#24-enchoice)
   - 2.5 [EnchoiceBar](#25-enchoicebar)
   - 2.6 [Modelo2()](#26-modelo2)
   - 2.7 [Modelo3()](#27-modelo3)
3. [Transações](#3-transações)
   - 3.1 [Begin Transaction](#31-begin-transaction)
   - 3.2 [BeginTran](#32-begintran)
4. [Relatórios](#4-relatórios)
   - 4.1 [TReport](#41-treport)
   - 4.2 [Funções Utilizadas para Desenvolvimento de Relatórios](#42-funções-utilizadas-para-desenvolvimento-de-relatórios)
   - 4.3 [AjustaSX1()](#43-ajustasx1)
5. [Utilizando Queries no Protheus](#5-utilizando-queries-no-protheus)
   - 5.1 [Embedded SQL](#51-embedded-sql)
6. [Manipulação de Arquivos](#6-manipulação-de-arquivos)
   - 6.1 [Geração e leitura de arquivos em formato texto](#61-geração-e-leitura-de-arquivos-em-formato-texto)
   - 6.2 [1ª Família de funções](#62-1ª-família-de-funções-de-gravação-e-leitura-de-arquivos-texto)
   - 6.3 [2ª Família de funções](#63-2ª-família-de-funções-de-gravação-e-leitura-de-arquivos-texto)
7. [Captura de Múltiplas Informações (Multi-Lines)](#7-captura-de-múltiplas-informações-multi-lines)
   - 7.1 [MsNewGetDados()](#711-msnewgetdados)
   - 7.2 [TCBrowse](#72-tcbrowse)
8. [FWTemporaryTable](#8-fwtemporarytable)
9. [Arquitetura MVC](#9-arquitetura-mvc)
   - 9.1 [Principais funções](#91-principais-funções-da-aplicação-em-advpl-utilizando-o-mvc)
   - 9.2 [ModelDef](#92-o-que-é-a-função-modeldef)
   - 9.3 [ViewDef](#93-o-que-é-a-função-viewdef)
   - 9.4 [MenuDef](#94-o-que-é-a-função-menudef)
10. [Novo Comportamento na Interface](#10-novo-comportamento-na-interface)
    - 10.1 [FWMBrowse](#101-aplicações-com-browses-fwmbrowse)
    - 10.2 [Exemplo completo de Browse](#102-exemplo-completo-de-browse)
11. [Construção de Aplicação ADVPL utilizando MVC](#11-construção-de-aplicação-advpl-utilizando-mvc)
12. [Criando o MenuDef](#12-criando-o-menudef)
13. [Construção da função ModelDef](#13-construção-da-função-modeldef)
14. [Construção da função ViewDef](#14-construção-da-função-viewdef)
15. [Objetos de Interface](#15-objetos-de-interface)
    - 15.1 [Réguas de processamento](#151-réguas-de-processamento)
    - 15.2 [ListBox()](#152-listbox)
    - 15.3 [ScrollBox()](#153-scrollbox)
16. [Componentes da Interface Visual do ADVPL](#16-componentes-da-interface-visual-do-advpl)
17. [Aplicações com a Interface Visual do ADVPL](#17-aplicações-com-a-interface-visual-do-advpl)
- [Apêndices – Boas Práticas de Programação](#apêndices--boas-práticas-de-programação)
  - 18 [Arredondamento](#18-arredondamento)
  - 19 [Utilização de Identação](#19-utilização-de-identação)
  - 20 [Capitulação de Palavras-Chave](#20-capitulação-de-palavras-chave)
  - 21 [Técnicas de Programação Eficiente](#21-técnicas-de-programação-eficiente)

---

## 1. Objetivo

Ao final do curso o treinando deverá ter desenvolvido os seguintes conceitos, habilidades e atitudes:

**a) Conceitos a serem aprendidos**
- Estruturas para implementação de relatórios e programas de atualização
- Estruturas para implementação de interfaces visuais
- Princípios do desenvolvimento de aplicações orientadas a objetos

**b) Habilidades e técnicas a serem aprendidas**
- Desenvolvimento de aplicações voltadas ao ERP Protheus
- Análise de fontes de média complexidade
- Desenvolvimento de aplicações básicas com orientação a objetos

**c) Atitudes a serem desenvolvidas**
- Adquirir conhecimentos através da análise das funcionalidades disponíveis no ERP Protheus
- Estudar a implementação de fontes com estruturas orientadas a objetos em ADVPL
- Embasar a realização de outros cursos relativos à linguagem ADVPL

---

## 2. Programação de Atualização

Os programas de atualização de cadastros e digitação de movimentos seguem um padrão que se apoia no Dicionário de Dados. Basicamente são três os modelos mais utilizados:

- **Modelo 1 ou AxCadastro:** Para cadastramentos em tela cheia. Exemplo: Cadastro de Cliente.
- **Modelo 2:** Cadastramentos envolvendo apenas uma tabela, mas com um cabeçalho e, opcionalmente, um rodapé e um corpo com quantidade ilimitada de linhas. Ideal para casos em que há dados que se repetem por vários itens. Exemplo: Pedido de Compra.
- **Modelo 3:** Cadastramentos envolvendo duas tabelas, um com dados de cabeçalho e outro digitado em linhas com os itens. Exemplo: Pedido de Vendas, Orçamento etc.

Todos os modelos são genéricos — o programa independe da tabela a ser tratada, bastando informar apenas o seu Alias. O restante é obtido do Dicionário de Dados (SX3).

---

## 2.1. Modelo1() ou AxCadastro()

O `AxCadastro()` é uma funcionalidade de cadastro simples, composta de:
- Browser padrão para visualização das informações da base de dados, de acordo com as configurações do SX3 – Dicionário de Dados (campo browser).
- Funções de pesquisa, visualização, inclusão, alteração e exclusão padrões para registros simples, sem a opção de cabeçalho e itens.

**Sintaxe:**
```advpl
AxCadastro(cAlias, cTitulo, cVldExc, cVldAlt)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cAlias`  | Alias padrão do sistema para utilização, definido no dicionário de dados – SX3 |
| `cTitulo` | Título da Janela |
| `cVldExc` | Validação para Exclusão |
| `cVldAlt` | Validação para Alteração |

**Exemplo: Função AxCadastro()**

```advpl
#include "protheus.ch"

User Function XCadSA2()
    Local cAlias  := "SA2"
    Local cTitulo := "Cadastro de Fornecedores"
    Local cVldExc := ".T."
    Local cVldAlt := ".T."

    dbSelectArea(cAlias)
    dbSetOrder(1)
    AxCadastro(cAlias, cTitulo, cVldExc, cVldAlt)
Return Nil
```

**Exemplo: Função de validação da alteração**

```advpl
User Function VldAlt(cAlias, nReg, nOpc)
    Local lRet   := .T.
    Local aArea  := GetArea()
    Local nOpcao := 0

    nOpcao := AxAltera(cAlias, nReg, nOpc)
    If nOpcao == 1
        MsgInfo("Alteração concluída com sucesso!")
    Endif
    RestArea(aArea)
Return lRet
```

**Exemplo: Função de validação da exclusão**

```advpl
User Function VldExc(cAlias, nReg, nOpc)
    Local lRet   := .T.
    Local aArea  := GetArea()
    Local nOpcao := 0

    nOpcao := AxExclui(cAlias, nReg, nOpc)
    If nOpcao == 1
        MsgInfo("Exclusão concluída com sucesso!")
    Endif
    RestArea(aArea)
Return lRet
```

---

## 2.2. Mbrowse()

A `Mbrowse()` é uma funcionalidade de cadastro que permite a utilização de recursos mais aprimorados na visualização e manipulação das informações do sistema, possuindo os seguintes componentes:

- Browse padrão para visualização das informações da base de dados (campo browse do SX3).
- Parametrização para funções específicas para as ações de visualização, inclusão, alteração e exclusão, viabilizando a manutenção de informações com estrutura de cabeçalhos e itens.
- Recursos adicionais como identificadores de status de registros, legendas e filtros.

**Sintaxe:**
```advpl
MBrowse(nLin1, nCol1, nLin2, nCol2, cAlias, aFixe, cCpo, nPar08, cFun, nClickDef,
        aColors, cTopFun, cBotFun, nPar14, bInitBloc, lNoMnuFilter, lSeeAll, lChgAll)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `nLin1` | Número da Linha Inicial |
| `nCol1` | Número da Coluna Inicial |
| `nLin2` | Número da Linha Final |
| `nCol2` | Número da Coluna Final |
| `cAlias` | Alias do arquivo que será visualizado no browse. Para arquivos de trabalho, o alias deve ser obrigatoriamente `'TRB'` e o parâmetro `aFixe` torna-se obrigatório. |
| `aFixe` | Array bi-dimensional com nomes dos campos fixos pré-definidos. Para dicionário: `[n][1]=>Descrição`, `[n][2]=>Nome`. Para trabalho: acrescenta `[n][3]=>Tipo`, `[n][4]=>Tamanho`, `[n][5]=>Decimal`, `[n][6]=>Picture`. |
| `cCpo` | Campo a ser validado para exibição do bitmap de status |
| `nPar08` | Parâmetro reservado |
| `cFun` | Função que retorna valor lógico para exibição do bitmap de status (descarta `cCpo`) |
| `nClickDef` | Opção do `aRotina` executada no duplo clique (default: visualização) |
| `aColors` | Array bi-dimensional para diferentes bitmaps de status: `[n][1]=>Função lógica`, `[n][2]=>Nome do bitmap` |
| `cTopFun` | Função que retorna o limite superior do filtro (usar com `cBotFun`) |
| `cBotFun` | Função que retorna o limite inferior do filtro (usar com `cTopFun`) |
| `nPar14` | Parâmetro reservado |
| `bInitBloc` | Bloco de código executado no ON INIT da janela do browse |
| `lNoMnuFilter` | `.T.` = não exibe opção de filtro no menu; `.F.` = exibe (default) |
| `lSeeAll` | Indica se o Browse mostrará todas as filiais (default: `.F.`) |
| `lChgAll` | Indica se registro de outra filial está autorizado para alterações (default: `.F.`) |

**Variáveis private adicionais:**

`aRotina` — Array com as funções executadas pela Mbrowse. Estrutura:
- `[n][1]` – Título
- `[n][2]` – Rotina
- `[n][3]` – Reservado
- `[n][4]` – Operação (1=pesquisa; 2=visualização; 3=inclusão; 4=alteração; 5=exclusão)

```advpl
AADD(aRotina, {"Pesquisar",  "AxPesqui", 0, 1})
AADD(aRotina, {"Visualizar", "AxVisual", 0, 2})
AADD(aRotina, {"Incluir",    "AxInclui", 0, 3})
AADD(aRotina, {"Alterar",    "AxAltera", 0, 4})
AADD(aRotina, {"Excluir",    "AxDeleta", 0, 5})
```

`cCadastro` — Título do browse que será exibido.

**Informações passadas para funções do aRotina:**

Quando o nome da função não é especificado com `()`, a Mbrowse passa como parâmetros:
- `cAlias` — Nome da área de trabalho definida para a Mbrowse
- `nReg` — Recno do registro posicionado no Browse
- `nOpc` — Posição da opção utilizada na Mbrowse de acordo com a ordem no `aRotina`

**Exemplo: Função Mbrowse()**

```advpl
#include "protheus.ch"

User Function MBrwSA1()
    Local cAlias := "SA1"
    Private cCadastro := "Cadastro de Clientes"
    Private aRotina   := {}

    AADD(aRotina, {"Pesquisar",  "AxPesqui", 0, 1})
    AADD(aRotina, {"Visualizar", "AxVisual", 0, 2})
    AADD(aRotina, {"Incluir",    "AxInclui", 0, 3})
    AADD(aRotina, {"Alterar",    "AxAltera", 0, 4})
    AADD(aRotina, {"Excluir",    "AxDeleta", 0, 5})

    dbSelectArea(cAlias)
    dbSetOrder(1)
    mBrowse( , , , , cAlias)
Return Nil
```

**Exemplo: Substituindo AxInclui() por função própria — Chamada da Mbrowse()**

```advpl
#include "protheus.ch"

User Function MBrwSA1()
    Local cAlias := "SA1"
    Private cCadastro := "Cadastro de Clientes"
    Private aRotina   := {}

    AADD(aRotina, {"Pesquisar",  "AxPesqui", 0, 1})
    AADD(aRotina, {"Visualizar", "AxVisual", 0, 2})
    AADD(aRotina, {"Incluir",    "U_Inclui", 0, 3})
    AADD(aRotina, {"Alterar",    "AxAltera", 0, 4})
    AADD(aRotina, {"Excluir",    "AxDeleta", 0, 5})

    dbSelectArea(cAlias)
    dbSetOrder(1)
    mBrowse(6, 1, 22, 75, cAlias)
Return Nil
```

**Exemplo: Função Inclui() substituindo AxInclui()**

```advpl
User Function Inclui(cAlias, nReg, nOpc)
    Local cTudoOk := "( Alert('OK'), .T. )"
    Local nOpcao  := 0

    nOpcao := AxInclui(cAlias, nReg, nOpc, , , , cTudoOk)
    If nOpcao == 1
        MsgInfo("Inclusão concluída com sucesso!")
    ElseIf nOpcao == 2
        MsgInfo("Inclusão cancelada!")
    Endif
Return Nil
```

**Exemplo: Determinando a opção do aRotina pela informação recebida em nOpc**

```advpl
#include "protheus.ch"

User Function Exclui(cAlias, nReg, nOpc)
    Local cTudoOk := "(Alert('OK'), .T.)"
    Local nOpcao  := 0

    // Identifica corretamente a opção definida para a função em aRotinas
    // com mais do que os 5 elementos padrões.
    nOpcao := AxDeleta(cAlias, nReg, aRotina[nOpc, 4])

    If nOpcao == 1
        MsgInfo("Exclusão realizada com sucesso!")
    ElseIf nOpcao == 2
        MsgInfo("Exclusão cancelada!")
    Endif
Return Nil
```

---

### 2.2.1. AxFunctions()

Funções padrões da aplicação ERP para visualização, inclusão, alteração e exclusão de dados em formato simples. Podem ser utilizadas na definição do `AxCadastro()` e no array `aRotina` da `Mbrowse()`:

#### AXPESQUI()

Função de pesquisa padrão em registros exibidos pelos browses, posicionando o browse no registro pesquisado. Exibe tela para seleção do índice e digitação das informações da chave de busca.

#### AXVISUAL()

```advpl
AXVISUAL(cAlias, nReg, nOpc, aAcho, nColMens, cMensagem, cFunc, aButtons, lMaximized)
```

Função de visualização padrão das informações de um registro, no formato Enchoice.

#### AXINCLUI()

```advpl
AxInclui(cAlias, nReg, nOpc, aAcho, cFunc, aCpos, cTudoOk, lF3,
         cTransact, aButtons, aParam, aAuto, lVirtual, lMaximized)
```

Função de inclusão padrão das informações de um registro, no formato Enchoice.

#### AXALTERA()

```advpl
AxAltera(cAlias, nReg, nOpc, aAcho, cFunc, aCpos, cTudoOk, lF3,
         cTransact, aButtons, aParam, aAuto, lVirtual, lMaximized)
```

Função de alteração padrão das informações de um registro, no formato Enchoice.

#### AXDELETA()

```advpl
AXDELETA(cAlias, nReg, nOpc, cTransact, aCpos, aButtons, aParam, aAuto, lMaximized)
```

Função de exclusão padrão das informações de um registro, no formato Enchoice.

---

### 2.2.2. FilBrowse()

Permite a utilização de filtros na MBrowse().

**Sintaxe:**
```advpl
FilBrowse(cAlias, aQuery, cFiltro, lShowProc)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cAlias` | Alias ativo definido para a Mbrowse() |
| `aQuery` | Inicializar sempre vazio, passagem obrigatoriamente por referência. Retorno: `[1]=>Nome do Arquivo Físico`, `[2]=>Ordem correspondente ao Sindex` |
| `cFiltro` | Condição de filtro para a MBrowse() |
| `lShowProc` | Habilita (`.T.`) ou desabilita (`.F.`) a mensagem "Selecionando registros..." |

> **Exercício:** Implementar uma MBrowse com as funções de cadastro padrões para a tabela SB1: Produtos.

---

### 2.2.3. EndFilBrw()

Elimina o filtro e o arquivo temporário criados pela `FilBrowse()`.

**Sintaxe:**
```advpl
EndFilBrw(cAlias, aQuery)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cAlias` | Alias ativo definido para a Mbrowse() |
| `aQuery` | Array de retorno passado por referência para a FilBrowse(). `[1]=>Nome do Arquivo Físico`, `[2]=>Ordem correspondente ao Sindex` |

---

### 2.2.4. PesqBrw()

Permite a pesquisa dentro da MBrowse(). Esta função deve obrigatoriamente substituir a `AxPesqui` no `aRotina` sempre que for utilizada a `FilBrowse()`.

**Sintaxe:**
```advpl
PesqBrw(cAlias, nReg, bBrwFilter)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cAlias` | Alias ativo definido para a Mbrowse() |
| `nReg` | Número do registro |
| `bBrwFilter` | Bloco de Código que contém a FilBrowse(). Ex: `bBrwFilter := {|| FilBrowse(cAlias, aQuery, cFiltro, lShowProc)}` |

---

### 2.2.5. BrwLegenda()

Permite a inclusão de legendas na MBrowse().

**Sintaxe:**
```advpl
BrwLegenda(cCadastro, cTitulo, aLegenda)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cCadastro` | Mesma variável utilizada para a MBrowse |
| `cTitulo` | Título (identificação) da Legenda |
| `aLegenda` | Array com definição da cor e texto explicativo: `{{"Cor", "Texto"}}` |

**Lista de cores disponíveis no Protheus:**
- `BR_AMARELO`, `BR_AZUL`, `BR_BRANCO`, `BR_CINZA`, `BR_LARANJA`
- `BR_MARRON`, `BR_VERDE`, `BR_VERMELHO`, `BR_PINK`, `BR_PRETO`

**Exemplo: Mbrowse() utilizando funções acessórias**

```advpl
#Include "Protheus.ch"

User Function MBrwSA2()
    Local cAlias  := "SA2"
    Local aCores  := {}
    Local cFiltra := ""

    cFiltra := "A2_FILIAL == '" + xFilial('SA2') + "' .And. A2_EST == 'SP'"

    Private cCadastro  := "Cadastro de Fornecedores"
    Private aRotina    := {}
    Private aIndexSA2  := {}
    Private bFiltraBrw := {|| FilBrowse(cAlias, @aIndexSA2, @cFiltra)}

    AADD(aRotina, {"Pesquisar",  "PesqBrw",   0, 1})
    AADD(aRotina, {"Visualizar", "AxVisual",  0, 2})
    AADD(aRotina, {"Incluir",    "U_BInclui", 0, 3})
    AADD(aRotina, {"Alterar",    "U_BAltera", 0, 4})
    AADD(aRotina, {"Excluir",    "U_BDeleta", 0, 5})
    AADD(aRotina, {"Legenda",    "U_BLegenda",0, 3})

    AADD(aCores, {"A2_TIPO == 'F'",    "BR_VERDE"   })
    AADD(aCores, {"A2_TIPO == 'J'",    "BR_AMARELO" })
    AADD(aCores, {"A2_TIPO == 'X'",    "BR_LARANJA" })
    AADD(aCores, {"A2_TIPO == 'R'",    "BR_MARRON"  })
    AADD(aCores, {"Empty(A2_TIPO)",    "BR_PRETO"   })

    dbSelectArea(cAlias)
    dbSetOrder(1)

    // Cria o filtro na MBrowse utilizando a função FilBrowse
    Eval(bFiltraBrw)
    dbSelectArea(cAlias)
    dbGoTop()
    mBrowse(6, 1, 22, 75, cAlias, , , , , , aCores)

    // Deleta o filtro utilizado na função FilBrowse
    EndFilBrw(cAlias, aIndexSA2)
Return Nil

// Rotina de Inclusão
User Function BInclui(cAlias, nReg, nOpc)
    Local nOpcao := 0
    nOpcao := AxInclui(cAlias, nReg, nOpc)
    If nOpcao == 1
        MsgInfo("Inclusão efetuada com sucesso!")
    Else
        MsgInfo("Inclusão cancelada!")
    Endif
Return Nil

// Rotina de Alteração
User Function BAltera(cAlias, nReg, nOpc)
    Local nOpcao := 0
    nOpcao := AxAltera(cAlias, nReg, nOpc)
    If nOpcao == 1
        MsgInfo("Alteração efetuada com sucesso!")
    Else
        MsgInfo("Alteração cancelada!")
    Endif
Return Nil

// Rotina de Exclusão
User Function BDeleta(cAlias, nReg, nOpc)
    Local nOpcao := 0
    nOpcao := AxDeleta(cAlias, nReg, nOpc)
    If nOpcao == 1
        MsgInfo("Exclusão efetuada com sucesso!")
    Else
        MsgInfo("Exclusão cancelada!")
    Endif
Return Nil

// Rotina de Legenda
User Function BLegenda()
    Local aLegenda := {}
    AADD(aLegenda, {"BR_VERDE",   "Pessoa Física"     })
    AADD(aLegenda, {"BR_AMARELO", "Pessoa Jurídica"   })
    AADD(aLegenda, {"BR_LARANJA", "Exportação"        })
    AADD(aLegenda, {"BR_MARRON",  "Fornecedor Rural"  })
    AADD(aLegenda, {"BR_PRETO",   "Não Classificado"  })
    BrwLegenda(cCadastro, "Legenda", aLegenda)
Return Nil
```

---

## 2.3. MarkBrowse()

A `MarkBrow()` permite que os elementos de um browse sejam marcados ou desmarcados. Para utilizá-la é necessário declarar as variáveis `cCadastro` e `aRotina` como Private antes da chamada da função.

**Sintaxe:**
```advpl
MarkBrow(cAlias, cCampo, cCpo, aCampos, lInvert, cMarca, cCtrlM, uPar8,
         cExpIni, cExpFim, cAval, bParBloco)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cAlias` | Alias ativo definido para a Mbrowse() |
| `cCampo` | Campo do arquivo onde será feito o controle (gravação) da marca |
| `cCpo` | Campo onde será feita a validação para marcação e exibição do bitmap de status |
| `aCampos` | Vetor de colunas: `[n][1]=>nome do campo`, `[n][2]=>Nulo(Nil)`, `[n][3]=>Título`, `[n][4]=>Máscara(picture)` |
| `lInvert` | Inverte a marcação |
| `cMarca` | String a ser gravada no campo especificado para marcação |
| `cCtrlM` | Função a ser executada caso deseje marcar todos elementos |
| `uPar8` | Parâmetro reservado |
| `cExpIni` | Função que retorna o conteúdo inicial do filtro baseada na chave de índice |
| `cExpFim` | Função que retorna o conteúdo final do filtro baseada na chave de índice |
| `cAval` | Função a ser executada no duplo clique em um elemento no browse |
| `bParBloco` | Bloco de código a ser executado na inicialização da janela |

**Informações passadas para funções do aRotina:**

| Variável | Descrição |
|----------|-----------|
| `cAlias` | Nome da área de trabalho definida para a Mbrowse |
| `nReg` | Recno do registro posicionado no Browse |
| `nOpc` | Posição da opção utilizada na Mbrowse |
| `cMarca` | Marca em uso pela MarkBrw() |
| `lInverte` | Indica se foi utilizada a inversão da seleção dos itens no browse |

### 2.3.1. Funções de Apoio

- `GetMark` — Define a marca atual.
- `IsMark` — Avalia se um determinado conteúdo é igual à marca atual.
- `ThisMark` — Captura a marca em uso.
- `ThisInv` — Indica se foi usado o recurso de selecionar todos (inversão).
- `MarkBRefresh` — Atualiza exibição na marca do browse.

**Exemplo: Função MarkBrow() e acessórias**

```advpl
#include "protheus.ch"

USER FUNCTION MkBrwSA1()
    Local aCpos   := {}
    Local aCampos := {}
    Local nI      := 0
    Local cAlias  := "SA1"

    Private aRotina   := {}
    Private cCadastro := "Cadastro de Clientes"
    Private aRecSel   := {}

    AADD(aRotina, {"Visualizar Lote", "U_VisLote", 0, 5})

    AADD(aCpos, "A1_OK"    )
    AADD(aCpos, "A1_FILIAL")
    AADD(aCpos, "A1_COD"   )
    AADD(aCpos, "A1_LOJA"  )
    AADD(aCpos, "A1_NOME"  )
    AADD(aCpos, "A1_TIPO"  )

    dbSelectArea("SX3")
    dbSetOrder(2)
    For nI := 1 To Len(aCpos)
        IF dbSeek(aCpos[nI])
            AADD(aCampos, {X3_CAMPO, "", IIF(nI==1, "", Trim(X3_TITULO)), Trim(X3_PICTURE)})
        ENDIF
    Next

    DbSelectArea(cAlias)
    DbSetOrder(1)
    MarkBrow(cAlias, aCpos[1], "A1_TIPO == ' '", aCampos, .F., GetMark(, "SA1", "A1_OK"))
Return Nil
```

**Exemplo: Função VisLote() — utilização das funções acessórias da MarkBrow()**

```advpl
USER FUNCTION VisLote()
    Local cMarca  := ThisMark()
    Local nX      := 0
    Local lInvert := ThisInv()
    Local cTexto  := ""
    Local cEOL    := CHR(10) + CHR(13)
    Local oDlg
    Local oMemo

    DbSelectArea("SA1")
    DbGoTop()
    While SA1->(!EOF())
        IF SA1->A1_OK == cMarca .AND. !lInvert
            AADD(aRecSel, {SA1->(Recno()), SA1->A1_COD, SA1->A1_LOJA, SA1->A1_NREDUZ})
        ELSEIF SA1->A1_OK != cMarca .AND. lInvert
            AADD(aRecSel, {SA1->(Recno()), SA1->A1_COD, SA1->A1_LOJA, SA1->A1_NREDUZ})
        ENDIF
        SA1->(dbSkip())
    Enddo

    IF Len(aRecSel) > 0
        cTexto := "Código | Loja | Nome Reduzido " + cEOL
        For nX := 1 to Len(aRecSel)
            cTexto += aRecSel[nX][2] + Space(1) + "|" + Space(2) + aRecSel[nX][3]
            cTexto += Space(3) + "|" + Space(1) + SUBSTRING(aRecSel[nX][4], 1, 20) + Space(1)
            cTexto += cEOL
        Next nX

        DEFINE MSDIALOG oDlg TITLE "Clientes Selecionados" From 000,000 TO 350,400 PIXEL
        @ 005,005 GET oMemo VAR cTexto MEMO SIZE 150,150 OF oDlg PIXEL
        oMemo:bRClicked := {|| AllwaysTrue()}
        DEFINE SBUTTON FROM 005,165 TYPE 1 ACTION oDlg:End() ENABLE OF oDlg PIXEL
        ACTIVATE MSDIALOG oDlg CENTER
        LimpaMarca()
    ENDIF
Return
```

**Exemplo: Função LimpaMarca()**

```advpl
STATIC FUNCTION LimpaMarca()
    Local nX := 0
    For nX := 1 to Len(aRecSel)
        SA1->(DbGoto(aRecSel[nX][1]))
        RecLock("SA1", .F.)
        SA1->A1_OK := SPACE(2)
        MsUnLock()
    Next nX
Return()
```

---

## 2.4. Enchoice

A função `Enchoice` é um recurso baseado no dicionário de dados para verificar campos obrigatórios, validações, gatilhos, consulta padrão etc. Permite criar pastas de cadastros. Pode ser usada tanto com variáveis de memórias Private como diretamente com os campos da tabela.

A diferença entre `Enchoice` e o objeto `MsMGet` é que a função não retorna o nome da variável de objeto exportável criado.

**Sintaxe:**
```advpl
Enchoice(cAlias [nReg] nOpc [aCRA] [cLetras] [cTexto] [aAcho] [aPos] [aCpos]
         [nModelo] [nColMens] [cMensagem] [cTudoOk] [oWnd] [lF3] [lMemoria]
         [lColumn] [caTela] [lNoFolder] [lProperty] [aField] [aFolder]
         [lCreate] [lNoMDIStrech] [cTela])
```

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|-------------|
| `cAlias` | Caractere | Tabela cadastrada no SX2 que será editada | X |
| `nReg` | Nulo | Parâmetro não utilizado | |
| `nOpc` | Numérico | Número da linha do aRotina que definirá o tipo de edição | X |
| `aCRA` | Nulo | Parâmetro não utilizado | |
| `cLetras` | Nulo | Parâmetro não utilizado | |
| `cTexto` | Nulo | Parâmetro não utilizado | |
| `aAcho` | Vetor | Vetor com nome dos campos que serão exibidos | |
| `aPos` | Vetor | Vetor com coordenadas `{Lin, Col, LinFim, ColFim}` | |
| `aCpos` | Vetor | Vetor com nome dos campos que poderão ser editados | |
| `nModelo` | Numérico | Se diferente de 1, desabilita execução de gatilhos estrangeiros | |
| `oWnd` | Objeto | Objeto onde a enchoice será criada | |
| `lF3` | Lógico | Indica se a enchoice está sendo criada em uma consulta F3 | |
| `lMemoria` | Lógico | Indica se utilizará variáveis de memória ou campos da tabela | |
| `lColumn` | Lógico | Indica se a apresentação dos campos será em forma de coluna | |
| `caTela` | Caractere | Nome da variável private que a enchoice utilizará no lugar de `aTela` | |
| `lNoFolder` | Lógico | Indica se a enchoice não irá utilizar as Pastas de Cadastro (SXA) | |
| `lProperty` | Lógico | Indica se não utilizará as variáveis private `aTela` e `aGets` | |
| `aField` | Vetor | Campos mostrados na Enchoice caso o SX3 não seja utilizado | |
| `aFolder` | Vetor | Nome das pastas caso o SX3 não seja utilizado | |
| `lCreate` | Lógico | Indica se cria as pastas especificadas no parâmetro `aFolder` | |
| `lNoMDIStrech` | Lógico | Define se o objeto não será alinhado conforme o espaço existente | |
| `cTela` | Caractere | Campo reservado | |

Para criar variáveis com o nome do campo utilizamos:

```advpl
RegToMemory(cAlias, lInc, lDic, lInitPad, cStack)
```

- `cAlias` — Alias da tabela a ter suas variáveis inicializadas.
- `lInc` — `.T.` para inclusão (valores vazios); `.F.` para manutenção (dados do registro posicionado).
- `lDic` — `.T.` inicializa baseado no dicionário (inclui campos virtuais); `.F.` apenas nos dados da WorkArea.
- `lInitPad` — Indica se o inicializador padrão do dicionário será executado (requer `lDic = .T.`).
- `cStack` — Parâmetro reservado.

Para referenciar campos e variáveis:
- Campo: `SA2->A2_NOME`
- Variável de memória: `M->A2_NOME`

Para verificar campos obrigatórios:

```advpl
Obrigatorio(aGets, aTela, uPar3, lShow)
```

Retorna `.T.` se todos os campos obrigatórios foram preenchidos.

**Funções auxiliares de campo:**

| Função | Sintaxe | Descrição |
|--------|---------|-----------|
| `FieldPos()` | `FieldPos(X3_CAMPO)` | Retorna a posição do campo na estrutura do alias corrente (0 se não existir) |
| `FieldGet()` | `FieldGet(<nFieldPos>)` | Retorna o conteúdo do campo pela posição ordinal |
| `FieldName()` | `FieldName(<cNomeCampo>)` | Retorna o nome do campo pela posição |
| `FieldPut()` | `FieldPut(<nCampo>, <Conteudo>)` | Atribui valor a um campo pela posição ordinal |

---

## 2.5. EnchoiceBar

Cria uma barra de botões padrão de Ok e Cancelar, permitindo a implementação de botões adicionais.

**Sintaxe:**
```advpl
ENCHOICEBAR(oDlg, bOk, bCancelar, [lMensApag], [aBotoes])
```

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `oDlg` | Objeto | Janela onde a barra será criada |
| `bOk` | Objeto | Bloco de código executado ao clicar em Ok |
| `bCancelar` | Objeto | Bloco de código executado ao clicar em Cancelar |
| `lMensApag` | Lógico | Se `.T.`, ao clicar Ok aparece tela de confirmação de exclusão (default: `.F.`) |
| `aBotoes` | Vetor | Vetor para criação de botões adicionais: `{bitmap, bloco de código, mensagem}` |

```advpl
AADD(aButtons, {"CLIPS", {|| AllwaysTrue()}, "Usuário"})
```

---

## 2.6. Modelo2()

O Modelo 2 é um protótipo de tela para entrada de dados em vários registros de uma só vez. Por exemplo: efetuar o movimento interno de vários produtos do estoque em um único lote.

> **Nota:** A função `Modelo2()` é uma função pronta que implementa o protótipo. Quando necessário intervir na rotina há poucos recursos para customização.

**Sintaxe:**
```advpl
Modelo2([cTitulo], [aCab], [aRoda], [aGrid], [nOpc], [cLinhaOk], [cTudoOk])
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cTitulo` | Título da janela |
| `aCab` | Array com informações do cabeçalho (formato Enchoice): `[n][1]=Variável private`, `[n][2]={Linha,Coluna}`, `[n][3]=Título`, `[n][4]=Picture`, `[n][5]=Validação`, `[n][6]=F3`, `[n][7]=Habilitado` |
| `aRoda` | Array com informações do rodapé (mesmo formato que `aCab`) |
| `aGrid` | Array com coordenadas da GetDados(). Padrão: `{44,5,118,315}` |
| `nOpc` | Opção selecionada: 2=Visualizar, 3=Incluir, 4=Alterar, 5=Excluir |
| `cLinhaOk` | Função para validação da linha na GetDados() |
| `cTudoOk` | Função para validação na confirmação da interface |

**Retorno:** Lógico — indica se a interface foi confirmada ou cancelada.

**Exemplo: Utilização da Modelo2() para visualização do Cadastro de Tabelas (SX5)**

```advpl
#include "protheus.ch"

USER FUNCTION MBrw2Sx5()
    Local cAlias := "SX5"
    Private cCadastro := "Arquivo de Tabelas"
    Private aRotina   := {}
    Private cDelFunc  := ".T."

    AADD(aRotina, {"Pesquisar", "AxPesqui",  0, 1})
    AADD(aRotina, {"Visualizar","U_SX52Vis", 0, 2})
    AADD(aRotina, {"Incluir",   "U_SX52Inc", 0, 3})
    AADD(aRotina, {"Alterar",   "U_SX52Alt", 0, 4})
    AADD(aRotina, {"Excluir",   "U_SX52Exc", 0, 5})

    dbSelectArea(cAlias)
    dbSetOrder(1)
    mBrowse(6, 1, 22, 75, cAlias)
Return

USER FUNCTION SX52INC(cAlias, nReg, nOpc)
    Local cTitulo  := "Inclusao de itens - Arquivo de Tabelas"
    Local aCab     := {}
    Local aRoda    := {}
    Local aGrid    := {80, 005, 050, 300}
    Local cLinhaOk := "AllwaysTrue()"
    Local cTudoOk  := "AllwaysTrue()"
    Local lRetMod2 := .F.
    Local nColuna  := 0

    Private aCols    := {}
    Private aHeader  := {}
    Private cX5Filial := xFilial("SX5")
    Private cX5Tabela := SPACE(5)

    // Montagem do array de cabeçalho
    // AADD(aCab, {"Variável", {L,C}, "Título", "Picture", "Valid", "F3", lEnable})
    AADD(aCab, {"cX5Filial", {015, 010}, "Filial", "@!", , , .F.})
    AADD(aCab, {"cX5Tabela", {015, 080}, "Tabela", "@!", , , .T.})

    // Montagem do aHeader
    AADD(aHeader, {"Chave",    "X5_CHAVE",  "@!", 5,  0, "AllwaysTrue()", "", "C", "", "R"})
    AADD(aHeader, {"Descricao","X5_DESCRI", "@!", 40, 0, "AllwaysTrue()", "", "C", "", "R"})

    // Montagem do aCols
    aCols := Array(1, Len(aHeader) + 1)

    // Inicialização do aCols
    For nColuna := 1 to Len(aHeader)
        If aHeader[nColuna][8] == "C"
            aCols[1][nColuna] := SPACE(aHeader[nColuna][4])
        ElseIf aHeader[nColuna][8] == "N"
            aCols[1][nColuna] := 0
        ElseIf aHeader[nColuna][8] == "D"
            aCols[1][nColuna] := CTOD("")
        ElseIf aHeader[nColuna][8] == "L"
            aCols[1][nColuna] := .F.
        ElseIf aHeader[nColuna][8] == "M"
            aCols[1][nColuna] := ""
        Endif
    Next nColuna
    aCols[1][Len(aHeader) + 1] := .F. // Linha não deletada

    lRetMod2 := Modelo2(cTitulo, aCab, aRoda, aGrid, nOpc, cLinhaOk, cTudoOk)

    IF lRetMod2
        For nLinha := 1 to len(aCols)
            Reclock("SX5", .T.)
            SX5->X5_FILIAL := cX5Filial
            SX5->X5_TABELA := cX5Tabela
            For nColuna := 1 to Len(aHeader)
                SX5->&(aHeader[nColuna][2]) := aCols[nLinha][nColuna]
            Next nColuna
            MsUnLock()
        Next nLinha
    ELSE
        MsgAlert("Você cancelou a operação", "MBRW2SX5")
    ENDIF
Return()
```

---

## 2.7. Modelo3()

O Modelo 3 é uma tela para manutenção em vários registros de uma só vez, relacionada a registros de outra tabela (relacionamento "pai e filho"). Por exemplo: manutenção de um pedido de vendas, com cabeçalho em uma tabela e itens em outra.

A tela de Modelo 3 é constituída de: `MsDialog`, `EnchoiceBar`, `Enchoice`, `MsNewGetDados`, `Say` e `Get`.

### 2.7.1. Estrutura de um programa utilizando a Modelo3()

**Linhas do programa:**

| Linha | Descrição |
|-------|-----------|
| 1-5 | Função principal: declaração de variáveis, acesso à tabela, chamada da MBrowse |
| 7-22 | Função de visualização/alteração/exclusão: variáveis de memória M->???, aHeader, aCOLS, MsDialog, Enchoice, MsGetDados, ativação, gravação |
| 24-35 | Função de inclusão: variáveis M->???, aHeader, aCOLS, MsDialog, TSay, TGet, MsGetDados, ativação, gravação |

**Rotina principal:**

```advpl
#Include "Protheus.ch"

User Function xModelo3()
    Private cCadastro := "Protótipo Modelo 3"
    Private aRotina   := {}
    Private oCliente
    Private oTotal
    Private cCliente  := ""
    Private nTotal    := 0
    Private bCampo    := {|nField| FieldName(nField)}
    Private aSize     := {}
    Private aInfo     := {}
    Private aObj      := {}
    Private aPObj     := {}
    Private aPGet     := {}

    // Retorna a área útil das janelas Protheus
    aSize := MsAdvSize()

    // Três áreas na janela:
    // 1ª - Enchoice (80 pontos pixel)
    // 2ª - MsGetDados (o que sobrar)
    // 3ª - Rodapé (15 pontos pixel)
    AADD(aObj, {100, 080, .T., .F.})
    AADD(aObj, {100, 100, .T., .T.})
    AADD(aObj, {100, 015, .T., .F.})

    // Cálculo automático das dimensões dos objetos (altura/largura) em pixel
    aInfo := {aSize[1], aSize[2], aSize[3], aSize[4], 3, 3}
    aPObj := MsObjSize(aInfo, aObj)

    // Cálculo automático de dimensões dos objetos MSGET
    aPGet := MsObjGetPos((aSize[3] - aSize[1]), 315, {{004, 024, 240, 270}})

    AADD(aRotina, {"Pesquisar",  "AxPesqui",   0, 1})
    AADD(aRotina, {"Visualizar", 'U_Mod3Mnt',  0, 2})
    AADD(aRotina, {"Incluir",    'U_Mod3Inc',  0, 3})
    AADD(aRotina, {"Alterar",    'U_Mod3Mnt',  0, 4})
    AADD(aRotina, {"Excluir",    'U_Mod3Mnt',  0, 5})

    dbSelectArea("ZA1")
    dbSetOrder(1)
    dbGoTop()
    MBrowse(, , , , "ZA1")
Return
```

**Função de Inclusão:**

```advpl
User Function Mod3Inc(cAlias, nReg, nOpc)
    Local oDlg
    Local oGet
    Local nX    := 0
    Local nOpcA := 0

    Private aHeader := {}
    Private aCOLS   := {}
    Private aGets   := {}
    Private aTela   := {}

    dbSelectArea(cAlias)
    dbSetOrder(1)
    For nX := 1 To FCount()
        M->&(Eval(bCampo, nX)) := CriaVar(FieldName(nX), .T.)
    Next nX

    Mod3aHeader()
    Mod3aCOLS(nOpc)

    DEFINE MSDIALOG oDlg TITLE cCadastro FROM aSize[7],aSize[1] TO aSize[6],aSize[5] OF oMainWnd PIXEL

    EnChoice(cAlias, nReg, nOpc, , , , , aPObj[1])

    // Atualização do nome do cliente
    @ aPObj[3,1],aPGet[1,1] SAY "Cliente: "  SIZE 70,7 OF oDlg PIXEL
    @ aPObj[3,1],aPGet[1,2] SAY oCliente VAR cCliente SIZE 98,7 OF oDlg PIXEL

    // Atualização do total
    @ aPObj[3,1],aPGet[1,3] SAY "Valor Total: " SIZE 70,7 OF oDlg PIXEL
    @ aPObj[3,1],aPGet[1,4] SAY oTotal VAR nTotal PICT "@E 9,999,999,999.99" SIZE 70,7 OF oDlg PIXEL

    oGet := MSGetDados():New(aPObj[2,1], aPObj[2,2], aPObj[2,3], aPObj[2,4],
                             nOpc, "U_Mod3LOk()", ".T.", "+ZA2_ITEM", .T.)

    ACTIVATE MSDIALOG oDlg ON INIT EnchoiceBar(oDlg,
        {|| IIF(Mod3TOk() .And. Obrigatorio(aGets, aTela), (nOpcA := 1, oDlg:End()), NIL)},
        {|| oDlg:End()})

    If nOpcA == 1 .And. nOpc == 3
        Mod3Grv(nOpc)
        ConfirmSXE()
    Endif
Return
```

**Função de Visualização, Alteração e Exclusão:**

```advpl
User Function Mod3Mnt(cAlias, nReg, nOpc)
    Local oDlg
    Local oGet
    Local nX    := 0
    Local nOpcA := 0

    Private aHeader := {}
    Private aCOLS   := {}
    Private aGets   := {}
    Private aTela   := {}
    Private aREG    := {}

    dbSelectArea(cAlias)
    dbSetOrder(1)
    For nX := 1 To FCount()
        M->&(Eval(bCampo, nX)) := FieldGet(nX)
    Next nX

    Mod3aHeader()
    Mod3aCOLS(nOpc)

    DEFINE MSDIALOG oDlg TITLE cCadastro FROM aSize[7],aSize[1] TO aSize[6],aSize[5] OF oMainWnd PIXEL

    EnChoice(cAlias, nReg, nOpc, , , , , aPObj[1])

    @ aPObj[3,1],aPGet[1,1] SAY "Cliente: "   SIZE 70,7 OF oDlg PIXEL
    @ aPObj[3,1],aPGet[1,2] SAY oCliente VAR cCliente SIZE 98,7 OF oDlg PIXEL
    @ aPObj[3,1],aPGet[1,3] SAY "Valor Total: " SIZE 70,7 OF oDlg PIXEL
    @ aPObj[3,1],aPGet[1,4] SAY oTotal VAR nTotal PICTURE "@E 9,999,999,999.99" SIZE 70,7 OF oDlg PIXEL

    U_Mod3Cli()

    oGet := MSGetDados():New(aPObj[2,1], aPObj[2,2], aPObj[2,3], aPObj[2,4],
                             nOpc, "U_Mod3LOk()", ".T.", "+ZA2_ITEM", .T.)

    ACTIVATE MSDIALOG oDlg ON INIT EnchoiceBar(oDlg,
        {|| IIF(Mod3TOk() .And. Obrigatorio(aGets, aTela), (nOpcA := 1, oDlg:End()), NIL)},
        {|| oDlg:End()})

    If nOpcA == 1 .And. (nOpc == 4 .Or. nOpc == 5)
        Mod3Grv(nOpc, aREG)
    Endif
Return
```

**Função para montar o vetor aHeader:**

```advpl
Static Function Mod3aHeader()
    Local aArea := GetArea()

    dbSelectArea("SX3")
    dbSetOrder(1)
    dbSeek("ZA2")
    While !EOF() .And. X3_ARQUIVO == "ZA2"
        If X3Uso(X3_USADO) .And. cNivel >= X3_NIVEL
            AADD(aHeader, {Trim(X3Titulo()), X3_CAMPO, X3_PICTURE, X3_TAMANHO,
                           X3_DECIMAL, X3_DECIMAL, X3_VALID, X3_USADO,
                           X3_TIPO, X3_ARQUIVO, X3_ARQUIVO, X3_ARQUIVO,
                           X3_ARQUIVO, X3_CONTEXT})
        Endif
        dbSkip()
    End
    RestArea(aArea)
Return
```

**Função para montar o vetor aCols:**

```advpl
Static Function Mod3aCOLS(nOpc)
    Local aArea  := GetArea()
    Local cChave := ""
    Local cAlias := "ZA2"
    Local nI     := 0

    If nOpc <> 3
        cChave := ZA1->ZA1_NUM
        dbSelectArea(cAlias)
        dbSetOrder(1)
        dbSeek(xFilial(cAlias) + cChave)
        While !EOF() .And. ZA2->(ZA2_FILIAL + ZA2_NUM) == xFilial(cAlias) + cChave
            AADD(aREG, ZA2->(RecNo()))
            AADD(aCOLS, Array(Len(aHeader) + 1))
            For nI := 1 To Len(aHeader)
                If aHeader[nI, 10] == "V"
                    aCOLS[Len(aCOLS), nI] := CriaVar(aHeader[nI, 2], .T.)
                Else
                    aCOLS[Len(aCOLS), nI] := FieldGet(FieldPos(aHeader[nI, 2]))
                Endif
            Next nI
            aCOLS[Len(aCOLS), Len(aHeader) + 1] := .F.
            dbSkip()
        EndDo
    Else
        AADD(aCOLS, Array(Len(aHeader) + 1))
        For nI := 1 To Len(aHeader)
            aCOLS[1, nI] := CriaVar(aHeader[nI, 2], .T.)
        Next nI
        aCOLS[1, GdFieldPos("ZA2_ITEM")]      := "01"
        aCOLS[1, Len(aHeader) + 1]            := .F.
    Endif
    Restarea(aArea)
Return
```

**Função para atribuir o nome do cliente à variável:**

```advpl
User Function Mod3Cli()
    cCliente := Posicione("SA1", 1, xFilial("SA1") + M->(ZA1_CLIENT + ZA1_LOJA), "A1_NREDUZ")
    oCliente:Refresh()
Return(.T.)
```

**Função para validar a mudança de linha na MsGetDados():**

```advpl
User Function Mod3LOk()
    Local nI := 0
    nTotal := 0
    For nI := 1 To Len(aCOLS)
        If aCOLS[nI, Len(aHeader) + 1]
            Loop
        Endif
        nTotal += Round(aCOLS[nI, GdFieldPos("ZA2_QTDVEN")] *
                        aCOLS[nI, GdFieldPos("ZA2_PRCVEN")], 2)
    Next nI
    oTotal:Refresh()
Return(.T.)
```

**Função de validação geral (Mod3TOk):**

```advpl
Static Function Mod3TOk()
    Local nI  := 0
    Local lRet := .T.

    For nI := 1 To Len(aCOLS)
        If aCOLS[nI, Len(aHeader) + 1]
            Loop
        Endif
        If Empty(aCOLS[nI, GdFieldPos("ZA2_PRODUT")]) .And. lRet
            MsgAlert("Campo PRODUTO preenchimento obrigatorio", cCadastro)
            lRet := .F.
        Endif
        If Empty(aCOLS[nI, GdFieldPos("ZA2_QTDVEN")]) .And. lRet
            MsgAlert("Campo QUANTIDADE preenchimento obrigatorio", cCadastro)
            lRet := .F.
        Endif
        If Empty(aCOLS[nI, GdFieldPos("ZA2_PRCVEN")]) .And. lRet
            MsgAlert("Campo PRECO UNITARIO preenchimento obrigatorio", cCadastro)
            lRet := .F.
        Endif
        If !lRet
            Exit
        Endif
    Next nI
Return(lRet)
```

**Função para efetuar a gravação dos dados em ZA1 e ZA2:**

```advpl
Static Function Mod3Grv(nOpc, aAltera)
    Local nX := 0
    Local nI := 0

    // Se for inclusão
    If nOpc == 3
        dbSelectArea("ZA2")
        dbSetOrder(1)
        For nX := 1 To Len(aCOLS)
            If !aCOLS[nX, Len(aCOLS) + 1]
                RecLock("ZA2", .T.)
                For nI := 1 To Len(aHeader)
                    FieldPut(FieldPos(Trim(aHeader[nI, 2])), aCOLS[nX, nI])
                Next nI
                ZA2->ZA2_FILIAL := xFilial("ZA2")
                ZA2->ZA2_NUM    := M->ZA1_NUM
                MsUnLock()
            Endif
        Next nX
        dbSelectArea("ZA1")
        RecLock("ZA1", .T.)
        For nX := 1 To FCount()
            If "FILIAL" $ FieldName(nX)
                FieldPut(nX, xFilial("ZA1"))
            Else
                FieldPut(nX, M->&(Eval(bCampo, nX)))
            Endif
        Next nX
        MsUnLock()
    Endif

    // Se for alteração
    If nOpc == 4
        dbSelectArea("ZA2")
        dbSetOrder(1)
        For nX := 1 To Len(aCOLS)
            If nX <= Len(aREG)
                dbGoto(aREG[nX])
                RecLock("ZA2", .F.)
                If aCOLS[nX, Len(aHeader) + 1]
                    dbDelete()
                Endif
            Else
                If !aCOLS[nX, Len(aHeader) + 1]
                    RecLock("ZA2", .T.)
                Endif
            Endif
            If !aCOLS[nX, Len(aHeader) + 1]
                For nI := 1 To Len(aHeader)
                    FieldPut(FieldPos(Trim(aHeader[nI, 2])), aCOLS[nX, nI])
                Next nI
                ZA2->ZA2_FILIAL := xFilial("ZA2")
                ZA2->ZA2_NUM    := M->ZA1_NUM
            Endif
            MsUnLock()
        Next nX
        dbSelectArea("ZA1")
        RecLock("ZA1", .F.)
        For nX := 1 To FCount()
            If "FILIAL" $ FieldName(nX)
                FieldPut(nX, xFilial("ZA1"))
            Else
                FieldPut(nX, M->&(Eval(bCampo, nX)))
            Endif
        Next
        MsUnLock()
    Endif

    // Se for exclusão
    If nOpc == 5
        dbSelectArea("ZA2")
        dbSetOrder(1)
        dbSeek(xFilial("ZA2") + M->ZA1_NUM)
        While !EOF() .And. ZA2->(ZA2_FILIAL + ZA2_NUM) == xFilial("ZA2") + M->ZA1_NUM
            RecLock("ZA2")
            dbDelete()
            MsUnLock()
            dbSkip()
        End
        dbSelectArea("ZA1")
        RecLock("ZA1", .F.)
        dbDelete()
        MsUnLock()
    Endif
Return
```

### 2.7.2. Função Modelo3()

A função `Modelo3()` é uma interface pré-definida pela Microsiga que implementa de forma padronizada os componentes para manipulação de estruturas de dados nas quais o cabeçalho e os itens estão em tabelas separadas.

Utiliza os seguintes componentes visuais:
- `MsDialog()`
- `Enchoice()`
- `EnchoiceBar()`
- `MsNewGetDados()`

A função `Modelo3()` não implementa as regras de visualização, inclusão, alteração e exclusão. A inicialização dos campos da `Enchoice()` deve ser realizada pela rotina que "suporta" a execução da `Modelo3()`, normalmente através de `RegToMemory()`.

**Sintaxe:**
```advpl
Modelo3([cTitulo], [cAliasE], [cAliasGetD], [aCposE], [cLinOk], [cTudOk],
        [nOpcE], [nOpcG], [cFieldOk])
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cTitulo` | Título da janela |
| `cAliasE` | Alias da tabela utilizada na Enchoice |
| `cAliasGetD` | Alias da tabela utilizada na GetDados |
| `aCposE` | Nomes dos campos da Enchoice: `AADD(aCposE, {"nome_campo"})` |
| `cLinhaOk` | Função para validação da linha na GetDados() |
| `cTudoOk` | Função para validação na confirmação da interface |
| `nOpcE` | Opção para controle da Enchoice: 2=Visualizar, 3=Incluir, 4=Alterar, 5=Excluir |
| `nOpcG` | Opção para controle da GetDados: 2=Visualizar, 3=Incluir, 4=Alterar, 5=Excluir |
| `cFieldOk` | Validação dos campos da Enchoice() |

**Retorno:** Lógico — indica se a interface foi confirmada ou cancelada.

**Exemplo: Utilização da Modelo3() para Pedidos de Vendas (SC5, SC6)**

```advpl
#INCLUDE "protheus.ch"

User Function MbrwMod3()
    Private cCadastro := "Pedidos de Venda"
    Private aRotina   := {}
    Private cDelFunc  := ".T."
    Private cAlias    := "SC5"

    AADD(aRotina, {"Pesquisa", "AxPesqui",  0, 1})
    AADD(aRotina, {"Visual",   "U_Mod3All", 0, 2})
    AADD(aRotina, {"Inclui",   "U_Mod3All", 0, 3})
    AADD(aRotina, {"Altera",   "U_Mod3All", 0, 4})
    AADD(aRotina, {"Exclui",   "U_Mod3All", 0, 5})

    dbSelectArea(cAlias)
    dbSetOrder(1)
    mBrowse(6, 1, 22, 75, cAlias)
Return

User Function Mod3All(cAlias, nReg, nOpcx)
    Local cTitulo   := "Cadastro de Pedidos de Venda"
    Local cAliasE   := "SC5"
    Local cAliasG   := "SC6"
    Local cLinOk    := "AllwaysTrue()"
    Local cTudOk    := "AllwaysTrue()"
    Local cFieldOk  := "AllwaysTrue()"
    Local aCposE    := {}
    Local nUsado, nX := 0

    Do Case
        Case nOpcx==3; nOpcE:=3; nOpcG:=3  // Incluir
        Case nOpcx==4; nOpcE:=3; nOpcG:=3  // Alterar
        Case nOpcx==2; nOpcE:=2; nOpcG:=2  // Visualizar
        Case nOpcx==5; nOpcE:=2; nOpcG:=2  // Excluir
    EndCase

    // Cria variáveis M->????? da Enchoice
    RegToMemory("SC5", (nOpcx==3 .or. nOpcx==4))

    // Cria aHeader e aCols da GetDados
    nUsado := 0
    dbSelectArea("SX3")
    dbSeek("SC6")
    aHeader := {}
    While !Eof() .And. (x3_arquivo=="SC6")
        If Alltrim(x3_campo)=="C6_ITEM"
            dbSkip()
            Loop
        Endif
        If X3USO(x3_usado) .And. cNivel>=x3_nivel
            nUsado := nUsado + 1
            Aadd(aHeader, {TRIM(x3_titulo), x3_campo, x3_picture,
                           x3_tamanho, x3_decimal, "AllwaysTrue()",
                           x3_usado, x3_tipo, x3_arquivo, x3_context})
        Endif
        dbSkip()
    End

    If nOpcx == 3 // Incluir
        aCols := {Array(nUsado + 1)}
        aCols[1, nUsado + 1] := .F.
        For nX := 1 to nUsado
            aCols[1, nX] := CriaVar(aHeader[nX, 2])
        Next
    Else
        aCols := {}
        dbSelectArea("SC6")
        dbSetOrder(1)
        dbSeek(xFilial() + M->C5_NUM)
        While !eof() .and. C6_NUM==M->C5_NUM
            AADD(aCols, Array(nUsado + 1))
            For nX := 1 to nUsado
                aCols[Len(aCols), nX] := FieldGet(FieldPos(aHeader[nX, 2]))
            Next
            aCols[Len(aCols), nUsado + 1] := .F.
            dbSkip()
        End
    Endif

    If Len(aCols) > 0
        aCposE    := {"C5_CLIENTE"}
        lRetMod3  := Modelo3(cTitulo, cAliasE, cAliasG, aCposE, cLinOk,
                             cTudOk, nOpcE, nOpcG, cFieldOk)
        If lRetMod3
            Aviso("Modelo3()", "Confirmada operacao!", {"Ok"})
        Endif
    Endif
Return
```

---

## 3. Transações

Em ambiente multiusuário é necessário um controle de concorrência das atualizações no banco de dados. Uma transação é uma unidade que preserva consistência (Atomicidade, Consistência, Isolamento e Durabilidade).

O Protheus possui as seguintes funções de controle de transações:
- `BEGIN TRANSACTION / END TRANSACTION`
- `BeginTran / DisarmTransaction / EndTran`

---

## 3.1. Begin Transaction

Define que as operações seguintes, delimitadas pelo `END TRANSACTION`, devem ser processadas como uma transação — um bloco único e indivisível. Durante recuperação de falha, todas as operações serão integralmente desfeitas.

**Exemplo:**

```advpl
BEGIN TRANSACTION
    RecLock("SB2")
    ...
    MsUnLock()
END TRANSACTION
```

---

## 3.2. BeginTran

Inicializa uma transação que permite o término por meio de uma condição. O `END TRANSACTION` não pode ter sua interpretação vinculada a uma condição — nesses casos use `BeginTran() ... EndTran()`.

> No uso do `BeginTran() ... EndTran()` é recomendável utilizar a função `MsUnLockAll()` para destravar todos os registros eventualmente locados.

**Exemplo:**

```advpl
AADD(xAutoCab, {"A1_FILIAL", xFilial("SA1"), Nil})
AADD(xAutoCab, {"A1_COD",    "000001",        Nil})
AADD(xAutoCab, {"A1_LOJA",   "01",            Nil})
AADD(xAutoCab, {"A1_NOME",   "TESTE - 000001",Nil})

BeginTran()
lMsErroAuto := .F.
MsExecAuto({|x,y| MATA030(x,y)}, xAutoCab, 3)
IF lMsErroAuto
    DisarmTransaction()
ELSE
    EndTran()
ENDIF
MsUnlockAll()
```

---

## 4. Relatórios

Os relatórios desenvolvidos em ADVPL possuem um padrão de desenvolvimento que depende mais de layout e tipos de parâmetros do que qualquer outro tipo de informação.

---

## 4.1. TReport

O Protheus oferece o recurso de personalização para relatórios de cadastros e movimentações. Principais funcionalidades:
- Definição de cores, estilos, tamanho, fontes, quebras, máscaras para cada seção
- Criação de fórmulas e funções (Soma, Média, etc.)
- Possibilidade de salvar configurações por usuário
- Criação de gráficos

Os relatórios personalizados são gravados com extensão `.PRT`, diferenciando-se dos relatórios padrões (extensão `.##R`).

O `TReport` é uma classe de impressão que substitui as funções `SetPrint`, `SetDefault`, `RptStatus` e `Cabec`.

**Estrutura do componente TReport:**
- O relatório (`TReport`) contém 1 ou mais seções (`TRSection`)
- Uma seção (`TRSection`) pode conter 1 ou mais seções
- A seção contém células pré-definidas e células selecionadas pelo usuário
- A seção também contém quebras (`TRBreak`) para impressão de totalizadores (`TRFunction`)
- Os totalizadores são incluídos pela seção que automaticamente inclui no relatório

**Pré-requisito:** Verificar se o repositório está com o Release 4 do Protheus-8 ou superior. Use `TRepInUse()` para verificar se a lib está liberada.

**Parâmetro MV_TREPORT:**
| Valor | Descrição |
|-------|-----------|
| 1 | Utiliza relatório no formato tradicional (antigo) |
| 2 | Utiliza relatório personalizável |
| 3 | Pergunta qual relatório será utilizado |

**Exemplo: Relatório simples com uma Section**

```advpl
User Function RSimples()
    Local oReport := nil
    oReport := RptDef()
    oReport:PrintDialog()
Return()

Static Function RptDef()
    Local oReport   := Nil
    Local oSection1 := Nil
    Local oBreak
    Local oFunction

    // TReport():New(cNome, cTitulo, cPerguntas, bBlocoCodigo, cDescricao)
    oReport := TReport():New("Exemplo01", "Cadastro Produtos", /*cPergunta*/,
                             {|oReport| ReportPrint(oReport)},
                             "Descrição do meu relatório")

    // Relatório em retrato
    oReport:SetPortrait()

    // Define se os totalizadores serão impressos em linha ou coluna
    oReport:SetTotalInLine(.F.)

    // Montando a primeira seção
    oSection1 := TRSection():New(oReport, "Produtos", {"SB1"}, NIL, .F., .T.)
    TRCell():New(oSection1, "B1_COD",   "SB1", "Produto",    "@!", 30 )
    TRCell():New(oSection1, "B1_DESC",  "SB1", "Descrição",  "@!", 100)
    TRCell():New(oSection1, "B1_LOCPAD","SB1", "Arm.Padrao", "@!", 20 )
    TRCell():New(oSection1, "B1_POSIPI","SB1", "NCM",        "@!", 30 )

    TRFunction():New(oSection1:Cell("B1_COD"), NIL, "COUNT", , , , , .F., .T.)
Return(oReport)

Static Function ReportPrint(oReport)
    Local oSection1 := oReport:Section(1)
    Local cQuery    := ""
    Local cAlias    := GetNextAlias()

    cPart  := "% AND B1_COD >= '" + MV_PAR01 + "' "
    cPart  += "  AND B1_COD <= '" + MV_PAR02 + "' %"

    BeginSql alias cAlias
        SELECT B1_COD, B1_DESC, B1_LOCPAD, B1_POSIPI
        FROM %table:SB1% SB1
        WHERE B1_FILIAL = %xfilial:SB1%
        AND B1_MSBLQL <> '1'
        AND SB1.%notDel%
        %exp:cPart%
        ORDER BY B1_COD
    EndSql

    dbSelectArea(cAlias)
    (cAlias)->(dbGoTop())
    oReport:SetMeter((cAlias)->(LastRec()))

    While !(cAlias)->(EOF())
        If oReport:Cancel()
            Exit
        EndIf
        oReport:IncMeter()
        IncProc("Imprimindo " + alltrim((cAlias)->B1_DESC))

        oSection1:Init()
        oSection1:Cell("B1_COD"   ):SetValue((cAlias)->B1_COD   )
        oSection1:Cell("B1_DESC"  ):SetValue((cAlias)->B1_DESC  )
        oSection1:Cell("B1_LOCPAD"):SetValue((cAlias)->B1_LOCPAD)
        oSection1:Cell("B1_POSIPI"):SetValue((cAlias)->B1_POSIPI)
        oSection1:Printline()

        (cAlias)->(dbSkip())
        oReport:ThinLine()
    Enddo

    oSection1:Finish()
Return(NIL)
```

**Exemplo: Relatório com método BeginQuery**

```advpl
User Function tReport_SQL()
    Local oReport
    CriaPerg()
    Pergunte("XCLIVEND", .F.)
    oReport := ReportDef()
    oReport:PrintDialog()
Return(Nil)

Static Function ReportDef()
    Local oReport
    Local oSection
    Local oBreak

    oReport := TReport():New("ClinteXVendedor", "Relatorio de Clientes X Vendedor",
                             "XCLIVEND",
                             {|oReport| PrintReport(oReport)},
                             "Relatorio de visitas de vendedores nos clientes")

    oSection := TRSection():New(oReport, "Dados dos Clientes", {"SA1"})
    TRCell():New(oSection, "A1_VEND",    "SA1")
    TRCell():New(oSection, "A1_COD",     "SA1", "Cliente")
    TRCell():New(oSection, "A1_LOJA",    "SA1")
    TRCell():New(oSection, "A1_NOME",    "SA1")
    TRCell():New(oSection, "A1_END",     "SA1")
    TRCell():New(oSection, "A1_CEP",     "SA1")
    TRCell():New(oSection, "A1_CONTATO", "SA1")
    TRCell():New(oSection, "A1_TEL",     "SA1")
    TRCell():New(oSection, "A1_EST",     "SA1")

    // Quebra por Estado
    oBreak := TRBreak():New(oSection, oSection:Cell("A1_EST"), "Sub Total Estados")

    // Contagem por código
    TRFunction():New(oSection:Cell("A1_COD"), NIL, "COUNT", oBreak)
Return(oReport)

Static Function PrintReport(oReport)
    Local oSection := oReport:Section(1)
    Local cPart    := ""

    oSection:BeginQuery()

    cPart  := "% AND A1_COD >= '" + MV_PAR01 + "' "
    cPart  += "  AND A1_COD <= '" + MV_PAR02 + "' %"

    BeginSql alias "QRYSA1"
        SELECT A1_COD, A1_LOJA, A1_NOME, A1_VEND, A1_ULTVIS,
               A1_TEMVIS, A1_TEL, A1_CONTATO, A1_EST
        FROM %table:SA1% SA1
        WHERE A1_FILIAL = %xfilial:SA1%
        AND A1_MSBLQL <> '1'
        AND SA1.%notDel%
        %exp:cPart%
        ORDER BY A1_EST Desc
    EndSql

    aRetSql := GetLastQuery()
    oSection:EndQuery()
    oSection:Print()
Return(Nil)

Static Function CriaPerg()
    cPerg := "XCLIVEND"
    PutSx1(cPerg, "01", "Cliente de", "", "", "mv_ch1", "C", 6, 0, 0, "M", "", "SA1", "", "", "MV_PAR01")
    PutSx1(cPerg, "02", "Cliente ate", "", "", "mv_ch2", "C", 6, 0, 0, "M", "", "SA1", "", "", "MV_PAR02")
Return
```

### 4.1.1. Impressão do relatório personalizável

Cada componente da tela de impressão do TReport deve ser configurado no programa.

### 4.1.2. Parâmetros de impressão

| Opção | Descrição |
|-------|-----------|
| Servidor | Gravado no diretório definido na senha do usuário (padrão `\SPOOL\`) |
| Local | Abre janela para escolha do local na máquina do usuário |
| Spool | Direciona para impressão via Windows |
| E-mail | Envia por e-mail (requer configuração de `MV_RELACNT`, `MV_RELPSW`, `MV_RELSERV`) |

### 4.1.3. Personalização

É possível configurar colunas do layout, acumuladores, cabeçalhos, linhas, fontes, tamanhos, cores, etc.

### 4.1.4. Definindo a Função ReportDef()

A função `ReportDef()` é responsável pela construção do layout do relatório (`oReport`). Define colunas, campos e informações a imprimir através dos comandos:

1. **DEFINE REPORT** — Cria o objeto Report via `TReport():New()`. Estrutura: 1 ou mais seções, que contêm células, quebras e totalizadores.
2. **DEFINE SECTION** — Define as seções (`oSection`) via `TRSection():New()`. Representa diferentes grupos de informações. Pode ter query, filtro ou índice.
3. **DEFINE CELL** — Define as células (campos a imprimir) via `TRCell():New()`. Cada célula é uma informação que será impressa.

---

## 4.2. Funções Utilizadas para Desenvolvimento de Relatórios

### 4.2.1. Pergunte()

Inicializa as variáveis de pergunta (`mv_par01`, ...) baseadas na pergunta cadastrada no Dicionário de Dados (SX1).

**Sintaxe:**
```advpl
Pergunte(cPergunta, [lAsk], [cTitle])
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cPergunta` | Pergunta cadastrada no SX1 |
| `lAsk` | Indica se exibirá a tela para edição |
| `cTitle` | Título do diálogo |

**Retorno:** Lógico — `.T.` se confirmada, `.F.` se cancelada.

---

## 4.3. AjustaSX1()

Permite a inclusão simultânea de vários itens de perguntas para um grupo no SX1 da empresa ativa.

**Sintaxe:**
```advpl
AJUSTASX1(cPerg, aPergs)
```

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `cPerg` | Grupo de perguntas do SX1 (X1_GRUPO) |
| `aPergs` | Array com estrutura dos campos que serão gravados no SX1 |

**Estrutura do item do array aPergs:**

| Posição | Campo | Tipo | Descrição |
|---------|-------|------|-----------|
| 01 | X1_PERGUNT | Caractere | Descrição da pergunta em português |
| 02 | X1_PERSPA | Caractere | Descrição da pergunta em espanhol |
| 03 | X1_PERENG | Caractere | Descrição da pergunta em inglês |
| 04 | X1_VARIAVL | Caractere | Nome da variável de controle auxiliar (mv_ch) |
| 05 | X1_TIPO | Caractere | Tipo do parâmetro |
| 06 | X1_TAMANHO | Numérico | Tamanho do conteúdo do parâmetro |
| 07 | X1_DECIMAL | Numérico | Número de decimais para conteúdos numéricos |
| 08 | X1_PRESEL | Numérico | Define qual opção do combo é a padrão |
| 09 | X1_GSC | Caractere | G=Get ou C=Choice (combo) |
| 10 | X1_VALID | Caractere | Expressão de validação do parâmetro |
| 11 | X1_VAR01 | Caractere | Nome da variável MV_PAR+"Ordem" |
| 12-35 | X1_DEF0x... | Caractere | Opções do combo (português/espanhol/inglês/conteúdo) |
| 36 | X1_F3 | Caractere | Código da consulta F3 vinculada |
| 37 | X1_GRPSXG | Caractere | Código do grupo de campos SXG |
| 38 | X1_PYME | Caractere | Disponível no ambiente Pyme |
| 39 | X1_HELP | Caractere | Conteúdo do campo X1_HELP |
| 40 | X1_PICTURE | Caractere | Picture de formatação |
| 41 | aHelpPor | Array | Linhas de help em português (até 40 chars/linha) |
| 42 | aHelpEng | Array | Linhas de help em inglês (até 40 chars/linha) |
| 43 | aHelpSpa | Array | Linhas de help em espanhol (até 40 chars/linha) |

### 4.3.1. PutSX1()

Permite a inclusão de um único item de pergunta em um grupo do SX1.

**Sintaxe:**
```advpl
PutSx1(cGrupo, cOrdem, cPergunt, cPerSpa, cPerEng, cVar, cTipo, nTamanho,
       nDecimal, nPresel, cGSC, cValid, cF3, cGrpSxg, cPyme, cVar01,
       cDef01, cDefSpa1, cDefEng1, cCnt01, cDef02, cDefSpa2, cDefEng2,
       cDef03, cDefSpa3, cDefEng3, cDef04, cDefSpa4, cDefEng4,
       cDef05, cDefSpa5, cDefEng5, aHelpPor, aHelpEng, aHelpSpa, cHelp)
```

### 4.3.2. ParamBox()

Implementa uma tela de parâmetros sem necessidade de criar um grupo de perguntas no SX1. Disponibiliza CheckBox e RadioButtons (que a `Pergunte()` não oferece).

**Sintaxe:**
```advpl
ParamBox(aParamBox, cTitulo, aRet, bOk, aButtons, lCentered,
         nPosx, nPosy, oMainDlg, cLoad, lCanSave, lUserSave)
```

**Retorno:** `lOK` — indica se a tela foi cancelada ou confirmada.

**Tipos de parâmetros do aParamBox:**

| Tipo | Código | Estrutura |
|------|--------|-----------|
| MsGet | 1 | `[2]=Descrição`, `[3]=Inicializador`, `[4]=Picture`, `[5]=Validação`, `[6]=F3`, `[7]=When`, `[8]=Tamanho`, `[9]=Obrigatório` |
| Combo | 2 | `[2]=Descrição`, `[3]=Opção inicial`, `[4]=Array de opções`, `[5]=Tamanho`, `[6]=Validação`, `[7]=Obrigatório` |
| Radio | 3 | `[2]=Descrição`, `[3]=Opção inicial`, `[4]=Array de opções`, `[5]=Tamanho`, `[6]=Validação`, `[7]=Obrigatório`, `[8]=When` |
| CheckBox (com Say) | 4 | `[2]=Descrição`, `[3]=Inicial lógico`, `[4]=Texto`, `[5]=Tamanho`, `[6]=Validação`, `[7]=Obrigatório` |
| CheckBox (linha inteira) | 5 | `[2]=Descrição`, `[3]=Inicial lógico`, `[4]=Tamanho`, `[5]=Validação`, `[6]=Editável` |
| File | 6 | `[2]=Descrição`, `[3]=Inicializador`, `[4]=Picture`, `[5]=Validação`, `[6]=When`, `[7]=Tamanho`, `[8]=Obrigatório`, `[9]=Tipos de arquivo`, `[10]=Diretório inicial`, `[11]=Parâmetros cGetFile` |
| Filtro | 7 | `[2]=Descrição`, `[3]=Alias`, `[4]=Filtro inicial`, `[5]=When Botão Editar` |
| MsGet Password | 8 | igual ao tipo 1 |
| MsGet Say | 9 | `[2]=Texto`, `[3]=Tamanho`, `[4]=Altura`, `[5]=Negrito` |
| Range | 10 | `[2]=Descrição`, `[3]=Range Inicial`, `[4]=F3`, `[5]=Largura em pixels`, `[6]=Tipo`, `[7]=Tamanho`, `[8]=When` |
| MultiGet (Memo) | 11 | `[2]=Descrição`, `[3]=Inicializador`, `[4]=Validação`, `[5]=When`, `[6]=Obrigatório` |
| Filtro de usuário por Rotina | 12 | `[2]=Título`, `[3]=Alias`, `[4]=Filtro inicial`, `[5]=When` |

**Parâmetros:**

| Parâmetro | Descrição |
|-----------|-----------|
| `aParamBox` | Array de parâmetros conforme regra da ParamBox |
| `cTitulo` | Título da janela de parâmetros |
| `aRet` | Array passado por referência, retornado com o conteúdo de cada parâmetro |
| `bOk` | Bloco de código para validação do OK |
| `aButtons` | Array para adição de novos botões: `{nType, bAction, cTexto}` |
| `lCentered` | Se a tela será exibida centralizada |
| `nPosx` | Posição inicial linha |
| `nPosy` | Posição inicial coluna |
| `oMainDlg` | Janela de vinculação |
| `cLoad` | Nome do arquivo para salvar/ler respostas |
| `lCanSave` | Se as respostas podem ser salvas |
| `lUserSave` | Se o usuário pode salvar sua própria configuração |

> A ParamBox define parâmetros seguindo o princípio das variáveis `MV_PARxx`. Quando usada junto com parâmetros padrões (SX1 + Pergunte()), salvar os parâmetros padrões, chamar a ParamBox(), salvar o retorno em variáveis `MVPARBOXxx` e depois restaurar os parâmetros padrões.

**Exemplo:**

```advpl
User Function ParamBox()
    Local aRet      := {}
    Local aParamBox := {}
    Local aCombo    := {"Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"}
    Local i         := 0
    Private cCadastro := "xParambox"

    AADD(aParamBox, {1, "Produto",          Space(15), "", "", "SB1", "", 0, .F.})
    AADD(aParamBox, {2, "Tipo de cliente",  1, aCombo, 50, "", .F.})
    AADD(aParamBox, {3, "Mostra deletados", IIF(Set(_SET_DELETED), 1, 2), {"Sim","Não"}, 50, "", .F.})
    AADD(aParamBox, {4, "Marca todos ?",    .F., "Marque todos", 50, "", .F.})
    AADD(aParamBox, {5, "Marca todos ?",    .F., 50, "", .F.})
    AADD(aParamBox, {6, "Arquivo?",         Space(50), "", "", "", 50, .F., "Arquivo .DBF |*.DBF"})
    AADD(aParamBox, {7, "Monte o filtro",   "SX5", "X5_FILIAL==xFilial('SX5')"})
    AADD(aParamBox, {8, "Digite a senha",   Space(15), "", "", "", "", 80, .F.})

    If ParamBox(aParamBox, "Teste ParamBox...", @aRet)
        For i := 1 To Len(aRet)
            MsgInfo(aRet[i], "Opção escolhida")
        Next
    Endif
Return(NIL)
```

---

## 5. Utilizando Queries no Protheus

Podemos utilizar queries no Protheus quando acessamos bancos de dados via TopConnect. Queries bem construídas melhoram a eficiência das consultas e reduzem a sobrecarga no servidor. Normalmente uma query substitui um Loop (`While`) na programação convencional.

### TCQUERY()

```advpl
TCQUERY cSQL ALIAS cAlias NEW VIA "TOPCONN"
```

Durante a compilação, `TCQUERY()` é substituída por:
```advpl
dbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), "ALIAS", .T., .F.)
```

> É recomendável utilizar diretamente `DbUseArea() + TcGenQry()`.

### DbUseArea()

```advpl
DBUseArea(lNovaArea, cDriver, cTabela, cAlias, lCompartilhado, lSomenteLeitura)
```

| Parâmetro | Descrição |
|-----------|-----------|
| `lNovaArea` | `.T.` = abrir em nova workarea; `.F.` = workarea atual (fecha tabela anterior) |
| `cDriver` | Driver (RDD) a utilizar. Para query no SGBD: `"TOPCONN"` |
| `cTabela` | Nome da tabela ou retorno de `TcGenQry()` para query |
| `cAlias` | Nome dado ao ALIAS |
| `lCompartilhado` | `.T.` = modo compartilhado |
| `lSomenteLeitura` | `.T.` = apenas leitura |

**Exemplo com DbUseArea():**

```advpl
Local cAliasFor := GetNextAlias()
Local cSql      := ""

cSql := " Select A2_COD, "
cSql += "        A2_LOJA, "
cSql += "        A2_NREDUZ, "
cSql += "        A2_EST, "
cSql += "        A2_MSBLQL "
cSql += " FROM " + RetSQLName("SA2")
cSql += " Where A2_FILIAL = '" + xFilial('SA2') + "'"
cSql += "   AND D_E_L_E_T_ = ' ' "
cSql := ChangeQuery(cSql)

dbUseArea(.T., "TOPCONN", TCGENQRY(,,cSql), (cAliasFor), .F., .T.)
```

**Funções de apoio:**

| Função | Descrição |
|--------|-----------|
| `CHANGEQUERY(cSql)` | Efetua adequações necessárias à query para execução no banco de dados em uso |
| `RetSQLName("SA1")` | Retorna o nome padrão da tabela para seleção no banco |
| `xFilial("SA1")` | Retorna a filial corrente para uso na query |
| `TCSetField(cAlias, cCampo, cTipo, [nTamanho], [nDecimais])` | Compatibiliza tipos de dados retornados pela query |
| `GetNextAlias()` | Retorna um alias disponível para o record set |
| `TCGenQry(xPar1, xPar2, cQuery)` | Permite abertura de query no banco de dados |

---

## 5.1. Embedded SQL

O Embedded SQL facilita a escrita e leitura de queries, permitindo escrever o `SELECT` diretamente no código ADVPL sem concatenação de strings.

O bloco deve ser iniciado com `BeginSQL Alias` e finalizado com `EndSQL`. Não é permitido incluir funções dentro do bloco — guardar valores em variáveis antes do `BeginSQL`.

**Exemplo:**

```advpl
Local cAliasProd := GetNextAlias()

BeginSql Alias cAlias
    Column D1_QUANT   as Numeric(12,2)
    Column D1_EMISSAO as date
    %NOPARSER%
    SELECT D1_DOC,
           D1_FORNECE,
           D1_LOJA,
           D1_Serie,
           D1_QUANT,
           D1_ITEM,
           D1_EMISSAO
    FROM %TABLE:SD1%
    WHERE D1_FILIAL   = %xFilial:SD1%
    AND   D1_EMISSAO >= %EXP:pDatade%
    AND   D1_EMISSAO <= %EXP:pDataAte%
    AND   %NOTDEL%
EndSql
```

**Características operacionais — Sintaxe:**

| Token | Descrição |
|-------|-----------|
| `%Table:SB1%` | Retorna o nome padrão da tabela |
| `%NotDel%` | Substituída por `D_E_L_E_T_=' '` |
| `%xFilial:SB1%` | Substituída pela função `xFilial("SB1")` |
| `%exp:NOME_VAR%` | Para informar uma variável no SELECT |
| `Column` | Faz a transformação do campo igual ao `TCSetField()` |
| `%NOPARSER%` | Indica que a query não deve passar pela `ChangeQuery()` |

---

## 6. Manipulação de Arquivos

### 6.1. Geração e leitura de arquivos em formato texto

Arquivos do tipo texto (TXT) são arquivos com registros de tamanho variável. O final de cada registro é representado por `"0D 0A"` (hex) / `"13 10"` (decimal) / `"CR LF"` (ASCII).

Existem duas famílias de funções:

1. **1ª Família:** `FCreate()`, `FWrite()`, `FClose()`, `FSeek()`, `FOpen()` e `FRead()`
2. **2ª Família:** `FT_FUse()`, `FT_FGoTop()`, `FT_FLastRec()`, `FT_FEof()`, `FT_FReadLn()`, `FT_FSkip()`, `FT_FGoto()`, `FT_FRecno()`

> A 1ª família funciona para arquivos de tamanho fixo. Para tamanho variável, use a 2ª família.

---

## 6.2. 1ª Família de funções de gravação e leitura de arquivos texto

### 6.2.1. FCREATE()

Cria um arquivo ou elimina seu conteúdo, retornando o handle do arquivo.

**Sintaxe:**
```advpl
FCREATE(<cArquivo>, [nAtributo])
```

**Atributos (fileio.ch):**

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `FC_NORMAL` | 0 | Criação normal (default) |
| `FC_READONLY` | 1 | Arquivo protegido para gravação |
| `FC_HIDDEN` | 2 | Arquivo oculto |
| `FC_SYSTEM` | 4 | Arquivo de sistema |

> Para múltiplos atributos, somar os valores. Ex: `FC_READONLY + FC_HIDDEN`.
> Se o arquivo já existir, o conteúdo será **eliminado** e o tamanho truncado para 0.

**Retorno:** Handle do arquivo (>= 0) ou `-1` em caso de erro (verificar com `FERROR()`).

### 6.2.2. FWRITE()

Escreve dados em um arquivo aberto, a partir da posição corrente do ponteiro.

**Sintaxe:**
```advpl
FWRITE(<nHandle>, <cBuffer>, [nQtdBytes])
```

| Parâmetro | Descrição |
|-----------|-----------|
| `nHandle` | Handle retornado por `FOPEN()`, `FCREATE()` ou `FOPENPORT()` |
| `cBuffer` | String a ser escrita (tamanho >= `nQtdBytes`) |
| `nQtdBytes` | Quantidade de bytes a escrever (default: todo o `cBuffer`) |

**Retorno:** Quantidade de bytes escritos. Se menor que `nQtdBytes`, ocorreu erro — usar `FERROR()`.

### 6.2.3. FCLOSE()

Fecha arquivos binários e força a escrita dos buffers no disco.

**Sintaxe:**
```advpl
FCLOSE(<nHandle>)
```

**Retorno:** `.T.` se bem sucedido; `.F.` em caso de erro.

### 6.2.4. FSEEK()

Posiciona o ponteiro do arquivo para próximas operações de leitura ou gravação.

**Sintaxe:**
```advpl
FSEEK(<nHandle>, [nOffSet], [nOrigem])
```

**Origens (fileio.ch):**

| Origem | Constante | Descrição |
|--------|-----------|-----------|
| 0 | `FS_SET` | A partir do início do arquivo (default) |
| 1 | `FS_RELATIVE` | Relativo à posição atual |
| 2 | `FS_END` | A partir do final do arquivo |

**Retorno:** Nova posição do ponteiro em relação ao início (posição 0).

### 6.2.5. FOPEN()

Abre um arquivo binário existente para leitura e/ou escrita.

**Sintaxe:**
```advpl
FOPEN(<cArq>, [nModo])
```

**Retorno:** Handle de arquivo (0 a 65.535) ou `-1` em caso de erro.

### 6.2.6. FREAD()

Realiza a leitura dos dados a partir de um arquivo aberto, armazenando por referência no buffer.

**Sintaxe:**
```advpl
FREAD(<nHandle>, <cBuffer>, <nQtdBytes>)
```

> A variável `cBuffer` deve ser pré-alocada e passada por referência (`@cBuffer`).

**Retorno:** Quantidade de bytes lidos. Se menor que solicitado: erro ou fim de arquivo.

**Exemplo: Geração de arquivo TXT (1ª família)**

```advpl
#include "protheus.ch"

User Function GeraTXT()
    Local oGeraTxt
    Private cPerg  := "EXPSA1"
    Private cAlias := "SA1"

    dbSelectArea(cAlias)
    dbSetOrder(1)

    DEFINE MSDIALOG oGeraTxt TITLE OemToAnsi("Geração de Arquivo Texto") ;
           FROM 000,000 TO 200,400 PIXEL
    @ 005,005 TO 095,195 OF oGeraTxt PIXEL
    @ 010,020 Say " Este programa irá gerar um arquivo texto..." OF oGeraTxt PIXEL
    @ 026,020 Say " SA1 " OF oGeraTxt PIXEL

    DEFINE SBUTTON FROM 070,030 TYPE 1 ACTION (OkGeraTxt(), oGeraTxt:End()) ENABLE OF oGeraTxt
    DEFINE SBUTTON FROM 070,070 TYPE 2 ACTION (oGeraTxt:End())              ENABLE OF oGeraTxt
    DEFINE SBUTTON FROM 070,110 TYPE 5 ACTION (Pergunte(cPerg, .T.))        ENABLE OF oGeraTxt

    ACTIVATE DIALOG oGeraTxt CENTERED
Return Nil

Static Function OkGeraTxt()
    Private cArqTxt := "\SYSTEM\EXPSA1.TXT"
    Private nHdl    := fCreate(cArqTxt)

    If nHdl == -1
        MsgAlert("O arquivo " + cArqTxt + " não pode ser criado!", "Atenção!")
        Return
    Endif

    Processa({|| RunCont()}, "Processando...")
Return Nil

Static Function RunCont()
    Local cLin
    dbSelectArea(cAlias)
    dbGoTop()
    ProcRegua(RecCount())

    While (cAlias)->(!EOF())
        IncProc()
        cLin  := (cAlias)->A1_FILIAL
        cLin  += (cAlias)->A1_COD
        cLin  += (cAlias)->A1_LOJA
        cLin  += (cAlias)->A1_NREDUZ
        cLin  += STRZERO((cAlias)->A1_MCOMPRA * 100, 16) // 14,2
        cLin  += DTOS((cAlias)->A1_ULTCOM)               // AAAAMMDD
        cLin  += CRLF

        If fWrite(nHdl, cLin, Len(cLin)) != Len(cLin)
            If !MsgAlert("Ocorreu um erro na gravação. Continua?", "Atenção!")
                Exit
            Endif
        Endif
        (cAlias)->(dbSkip())
    EndDo

    fClose(nHdl)
Return Nil
```

**Exemplo: Leitura de arquivo TXT (1ª família)**

```advpl
#Include "protheus.ch"

Static Function OkLeTxt()
    Private cArqTxt := "\SYSTEM\EXPSA1.TXT"
    Private nHdl    := fOpen(cArqTxt, 68)

    If nHdl == -1
        MsgAlert("O arquivo " + cArqTxt + " não pode ser aberto!", "Atenção!")
        Return
    Endif

    Processa({|| RunCont()}, "Processando...")
Return Nil

Static Function RunCont()
    Local nTamFile := 0
    Local nTamLin  := 56
    Local cBuffer  := ""
    Local nBtLidos := 0
    Local cFilSA1  := ""
    Local cCodSA1  := ""
    Local cLojaSA1 := ""
    // Layout:
    // A1_FILIAL  - 01,02 - TAM: 02
    // A1_COD     - 03,08 - TAM: 06
    // A1_LOJA    - 09,10 - TAM: 02
    // A1_NREDUZ  - 11,30 - TAM: 20
    // A1_MCOMPRA - 31,46 - TAM: 14,2
    // A1_ULTCOM  - 47,54 - TAM: 08

    nTamFile := fSeek(nHdl, 0, 2)
    fSeek(nHdl, 0, 0)
    cBuffer  := Space(nTamLin)
    ProcRegua(nTamFile)

    While nBtLidos < nTamFile
        IncProc()
        nBtLidos += fRead(nHdl, @cBuffer, nTamLin)
        cFilSA1  := Substr(cBuffer, 01, 02)
        cCodSA1  := Substr(cBuffer, 03, 06)
        cLojaSA1 := Substr(cBuffer, 09, 02)

        While .T.
            IF dbSeek(cFilSA1 + cCodSA1 + cLojaSA1)
                cCodSA1 := SOMA1(cCodSA1)
                Loop
            Else
                Exit
            Endif
        Enddo

        dbSelectArea(cAlias)
        RecLock(cAlias, .T.)
        (cAlias)->A1_FILIAL  := cFilSA1
        (cAlias)->A1_COD     := cCodSA1
        (cAlias)->A1_LOJA    := cLojaSA1
        (cAlias)->A1_NREDUZ  := Substr(cBuffer, 11, 20)
        (cAlias)->A1_MCOMPRA := Val(Substr(cBuffer, 31, 16)) / 100
        (cAlias)->A1_ULTCOM  := STOD(Substr(cBuffer, 47, 08))
        MSUnLock()
    EndDo

    fClose(nHdl)
Return Nil
```

---

## 6.3. 2ª Família de funções de gravação e leitura de arquivos texto

### 6.3.1. FT_FUSE()

Abre ou fecha um arquivo texto. As linhas são delimitadas por CRLF ou LF, com tamanho máximo de 1022 bytes por linha.

```advpl
FT_FUSE([cTXTFile])
```

**Retorno:** Handle de controle ou `-1` em caso de falha.

### 6.3.2. FT_FGOTOP()

Move o ponteiro para o início do arquivo texto.

### 6.3.3. FT_FLASTREC()

Retorna o número total de linhas do arquivo texto aberto pela `FT_FUse`.

```advpl
FT_FLASTREC()
```

**Retorno:** Número de linhas (0 se vazio ou sem arquivo aberto).

### 6.3.4. FT_FEOF()

Retorna `.T.` se o arquivo texto está posicionado no final.

```advpl
FT_FEOF()
```

### 6.3.5. FT_FREADLN()

Retorna uma linha de texto do arquivo aberto. Linhas delimitadas por CRLF (`chr(13)+chr(10)`) ou LF (`chr(10)`).

```advpl
FT_FREADLN()
```

**Retorno:** Linha inteira na posição do ponteiro.

### 6.3.6. FT_FSKIP()

Move o ponteiro para a próxima linha (similar ao `DBSKIP()`).

```advpl
FT_FSKIP([nLinhas])
```

### 6.3.7. FT_FGOTO()

Move o ponteiro para a posição absoluta especificada.

```advpl
FT_FGOTO(<nPos>)
```

### 6.3.8. FT_FRECNO()

Retorna a posição corrente do ponteiro do arquivo texto.

```advpl
FT_FRECNO()
```

**Exemplo: Leitura de arquivo TXT (2ª família)**

```advpl
#Include "Protheus.ch"

User Function LeArqTxt()
    Private nOpc      := 0
    Private cCadastro := "Ler arquivo texto"
    Private aSay      := {}
    Private aButton   := {}

    AADD(aSay, "O objetivo desta rotina é efetuar a leitura em um arquivo texto")
    AADD(aButton, {1, .T., {|| nOpc := 1, FechaBatch()}})
    AADD(aButton, {2, .T., {|| FechaBatch()}})

    FormBatch(cCadastro, aSay, aButton)
    If nOpc == 1
        Processa({|| Import()}, "Processando...")
    Endif
Return Nil

Static Function Import()
    Local cBuffer   := ""
    Local cFileOpen := ""
    Local cTitulo1  := "Selecione o arquivo"
    Local cExtens   := "Arquivo TXT | *.txt"

    // cGetFile(cFiltro, cTitulo, nMascaraDefault, cDirInicial, lAbrir, nMascara)
    cFileOpen := cGetFile(cExtens, cTitulo1, , cMainPath, .T.)

    If !File(cFileOpen)
        MsgAlert("Arquivo texto: " + cFileOpen + " não localizado", cCadastro)
        Return
    Endif

    FT_FUSE(cFileOpen)              // Abrir arquivo
    FT_FGOTOP()                     // Ponteiro no topo
    ProcRegua(FT_FLASTREC())        // Quantidade de registros a ler

    While !FT_FEOF()                // Enquanto não for fim de arquivo
        IncProc()
        cBuffer := FT_FREADLN()     // Lendo linha

        cMsg  := "Filial : "       + SubStr(cBuffer, 01, 02) + Chr(13)+Chr(10)
        cMsg  += "Código: "        + SubStr(cBuffer, 03, 06) + Chr(13)+Chr(10)
        cMsg  += "Loja:   "        + SubStr(cBuffer, 09, 02) + Chr(13)+Chr(10)
        cMsg  += "Nome fantasia: " + SubStr(cBuffer, 11, 15) + Chr(13)+Chr(10)
        cMsg  += "Valor:  "        + SubStr(cBuffer, 26, 14) + Chr(13)+Chr(10)
        cMsg  += "Data:   "        + SubStr(cBuffer, 40, 08) + Chr(13)+Chr(10)
        MsgInfo(cMsg)

        FT_FSKIP()                  // Próximo registro
    EndDo

    FT_FUSE()                       // Fecha o arquivo
    MsgInfo("Processo finalizado")
Return Nil
```

> **Exercício:** Desenvolver uma rotina que realize a exportação dos itens marcados no cadastro de clientes para um arquivo TXT em um diretório especificado pelo usuário.
