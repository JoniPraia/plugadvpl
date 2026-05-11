# ADVPL MVC – Guia de Desenvolvimento

> **MVC Protheus – Versão 12**
> Todos os direitos autorais reservados pela TOTVS S.A. Proibida a reprodução total ou parcial, bem como a armazenagem em sistema de recuperação e a transmissão, de qualquer modo ou por qualquer outro meio, sem prévia autorização por escrito da proprietária. Conforme artigos 122 e 130 da LEI no. 5.988 de 14 de Dezembro de 1973.

---

## Sumário

- [1. Objetivo](#1-objetivo)
  - [1.1 Introdução](#11-introdução)
- [2. Arquitetura MVC](#2-arquitetura-mvc)
  - [2.1 Principais funções da aplicação em AdvPL utilizando o MVC](#21-principais-funções-da-aplicação-em-advpl-utilizando-o-mvc)
  - [2.2 O que é a função ModelDef?](#22-o-que-é-a-função-modeldef)
  - [2.3 O que é a função ViewDef?](#23-o-que-é-a-função-viewdef)
  - [2.4 O que é a função MenuDef?](#24-o-que-é-a-função-menudef)
- [3. Novo comportamento na interface](#3-novo-comportamento-na-interface)
  - [3.1 Aplicações com Browses (FWMBrowse)](#31-aplicações-com-browses-fwmbrowse)
  - [3.2 Construção básica de um Browse](#32-construção-básica-de-um-browse)
  - [3.3 Exemplo completo de Browse](#33-exemplo-completo-de-browse)
- [4. Construção de aplicação ADVPL utilizando MVC](#4-construção-de-aplicação-advpl-utilizando-mvc)
  - [4.1 Criando o MenuDef](#41-criando-o-menudef)
  - [4.2 Construção da função ModelDef](#42-construção-da-função-modeldef)
  - [4.3 Exemplo completo da ModelDef](#43-exemplo-completo-da-modeldef)
- [5. Construção da função ViewDef](#5-construção-da-função-viewdef)
  - [5.1 Exibição dos dados na interface](#51-exibição-dos-dados-na-interface-createhorizontalbox--createverticalbox)
  - [5.2 Relacionando o componente da interface (SetOwnerView)](#52-relacionando-o-componente-da-interface-setownerview)
  - [5.3 Removendo campos da tela](#53-removendo-campos-da-tela)
  - [5.4 Finalização da ViewDef](#54-finalização-da-viewdef)
  - [5.5 Exemplo completo da ViewDef](#55-exemplo-completo-da-viewdef)
- [6. Carregar o modelo de dados de uma aplicação já existente (FWLoadModel)](#6-carregar-o-modelo-de-dados-de-uma-aplicação-já-existente-fwloadmodel)
- [7. Carregar a interface de uma aplicação já existente (FWLoadView)](#7-carregar-a-interface-de-uma-aplicação-já-existente-fwloadview)
- [8. Instalação do Desenhador MVC](#8-instalação-do-desenhador-mvc)
  - [8.1 Criação de um novo fonte Desenhador MVC](#81-criação-de-um-novo-fonte-desenhador-mvc)
- [9. Tratamentos para o modelo de dados](#9-tratamentos-para-o-modelo-de-dados)
  - [9.1 Mensagens exibidas na interface](#91-mensagens-exibidas-na-interface)
  - [9.2 Ação de interface (SetViewAction)](#92-ação-de-interface-setviewaction)
  - [9.3 Ação de interface do campo (SetFieldAction)](#93-ação-de-interface-do-campo-setfieldaction)
  - [9.4 Obtenção da operação que está sendo realizada (GetOperation)](#94-obtenção-da-operação-que-está-sendo-realizada-getoperation)
  - [9.5 Obtenção de componente do modelo de dados (GetModel)](#95-obtenção-de-componente-do-modelo-de-dados-getmodel)
  - [9.6 Obtenção e atribuição de valores ao modelo de dados](#96-obtenção-e-atribuição-de-valores-ao-modelo-de-dados)
  - [9.7 Adicionando botão na tela](#97-adicionando-botão-na-tela)
- [10. Manipulação da componente FormGrid](#10-manipulação-da-componente-formgrid)
  - [10.1 Criação de relação entre as entidades do modelo (SetRelation)](#101-criação-de-relação-entre-as-entidades-do-modelo-setrelation)
  - [10.2 Campo Incremental (AddIncrementField)](#102-campo-incremental-addincrementfield)
  - [10.3 Quantidade de linhas do componente de grid (Length)](#103-quantidade-de-linhas-do-componente-de-grid-length)
  - [10.4 Status da linha de um componente de grid](#104-status-da-linha-de-um-componente-de-grid)
  - [10.5 Adição de uma linha a grid (AddLine)](#105-adição-de-uma-linha-a-grid-addline)
  - [10.6 Apagando e recuperando uma linha da grid (DeleteLine e UnDeleteLine)](#106-apagando-e-recuperando-uma-linha-da-grid-deleteline-e-undeleteline)
  - [10.7 Recuperando uma linha da grid que está apagada](#107-recuperando-uma-linha-da-grid-que-está-apagada)
  - [10.8 Guardando e restaurando o posicionamento do grid (FWSaveRows / FWRestRows)](#108-guardando-e-restaurando-o-posicionamento-do-grid-fwsaverows--fwrestrows)
  - [10.9 Criação de pastas (CreateFolder)](#109-criação-de-pastas-createfolder)
  - [10.10 Criação de campos de total ou contadores (AddCalc)](#1010-criação-de-campos-de-total-ou-contadores-addcalc)
  - [10.11 Outros objetos (AddOtherObjects)](#1011-outros-objetos-addotherobjects)
  - [10.12 Validações](#1012-validações)
  - [10.13 Validações AddFields](#1013-validações-addfields)
- [11. Eventos View](#11-eventos-view)
  - [11.1 SetCloseOnOk](#111-setcloseonok)
  - [11.2 SetViewAction](#112-setviewaction)
  - [11.3 SetAfterOkButton](#113-setafterokbutton)
  - [11.4 SetViewCanActivate](#114-setviewcanactivate)
  - [11.5 SetAfterViewActivate](#115-setafterviewactivate)
  - [11.6 SetVldFolder](#116-setvldfolder)
  - [11.7 SetTimer](#117-settimer)
- [12. Pontos de entrada no MVC](#12-pontos-de-entrada-no-mvc)
- [13. Browse com coluna de marcação (FWMarkBrowse)](#13-browse-com-coluna-de-marcação-fwmarkbrowse)
- [14. Apêndice](#14-apêndice)

---

## 1. Objetivo

Ao final do treinamento deverá ter desenvolvido os seguintes conceitos:

**a) Conceitos a serem aprendidos**
- Arquitetura Model-View-Controller ou MVC
- Introdução às técnicas de programação voltado ao MVC
- Introdução aos conceitos entre as camadas do MVC

**b) Habilidades e técnicas a serem aprendidas**
- Desenvolvimento de aplicações voltadas ao ERP Protheus
- Análise de fontes de média complexidade
- Desenvolvimento de fontes com mais de uma entidade

### 1.1 Introdução

A arquitetura Model-View-Controller ou MVC, como é mais conhecida, é um padrão de arquitetura de software que visa separar a lógica de negócio da lógica de apresentação (a interface), permitindo o desenvolvimento, teste e manutenção isolada de ambos.

Aqueles que já desenvolveram uma aplicação em AdvPL vão perceber que justamente a diferença mais importante entre a forma de construir uma aplicação em MVC e a forma tradicional é essa separação, que vai permitir o uso da regra de negócio em aplicações que tenham ou não interfaces, como Web Services e aplicação automática, bem como seu reuso em outras aplicações.

---

## 2. Arquitetura MVC

A arquitetura MVC é um padrão de arquitetura de software que visa separar a lógica de negócio da lógica de apresentação (a interface), permitindo o desenvolvimento, teste e manutenção isolados de ambos.

A arquitetura MVC possui três componentes básicos:

- **Model (modelo de dados):** representa as informações do domínio do aplicativo e fornece funções para operar os dados, isto é, ele contém as funcionalidades do aplicativo. Nele definimos as regras de negócio: tabelas, campos, estruturas, relacionamentos etc. O modelo de dados (Model) também é responsável por notificar a interface (View) quando os dados forem alterados.
- **View (interface):** responsável por renderizar o modelo de dados (Model) e possibilitar a interação do usuário, ou seja, é o responsável por exibir os dados.
- **Controller:** responde às ações dos usuários, possibilita mudanças no Modelo de dados (Model) e seleciona a View correspondente.

Para facilitar e agilizar o desenvolvimento, na implementação do MVC feita no AdvPL, o desenvolvedor trabalhará com as definições de Modelo de dados (Model) e View; a parte responsável pelo Controller já está intrínseca.

A grande mudança, o grande paradigma a ser quebrado na forma de pensar e se desenvolver uma aplicação em AdvPL utilizando MVC é a separação da regra de negócio da interface. Para que isso fosse possível foram desenvolvidas várias novas classes e métodos no AdvPL.

### 2.1 Principais funções da aplicação em AdvPL utilizando o MVC

Os desenvolvedores em suas aplicações serão responsáveis por definir as seguintes funções:

- **ModelDef:** Contém a construção e a definição do Model, lembrando que o Modelo de dados (Model) contém as regras de negócio.
- **ViewDef:** Contém a construção e definição da View, ou seja, será a construção da interface.
- **MenuDef:** Contém a definição das operações disponíveis para o modelo de dados (Model).

Cada fonte em MVC (PRW) só pode conter uma de cada dessas funções. Só pode ter uma `ModelDef`, uma `ViewDef` e uma `MenuDef`. Ao se fazer uma aplicação em AdvPL utilizando MVC, automaticamente ao final, essa aplicação já terá disponível:

- Pontos de Entradas já disponíveis
- Web Service para sua utilização
- Importação ou exportação de mensagens XML

### 2.2 O que é a função ModelDef?

A função `ModelDef` define a regra de negócios propriamente dita, onde são definidas:

- Todas as entidades (tabelas) que farão parte do modelo de dados (Model)
- Regras de dependência entre as entidades
- Validações (de campos e aplicação)
- Persistência dos dados (gravação)

Para uma `ModelDef` não é preciso necessariamente possuir uma interface. Como a regra de negócios é totalmente separada da interface no MVC, podemos utilizar a `ModelDef` em qualquer outra aplicação, ou até utilizarmos uma determinada `ModelDef` como base para outra mais complexa.

As entidades da `ModelDef` não se baseiam necessariamente em metadados (dicionários); ela se baseia em estruturas e essas por sua vez é que podem vir do metadados ou serem construídas manualmente. A `ModelDef` deve ser uma `Static Function` dentro da aplicação.

### 2.3 O que é a função ViewDef?

A função `ViewDef` define como será a interface e, portanto, como o usuário interage com o modelo de dados (Model), recebendo os dados informados pelo usuário, fornecendo ao modelo de dados (definido na `ModelDef`) e apresentando o resultado. A interface pode ser baseada totalmente ou parcialmente em um metadado (dicionário), permitindo:

- Reaproveitamento do código da interface, pois uma interface básica pode ser acrescida de novos componentes
- Simplicidade no desenvolvimento de interfaces complexas. Um exemplo disso são aquelas aplicações onde uma GRID depende de outra. No MVC a construção de aplicações que têm GRIDs dependentes é extremamente fácil
- Agilidade no desenvolvimento — a criação e a manutenção se tornam muito mais ágeis
- Mais de uma interface por Business Object. Poderemos ter interfaces diferentes para cada variação de um segmento de mercado, como o varejo

A `ViewDef` deve ser uma `Static Function` dentro da aplicação.

### 2.4 O que é a função MenuDef?

Uma função `MenuDef` define as operações que serão realizadas pela aplicação, tais como inclusão, alteração, exclusão, etc.

Deve retornar um array em um formato específico com as seguintes informações:

| Campo | Descrição |
|-------|-----------|
| Título | Nome do item no menu |
| Nome da aplicação associada | Referência à ViewDef |
| Reservado | — |
| Tipo de Transação | Valor numérico da operação |

**Tipos de transação:**

| Valor | Operação |
|-------|----------|
| 1 | Pesquisar |
| 2 | Visualizar |
| 3 | Incluir |
| 4 | Alterar |
| 5 | Excluir |
| 6 | Imprimir |
| 7 | Copiar |

Demais parâmetros:
- **5.** Nível de acesso
- **6.** Habilita Menu Funcional

---

## 3. Novo comportamento na interface

Nas aplicações desenvolvidas em AdvPL tradicional, após a conclusão de uma operação de alteração fecha-se a interface e retorna ao Browse.

Nas aplicações em MVC, após as operações de inclusão e alteração, a interface permanece ativa e no rodapé exibe-se a mensagem de que a operação foi bem-sucedida.

### 3.1 Aplicações com Browses (FWMBrowse)

Para a construção de uma aplicação que possui um Browse, o MVC utiliza a classe `FWMBrowse`. Esta classe exibe um objeto Browse que é construído a partir de metadados (dicionários). Esta classe não foi desenvolvida exclusivamente para o MVC — aplicações que não são em MVC também podem utilizá-la.

**Principais benefícios:**
- Substituir componentes de Browse
- Reduzir o tempo de manutenção em caso de adição de um novo requisito
- Ser independente do ambiente Microsiga Protheus

**Principais melhorias:**
- Padronização de legenda de cores
- Melhor usabilidade no tratamento de filtros
- Padrão de cores, fontes e legenda definidas pelo usuário (deficiente visual)
- Redução do número de operações no SGBD (no mínimo 3 vezes mais rápido)
- Novo padrão visual

### 3.2 Construção básica de um Browse

Crie um objeto Browse da seguinte forma:

```advpl
oBrowse := FWMBrowse():New()
```

Defina a tabela que será exibida no Browse utilizando o método `SetAlias`. As colunas, ordens, etc., são obtidas pelo metadados (dicionários).

```advpl
oBrowse:SetAlias('SA1')
```

Defina o título que será exibido com o método `SetDescription`.

```advpl
oBrowse:SetDescription('Cadastro de Cliente')
```

Ao final, ative a classe.

```advpl
oBrowse:Activate()
```

Com esta estrutura básica é construída uma aplicação com Browse. O Browse apresentado automaticamente já terá:
- Pesquisa de registro
- Filtro configurável
- Configuração de colunas e aparência
- Impressão

#### 3.2.1 Legendas de um Browse (AddLegend)

Para o uso de legendas no Browse utilizamos o método `AddLegend`, que possui a seguinte sintaxe:

```advpl
AddLegend( <cRegra>, <cCor>, <cDescrição> )
```

**Exemplo:**

```advpl
oBrowse:AddLegend( "ZA0_TIPO =='F'", "YELLOW", "Cons.Final"  )
oBrowse:AddLegend( "ZA0_TIPO=='L'", "BLUE"  , "Produtor Rural" )
```

- **cRegra:** é a expressão em AdvPL para definir a legenda.
- **cCor:** define a cor de cada item da legenda.

**Cores disponíveis:**

| Constante | Cor |
|-----------|-----|
| GREEN | Verde |
| RED | Vermelha |
| YELLOW | Amarela |
| ORANGE | Laranja |
| BLUE | Azul |
| GRAY | Cinza |
| BROWN | Marrom |
| BLACK | Preta |
| PINK | Rosa |
| WHITE | Branca |

- **cDescrição:** texto que será exibido para cada item da legenda.

> **Atenção:** Cada uma das legendas se tornará automaticamente uma opção de filtro. Cuidado ao montar as regras da legenda. Se houverem regras conflitantes será exibida a legenda correspondente à 1ª regra que for satisfeita.

#### 3.2.2 Filtros de um Browse (SetFilterDefault)

Para definir um filtro para o Browse, utilizamos o método `SetFilterDefault`:

```advpl
SetFilterDefault( <filtro> )
```

**Exemplos:**

```advpl
oBrowse:SetFilterDefault("A1_TIPO=='F'")

oBrowse:SetFilterDefault( "Empty(A1_ULTCOM)" )
```

A expressão de filtro é em AdvPL. O filtro definido na aplicação não anula a possibilidade do usuário fazer seus próprios filtros. Os filtros feitos pelo usuário serão aplicados em conjunto com o definido na aplicação (condição de AND). O filtro da aplicação não poderá ser desabilitado pelo usuário.

#### 3.2.3 Desabilitar o Detalhes do Browse (DisableDetails)

Automaticamente para o Browse são exibidos, em detalhes, os dados da linha posicionada. Para desabilitar esta característica utilizamos o método `DisableDetails`.

```advpl
oBrowse:DisableDetails()
```

### 3.3 Exemplo completo de Browse

```advpl
User Function COMP011_MVC()
  Local oBrowse

  // Instanciamento da Classe de Browse
  oBrowse := FWMBrowse():New()

  // Definição da tabela do Browse
  oBrowse:SetAlias('SA1')

  // Definição da legenda
  oBrowse:AddLegend("A1_TIPO='F'","YELLOW","Cons.Final")
  oBrowse:AddLegend("A1_TIPO='L'","BLUE"  ,"Produtor Rural")

  // Definição de filtro
  oBrowse:SetFilterDefault( "A1_TIPO=='F'" )

  // Titulo da Browse
  oBrowse:SetDescription('Cadastro de Clientes')

  // Opcionalmente pode ser desligado a exibição dos detalhes
  //oBrowse:DisableDetails()

  // Ativação da Classe
  oBrowse:Activate()

Return NIL
```

---

## 4. Construção de aplicação ADVPL utilizando MVC

Iniciamos agora a construção da parte em MVC da aplicação, que são as funções de `ModelDef` (regras de negócio) e `ViewDef` (interface). Um ponto importante que deve ser observado é que, assim como a `MenuDef`, só pode haver uma função `ModelDef` e uma função `ViewDef` em uma fonte.

Se para uma determinada situação for preciso trabalhar em mais de um modelo de dados (Model), a aplicação deve ser quebrada em vários fontes (PRW), cada um com apenas uma `ModelDef` e uma `ViewDef`.

### 4.1 Criando o MenuDef

A criação da estrutura do `MenuDef` deve ser uma `Static Function` dentro da aplicação.

**Forma tradicional (com array):**

```advpl
Static Function MenuDef()
  Local aRotina := {}

  aAdd( aRotina, { 'Visualizar', 'VIEWDEF.COMP021_MVC', 0, 2, 0, NIL } )
  aAdd( aRotina, { 'Incluir'   , 'VIEWDEF.COMP021_MVC', 0, 3, 0, NIL } )
  aAdd( aRotina, { 'Alterar'   , 'VIEWDEF.COMP021_MVC', 0, 4, 0, NIL } )
  aAdd( aRotina, { 'Excluir'   , 'VIEWDEF.COMP021_MVC', 0, 5, 0, NIL } )
  aAdd( aRotina, { 'Imprimir'  , 'VIEWDEF.COMP021_MVC', 0, 8, 0, NIL } )
  aAdd( aRotina, { 'Copiar'    , 'VIEWDEF.COMP021_MVC', 0, 9, 0, NIL } )

Return aRotina
```

Sempre referenciaremos a `ViewDef` de um fonte, pois ela é a função responsável pela interface da aplicação.

**Forma simplificada (recomendada para MVC):**

```advpl
Static Function MenuDef()
  Local aRotina := {}

  ADD OPTION aRotina Title 'Visualizar' Action 'VIEWDEF.COMP021_MVC' OPERATION 2 ACCESS 0
  ADD OPTION aRotina Title 'Incluir'    Action 'VIEWDEF.COMP021_MVC' OPERATION 3 ACCESS 0
  ADD OPTION aRotina Title 'Alterar'    Action 'VIEWDEF.COMP021_MVC' OPERATION 4 ACCESS 0
  ADD OPTION aRotina Title 'Excluir'    Action 'VIEWDEF.COMP021_MVC' OPERATION 5 ACCESS 0
  ADD OPTION aRotina Title 'Imprimir'   Action 'VIEWDEF.COMP021_MVC' OPERATION 8 ACCESS 0
  ADD OPTION aRotina Title 'Copiar'     Action 'VIEWDEF.COMP021_MVC' OPERATION 9 ACCESS 0

Return aRotina
```

**Parâmetros do ADD OPTION:**

| Parâmetro | Descrição |
|-----------|-----------|
| TITLE | Nome do item no menu |
| ACTION | `'VIEWDEF.nome_do_arquivo_fonte'` (PRW) |
| OPERATION | Valor que define a operação a ser executada (inclusão, alteração, etc.) |
| ACCESS | Valor que define o nível de acesso |

**Menu padrão com `FWMVCMENU`:**

Podemos criar um menu com opções padrão para o MVC utilizando a função `FWMVCMENU`:

```advpl
Static Function MenuDef()
Return FWMVCMenu( 'COMP011_MVC' )
```

Será criado um menu padrão com as opções: Visualizar, Incluir, Alterar, Excluir, Imprimir e Copiar.

### 4.2 Construção da função ModelDef

Nessa função são definidas as regras de negócio ou modelo de dados (Model). Elas contêm as definições de:
- Entidades envolvidas
- Validações
- Relacionamentos
- Persistência de dados (gravação)

**Iniciando a função ModelDef:**

```advpl
Static Function ModelDef()
  Local oModel // Modelo de dados que será construído

  // Construindo o Model
  oModel := MPFormModel():New( 'COMP011M' )
```

`MPFormModel` é a classe utilizada para a construção de um objeto de modelo de dados (Model). Devemos dar um identificador (ID) para o modelo como um todo e também para cada componente.

> **Importante:** Se a aplicação é uma `Function`, o identificador (ID) do modelo de dados (Model) não pode ter o mesmo nome da função.

#### 4.2.1 Construção de uma estrutura de dados (FWFormStruct)

A primeira coisa que precisamos fazer é criar a estrutura utilizada no modelo de dados (Model). As estruturas são objetos que contêm as definições dos dados necessárias para uso da `ModelDef` ou para a `ViewDef`:
- Estrutura dos Campos
- Índices
- Gatilhos
- Regras de preenchimento

O MVC trabalha vinculado a estruturas, não diretamente ao metadado. Com a função `FWFormStruct` a estrutura será criada a partir do metadado.

**Sintaxe:**

```advpl
FWFormStruct( <nTipo>, <cAlias> )
```

| Parâmetro | Descrição |
|-----------|-----------|
| nTipo | 1 para Modelo de dados (Model); 2 para interface (View) |
| cAlias | Alias da tabela no metadado |

**Exemplo:**

```advpl
Local oStruSA1 := FWFormStruct( 1, 'SA1' )
```

> Para **Model** (`nTipo=1`): a `FWFormStruct` traz todos os campos que compõem a tabela independentemente do nível, uso ou módulo. Considera também os campos virtuais.
> Para **View** (`nTipo=2`): a `FWFormStruct` traz os campos conforme o nível, uso ou módulo.

#### 4.2.2 Criação de um componente de formulários (AddFields)

O método `AddFields` adiciona um componente de formulário ao modelo. A estrutura do modelo de dados (Model) **deve iniciar, obrigatoriamente, com um componente de formulário**.

```advpl
oModel:AddFields( 'SA1MASTER', /*cOwner*/, oStruSA1 )
```

- **SA1MASTER:** identificador (ID) dado ao componente de formulário no modelo
- **oStruSA1:** estrutura construída anteriormente com `FWFormStruct`
- **cOwner:** não informado pois este é o 1º componente do modelo (o Pai); não tem componente superior

#### 4.2.3 Criação de um componente de formulários na interface (AddField)

Adicionamos na interface (View) um controle do tipo formulário (antiga enchoice) com o método `AddField`. A interface (View) **deve iniciar, obrigatoriamente, com um componente do tipo formulário**.

```advpl
oView:AddField( 'VIEW_SA1', oStruSA1, 'SA1MASTER' )
```

- **VIEW_SA1:** identificador (ID) do componente da interface (View)
- **oStruSA1:** estrutura a ser usada
- **SA1MASTER:** identificador (ID) do componente do modelo de dados (Model) vinculado a este componente da interface (View)

#### 4.2.4 Descrição dos componentes do modelo de dados (SetDescription)

```advpl
// Descrição do modelo de dados
oModel:SetDescription( 'Modelo de dados Cliente' )

// Descrição dos componentes do modelo de dados
oModel:GetModel( 'SA1MASTER' ):SetDescription( 'Dados dos Clientes' )
```

#### 4.2.5 Índice do Model — PrimaryKey

Atribui a PrimaryKey da entidade Modelo. A PrimaryKey é imprescindível para a correta operação das rotinas automáticas, web-services, relatórios, etc. Não é necessário informar uma para cada submodelo — a Primary Key é definida somente para o primeiro submodelo do tipo FormField.

```advpl
oModel:SetPrimaryKey({ 'A1_COD', 'A1_LOJA', 'A1_FILIAL' })
```

#### 4.2.6 Finalização de ModelDef

Ao final da função `ModelDef`, deve ser retornado o objeto de modelo de dados (Model) gerado na função.

```advpl
Return oModel
```

### 4.3 Exemplo completo da ModelDef

```advpl
Static Function ModelDef()
  Local oModel // Modelo de dados que será construído

  // Cria o objeto do Modelo de Dados
  oModel := MPFormModel():New('COMP011M')

  // Cria a estrutura a ser usada no Modelo de Dados
  Local oStruSA1 := FWFormStruct( 1, 'SA1' )

  // Adiciona ao modelo um componente de formulário
  oModel:AddFields( 'SA1MASTER', /*cOwner*/, oStruSA1)

  // Adiciona a descrição do Modelo de Dados
  oModel:SetDescription( 'Modelo de dados de Clientes' )

  // Adiciona a descrição do Componente do Modelo de Dados
  oModel:GetModel( 'SA1MASTER' ):SetDescription( 'Dados do Cliente' )

  // Retorna o Modelo de dados
Return oModel
```

---

## 5. Construção da função ViewDef

A interface (View) é responsável por renderizar o modelo de dados (Model) e possibilitar a interação do usuário, ou seja, é o responsável por exibir os dados. A `ViewDef` contém a definição de toda a parte visual da aplicação.

```advpl
Static Function ViewDef()
```

A interface (View) sempre trabalha baseada em um modelo de dados (Model). Com a função `FWLoadModel` obtemos o modelo de dados (Model) que está definido em um fonte:

```advpl
Local oModel := FWLoadModel('COMP011_MVC')
```

Iniciando a construção da interface (View):

```advpl
oView := FWFormView():New()
```

`FWFormView` é a classe que deverá ser usada para a construção de um objeto de interface (View). Em seguida, definimos qual o modelo de dados (Model) que será utilizado na interface (View):

```advpl
oView:SetModel( oModel )
```

### 5.1 Exibição dos dados na interface (CreateHorizontalBox / CreateVerticalBox)

Sempre precisamos criar um contêiner para receber algum elemento da interface (View). Em MVC criaremos sempre box horizontal ou vertical para isso.

```advpl
oView:CreateHorizontalBox( 'TELA' , 100 )
```

- **TELA:** identificador (ID) dado ao box
- **100:** percentual da tela que será utilizado pelo Box

> No MVC não há referências a coordenadas absolutas de tela; os componentes visuais são sempre **All Client**, ou seja, ocuparão todo o contêiner onde for inserido.

### 5.2 Relacionando o componente da interface (SetOwnerView)

Precisamos relacionar o componente da interface (View) com um box para exibição, para isso usamos o método `SetOwnerView`.

```advpl
oView:SetOwnerView( 'VIEW_SA1', 'TELA' )
```

Desta forma o componente `VIEW_SA1` será exibido na tela utilizando o box `TELA`.

### 5.3 Removendo campos da tela

Remoção de campos são tratados na visão `ViewDef` com o método `RemoveField`. No exemplo, aplica-se condição para não mostrar determinados campos:

```advpl
oStruct := FWFormStruct(2, "SA1")

If __cUserID <> "000000"
  oStruct:RemoveField( "A1_DESC" )
EndIf
```

### 5.4 Finalização da ViewDef

Ao final da função `ViewDef`, deve ser retornado o objeto de interface (View) gerado:

```advpl
Return oView
```

### 5.5 Exemplo completo da ViewDef

```advpl
Static Function ViewDef()
  // Cria um objeto de Modelo de dados baseado no ModelDef() do fonte informado
  Local oModel := FWLoadModel( 'COMP011_MVC' )

  // Cria a estrutura a ser usada na View
  Local oStruSA1 := FWFormStruct( 2, 'SA1' )

  // Interface de visualização construída
  Local oView

  // Cria o objeto de View
  oView := FWFormView():New()

  // Define qual o Modelo de dados será utilizado na View
  oView:SetModel( oModel )

  // Adiciona no nosso View um controle do tipo formulário (antiga Enchoice)
  oView:AddField( 'VIEW_SA1', oStruSA1, 'SA1MASTER' )

  // Criar um "box" horizontal para receber algum elemento da view
  oView:CreateHorizontalBox( 'TELA' , 100 )

  // Relaciona o identificador (ID) da View com o "box" para exibição
  oView:SetOwnerView( 'VIEW_SA1', 'TELA' )

  // Retorna o objeto de View criado
Return oView
```

---

## 6. Carregar o modelo de dados de uma aplicação já existente (FWLoadModel)

Para criarmos um objeto com o modelo de dados de uma aplicação, utilizamos a função `FWLoadModel`:

```advpl
FWLoadModel( <nome do fonte> )
```

**Exemplo:**

```advpl
Static Function ModelDef()
  // Utilizando um model que ja existe em outra aplicacao
Return FWLoadModel( 'COMP011_MVC' )
```

---

## 7. Carregar a interface de uma aplicação já existente (FWLoadView)

Para criarmos um objeto com a interface de uma aplicação, utilizamos a função `FWLoadView`:

```advpl
FWLoadView( <nome do fonte> )
```

**Exemplo:**

```advpl
Static Function ViewDef()
  // Utilizando uma view que ja existe em outra aplicacao
Return FWLoadView( 'COMP011_MVC' )
```

---

## 8. Instalação do Desenhador MVC

O **Desenhador MVC** é um conjunto de plug-ins que funcionam dentro do **TDS (Totvs Developer Studio)**, sendo uma ferramenta de auxílio na criação e manutenção de códigos fontes escritos em AdvPL em conjunto com o framework de desenvolvimento.

Para fazer a instalação do Desenhador MVC é necessário ter instalado o TDS. Ao acessar o TDS ir na opção **Ajuda → Install New Software**.

Após acessar, preencher **Work With** com o endereço do instalador do desenhador MVC:

```
http://ds.totvs.com/updates/desenhador/
```

As opções que devem estar habilitadas:
- Show Only the latest version of available software
- Contact all update sites during install to find required software

As demais opções devem estar desabilitadas.

Selecionar a opção **Desenhador MVC** e depois o botão **Next**.

Selecionar a opção que aceita os termos de licença de uso: **I accept the terms of license agreements**.

Selecionar o botão concluir. Após esse processo o desenhador será instalado. Para confirmar a instalação do desenhador, acesse **Ajuda → Sobre Totvs Developer Studio** e selecione o botão **"Detalhes da Instalação"**.

Irá listar todos os plug-ins instalados no TDS. Localize o **"Desenhador MVC"**; caso não esteja na lista, refaça o processo.

**Pré-Requisitos para instalação do desenhador:**
- TDS atualizado
- Ambiente com LIB atualizada (Portal do Cliente)

### 8.1 Criação de um novo fonte Desenhador MVC

Os fontes MVC AdvPL precisam necessariamente estar dentro de um projeto TOTVS.

Para criar um fonte novo, clique em **Arquivos → Novo → Outras**, escolha o item **Nova Função MVC ADVPL do Totvs SDK AdvPL**.

Na tela do novo fonte MVC, preencher os campos:

| Campo | Descrição |
|-------|-----------|
| Local | Pasta do projeto onde deseja salvar o fonte |
| Nome da função | Nome do PRW |
| Criar Arquivo com referência | Para salvar o fonte fora do WorkSpace |

O fonte é aberto com o Desenhador MVC e possui três abas: **Source**, **View** e **Model**.

Com o novo plugin MVC há novas validações do compilador facilitando o desenvolvimento.

#### Guia Model

Na guia **Model** possui todos os componentes para criação do `ModelDef`:

**Componentes:**
- **Field:** Adiciona no Model um sub-Modelo de campos (Enchoice)
- **Grid:** Adiciona no Model um sub-Modelo de grid (GetDados)
- **Calc:** Adiciona no grid campos totalizadores

**Propriedades:**

| Propriedade | Descrição |
|-------------|-----------|
| Editable | Se o modelo for carregado usando `FWloadModel`, não é possível alterar as propriedades |
| Identifier | Identificador do Modelo |
| Component | Nome do componente |
| Description | Atribui ao modelo um texto explicativo sobre o objetivo do Modelo (mostrado em web services, relatórios e schemas) |
| bPre | Bloco de código de pré-validação do modelo. Recebe o objeto de Model como parâmetro; deve retornar valor lógico |
| bPos | Bloco de código de pós-validação do modelo, equivale ao "TUDOOK". Recebe o objeto de Model; deve retornar valor lógico |
| bVldActivate | Bloco de código chamado antes do Activate do model; pode inibir a inicialização do model |
| bCommit | Bloco de código de persistência dos dados, invocado pelo método CommitData |
| bCancel | Bloco de código de cancelamento da edição, invocado pelo método CancelData |
| bLoadXML | Configura o modelo para ser ativado com uma folha de dados em XML |
| bActivate | Bloco de código chamado logo após o Activate do model |
| bDeActivate | Bloco de código chamado logo após o DeActivate do model |
| onDemand | Define se a carga dos dados será por demanda |
| Type | `MPFormModel` realiza tratamento nas variáveis de memória e possibilita o uso do Help. `FWFormModel` não realiza esses tratamentos |
| TotalReport | Configura se o relatório gerado pelo método ReportDef deverá totalizar todos os campos numéricos |

#### Guia View

Na guia **View** são listadas todas as propriedades para definir a função `ViewDef`.

**Árvore de componentes:**
- **View:** Estrutura do View
- **Menu:** Botões no View — lista todos os botões criados pelo `UserButton`
- **Root:** Lista todos os componentes visuais
- **Menu:** Componente onde serão colocados os botões de usuário
- **Root:** Componente base onde os componentes de interface serão alocados

**Palette (Componentes de visualização):**

| Componente | Descrição |
|------------|-----------|
| HorizontalBox | Divide a tela na posição horizontal. Atenção: só pode ser colocado dentro de um box vertical |
| VerticalBox | Divide a tela na posição vertical. Atenção: só pode ser colocado dentro de um box horizontal |
| FormField | Formulário que exibe campos no mesmo modelo da antiga enchoice. Requer submodelo do tipo field no Model |
| FormGrid | Formulário que exibe um grid (diversos registros na tela). Requer submodelo do tipo grid no Model |
| FormCalc | Formulário que exibe campos calculados criados no Model. Requer submodelo do tipo calc no Model |
| OtherObject | Cria um painel onde pode ser colocado qualquer coisa que o desenvolvedor desejar |
| Folder | Cria um componente de pasta capaz de armazenar diversas abas |
| Sheet | Cria uma aba dentro de uma Folder |
| UserButton | Adiciona botões do desenvolvedor na barra de ferramentas do formulário |

Tudo que foi desenvolvido nas guias View e Model é gerado automaticamente na guia **Source**.

---

## 9. Tratamentos para o modelo de dados

Veremos alguns tratamentos que podem ser feitos no modelo de dados (Model) conforme a necessidade:
- Validações
- Comportamentos
- Manipulação da Grid
- Obter e atribuir valores ao modelo de dados (Model)
- Gravação dos dados manualmente
- Regras de preenchimento

### 9.1 Mensagens exibidas na interface

As mensagens são usadas principalmente durante as validações feitas no modelo de dados. A validação é um processo executado dentro da regra de negócio, e uma eventual mensagem de erro que será exibida ao usuário é um processo que deve ser executado na interface.

Para trabalhar essa situação foi feito um tratamento para a função `help`. A função `help` poderá ser utilizada nas funções dentro do modelo de dados (Model), porém o MVC irá guardar essa mensagem e ela só será exibida quando o controle voltar para a interface.

**Exemplo:**

```advpl
If nPrcUnit == 0 // Preço unitário
  Help( ,, 'Título do campo','', 'Mensagem a ser exibida no help.', 1, 0 )
EndIf
```

Ao debugar o fonte, você verá que ao passar pela função `Help` nada acontece; quando o controle interno volta para a interface, a mensagem é exibida.

### 9.2 Ação de interface (SetViewAction)

Existe no MVC a possibilidade de se executar uma função em algumas ações da interface (View). Esse recurso pode ser usado quando queremos executar algo na interface e que não tem reflexo no modelo de dados (Model), como um Refresh de tela.

Situações disponíveis:
- Refresh da interface
- Acionamento do botão confirmar da interface
- Acionamento do botão cancelar da interface
- Deleção da linha da grid
- Restauração da linha da grid

**Sintaxe:**

```advpl
oView:SetViewAction( <cActionlID>, <bAction> )
```

**Parâmetros cActionlID:**

| ID | Momento de execução |
|----|---------------------|
| REFRESH | Executa a ação no Refresh da View |
| BUTTONOK | Executa a ação no acionamento do botão confirmar da View |
| BUTTONCANCEL | Executa a ação no acionamento do botão cancelar da View |
| DELETELINE | Executa a ação na deleção da linha da grid |
| UNDELETELINE | Executa a ação na restauração da linha da grid |

**bAction:** bloco com a ação a ser executada.

| ID | Parâmetro recebido |
|----|-------------------|
| REFRESH | Objeto de View |
| BUTTONOK | Objeto de View |
| BUTTONCANCEL | Objeto de View |
| DELETELINE | Objeto de View, ID da View e número da linha |
| UNDELETELINE | Objeto de View, ID da View e número da linha |

**Exemplo:**

```advpl
oView:SetViewAction( 'BUTTONOK'    , { |oView| SuaFuncao( oView ) } )
oView:SetViewAction( 'BUTTONCANCEL', { |oView| OutraFuncao( oView ) } )
```

> **Dica:** Essas ações são executadas apenas quando existe uma interface (View). O que não ocorre quando temos o instanciamento direto do modelo, rotina automática ou Web Service. Deve-se evitar então colocar nestas funções ações que possam influenciar a regra de negócio, pois na execução da aplicação sem interface essas ações não serão executadas.

### 9.3 Ação de interface do campo (SetFieldAction)

Existe no MVC a possibilidade de se executar uma função após a validação de campo de algum componente do modelo de dados (Model). Esse recurso pode ser usado quando queremos executar algo na interface e que não tem reflexo no modelo, como um Refresh de tela ou abrir uma tela auxiliar.

**Sintaxe:**

```advpl
oView:SetFieldAction( <cIDField>, <bAction> )
```

| Parâmetro | Descrição |
|-----------|-----------|
| cIDField | ID do campo (nome) |
| bAction | Bloco com a ação a ser executada |

O bloco `bAction` recebe como parâmetro:
- Objeto de View
- Identificador (ID) da View
- Identificador (ID) do campo
- Conteúdo do campo

**Exemplo:**

```advpl
oView:SetFieldAction( 'A1_COD', { |oView, cIDView, cField, xValue| SuaFuncao( oView, cIDView, cField, xValue ) } )
```

### 9.4 Obtenção da operação que está sendo realizada (GetOperation)

Para sabermos a operação com que um modelo de dados (Model) está trabalhando, usamos o método `GetOperation`.

**Retorno:**

| Valor | Operação |
|-------|----------|
| 3 | Inclusão |
| 4 | Alteração |
| 5 | Exclusão |

```advpl
Local nVar := oModel:GetOperation()
```

**Constantes disponíveis:**
- `MODEL_OPERATION_INSERT`
- `MODEL_OPERATION_UPDATE`
- `MODEL_OPERATION_DELETE`

**Exemplo:**

```advpl
If oModel:GetOperation() == MODEL_OPERATION_INSERT
  Help( ,, 'Help',, 'Não permitido incluir.', 1, 0 )
EndIf
```

### 9.5 Obtenção de componente do modelo de dados (GetModel)

Durante o desenvolvimento teremos que manipular o modelo de dados (Model). Para facilitar essa manipulação podemos trabalhar com uma parte específica (um componente) de cada vez.

```advpl
// Capturar um componente específico
Local oModel := oModel:GetModel( 'NOME DO ID DO MODELO DE DADOS' )

// Capturar o modelo completo
Local oModel := oModel:GetModel()
```

### 9.6 Obtenção e atribuição de valores ao modelo de dados

**GetValue** — Obtém um dado do modelo de dados (Model):

```advpl
// A partir do modelo completo
cVar := oModel:GetValue( 'ID do componente', 'Nome do campo para obter o dado' )

// Sem ter recuperado o modelo da tabela em uma variável
cVar := oModel:GetModel('ID'):GetValue( 'Nome do campo do qual se deseja obter o dado' )
```

**SetValue** — Atribui um dado ao modelo de dados (Model):

```advpl
// A partir do modelo completo
oModel:SetValue( 'ID', 'Nome do Campo', 'Valor para o campo' )

// Sem ter recuperado o modelo da tabela em uma variável
oModel:SetValue( 'Nome do Campo', 'Valor para o campo' )
```

### 9.7 Adicionando botão na tela

Para adicionar botões na barra de ferramentas do formulário, utilize a função:

```advpl
FWFORMVIEW():addUserButton( <cTitle>, <cResource>, <bBloco>, [cToolTip], [nShortCut], [aOptions] )
```

**Exemplo:**

```advpl
oView:AddUserButton('NomeBotão', 'CLIPS', ;
  {|| fValSto()}, 'NomeBotao', /*nShortCut*/, ;
  {MODEL_OPERATION_INSERT, MODEL_OPERATION_UPDATE})
```

---

## 10. Manipulação da componente FormGrid

Alguns tratamentos que poderão ser feitos nos componentes de grid de um modelo de dados (Model).

### 10.1 Criação de relação entre as entidades do modelo (SetRelation)

Dentro do modelo devemos relacionar todas as entidades que participam dele. Toda entidade do modelo que possui um superior (owner) deve ter seu relacionamento para ele definido. O método utilizado para esta definição é o `SetRelation`.

```advpl
oModel:SetRelation( 'FMRDETAIL', { { 'C6_FILIAL', 'xFilial( "SC6" )' }, ;
  { 'C6_NUM', 'C5_NUM' } }, SC6->( IndexKey( 1 ) ) )
```

- **FMRDETAIL:** identificador (ID) da entidade Detail
- **2º parâmetro:** vetor bidimensional onde são definidos os relacionamentos entre cada campo do filho para o Pai
- **3º parâmetro:** ordenação dos dados no componente

O relacionamento sempre é definido do Detail (Filho) para o Master (Pai).

### 10.2 Campo Incremental (AddIncrementField)

Podemos fazer com que um campo do modelo de dados (Model) que faça parte de um componente de grid possa ser incrementado unitariamente a cada nova linha inserida. Para isso utilizamos o método `AddIncrementField`.

```advpl
oView:AddIncrementField( 'VIEW_SC6', 'C6_ITEM' )
```

Onde `VIEW_SC6` é o identificador (ID) do componente da interface (View) onde se encontra o campo e `C6_ITEM` é o nome do campo que será incrementado.

### 10.3 Quantidade de linhas do componente de grid (Length)

Para se obter a quantidade de linhas do grid devemos utilizar o método `Length`. As linhas apagadas também são consideradas na contagem.

```advpl
For nI := 1 To oModel:Length()
  // Segue a funcao ...
Next nI
```

Se for passado um parâmetro no método `Length`, o retorno será apenas a quantidade de linhas não apagadas da grid:

```advpl
nLinhas := oModel:Length( .T. ) // Quantidade linhas não apagadas
```

### 10.4 Status da linha de um componente de grid

Quando a operação é de alteração, o grid pode ter linhas incluídas, alteradas ou excluídas. Em MVC é possível saber que operações uma linha sofreu pelos seguintes métodos de status:

| Método | Descrição |
|--------|-----------|
| `IsDeleted()` | Retorna `.T.` se a linha foi apagada |
| `IsUpdated()` | Retorna `.T.` se a linha foi alterada |
| `IsInserted()` | Retorna `.T.` se a linha foi inserida (linha nova no grid) |

**Exemplo:**

```advpl
Static Function COMP23ACAO()
  Local oModel     := FWModelActive()
  Local oModelZA2  := oModel:GetModel( 'ZA2DETAIL' )
  Local nI         := 0
  Local nCtInc     := 0
  Local nCtAlt     := 0
  Local nCtDel     := nCtInc := nCtAlt := 0
  Local aSaveLines := FWSaveRows()

  For nI := 1 To oModel:Length()
    oModel:GoLine( nI )
    If oModel:IsDeleted()
      nCtDel++
    ElseIf oModel:IsInserted()
      nCtInc++
    ElseIf oModel:IsUpdated()
      nCtAlt++
    EndIf
  Next

  FwRestRows(aSaveLines)
```

### 10.5 Adição de uma linha a grid (AddLine)

Para adicionarmos uma linha a um componente do grid do modelo de dados (Model) utilizamos o método `AddLine`.

```advpl
nLinha++
If oModel:AddLine() == nLinha
  // Segue a função
EndIf
```

O método `AddLine` retorna a quantidade total de linhas da grid. Se a grid já possui 2 linhas e tudo correu bem na adição, o `AddLine` retornará 3. Os motivos para a inserção não ser bem-sucedida podem ser: campo obrigatório não informado, pós-validação da linha retornou `.F.`, atingiu a quantidade máxima de linhas para o grid.

### 10.6 Apagando e recuperando uma linha da grid (DeleteLine e UnDeleteLine)

Para apagarmos uma linha de um componente de grid do modelo de dados (Model) utilizamos o método `DeleteLine`.

```advpl
Local oModel    := FWModelActive()
Local oModel    := oModel:GetModel( 'ZA2DETAIL' )
Local nI        := 0

For nI := 1 To oModel:Length()
  oModel:GoLine( nI )
  If !oModel:IsDeleted()
    oModel:DeleteLine()
  EndIf
Next
```

O método `DeleteLine` retorna `.T.` se a deleção foi bem-sucedida.

### 10.7 Recuperando uma linha da grid que está apagada

Utilizamos o método `UnDeleteLine`.

```advpl
Local oModel   := oModel:GetModel( 'SA1DETAIL' )
Local nI       := 0

For nI := 1 To oModelSA1:Length()
  If oModel:IsDeleted()
    oModel:GoLine( nI )
    oModel:UnDeleteLine()
  EndIf
Next
```

O método `UnDeleteLine` retorna `.T.` se a recuperação foi bem-sucedida.

### 10.8 Guardando e restaurando o posicionamento do grid (FWSaveRows / FWRestRows)

Um cuidado que devemos ter quando escrevemos uma função, mesmo que não seja para uso em MVC, é restaurarmos as áreas das tabelas que desposicionamos.

```advpl
Local aSaveLines := FWSaveRows()

// ... operações no grid ...

// Antes do Return, para restaurar o valor:
FwRestRows( aSaveLines )
```

### 10.9 Criação de pastas (CreateFolder)

Em MVC podemos criar pastas onde serão colocados os componentes da interface (View). Para isso utilizamos o método `CreateFolder`.

```advpl
oView:CreateFolder( 'PASTAS' )
```

Após a criação da pasta principal, precisamos criar as abas com o método `AddSheet`:

```advpl
oView:AddSheet( 'PASTAS', 'ABA01', 'Cabeçalho' )
oView:AddSheet( 'PASTAS', 'ABA02', 'Item' )
```

- **PASTAS:** identificador (ID) da pasta
- **ABA01 / ABA02:** IDs dados a cada aba
- **Cabeçalho / Item:** títulos de cada aba

Para que possamos colocar um componente em uma aba, precisamos criar um box para receber os elementos:

```advpl
oView:CreateHorizontalBox( 'SUPERIOR', 100,,, 'PASTAS', 'ABA01' )
oView:CreateHorizontalBox( 'INFERIOR', 100,,, 'PASTAS', 'ABA02' )
```

- **SUPERIOR / INFERIOR:** IDs dados a cada box
- **100:** percentual que o box ocupará da aba
- **PASTAS:** ID da pasta
- **ABA01 / ABA02:** IDs das abas

Em seguida, relacionamos o componente da interface (View) com o box:

```advpl
oView:SetOwnerView( 'VIEW_SB1', 'SUPERIOR' )
oView:SetOwnerView( 'VIEW_SB5', 'INFERIOR' )
```

### 10.10 Criação de campos de total ou contadores (AddCalc)

Em MVC é possível criar automaticamente um novo componente composto de campos totalizadores ou contadores. Os campos do componente de cálculos são baseados em componentes de grid do modelo; atualizando o componente de grid, automaticamente os campos do componente de cálculos serão atualizados.

**Sintaxe:**

```advpl
AddCalc( cId, cOwner, cIdForm, cIdField, cIdCalc, cOperation, bCond, bInitValue, cTitle, bFormula, nTamanho, nDecimal )
```

| Parâmetro | Descrição |
|-----------|-----------|
| cId | Identificador do componente de cálculos |
| cOwner | Identificador do componente superior (owner) |
| cIdForm | Código do componente de grid que contém o campo |
| cIdField | Nome do campo do componente de grid |
| cIdCalc | Identificador (nome) para o campo calculado |
| cOperation | Identificador da operação a ser realizada |
| bCond | Condição para avaliação do campo calculado. Recebe o objeto do modelo. Ex: `{|oModel| teste(oModel)}` |
| bInitValue | Bloco de código para o valor inicial. Ex: `{|oModel| teste(oModel)}` |
| cTitle | Título para o campo calculado |
| bFormula | Fórmula utilizada quando `cOperation` é do tipo FORMULA |
| nTamanho | Tamanho do campo calculado |
| nDecimal | Número de casas decimais do campo calculado |

**Operações disponíveis:**

| Operação | Descrição |
|----------|-----------|
| SUM | Faz a soma do campo do componente de grid |
| COUNT | Faz a contagem do campo do componente de grid |
| AVG | Faz a média do campo do componente de grid |
| FORMULA | Executa uma fórmula para o campo do componente de grid |

**Tamanhos padrão por operação:**

| Operação | Tamanho |
|----------|---------|
| SUM | Tamanho do campo do grid + 3 |
| COUNT | Fixo em 6 |
| AVG | Tamanho do campo do grid |
| FORMULA | Tamanho do campo do grid + 3 |

**bFormula** recebe como parâmetros: o objeto do modelo, o valor atual do campo fórmula, o conteúdo do campo do componente de grid, campo lógico indicando se é soma (`.T.`) ou subtração (`.F.`):

```advpl
{ |oModel, nTotalAtual, xValor, lSomando| Calculo( oModel, nTotalAtual, xValor, lSomando ) }
```

**Exemplo — Contador de registros (na ModelDef):**

```advpl
oModel:AddCalc( 'COUNTTOTAL', 'MODEL_AAA', 'MODEL_BBB', 'AAA_ID', 'Total', 'COUNT' )
```

- **COUNTTOTAL:** identificador do componente de cálculos
- **MODEL_AAA:** identificador do componente superior (owner)
- **MODEL_BBB:** código do componente de grid de onde virão os dados
- **AAA_ID:** nome do campo do componente de grid
- **Total:** identificador (nome) para o campo calculado
- **COUNT:** identificador da operação a ser realizada

**Na ViewDef**, use `FWCalcStruct` para obter a estrutura criada na ModelDef:

```advpl
Local oCount := FWCalcStruct( oModel:GetModel('COUNTTOTAL') )

oView:AddField( 'VCALC_ID', oCount, 'INFERIOR' )
oView:CreateHorizontalBox( 'INFERIOR', 24)
oView:SetOwnerView('VCALC_ID', 'INFERIOR')
```

> **Atenção:** Para as operações de SUM e AVG o campo do componente de grid deve ser do tipo numérico.

### 10.11 Outros objetos (AddOtherObjects)

Na construção de algumas aplicações pode ser que tenhamos que adicionar à interface um componente que não faz parte da interface padrão do MVC, como um gráfico, um calendário, etc. Para isso usaremos o método `AddOtherObject`.

```advpl
AddOtherObject( <Id>, <Code Block a ser executado> )
```

- **Id:** identificador (ID) do componente
- **Code Block:** para a criação dos outros objetos. O MVC se limita a fazer a chamada da função; a responsabilidade de construção e atualização dos dados cabe ao desenvolvedor.

**Exemplo:**

```advpl
AddOtherObject( "OTHER_PANEL", { |oPanel| COMP23BUT( oPanel ) } )

// Para o componente aparecer na camada view, necessário associá-lo ao box
oView:SetOwnerView("OTHER_PANEL", 'EMBAIXODIR')
```

```advpl
Static Function COMP23BUT( oPanel )
  TButton():New( 020, 020, "TESTE", oPanel, {|| MsgInfo('TESTE') }, 030, 010, , , .F., .T., .F., , .F., , , .F. )
Return( Nil )
```

### 10.12 Validações

Dentro do modelo de dados existem vários pontos onde podem ser inseridas as validações necessárias à regra de negócio:

- **Pós-validação do modelo:** É a validação realizada após o preenchimento do modelo de dados (Model) e sua confirmação. Seria o equivalente ao antigo processo de TudoOk.
- **Pós-validação de linha:** Em um modelo de dados onde existam componentes de grid, pode ser definida uma validação que será executada na troca das linhas do grid. Seria o equivalente ao antigo processo de LinhaOk.
- **Validação da ativação do modelo:** É a validação realizada no momento da ativação do modelo, permitindo ou não a sua ativação.

#### 10.12.1 Validação de linha duplicada (SetUniqueLine)

Em um modelo de dados onde existam componentes de grid podem ser definidos quais os campos que não podem se repetir dentro deste grid. O método do modelo de dados (Model) que dever ser usado é o `SetUniqueLine`.

```advpl
oModel:GetModel( 'SB1DETAIL' ):SetUniqueLine( { 'B1_COD' } )
```

No exemplo, o campo `B1_COD` não poderá ter seu conteúdo repetido no grid. Também pode ser informado mais de um campo, criando assim um controle com chave composta.

#### 10.12.2 SetDeActivate

Antes da ativação do Model é permitido executar função para validar o modo de operação; será chamado logo após o DeActivate do model. Esse bloco recebe como parâmetro o próprio model.

```advpl
oModel:SetDeActivate( bBloco() )
```

**Exemplo:**

```advpl
oModel:SetDeActivate( {|oModel| MsgInfo("SetDeActivate","Model")} )
```

#### 10.12.3 Pré-validação do Modelo

O bloco recebe como parâmetro o objeto de Model e deve retornar um valor lógico. Quando houver uma tentativa de atualização de valor de qualquer Submodelo, o bloco de código será invocado.

```advpl
oModel:New(<cID>, <bPre>, <bPost>, <bCommit>, <bCancel>)
```

**Exemplo:**

```advpl
Static Function ModelDef()
  Local bPre   := {| | ValidPre(oModel)}
  Local oModel := MPFormModel():New('SA1MODEL', , bPre)

Static Function ValidPre(oModel)
  Local nOperation := oModel:GetOperation()
  Local lRet       := .T.

  If nOperation == MODEL_OPERATION_UPDATE
    If Empty( oModel:GetValue( 'SA1MASTER', 'A1_CGC' ) )
      Help( ,, 'HELP',, 'Informe o CNPJ', 1, 0)
      lRet := .F.
    EndIf
  EndIf

Return lRet
```

#### 10.12.4 Pós-validação do Modelo

A pós-validação do modelo equivale ao "TUDOOK". O bloco recebe como parâmetro o objeto de Model e deve retornar um valor lógico. O bloco será invocado antes da persistência dos dados para validar o model.

```advpl
MPFORMMODEL():New(<cID>, <bPre>, <bPost>, <bCommit>, <bCancel>)
```

**Exemplo:**

```advpl
Static Function ModelDef()
  Local oModel := MPFormModel():New('SA1MODEL', , { |oMdl| COMP011POS( oMdl ) })
Return

Static Function COMP011POS( oModel )
  Local nOperation := oModel:GetOperation()
  Local lRet       := .T.

  If nOperation == MODEL_OPERATION_UPDATE
    If Empty( oModel:GetValue( 'SA1MASTER', 'A1_COD' ) )
      Help( ,, 'HELP',, 'Informe o codigo do cliente', 1, 0)
      lRet := .F.
    EndIf
  EndIf

Return lRet
```

#### 10.12.5 Gravação manual de dados (FWFormCommit)

A gravação dos dados do modelo de dados (Model) (persistência) é realizada pelo MVC. Porém, pode haver a necessidade de se efetuar gravações em outras entidades que não participam do modelo.

Para isso definimos um bloco de código no 4º parâmetro da classe de construção do modelo:

```advpl
MPFORMMODEL():New(<cID>, <bPre>, <bPost>, <bCommit>, <bCancel>)
```

O bloco de código para gravação **substitui** a gravação dos dados. Ao ser definido um bloco de código para gravação, passa a ser responsabilidade da função criada a gravação de todos os dados, inclusive os dados do modelo de dados em uso.

A função `FWFormCommit` fará a gravação dos dados do objeto de modelo de dados (Model) informado:

```advpl
Static Function COMP011GRV( oModel )
  Local lGravo

  lGravo := FWFormCommit( oModel )

  If lGravo
    // Efetuar a gravação de outros dados em entidade que
    // não são do model
  EndIf
```

> **Atenção:** Não devem ser feitas atribuições de dados no modelo (Model) dentro da função de gravação.

#### 10.12.6 Cancelamento da gravação de dados

Essa validação realiza os tratamentos necessários ao cancelamento dos formulários de edição. O bloco recebe como parâmetro o objeto do Model.

Quando esse bloco é passado, o tratamento de numeração automática não é mais realizado, a menos que o bloco chame a função `FWFormCancel`.

```advpl
MPFORMMODEL():New(<cID>, <bPre>, <bPost>, <bCommit>, <bCancel>)
```

**Exemplo:**

```advpl
oModel := MPFormModel():New("MODELO",,, ,{ |oModel| FWFormCancel(oModel) })
```

#### 10.12.7 SetVldActivate

Será chamado antes do Activate do model. Ele pode ser utilizado para inibir a inicialização do model. Se o retorno for negativo, uma exceção de usuário será gerada. O code-block recebe como parâmetro o objeto model.

```advpl
MPFORMMODEL():SetVldActivate( <bBloco> )
```

### 10.13 Validações AddFields

Um submodelo do tipo Field permite manipular somente um registro por vez. Ele tem um relacionamento do tipo 1xN ou 1x1 com outros SubModelos.

```advpl
FWFORMMODEL():AddFields( [cId], [cOwner], [oModelStruct], [bPre], [bPost], [bLoad] ) -> NIL
```

#### 10.13.1 Pré-Validação do AddFields

É invocado quando há uma tentativa de atribuição de valores. O bloco recebe como parâmetro o objeto do FormField (`FWFormFieldsModel`), a identificação da ação e a identificação do campo.

**Ações possíveis:**
- `"CANSETVALUE"`: valida se o submodelo pode ou não receber atribuição de valor
- `"SETVALUE"`: valida se o campo do submodelo pode receber aquele valor (neste caso o bloco recebe um 4º parâmetro com o valor que está sendo atribuído)

O bloco deve retornar um valor lógico. Se falso, um erro será atribuído no Model (use `SetErrorMessage` para indicar a natureza do erro).

**Exemplo:**

```advpl
Static Function ModelDef()
  Local oModel
  Local oStruZA1 := FWFormStruct(1, 'SA1')
  Local bPre     := {|oFieldModel, cAction, cIDField, xValue| validPre(oFieldModel, cAction, cIDField, xValue)}

  oModel := FWFormModel():New('COMP021')
  oModel:addFields('ZA1MASTER',, oStruZA1, bPre, bPos, bLoad)

Static Function validPre(oFieldModel, cAction, cIDField, xValue)
  Local lRet := .T.

  If cAction == "SETVALUE" .And. cIDField == "A1_CGC"
    Help( ,, 'HELP',, ( 'Não possível atribuir valor ao campo ' + cIDField ), 1, 0)
    lRet := .F.
  EndIf

Return lRet
```

#### 10.13.2 Pós-Validação do AddFields

Equivalente ao "TUDOOK". O bloco de código recebe como parâmetro o objeto de model do FormField (`FWFormFieldsModel`) e deve retornar um valor lógico. Este bloco é invocado antes da persistência (gravação) dos dados.

```advpl
FWFORMMODEL():AddFields( [cId], [cOwner], [oModelStruct], [bPre], [bPost], [bLoad] ) -> NIL
```

**Exemplo:**

```advpl
Static Function fieldValidPos(oFieldModel)
  Local lRet := .T.

  If "@" $ Upper(oFieldModel:GetValue("A1_EMAIL"))
    Help( ,, 'HELP',, 'Informar um email valido', 1, 0)
    lRet := .F.
  EndIf

Return lRet
```

#### 10.13.3 Load do AddFields

Este bloco será invocado durante a execução do método activate desta classe. O bloco recebe por parâmetro o objeto de model do FormField (`FWFormFieldsModel`) e um valor lógico indicando se é uma operação de cópia. Espera-se como retorno um array com os dados que serão carregados no objeto.

```advpl
MPFORMMODEL():AddFields( <cId>, <cOwner>, <oModelStruct>, <bPre>, <bPost>, <bLoad> )
```

**Exemplo:**

```advpl
Static Function loadField(oFieldModel, lCopy)
  Local aLoad := {}

  aAdd(aLoad, 1)                                          // recno
  aAdd(aLoad, {xFilial("ZA1"), "000001", "01", "Teste"}) // dados

Return aLoad
```

#### 10.13.4 Validações AddGrid

Um submodelo do tipo Grid permite manipular diversos registros por vez. Ele tem um relacionamento do tipo Nx1 ou NxM com outros Submodelos.

```advpl
MPFORMMODEL():AddGrid( <cId>, <cOwner>, <oModelStruct>, <bLinePre>, <bLinePost>, <bPre>, <bPost>, <bLoad> )
```

#### 10.13.5 Pré-Linha Validação do AddGrid

O bloco é invocado na deleção de linha, no undelete da linha e nas tentativas de atribuição de valor. Recebe como parâmetro o objeto de modelo do FormGrid, o número da linha atual e a identificação da ação.

**Ações possíveis:**
- `"UNDELETE"`: undelete da linha
- `"DELETE"`: deleção da linha
- `"SETVALUE"`: atribuição de valor (parâmetros adicionais: ID do campo, valor sendo atribuído, valor atual no campo)
- `"CANSETVALUE"`: tentativa de atualização (parâmetro adicional: ID do campo)

```advpl
MPFORMMODEL():AddGrid( <cId>, <cOwner>, <oModelStruct>, <bLinePre>, <bLinePost>, <bPre>, <bPost>, <bLoad> )
```

**Exemplo:**

```advpl
Static Function ModelDef()
  Local oModel
  Local oStruZA1   := FWFormStruct(1, 'ZA1')
  Local oStruZA2   := FWFormStruct( 1, 'ZA2')
  Local bLinePre   := {|oGridModel, nLine, cAction, cIDField, xValue, xCurrentValue| linePreGrid(oGridModel, nLine, cAction, cIDField, xValue, xCurrentValue)}

  oModel := MPFormModel():New('COMP021')
  oModel:AddFields('ZA1MASTER',, oStruZA1)
  oModel:AddGrid( 'ZA2DETAIL', 'ZA1MASTER', oStruZA2, bLinePre, , , , bLoad)

Return oModel

Static Function linePreGrid(oGridModel, nLine, cAction, cIDField, xValue, xCurrentValue)
  Local lRet := .T.

  If cAction == "SETVALUE"
    If oGridModel:GetValue("ZA2_TIPO") == "AUTOR"
      lRet := .F.
      Help( ,, 'HELP',, 'Não é possível alterar linhas do tipo Autor', 1, 0)
    EndIf
  EndIf

Return lRet
```

#### 10.13.6 Pós-Linha Validação do AddGrid

Código de pós-validação da linha do grid, equivale ao "LINHAOK". Recebe como parâmetro o objeto de modelo do FormGrid e o número da linha que está sendo validada. O bloco será invocado antes da gravação dos dados e na inclusão de uma linha.

```advpl
MPFORMMODEL():AddGrid( <cId>, <cOwner>, <oModelStruct>, <bLinePre>, <bLinePost>, <bPre>, <bPost>, <bLoad> )
```

#### 10.13.7 Pré-Validação do AddGrid

O bloco é invocado na deleção de linha, no undelete da linha, na inserção de uma linha e nas tentativas de atribuição de valor.

**Ações possíveis:**
- `"UNDELETE"`: undelete da linha
- `"DELETE"`: deleção da linha
- `"ADDLINE"`: inserção de linha (nenhum parâmetro adicional de número de linha é passado)
- `"SETVALUE"`: atribuição de valor (parâmetros adicionais: ID do campo, valor sendo atribuído, valor atual)
- `"CANSETVALUE"`: tentativa de atualização (parâmetro adicional)

#### 10.13.8 Pós-Validação do AddGrid

A pós-validação do submodelo é equivalente ao "TUDOOK". O bloco de código recebe como parâmetro o objeto de model do FormGrid (`FWFormGridModel`) e deve retornar um valor lógico. Este bloco é invocado antes da persistência(gravação) dos dados, validando o submodelo.

#### 10.13.9 Load do AddGrid

Este bloco será invocado durante a execução do método activate desta classe. Recebe como parâmetro o objeto de model do FormGrid e um valor lógico indicando se é uma operação de cópia.

**Exemplo:**

```advpl
Static Function ModelDef()
  Local oModel
  Local oStruZA1 := FWFormStruct(1, 'ZA1')
  Local oStruZA2 := FWFormStruct( 1, 'ZA2')
  Local bLoad    := {|oGridModel, lCopy| loadGrid(oGridModel, lCopy)}

  oModel := FWFormModel():New('COMP021')
  oModel:AddFields('ZA1MASTER',, oStruZA1)
  oModel:AddGrid( 'ZA2DETAIL', 'ZA1MASTER', oStruZA2, , , , , bLoad)

Return oModel

Static Function loadGrid(oModel, lCopy)
  Local nI       := 0
  Local aFields  := oModel:GetStruct():GetFields() // Carrega a estrutura criada
  Local aDados   := {}
  Local aAux     := {}
  Local aRet     := {}

  aAux := Array(Len(aFields))

  For ni := 1 to Len(aFields)
    If Alltrim( aFields[ni,3] ) == "CODIGO"
      aAux[ni] := "000001"
    ElseIf alltrim(aFields[ni,3]) == "QTD"
      aAux[ni] := 10
    EndIf
  Next nI

  aAdd(aRet, {0, aAux})

Return aRet
```

---

## 11. Eventos View

### 11.1 SetCloseOnOk

Método que define um bloco de código para verificar se a janela deve ou não ser fechada após a execução do botão OK na inclusão.

```advpl
oView:SetCloseOnOk( {|| .T. } )
```

### 11.2 SetViewAction

Define uma ação a ser executada em determinados pontos da View.

```advpl
FWFORMVIEW():SetViewAction( <cActionlID>, <bAction> )
```

**Pontos de ação disponíveis:**

| cActionlID | Execução |
|------------|----------|
| REFRESH | Executa a ação no Refresh da View |
| BUTTONOK | Executa a ação no acionamento do botão confirmar da View |
| BUTTONCANCEL | Executa a ação no acionamento do botão cancelar da View |
| DELETELINE | Executa a ação na deleção da linha da grid |
| UNDELETELINE | Executa a ação na restauração da linha da grid |

**Exemplo:**

```advpl
oView:SetViewAction( 'BUTTONOK'    , { |oView| MsgInfo('Apertei OK') } )
oView:SetViewAction( 'BUTTONCANCEL', { |oView| MsgInfo('Apertei Cancelar') } )
oView:SetViewAction( 'DELETELINE'  , { |oView, cIdView, nNumLine| MsgInfo('Apertei Deletar') } )
```

### 11.3 SetAfterOkButton

Método que define um bloco de código que será chamado no final da execução do botão OK. O bloco recebe como parâmetro o objeto de View e não precisa retornar nenhum valor.

```advpl
FWFORMVIEW():SetAfterOkButton( <bBlock> )
```

**Exemplo:**

```advpl
oView:SetAfterOkButton({|| MsgInfo( "Após evento de OK" ) })
```

### 11.4 SetViewCanActivate

Método que define um Code-block para ser avaliado antes de se ativar o View. No momento de chamada desse bloco o Model e o View não estão ativos. O bloco recebe como parâmetro o objeto `oView` e deve retornar verdadeiro para permitir a ativação. Se retornar falso, a janela será fechada.

```advpl
FWFORMVIEW():SetViewCanActivate( <bBlock> )
```

**Exemplo:**

```advpl
oView:SetViewCanActivate({|| MsgInfo('Pode Ativar'), .F. })
```

### 11.5 SetAfterViewActivate

Define um bloco de código que será chamado depois do Activate do View. Esse bloco será apenas executado; o retorno dele não será observado. O bloco de código recebe como parâmetro o objeto View.

**Exemplo:**

```advpl
oView:SetAfterViewActivate({|| MsgInfo('Depois de ativado') })
```

### 11.6 SetVldFolder

Executa ação quando uma aba é selecionada em qualquer folder da View.

```advpl
oView:SetVldFolder( {|cFolderID, nOldSheet, nSelSheet| ValFolder(cFolderID, nOldSheet, nSelSheet)} )
```

**Exemplo:**

```advpl
Static Function VldFolder(cFolderID, nOldSheet, nSelSheet)
  Local lRet := .T.

  If nOldSheet == 1 .And. nSelSheet == 2
    Help( ,, 'Help',, ;
      'Não é permitido selecionar a aba 2 se você estiver na aba 1.', 1, 0 )
    lRet := .F.
  EndIf

Return lRet
```

### 11.7 SetTimer

Define um timer para a janela do view. O intervalo é em milissegundos para disparar o bloco de código do Timer.

```advpl
FWFORMVIEW():SetTimer( <nInterval>, <bAction> )
```

**Exemplo:**

```advpl
oView:SetTimer(10000, {|| MsgInfo('10 Segundo') })
```

---

## 12. Pontos de entrada no MVC

Pontos de entrada são desvios controlados executados no decorrer das aplicações. Ao se escrever uma aplicação utilizando o MVC, automaticamente já estarão disponíveis pontos de entrada pré-definidos.

Em MVC criamos um único ponto de entrada e este é chamado em vários momentos dentro da aplicação desenvolvida. Este ponto de entrada único deve ser uma `User Function` e ter como nome o identificador (ID) do modelo de dados (Model) do fonte.

O ponto de entrada criado recebe via parâmetro (`PARAMIXB`) um vetor com informações referentes à aplicação.

**Posições do array de parâmetros comuns a todos os IDs:**

| Posição | Tipo | Descrição |
|---------|------|-----------|
| 1 | O | Objeto do formulário ou do modelo, conforme o caso |
| 2 | C | ID do local de execução do ponto de entrada |
| 3 | C | ID do formulário |

**IDs e momentos de execução:**

| ID | Momento de Execução | Parâmetros Adicionais | Retorno |
|----|---------------------|-----------------------|---------|
| MODELPRE | Antes da alteração de qualquer campo do modelo | — | Lógico |
| MODELPOS | Na validação total do modelo | — | Lógico |
| FORMPRE | Antes da alteração de qualquer campo do formulário | — | Lógico |
| FORMPOS | Na validação total do formulário | — | Lógico |
| FORMLINEPRE | Antes da alteração da linha do formulário FWFORMGRID | [4] Número da Linha; [5] Ação da FWFORMGRID; [6] Id do campo | Lógico |
| FORMLINEPOS | Na validação total da linha do formulário FWFORMGRID | [4] Número da Linha da FWFORMGRID | Lógico |
| MODELCOMMITTTS | Após a gravação total do modelo e dentro da transação | — | Não espera retorno |
| MODELCOMMITNTTS | Após a gravação total do modelo e fora da transação | — | Não espera retorno |
| FORMCOMMITTTSPRE | Antes da gravação da tabela do formulário | [4] `.T.` = inclusão; `.F.` = alteração/exclusão | Não espera retorno |
| FORMCOMMITTTSPOS | Após a gravação da tabela do formulário | [4] `.T.` = inclusão; `.F.` = alteração/exclusão | Não espera retorno |
| FORMCANCEL | No cancelamento do botão | — | Lógico |
| BUTTONBAR | Para a inclusão de botões na ControlBar | — | Array bidimensional com estrutura pré-definida |

**Estrutura do retorno para BUTTONBAR:**

| Posição | Tipo | Descrição |
|---------|------|-----------|
| 1 | C | Título para o botão |
| 2 | C | Nome do Bitmap para exibição |
| 3 | B | CodeBlock a ser executado |
| 4 | C | ToolTip (Opcional) |

**Exemplo completo de ponto de entrada em MVC:**

```advpl
#Include 'Protheus.ch'

User Function ModelADM()
  Local aParam    := PARAMIXB
  If aParam <> NIL
    oObj      := aParam[1]
    cIdPonto  := aParam[2]
    cIdModel  := aParam[3]
    lIsGrid   := ( Len( aParam ) > 3 )
    cClasse   := IIf( oObj <> NIL, oObj:ClassName(), '' )

    If lIsGrid
      nQtdLinhas := oObj:GetQtdLine()
      nLinha     := oObj:nLine
    EndIf

    If cIdPonto == 'MODELPOS'
      cMsg := 'Chamada na validação total do modelo (MODELPOS).' + CRLF
      cMsg += 'ID ' + cIdModel + CRLF
      If !( xRet := ApMsgYesNo( cMsg + 'Continua ?' ) )
        Help( ,, 'Help',, 'O MODELPOS retornou .F.', 1, 0 )
      EndIf

    ElseIf cIdPonto == 'FORMPOS'
      cMsg := 'Chamada na validação total do formulário (FORMPOS).' + CRLF
      cMsg += 'ID ' + cIdModel + CRLF
      If cClasse == 'FWFORMGRID'
        cMsg += 'É um FORMGRID com ' + Alltrim( Str( nQtdLinhas ) ) + ' linha(s).' + CRLF
        cMsg += 'Posicionado na linha ' + Alltrim( Str( nLinha ) ) + CRLF
      ElseIf cClasse == 'FWFORMFIELD'
        cMsg += 'É um FORMFIELD' + CRLF
      EndIf
      If !( xRet := ApMsgYesNo( cMsg + 'Continua ?' ) )
        Help( ,, 'Help',, 'O FORMPOS retornou .F.', 1, 0 )
      EndIf

    ElseIf cIdPonto == 'FORMLINEPRE'
      If aParam[5] == 'DELETE'
        cMsg := 'Chamada na pre validação da linha do formulário (FORMLINEPRE).' + CRLF
        cMsg += 'Onde esta se tentando deletar uma linha' + CRLF
        cMsg += 'É um FORMGRID com ' + Alltrim( Str( nQtdLinhas ) ) + ' linha(s).' + CRLF
        cMsg += 'Posicionado na linha ' + Alltrim( Str( nLinha ) ) + CRLF
        cMsg += 'ID ' + cIdModel + CRLF
        If !( xRet := ApMsgYesNo( cMsg + 'Continua ?' ) )
          Help( ,, 'Help',, 'O FORMLINEPRE retornou .F.', 1, 0 )
        EndIf
      EndIf

    ElseIf cIdPonto == 'FORMLINEPOS'
      cMsg := 'Chamada na validação da linha do formulário (FORMLINEPOS).' + CRLF
      cMsg += 'ID ' + cIdModel + CRLF
      cMsg += 'É um FORMGRID com ' + Alltrim( Str( nQtdLinhas ) ) + ' linha(s).' + CRLF
      cMsg += 'Posicionado na linha ' + Alltrim( Str( nLinha ) ) + CRLF
      If !( xRet := ApMsgYesNo( cMsg + 'Continua ?' ) )
        Help( ,, 'Help',, 'O FORMLINEPOS retornou .F.', 1, 0 )
      EndIf

    ElseIf cIdPonto == 'MODELCOMMITTTS'
      ApMsgInfo('Chamada apos a gravação total do modelo e dentro da transação (MODELCOMMITTTS).' + CRLF + 'ID ' + cIdModel )

    ElseIf cIdPonto == 'MODELCOMMITNTTS'
      ApMsgInfo('Chamada apos a gravação total do modelo e fora da transação (MODELCOMMITNTTS).' + CRLF + 'ID ' + cIdModel)

    ElseIf cIdPonto == 'FORMCOMMITTTSPRE'
      ApMsgInfo('Antes da gravação da tabela do formulário (FORMCOMMITTTSPRE).' + CRLF + 'ID ' + cIdModel)

    ElseIf cIdPonto == 'FORMCOMMITTTSPOS'
      ApMsgInfo('Chamada apos a gravação da tabela do formulário (FORMCOMMITTTSPOS).' + CRLF + 'ID ' + cIdModel)

    ElseIf cIdPonto == 'MODELCANCEL'
      cMsg := 'Chamada no Botão Cancelar (MODELCANCEL).' + CRLF + 'Deseja Realmente Sair ?'
      If !( xRet := ApMsgYesNo( cMsg ) )
        Help( ,, 'Help',, 'O MODELCANCEL retornou .F.', 1, 0 )
      EndIf

    ElseIf cIdPonto == 'BUTTONBAR'
      ApMsgInfo('Adicionando Botao na Barra de Botoes (BUTTONBAR).' + CRLF + 'ID ' + cIdModel )
      xRet := { {'Salvar', 'SALVAR', {|| Alert( 'Salvou' ) }, 'Este botao Salva' } }
    EndIf
  EndIf

Return xRet
```

---

## 13. Browse com coluna de marcação (FWMarkBrowse)

Se construir uma aplicação com um Browse que utilize uma coluna para marcação (similarmente à função `MarkBrowse` no AdvPL tradicional), utilizaremos a classe `FWMarkBrowse`.

Como premissa, é preciso que haja um campo na tabela do tipo caracter com o tamanho de 2 que receberá fisicamente a marca. Será gerada uma marca diferente cada vez que a `FWMarkBrowse` for executada.

**Construção básica de um FWMarkBrowse:**

```advpl
// Instanciamento da classe
oMark := FWMarkBrowse():New()

// Adicionando botões (não necessário ter MenuDef)
oMark:AddButton("Exemplo Marca", "U_SA2_Marca", , 1 )

// Definição da tabela a ser utilizada
oMark:SetAlias("SA2")

// Define o título do browse de marcação
oMark:SetDescription( "Cadastro de Grupo" )

// Define o campo que sera utilizado para a marcação
oMark:SetFieldMark( "A2_OK" )

// Ativação da classe
oMark:Activate()

Return( NIL )
```

**Função de processamento da marcação:**

```advpl
User Function SA2_Marca()
  Local cMarca := oMark:Mark()

  dbSelectArea("SA2")
  SA2->(dbGotop())

  While ! SA2->(EOF())
    If oMark:IsMark(cMarca)
      msgInfo(SA2->A2_COD + ' ' + SA2->A2_NOME)
    EndIf
    SA2->( dbSkip() )
  EndDo

  // Executa a atualização das informações no Browse
  // .T. indica que deverá ser posicionado no primeiro registro do Browse
  oMark:Refresh(.T.)

Return( NIL )
```

---

## 14. Apêndice

### FWModelActive

Esta função fornece o último objeto da classe `FWFormModel` ativo, para ser utilizado nas regras de validação do sistema Microsiga Protheus.

```advpl
Local oModel := FWModelActive()
```

### FWMemoVirtual

Alguns campos do tipo MEMO utilizam-se de tabelas para a gravação de seus valores (SYP3). Esses campos devem ser informados na estrutura para que o MVC consiga fazer seu tratamento corretamente. Para esses campos MEMO sempre deve haver outro campo que conterá o código com que o campo MEMO foi armazenado na tabela auxiliar.

```advpl
oStrut := FWFormStruct(1, "SA1")
FWMemoVirtual( oStrut, { { 'A1_OBS' }, {'A1_OBS'} } )
```

### FWFORMMODELSTRUCT — Métodos

#### GetTable()

Fornece os dados da tabela da estrutura.

**Retorno — Array com os seguintes dados:**

| Posição | Tipo | Descrição |
|---------|------|-----------|
| [01] | ExpC | Alias da tabela |
| [02] | ExpA | Array unidimensional com os campos que correspondem a primary key |
| [03] | ExpC | Descrição da tabela |

#### GetIndex()

Fornece os dados de todos os índices da estrutura.

**Retorno — Array com a definição dos índices:**

| Posição | Tipo | Descrição |
|---------|------|-----------|
| [01] | ExpN | Ordem numérica |
| [02] | ExpC | Ordem no metadado |
| [03] | ExpC | Chave do índice |
| [04] | ExpC | Descrição do índice |
| [05] | ExpC | LookUp |
| [06] | ExpC | NickName |
| [07] | ExpL | Show? |

#### GetFields()

Retorna a coleção de campos da estrutura.

**Retorno — Array com a estrutura de metadado dos campos:**

| Posição | Tipo | Descrição |
|---------|------|-----------|
| [n][01] | ExpC | Título |
| [n][02] | ExpC | Tooltip |
| [n][03] | ExpC | IdField |
| [n][04] | ExpC | Tipo |
| [n][05] | ExpN | Tamanho |
| [n][06] | ExpN | Decimal |
| [n][07] | ExpB | Valid |
| [n][08] | ExpB | When |
| [n][09] | ExpA | Lista de valores (Combo) |
| [n][10] | ExpL | Obrigatório |
| [n][11] | ExpB | Inicializador padrão |
| [n][12] | ExpL | Campo chave |
| [n][13] | ExpL | Campo atualizável |
| [n][14] | ExpL | Campo virtual |
| [n][15] | ExpC | Valid do usuário em formato texto (usado para criar o aheader de compatibilidade) |

#### GetTriggers()

Retorna a coleção de triggers da estrutura.

**Retorno — Array com a estrutura de metadado dos triggers:**

| Posição | Tipo | Descrição |
|---------|------|-----------|
| [n][01] | ExpC | IdField Origem |
| [n][02] | ExpC | IdField Alvo |
| [n][03] | ExpB | When |
| [n][04] | ExpB | Execução |

#### Outros métodos

| Método | Descrição |
|--------|-----------|
| `IsEmpty()` | Se verdadeiro, a estrutura está vazia |
| `HasField( <cIdField> )` | Informa se um determinado campo existe na estrutura |
| `GetFieldPos( <cIdField> )` | Retorna a posição na estrutura de um campo |
| `getLogicTableName()` | Retorna o nome físico da tabela |
| `FieldsLength()` | Retorna a quantidade de campos na estrutura |
