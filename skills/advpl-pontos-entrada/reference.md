# Pontos de Entrada – ADVPL e MVC

> Guia completo sobre customização do ERP TOTVS Protheus via Pontos de Entrada, cobrindo o modelo clássico ADVPL e o modelo MVC.

---

## Sumário

- [1. Conceito e Propósito](#1-conceito-e-propósito)
- [2. Pontos de Entrada Clássicos (ADVPL)](#2-pontos-de-entrada-clássicos-advpl)
  - [2.1 Como funcionam — ExecBlock e ExistBlock](#21-como-funcionam--execblock-e-existblock)
  - [2.2 Estrutura básica de um Ponto de Entrada](#22-estrutura-básica-de-um-ponto-de-entrada)
  - [2.3 Parâmetros — PARAMIXB](#23-parâmetros--paramixb)
  - [2.4 Retorno dos Pontos de Entrada](#24-retorno-dos-pontos-de-entrada)
  - [2.5 Regras e premissas](#25-regras-e-premissas)
  - [2.6 Como descobrir quais PEs existem em uma rotina](#26-como-descobrir-quais-pes-existem-em-uma-rotina)
  - [2.7 Exemplos reais de PEs clássicos](#27-exemplos-reais-de-pes-clássicos)
  - [2.8 Pontos de Entrada em relatórios (TReport)](#28-pontos-de-entrada-em-relatórios-treport)
  - [2.9 Pontos de Entrada em validações de campo (X3_VALID)](#29-pontos-de-entrada-em-validações-de-campo-x3_valid)
- [3. Pontos de Entrada MVC](#3-pontos-de-entrada-mvc)
  - [3.1 Diferenças em relação ao modelo clássico](#31-diferenças-em-relação-ao-modelo-clássico)
  - [3.2 Estrutura da arquitetura MVC](#32-estrutura-da-arquitetura-mvc)
  - [3.3 PARAMIXB no contexto MVC](#33-paramixb-no-contexto-mvc)
  - [3.4 Tabela completa de IDs de hooks MVC](#34-tabela-completa-de-ids-de-hooks-mvc)
  - [3.5 Detalhamento dos hooks mais importantes](#35-detalhamento-dos-hooks-mais-importantes)
  - [3.6 Exemplos completos de PEs MVC](#36-exemplos-completos-de-pes-mvc)
  - [3.7 Funções de validação no MVC — ModelDef e ViewDef](#37-funções-de-validação-no-mvc--modeldef-e-viewdef)
- [4. Boas Práticas](#4-boas-práticas)
  - [4.1 Quando usar PE vs gatilho vs validação de campo](#41-quando-usar-pe-vs-gatilho-vs-validação-de-campo)
  - [4.2 Preservar o ambiente — GetArea e RestArea](#42-preservar-o-ambiente--getarea-e-restarea)
  - [4.3 Performance](#43-performance)
  - [4.4 Retorno correto](#44-retorno-correto)
- [5. Referência de PEs por módulo](#5-referência-de-pes-por-módulo)
- [6. Fontes e Referências](#6-fontes-e-referências)

---

## 1. Conceito e Propósito

**Ponto de Entrada (PE)** é um mecanismo de extensibilidade do ERP Protheus. São chamadas de programas ADVPL colocadas em pontos estratégicos dentro das rotinas padrão do sistema que, originalmente, não fazem nada.

A TOTVS não distribui os fontes das rotinas padrão compiladas (`.PRW`). Para que parceiros e clientes possam adaptar o sistema sem modificar o código-fonte original, a empresa disponibiliza esses "ganchos" (hooks) em lugares pré-determinados de cada rotina.

O conceito é análogo às *Stored Procedures* de banco de dados: assim que o desenvolvedor identifica a necessidade de uma intervenção, basta criar uma `User Function` com o **nome exato** do ponto de entrada, compilá-la no RPO (Repositório de Objetos) e ela será executada automaticamente quando a rotina padrão passar por aquele ponto.

**Finalidades principais:**
- Adicionar validações de negócio antes ou após operações (inclusão, alteração, exclusão)
- Modificar campos, valores ou comportamentos padrão da tela
- Integrar com sistemas externos após a gravação de registros
- Adicionar botões e ações customizadas na interface
- Bloquear operações com base em regras específicas do cliente

> **Importante:** Pontos de Entrada não devem ser usados para corrigir bugs do sistema padrão. Erros em rotinas padrão devem ser reportados à TOTVS via chamado de suporte.

---

## 2. Pontos de Entrada Clássicos (ADVPL)

### 2.1 Como funcionam — ExecBlock e ExistBlock

No modelo clássico, o sistema chama o PE através de duas funções nativas do framework:

#### `ExistBlock(cFunc)`

Verifica se uma determinada função ou ponto de entrada existe no RPO (Repositório de Objetos). Retorna `.T.` se existir, `.F.` caso contrário.

```advpl
// Sintaxe
ExistBlock( cFunc )

// Parâmetros
// cFunc  - Nome da função ou ponto de entrada (Character)
```

#### `ExecBlock(cFunc, lVar, lSet, uPar)`

Executa um ponto de entrada ou função de usuário. Retorna o valor devolvido pela função chamada.

```advpl
// Sintaxe
ExecBlock( cFunc, lVar, lSet, uPar )

// Parâmetros
// cFunc  - Nome do PE / User Function (Character)
// lVar   - Se .T., passa variáveis privadas M-> para a função
// lSet   - Se .T., seta variáveis privadas no retorno
// uPar   - Parâmetros adicionais, geralmente um Array (acessados via PARAMIXB)
```

**Padrão de chamada dentro das rotinas padrão:**

```advpl
// Padrão mais comum — se o PE não existe, retorna .T. e continua
lRet := !ExistBlock("MT101OK") .OR. ExecBlock("MT101OK", .F., .F.)

// Alternativa explícita
If ExistBlock("MT101OK")
    lRet := ExecBlock("MT101OK", .F., .F.)
EndIf
```

O operador `!ExistBlock(...) .OR. ExecBlock(...)` garante que, se o PE não existir, a expressão já é verdadeira (curto-circuito) e a rotina continua normalmente.

---

### 2.2 Estrutura básica de um Ponto de Entrada

Um PE é simplesmente uma `User Function` com o nome exato do ponto de entrada documentado.

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} MT101OK
    Ponto de entrada na validação do Cadastro de Produtos (MATA101).
    Executado ao clicar em Confirmar, tanto na inclusão quanto na alteração.
    @return lRet Logical - .T. para prosseguir, .F. para bloquear
    @author Desenvolvedor
    @since 01/01/2025
/*/
User Function MT101OK()
    Local lRet := .T.

    // Validação: bloqueia produto sem descrição
    If Empty(M->B1_DESC)
        MsgAlert("A descrição do produto é obrigatória!", "Atenção")
        lRet := .F.
    EndIf

Return lRet
```

**Regras do nome:**
- O nome da `User Function` deve ser **idêntico** ao nome do ponto de entrada (sem distinção de maiúsculas/minúsculas no RPO, mas mantenha o padrão da documentação)
- O nome do arquivo `.PRW` pode ser diferente — é o nome da função que importa
- Tamanho máximo: 10 caracteres (limitação histórica do ADVPL)

---

### 2.3 Parâmetros — PARAMIXB

A variável de sistema `PARAMIXB` recebe os parâmetros passados pelo `ExecBlock` no quarto argumento (`uPar`). Ela é a forma padrão de comunicação entre a rotina padrão e o ponto de entrada.

**Características:**
- É uma variável **privada** do ambiente de execução
- Pode ser de qualquer tipo: `Character`, `Numeric`, `Logical`, `Array`, `Object`, `NIL`
- Quando o `ExecBlock` passa um array, `PARAMIXB` será esse array e cada posição deve ser acessada por índice

```advpl
// Na rotina padrão (como o Protheus chama o PE):
ExecBlock("MEUBLOCK", .F., .F., {cNota, cSerie, dEmissao, nValor})

// No PE (como o desenvolvedor recebe):
User Function MEUBLOCK()
    Local cNota    := PARAMIXB[1]   // "000001"
    Local cSerie   := PARAMIXB[2]   // "01"
    Local dEmissao := PARAMIXB[3]   // 28/03/2026
    Local nValor   := PARAMIXB[4]   // 1500.00

    // Processamento...

Return .T.
```

**Quando PARAMIXB é NIL:**

Alguns pontos de entrada não passam parâmetros. Sempre verifique a documentação e proteja o código:

```advpl
User Function MEUBLOCK()
    Local aParam := PARAMIXB
    Local cNota  := ""

    If aParam <> NIL .AND. ValType(aParam) == "A"
        cNota := aParam[1]
    EndIf

Return .T.
```

**Tabela de tipos comuns de PARAMIXB:**

| Tipo | Exemplo de acesso | Situação típica |
|------|-------------------|-----------------|
| `NIL` | `PARAMIXB == NIL` | PE sem parâmetros |
| `Character` | `PARAMIXB` | Passagem de um único valor texto |
| `Numeric` | `PARAMIXB` | Passagem de um único valor numérico |
| `Logical` | `PARAMIXB` | Passagem de flag verdadeiro/falso |
| `Array` | `PARAMIXB[1]`, `PARAMIXB[2]`... | Passagem de múltiplos valores |
| `Object` | `PARAMIXB:metodo()` | Passagem de objeto do framework |

---

### 2.4 Retorno dos Pontos de Entrada

O tipo de retorno esperado varia conforme o PE. Consulte sempre a documentação oficial no TDN.

| Retorno | Significado | Quando usar |
|---------|-------------|-------------|
| `.T.` | Verdadeiro — prosseguir | Validações OK, operação permitida |
| `.F.` | Falso — bloquear/cancelar | Validação falhou, operação impedida |
| `NIL` | Sem retorno relevante | PEs de ação, pós-gravação sem validação |
| `Array` | Lista de itens | PEs que retornam dados para o sistema |
| `Character` | Valor texto | PEs que definem conteúdo de campo |
| `Numeric` | Valor numérico | PEs de cálculo |

> **Atenção:** retornar um tipo incorreto pode causar erros em tempo de execução na rotina padrão. Se a documentação diz que o retorno é `Logical`, sempre retorne `.T.` ou `.F.`.

**Valor padrão seguro:**

```advpl
User Function MEUBLOCK()
    Local lRet := .T.   // padrão "prosseguir" — seguro se nada precisar ser feito

    // lógica customizada...

Return lRet
```

---

### 2.5 Regras e premissas

#### O que PODE ser feito em um PE

- Implementar validações de negócio adicionais (retornando `.T.`/`.F.`)
- Realizar integrações com APIs externas após gravação
- Popular campos customizados (campos criados pelo cliente no dicionário)
- Exibir mensagens, confirmações e alertas ao usuário
- Gravar logs em tabelas customizadas
- Alterar comportamento de campos da interface
- Adicionar botões e ações à ControlBar

#### O que NÃO PODE / NÃO DEVE ser feito

- **Corrigir bugs** da rotina padrão — abra chamado na TOTVS
- **Usar fora da finalidade documentada** — risco de inconsistência de dados
- **Abrir transações (`Begin Trans`)** quando já existe transação ativa (risco de `deadlock`)
- **Fazer operações pesadas em PEs de campo** — impacta performance a cada digitação
- **Alterar tabelas que a rotina padrão também manipula** sem restaurar o ambiente corretamente

#### Premissa fundamental: restaurar o ambiente

Todas as tabelas acessadas pelo PE **devem ter sua situação restaurada** ao término da execução. Use `GetArea()` e `RestArea()`:

```advpl
User Function MT101OK()
    Local lRet   := .T.
    Local aAreaSA1 := SA1->( GetArea() )   // salva área corrente de SA1

    SA1->( DbSeek(xFilial("SA1") + M->B1_CODVEND) )
    If SA1->( Found() ) .AND. SA1->A1_MSBLQL == "1"
        MsgAlert("Vendedor bloqueado!", "Atenção")
        lRet := .F.
    EndIf

    RestArea(aAreaSA1)   // restaura área de SA1

Return lRet
```

---

### 2.6 Como descobrir quais PEs existem em uma rotina

#### 1. TDN (Documentação Oficial)

O portal [tdn.totvs.com](https://tdn.totvs.com) é a principal fonte. Cada módulo possui sua página de pontos de entrada. Exemplos de páginas:
- Faturamento (SIGAFAT): buscar por "Pontos de Entrada SIGAFAT"
- Compras (SIGACOM): buscar por "Pontos de Entrada MATA103"
- Financeiro (SIGAFIN): buscar por "Pontos de Entrada SIGAFIN"

#### 2. Central de Diagnóstico do Protheus

O próprio sistema possui uma Central de Diagnóstico onde é possível visualizar os pontos de entrada associados a cada rotina em tempo real. Na tabela exibida constam:

| Campo | Descrição |
|-------|-----------|
| Ponto de Entrada | Nome do PE (ex: `A012BRWT`) |
| Descrição | Descrição resumida se documentado |
| Status | `Inexistente`, `Compilado` ou `Desativado` |
| Ação | Opção de ativar/desativar |
| Documento | Link para documentação no TDN |

#### 3. Busca nos fontes (quando disponíveis)

Em relatórios e algumas customizações, os fontes `.PRW` são distribuídos. Pesquise por `ExistBlock` e `ExecBlock` no código:

```advpl
// Procure padrões como:
ExistBlock("NOMEDO PE")
ExecBlock("NOMEDO PE", ...)
```

#### 4. Listas compiladas pela comunidade

- [Terminal de Informação — Lista de PEs](https://terminaldeinformacao.com/2017/11/04/lista-de-pontos-de-entrada-protheus/)
- [Wiki TOTVS — Lista de Pontos de Entrada](https://totvs.fandom.com/pt-br/wiki/Lista_de_Pontos_de_Entrada)
- [Global ERP — Lista PEs TOTVS Protheus](https://globalerp.com.br/lista-pontos-de-entrada-protheus-totvs/)
- [GitHub dan-atilio/AdvPL](https://github.com/dan-atilio/AdvPL) — exemplos funcionais

---

### 2.7 Exemplos reais de PEs clássicos

#### NF de Saída — MATA460 / MATA461 (Faturamento)

| PE | Momento | Retorno | Descrição |
|----|---------|---------|-----------|
| `M460MARK` | Início do processamento | Lógico | Valida pedidos marcados antes de gerar NF |
| `M460VISS` | Cálculo de ISS | Numérico | Permite alterar a base de cálculo do ISS |
| `M460IPI` | Cálculo de IPI | Numérico | Permite alterar valor do IPI da NF |
| `M460IREN` | Retenção de IR | Lógico | Valida/altera retenção de IR na NF |
| `M460FIM` | Pós-gravação da NF | NIL | Executado após gravação total, fora da transação |

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} M460VISS
    PE para alteração da base de cálculo do ISS na geração de NF de Saída.
    @param PARAMIXB[1] - Numeric - Valor base calculado pelo sistema
    @return nBase - Numeric - Novo valor base do ISS
    @author Desenvolvedor
    @since 01/01/2025
/*/
User Function M460VISS()
    Local nBase := PARAMIXB[1]   // valor base calculado pelo sistema

    // Exemplo: aplica desconto de 10% na base do ISS para clientes especiais
    If M->A1_TIPO == "E"
        nBase := nBase * 0.90
    EndIf

Return nBase
```

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} M460FIM
    PE executado após a gravação total da NF de Saída (fora da transação).
    Ideal para integrações externas após confirmação da NF.
    @param PARAMIXB[1] - Character - Número da NF gerada
    @return NIL
/*/
User Function M460FIM()
    Local cNumNF := ""

    If PARAMIXB <> NIL
        cNumNF := PARAMIXB[1]
    EndIf

    // Integração com sistema externo
    If !Empty(cNumNF)
        u_IntegracaoNF(cNumNF)
    EndIf

Return NIL
```

#### Compras / NF de Entrada — MATA103 (SIGACOM)

| PE | Momento | Retorno | Descrição |
|----|---------|---------|-----------|
| `MT103INC` | Validação de inclusão/classificação | Lógico | Verifica se o documento pode ser incluído |
| `MT103FIM` | Pós-gravação da NF de Entrada | NIL | Executado após gravação completa |
| `MT103FIN` | Última validação do folder financeiro | Lógico | Validação final antes de gravar duplicatas |
| `MT103DEV` | Busca de NFs de Saída para devolução | Array | Retorna NFs para o processo de devolução |
| `MT103ISS` | Cálculo de ISS | Numérico | Permite alterar valores do ISS |
| `MT103ENEG` | Controle de negatividade no estoque | Lógico | Permite negatividade em casos especiais |
| `A103BLOQ` | Bloqueio da NF | Lógico | Indica possível bloqueio na NF de Entrada |
| `A103CUST` | Manipulação do custo de entrada | Numérico | Altera custo de entrada dos itens |
| `MA100DSP` | Exibição de dados do cabeçalho | Lógico | Controla visibilidade/edição de campos |

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} MT103INC
    PE para validação na inclusão/classificação do Documento de Entrada (MATA103).
    @return lRet Logical - .T. para prosseguir, .F. para bloquear
/*/
User Function MT103INC()
    Local lRet     := .T.
    Local aAreaSC7 := SC7->( GetArea() )

    // Exemplo: bloqueia NF de fornecedor com CNPJ não validado
    If Empty(M->A2_CGC)
        MsgAlert("Fornecedor sem CNPJ cadastrado. Operação bloqueada.", "Atenção")
        lRet := .F.
    EndIf

    RestArea(aAreaSC7)

Return lRet
```

#### Produtos — MATA101 (Cadastro de Produtos)

| PE | Momento | Retorno | Descrição |
|----|---------|---------|-----------|
| `MT101OK` | Validação antes de gravar (inclusão e alteração) | Lógico | Valida dados do produto antes de confirmar |
| `MT101INC` | Após confirmação de inclusão | Lógico | Executado após incluir um novo produto |
| `MT101ALT` | Após confirmação de alteração | Lógico | Executado após alterar um produto |
| `MT101DEL` | Antes da exclusão | Lógico | Valida se o produto pode ser excluído |

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} MT101OK
    PE de validação do Cadastro de Produtos (MATA101).
    Executado ao confirmar inclusão ou alteração.
    @return lRet Logical - .T. permite gravar, .F. bloqueia
/*/
User Function MT101OK()
    Local lRet := .T.

    // Regra: produto do tipo "PA" (Produto Acabado) deve ter peso informado
    If M->B1_TIPO == "PA" .AND. M->B1_PESO <= 0
        MsgAlert("Produtos Acabados devem ter o Peso informado!", "Validação")
        lRet := .F.
    EndIf

Return lRet


/*/{Protheus.doc} MT101INC
    PE executado após a confirmação de inclusão de produto.
    @return lRet Logical - .T. prossegue, .F. cancela a inclusão
/*/
User Function MT101INC()
    Local lRet := .T.

    // Log de inclusão em tabela customizada
    u_GravarLogProduto(M->B1_COD, "INCLUSAO", cUserName)

    MsgInfo("Produto " + AllTrim(M->B1_COD) + " incluído com sucesso!", "Info")

Return lRet


/*/{Protheus.doc} MT101ALT
    PE executado após a confirmação de alteração de produto.
    @return lRet Logical
/*/
User Function MT101ALT()
    Local lRet := .T.

    // Log de alteração
    u_GravarLogProduto(SB1->B1_COD, "ALTERACAO", cUserName)

Return lRet


/*/{Protheus.doc} MT101DEL
    PE executado antes da exclusão de produto.
    @return lRet Logical - .T. permite excluir, .F. bloqueia
/*/
User Function MT101DEL()
    Local lRet := .T.

    // Bloqueia exclusão de produtos com movimentação nos últimos 12 meses
    If u_TemMovimentacao(SB1->B1_COD, 12)
        MsgAlert("Produto com movimentação recente não pode ser excluído!", "Bloqueio")
        lRet := .F.
    EndIf

Return lRet
```

#### Pedido de Compras — MA100OK / MA100DSP

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} MA100OK
    PE de validação final do Pedido de Compras (MATA100).
    @return lRet Logical
/*/
User Function MA100OK()
    Local lRet    := .T.
    Local nTotal  := 0
    Local nLimite := 50000

    // Soma valor total dos itens do pedido
    nTotal := u_SomaTotalPedido()

    If nTotal > nLimite
        lRet := ApMsgYesNo("Pedido acima de R$ " + Transform(nLimite, "@E 999,999.99") + ;
                           ". Deseja prosseguir?", "Confirmação")
    EndIf

Return lRet
```

#### Outros PEs relevantes

| PE | Módulo | Descrição |
|----|--------|-----------|
| `FA050INC` | Financeiro (FINA050) | Pós-inclusão no Contas a Pagar |
| `A410EXC` | Faturamento (MATA410) | Valida exclusão de Pedido de Venda |
| `M410PVNF` | Faturamento | Valida geração de NF a partir do Pedido de Venda |
| `AFTERLOGIN` | Geral | Executado após login do usuário no módulo |
| `MT010INC` | Estoque | Pós-inclusão no Cadastro de Produtos (MATA010) |
| `MT010BRW` | Estoque | Customização do browse de Produtos |

---

### 2.8 Pontos de Entrada em relatórios (TReport)

O **TReport** é a classe padrão para construção de relatórios customizados no Protheus. Diferente dos PEs de rotina (que têm nomes pré-definidos), relatórios geralmente expõem pontos de customização através de **blocos de código** passados na construção das células e seções.

#### Estrutura básica do TReport

```advpl
#Include "Protheus.ch"
#Include "Report.ch"

/*/{Protheus.doc} RelClientes
    Relatório de clientes usando TReport.
    @author Desenvolvedor
    @since 01/01/2025
/*/
User Function RelClientes()
    Local oReport   as Object
    Local oSection  as Object
    Local oBreak    as Object
    Local cPerg     := "RelCli01"

    // Cria parâmetros de filtro (SX1)
    CriaSX1(cPerg)
    Pergunte(cPerg, .F.)

    // Define o relatório
    oReport := TReport():New( ;
        "RELCLI01",          ;  // ID do relatório
        "Listagem de Clientes", ;  // Título
        cPerg,               ;  // Pergunta (filtros)
        {|oRpt| PrintReport(oRpt, oSection)}, ;  // Bloco de impressão
        "Relatório de Clientes – SA1" ;  // Descrição
    )

    oReport:SetLandscape()     // Orientação paisagem
    oReport:nFontBody := 9     // Tamanho da fonte

    // Define seção com a tabela SA1
    oSection := TRSection():New(oReport, "Clientes", {"SA1"})

    // Define células (colunas)
    TRCell():New(oSection, "A1_COD",  "SA1", "Código",    "C", 8,  .T.)
    TRCell():New(oSection, "A1_NOME", "SA1", "Nome",      "C", 40, .T.)
    TRCell():New(oSection, "A1_CGC",  "SA1", "CNPJ",      "C", 18, .T.)
    TRCell():New(oSection, "A1_MUN",  "SA1", "Cidade",    "C", 20, .T.)
    TRCell():New(oSection, "A1_EST",  "SA1", "UF",        "C", 2,  .T.)

    // Exibe diálogo de impressão
    oReport:PrintDialog()

Return


Static Function PrintReport(oReport, oSection)
    Local cFilAnt := ""
    Local cFil    := xFilial("SA1")

    DbSelectArea("SA1")
    SA1->( DbSetOrder(1) )
    SA1->( DbSeek(cFil) )

    While SA1->( !EOF() ) .AND. SA1->A1_FILIAL == cFil
        oSection:Print()   // imprime a linha corrente
        SA1->( DbSkip() )
    EndDo

Return
```

#### Customização via bCanPrint (condicional de impressão)

```advpl
// Célula que só é impressa para clientes ativos
Local oCell := TRCell():New(oSection, "A1_COD", "SA1", "Código")
oCell:bCanPrint := {|| SA1->A1_MSBLQL != "1"}   // não imprime bloqueados
```

#### Customização via bCellBlock (conteúdo dinâmico)

```advpl
// Célula com conteúdo calculado dinamicamente
Local oCell := TRCell():New(oSection, "A1_SALDO", "SA1", "Saldo")
oCell:bCellBlock := {|| u_CalcSaldoCliente(SA1->A1_COD)}
```

---

### 2.9 Pontos de Entrada em validações de campo (X3_VALID)

O campo `X3_VALID` do dicionário de dados (tabela SX3) define uma **expressão ADVPL** executada para validar o conteúdo de um campo antes de aceitar a entrada do usuário.

```
X3_VALID = "ExecBlock('MYVLDFUN', .F., .F.)"
```

Ou diretamente uma função:

```
X3_VALID = "VldMeuCampo()"
```

**Exemplo de função de validação via X3_VALID:**

```advpl
#Include "Protheus.ch"

/*/{Protheus.doc} VldCodProd
    Validação customizada para o campo B1_COD (Código do Produto).
    Chamado via X3_VALID = "VldCodProd()".
    @return lRet Logical - .T. aceita o valor, .F. rejeita
/*/
User Function VldCodProd()
    Local lRet    := .T.
    Local cCodigo := M->B1_COD

    // Regra: código não pode conter caracteres especiais
    If At("@", cCodigo) > 0 .OR. At("#", cCodigo) > 0
        MsgAlert("Código do produto não pode conter @ ou #", "Validação")
        lRet := .F.
    EndIf

Return lRet
```

**Diferença entre X3_VALID e PE:**

| Aspecto | X3_VALID | Ponto de Entrada |
|---------|----------|------------------|
| Escopo | Campo individual | Operação completa (incl./alt./excl.) |
| Frequência | A cada alteração do campo | Uma vez por operação |
| Performance | Cuidado com lógica pesada | Mais adequado para lógica complexa |
| Parâmetros | Variável `M->` disponível | `PARAMIXB` + variáveis do contexto |
| Configuração | Dicionário de dados (SX3) | Compilação no RPO |

---

## 3. Pontos de Entrada MVC

### 3.1 Diferenças em relação ao modelo clássico

No modelo **clássico**, cada momento de customização tem um nome de PE diferente. Exemplo para MATA010:
- `MT010BRW` — customização do browse
- `MT010INC` — pós-inclusão
- `MT010ALT` — pós-alteração
- `MTA010OK` — validação final

No modelo **MVC**, o conceito é diferente. Cria-se **um único Ponto de Entrada** com o nome igual ao **ID do Model** da rotina, e esse PE é chamado em múltiplos momentos (hooks). O hook ativo é identificado pelo segundo elemento do `PARAMIXB`.

| Aspecto | Clássico | MVC |
|---------|----------|-----|
| Número de PEs | Um por momento | Um único PE para todos os momentos |
| Nome do PE | Nome definido pela TOTVS | ID do Model definido pela rotina |
| Identificação do momento | Pelo próprio nome do PE | Pelo campo `PARAMIXB[2]` (cIdPonto) |
| Acesso ao modelo | Variáveis `M->` e aliases | Objeto `oObj` em `PARAMIXB[1]` |
| Operação atual | Contexto implícito | `oObj:nOperation` ou `oObj:GetOperation()` |

---

### 3.2 Estrutura da arquitetura MVC

Uma rotina MVC é composta por três funções estáticas obrigatórias:

```advpl
// ModelDef — Define o modelo de dados (regras de negócio)
Static Function ModelDef()
    Local oModel := MPFormModel():New("MEUMODEL", ...)
    // configurações do model...
Return oModel


// ViewDef — Define a interface (tela)
Static Function ViewDef()
    Local oModel := FWLoadModel("MEUFONTE")
    Local oView  := FWFormView():New()
    oView:SetModel(oModel)
    // configurações da view...
Return oView


// MenuDef — Define as operações disponíveis (Incluir, Alterar, Excluir...)
Static Function MenuDef()
    Local aRet := FWMVCMenu("MEUFONTE")
Return aRet
```

> **Regra crítica:** O ID do Model (`"MEUMODEL"` no exemplo acima) **não pode ser igual** ao nome do arquivo fonte (`.PRW`). Se o fonte se chama `MEUFONTE.PRW`, o ID do Model deve ser outro — por exemplo, `"MEUMODEL"`.

O PE do usuário terá o nome do **ID do Model**:

```advpl
User Function MEUMODEL()
    // PE MVC
Return xRet
```

---

### 3.3 PARAMIXB no contexto MVC

No PE MVC, `PARAMIXB` é sempre um **array** com a seguinte estrutura:

| Posição | Tipo | Conteúdo |
|---------|------|----------|
| `[1]` | Object / NIL | Objeto da classe em execução (Model ou View) |
| `[2]` | Character | ID do hook (ponto de execução) — ex: `"MODELPOS"` |
| `[3]` | Character | ID do Model (quando `[1]` for NIL) |

```advpl
User Function MEUMODEL()
    Local aParam   := PARAMIXB
    Local oObj     := NIL
    Local cIdPonto := ""
    Local cIdModel := ""

    If aParam <> NIL
        oObj     := aParam[1]   // Objeto do Model ou NIL
        cIdPonto := aParam[2]   // Hook atual: "MODELPOS", "FORMCOMMITTTS", etc.
        cIdModel := IIf(oObj <> NIL, oObj:GetId(), aParam[3])
    EndIf

    // Identificar a operação (inclusão/alteração/exclusão)
    // Usando constantes de FWMVCDEF.CH:
    // MODEL_OPERATION_INSERT = 3
    // MODEL_OPERATION_UPDATE = 4
    // MODEL_OPERATION_DELETE = 5

Return .T.
```

---

### 3.4 Tabela completa de IDs de hooks MVC

| ID do Hook (`cIdPonto`) | Momento de execução | Retorno | Observação |
|-------------------------|---------------------|---------|------------|
| `MODELVLDACTIVE` | Na ativação do modelo | Lógico | Primeiro hook chamado — valida abertura da tela |
| `MODELPRE` | Antes da alteração de qualquer campo do modelo | Lógico | Executado a cada mudança de campo |
| `MODELPOS` | Validação total do modelo ao confirmar | Lógico | Equivalente ao "Tudo Ok" do clássico |
| `FORMPRE` | Antes da alteração de qualquer campo do formulário | Lógico | Específico para um formulário |
| `FORMPOS` | Validação total do formulário | Lógico | Equivalente ao ValidFields do formulário |
| `FORMLINEPRE` | Antes da alteração da linha do grid | Lógico | Equivalente ao `aHeader`/validação de linha |
| `FORMLINEPOS` | Validação total da linha do grid | Lógico | Equivalente ao ValidLines / Linha Ok |
| `FORMCOMMITTTSPRE` | **Antes** da gravação da tabela do formulário | NIL | BeforePost por formulário — dentro da TTS |
| `FORMCOMMITTTSPOS` | **Após** a gravação da tabela do formulário | NIL | AfterPost por formulário — dentro da TTS |
| `MODELCOMMITTTS` | Após gravação total do modelo, **dentro** da TTS | NIL | Dentro da transação — todos os forms gravados |
| `MODELCOMMITNTTS` | Após gravação total do modelo, **fora** da TTS | NIL | Fora da transação — ideal para integrações |
| `MODELCANCEL` | No cancelamento da operação | Lógico | Retornar `.F.` impede o cancelamento |
| `BUTTONBAR` | Para inclusão de botões customizados | Array | Cada item: `{cTitulo, cImagem, bAcao, cTooltip}` |

---

### 3.5 Detalhamento dos hooks mais importantes

#### MODELVLDACTIVE — Ativação do modelo

Executado quando o modelo é ativado, antes de qualquer interação do usuário. Permite verificar a operação (inclusão/alteração/exclusão) e o registro corrente.

```advpl
ElseIf cIdPonto == "MODELVLDACTIVE"
    // Obtém a operação: 3=Insert, 4=Update, 5=Delete
    Local nOper := oObj:nOperation

    If nOper == MODEL_OPERATION_UPDATE
        // Exemplo: bloqueia alteração para usuários sem perfil
        If !(cUserName $ "GERENTE,SUPERVISOR")
            MsgAlert("Somente gerentes podem alterar este cadastro!", "Permissão")
            xRet := .F.
        EndIf
    EndIf
```

#### MODELPOS — Validação ao confirmar

Hook mais utilizado para regras de negócio antes da gravação. Equivalente ao ponto de validação "Tudo Ok" do modelo clássico.

```advpl
ElseIf cIdPonto == "MODELPOS"
    // Acessa campo do formulário via GetValue
    Local cCodigo := oObj:GetValue("CABE", "B1_COD")   // tabela CABE, campo B1_COD
    Local nQtd    := oObj:GetValue("ITENS", "C6_QTDVEN")

    If Empty(cCodigo)
        MsgAlert("Código obrigatório!", "Validação")
        xRet := .F.
    ElseIf nQtd <= 0
        MsgAlert("Quantidade deve ser maior que zero!", "Validação")
        xRet := .F.
    EndIf
```

#### FORMCOMMITTTSPRE / FORMCOMMITTTSPOS — Before/After Post

Executados imediatamente antes e após a gravação de **cada tabela** do formulário, dentro da transação ativa.

```advpl
ElseIf cIdPonto == "FORMCOMMITTTSPRE"
    // Executa ANTES de gravar a tabela
    // Ainda é possível cancelar via xRet := .F. (verificar documentação da rotina)
    ConOut("PRE-gravação do formulário: " + oObj:GetId())

ElseIf cIdPonto == "FORMCOMMITTTSPOS"
    // Executa APÓS gravar a tabela — registros já persistidos
    // Ideal para atualizar campos relacionados dentro da mesma TTS
    Local cCod := oObj:GetValue("CABE", "C5_NUM")
    u_AtualizaTabAux(cCod)
```

#### MODELCOMMITTTS — Após gravação total (dentro da TTS)

Chamado uma única vez após todos os formulários do modelo serem gravados, ainda dentro da transação. Permite operações adicionais de banco que devem estar na mesma transação atômica.

```advpl
ElseIf cIdPonto == "MODELCOMMITTTS"
    Local nOper := oObj:nOperation

    If nOper == MODEL_OPERATION_INSERT
        // Gravar em tabela auxiliar na mesma transação
        RecLock("ZZ1", .T.)   // novo registro em ZZ1 customizada
        ZZ1->ZZ_FILIAL := xFilial("ZZ1")
        ZZ1->ZZ_ORIGEM := "MEUMODEL"
        ZZ1->ZZ_DATA   := dDataBase
        MsUnLock()
    EndIf
```

#### MODELCOMMITNTTS — Após gravação total (fora da TTS)

Chamado após o fechamento da transação. Ideal para integrações com sistemas externos, envio de e-mails, chamadas de API REST — operações que não devem estar dentro da transação do banco.

```advpl
ElseIf cIdPonto == "MODELCOMMITNTTS"
    Local nOper := oObj:nOperation

    If nOper == MODEL_OPERATION_INSERT
        // Integração com API externa (fora da TTS = seguro)
        u_EnviarParaAPI(oObj:GetValue("CABE", "C5_NUM"))
    EndIf
```

#### BUTTONBAR — Botões customizados

Permite adicionar botões à ControlBar da tela MVC. O retorno deve ser um array onde cada item é um array com: `{cTitulo, cImagem, bAcao, cTooltip}`.

```advpl
ElseIf cIdPonto == "BUTTONBAR"
    xRet := {}
    aAdd(xRet, { ;
        "* Aprovação",          ;   // cTitulo (asterisco indica botão de ação)
        "APROVA",               ;   // cImagem (nome do ícone no repositório)
        {|| u_AprovarPedido()}, ;   // bAcao — bloco de código
        "Aprovar este pedido"   ;   // cTooltip
    })
    aAdd(xRet, { ;
        "* Histórico",          ;
        "",                     ;
        {|| u_HistoricoPedido()}, ;
        "Ver histórico de aprovações" ;
    })
```

---

### 3.6 Exemplos completos de PEs MVC

#### Exemplo 1: PE para MATA070 (Cadastro de Bancos)

```advpl
#Include "Protheus.ch"
#Include "FWMVCDEF.CH"

/*/{Protheus.doc} MATA070
    Ponto de Entrada MVC para o Cadastro de Bancos (MATA070).
    O nome deste PE = ID do Model da rotina MATA070.
    O arquivo .PRW deve ter nome diferente, ex: MATA070_PE.PRW
    @author Desenvolvedor
    @since 01/01/2025
/*/
User Function MATA070()
    Local aParam   := PARAMIXB
    Local xRet     := .T.
    Local oObj     := NIL
    Local cIdPonto := ""
    Local cIdModel := ""

    If aParam <> NIL
        oObj     := aParam[1]
        cIdPonto := aParam[2]
        cIdModel := IIf(oObj <> NIL, oObj:GetId(), aParam[3])
    EndIf

    // Adiciona botões customizados
    If cIdPonto == "BUTTONBAR"
        xRet := {}
        aAdd(xRet, {"* Extrato", "", {|| u_ExtratoBank()}, "Ver extrato bancário"})

    // Validação ao confirmar
    ElseIf cIdPonto == "MODELPOS"
        If Empty(oObj:GetValue("CABE", "A6_CONTATO"))
            Aviso("Atenção", "Informe o nome do Contato no banco!", {"OK"}, 03)
            xRet := .F.
        EndIf

    // Antes de gravar a tabela SA6
    ElseIf cIdPonto == "FORMCOMMITTTSPRE"
        // Validação ou ajuste imediatamente antes de persistir
        ConOut("[MATA070 PE] PRE-gravação de " + cIdModel)

    // Após gravar a tabela SA6
    ElseIf cIdPonto == "FORMCOMMITTTSPOS"
        ConOut("[MATA070 PE] POS-gravação de " + cIdModel)

    // Após gravação total — dentro da TTS
    ElseIf cIdPonto == "MODELCOMMITTTS"
        Local nOper := oObj:nOperation
        ConOut("[MATA070 PE] Gravação total. Operação: " + CValToChar(nOper))

    // Após gravação total — fora da TTS (ideal para integrações)
    ElseIf cIdPonto == "MODELCOMMITNTTS"
        u_SincronizarBanco(oObj:GetValue("CABE", "A6_COD"))

    // Controle do cancelamento
    ElseIf cIdPonto == "MODELCANCEL"
        xRet := ApMsgYesNo("Deseja realmente cancelar a operação?", "Confirmação")

    EndIf

Return xRet
```

#### Exemplo 2: PE para rotina MVC de Pedido (CRMA980 — Gestão de Clientes)

```advpl
#Include "Protheus.ch"
#Include "FWMVCDEF.CH"

/*/{Protheus.doc} CRMA980
    PE MVC para o Cadastro de Clientes (CRMA980/MATA030).
    Fonte: MATA030_PECRM.PRW
/*/
User Function CRMA980()
    Local aParam   := PARAMIXB
    Local xRet     := .T.
    Local oObj     := NIL
    Local cIdPonto := ""

    If aParam == NIL
        Return xRet
    EndIf

    oObj     := aParam[1]
    cIdPonto := aParam[2]

    Do Case
    Case cIdPonto == "MODELVLDACTIVE"
        // Bloqueia exclusão de clientes com saldo
        If oObj:nOperation == MODEL_OPERATION_DELETE
            If u_ClienteTemSaldo(SA1->A1_COD)
                MsgAlert("Cliente com saldo em aberto não pode ser excluído!", "Bloqueio")
                xRet := .F.
            EndIf
        EndIf

    Case cIdPonto == "MODELPOS"
        // Valida e-mail ao confirmar
        Local cEmail := oObj:GetValue("SA1MASTER", "A1_EMAIL")
        If !Empty(cEmail) .AND. At("@", cEmail) == 0
            MsgAlert("E-mail inválido: " + cEmail, "Validação")
            xRet := .F.
        EndIf

    Case cIdPonto == "MODELCOMMITNTTS"
        // Integração CRM após gravação confirmada
        Local nOper := oObj:nOperation
        If nOper == MODEL_OPERATION_INSERT
            u_EnviarCRM("NOVO_CLIENTE", SA1->A1_COD)
        ElseIf nOper == MODEL_OPERATION_UPDATE
            u_EnviarCRM("ATUALIZAR_CLIENTE", SA1->A1_COD)
        EndIf

    EndCase

Return xRet
```

---

### 3.7 Funções de validação no MVC — ModelDef e ViewDef

#### ValidFields (equivalente no MVC)

No modelo clássico, o `ValidFields` é configurado no objeto `EnchoiceBar` ou `GetDados`. No MVC, a validação de campo é configurada no `ModelDef` através de `SetFieldValidity`:

```advpl
Static Function ModelDef()
    Local oModel := MPFormModel():New("MEUMODEL", ...)
    Local oStruct

    oStruct := FWFormStruct(1, "SB1")  // estrutura baseada no dicionário SB1

    oModel:AddFields("CABE", NIL, oStruct)

    // Validação de campo específico no model
    oModel:SetFieldValidity("CABE", "B1_TIPO", {|oModel| ValidaTipoProd(oModel)})

Return oModel

Static Function ValidaTipoProd(oModel)
    Local lRet  := .T.
    Local cTipo := oModel:GetValue("CABE", "B1_TIPO")

    If !(cTipo $ "PA/PI/ME/MP")
        MsgAlert("Tipo de produto inválido: " + cTipo, "Validação")
        lRet := .F.
    EndIf

Return lRet
```

#### SetViewAction — Ação customizada na View

O método `SetViewAction` permite associar ações a botões ou eventos da interface:

```advpl
Static Function ViewDef()
    Local oModel := FWLoadModel("MEUFONTE")
    Local oView  := FWFormView():New()

    oView:SetModel(oModel)
    oView:AddField("VIEW", FWFormField():New("CABE"))

    // Define ação para o botão confirmar da View
    oView:SetViewAction("CONFIRM", {|oView| ValidarView(oView)})

Return oView

Static Function ValidarView(oView)
    Local lRet := .T.
    // validações específicas da interface
Return lRet
```

---

## 4. Boas Práticas

### 4.1 Quando usar PE vs gatilho vs validação de campo

| Situação | Recurso recomendado | Motivo |
|----------|---------------------|--------|
| Validar campo simples ao digitar | `X3_VALID` no dicionário | Sem necessidade de compilação, direto no SX3 |
| Calcular campo baseado em outro | `X3_TRIGGER` (gatilho) | Projetado para propagação de valores |
| Validar o registro completo antes de gravar | Ponto de Entrada (`*OK`) | Contexto completo de todos os campos |
| Executar ação após gravação (log, integração) | PE pós-gravação (`*FIM`, `MODELCOMMITNTTS`) | Garante que os dados já estão persistidos |
| Bloquear operação (exclusão, alteração) | PE de validação específico | Retorno `.F.` cancela a operação |
| Adicionar botões/ações à tela | PE `BUTTONBAR` (MVC) | Forma suportada de extensão da interface |
| Manipular grid / linhas | `ValidLines` / `FORMLINEPOS` | Contexto da linha ativo |

### 4.2 Preservar o ambiente — GetArea e RestArea

**Regra fundamental:** qualquer tabela aberta no PE que também seja usada pela rotina padrão deve ter seu estado restaurado.

```advpl
User Function MEUBLOCK()
    Local lRet    := .T.
    Local aAreaSA1 := SA1->( GetArea() )   // salva posição de SA1
    Local aAreaSB1 := SB1->( GetArea() )   // salva posição de SB1

    // Processamento que muda a posição das tabelas
    SA1->( DbSeek(xFilial("SA1") + cCodigo) )
    SB1->( DbSeek(xFilial("SB1") + cProduto) )

    // ... lógica ...

    RestArea(aAreaSB1)   // restaura SB1 ANTES de SA1 (ordem inversa)
    RestArea(aAreaSA1)   // restaura SA1

Return lRet
```

**Para alias diferente do ativo:**

```advpl
// GetArea no alias desejado
Local aAreaSC5 := SC5->( GetArea() )

// ... uso de SC5 ...

RestArea(aAreaSC5)
```

### 4.3 Performance

- **Evite lógica pesada em `X3_VALID`** — é executada a cada tecla pressionada no campo
- **Evite lógica pesada em `MODELPRE` / `FORMPRE`** — executados a cada mudança de campo
- **Use `ExistBlock` sempre antes de `ExecBlock`** para evitar erros quando o PE não existe
- **Não abra transações desnecessárias** em PEs de pós-gravação que já estão em TTS
- **Evite consultas SQL sem índice** em PEs de validação que rodam durante digitação
- **Em grids grandes, evite percorrer todos os itens** em hooks de linha (`FORMLINEPRE`/`FORMLINEPOS`)

```advpl
// Padrão correto: verifica existência antes de executar
If ExistBlock("MT101OK")
    lRet := ExecBlock("MT101OK", .F., .F.)
EndIf

// Forma compacta (curto-circuito):
lRet := !ExistBlock("MT101OK") .OR. ExecBlock("MT101OK", .F., .F.)
```

### 4.4 Retorno correto

```advpl
// ERRADO: retorna tipo diferente do esperado
User Function MT101OK()
Return "OK"   // A rotina espera Logical, não Character!

// CORRETO: retorna o tipo documentado
User Function MT101OK()
    Local lRet := .T.
    // ... validações ...
Return lRet   // Logical

// CORRETO: PE de ação sem retorno relevante
User Function M460FIM()
    // ... integrações ...
Return NIL    // documentado como retorno NIL

// CORRETO: PE que pode ou não ter retorno (proteção)
User Function MEUBLOCK()
    Local xRet := .T.   // valor padrão seguro
    // ... lógica ...
Return xRet
```

---

## 5. Referência de PEs por módulo

### Faturamento (SIGAFAT / MATA460-461)

| PE | Descrição |
|----|-----------|
| `M460MARK` | Valida pedidos marcados antes de gerar NF |
| `M460VISS` | Altera base de cálculo do ISS |
| `M460IPI` | Altera valor do IPI |
| `M460IREN` | Valida/altera retenção de IR |
| `M460FIM` | Pós-gravação total da NF de Saída |
| `M410PVNF` | Valida geração de NF a partir do PV |

### Compras / Documento de Entrada (SIGACOM / MATA103)

| PE | Descrição |
|----|-----------|
| `MT103INC` | Valida inclusão/classificação do documento |
| `MT103FIM` | Pós-gravação do Documento de Entrada |
| `MT103FIN` | Última validação do folder financeiro |
| `MT103DEV` | Retorna NFs para processo de devolução |
| `MT103ISS` | Altera valores do ISS |
| `MT103ENEG` | Controla negatividade do estoque |
| `A103BLOQ` | Indica bloqueio na NF de Entrada |
| `A103CUST` | Manipula custo de entrada |
| `MA100DSP` | Controla exibição de campos do cabeçalho |
| `MA100OK` | Validação final do Pedido de Compras |

### Estoque / Produtos (SIGAEST / MATA101)

| PE | Descrição |
|----|-----------|
| `MT101OK` | Validação antes de gravar produto |
| `MT101INC` | Pós-inclusão de produto |
| `MT101ALT` | Pós-alteração de produto |
| `MT101DEL` | Valida exclusão de produto |
| `MT010BRW` | Customização do browse de produtos |
| `MT010INC` | Pós-inclusão no Cadastro de Produtos (MATA010 MVC) |

### Financeiro (SIGAFIN)

| PE | Descrição |
|----|-----------|
| `FA050INC` | Pós-inclusão no Contas a Pagar (FINA050) |
| `FA050ALT` | Pós-alteração no Contas a Pagar |
| `FA050DEL` | Valida exclusão no Contas a Pagar |
| `FA060INC` | Pós-inclusão no Contas a Receber |

### Geral / Sistema

| PE | Descrição |
|----|-----------|
| `AFTERLOGIN` | Executado após login do usuário no módulo |
| `MBRWBTN` | Adiciona botões ao browse padrão (v11.80+) |

---

## 6. Fontes e Referências

### Documentação Oficial TOTVS

- [TDN — ExecBlock: Execução do Ponto de Entrada](https://tdn.totvs.com/pages/releaseview.action?pageId=6814883)
- [TDN — Pontos de Entrada para fontes ADVPL em MVC](https://tdn.totvs.com/display/public/framework/Pontos+de+Entrada+para+fontes+Advpl+desenvolvidos+utilizando+o+conceito+MVC)
- [TDN — Ponto de Entrada Padrão do MVC](https://tdn.totvs.com.br/pages/releaseview.action?pageId=208345968)
- [Central de Atendimento TOTVS — Ponto de Entrada MVC](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360025211034-Cross-Segmento-TOTVS-Backoffice-Linha-Protheus-ADVPL-Ponto-de-entrada-MVC)
- [Central de Atendimento TOTVS — Pontos de Entrada MVC (lista)](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360025996033-Cross-Segmento-TOTVS-Backoffice-Linha-Protheus-ADVPL-Pontos-de-entrada-MVC)
- [Central de Atendimento TOTVS — PEs MVC MATA010/020/030](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360016405952-Cross-Segmento-TOTVS-Backoffice-Linha-Protheus-ADVPL-Ponto-de-entrada-MVC-para-as-rotinas-MATA010-MATA020-e-MATA030)
- [Central de Atendimento TOTVS — Todos os PEs do Faturamento](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360028794472-Cross-Segmentos-TOTVS-Backoffice-Linha-Protheus-SIGAFAT-Todos-os-Pontos-de-Entrada-no-Faturamento)
- [Central de Atendimento TOTVS — PEs de Compras](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360000169747-Cross-Segmentos-Totvs-Backoffice-Protheus-SIGACOM-Pontos-de-Entrada-Compras)
- [TDN — MDTA056 Pontos de Entrada Padrão MVC](https://tdn.totvs.com/pages/releaseview.action?pageId=828418118)

### Comunidade e Artigos Técnicos

- [Terminal de Informação — Lista de Pontos de Entrada do Protheus](https://terminaldeinformacao.com/2017/11/04/lista-de-pontos-de-entrada-protheus/)
- [Terminal de Informação — Ponto de Entrada MATA070 (MVC)](https://terminaldeinformacao.com/knowledgebase/ponto-de-entrada-mata070-mvc/)
- [Terminal de Informação — Curso Pontos de Entrada](https://terminaldeinformacao.com/2023/09/05/curso-pontos-de-entrada/)
- [Universo do Desenvolvedor — ADVPL Ponto de Entrada em MVC](https://udesenv.com.br/post/advpl-ponto-de-entrada-em-mvc)
- [Universo do Desenvolvedor — CRMA980 PE MVC para Clientes](https://udesenv.com.br/post/crma980-manipulacao-de-cliente-mata030-ponto-de-entrada-mvc)
- [Wiki TOTVS — Lista de Pontos de Entrada](https://totvs.fandom.com/pt-br/wiki/Lista_de_Pontos_de_Entrada)
- [Global ERP — Lista de PEs Protheus TOTVS](https://globalerp.com.br/lista-pontos-de-entrada-protheus-totvs/)

### GitHub — Exemplos Práticos

- [dan-atilio/AdvPL — Exemplos de PEs MVC (MATA070)](https://github.com/dan-atilio/AdvPL/blob/master/Exemplos/V%C3%ADdeo%20Aulas/023%20-%20Pontos%20de%20Entrada%20em%20MVC/MATA070_pe.prw)
- [dan-atilio/AdvPL — Repositório geral ADVPL/TL++](https://github.com/dan-atilio/AdvPL)

### PDFs e Materiais de Referência

- [MVC ADVPL — Central Protheus (PDF)](https://centralprotheus.com.br/wp-content/uploads/2023/12/ADVPL-MVC.pdf)
- [AdvPL utilizando MVC — Aprendendo ADVPL (PDF)](https://aprendendoadvpl.wordpress.com/wp-content/uploads/2013/01/mvc_advpl.pdf)
- [Manual ADVPL com MVC — TOTVS (Academia.edu)](https://www.academia.edu/17040592/Manual_ADVPL_com_MVC_TOTVS)

---

> Documento gerado com base em pesquisa nas fontes oficiais da TOTVS (TDN, Central de Atendimento), forum.totvs.io, GitHub dan-atilio/AdvPL e artigos técnicos da comunidade. Atualizado em março de 2026.
