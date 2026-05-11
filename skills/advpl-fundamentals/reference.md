# Apostila ADVPL I – Programação Avançada

> **Fonte:** TOTVS S.A. – Educação Corporativa
> Todos os direitos autorais reservados pela TOTVS S.A.
> Proibida a reprodução total ou parcial sem prévia autorização por escrito da proprietária.

---

## Sumário

- [1. Objetivo do Curso](#1-objetivo-do-curso)
- [2. A Linguagem ADVPL](#2-a-linguagem-advpl)
  - [2.1 Programação Com Interface Própria com o Usuário](#21-programação-com-interface-própria-com-o-usuário)
  - [2.2 Programação Sem Interface Própria com o Usuário](#22-programação-sem-interface-própria-com-o-usuário)
- [3. Estrutura de um Programa ADVPL](#3-estrutura-de-um-programa-advpl)
  - [3.1 Áreas de um Programa ADVPL](#31-áreas-de-um-programa-advpl)
  - [3.2 Área de Identificação](#32-área-de-identificação)
  - [3.3 Área de Ajustes Iniciais](#33-área-de-ajustes-iniciais)
  - [3.4 Corpo do Programa](#34-corpo-do-programa)
  - [3.5 Área de Encerramento](#35-área-de-encerramento)
- [4. Declaração e Atribuição de Variáveis](#4-declaração-e-atribuição-de-variáveis)
  - [4.1 Tipo de Dados](#41-tipo-de-dados)
  - [4.2 Numérico](#42-numérico)
  - [4.3 Lógico](#43-lógico)
  - [4.4 Caractere](#44-caractere)
  - [4.5 Data](#45-data)
  - [4.6 Array](#46-array)
  - [4.7 Bloco de Código](#47-bloco-de-código)
  - [4.8 Declaração de Variáveis](#48-declaração-de-variáveis)
- [5. Escopo de Variáveis](#5-escopo-de-variáveis)
  - [5.1 O Contexto de Variáveis dentro de um Programa](#51-o-contexto-de-variáveis-dentro-de-um-programa)
  - [5.2 Variáveis de Escopo Local](#52-variáveis-de-escopo-local)
  - [5.3 Variáveis de Escopo Static](#53-variáveis-de-escopo-static)
  - [5.4 Variáveis de Escopo Private](#54-variáveis-de-escopo-private)
  - [5.5 Variáveis de Escopo Public](#55-variáveis-de-escopo-public)
  - [5.6 Entendendo a Influência do Escopo das Variáveis](#56-entendendo-a-influência-do-escopo-das-variáveis)
  - [5.7 Operações com Variáveis](#57-operações-com-variáveis)
- [6. Operadores da Linguagem ADVPL](#6-operadores-da-linguagem-advpl)
  - [6.1.1 Operadores Matemáticos](#611-operadores-matemáticos)
  - [6.1.2 Operadores de String](#612-operadores-de-string)
  - [6.1.3 Operadores Relacionais](#613-operadores-relacionais)
  - [6.1.4 Operadores Lógicos](#614-operadores-lógicos)
  - [6.1.5 Operadores de Atribuição](#615-operadores-de-atribuição)
  - [6.1.6 Atribuição em Linha](#616-atribuição-em-linha)
  - [6.1.7 Atribuição Composta](#617-atribuição-composta)
  - [6.1.8 Operadores de Incremento/Decremento](#618-operadores-de-incrementodecremento)
  - [6.1.9 Operadores Especiais](#619-operadores-especiais)
  - [6.1.10 Ordem de Precedência dos Operadores](#6110-ordem-de-precedência-dos-operadores)
- [7. Operação de Macro Substituição](#7-operação-de-macro-substituição)
- [8. Funções de Manipulação de Variáveis](#8-funções-de-manipulação-de-variáveis)
- [9. Conversões entre Tipos de Variáveis](#9-conversões-entre-tipos-de-variáveis)
  - [9.1 Manipulação de Strings](#91-manipulação-de-strings)
  - [9.2 Manipulação de Variáveis Numéricas](#92-manipulação-de-variáveis-numéricas)
  - [9.3 Verificação de Tipos de Variáveis](#93-verificação-de-tipos-de-variáveis)
- [10. Estruturas Básicas de Programação](#10-estruturas-básicas-de-programação)
- [11. Estruturas de Repetição](#11-estruturas-de-repetição)
  - [11.1 FOR...NEXT](#111-fornext)
  - [11.2 WHILE...ENDDO](#112-whileenddo)
- [12. Estruturas de Decisão](#12-estruturas-de-decisão)
  - [12.1 IF...ELSE...ENDIF](#121-ifelsendif)
  - [12.2 IF...ELSEIF...ELSE...ENDIF](#122-ifelseifelsendif)
  - [12.3 DO CASE...ENDCASE](#123-do-caseendcase)
- [13. Arrays e Blocos de Código](#13-arrays-e-blocos-de-código)
  - [13.1 Arrays](#131-arrays)
  - [13.2 Arrays como Estruturas](#132-arrays-como-estruturas)
  - [13.3 Funções de Manipulação de Arrays](#133-funções-de-manipulação-de-arrays)
  - [13.4 Cópia de Arrays](#134-cópia-de-arrays)
- [14. Blocos de Código](#14-blocos-de-código)
- [15. Funções](#15-funções)
  - [15.1 Tipos e Escopos de Funções](#151-tipos-e-escopos-de-funções)
- [16. Passagem de Parâmetros entre Funções](#16-passagem-de-parâmetros-entre-funções)
  - [16.1 Passagem de Parâmetros por Conteúdo](#161-passagem-de-parâmetros-por-conteúdo)
  - [16.2 Passagem de Parâmetros por Referência](#162-passagem-de-parâmetros-por-referência)
- [18. Diretivas de Compilação](#18-diretivas-de-compilação)
- [19. Diretiva: #INCLUDE](#19-diretiva-include)
- [20. Diretiva: #DEFINE](#20-diretiva-define)
- [21. Diretivas: #IFDEF, #IFNDEF, #ELSE e #ENDIF](#21-diretivas-ifdef-ifndef-else-e-endif)
- [22. Diretiva: #COMMAND](#22-diretiva-command)
- [23. Desenvolvimento de Pequenas Customizações](#23-desenvolvimento-de-pequenas-customizações)
  - [23.1 Acesso e Manipulação de Bases de Dados em ADVPL](#231-acesso-e-manipulação-de-bases-de-dados-em-advpl)
  - [23.2 Funções de Acesso e Manipulação de Dados](#232-funções-de-acesso-e-manipulação-de-dados)
- [24. Diferenciação entre Variáveis e Nomes de Campos](#24-diferenciação-entre-variáveis-e-nomes-de-campos)
- [25. Controle de Numeração Sequencial](#25-controle-de-numeração-sequencial)
- [26. Semáforos](#26-semáforos)
  - [26.1 Funções de Controle de Semáforos](#261-funções-de-controle-de-semáforos)
- [27. Customizações para a Aplicação ERP](#27-customizações-para-a-aplicação-erp)
  - [27.1 Customização de Campos – Dicionário de Dados](#271-customização-de-campos--dicionário-de-dados)
  - [27.2 Pictures de Formação Disponíveis](#272-pictures-de-formação-disponíveis)
  - [27.3 Customização de Gatilhos – Configurador](#273-customização-de-gatilhos--configurador)
  - [27.4 Customização de Parâmetros – Configurador](#274-customização-de-parâmetros--configurador)
- [28. Pontos de Entrada – Conceitos, Premissas e Regras](#28-pontos-de-entrada--conceitos-premissas-e-regras)
  - [28.1 Premissas e Regras](#281-premissas-e-regras)
- [29. Interfaces Visuais](#29-interfaces-visuais)
  - [29.1 Sintaxe e Componentes das Interfaces Visuais](#291-sintaxe-e-componentes-das-interfaces-visuais)
  - [29.2 Interface Visual Completa](#292-interface-visual-completa)
  - [29.3 MBrowse()](#293-mbrowse)
  - [29.4 AxFunctions()](#294-axfunctions)
- [30. Apêndices](#30-apêndices)
  - [30.1 Boas Práticas de Programação](#301-boas-práticas-de-programação)
  - [30.2 Capitulação de Palavras-Chaves](#302-capitulação-de-palavras-chaves)
- [31. Guia de Referência Rápida: Funções e Comandos ADVPL](#31-guia-de-referência-rápida-funções-e-comandos-advpl)
- [32. Funções Visuais para Aplicações](#32-funções-visuais-para-aplicações)

---

## 1. Objetivo do Curso

Ao final do curso o treinando deverá ter desenvolvido os seguintes conceitos, habilidades e atitudes:

**a) Conceitos a serem aprendidos**
- Fundamentos e técnicas de programação
- Princípios básicos da linguagem ADVPL
- Comandos e funções específicas da TOTVS

**b) Habilidades e técnicas a serem aprendidas**
- Resolução de algoritmos através de sintaxes orientadas à linguagem ADVPL
- Análise de fontes de baixa complexidade da aplicação ERP Protheus
- Desenvolvimento de pequenas customizações para o ERP Protheus

**c) Atitudes a serem desenvolvidas**
- Adquirir conhecimentos através da análise das funcionalidades disponíveis no ERP Protheus
- Embasar a realização de outros cursos relativos à linguagem ADVPL

---

## 2. A Linguagem ADVPL

A Linguagem ADVPL teve seu início em 1994, sendo na verdade uma evolução na utilização de linguagens no padrão xBase pela Microsiga Software S.A. (Clipper, Visual Objects e depois FiveWin). Com a criação da tecnologia Protheus, era necessário criar uma linguagem que suportasse o padrão xBase para a manutenção de todo o código existente do sistema de ERP Siga Advanced. Foi então criada a linguagem chamada **Advanced Protheus Language**.

O ADVPL é uma extensão do padrão xBase de comandos e funções, operadores, estruturas de controle de fluxo e palavras reservadas, contando também com funções e comandos disponibilizados pela Microsiga que a torna uma linguagem completa para a criação de aplicações ERP prontas para a Internet. Também é uma linguagem orientada a objetos e eventos, permitindo ao programador desenvolver aplicações visuais e criar suas próprias classes de objetos.

Quando compilados, todos os arquivos de código tornam-se unidades de inteligência básicas, chamados **APO's** (Advanced Protheus Objects). Tais APO's são mantidos em um repositório e carregados dinamicamente pelo PROTHEUS Server para a execução.

O compilador e o interpretador da linguagem ADVPL é o próprio servidor PROTHEUS (PROTHEUS Server), e existe um Ambiente visual para desenvolvimento integrado (PROTHEUSIDE), em que o código pode ser criado, compilado e depurado.

### 2.1 Programação Com Interface Própria com o Usuário

Nesta categoria, entram os programas desenvolvidos para serem executados através do terminal remoto do Protheus, o **Protheus Remote**. O Protheus Remote é a aplicação encarregada da interface e da interação com o usuário, sendo que todo o processamento do código em ADVPL, o acesso ao banco de dados e o gerenciamento de conexões é efetuado no Protheus Server.

Podem-se criar rotinas para a customização do sistema ERP Microsiga Protheus, desde processos adicionais até mesmo relatórios. Todo o código do sistema ERP Microsiga Protheus é escrito em ADVPL.

### 2.2 Programação Sem Interface Própria com o Usuário

As rotinas criadas sem interface geralmente têm uma utilização mais específica. Tais rotinas não têm interface com o usuário através do Protheus Remote. Estas rotinas são apenas processos, ou **Jobs**, executados no Protheus Server.

Subcategorias:

- **Programação por Processos:** Rotinas iniciadas como processos individuais via `StartJob()` ou `CallProc()`, ou automaticamente na inicialização do Protheus Server.
- **Programação de RPC:** Execução de rotinas ADVPL diretamente no Protheus Server por aplicações externas via TCP/IP (*Remote Procedure Call*).
- **Programação Web:** O Protheus Server atua como servidor Web, respondendo a requisições HTTP e compilando arquivos HTML com código ADVPL embutido (ADVPL ASP).
- **Programação TelNet:** Emulação de terminal TelNet ou coletor de dados móvel via rotinas ADVPL.

---

## 3. Estrutura de um Programa ADVPL

Um programa de computador nada mais é do que um grupo de comandos logicamente dispostos com o objetivo de executar determinada tarefa. No caso do ADVPL, o código compilado é executado pelo Protheus Server.

**Tipos de linha:**

- **Linhas de Comando:** possuem comandos ou instruções que serão executadas.
- **Linhas de Comentário:** não são executadas; servem apenas para documentação.
- **Linhas Mistas:** linha de comando com comentário ao final.

**Formas de comentário:**

```advpl
// Comentário de linha (forma recomendada)

/*
  Bloco de comentário
  pode ter várias linhas
*/

* Comentário xBase (obsoleto, evitar)
NOTE Comentário xBase (obsoleto, evitar)
&& Comentário xBase (obsoleto, evitar)
```

**Quebra de linha lógica** — use `;` para continuar a instrução na próxima linha física:

```advpl
If !Empty(cNome) .And. !Empty(cEnd) .And. ;
   !Empty(cTel) .And. !Empty(cFax) .And. ;
   !Empty(cEmail)
   GravaDados(cNome, cEnd, cTel, cFax, cEmail)
Endif
```

### 3.1 Áreas de um Programa ADVPL

A estrutura de um programa ADVPL é composta pelas seguintes áreas:

1. Área de Identificação
2. Área de Ajustes Iniciais
3. Corpo do Programa
4. Área de Encerramento

### 3.2 Área de Identificação

Área não obrigatória, dedicada à documentação do programa. Aparece antes de qualquer linha de comando e pode conter definições de constantes ou inclusões de arquivos de cabeçalho.

```advpl
#include "protheus.ch"

/*
  +==========================================+
  | Programa: Cálculo do Fatorial            |
  | Autor   : Microsiga Software S.A.        |
  | Data    : 02 de outubro de 2001          |
  +==========================================+
*/

User Function CalcFator()
```

### 3.3 Área de Ajustes Iniciais

Nesta área geralmente se fazem os ajustes iniciais: declarações de variáveis, inicializações, abertura de arquivos, etc. Apesar do ADVPL não ser uma linguagem rígida, é aconselhável declarar todas as variáveis aqui para tornar o código mais legível.

### 3.4 Corpo do Programa

É onde se realiza a tarefa necessária por meio da organização lógica das linhas de código. Exemplo:

```advpl
// Cálculo do fatorial
nFator := GetFator()  // GetFator – função ilustrativa

If nFator <= 0
   Alert("Informação inválida")
   Return
Endif

For nCnt := nFator To 1 Step -1
   nResultado *= nCnt
Next nCnt
```

### 3.5 Área de Encerramento

É onde os arquivos abertos são fechados e o resultado da execução é utilizado. Todo programa em ADVPL deve sempre terminar com a palavra-chave `Return`.

```advpl
// Exibe o resultado na tela
MsgAlert("O fatorial de " + cValToChar(nFator) + ;
         " é " + cValToChar(nResultado))

// Termina a função
Return( NIL )
```

---

## 4. Declaração e Atribuição de Variáveis

### 4.1 Tipo de Dados

O ADVPL não é uma linguagem de tipos rígidos (*strongly typed*), o que significa que variáveis de memória podem receber diferentes tipos de dados durante a execução do programa. Os tipos primários são:

| Tipo | Identificador na Notação Húngara |
|---|---|
| Numérico | `n` |
| Lógico | `l` |
| Caractere | `c` |
| Data | `d` |
| Array | `a` |
| Bloco de Código | `b` |
| Objeto | `o` |
| Indefinido | `x` |

### 4.2 Numérico

O ADVPL não diferencia valores inteiros de valores com ponto flutuante. Uma variável numérica pode conter um número de dezoito dígitos, incluindo o ponto flutuante, no intervalo de `2.2250738585072014E–308` até `1.7976931348623158E+308`.

```advpl
2
43.53
0.5
0.00001
1000000
```

### 4.3 Lógico

Valores lógicos são identificados por `.T.` ou `.Y.` para verdadeiro e `.F.` ou `.N.` para falso (independentemente de maiúsculo ou minúsculo).

### 4.4 Caractere

Strings são identificadas por blocos de texto entre aspas duplas ou aspas simples:

```advpl
"Olá !!!"
'Esta é uma string'
"Esta é 'outra' string"
```

Uma variável do tipo caractere pode conter strings com no máximo 1 MB (1.048.576 caracteres).

### 4.5 Data

O ADVPL tem um tipo de dado específico para datas. Internamente são armazenadas como número Juliano. Variáveis do tipo Data não podem ser declaradas diretamente, mas sim por funções como `CTOD()`.

### 4.6 Array

O Array é a disposição de outros elementos em colunas e linhas. O ADVPL suporta arrays unidimensionais (vetores) ou multidimensionais (matrizes). Os elementos são acessados por índices numéricos iniciados em 1.

> **Atenção:** Arrays devem ser utilizados com cautela, pois arrays muito grandes podem exaurir a memória do servidor.

### 4.7 Bloco de Código

O bloco de código é utilizado para armazenar instruções ADVPL que poderão ser executadas posteriormente via função `Eval()`.

### 4.8 Declaração de Variáveis

O nome de uma variável é um identificador único que deve respeitar um máximo de **10 caracteres** (apenas os 10 primeiros são considerados). Exemplo do problema:

```advpl
nTotalGeralMensal := 100
nTotalGeralAnual  := 300
Alert("Valor mensal: " + cValToChar(nTotalGeralMensal))
// Exibirá 300, pois ambas são tratadas como a mesma variável (10 primeiros chars iguais)
```

---

## 5. Escopo de Variáveis

### 5.1 O Contexto de Variáveis dentro de um Programa

Os identificadores de escopo são:

- `Local`
- `Static`
- `Private`
- `Public`

```advpl
Local nNumero := 10
```

Quando um valor é atribuído a uma variável sem identificador de escopo, o ADVPL criará a variável como se tivesse sido declarada como `Private`.

### 5.2 Variáveis de Escopo Local

Pertencentes apenas ao escopo da função onde foram declaradas. Devem ser explicitamente declaradas com `LOCAL`.

```advpl
User Function Pai()
   Local nVar := 10, aMatriz := {0,1,2,3}
   <comandos>
   Filha()
   <mais comandos>
Return(.T.)
```

- São criadas automaticamente a cada ativação da função.
- Continuam a existir até o fim da ativação da função.
- Em recursão, cada chamada cria um novo conjunto de variáveis locais.

### 5.3 Variáveis de Escopo Static

Funcionam como variáveis de escopo local, mas **mantêm seu valor** entre execuções. Devem ser declaradas com `STATIC`.

```advpl
User Function Pai()
   Static nVar := 10
   <comandos>
   Filha()
   <mais comandos>
Return(.T.)
```

- Se declaradas dentro de uma função: escopo limitado àquela rotina.
- Se declaradas fora de qualquer rotina: afeta todas as funções do mesmo arquivo fonte.

### 5.4 Variáveis de Escopo Private

A declaração é opcional (mas recomendada) com o identificador `PRIVATE`. Uma variável privada é visível dentro da função de criação e em todas as funções chamadas por esta.

```advpl
User Function Pai()
   Private nVar := 10
   <comandos>
   Filha()  // nVar está acessível aqui
   <mais comandos>
Return(.T.)
```

### 5.5 Variáveis de Escopo Public

Criadas com o identificador `PUBLIC`. Continuam a existir e mantêm seu valor até o fim da execução da thread (conexão).

```advpl
Public _cRotina  // Inicializa com .F. quando não inicializada explicitamente
```

> **Convenção no ERP Protheus:** adicione o caractere `_` antes do nome de variáveis `PRIVATE` e `PUBLIC`.
> Exemplo: `Public _cRotina`

### 5.6 Entendendo a Influência do Escopo das Variáveis

```advpl
// Errado: variável não declarada causa erro "variable does not exist"
nResultado := 250 * (1 + (nPercentual / 100))

// Correto: declarar e inicializar antes
Local nPercentual := 10
Local nResultado  := 0
nResultado := 250 * (1 + (nPercentual / 100))
```

> Use sempre o operador `:=` (atribuição composta de dois pontos e igual) para evitar confusão com o operador relacional `=`.

### 5.7 Operações com Variáveis

```advpl
Local xVariavel  // Declara a variável inicialmente com valor nulo

xVariavel := "Agora a variável é caractere..."
Alert("Valor do Texto: " + xVariavel)

xVariavel := 22  // Agora a variável é numérica
Alert(cValToChar(xVariavel))

xVariavel := .T.  // Agora a variável é lógica
If xVariavel
   Alert("A variável tem valor verdadeiro...")
Else
   Alert("A variável tem valor falso...")
Endif

xVariavel := Date()  // Agora a variável é data
Alert("Hoje é: " + DtoC(xVariavel))

xVariavel := nil  // Nulo novamente
Alert("Valor nulo: " + xVariavel)  // ERRO: type mismatch on +

Return
```

---

## 6. Operadores da Linguagem ADVPL

### 6.1.1 Operadores Matemáticos

| Operador | Descrição |
|---|---|
| `+` | Adição |
| `-` | Subtração |
| `*` | Multiplicação |
| `/` | Divisão |
| `**` ou `^` | Exponenciação |
| `%` | Módulo (Resto da Divisão) |

### 6.1.2 Operadores de String

| Operador | Descrição |
|---|---|
| `+` | Concatenação de strings (união) |
| `-` | Concatenação com eliminação dos brancos finais das strings intermediárias |
| `$` | Comparação de Substrings (contido em) |

### 6.1.3 Operadores Relacionais

| Operador | Descrição |
|---|---|
| `<` | Menor |
| `>` | Maior |
| `=` | Igual |
| `==` | Exatamente Igual (para caracteres) |
| `<=` | Menor ou Igual |
| `>=` | Maior ou Igual |
| `<>` ou `!=` | Diferente |

### 6.1.4 Operadores Lógicos

| Operador | Descrição |
|---|---|
| `.And.` | E lógico |
| `.Or.` | OU lógico |
| `.Not.` ou `!` | NÃO lógico |

### 6.1.5 Operadores de Atribuição

| Operador | Descrição |
|---|---|
| `:=` | Atribuição Simples |
| `+=` | Adição e Atribuição em Linha |
| `-=` | Subtração e Atribuição em Linha |
| `*=` | Multiplicação e Atribuição em Linha |
| `/=` | Divisão e Atribuição em Linha |
| `**=` ou `^=` | Exponenciação e Atribuição em Linha |
| `%=` | Módulo e Atribuição em Linha |

### 6.1.6 Atribuição em Linha

Permite atribuir mais de uma variável ao mesmo tempo (da direita para a esquerda):

```advpl
// Substitui:
Local nVar1 := 0, nVar2 := 0, nVar3 := 0

// Por:
nVar1 := nVar2 := nVar3 := 0
```

### 6.1.7 Atribuição Composta

| Operador | Exemplo | Equivalente a |
|---|---|---|
| `+=` | `X += Y` | `X = X + Y` |
| `-=` | `X -= Y` | `X = X - Y` |
| `*=` | `X *= Y` | `X = X * Y` |
| `/=` | `X /= Y` | `X = X / Y` |
| `**=` ou `^=` | `X **= Y` | `X = X ** Y` |
| `%=` | `X %= Y` | `X = X % Y` |

### 6.1.8 Operadores de Incremento/Decremento

| Operador | Descrição |
|---|---|
| `++` | Incremento Pós ou Pré-fixado |
| `--` | Decremento Pós ou Pré-fixado |

```advpl
Local nA := 10
Local nB := nA++ + nA  // nB = 21 (10 + 11); nA final = 11

Local nA := 10
Local nB := ++nA + nA  // nB = 22 (11 + 11); nA final = 11
```

### 6.1.9 Operadores Especiais

| Operador | Descrição |
|---|---|
| `()` | Agrupamento ou Função |
| `[]` | Elemento de Matriz |
| `{}` | Definição de Matriz, Constante ou Bloco de Código |
| `->` | Identificador de Apelido (campo de arquivo) |
| `&` | Macro substituição |
| `@` | Passagem de parâmetro por referência |
| `\|\|` | Passagem de parâmetro por valor |

### 6.1.10 Ordem de Precedência dos Operadores

1. Operadores de Incremento/Decremento pré-fixado
2. Operadores de String
3. Operadores Matemáticos
   - Exponenciação
   - Multiplicação e Divisão
   - Adição e Subtração
4. Operadores Relacionais
5. Operadores Lógicos
6. Operadores de Atribuição
7. Operadores de Incremento/Decremento pós-fixado

```advpl
Local nResultado := 2+10/2+5*3+2^3
// Resultado: 30
// Cálculo: 2^3=8, 10/2=5, 5*3=15, então 2+5+15+8=30

Local nResultado := (2+10)/(2+5)*3+2^3
// Resultado: 13.14
// Cálculo: 2^3=8, (2+10)=12, (2+5)=7, então 12/7*3+8=13.14
```

---

## 7. Operação de Macro Substituição

O operador de macro substituição `&` é utilizado para a avaliação de expressões em tempo de execução:

```advpl
X := 10
Y := "X + 1"
B := &Y  // O conteúdo de B será 11
```

O operador de macro cancela as aspas, transformando a string em código executável:
- `&"X + 1"` equivale a `X + 1`

> **Limitação:** variáveis referenciadas dentro da string de caracteres não podem ser `Local`.

---

## 8. Funções de Manipulação de Variáveis

As operações de manipulação de conteúdo mais comuns são:

- Conversões entre tipos de variáveis
- Manipulação de strings
- Manipulação de variáveis numéricas
- Verificação de tipos de variáveis
- Manipulação de arrays
- Execução de blocos de código

---

## 9. Conversões entre Tipos de Variáveis

### CTOD()

Converte uma string no formato `"DD/MM/AAAA"` para uma variável do tipo data.

```advpl
CtoD("01/12/16") + 5  // -> 06/12/2016
```

### DTOC()

Converte uma data para caractere no formato `"DD/MM/AAAA"`.

```advpl
DtoC(Date())  // -> data da máquina em formato "DD/MM/AA" caractere
```

### DTOS()

Converte uma data para caractere no formato `"AAAAMMDD"`.

```advpl
DtoS(Date())  // -> "20161212"
```

### STOD()

Converte uma string `"AAAAMMDD"` para data.

```advpl
Stod("20161212")  // -> data
```

### CVALTOCHAR()

Converte um numérico em string, sem adição de espaços.

```advpl
cValToChar(50)  // -> "50"
```

### STR()

Converte um numérico em string, adicionando espaços à direita.

```advpl
Str(700, 8, 2)  // -> "   700.00"
```

### STRZERO()

Converte um numérico em string, adicionando zeros à esquerda.

```advpl
StrZero(60, 10)  // -> "0000000060"
```

### VAL()

Converte uma string em numérico.

```advpl
Val("1234")  // -> 1234
```

### 9.1 Manipulação de Strings

#### ALLTRIM()

```advpl
AllTrim("   ADVPL   ")  // -> "ADVPL"
```

#### ASC()

Converte um caractere em seu valor ASCII.

```advpl
Asc("A")  // -> 65
```

#### AT()

Retorna a primeira posição de um caractere dentro de uma string.

```advpl
At("a", "abcde")  // -> 1
At("f", "abcde")  // -> 0
```

#### RAT()

Retorna a última posição de um caractere dentro de uma string.

```advpl
RAt("A", "MARIANO")  // -> 5
```

#### CHR()

Converte um código ASCII no caractere correspondente.

```advpl
Chr(65)  // -> "A"
Chr(13)  // -> Tecla Enter
```

#### LEN()

Retorna o tamanho da string ou array.

```advpl
Len("ABCDEF")           // -> 6
Len({"Jorge", 34, .T.}) // -> 3
```

#### LOWER()

```advpl
Lower("AbCdE")  // -> "abcde"
```

#### UPPER()

```advpl
Upper("AbCdE")  // -> "ABCDE"
```

#### STUFF()

Substitui parte de uma string.

```advpl
Stuff("ABCDE", 3, 2, "123")  // -> "AB123E" (substitui "CD" por "123")
```

#### SUBSTR()

Retorna parte de uma string.

```advpl
Substr("ADVPL", 3, 2)  // -> "VL"
```

#### PADR(), PADC(), PADL()

```advpl
PadR("ABC", 10, "*")  // -> "ABC*******"
PadC("ABC", 10, "*")  // -> "***ABC****"
PadL("ABC", 10, "*")  // -> "*******ABC"
```

#### REPLICATE()

```advpl
Replicate("*", 5)  // -> "*****"
```

#### STRTRAN()

Pesquisa e substitui caracteres em uma string.

```advpl
StrTran("ABCABC", "B", "1")  // -> "A1CA1C"
```

### 9.2 Manipulação de Variáveis Numéricas

#### ABS()

Retorna o valor absoluto.

```advpl
ABS(10 - 90)  // -> 80
```

#### INT()

Retorna a parte inteira de um valor.

```advpl
INT(999.10)  // -> 999
```

#### NOROUND()

Trunca a parte decimal conforme quantidade de casas especificada.

```advpl
NOROUND(2.985, 2)  // -> 2.98
```

#### ROUND()

Arredonda conforme critério matemático.

```advpl
ROUND(2.986, 2)  // -> 2.99
```

### 9.3 Verificação de Tipos de Variáveis

#### TYPE()

Determina o tipo do conteúdo de uma variável **não** definida na função em execução.

```advpl
TYPE("DATE()")  // -> "D"
```

#### VALTYPE()

Determina o tipo do conteúdo de uma variável definida na função em execução.

```advpl
VALTYPE("nValor / 2")  // -> "N"
```

**Retornos possíveis:** `"C"` (caractere), `"N"` (numérico), `"D"` (data), `"L"` (lógico), `"A"` (array), `"B"` (bloco de código), `"O"` (objeto), `"U"` (indefinido/nulo).

---

## 10. Estruturas Básicas de Programação

O ADVPL suporta várias estruturas de controle que permitem mudar a sequência de fluxo de execução de um programa. Em ADVPL, todas as estruturas de controle podem ser aninhadas dentro de todas as demais estruturas, contanto que estejam aninhadas propriamente.

---

## 11. Estruturas de Repetição

### 11.1 FOR...NEXT

Repete uma seção de código um número determinado de vezes.

**Sintaxe:**

```advpl
For Variavel := nValorInicial To nValorFinal [Step nIncremento]
   Comandos...
   [Exit]
   [Loop]
Next
```

**Parâmetros:**

| Parâmetro | Descrição |
|---|---|
| `Variavel` | Contador. Se não existir, será criada como variável privada. |
| `nValorInicial To nValorFinal` | Intervalo do contador. |
| `Step nIncremento` | Incremento (positivo ou negativo). Padrão: 1. |
| `Exit` | Sai imediatamente do loop. |
| `Loop` | Retorna ao início do loop sem executar o restante. |

**Exemplo:**

```advpl
Local nCnt
Local nSomaPar := 0

For nCnt := 0 To 100 Step 2
   nSomaPar += nCnt
Next

Alert("A soma dos 100 primeiros números pares é: " + ;
      cValToChar(nSomaPar))
Return
```

### 11.2 WHILE...ENDDO

Repete uma seção de código enquanto uma expressão lógica resultar verdadeiro.

**Sintaxe:**

```advpl
While lExpressao
   Comandos...
   [Exit]
   [Loop]
EndDo
```

**Exemplo com LOOP:**

```advpl
aItens     := ListaProdutos()
nQuantidade := Len(aItens)
nItens      := 0

While nItens < nQuantidade
   nItens++
   If Bloqueado(aItens[nItens])
      Loop  // Volta ao While sem imprimir
   Endif
   Imprime()
EndDo
```

**Exemplo com EXIT:**

```advpl
While lWhile
   If MsgYesNo("Deseja jogar o jogo da forca?")
      JForca()
   Else
      Exit  // Sai do loop
   Endif
EndDo
MsgInfo("Final de Jogo")
```

---

## 12. Estruturas de Decisão

### 12.1 IF...ELSE...ENDIF

```advpl
If lExpressao
   Comandos
[Else
   Comandos...]
Endif
```

**Exemplo:**

```advpl
Local dVencto := CTOD("31/12/16")

If Date() > dVencto
   Alert("Vencimento ultrapassado!")
Endif
Return
```

### 12.2 IF...ELSEIF...ELSE...ENDIF

```advpl
If lExpressao1
   Comandos
[ElseIf lExpressaoX
   Comandos]
[Else
   Comandos...]
Endif
```

**Exemplo:**

```advpl
Local dVencto := CTOD("31/12/16")

If Date() > dVencto
   Alert("Vencimento ultrapassado!")
ElseIf Date() == dVencto
   Alert("Vencimento na data!")
Else
   Alert("Vencimento dentro do prazo!")
Endif
Return()
```

### 12.3 DO CASE...ENDCASE

Executa o primeiro conjunto de comandos cuja expressão condicional resulta em verdadeiro.

```advpl
Do Case
   Case lExpressao1
      Comandos
   Case lExpressao2
      Comandos
   Case lExpressaoN
      Comandos
   Otherwise
      Comandos
EndCase
```

**Exemplo:**

```advpl
Local nMes    := Month(Date())
Local cPeriodo := ""

Do Case
   Case nMes <= 3
      cPeriodo := "Primeiro Trimestre"
   Case nMes >= 4 .And. nMes <= 6
      cPeriodo := "Segundo Trimestre"
   Case nMes >= 7 .And. nMes <= 9
      cPeriodo := "Terceiro Trimestre"
   Otherwise
      cPeriodo := "Quarto Trimestre"
EndCase
Return( NIL )
```

---

## 13. Arrays e Blocos de Código

### 13.1 Arrays

Arrays são coleções de valores. Cada item é referenciado por sua posição numérica iniciada em 1.

```advpl
Local aLetras  // Declaração da variável
aLetras := {"A", "B", "C"}    // Atribuição do array
Alert(aLetras[2])              // Exibe "B"
Alert(cValToChar(Len(aLetras)))// Exibe "3"

AADD(aLetras, "D")  // Adiciona o quarto elemento ao final
Alert(aLetras[4])   // Exibe "D"
```

### 13.2 Arrays como Estruturas

Um array pode conter qualquer tipo de dado simultaneamente:

```advpl
#define FUNCT_NOME   1
#define FUNCT_IDADE  2
#define FUNCT_CASADO 3

aFunct1 := {"Pedro",  32, .T.}
aFunct2 := {"Maria",  22, .T.}
aFunct3 := {"Antônio", 42, .F.}

// Agrupando em um array de arrays (tabela)
aFuncts := { {"Pedro",  32, .T.}, ;
             {"Maria",  22, .T.}, ;
             {"Antônio", 42, .F.} }

Local nCount
For nCount := 1 To Len(aFuncts)
   MsgInfo(aFuncts[nCount, FUNCT_NOME])
Next
```

**Inicializando arrays de tamanho conhecido:**

```advpl
Local nCnt
Local aX[10]            // Método 1: usando colchetes
Local aY := Array(10)   // Método 2: usando função Array()
Local aZ := {0,0,0,0,0,0,0,0,0,0}  // Método 3: listando elementos

For nCnt := 1 To 10
   aX[nCnt] := nCnt * nCnt
Next nCnt
```

**Inicializando arrays de tamanho variável:**

```advpl
Local nCnt
Local aX[0]       // Array vazio via colchetes
Local aY := Array(0)  // Array vazio via função
Local aZ := {}    // Array vazio via chaves

For nCnt := 1 To nSize
   AADD(aX, nCnt * nCnt)
Next nCnt
```

### 13.3 Funções de Manipulação de Arrays

#### ARRAY()

```advpl
aVetor := Array(3)    // array unidimensional com 3 posições
aMatriz := Array(3,2) // array 3x2
```

#### AADD()

Insere um item ao final de um array existente.

```advpl
Local aVetor := {}
AADD(aVetor, "Maria" )
AADD(aVetor, "Jose"  )
AADD(aVetor, "Marcio")

Local aMatriz := {}
AADD(aMatriz, {"Maria",  29, "F"})
AADD(aMatriz, {"Jose",   42, "M"})
AADD(aMatriz, {"Marcio", 53, "M"})
```

#### ACLONE()

Cópia integral dos elementos de um array para outro.

```advpl
aItens := ACLONE(aDados)
```

#### ADEL()

Exclui um elemento do array (a última posição fica nula).

```advpl
Local aVetor := {"1","2","3","4","5","6","7","8","9"}
ADEL(aVetor, 1)
// aVetor -> {"2","3","4","5","6","7","8","9", NIL}
```

#### ASIZE()

Redefine o tamanho de um array.

```advpl
Local aVetor := {"1","2","3","4","5","6","7","8","9"}
aSize(aVetor, 8)
// aVetor -> {"1","2","3","4","5","6","7","8"}
```

#### AINS()

Insere um elemento em qualquer posição do array.

```advpl
Local aVetor := {"1","2","3","4","5","6","7","8","9"}
aIns(aVetor, 1)
// aVetor -> {NIL,"1","2","3","4","5","6","7","8"}
```

#### ASORT()

Ordena os itens de um array.

```advpl
Local aVetor := {"A","D","C","B"}
ASORT(aVetor)                           // -> {"A","B","C","D"}
ASORT(aVetor,,, {|x, y| x > y})        // -> {"D","C","B","A"}

Local aMatriz := {{"Fipe",9.3},{"IPC",8.7},{"DIEESE",12.3}}
ASORT(aMatriz,,,{|x,y| x[2] > y[2]})
// Resultado: DIEESE 12.3 / Fipe 9.3 / IPC 8.7
```

#### ASCAN()

Identifica a posição de um elemento no array.

```advpl
Local aVetor := {"Java","AdvPL","C++"}
nPos := ASCAN(aVetor, "AdvPL")  // -> 2

Local aMatriz := {{"Fipe",9.3},{"IPC",8.7},{"DIEESE",12.3}}
nPos := ASCAN(aMatriz, {|x| x[1] == "IPC"})  // -> 2
```

### 13.4 Cópia de Arrays

> **Atenção:** O operador `:=` em arrays **não copia o conteúdo** — copia apenas a referência (o "mapa" da memória).

```advpl
aPessoas := {"Ricardo", "Cristiane", "André", "Camila"}
aAlunos  := aPessoas  // ERRADO: aAlunos aponta para o mesmo array!

// Qualquer alteração em aAlunos afetará aPessoas também.
// Use ACLONE() para cópia real:

aAlunos := ACLONE(aPessoas)  // CORRETO
```

---

## 14. Blocos de Código

Um bloco de código é semelhante a uma pequena função inline. Para executá-lo, utiliza-se a função `Eval()`:

```advpl
nRes := Eval(B)  // ==> 20
```

### EVAL()

```advpl
nInt   := 10
bBloco := {|N| x := 10, y := x*N, z := y/(x*N)}
nValor := EVAL(bBloco, nInt)
// N = 10, X = 10, Y = 100, Z = 1 (retorno da última expressão)
```

### DBEVAL()

Avalia um bloco de código para cada registro de uma tabela.

```advpl
// Forma tradicional:
dbSelectArea("SX5")
dbSetOrder(1)
dbGotop()
While !Eof() .And. X5_FILIAL == xFilial("SX5") .And. X5_TABELA <= cTab
   nCnt++
   dbSkip()
EndDo

// Com DBEVAL():
dbEval({|x| nCnt++},, {|| X5_FILIAL == xFilial("SX5") .And. X5_TABELA <= cTab})
```

### AEVAL()

Avalia um bloco de código para cada elemento de um array.

```advpl
// Forma tradicional:
AADD(aCampos, "A1_FILIAL")
AADD(aCampos, "A1_COD")
SX3->(dbSetOrder(2))
For nX := 1 To Len(aCampos)
   SX3->(dbSeek(aCampos[nX]))
   aAdd(aTitulos, AllTrim(SX3->X3_TITULO))
Next nX

// Com AEVAL():
aEval(aCampos, {|x| SX3->(dbSeek(x)), IIF(Found(), aAdd(aTitulos, AllTrim(SX3->X3_TITULO)))})
```

---

## 15. Funções

Uma função é um conjunto de comandos reutilizáveis. Os parâmetros em ADVPL são **posicionais** (o que importa é a posição, não o nome).

```advpl
// Chamada:
Calcula(parA, parB, parC)

// Definição:
User Function Calcula(x, y, z)
   ...Comandos da Função
Return ...

// A := Calcula(parA, parB, parC) atribui a A o retorno da função
```

### 15.1 Tipos e Escopos de Funções

#### Function()

Funções ADVPL convencionais, restritas ao desenvolvimento da área de Inteligência Protheus da Microsiga. Nomes com até 10 caracteres significativos. Somente podem ser compiladas com autorização especial.

#### User Function()

Funções definidas pelos usuários. O interpretador ADVPL trata o nome precedido de `"U_"`:

- `U_XMAT100I` é a forma interna de `User Function XMAT100I`
- Recomenda-se nomes com até **8 caracteres** para evitar truncamento
- Para chamar: `U_NomeDaFuncao(parametros)`

#### Static Function()

Visibilidade restrita às funções do mesmo arquivo fonte. Usada para:
- Padronizar nomes de funções com implementações variantes
- Redefinir funções padrão da aplicação localmente
- Proteger funções de uso exclusivo de um arquivo

#### Main Function()

Tipo especial que pode ser executado a partir da tela inicial do client ERP. Desenvolvimento restrito à Inteligência Protheus da Microsiga.

---

## 16. Passagem de Parâmetros entre Funções

### 16.1 Passagem de Parâmetros por Conteúdo

**Exemplo 1 – Passagem de conteúdos diretos:**

```advpl
User Function DirFator()
   Local nResultado := 0
   nResultado := CalcFator(5)  // Passa o valor 5 diretamente
Return

User Function CalcFator(nFator)
   Local nCnt
   Local nResultado := 0
   For nCnt := nFator To 1 Step -1
      nResultado *= nCnt
   Next nCnt
   Alert("O fatorial de " + cValToChar(nFator) + " é " + cValToChar(nResultado))
Return( NIL )
```

**Exemplo 2 – Passagem de variáveis como conteúdos:**

```advpl
User Function DirFator()
   Local nFatorUser := GetFator()  // Obtém valor do usuário
   nResultado := CalcFator(nFatorUser)
Return
```

> **Atenção:** Os parâmetros são variáveis de escopo `LOCAL` para efeito de execução. Não os redeclare como `LOCAL` dentro da função, pois causará perda dos valores recebidos.

### 16.2 Passagem de Parâmetros por Referência

Ao invés de passar o conteúdo, passa-se a referência da área de memória. Usa-se o símbolo `@`:

```advpl
// A variável passada com @ é modificada na função chamadora também
MinhaFuncao(@cVariavel)
```

#### 16.2.1 Tratamento de Conteúdos Padrões (DEFAULT)

O identificador `DEFAULT` garante um valor padrão quando o parâmetro não for informado:

```advpl
User Function CalcFator(nFator)
   Local nCnt
   Local nResultado := 0
   Default nFator := 1  // Se nFator não for passado, assume 1

   For nCnt := nFator To 1 Step -1
      nResultado *= nCnt
   Next nCnt
Return nResultado
```

> Sem `Default`, um parâmetro não informado terá conteúdo nulo (`NIL`), causando erro de *type mismatch* em operações matemáticas.

---

## 18. Diretivas de Compilação

O pré-processador ADVPL examina o programa fonte e executa modificações baseadas em **Diretivas de Compilação** (iniciadas pelo caractere `#`):

```advpl
#INCLUDE
#DEFINE
#IFDEF
#IFNDEF
#ELSE
#ENDIF
#COMMAND
```

---

## 19. Diretiva: #INCLUDE

Indica o arquivo `.CH` (cabeçalho) a ser utilizado pelo pré-processador.

**Principais includes:**

| Include | Descrição |
|---|---|
| `PROTHEUS.CH` | Include padrão da linguagem. Contém a maioria das sintaxes e compatibilidade com Clipper. Inclui: `DIALOG.CH`, `FONT.CH`, `INI.CH`, `PTMENU.CH`, `PRINT.CH` |
| `AP5MAIL.CH` | Sintaxe tradicional para funções de envio/recebimento de e-mail |
| `TOPCONN.CH` | Sintaxe tradicional para integração com TOPCONNECT (DbAcess) |
| `TBICONN.CH` | Definição de conexões com o application server |
| `XMLXFUN.CH` | Manipulação de arquivos e strings no padrão XML |

```advpl
#include "protheus.ch"
```

---

## 20. Diretiva: #DEFINE

Cria constantes no código fonte. Afeta somente o fonte no qual está definida e não permite alteração do conteúdo.

```advpl
#Define NUMLINES 60
#Define NUMPAGES 1000
```

---

## 21. Diretivas: #IFDEF, #IFNDEF, #ELSE e #ENDIF

Permitem criar fontes flexíveis sensíveis ao ambiente (idioma, banco de dados, etc.).

**Verificação de idioma:**

```advpl
#IFDEF SPANISH
   #DEFINE STR0001 "Hola !!!"
#ELSE
   #IFDEF ENGLISH
      #DEFINE STR0001 "Hello !!!"
   #ELSE
      #DEFINE STR0001 "Olá !!!"
   #ENDIF
#ENDIF
```

**Verificação de banco de dados:**

```advpl
#IFDEF TOP
   cQuery := "SELECT * FROM " + RETSQLNAME("SA1")
   dbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), "SA1QRY", .T., .T.)
#ELSE
   DbSelectArea("SA1")
#ENDIF
```

> Não existe a diretiva `#ELSEIF`, o que torna necessário o aninhamento de múltiplos `#IFDEF`.

---

## 22. Diretiva: #COMMAND

Utilizada para traduzir comandos em sintaxe Clipper para funções ADVPL. Exemplo do arquivo `PROTHEUS.CH`:

```advpl
#xcommand @ <nRow>, <nCol> SAY [ <oSay> <label: PROMPT,VAR > ] <cText> ;
   [ PICTURE <cPict> ] ; [ <dlg: OF,WINDOW,DIALOG > <oWnd> ] ;
   [ FONT <oFont> ] ; ...
   => ;
   [ <oSay> := ] TSay():New( <nRow>, <nCol>, <{cText}>, ...)
```

---

## 23. Desenvolvimento de Pequenas Customizações

### 23.1 Acesso e Manipulação de Bases de Dados em ADVPL

A linguagem possui dois grupos de funções distintos:

1. **Funções de manipulação de dados genéricos:** funcionam independentemente do tipo de banco de dados (ISAM ou SQL).
2. **Funções específicas para TOPCONNECT / DBACCESS:** permitem execução de comandos SQL diretamente do fonte.

**Principais diferenças entre bases ISAM e SQL:**

| Característica | ISAM | SQL |
|---|---|---|
| Leitura | Registros inteiros | Pode ler apenas campos necessários |
| Índices | Arquivo CDX único | Índice por numeração sequencial |
| ID do registro | RECNO nativo | Campo `R_E_C_N_O_` (chave primária) |
| Exclusão | Lógica (flag) | Física nativa; lógica implementada via `D_E_L_E_T_` |
| Exclusão lógica | Conceito nativo | Implementado via campos de controle |

**Campos de controle em bancos SQL:**
- `R_E_C_N_O_` — identificador único (chave primária)
- `D_E_L_E_T_` — flag de exclusão lógica
- `R_E_C_D_E_L` — controle complementar

### 23.2 Funções de Acesso e Manipulação de Dados

#### DBRLOCK()

Efetua o lock do registro identificado pelo parâmetro. Sem parâmetro, libera todos os locks e trava o registro posicionado.

#### DBCLOSEAREA()

Fecha o alias ativo na conexão.

```advpl
DbSelectArea("SA1")
DbCloseArea()
```

#### DBCOMMIT() / DBCOMMITALL()

Efetua as atualizações pendentes na área de trabalho ativa / em todas as áreas.

#### DBDELETE()

Exclusão lógica do registro posicionado. Usar com `RecLock()` e `MsUnLock()`.

#### DBGOTO()

Move o cursor para um recno específico.

```advpl
DbSelectArea("SA1")
DbGoto(100)
```

#### DBGOTOP() / DBGOBOTTON()

Move o cursor para o primeiro/último registro lógico.

#### DBSEEK() e MSSEEK()

Posicionam o cursor conforme chave de busca.

```advpl
// DbSeek: busca exata
DbSelectArea("SA1")
DbSetOrder(1)
If DbSeek("01" + "000001" + "02")
   MsgInfo("Cliente localizado")
Else
   MsgAlert("Cliente não encontrado")
Endif

// DbSeek: busca aproximada (SoftSeek)
DbSeek("01" + "000001" + "02", .T.)
```

> `MsSeek()` mantém em memória os dados já localizados, evitando novo acesso ao banco.

#### DBSKIP()

Move o cursor para o próximo/anterior registro.

```advpl
DbSelectArea("SA1")
DbSetOrder(2)  // A1_FILIAL + A1_NOME
DbGoTop()
While !EOF()
   MsgInfo("Cliente: " + A1_NOME)
   DbSkip()
End
```

#### DBSELECTAREA()

Define a área de trabalho ativa.

```advpl
DbSelectArea("SA1")
// ou
DbSelectArea(nArea)
```

#### DBSETFILTER()

Define um filtro para a área de trabalho ativa.

```advpl
bCondicao := {|| A1_COD >= "000001" .AND. A1_COD <= "001000"}
DbSelectArea("SA1")
DbSetOrder(1)
DbSetFilter(bCondicao)
```

#### DBSETORDER()

Define qual índice será utilizado.

```advpl
DbSelectArea("SA1")
DbSetOrder(1)  // A1_FILIAL + A1_COD + A1_LOJA
```

#### DBORDERNICKNAME()

Define qual índice criado pelo usuário será utilizado.

```advpl
DbSelectArea("SA1")
DbOrderNickName("Tipo")  // Índice: A1_FILIAL + A1_TIPO, NickName: Tipo
```

#### DBUSEAREA()

Define um arquivo de banco de dados como área de trabalho.

```advpl
DbUseArea(.T., "DBFCDX", "\SA1010.DBF", "SA1DBF", .T., .F.)
DbSelectArea("SA1DBF")
MsgInfo("A tabela SA1010.DBF possui:" + STRZERO(RecCount(),6) + " registros.")
DbCloseArea()
```

#### RECLOCK()

Trava o registro para inclusão ou alteração.

```advpl
// Inclusão:
DbSelectArea("SA1")
RecLock("SA1", .T.)
SA1->A1_FILIAL := xFilial("SA1")
SA1->A1_COD    := "900001"
SA1->A1_LOJA   := "01"
MsUnLock()

// Alteração:
DbSelectArea("SA1")
DbSetOrder(1)
DbSeek("01" + "900001" + "01")
If Found()
   RecLock("SA1", .F.)
   SA1->A1_NOME   := "CLIENTE CURSO ADVPL BÁSICO"
   SA1->A1_NREDUZ := "ADVPL BÁSICO"
   MsUnLock()
Endif
```

#### MSUNLOCK()

Libera o lock e confirma as atualizações.

#### SOFTLOCK()

Reserva o registro sem obrigação de atualização. Usado nos browses do ERP antes da confirmação de alteração/exclusão.

```advpl
DbSeek(cChave)
If Found()
   SoftLock()
   lConfirma := AlteraSA1()
   If lConfirma
      RecLock("SA1", .F.)
      GravaSA1()
      MsUnLock()
   Endif
Endif
```

#### RLOCK() / UNLOCK() / DBUNLOCK() / DBUNLOCKALL()

Funções adicionais de controle de travamento de registros.

#### SELECT()

Retorna o número de referência de um alias. Retorna 0 se não estiver em uso.

```advpl
nArea := Select("SA1")  // -> 10 (proposto)
```

---

## 24. Diferenciação entre Variáveis e Nomes de Campos

Quando uma variável tem o mesmo nome que um campo, o ADVPL privilegiará o campo. Use os identificadores `MEMVAR` ou `FIELD` (ou o alias da tabela) para distinguir:

```advpl
cRes := MEMVAR->NOME    // Valor da variável de memória NOME
cRes := FIELD->NOME     // Valor do campo NOME na área atual
cRes := CLIENTES->NOME  // Valor do campo NOME da tabela CLIENTES
cRes := SA1->A1_NOME    // SA1 – Cadastro de Clientes
```

---

## 25. Controle de Numeração Sequencial

Alguns campos de numeração do Protheus são fornecidos em ordem ascendente (ex.: número do pedido de venda). Esses campos **não devem ser considerados como chave primária** das tabelas.

---

## 26. Semáforos

O semáforo garante que números sequenciais sejam exclusivos em ambientes multiusuário. Ao ser fornecido, um número fica reservado até a conclusão da operação. Se cancelada, o número volta a ficar disponível.

### 26.1 Funções de Controle de Semáforos

#### GETSXENUM()

```advpl
GETSXENUM(cAlias, cCampo, cAliasSXE, nOrdem)
```

Obtém o número sequencial do alias especificado, através dos arquivos SXE/SXF ou do servidor de numeração.

#### CONFIRMSXE()

```advpl
CONFIRMSXE(lVerifica)
```

Confirma o número alocado pelo último `GETSXENUM()`.

#### ROLLBACKSXE()

```advpl
ROLLBACKSXE()
```

Descarta o número fornecido pelo último `GETSXENUM()`, retornando-o para disponibilização.

---

## 27. Customizações para a Aplicação ERP

Pelos recursos do módulo Configurador, é possível implementar:

- Validações de campos e perguntas
- Inclusão de gatilhos em campos
- Inclusão de regras em parâmetros
- Desenvolvimento de pontos de entrada

### 27.1 Customização de Campos – Dicionário de Dados

As funções de validação têm como característica fundamental um retorno do tipo **lógico** (`.T.` ou `.F.`).

Locais de configuração:
- `SX3` – Validação de usuário (`X3_VLDUSER`)
- `SX1` – Validação da pergunta (`X1_VALID`)

**Funções de validação:**

#### EXISTCHAV()

```advpl
ExistChav(cAlias, cConteudo, nIndice)
```

Retorna `.T.` se o conteúdo já existe no alias (chave duplicada). Exibe help de sistema em caso positivo. Usado para verificar se um código já existe na tabela.

#### EXISTCPO()

```advpl
ExistCpo(cAlias, cConteudo, nIndice)
```

Retorna `.T.` se o conteúdo **não** existe no alias (referência inválida). Exibe help de sistema em caso negativo. Usado para verificar se uma referência existe na tabela relacionada.

#### NAOVAZIO()

```advpl
NaoVazio()
```

Retorna `.T.` se o conteúdo do campo posicionado não está vazio.

#### NEGATIVO()

```advpl
Negativo()
```

Retorna `.T.` se o conteúdo digitado é negativo.

#### PERTENCE()

```advpl
Pertence(cString)
```

Retorna `.T.` se o conteúdo digitado está contido na string parâmetro.

#### POSITIVO()

```advpl
Positivo()
```

Retorna `.T.` se o conteúdo digitado é positivo.

#### TEXTO()

```advpl
Texto()
```

Retorna `.T.` se o conteúdo digitado contém apenas números ou alfanuméricos.

#### VAZIO()

```advpl
Vazio()
```

Retorna `.T.` se o conteúdo do campo posicionado está vazio.

### 27.2 Pictures de Formação Disponíveis

**Funções para Dicionário de Dados (SX3) e GET:**

| Conteúdo | Funcionalidade |
|---|---|
| `A` | Permite apenas caracteres alfabéticos |
| `C` | Exibe CR depois de números positivos |
| `E` | Formato Europeu (ponto e vírgula invertidos) |
| `R` | Insere caracteres de template sem incluir na variável |
| `S<n>` | Rolamento horizontal do texto |
| `X` | Exibe DB depois de números negativos |
| `Z` | Exibe zeros como brancos |
| `(` | Negativos entre parênteses com espaços iniciais |
| `)` | Negativos entre parênteses sem espaços iniciais |
| `!` | Converte para maiúsculo |

**Templates:**

| Conteúdo | Funcionalidade |
|---|---|
| `X` | Permite qualquer caractere |
| `9` | Permite apenas dígitos |
| `#` | Dígitos, sinais e espaços em branco |
| `!` | Converte para maiúsculo |
| `*` | Asterisco no lugar dos espaços em branco iniciais |
| `.` | Ponto decimal |
| `,` | Posição do milhar |

**Exemplos:**

```advpl
// Campo numérico CT2_VALOR (17,2):
Picture: @E 99,999,999,999,999.99

// Campo texto A1_NOME (40 chars) em caixa alta:
Picture: @!
```

### 27.3 Customização de Gatilhos – Configurador

Os gatilhos auxiliam o usuário no preenchimento de informações durante a digitação.

**Regras para configuração da chave de busca:**

- **Tabelas com estrutura cabeçalho/itens:** usar filial da tabela de **origem** do gatilho
  - Pedido de vendas: SC5 x SC6
  - Nota fiscal de entrada: SF1 x SD1
  - Ficha de imobilizado: SN1 x SN3

- **Tabelas de cadastros:** usar filial da tabela a ser **consultada**
  - SA1 – Cadastro de Clientes (compartilhado)
  - SA2 – Cadastro de Fornecedores (compartilhado)
  - SA3 – Cadastro de Vendedores (exclusivo)
  - SA4 – Cadastro de Transportadoras (exclusivo)

- **Tabelas de movimentos:** usar filial da tabela a ser **consultada**
  - SE2 – Contas a pagar (compartilhado)
  - CT2 – Movimentos contábeis (exclusivo)
  - SC7 – Pedidos de compras (compartilhado)
  - SD1 – Itens da nota fiscal de entrada (exclusivo)

### 27.4 Customização de Parâmetros – Configurador

Os parâmetros do sistema possuem:
- **Tipo** (similar ao tipo de uma variável)
- **Interpretação do conteúdo:** simples ou macro executável

Funções para manipulação de parâmetros:

#### GETMV()

```advpl
GETMV(cParametro)
```

Retorna o conteúdo do parâmetro no arquivo SX6, considerando a filial da conexão.

#### GETNEWPAR()

```advpl
GETNEWPAR(cParametro, cPadrao, cFilial)
```

Similar ao `GetMV()`, mas não exibe help quando o parâmetro não existe (para parâmetros que podem não existir na versão atual).

#### PUTMV()

```advpl
PUTMV(cParametro, cConteudo)
```

Atualiza o conteúdo do parâmetro no arquivo SX6.

#### SUPERGETMV()

```advpl
SUPERGETMV(cParametro, lHelp, cPadrao, cFilial)
```

Similar ao `GetMV()`, mas adiciona os parâmetros consultados em área de memória (cache), evitando novos acessos ao banco.

#### 27.4.1 Cuidados na Utilização de Parâmetros

> **Proibido:** usar funções em parâmetros para manipular informações da base de dados do sistema. As rotinas do ERP não protegem a consulta de conteúdos de parâmetros quanto a gravações dentro ou fora de uma transação, podendo causar perda de integridade.
> Para tratamentos adicionais em processos padrões, utilize **Pontos de Entrada**.

---

## 28. Pontos de Entrada – Conceitos, Premissas e Regras

Um ponto de entrada é uma `User Function` desenvolvida para interagir com uma rotina padrão do ERP, com nome pré-estabelecido no desenvolvimento da rotina padrão.

**Finalidades possíveis:**
- Complementar uma validação da aplicação
- Complementar atualizações em tabelas padrões
- Implementar atualizações em tabelas específicas
- Executar ações sem processos de atualização
- Substituir um processamento padrão por uma regra específica do cliente

### 28.1 Premissas e Regras

- O ponto de entrada deve ser **transparente** para o processo padrão
- Todas as tabelas acessadas devem ter sua situação restaurada ao término
- Use `GETAREA()` e `RESTAREA()` para proteger o ambiente:

```advpl
// GETAREA() – Salva o ambiente atual
// Retorno: Array {Alias(), IndexOrd(), Recno()}
aArea := GetArea()

// RESTAREA() – Restaura o ambiente salvo
// Sintaxe: RESTAREA(aArea)
RestArea(aArea)
```

- Parâmetros são recebidos via variável de sistema `PARAMIXB` (pode ser qualquer tipo: simples, array ou objeto)
- Pontos de entrada não recebem parâmetros diretamente (não são chamados como função)

---

## 29. Interfaces Visuais

A linguagem ADVPL possui duas formas para definição de interfaces visuais:
1. Sintaxe convencional (padrões Clipper)
2. Sintaxe orientada a objetos

### 29.1 Sintaxe e Componentes das Interfaces Visuais

**Includes disponíveis:**
- `RWMAKE.CH` — sintaxe Clipper
- `PROTHEUS.CH` — sintaxe ADVPL convencional (recomendado)

**Comparação:**

```advpl
// Include Rwmake.ch (sintaxe Clipper):
#include "rwmake.ch"
@ 0,0 TO 400,600 DIALOG oDlg TITLE "Janela em sintaxe Clipper"
ACTIVATE DIALOG oDlg CENTERED

// Include Protheus.ch (sintaxe ADVPL – recomendada):
#include "Protheus.ch"
DEFINE MSDIALOG oDlg TITLE "Janela em sintaxe ADVPL" FROM 000,000 ;
   TO 400,600 PIXEL
ACTIVATE MSDIALOG oDlg CENTERED
```

**Componentes principais:**

#### BUTTON()

```advpl
@ nLinha, nColuna BUTTON cTexto SIZE nLargura,nAltura UNIDADE OF oObjetoRef ACTION ACAO
```

Define botão de operação com texto simples.

#### MSDIALOG()

```advpl
DEFINE MSDIALOG oObjetoDLG TITLE cTitulo FROM nLinIni,nColIni TO nLiFim,nColFim OF oObjetoRef UNIDADE
```

Define a janela base para os demais componentes.

#### MSGET()

```advpl
@ nLinha, nColuna MSGET VARIAVEL SIZE nLargura,nAltura UNIDADE OF oObjetoRef ;
   F3 cF3 VALID VALID WHEN WHEN PICTURE cPicture
```

Captura informações digitáveis.

#### SAY()

```advpl
@ nLinha, nColuna SAY cTexto SIZE nLargura,nAltura UNIDADE OF oObjetoRef
```

Exibe textos na tela.

#### SBUTTON()

```advpl
DEFINE SBUTTON FROM nLinha, nColuna TYPE N ACTION ACAO STATUS OF oObjetoRef
```

Botão com suporte a imagem (Bitmap) pré-definida.

### 29.2 Interface Visual Completa

```advpl
DEFINE MSDIALOG oDlg TITLE cTitulo FROM 000,000 TO 080,300 PIXEL

@ 001,001 TO 040, 150 OF oDlg PIXEL
@ 010,010 SAY cTexto SIZE 55, 07 OF oDlg PIXEL
@ 010,050 MSGET cCGC SIZE 55, 11 OF oDlg PIXEL ;
   PICTURE "@R 99.999.999/9999-99" VALID !Vazio()

DEFINE SBUTTON FROM 010, 120 TYPE 1 ACTION (nOpca := 1, oDlg:End()) ;
   ENABLE OF oDlg
DEFINE SBUTTON FROM 020, 120 TYPE 2 ACTION (nOpca := 2, oDlg:End()) ;
   ENABLE OF oDlg

ACTIVATE MSDIALOG oDlg CENTERED
```

**Interfaces padrões para atualização de dados:**

#### AxCadastro()

Funcionalidade de cadastro simples com mBrowse padrão e funções de pesquisa, visualização, inclusão, alteração e exclusão.

```advpl
// Sintaxe:
AxCadastro(cAlias, cTitulo, cVldExc, cVldAlt)

// Exemplo:
#include "protheus.ch"

User Function XCadSA2()
   Local cAlias   := "SA2"
   Local cTitulo  := "Cadastro de Fornecedores"
   Local cVldExc  := ".T."
   Local cVldAlt  := ".T."

   dbSelectArea(cAlias)
   dbSetOrder(1)
   AxCadastro(cAlias, cTitulo, cVldExc, cVldAlt)
Return
```

### 29.3 MBrowse()

Funcionalidade de cadastro com recursos avançados: browse com status de registros, legendas, filtros e parametrização de funções para inclusão/alteração/exclusão com estrutura de cabeçalhos e itens.

```advpl
// Sintaxe simplificada:
MBrowse(nLin1, nCol1, nLin2, nCol2, cAlias)
```

**Exemplo básico:**

```advpl
#include "protheus.ch"

User Function MBrwSA2()
   Local cAlias     := "SA2"
   Private cCadastro := "Cadastro de Fornecedores"
   Private aRotina   := {}

   AADD(aRotina, {"Pesquisar" , "AxPesqui", 0, 1})
   AADD(aRotina, {"Visualizar", "AxVisual", 0, 2})
   AADD(aRotina, {"Incluir"   , "AxInclui", 0, 3})
   AADD(aRotina, {"Alterar"   , "AxAltera", 0, 4})
   AADD(aRotina, {"Excluir"   , "AxDeleta", 0, 5})

   dbSelectArea(cAlias)
   dbSetOrder(1)
   mBrowse(6, 1, 22, 75, cAlias)
Return()
```

**Ordem padrão do aRotina:**

| Posição | Ação |
|---|---|
| 1 | Pesquisar |
| 2 | Visualizar |
| 3 | Incluir |
| 4 | Alterar |
| 5 | Excluir |
| 6+ | Livre |

**Parâmetros passados automaticamente pela MBrowse às funções sem `()`:**
- `cAlias` — alias ativo
- `nRecno` — record number do registro posicionado
- `nOpc` — posição da opção no array aRotina

**Exemplo com função customizada de inclusão:**

```advpl
#include "protheus.ch"

User Function MBrwSA2()
   Local cAlias      := "SA2"
   Private cCadastro := "Cadastro de Fornecedores"
   Private aRotina   := {}

   AADD(aRotina, {"Pesquisar" , "AxPesqui"  , 0, 1})
   AADD(aRotina, {"Visualizar", "AxVisual"  , 0, 2})
   AADD(aRotina, {"Incluir"   , "U_BInclui" , 0, 3})  // Função customizada
   AADD(aRotina, {"Alterar"   , "AxAltera"  , 0, 4})
   AADD(aRotina, {"Excluir"   , "AxDeleta"  , 0, 5})

   dbSelectArea(cAlias)
   dbSetOrder(1)
   mBrowse(6, 1, 22, 75, cAlias)
Return( NIL )

//----------------------------------------------------------------------
User Function BInclui(cAlias, nReg, nOpc)
   Local cTudoOk := "(Alert('OK'), .T.)"
   AxInclui(cAlias, nReg, nOpc,,,, cTudoOk)
Return()
```

### 29.4 AxFunctions()

Funções padrões do ERP para visualização, inclusão, alteração e exclusão:

#### AXALTERA()

```advpl
AxAltera(cAlias, nReg, nOpc, aAcho, cFunc, aCpos, cTudoOk, lF3, ;
         cTransact, aButtons, aParam, aAuto, lVirtual, lMaximized)
```

Alteração padrão em formato Enchoice.

#### AXDELETA()

```advpl
AxDeleta(cAlias, nReg, nOpc, cTransact, aCpos, aButtons, aParam, ;
         aAuto, lMaximized)
```

Exclusão padrão em formato Enchoice.

#### AXINCLUI()

```advpl
AxInclui(cAlias, nReg, nOpc, aAcho, cFunc, aCpos, cTudoOk, lF3, ;
         cTransact, aButtons, aParam, aAuto, lVirtual, lMaximized)
```

Inclusão padrão em formato Enchoice.

#### AXPESQUI()

```advpl
AxPesqui()
```

Pesquisa padrão nos registros do browse. Permite seleção do índice e digitação da chave de busca.

#### AXVISUAL()

```advpl
AxVisual(cAlias, nReg, nOpc, aAcho, nColMens, cMensagem, cFunc, ;
         aButtons, lMaximized)
```

Visualização padrão em formato Enchoice.

---

## 30. Apêndices

### 30.1 Boas Práticas de Programação

#### 30.1.1 Utilização de Identação

A identação é **obrigatória** — torna o código muito mais legível.

**Sem identação (ruim):**

```advpl
Local ncnt
while ( ncnt++ < 10 )
ntotal += ncnt * 2
enddo
```

**Com identação (correto):**

```advpl
Local nCnt
While ( nCnt++ < 10 )
   nTotal += nCnt * 2
EndDo
```

### 30.2 Capitulação de Palavras-Chaves

Usar combinação de maiúsculo e minúsculo para facilitar leitura:

```advpl
// Para funções "db": capitalizar apenas após o prefixo
dbSeek()
dbSelectArea()
```

#### Palavras em Maiúsculo

| Situação | Exemplo |
|---|---|
| Constantes | `#Define NUMLINES 60` |
| Variáveis de memória | `M->CT2_CRCONV` |
| Campos | `SC6->C6_NUMPED` |
| Queries SQL | `SELECT * FROM...` |

#### Notação Húngara

Prefixos obrigatórios para variáveis:

| Notação | Tipo de dado | Exemplo |
|---|---|---|
| `a` | Array | `aValores` |
| `b` | Bloco de código | `bSeek` |
| `c` | Caractere | `cNome` |
| `d` | Data | `dDataBase` |
| `l` | Lógico | `lContinua` |
| `n` | Numérico | `nValor` |
| `o` | Objeto | `oMainWindow` |
| `x` | Indefinido | `xConteudo` |

#### Palavras Reservadas

```
AADD     DTOS     INKEY    REPLICATE  VAL
ABS      ELSE     INT      RLOCK      VALTYPE
ASC      ELSEIF   LASTREC  ROUND      WHILE
AT       EMPTY    LEN      ROW        WORD
BOF      ENDCASE  LOCK     RTRIM      YEAR
BREAK    ENDDO    LOG      SECONDS    CDOW
ENDIF    LOWER    SELECT   CHR        EOF
LTRIM    SETPOS   CMONTH   EXP        MAX
SPACE    COL      FCOUNT   MIN        SQRT
CTOD     FIELDNAME MONTH   STR        DATE
FILE     PCOL     SUBSTR   DAY        FLOCK
PCOUNT   TIME     DELETED  FOUND      PROCEDURE
TRANSFORM DEVPOS  FUNCTION PROW       TRIM
DOW      IF       RECCOUNT TYPE       DTOC
IIF      RECNO    UPPER    TRY        AS
CATCH    THROW
```

> Palavras reservadas não podem ser usadas para variáveis, procedimentos ou funções.
> Identificadores que comecem com dois ou mais `_` são reservados para uso interno.
> Identificadores `PRIVATE` ou `PUBLIC` em aplicações de clientes devem começar com `_`.

---

## 31. Guia de Referência Rápida: Funções e Comandos ADVPL

### Conversão entre Tipos de Dados

#### CTOD()

```advpl
// Sintaxe: CTOD(cData)
cData  := "31/12/2016"
dData  := CTOD(cData)
If dDataBase >= dData
   MsgAlert("Data do sistema fora da competência")
Else
   MsgInfo("Data do sistema dentro da competência")
Endif
```

#### CVALTOCHAR()

```advpl
// Sintaxe: CVALTOCHAR(nValor)
For nPercorridos := 1 To 10
   MsgInfo("Passos percorridos: " + CvalToChar(nPercorridos))
Next nPercorridos
```

#### DTOC()

```advpl
// Sintaxe: DTOC(dData)
MsgInfo("Database do sistema: " + DTOC(dData))
```

#### DTOS()

```advpl
// Sintaxe: DTOS(dData)
cQuery := "SELECT A1_COD, A1_LOJA, A1_NREDUZ FROM SA1010 WHERE "
cQuery += "A1_DULTCOM >= '" + DTOS(dDataIni) + "'"
```

#### STOD()

```advpl
// Sintaxe: STOD(sData) — formato "AAAAMMDD"
sData := LerStr(01, 08)
dData := STOD(sData)
```

#### STRZERO()

```advpl
// Sintaxe: STRZERO(nValor, nTamanho)
For nPercorridos := 1 To 10
   MsgInfo("Passos percorridos: " + CvalToChar(nPercorridos))
Next nPercorridos
```

#### VAL()

```advpl
// Sintaxe: VAL(cValor)
Static Function Modulo11(cData)
   Local L, D, P := 0
   L := Len(cData)
   D := 0
   P := 1
   While L > 0
      P := P + 1
      D := D + (Val(SubStr(cData, L, 1)) * P)
      If P = 9
         P := 1
      End
      L := L - 1
   End
   D := 11 - (mod(D, 11))
   If (D == 0 .Or. D == 1 .Or. D == 10 .Or. D == 11)
      D := 1
   End
Return(D)
```

### 31.1 Verificação de Tipos de Variáveis

#### TYPE()

```advpl
// Sintaxe: TYPE("cVariavel")
If TYPE("dDataBase") == "D"
   MsgInfo("Database do sistema: " + DTOC(dDataBase))
Else
   MsgInfo("Variável indefinida no momento")
Endif
```

#### VALTYPE()

```advpl
// Sintaxe: VALTYPE(cVariavel)
Static Function GetTexto(nTamanho, cTitulo, cSay)
   Local cTexto    := ""
   Local nColF     := 0
   Local nLargGet  := 0
   Private oDlg

   Default cTitulo   := "Tela para informar texto"
   Default cSay      := "Informe o texto:"
   Default nTamanho  := 1

   If ValType(nTamanho) != "N"
      nTamanho := 1
   Endif

   cTexto   := Space(nTamanho)
   nLargGet := Round(nTamanho * 2.5, 0)
   nColf    := Round(195 + (nLargGet * 1.75), 0)

   DEFINE MSDIALOG oDlg TITLE cTitulo FROM 000,000 TO 120,nColF PIXEL
   @ 005,005 TO 060, Round(nColF/2, 0) OF oDlg PIXEL
   @ 010,010 SAY cSay SIZE 55, 7 OF oDlg PIXEL
   @ 010,065 MSGET cTexto SIZE nLargGet, 11 OF oDlg PIXEL ;
      Picture "@!" VALID !Empty(cTexto)
   DEFINE SBUTTON FROM 030, 010 TYPE 1 ;
      ACTION (nOpca := 1, oDlg:End()) ENABLE OF oDlg
   DEFINE SBUTTON FROM 030, 040 TYPE 2 ;
      ACTION (nOpca := 0, oDlg:End()) ENABLE OF oDlg
   ACTIVATE MSDIALOG oDlg CENTERED

   cTexto := IIF(nOpca == 1, cTexto, "")
Return cTexto
```

### 31.2 Manipulação de Arrays

#### Array()

```advpl
// Sintaxe: Array(nLinhas, nColunas)
aDados := Array(3, 3)  // Array 3x3; elementos inicialmente nulos
// aDados[1][1] -> nulo
```

#### AADD()

```advpl
// Sintaxe: AADD(aArray, xItem)
aDados := {}
aItem  := {}

AADD(aItem, cVariavel1)
AADD(aItem, cVariavel2)
AADD(aItem, cVariavel3)
AADD(aDados, aItem)
AADD(aDados, aItem)
AADD(aDados, aItem)
// aDados[1][1], aDados[1][2], aDados[1][3]
// aDados[2][1], aDados[2][2], aDados[2][3]
// aDados[3][1], aDados[3][2], aDados[3][3]
```

#### ACLONE()

```advpl
// Sintaxe: ACLONE(aArray)
aItens := ACLONE(aDados)
// aItens possui exatamente a mesma estrutura e informações de aDados
```

#### ADEL()

```advpl
// Sintaxe: ADEL(aArray, nPosição)
ADEL(aItens, 1)  // Remove o primeiro elemento
// aItens[1] -> antigo aItens[2]
// aItens[2] -> antigo aItens[3]
// aItens[3] -> nulo (última posição fica nula)
```

#### ASIZE()

```advpl
// Sintaxe: ASIZE(aArray, nTamanho)
ASIZE(aItens, Len(aItens) - 1)
// Prática recomendada após ADEL() para remover o elemento nulo final
```

#### ASORT()

```advpl
// Sintaxe: ASORT(aArray, nInicio, nItens, bOrdem)
aAlunos := {"Mauren", "Soraia", "Andréia"}

// Ascendente:
aSort(aAlunos)
// -> {"Andréia", "Mauren", "Soraia"}

// Descendente:
bOrdem := {|cNomeAtu, cNomeProx| cNomeAtu > cNomeProx}
aSort(aAlunos,,, bOrdem)
// -> {"Soraia", "Mauren", "Andréia"}
```

#### ASCAN()

```advpl
// Sintaxe: ASCAN(aArray, bSeek)
aAlunos    := {"Márcio", "Denis", "Arnaldo", "Patrícia"}
bSeek      := {|cNome| cNome == "Denis"}
nPosAluno  := aScan(aAlunos, bSeek)  // -> 2
```

#### AINS()

```advpl
// Sintaxe: AINS(aArray, nPosicao)
aAlunos := {"Edson", "Robson", "Renato", "Tatiana"}
AINS(aAlunos, 3)
// -> {"Edson", "Robson", NIL, "Renato", "Tatiana"}
// O elemento inserido tem conteúdo nulo — deve ser preenchido posteriormente
```

### 31.3 Manipulação de Blocos de Código

#### EVAL()

```advpl
// Sintaxe: EVAL(bBloco, xParam1, xParam2, xParamZ)
nInt   := 10
bBloco := {|N| x := 10, y := x*N, z := y/(x*N)}
nValor := EVAL(bBloco, nInt)
// N=10, X=10, Y=100, Z=1 (retorno: última expressão = z = 1)
```

#### DBEVAL()

```advpl
// Sintaxe: DBEVAL(bBloco, bFor, bWhile)

// Exemplo 01:
dbSelectArea("SX5")
dbSetOrder(1)
dbGotop()
// Forma com DBEVAL:
dbEval({|x| nCnt++},, {|| X5_FILIAL == xFilial("SX5") .And. X5_TABELA <= mv_par02})

// Exemplo 02:
dbEval({|| aAdd(aTabela, {X5_CHAVE, Capital(X5_DESCRI)})},, ;
       {|| X5_TABELA == cTabela})
```

#### AEVAL()

```advpl
// Sintaxe: AEVAL(aArray, bBloco, nInicio, nFim)
AADD(aCampos, "A1_FILIAL")
AADD(aCampos, "A1_COD")
SX3->(dbSetOrder(2))

// Forma com AEVAL:
aEval(aCampos, {|x| SX3->(dbSeek(x)), IIF(Found(), aAdd(aTitulos, ;
      AllTrim(SX3->X3_TITULO)))})
```

### 31.4 Manipulação de Strings

#### ALLTRIM()

```advpl
// Sintaxe: ALLTRIM(cString)
cNome := ALLTRIM(SA1->A1_NOME)
MsgInfo("Tamanho sem espaços: " + CVALTOCHAR(LEN(cNome)))
```

#### ASC()

```advpl
// Sintaxe: ASC(cCaractere)
User Function NoAcento(Arg1)
   Local nConta := 0
   Local cLetra := ""
   Local cRet   := ""

   Arg1 := Upper(Arg1)
   For nConta := 1 To Len(Arg1)
      cLetra := SubStr(Arg1, nConta, 1)
      Do Case
         Case (Asc(cLetra) > 191 .And. Asc(cLetra) < 198) .Or. ;
              (Asc(cLetra) > 223 .And. Asc(cLetra) < 230)
            cLetra := "A"
         Case (Asc(cLetra) > 199 .And. Asc(cLetra) < 204) .Or. ;
              (Asc(cLetra) > 231 .And. Asc(cLetra) < 236)
            cLetra := "E"
         Case (Asc(cLetra) > 204 .And. Asc(cLetra) < 207) .Or. ;
              (Asc(cLetra) > 235 .And. Asc(cLetra) < 240)
            cLetra := "I"
         Case (Asc(cLetra) > 209 .And. Asc(cLetra) < 215) .Or. ;
              (Asc(cLetra) == 240) .Or. (Asc(cLetra) > 241 .And. ;
              Asc(cLetra) < 247)
            cLetra := "O"
         Case (Asc(cLetra) > 216 .And. Asc(cLetra) < 221) .Or. ;
              (Asc(cLetra) > 248 .And. Asc(cLetra) < 253)
            cLetra := "U"
         Case Asc(cLetra) == 199 .Or. Asc(cLetra) == 231
            cLetra := "C"
      EndCase
      cRet := cRet + cLetra
   Next
Return UPPER(cRet)
```

#### AT()

```advpl
// Sintaxe: AT(cCaractere, cString)
Static Function NoMascara(cString, cMascara, nTamanho)
   Local cNoMascara := ""
   Local nX         := 0

   If !Empty(cMascara) .AND. AT(cMascara, cString) > 0
      For nX := 1 To Len(cString)
         If !(SUBSTR(cString, nX, 1) $ cMascara)
            cNoMascara += SUBSTR(cString, nX, 1)
         Endif
      Next nX
      cNoMascara := PADR(ALLTRIM(cNoMascara), nTamanho)
   Else
      cNoMascara := PADR(ALLTRIM(cString), nTamanho)
   Endif
Return cNoMascara
```

#### CHR()

```advpl
// Sintaxe: CHR(nASCII)
#DEFINE CRLF CHR(13) + CHR(10)  // Final de linha
```

#### LEN()

```advpl
// Sintaxe: LEN(cString)
cNome := ALLTRIM(SA1->A1_NOME)
MsgInfo("Tamanho campo: " + CVALTOCHAR(LEN(SA1->A1_NOME)) + CRLF + ;
        "Tamanho sem espaços: " + CVALTOCHAR(LEN(cNome)))
```

#### LOWER() / UPPER()

```advpl
// Sintaxe: LOWER(cString) / UPPER(cString)
cTexto := "ADVPL"
MsgInfo("Minúsculo: " + LOWER(cTexto))  // -> "advpl"
MsgInfo("Maiúsculo: " + UPPER("advpl")) // -> "ADVPL"
```

#### RAT()

```advpl
// Sintaxe: RAT(cCaractere, cString)
// Retorna a última posição de um caractere na string
```

#### STUFF()

```advpl
// Sintaxe: STUFF(cString, nPosInicial, nExcluir, cAdicao)
cLin := Space(100) + cEOL
cCpo := PADR(SA1->A1_FILIAL, 02)
cLin := Stuff(cLin, 01, 02, cCpo)
```

#### SUBSTR()

```advpl
// Sintaxe: SUBSTR(cString, nPosInicial, nCaracteres)
cCampo    := "A1_NOME"
nPosUnder := AT("_", cCampo)
cPrefixo  := SUBSTR(cCampo, 1, nPosUnder)  // -> "A1_"
```

### 31.5 Manipulação de Variáveis Numéricas

#### ABS()

```advpl
// Sintaxe: ABS(nValor)
nPessoas := 20
nLugares := 18
If nPessoas < nLugares
   MsgInfo("Existem " + CVALTOCHAR(nLugares - nPessoas) + " disponíveis")
Else
   MsgStop("Existem " + CVALTOCHAR(ABS(nLugares - nPessoas)) + " faltando")
Endif
```

#### INT()

```advpl
// Sintaxe: INT(nValor)
Static Function Comprar(nQuantidade)
   Local nDinheiro := 0.30
   Local nPrcUnit  := 0.25

   If nDinheiro >= (nQuantidade * nPrcUnit)
      Return nQuantidade
   ElseIf nDinheiro > nPrcUnit
      nQuantidade := INT(nDinheiro / nPrcUnit)
   Else
      nQuantidade := 0
   Endif
Return nQuantidade
```

#### NOROUND()

```advpl
// Sintaxe: NOROUND(nValor, nCasas)
nBase  := 2.985
nValor := NOROUND(nBase, 2)  // -> 2.98 (trunca)
```

#### ROUND()

```advpl
// Sintaxe: ROUND(nValor, nCasas)
nBase  := 2.985
nValor := ROUND(nBase, 2)  // -> 2.99 (arredonda)
```

### 31.6 Manipulação de Arquivos

#### SELECT()

```advpl
// Sintaxe: Select(cArea)
nArea := Select("SA1")
Alert("Referência do alias SA1: " + STRZERO(nArea, 3))  // -> "010"
```

#### DBGOTO()

```advpl
// Sintaxe: DbGoto(nRecno)
DbSelectArea("SA1")
DbGoto(100)
If !EOF()
   MsgInfo("Você está no cliente: " + A1_NOME)
Endif
```

#### DBGOTOP()

```advpl
// Sintaxe: DbGoTop()
nCount := 0
DbSelectArea("SA1")
DbSetOrder(1)
DbGoTop()
While !BOF()
   nCount++
   DbSkip(-1)
EndDo
MsgInfo("Existem: " + STRZERO(nCount, 6) + " registros no intervalo")
```

#### DBGOBOTTON()

```advpl
// Sintaxe: DbGoBotton()
nCount := 0
DbSelectArea("SA1")
DbSetOrder(1)
DbGoBotton()
While !EOF()
   nCount++
   DbSkip(1)
End
MsgInfo("Existem: " + STRZERO(nCount, 6) + " registros no intervalo")
```

#### DBSELECTAREA()

```advpl
// Sintaxe: DbSelectArea(nArea | cArea)

// Por número:
nArea := Select("SA1")  // -> 10
DbSelectArea(nArea)
Alert("Nome do cliente: " + A1_NOME)

// Por nome:
DbSelectArea("SA1")
Alert("Nome do cliente: " + A1_NOME)
```

#### DBSETORDER()

```advpl
// Sintaxe: DbSetOrder(nOrdem)
DbSelectArea("SA1")
DbSetOrder(1)  // A1_FILIAL + A1_COD + A1_LOJA (conforme SIX)
```

#### DBORDERNICKNAME()

```advpl
// Sintaxe: DbOrderNickName(NickName)
DbSelectArea("SA1")
DbOrderNickName("Tipo")  // Índice: A1_FILIAL + A1_TIPO, NickName: Tipo
```

#### DBSEEK() e MSSEEK()

```advpl
// Sintaxe: DbSeek(cChave, lSoftSeek, lLast)

// Busca exata:
DbSelectArea("SA1")
DbSetOrder(1)
If DbSeek("01" + "000001" + "02")
   MsgInfo("Cliente localizado", "Consulta por cliente")
Else
   MsgAlert("Cliente não encontrado", "Consulta por cliente")
Endif

// Busca aproximada:
DbSeek("01" + "000001" + "02", .T.)
MsgInfo("Filial: " + A1_FILIAL + CRLF + ;
        "Código: " + A1_COD   + CRLF + ;
        "Loja: "   + A1_LOJA  + CRLF + ;
        "Nome: "   + A1_NOME, "Consulta por cliente")
```

#### DBSKIP()

```advpl
// Sintaxe: DbSkip(nRegistros)

// Avançar registros:
DbSelectArea("SA1")
DbSetOrder(2)  // A1_FILIAL + A1_NOME
DbGoTop()
While !EOF()
   MsgInfo("Você está no cliente: " + A1_NOME)
   DbSkip()
End

// Retroceder registros:
DbGoBotton()
While !BOF()
   MsgInfo("Você está no cliente: " + A1_NOME)
   DbSkip(-1)
End
```

#### DBSETFILTER()

```advpl
// Sintaxe: DbSetFilter(bCondicao, cCondicao)

// Com bloco de código:
bCondicao := {|| A1_COD >= "000001" .AND. A1_COD <= "001000"}
DbSelectArea("SA1")
DbSetOrder(1)
DbSetFilter(bCondicao)

// Com expressão simples:
cCondicao := "A1_COD >= '000001' .AND. A1_COD <= '001000'"
DbSetFilter(, cCondicao)
```

#### DBSTRUCT()

```advpl
// Sintaxe: DbStruct()
// Retorna array bidimensional com a estrutura da área de trabalho ativa
cCampos    := ""
DbSelectArea("SA1")
aStructSA1 := DbStruct()
For nX := 1 To Len(aStructSA1)
   cCampos += aStructSA1[nX][1] + "/"
Next nX
Alert(cCampos)
```

#### RECLOCK()

```advpl
// Sintaxe: RecLock(cAlias, lInclui)

// Inclusão:
DbSelectArea("SA1")
RecLock("SA1", .T.)
SA1->A1_FILIAL := xFilial("SA1")
SA1->A1_COD    := "900001"
SA1->A1_LOJA   := "01"
MsUnLock()

// Alteração:
DbSelectArea("SA1")
DbSetOrder(1)
DbSeek("01" + "900001" + "01")
If Found()
   RecLock("SA1", .F.)
   SA1->A1_NOME   := "CLIENTE CURSO ADVPL BÁSICO"
   SA1->A1_NREDUZ := "ADVPL BÁSICO"
   MsUnLock()
Endif
```

#### MSUNLOCK()

```advpl
// Sintaxe: MsUnLock()
DbSelectArea("SA1")
DbSetOrder(1)
DbSeek("01" + "900001" + "01")
If Found()
   RecLock("SA1", .F.)
   SA1->A1_NOME   := "CLIENTE CURSO ADVPL BÁSICO"
   SA1->A1_NREDUZ := "ADVPL BÁSICO"
   MsUnLock()
Endif
```

#### SOFTLOCK()

```advpl
// Sintaxe: SoftLock(cAlias)
cChave := GetCliente()
DbSelectArea("SA1")
DbSetOrder(1)
DbSeek(cChave)
If Found()
   SoftLock()
   lConfirma := AlteraSA1()
   If lConfirma
      RecLock("SA1", .F.)
      GravaSA1()
      MsUnLock()
   Endif
Endif
```

#### DBDELETE()

```advpl
// Sintaxe: DbDelete()
DbSelectArea("SA1")
DbSetOrder(1)
DbSeek("01" + "900001" + "01")
If Found()
   RecLock("SA1", .F.)
   DbDelete()
   MsUnLock()
Endif
```

#### DBUSEAREA()

```advpl
// Sintaxe: DbUseArea(lNovo, cDriver, cArquivo, cAlias, lCompartilhado, lSoLeitura)
DbUseArea(.T., "DBFCDX", "\SA1010.DBF", "SA1DBF", .T., .F.)
DbSelectArea("SA1DBF")
MsgInfo("A tabela SA1010.DBF possui: " + STRZERO(RecCount(), 6) + " registros.")
DbCloseArea()
```

#### DBCLOSEAREA()

```advpl
// Sintaxe: DbCloseArea()
DbSelectArea("SA1DBF")
DbCloseArea()
```

---

## 32. Funções Visuais para Aplicações

#### ALERT()

```advpl
// Sintaxe: Alert(cTexto)
Alert("Mensagem de alerta")
```

#### AVISO()

```advpl
// Sintaxe: AVISO(cTitulo, cTexto, aBotoes, nTamanho)
// Retorno: numérico indicando o botão selecionado
nBotao := AVISO("Título", "Texto do aviso", {"OK", "Cancelar"}, 1)
```

#### FORMBATCH()

```advpl
// Sintaxe: FORMBATCH(cTitulo, aTexto, aBotoes, bValid, nAltura, nLargura)
// aBotoes: array com estrutura {nTipo, lEnable, {|| Acao()}}
```

#### Funções MSG

```advpl
// Exibe mensagem de alerta (ícone de aviso):
MsgAlert(cTexto, cTitulo)

// Exibe mensagem informativa:
MsgInfo(cTexto, cTitulo)

// Exibe mensagem de parada/erro:
MsgStop(cTexto, cTitulo)

// Exibe pergunta Sim/Não; retorna .T. para Sim:
If MsgYesNo(cTexto, cTitulo)
   // usuário confirmou
Endif
```

---

## Referências Bibliográficas

- Gestão empresarial com ERP — Ernesto Haberkorn, 2006
- Apostila de Treinamento – ADVPL — Educação Corporativa TOTVS
- Apostila de Treinamento – Introdução à Programação — Educação Corporativa TOTVS
- Apostila de Treinamento – Boas Práticas de Programação — Inteligência Protheus e Fábrica de Software TOTVS
- Materiais diversos de colaboradores Microsiga Protheus / Colaboradores TOTVS
