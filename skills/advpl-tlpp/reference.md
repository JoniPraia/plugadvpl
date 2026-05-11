# TLPP – TOTVS Language Plus Productive

> **Versão do documento:** 1.0 — Março/2026
> **Baseado em:** Documentação oficial TOTVS TDN, GitHub TOTVS, Medium TOTVS Developers, fóruns e comunidade

---

## Índice

1. [O que é TLPP](#1-o-que-é-tlpp)
   - 1.1 [Histórico e Motivações](#11-histórico-e-motivações)
   - 1.2 [TLPP vs ADVPL — Comparativo Geral](#12-tlpp-vs-advpl--comparativo-geral)
   - 1.3 [Extensões de Arquivo](#13-extensões-de-arquivo)
   - 1.4 [tlppCore e tlpp.rpo](#14-tlppcore-e-tlpprpo)
2. [Sintaxe Nova e Tipos de Dados](#2-sintaxe-nova-e-tipos-de-dados)
   - 2.1 [Tipagem de Variáveis](#21-tipagem-de-variáveis)
   - 2.2 [Nomes Longos](#22-nomes-longos)
   - 2.3 [Parâmetros Nomeados](#23-parâmetros-nomeados)
   - 2.4 [Includes TLPP](#24-includes-tlpp)
   - 2.5 [Tabela de Tipos](#25-tabela-de-tipos)
3. [Namespaces](#3-namespaces)
   - 3.1 [Declaração de Namespace](#31-declaração-de-namespace)
   - 3.2 [Using Namespace](#32-using-namespace)
   - 3.3 [Namespace com Herança](#33-namespace-com-herança)
   - 3.4 [Convenções e Restrições](#34-convenções-e-restrições)
4. [Orientação a Objetos](#4-orientação-a-objetos)
   - 4.1 [Classes no ADVPL Clássico vs TLPP](#41-classes-no-advpl-clássico-vs-tlpp)
   - 4.2 [Declaração de Classe](#42-declaração-de-classe)
   - 4.3 [Modificadores de Acesso](#43-modificadores-de-acesso)
   - 4.4 [Construtores](#44-construtores)
   - 4.5 [Herança Simples](#45-herança-simples)
   - 4.6 [Interfaces](#46-interfaces)
   - 4.7 [Herança + Interface](#47-herança--interface)
   - 4.8 [Métodos e Propriedades Estáticos](#48-métodos-e-propriedades-estáticos)
   - 4.9 [Modificadores de Classe](#49-modificadores-de-classe)
   - 4.10 [Self e :: (dois pontos duplos)](#410-self-e--dois-pontos-duplos)
5. [Tratamento de Exceções](#5-tratamento-de-exceções)
   - 5.1 [Estrutura Try/Catch/Finally](#51-estrutura-trycatchfinally)
   - 5.2 [Throw — Lançamento Explícito](#52-throw--lançamento-explícito)
   - 5.3 [ErrorClass](#53-errorclass)
   - 5.4 [Boas Práticas de Exceções](#54-boas-práticas-de-exceções)
6. [Anotações (@Annotation)](#6-anotações-annotation)
   - 6.1 [O que são Annotations](#61-o-que-são-annotations)
   - 6.2 [Reflection e Annotation](#62-reflection-e-annotation)
   - 6.3 [Annotations em Funções e Métodos](#63-annotations-em-funções-e-métodos)
7. [JSON Nativo](#7-json-nativo)
   - 7.1 [Criação de JSON Literal](#71-criação-de-json-literal)
   - 7.2 [JsonObject — Serialização e Desserialização](#72-jsonobject--serialização-e-desserialização)
8. [REST com TLPP](#8-rest-com-tlpp)
   - 8.1 [Modelos de REST no Protheus](#81-modelos-de-rest-no-protheus)
   - 8.2 [Configuração do appserver.ini](#82-configuração-do-appserverini)
   - 8.3 [Includes Obrigatórios](#83-includes-obrigatórios)
   - 8.4 [Annotations REST](#84-annotations-rest)
   - 8.5 [Objeto oRest — Métodos Disponíveis](#85-objeto-orest--métodos-disponíveis)
   - 8.6 [Exemplos Completos de Endpoints](#86-exemplos-completos-de-endpoints)
   - 8.7 [REST em Classes TLPP](#87-rest-em-classes-tlpp)
   - 8.8 [Documentação Automática de APIs](#88-documentação-automática-de-apis)
   - 8.9 [FWRest — Consumindo APIs Externas](#89-fwrest--consumindo-apis-externas)
9. [Interoperabilidade com ADVPL](#9-interoperabilidade-com-advpl)
   - 9.1 [TLPP chamando ADVPL](#91-tlpp-chamando-advpl)
   - 9.2 [ADVPL chamando TLPP](#92-advpl-chamando-tlpp)
   - 9.3 [StaticCall — Descontinuação](#93-staticcall--descontinuação)
   - 9.4 [MVC no TLPP](#94-mvc-no-tlpp)
10. [DynCall — Importação de DLL](#10-dyncall--importação-de-dll)
11. [PROBAT — Testes Unitários](#11-probat--testes-unitários)
12. [TDS — TOTVS Developer Studio for VSCode](#12-tds--totvs-developer-studio-for-vscode)
    - 12.1 [Instalação e Configuração](#121-instalação-e-configuração)
    - 12.2 [Compilação](#122-compilação)
    - 12.3 [Deploy e Patches](#123-deploy-e-patches)
    - 12.4 [TLPP Tools](#124-tlpp-tools)
13. [Migração de ADVPL para TLPP](#13-migração-de-advpl-para-tlpp)
    - 13.1 [Estratégia de Migração](#131-estratégia-de-migração)
    - 13.2 [Armadilhas Comuns](#132-armadilhas-comuns)
14. [Boas Práticas TLPP](#14-boas-práticas-tlpp)
    - 14.1 [Convenções de Nomenclatura](#141-convenções-de-nomenclatura)
    - 14.2 [Organização de Código](#142-organização-de-código)
    - 14.3 [Princípios SOLID em TLPP](#143-princípios-solid-em-tlpp)
15. [Exemplos de Código Completos](#15-exemplos-de-código-completos)
    - 15.1 [Hello World em TLPP](#151-hello-world-em-tlpp)
    - 15.2 [Classe Completa com Herança](#152-classe-completa-com-herança)
    - 15.3 [API REST CRUD Completa](#153-api-rest-crud-completa)
    - 15.4 [Tratamento de Erro Completo](#154-tratamento-de-erro-completo)
16. [Referências e Recursos](#16-referências-e-recursos)

---

## 1. O que é TLPP

**TLPP** (TOTVS Language Plus Productive, também referida como **TL++** ou **TOTVS Language Plus Plus**) é a evolução moderna da linguagem **ADVPL** (Advanced Protheus Language), desenvolvida pela TOTVS S/A para o ecossistema **ERP Protheus**.

Enquanto o ADVPL foi lançado em 1999 e permaneceu como a linguagem central do Protheus por duas décadas (com mais de **30 milhões de linhas de código** e mais de **90 módulos**), o TLPP foi concebido para modernizar o desenvolvimento sem abandonar o vasto legado existente.

### 1.1 Histórico e Motivações

| Ano | Marco |
|-----|-------|
| 1999 | Lançamento do ADVPL (Advanced Protheus Language) |
| ~2016–2018 | Desenvolvimento interno da linguagem TL++ na TOTVS |
| 2019 | Anúncio público do TL++ / TLPP |
| 17.3.0.0 | Liberação do recurso de **Namespace** para o TLPP |
| 12.1.2410 (2024) | Suporte completo a **MVC no TLPP** no framework Protheus |

**Motivações principais:**

- Eliminar o limite de **10 caracteres** para nomes de identificadores (variáveis, funções, classes)
- Introduzir **tipagem forte** com verificação em tempo de compilação
- Suportar **namespaces** para organizar grandes bases de código
- Modernizar a **orientação a objetos** com modificadores de acesso reais (`private`, `protected`, `public`)
- Oferecer **tratamento de exceções** com `try/catch/finally/throw`
- Criar **APIs REST** de forma declarativa via annotations (`@Get`, `@Post`, etc.)
- Proporcionar **interoperabilidade bidirecional** com o ADVPL existente

### 1.2 TLPP vs ADVPL — Comparativo Geral

| Característica | ADVPL | TLPP |
|---|---|---|
| Extensão de arquivo | `.prw`, `.prg`, `.prx` | `.tlpp` |
| Extensão de include | `.ch` | `.th` (aceita `.ch` também) |
| Tamanho máximo de identificadores | 10 caracteres | 255 caracteres |
| Tipagem de variáveis | Dinâmica (sem verificação em compilação) | Forte (erro em compilação) |
| Namespaces | Não suportado | Suportado |
| Parâmetros nomeados | Não | Sim |
| Modificadores de acesso (OOP) | Não (tudo público) | `public`, `private`, `protected` |
| Interfaces | Não | Sim (`interface … endinterface`) |
| Métodos estáticos | Não | Sim (`static method`) |
| Try/Catch/Finally | Não | Sim |
| Throw | Indireto (via UserException) | Direto (`throw objeto`) |
| Annotations (`@`) | Não | Sim |
| JSON literal nativo | Não | Sim |
| Sobrecarga de operadores | Não | Sim |
| StaticCall | Sim | Não (descontinuado) |
| REST com annotations | Não | Sim |
| Testes unitários (PROBAT) | Via tlppCore | Via tlppCore nativo |
| DynCall (importar DLL) | Não | Sim |

### 1.3 Extensões de Arquivo

```
Fonte ADVPL:  nome.prw  /  nome.prg  /  nome.prx
Fonte TLPP:   nome.tlpp

Include ADVPL: nome.ch
Include TLPP:  nome.th   (também aceita .ch)
```

A renomeação de um `.prw` para `.tlpp` **não** faz o código se tornar automaticamente TLPP — é necessário adaptar o código às regras da linguagem (tipagem, nomes longos, ausência de staticcall, etc.).

### 1.4 tlppCore e tlpp.rpo

O **tlppCore** é o módulo central do ecossistema TLPP. Ele é distribuído como `tlpp.rpo` junto com o AppServer e fornece:

- Motor de REST nativo (com annotations)
- Motor de testes unitários (**PROBAT**)
- Suporte a **DynCall** (importação de DLLs)
- Expressões regulares
- Motor de documentação automática de APIs
- Recursos de Reflection e Annotation

Os **includes** do TLPP são extraídos a partir do `tlpp.rpo` e devem ser copiados para o diretório de includes do projeto.

> **Importante:** Sempre que atualizar o binário (AppServer) ou o `tlpp.rpo`, reextraia os includes para garantir compatibilidade.

---

## 2. Sintaxe Nova e Tipos de Dados

### 2.1 Tipagem de Variáveis

No TLPP, as variáveis podem (e devem) ser declaradas com tipo explícito usando a cláusula `as`:

```tlpp
Local cNome      as Character
Local nValor     as Numeric
Local lAtivo     as Logical
Local dVencto    as Date
Local oCliente   as Object
Local aItens     as Array
Local bBloco     as Block
```

A tipagem gera **erros em tempo de compilação** (não somente warnings), prevenindo erros silenciosos que no ADVPL só apareciam em runtime.

**Comparativo de declaração:**

```advpl
// ADVPL clássico — sem tipagem
Local cNome
Local nValor
cNome  := "João"
nValor := 100
```

```tlpp
// TLPP — com tipagem forte
Local cNome  := "João"  as Character
Local nValor := 100     as Numeric
```

### 2.2 Nomes Longos

O TLPP expande o limite de identificadores de **10** para **255 caracteres**:

```tlpp
#include "protheus.ch"

user function essaEhUmaFuncaoEmTLPPComNomeLongo()
  Local cTestandoNomesLongosEmTLPP as Character
  cTestandoNomesLongosEmTLPP := "Testando nomes longos em TLPP"
  ConOut(cTestandoNomesLongosEmTLPP)
Return nil
```

> **Atenção:** Uma função chamada `myFunction001()` no ADVPL era armazenada como `myFunction` (10 chars). Em TLPP, será armazenada como `myFunction001`. Código existente que chama `myFunction()` quebrará ao migrar para TLPP.

### 2.3 Parâmetros Nomeados

O TLPP suporta **parâmetros nomeados**, permitindo chamar funções especificando o nome do parâmetro:

```tlpp
namespace meu.exemplo

function criarUsuario(cNome as Character, nIdade as Numeric, lAtivo as Logical)
  ConOut("Nome: " + cNome)
  ConOut("Idade: " + cValToChar(nIdade))
Return

// Chamada com parâmetros nomeados
meu.exemplo.criarUsuario(cNome: "Ana", nIdade: 30, lAtivo: .T.)
```

### 2.4 Includes TLPP

A ordem correta de inclusão dos headers é **crítica**:

```tlpp
// CORRETO: tlpp-core.th ANTES dos includes do Protheus
#include "tlpp-core.th"
#include "tlpp-object.th"   // somente OOP
#include "tlpp-rest.th"     // somente REST
#include "totvs.ch"
#include "protheus.ch"
```

```tlpp
// INCORRETO: sem o include correto, modificadores de acesso não funcionam
#include "protheus.ch"
// Faltando tlpp-core.th — private/public/protected não terão efeito
```

| Include | Finalidade |
|---|---|
| `tlpp-core.th` | Todos os recursos da linguagem TLPP (recomendado) |
| `tlpp-object.th` | Somente recursos de OOP (classes, interfaces, etc.) |
| `tlpp-rest.th` | Annotations REST (`@Get`, `@Post`, etc.) |
| `totvs.ch` | Defines gerais da TOTVS |
| `protheus.ch` | Defines do Protheus |

### 2.5 Tabela de Tipos

| Tipo TLPP | Equivalente ADVPL | Descrição |
|---|---|---|
| `Character` | `string` / `character` | Cadeia de caracteres |
| `Numeric` | `numeric` | Número (inteiro ou decimal) |
| `Logical` | `boolean` | Verdadeiro (`.T.`) ou Falso (`.F.`) |
| `Date` | `date` | Data |
| `Object` | `object` | Referência a objeto |
| `Array` | `array` | Vetor |
| `Block` | `block` / `codeblock` | Bloco de código |
| `Variant` | *(implícito)* | Tipo dinâmico (sem tipagem) |

> **Nota de migração:** No ADVPL, o tipo era `string`; no TLPP, o equivalente é `Character`. O uso de `as string` pode causar erro de compilação no TLPP.

---

## 3. Namespaces

O recurso de **Namespace** foi liberado na versão **17.3.0.0** do TLPP e permite organizar o código em domínios lógicos, evitando colisões de nomes e facilitando a modularização.

### 3.1 Declaração de Namespace

A declaração de namespace é feita no **início do arquivo** `.tlpp`:

```tlpp
#include "tlpp-core.th"

namespace meu.exemplo

user function U_Ola_Mundo_em_TLPP()
  ConOut("Olá Mundo — meu primeiro programa em TLPP")
Return
```

Para executar via SmartClient ou console, usa-se o nome completo:

```
meu.exemplo.U_Ola_Mundo_em_TLPP
```

**Namespace com classe:**

```tlpp
#include "tlpp-core.th"
namespace exemplo

Class ClassWithNamespace
  Public Method new()
  Data dataI as Character
EndClass

Method new() Class ClassWithNamespace
  Local cFrase := "exemplo frase TLPP" as Character
  ConOut(cFrase)
Return Self
```

### 3.2 Using Namespace

Para consumir funções ou classes de outro namespace sem repetir o prefixo:

```tlpp
// Arquivo: exemplo1.tlpp
#include "tlpp-core.th"
namespace exemplo

User Function testeNamespace()
  Local nNumber := 2 as Numeric
  ConOut(nNumber)
  u_testeNamespace2()
Return

User Function testeNamespace2()
  ConOut("testeNamespace2")
Return
```

```tlpp
// Arquivo: exemplo2.tlpp — usando "using namespace"
#include "tlpp-core.th"
using namespace exemplo

User Function exemplo3()
  // Chamará a função testeNamespace do namespace "exemplo"
  u_testeNamespace()
Return
```

**Chamando de ADVPL sem `using namespace`:**

```advpl
// Arquivo ADVPL (.prw) — prefixo completo
User Function nameEX2()
  exemplo.u_testeNamespace()
Return
```

### 3.3 Namespace com Herança

Ao herdar uma classe que está em um namespace, é preciso usar o **nome completamente qualificado** na declaração `From`:

```tlpp
// integracao.tlpp
namespace MeuNamespace

Class Integracao
  Method New()
  Method Teste()
EndClass

Method New() Class Integracao
Return Self

Method Teste() Class Integracao
  ConOut("Método Teste da classe Integracao")
Return
```

```tlpp
// cliente.tlpp — CORRETO: nome qualificado no From
namespace MeuNamespace

Class Cliente From MeuNamespace.Integracao
  Method New()
EndClass

Method New() Class Cliente
  _Super:New()
Return Self
```

```tlpp
// cliente.tlpp — INCORRETO: sem qualificação o método não é encontrado
Class Cliente From Integracao   // Não funciona corretamente
  Method New()
EndClass
```

### 3.4 Convenções e Restrições

- **Nomes em minúsculo**, separados por ponto, sem underscore
- **Customizações de clientes** devem iniciar com `custom`:
  - `custom.cadastros.cliente`
  - `custom.relatorios.faturamento`
- Namespaces iniciados com **`tlpp`** ou **`core`** são **reservados** para uso interno da TOTVS — compilação será bloqueada
- Separador: ponto (`.`) para hierarquia
- Idioma recomendado: **inglês** (para internacionalização)

**Exemplos válidos:**

```
backoffice.fiscal.nfe
health.planos.consulta
custom.ma030inc
custom.cadastros.meus
```

---

## 4. Orientação a Objetos

O TLPP representa um **grande salto** na orientação a objetos em relação ao ADVPL clássico, introduzindo modificadores de acesso reais, interfaces, métodos estáticos e sobrecarga de operadores.

### 4.1 Classes no ADVPL Clássico vs TLPP

**ADVPL clássico:**

```advpl
// Arquivo: MinhaClasse.prw
Class MinhaClasse
  Data cNome
  Data nIdade

  Method New()    Constructor
  Method GetNome()
  Method SetNome()
EndClass

Method New() Class MinhaClasse
  ::cNome  := ""
  ::nIdade := 0
Return Self

Method GetNome() Class MinhaClasse
Return ::cNome

Method SetNome(cNome) Class MinhaClasse
  ::cNome := cNome
Return
```

**TLPP moderno:**

```tlpp
// Arquivo: MinhaClasse.tlpp
#include "tlpp-core.th"

namespace meu.dominio

Class MinhaClasse
  Private Data cNome  as Character
  Private Data nIdade as Numeric

  Public Method New()    Constructor
  Public Method GetNome() as Character
  Public Method SetNome(cNome as Character)
EndClass

Method New() Class MinhaClasse
  ::cNome  := ""
  ::nIdade := 0
Return Self

Method GetNome() Class MinhaClasse as Character
Return ::cNome

Method SetNome(cNome as Character) Class MinhaClasse
  ::cNome := cNome
Return
```

### 4.2 Declaração de Classe

Estrutura geral de uma classe em TLPP:

```tlpp
#include "tlpp-core.th"

namespace minha.aplicacao

Class NomeDaClasse [From ClassePai] [Implements Interface1[, Interface2]]
  [modificador] Data nomePropriedade [as Tipo] [init ValorPadrao]
  [modificador] Method NomeMetodo([params]) [as TipoRetorno]
  [modificador] static Method NomeMetodoEstatico()
EndClass

Method NomeMetodo([params]) Class NomeDaClasse [as TipoRetorno]
  // Implementação
Return [valor]
```

### 4.3 Modificadores de Acesso

| Modificador | Propriedades | Métodos | Comportamento |
|---|---|---|---|
| `Public` | Sim | Sim | Acessível de qualquer contexto |
| `Private` | Sim | Sim | Acessível apenas dentro da própria classe |
| `Protected` | Sim | Sim | Acessível na classe e em classes filhas (herança) |
| `Static` | Sim | Sim | Pertence à classe, não à instância |
| `Final` | Sim | Sim | Não pode ser sobrescrito em herança |
| `Abstract` | Apenas classe | Não | Classe não pode ser instanciada diretamente |

```tlpp
#include "tlpp-core.th"

Class Conta
  Public    Data cTitular  as Character
  Protected Data nSaldo    as Numeric
  Private   Data cSenha    as Character

  Public  Method New(cTitular as Character, nSaldoInicial as Numeric)
  Public  Method Depositar(nValor as Numeric)
  Public  Method GetSaldo() as Numeric
  Private Method ValidarSenha(cSenhaInformada as Character) as Logical
EndClass

Method New(cTitular as Character, nSaldoInicial as Numeric) Class Conta
  ::cTitular := cTitular
  ::nSaldo   := nSaldoInicial
  ::cSenha   := "1234"
Return Self

Method Depositar(nValor as Numeric) Class Conta
  If nValor > 0
    ::nSaldo += nValor
  EndIf
Return

Method GetSaldo() Class Conta as Numeric
Return ::nSaldo

Method ValidarSenha(cSenhaInformada as Character) Class Conta as Logical
Return (::cSenha == cSenhaInformada)
```

### 4.4 Construtores

O construtor é definido com a cláusula `Constructor` e deve retornar `Self`:

```tlpp
#include "tlpp-core.th"

Class Produto
  Public Data cCodigo     as Character
  Public Data cDescricao  as Character
  Public Data nPreco      as Numeric

  Public Method New(cCodigo as Character, cDesc as Character, nPreco as Numeric) Constructor
EndClass

Method New(cCodigo as Character, cDesc as Character, nPreco as Numeric) Class Produto
  ::cCodigo    := cCodigo
  ::cDescricao := cDesc
  ::nPreco     := nPreco
Return Self

// Uso:
// Local oProduto := Produto():New("P001", "Caneta Azul", 2.50)
```

### 4.5 Herança Simples

TLPP suporta **herança simples** (uma classe filha de uma única classe pai):

```tlpp
#include "tlpp-core.th"

// Classe Pai
Class Animal
  Protected Data cNome as Character
  Protected Data cSom  as Character

  Public Method New(cNome as Character) Constructor
  Public Method EmitirSom()
  Public Method GetNome() as Character
EndClass

Method New(cNome as Character) Class Animal
  ::cNome := cNome
  ::cSom  := "..."
Return Self

Method EmitirSom() Class Animal
  ConOut(::cNome + " faz: " + ::cSom)
Return

Method GetNome() Class Animal as Character
Return ::cNome

// Classe Filha
Class Cachorro From Animal
  Public Method New(cNome as Character) Constructor
  Public Method EmitirSom()   // Sobrescrevendo o método do pai
  Public Method Buscar()
EndClass

Method New(cNome as Character) Class Cachorro
  _Super:New(cNome)   // Chama o construtor do pai
  ::cSom := "Au Au"
Return Self

Method EmitirSom() Class Cachorro
  ConOut("[CACHORRO] " + ::cNome + " late: " + ::cSom)
Return

Method Buscar() Class Cachorro
  ConOut(::cNome + " está buscando a bola!")
Return

// Uso:
// Local oCao := Cachorro():New("Rex")
// oCao:EmitirSom()   -> [CACHORRO] Rex late: Au Au
// oCao:Buscar()      -> Rex está buscando a bola!
// oCao:GetNome()     -> Rex  (herdado do pai)
```

**Herança multinível (`_Super` recursivo):**

```tlpp
Class Apavo      // Avô
  Public Method New() Constructor
  Public Method FalarAvos()
EndClass

Class Appai From Apavo   // Pai herda Avô
  Public Method New() Constructor
  Public Method FalarPai()
EndClass

Class Apneta From Appai  // Neta herda Pai (que herda Avô)
  Public Method New() Constructor
EndClass

// A classe Apneta pode chamar FalarAvos() — busca recursiva automática
```

### 4.6 Interfaces

Interfaces definem contratos que as classes devem implementar:

```tlpp
#include "tlpp-core.th"

Interface ICalculavel
  Public Method calcular(nA as Numeric, nB as Numeric) as Numeric
EndInterface

Interface IExibivel
  Public Method exibir()
EndInterface

Class Soma Implements ICalculavel
  Public Method New() Constructor
  Public Method calcular(nA as Numeric, nB as Numeric) as Numeric
EndClass

Method New() Class Soma
Return Self

Method calcular(nA as Numeric, nB as Numeric) Class Soma as Numeric
Return nA + nB
```

> **Herança múltipla** não é permitida em TLPP. Porém, é possível implementar **múltiplas interfaces**:

```tlpp
Class MinhaClasse From ClassePai Implements Interface1, Interface2
  // ...
EndClass
```

### 4.7 Herança + Interface

Combinando herança simples com implementação de múltiplas interfaces (similar ao modelo Java):

```tlpp
#include "tlpp-core.th"

// Classe Pai
Class TlppParent
  Public Method New() Constructor
  Public Method create()
EndClass

Method New() Class TlppParent
Return Self

Method create() Class TlppParent
  ConOut("TlppParent::create() executado")
Return

// Interface 1
Interface TlppInterface
  Public Method run()
EndInterface

// Interface 2
Interface TlppInterface2
  Public Method run2()
EndInterface

// Classe filha que herda e implementa
Class TlppChild From TlppParent Implements TlppInterface, TlppInterface2
  Public Method New()     Constructor
  Public Method run()
  Public Method run2()
EndClass

Method New() Class TlppChild
  _Super:New()    // Chama construtor do pai
  ::Create()      // Chama método herdado do pai
Return Self

Method run() Class TlppChild
  ConOut("TlppChild::run() implementando TlppInterface")
Return

Method run2() Class TlppChild
  ConOut("TlppChild::run2() implementando TlppInterface2")
Return
```

### 4.8 Métodos e Propriedades Estáticos

Membros `static` pertencem à **classe**, não à instância — podem ser acessados sem instanciar o objeto:

```tlpp
#include "tlpp-core.th"

Class Contador
  Static Data nTotal as Numeric init 0   // Compartilhado entre instâncias

  Public Method New()          Constructor
  Static Method incrementar()
  Static Method getTotal()     as Numeric
EndClass

Method New() Class Contador
  Contador.incrementar()
Return Self

Static Method incrementar() Class Contador
  Contador.nTotal++
Return

Static Method getTotal() Class Contador as Numeric
Return Contador.nTotal

// Uso — sem instanciar:
// Contador.incrementar()
// ConOut(cValToChar(Contador.getTotal()))
```

### 4.9 Modificadores de Classe

| Modificador | Aplicável a | Efeito |
|---|---|---|
| `final` | Classe, método | Impede herança da classe / sobrescrita do método |
| `abstract` | Classe | Impede instanciação direta (apenas para herança) |
| `static` | Método, propriedade | Membro de classe, não de instância |

```tlpp
// Classe final — não pode ser herdada
final Class SenhaMestre
  Private Data cSenha as Character
  Public Method New() Constructor
EndClass

// Classe abstrata — não pode ser instanciada diretamente
abstract Class FormaGeometrica
  Public Method New() Constructor
  Public Method calcularArea() as Numeric  // deve ser implementado nas filhas
EndClass
```

### 4.10 Self e :: (dois pontos duplos)

Dentro dos métodos, `self` e `::` são equivalentes — `::` é um `#translate` de compilação que é convertido em `self:`:

```tlpp
Method SetNome(cNome as Character) Class Pessoa
  // As duas formas são equivalentes:
  Self:cNome := cNome
  ::cNome    := cNome   // Convenção preferida
Return
```

> `::` é a **convenção mais usual** na comunidade TOTVS/TLPP.

---

## 5. Tratamento de Exceções

O `try/catch/finally/throw` é um dos recursos **exclusivos do TLPP** — não está disponível no ADVPL clássico (embora seja possível lançar um `throw` de dentro do ADVPL para ser capturado no TLPP).

### 5.1 Estrutura Try/Catch/Finally

```tlpp
#include "tlpp-core.th"
#include "protheus.ch"

User Function exemploTryCatch()
  Local oError as Object

  TRY
    // Código que pode gerar exceção
    chamadaQueNaoExiste()
    ConOut("Esta linha NÃO deve executar se houver erro")

  CATCH oError
    // Tratamento do erro — oError é instância de ErrorClass
    ConOut("Erro capturado: " + oError:description)
    ConOut("Código: "         + cValToChar(oError:genCode))

  FINALLY
    // Sempre executado — ideal para liberar recursos
    ConOut("Bloco finally: executado sempre, com ou sem erro")

  ENDTRY
Return
```

**Estrutura resumida:**

```
TRY
  [código que pode falhar]
CATCH [variável]
  [tratamento do erro]
FINALLY
  [sempre executado — opcional]
ENDTRY
```

### 5.2 Throw — Lançamento Explícito

```tlpp
#include "tlpp-core.th"
#include "protheus.ch"

function u_lancarErroCustom()
  Local oErro := ErrorClass():New()
  oErro:genCode    := 9001
  oErro:description := "Valor inválido informado para o parâmetro nQuantidade"
  oErro:operation  := "u_lancarErroCustom"

  throw oErro  // Lança a exceção
  ConOut("Esta linha NUNCA executa após o throw")
Return

User Function TryCatch_Throw()
  TRY
    u_lancarErroCustom()
  CATCH oError
    ConOut("Erro capturado pelo throw: " + oError:description)
  ENDTRY
Return
```

**Macroexecução protegida por try/catch:**

```tlpp
User Function TryCatch_Macro()
  Local oError  as Object
  Local xResult
  Local cTexto := "If(XPTO->CAMPO$'N')" as Character

  TRY
    xResult := &cTexto   // Macroexecução — pode falhar
  CATCH oError
    ConOut("Erro na macroexecução: " + oError:description)
  ENDTRY
Return
```

### 5.3 ErrorClass

O objeto `oError` capturado no `catch` é uma instância de `ErrorClass()` com as seguintes propriedades principais:

| Propriedade | Tipo | Descrição |
|---|---|---|
| `description` | Character | Mensagem descritiva do erro |
| `genCode` | Numeric | Código numérico do erro |
| `operation` | Character | Operação que gerou o erro |
| `subCode` | Numeric | Subcódigo do erro |
| `fileName` | Character | Nome do arquivo fonte |
| `lineNumber` | Numeric | Linha do código onde ocorreu |
| `canDefault` | Logical | Se pode usar tratamento padrão |
| `canRetry` | Logical | Se pode tentar novamente |

```tlpp
User Function exemploErrorClass()
  TRY
    UserException("Testando a estrutura TryCatch")

  CATCH e
    ConOut("description: " + e:description)
    ConOut("genCode: "     + cValToChar(e:genCode))
    ConOut("operation: "   + e:operation)

  FINALLY
    ConOut("finally — limpar recursos aqui")

  ENDTRY
Return
```

### 5.4 Boas Práticas de Exceções

- **Não use try/catch global** — aplique por função ou contexto específico
- **Ordene os catch do mais específico ao mais genérico**
- Use o `finally` para **liberar recursos** (fechar conexões, arquivos, áreas de banco)
- **Não engula erros silenciosamente** — sempre logue ou re-lance
- Use `throw` explícito para **validações de negócio** com objetos `ErrorClass` customizados

```tlpp
// Boa prática: finally para limpeza de recursos
User Function processarArquivo(cArquivo as Character)
  Local nHandle as Numeric
  nHandle := FOpen(cArquivo, 0)

  TRY
    // processar o arquivo
    processarLinhas(nHandle)
  CATCH oError
    ConOut("Erro ao processar " + cArquivo + ": " + oError:description)
  FINALLY
    If nHandle > 0
      FClose(nHandle)  // Sempre fechado, mesmo com erro
    EndIf
  ENDTRY
Return
```

---

## 6. Anotações (@Annotation)

### 6.1 O que são Annotations

As **Annotations** (anotações) são metadados declarativos adicionados a funções, métodos ou classes para modificar ou configurar o comportamento em tempo de execução. No TLPP, são escritas com o prefixo `@` antes da declaração.

As annotations são especialmente utilizadas para:
- Mapeamento de endpoints REST (`@Get`, `@Post`, `@Put`, `@Delete`, `@Patch`)
- Testes unitários com PROBAT (`@test`)
- Marcadores de documentação

### 6.2 Reflection e Annotation

O **Reflection** é o mecanismo que permite ao TLPP inspecionar classes, métodos e annotations em tempo de execução. Isso é o que possibilita o motor REST do tlppCore "descobrir" automaticamente os endpoints definidos por `@Get`, `@Post`, etc., sem necessidade de registro manual.

```tlpp
// Exemplo conceitual — buscar classes por annotation
using namespace tlpp.core.reflection

Local aClasses := Reflection.getClassesByAnnotation("RestEndpoint", "minha.api")
```

### 6.3 Annotations em Funções e Métodos

**Em User Functions:**

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Get("/api/v1/produtos")
User Function listarProdutos()
  // oRest disponível automaticamente pelo motor REST
  oRest:setKeyHeaderResponse("Content-Type", "application/json")
  oRest:setResponse('{"produtos": []}')
Return .T.
```

**Em métodos de classe — annotation ANTES da declaração na definição da classe:**

```tlpp
Class PedidoController
  Public Method New()
  @Get("/api/v1/pedidos")
  Public Method listarPedidos()
  @Post("/api/v1/pedidos")
  Public Method criarPedido()
EndClass

Method New() Class PedidoController
Return Self

Method listarPedidos() Class PedidoController
  // implementação
Return .T.

Method criarPedido() Class PedidoController
  // implementação
Return .T.
```

> **Atenção:** A annotation deve ser posicionada **dentro da definição da classe** (antes da declaração do método), não após o `EndClass`. Colocar após `EndClass` pode resultar em "Not Found 404".

---

## 7. JSON Nativo

### 7.1 Criação de JSON Literal

O TLPP suporta criação de objetos JSON com sintaxe literal (sem instanciar `JsonObject`):

```tlpp
#include "tlpp-core.th"
#include "protheus.ch"

User Function exemploJsonNativo()
  Local jJson as Object

  // Sintaxe literal JSON — exclusiva do TLPP
  jJson := { "id": "xisto", "values": { "name": "Daniel", "obs": "DEV" } }

  ConOut( jJson["id"] )              // -> xisto
  ConOut( jJson["values"]["name"] )  // -> Daniel
Return
```

### 7.2 JsonObject — Serialização e Desserialização

```tlpp
#include "protheus.ch"
#include "tlpp-core.th"

User Function exemploJsonObject()
  Local oJson    as Object
  Local oRegistro as Object
  Local aItens    as Array
  Local cParseResult as Character
  Local cJsonStr as Character

  // Desserializar JSON recebido
  cJsonStr := '{"codigo": "001", "nome": "Produto A", "preco": 25.90}'
  oJson := JsonObject():New()
  cParseResult := oJson:fromJson(cJsonStr)

  ConOut("Código: " + oJson:GetJsonText("codigo"))
  ConOut("Nome: "   + oJson:GetJsonText("nome"))

  // Serializar objeto para JSON
  oRegistro := JsonObject():New()
  oRegistro["codigo"]    := "002"
  oRegistro["descricao"] := "Produto B"
  oRegistro["ativo"]     := .T.

  ConOut("JSON: " + oRegistro:toJSON())
  // -> {"codigo":"002","descricao":"Produto B","ativo":true}

  // JSON com array aninhado
  Local cJsonAninhado := '{"data": [{"id": "1","nome": "Ana"},{"id": "2","nome": "Bruno"}]}'
  Local oJsonOuter := JsonObject():New()
  oJsonOuter:fromJson(cJsonAninhado)

  Local oArray := oJsonOuter:GetJsonObject("data")
  ConOut("Primeiro: " + oArray[1]:GetJsonText("nome"))  // -> Ana
  ConOut("Segundo: "  + oArray[2]:GetJsonText("nome"))  // -> Bruno

  FreeObj(oJson)
  FreeObj(oRegistro)
  FreeObj(oJsonOuter)
Return
```

| Método | Descrição |
|---|---|
| `JsonObject():New()` | Cria nova instância |
| `:fromJson(cString)` | Parse de string JSON para objeto |
| `:toJSON()` | Serializa objeto para string JSON |
| `:GetNames()` | Retorna array com nomes das propriedades |
| `:GetJsonObject(cChave)` | Retorna objeto filho de uma propriedade |
| `:GetJsonText(cChave)` | Retorna valor textual de uma propriedade |
| `FwJsonSerialize(aArray)` | Serializa array de objetos JSON |

---

## 8. REST com TLPP

### 8.1 Modelos de REST no Protheus

Existem dois modelos principais de REST no ecossistema Protheus:

| Modelo | Tecnologia | Configuração | Annotations | Performance |
|---|---|---|---|---|
| REST ADVPL (legado) | `WSRESTFUL`, `FWRest` | Seção `[HTTPV11]` no INI, `HTTP_START` via job | Não | Baseline |
| REST TLPP (moderno) | `tlppCore` nativo | Seção `[HTTPSERVER]` no INI | Sim | Até 3x mais rápido |

O REST TLPP nativo oferece **até 3x mais performance** em relação ao modelo ADVPL, graças à substituição das camadas de `accept` e de controle.

### 8.2 Configuração do appserver.ini

```ini
[HTTPSERVER]
Enable=1
Servers=HTTP_REST

[HTTP_REST]
hostname=localhost
port=8099
locations=HTTP_ROOT

[HTTP_ROOT]
Path=/
RootPath=root/web
ThreadPool=THREAD_POOL

[THREAD_POOL]
Environment=PRODUCAO
MinThreads=1
MaxThreads=10
GrowthFactor=2
InactiveTimeout=30000
AcceptTimeout=10000
```

| Chave | Descrição |
|---|---|
| `Enable=1` | Ativa o servidor HTTP ao iniciar o AppServer |
| `Servers=` | Lista de servidores a ativar (nomes das seções abaixo) |
| `port=` | Porta TCP do servidor REST |
| `hostname=` | Nome/IP do host |
| `ThreadPool=` | Nome da seção que configura o pool de threads |
| `Environment=` | Nome do Environment (seção do INI do Protheus) |
| `MinThreads=` | Mínimo de threads ativas para atender requisições |
| `MaxThreads=` | Máximo de threads simultâneas |

### 8.3 Includes Obrigatórios

```tlpp
#include "tlpp-core.th"    // Sempre necessário
#include "tlpp-rest.th"    // Para annotations REST
#include "protheus.ch"     // Para funções do Protheus
```

### 8.4 Annotations REST

| Annotation | Verbo HTTP | Uso Típico |
|---|---|---|
| `@Get(path)` | GET | Consultar / listar recursos |
| `@Post(path)` | POST | Criar novos recursos |
| `@Put(path)` | PUT | Atualizar recursos (completo) |
| `@Delete(path)` | DELETE | Remover recursos |
| `@Patch(path)` | PATCH | Atualizar recursos (parcial) |

**Sintaxe das annotations REST:**

```tlpp
// Path simples
@Get("/api/v1/clientes")

// Path com parâmetro de rota
@Get("/api/v1/clientes/:codigo")

// Path com múltiplos parâmetros
@Put("/api/v1/pedidos/:empresa/:filial/:pedido")

// Path com description (para documentação automática)
@Get(endpoint="/api/v1/produtos", description="Lista todos os produtos ativos")
```

### 8.5 Objeto oRest — Métodos Disponíveis

O objeto `oRest` é disponibilizado **automaticamente** pelo motor REST do tlppCore para toda função ou método anotado com `@Get`, `@Post`, etc.

**Leitura de parâmetros:**

| Método | Retorno | Descrição |
|---|---|---|
| `oRest:GetBodyRequest()` | `Character` | Corpo (body) da requisição como string |
| `oRest:getQueryRequest()` | `JsonObject` | Parâmetros de query string (`?chave=valor`) |
| `oRest:getPathParamsRequest()` | `JsonObject` | Parâmetros de rota (`:id`, `:codigo`) |
| `oRest:getHeaderRequest()` | `JsonObject` | Headers da requisição |

**Escrita da resposta:**

| Método | Parâmetros | Descrição |
|---|---|---|
| `oRest:setResponse(cJson)` | `Character` | Define o corpo da resposta |
| `oRest:setKeyHeaderResponse(cChave, cValor)` | `Character, Character` | Adiciona header à resposta |
| `oRest:setStatusCode(nCode)` | `Numeric` | Define código HTTP de status |
| `oRest:setFault(cMensagem)` | `Character` | Retorna erro 500 com mensagem |

> **Atenção:** Os objetos JSON retornados por `oRest:getQueryRequest()` e similares são **referências** ao objeto interno do motor REST. **Não os modifique diretamente** — use os valores lidos para criar cópias locais.

### 8.6 Exemplos Completos de Endpoints

**@Get com QueryString:**

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"
#include "protheus.ch"

@Get("/api/v1/clientes")
User Function getClientes()
  Local jQueryString as Object
  Local cCodCli      as Character
  Local oResponse    as Object
  Local aDados       as Array
  Local cQuery       as Character

  RPCSetEnv("01", "0101001")
  oRest:setKeyHeaderResponse("Content-Type", "application/json")

  jQueryString := oRest:getQueryRequest()

  If jQueryString <> Nil
    cCodCli := jQueryString:GetJsonText("codigo")
    If cCodCli == "null"
      cCodCli := ""
    EndIf
  EndIf

  cQuery := "SELECT A1_COD, A1_NOME, A1_CGC FROM " + RetSQLName("SA1") + " SA1 "
  cQuery += "WHERE D_E_L_E_T_ = ' ' AND A1_FILIAL = '" + xFilial("SA1") + "'"
  If !empty(cCodCli)
    cQuery += " AND A1_COD = '" + cCodCli + "'"
  EndIf

  dbUseArea(.T., "TOPCONN", TCGenQry(,, cQuery), "QTMPSA1", .T., .T.)
  aDados := {}
  While QTMPSA1->(!EOF())
    Local oItem := JsonObject():New()
    oItem["codigo"] := AllTrim(QTMPSA1->A1_COD)
    oItem["nome"]   := AllTrim(QTMPSA1->A1_NOME)
    oItem["cnpj"]   := AllTrim(QTMPSA1->A1_CGC)
    aAdd(aDados, oItem)
    QTMPSA1->(dbSkip())
  EndDo
  dbCloseArea()

  oResponse := JsonObject():New()
  oResponse["clientes"] := aDados
  oResponse["total"]    := Len(aDados)

  oRest:setResponse(oResponse:toJSON())
  rpcClearEnv()
Return .T.
```

**@Get com PathParam:**

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Get("/api/v1/clientes/:codigo")
User Function getClientePorCodigo()
  Local jPath   as Object
  Local cCodigo as Character
  Local cData   as Character

  jPath := oRest:getPathParamsRequest()

  If jPath <> Nil
    cCodigo := jPath["codigo"]
    If ValType(cCodigo) == "U"
      cCodigo := ""
    EndIf
  EndIf

  If empty(cCodigo)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "Código do cliente é obrigatório"}')
    Return .F.
  EndIf

  // Buscar cliente no banco...
  cData := '{"codigo": "' + cCodigo + '", "nome": "Cliente Exemplo"}'
  oRest:setKeyHeaderResponse("Content-Type", "application/json")
  oRest:setResponse(cData)
Return .T.
```

**@Post criando recurso:**

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Post("/api/v1/pedidos")
User Function criarPedido()
  Local jBody    as Object
  Local cBodyStr as Character
  Local nNumPed  as Numeric
  Local cErro    as Character

  oRest:setKeyHeaderResponse("Content-Type", "application/json")

  cBodyStr := oRest:GetBodyRequest()
  If empty(cBodyStr)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "Body da requisição está vazio"}')
    Return .F.
  EndIf

  jBody := JsonObject():New()
  jBody:fromJson(cBodyStr)

  If jBody == Nil
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "JSON inválido"}')
    Return .F.
  EndIf

  // Criar pedido (lógica de negócio)...
  nNumPed := 1001  // Número gerado

  oRest:setStatusCode(201)
  oRest:setResponse('{"numeroPedido": ' + cValToChar(nNumPed) + ', "status": "criado"}')
Return .T.
```

**@Put atualizando recurso:**

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Put("/api/v1/pedidos/:id")
User Function atualizarPedido()
  Local jPath as Object
  Local jBody as Object
  Local cId   as Character

  jPath := oRest:getPathParamsRequest()
  cId   := jPath <> Nil .And. ValType(jPath["id"]) != "U" ? jPath["id"] : ""

  If empty(cId)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "ID do pedido é obrigatório"}')
    Return .F.
  EndIf

  jBody := JsonObject():New()
  jBody:fromJson(oRest:GetBodyRequest())

  // Lógica de atualização...
  oRest:setStatusCode(200)
  oRest:setResponse('{"id": "' + cId + '", "status": "atualizado"}')
Return .T.
```

**@Delete removendo recurso:**

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Delete("/api/v1/pedidos/:id")
User Function deletarPedido()
  Local jPath as Object
  Local cId   as Character

  jPath := oRest:getPathParamsRequest()
  cId   := jPath <> Nil .And. ValType(jPath["id"]) != "U" ? jPath["id"] : ""

  If empty(cId)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "ID é obrigatório"}')
    Return .F.
  EndIf

  // Lógica de remoção...
  oRest:setStatusCode(204)
  oRest:setResponse("")
Return .T.
```

### 8.7 REST em Classes TLPP

As annotations devem ser posicionadas **dentro da definição da classe**, antes da declaração do método:

```tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"
#include "protheus.ch"

namespace backoffice.vendas

Class PedidoApi
  Public Method New() Constructor

  @Get("/api/v1/pedidos")
  Public Method listar()

  @Get("/api/v1/pedidos/:id")
  Public Method buscarPorId()

  @Post("/api/v1/pedidos")
  Public Method criar()

  @Put("/api/v1/pedidos/:id")
  Public Method atualizar()

  @Delete("/api/v1/pedidos/:id")
  Public Method deletar()
EndClass

Method New() Class PedidoApi
Return Self

Method listar() Class PedidoApi
  Local oResp := JsonObject():New()
  oResp["pedidos"] := {}
  oRest:setKeyHeaderResponse("Content-Type", "application/json")
  oRest:setResponse(oResp:toJSON())
Return .T.

Method buscarPorId() Class PedidoApi
  Local jPath := oRest:getPathParamsRequest()
  Local cId   := jPath["id"]
  oRest:setResponse('{"id": "' + cId + '", "status": "confirmado"}')
Return .T.

// ... demais métodos
```

### 8.8 Documentação Automática de APIs

O `tlppCore` possui um **motor nativo de documentação** que gera automaticamente a documentação das APIs REST definidas por annotations.

Disponível a partir do **tlppCore 01.04.02** + AppServer **20.3.1.10**.

Repositório de exemplos: [github.com/totvs/tlpp-sample-rest-documentation](https://github.com/totvs/tlpp-sample-rest-documentation)

```tlpp
// Annotation com descrição para documentação automática
@Get(endpoint="/api/v1/produtos", description="Retorna lista de produtos ativos no estoque")
User Function getProdutos()
  // ...
Return .T.
```

### 8.9 FWRest — Consumindo APIs Externas

Para consumir APIs REST externas (client-side), usa-se a classe `FWRest` (disponível tanto em ADVPL quanto em TLPP):

```advpl
// Consulta de CEP (sem autenticação)
Local oRestClient := FWRest():New("https://viacep.com.br/ws")
Local aHeader := {}

oRestClient:setPath("/" + cCep + "/json/")

If oRestClient:Get(aHeader)
  ConOut("Resultado: " + oRestClient:cResult)
Else
  Alert("Erro: " + oRestClient:GetLastError())
EndIf
```

```advpl
// Com autenticação Bearer Token
Local oRestClient := FWRest():New("https://api.exemplo.com")
Local aHeader := {}

aAdd(aHeader, "Authorization: Bearer " + cToken)
aAdd(aHeader, "Content-Type: application/json")

oRestClient:setPath("/api/v1/clientes")
oRestClient:setBody('{"codigo": "001"}')

If oRestClient:Post(aHeader)
  ConOut(oRestClient:cResult)
EndIf
```

---

## 9. Interoperabilidade com ADVPL

### 9.1 TLPP chamando ADVPL

Um programa TLPP pode chamar qualquer **User Function** ou **Procedure** ADVPL normalmente:

```tlpp
// Arquivo: meuProgramaTlpp.tlpp
#include "tlpp-core.th"
#include "protheus.ch"

namespace minha.app

User Function testeInterop()
  Local cResultado as Character
  Local cCodigo    := "A001" as Character

  // Chamando função ADVPL diretamente (sem namespace)
  cResultado := U_BuscaCliente(cCodigo)   // U_BuscaCliente está em um .prw
  ConOut("Cliente: " + cResultado)
Return
```

### 9.2 ADVPL chamando TLPP

Para chamar uma função TLPP a partir do ADVPL, a função TLPP **deve ter um namespace** declarado:

```tlpp
// Arquivo: validacoes.tlpp
#include "tlpp-core.th"
namespace custom.validacoes

User Function validarCNPJ(cCNPJ as Character) as Logical
  // lógica de validação
Return .T.
```

```advpl
// Arquivo: meuFonte.prw (ADVPL)
User Function chamarTLPP()
  Local lValido as Logical
  Local cCNPJ   := "12.345.678/0001-90"

  // Chamando a função TLPP com namespace completo
  lValido := custom.validacoes.U_validarCNPJ(cCNPJ)

  If lValido
    Alert("CNPJ válido!")
  EndIf
Return
```

> **Como funciona:** Ao entrar na função TLPP, o motor reconhece variáveis e funções com nomes maiores do que o permitido no ADVPL. Ao retornar, os padrões ADVPL são restaurados.

### 9.3 StaticCall — Descontinuação

O `StaticCall()` do ADVPL permitia executar **Static Functions** de outros fontes. O TLPP **não suporta** o conceito de StaticCall e **bloqueou** essa funcionalidade para arquivos `.tlpp`.

| Situação | ADVPL | TLPP |
|---|---|---|
| `Static Function` visível no mesmo fonte | Sim | Sim |
| `Static Function` de outro fonte via `StaticCall()` | Sim | **Não** (descontinuado) |
| Funções públicas entre fontes | Via `User Function U_` | Via `User Function` + namespace |

**Migração da Static Function para namespace TLPP:**

```advpl
// ADVPL antigo — usando static function + staticcall
// Arquivo: Xisto.prw
static function MenuDef() as Array
  // ...
Return aMenu
```

```tlpp
// TLPP novo — usando namespace
// Arquivo: custom.xisto.minharotina.tlpp
namespace custom.xisto.minharotina

User Function MenuDef() as Array
  // ...
Return aMenu
```

### 9.4 MVC no TLPP

O MVC no Protheus era baseado em `StaticCall` para localizar `MenuDef`, `ModelDef`, `ViewDef` etc. Com a descontinuação do StaticCall no TLPP, o uso de MVC em `.tlpp` foi limitado por muito tempo.

A partir do **release 12.1.2410**, o Framework Protheus foi atualizado para suportar MVC em TLPP:

```tlpp
// Arquivo: custom.modulo.naturezas.tlpp
#include "tlpp-core.th"
#include "protheus.ch"

namespace custom.modulo.naturezas

// MVC publicado como REST e menu integrado
PUBLISH USER MODEL REST NAME customNaturezasCrudSED

User Function MenuDef() as Array
  // definição do menu
Return aMenu

User Function ModelDef() as Object
  // definição do modelo
Return oModel

User Function ViewDef() as Object
  // definição da view
Return oView
```

> **Versões anteriores a 12.1.2410:** Manter fontes MVC em `.prw` (ADVPL). Somente novas rotinas sem MVC devem ir para `.tlpp`.

---

## 10. DynCall — Importação de DLL

O **DynCall** é um recurso exclusivo do TLPP que permite importar e chamar funções de **DLLs (Dynamic Link Libraries)** nativas (escritas em C/C++):

```tlpp
#include "tlpp-core.th"

User Function exemploDynCall()
  Local oDll as Object

  // Carregar a DLL
  If IsSrvUnix()
    oDll := tRunDll():New("./minhabiblioteca.so")
  Else
    oDll := tRunDll():New("minhabiblioteca.dll")
  EndIf

  TRY
    // Chamar função da DLL — assinatura: "IS" = retorna Int, recebe String
    // 'V' = void, 'I' = int, 'S' = string, 'D' = double, 'L' = long
    Local nResultado := oDll:callFunction("calcularValor", "IS", "parametro")
    ConOut("Resultado: " + cValToChar(nResultado))

  CATCH oError
    ConOut("Erro ao chamar DLL: " + oError:description)
    ConOut("Código: " + cValToChar(oDll:GetLastError()))

  FINALLY
    oDll:Free()   // Liberar a DLL

  ENDTRY
Return
```

**Tabela de tipos para assinatura DynCall:**

| Letra | Tipo C/C++ | Observação |
|---|---|---|
| `V` | `void` | Sem retorno / sem parâmetro |
| `I` | `int` / `int32_t` | Inteiro 32 bits |
| `L` | `long` | Long |
| `D` | `double` | Ponto flutuante dupla precisão |
| `S` | `char*` | String (ponteiro para char) |
| `P` | `void*` | Ponteiro genérico |

> A assinatura **sempre começa pelo tipo de retorno**, seguido pelos tipos dos parâmetros.

---

## 11. PROBAT — Testes Unitários

O **PROBAT** é o motor de testes unitários nativo do tlppCore. Suporta:

- Testes unitários
- Testes funcionais
- Testes integrados
- Análise de **cobertura de código**
- Integração com **DevOps/CI-CD**
- TDD (Test-Driven Development)

```tlpp
#include "tlpp-core.th"
#include "test.th"            // Include do PROBAT

namespace sample.customer.test

using namespace tunittest.core
using namespace tunittest.assistant
using namespace sample.customer

// Annotation @test marca uma função como caso de teste
@test("Deve retornar erro ao criar pedido sem body")
function testCriarPedidoSemBody()
  TlppRestMock():createPostRequest()   // Simula uma requisição POST vazia
  criarPedido()
  Assert():AreEqual(oRest:getStatusCode(), 400, "Deveria retornar 400 sem body")
Return

@test("Deve criar pedido com dados válidos")
function testCriarPedidoValido()
  Local cBody := '{"cliente": "001", "total": 150.00}'
  TlppRestMock():createPostRequest(cBody)
  criarPedido()
  Assert():AreEqual(oRest:getStatusCode(), 201, "Deveria retornar 201 - criado")
Return
```

**Repositório oficial de exemplos:** [github.com/totvs/tlpp-probat-samples](https://github.com/totvs/tlpp-probat-samples)

Estrutura do projeto de testes:

```
/ini    — Configurações do AppServer para PROBAT
/run    — Scripts para execução automatizada dos testes
/src    — Código-fonte a ser testado
/test   — Implementações dos casos de teste
```

---

## 12. TDS — TOTVS Developer Studio for VSCode

### 12.1 Instalação e Configuração

A extensão oficial para desenvolvimento TLPP/ADVPL é o **TOTVS Developer Studio for VSCode (TDS-VSCode)**, disponível no [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=totvs.tds-vscode).

**Instalação:**

1. Abra o VSCode
2. Vá em Extensões (Ctrl+Shift+X)
3. Pesquise por `tds`
4. Instale **"TOTVS Developer Studio for VSCode (AdvPL, TLPP e 4GL)"**

**Configuração de encode** (essencial para evitar problemas com acentuação):

```
Ctrl+, → buscar "encode" → selecionar Windows1252 (cp1252)
```

**Configuração de Includes TLPP:**

1. Extraia os includes do `tlpp.rpo` usando a ferramenta de extração
2. Adicione o diretório de includes nas configurações do workspace:

```json
// .vscode/settings.json
{
  "totvsLanguageServer.includes": [
    "c:/totvs/includes",
    "c:/totvs/tlpp-includes"
  ]
}
```

**Configuração de ambiente:**

O TDS-VSCode requer registro de ambientes individuais (diferente do TDS-Eclipse), baseados nas seções do `appserver.ini`.

### 12.2 Compilação

| Ação | Atalho | Comando |
|---|---|---|
| Compilar arquivo atual | `Ctrl+F9` | `TOTVS: Compile File` |
| Recompilar arquivo atual | `Ctrl+Shift+F9` | `TOTVS: Recompile File` |
| Compilar editores abertos | `Ctrl+F10` | `TOTVS: Compile Open Editors` |
| Recompilar editores abertos | `Ctrl+Shift+F10` | `TOTVS: Recompile Open Editors` |
| Executar/depurar | `Ctrl+F5` / `F5` | Executar sem depuração / com depuração |

> Somente extensões cadastradas na lista de extensões permitidas são compiladas. Certifique-se de que `.tlpp` está na lista.

**Compilação via linha de comando (TDS-CLI):**

```bash
# Compilar um único arquivo
tds-cli compile --server <servidor> --port <porta> --env <ambiente> --file meuArquivo.tlpp

# Compilar uma pasta inteira
tds-cli compile --server <servidor> --port <porta> --env <ambiente> --folder ./src
```

### 12.3 Deploy e Patches

O TDS-VSCode suporta todas as operações de deploy:

| Operação | Descrição |
|---|---|
| Gerar Patch | Cria um arquivo `.ptm` com os fontes compilados |
| Aplicar Patch | Aplica um `.ptm` no RPO do servidor |
| Deletar do RPO | Remove fontes compilados do repositório |
| Desfragmentar RPO | Otimiza o arquivo RPO |

### 12.4 TLPP Tools

A extensão complementar **totvs.tlpp-tools** adiciona funcionalidades específicas para TLPP:

- Visualização de **cobertura de código** gerada por testes PROBAT
- Geração de código-fonte a partir de **templates PROBAT**
- Integração com o Language Server do TDS-VSCode

Instalação: pesquise por `tlpp-tools` no marketplace do VSCode ou acesse [github.com/totvs/tlpp-tools](https://github.com/totvs/tlpp-tools).

**Ativar logs para suporte:**

```
Ctrl+Shift+P → "TOTVS: On Logger Capture"
[reproduza o problema]
Ctrl+Shift+P → "TOTVS: Off Logger Capture"
[arquivo tdsSupport.zip será gerado]
```

---

## 13. Migração de ADVPL para TLPP

### 13.1 Estratégia de Migração

A TOTVS recomenda uma abordagem **gradual e sem pressa**:

1. **Novos desenvolvimentos:** Começar em TLPP imediatamente
2. **Integração gradual:** Migrar seções antigas que precisem de recursos TLPP, criando componentes TLPP chamados pelas rotinas ADVPL existentes
3. **Conversão progressiva:** Migrar o restante em ritmo confortável

```
[Legado ADVPL] ←→ [Componentes TLPP novos] → [Gradualmente substituir ADVPL]
```

### 13.2 Armadilhas Comuns

**1. Nomes de funções truncados:**

```advpl
// ADVPL: nomes são truncados em 10 chars
function myFunction001()  // compilado como "myFunction" (10 chars)
```

```tlpp
// TLPP: nome completo preservado
function myFunction001()  // compilado como "myFunction001" (13 chars)
// QUEBRA: código que chamava "myFunction()" não encontra mais a função
```

**Solução:** Revisar todos os nomes de funções antes de migrar e atualizar todos os pontos de chamada.

**2. Tipos de dados diferentes:**

```advpl
Local cTexto as string     // ADVPL — aceito
```

```tlpp
Local cTexto as Character  // TLPP — correto
Local cTexto as string     // TLPP — pode gerar erro de compilação
```

**3. MVC e Static Functions:**

```advpl
// ADVPL — funciona via StaticCall
static function MenuDef()
  Return aMenu
```

```tlpp
// TLPP — não funciona: sem StaticCall, sem static function
// SOLUÇÃO: usar namespace + user function
namespace custom.meumodulo
User Function MenuDef() as Array
  Return aMenu
```

**4. Include na ordem errada:**

```tlpp
// ERRADO — protheus.ch antes do tlpp-core.th
#include "protheus.ch"
#include "tlpp-core.th"   // Modificadores de acesso podem não funcionar
```

```tlpp
// CORRETO
#include "tlpp-core.th"
#include "protheus.ch"
```

**5. Modificar objeto retornado pelo oRest:**

```tlpp
// ERRADO — modifica o objeto interno do motor REST
Local jQuery := oRest:getQueryRequest()
jQuery["novaChave"] := "valor"  // Persiste para próximas requisições!
```

```tlpp
// CORRETO — ler o valor apenas
Local cValor := oRest:getQueryRequest():GetJsonText("minhaChave")
```

---

## 14. Boas Práticas TLPP

### 14.1 Convenções de Nomenclatura

| Elemento | Convenção | Exemplo |
|---|---|---|
| Namespace | Minúsculo, pontos, sem underscore | `backoffice.fiscal.nfe` |
| Classes | PascalCase | `ClienteController`, `PedidoService` |
| Métodos e funções | camelCase | `buscarCliente()`, `calcularTotal()` |
| Variáveis locais | Prefixo de tipo + camelCase | `cNome`, `nValor`, `lAtivo`, `oCliente` |
| Constantes | MAIÚSCULO_COM_UNDERSCORE | `MAX_TENTATIVAS`, `STATUS_ATIVO` |
| Namespaces de customização | Iniciar com `custom` | `custom.rh.folha` |
| Namespaces reservados | `tlpp.*`, `core.*` | Uso restrito à TOTVS |
| Idioma | Inglês (recomendado) | `customerService`, `orderController` |

### 14.2 Organização de Código

```
projeto/
├── src/
│   ├── custom.cliente.controller.tlpp
│   ├── custom.cliente.service.tlpp
│   ├── custom.cliente.repository.tlpp
│   └── custom.cliente.model.tlpp
├── test/
│   ├── custom.cliente.controller.test.tlpp
│   └── custom.cliente.service.test.tlpp
└── includes/
    ├── tlpp-core.th
    └── tlpp-rest.th
```

**Responsabilidades por camada:**

| Arquivo / Namespace | Responsabilidade |
|---|---|
| `*.controller.tlpp` | Endpoints REST, validação de entrada/saída |
| `*.service.tlpp` | Regras de negócio |
| `*.repository.tlpp` | Acesso a banco de dados |
| `*.model.tlpp` | Definição de classes de domínio |

### 14.3 Princípios SOLID em TLPP

**Single Responsibility (SRP):**

```tlpp
// ERRADO — classe com múltiplas responsabilidades
Class ClienteManager
  Public Method salvarNoArquivo()
  Public Method enviarEmail()
  Public Method calcularDesconto()
EndClass

// CORRETO — uma responsabilidade por classe
Class ClienteRepository
  Public Method salvar(oCliente as Object)
EndClass

Class ClienteNotificacao
  Public Method enviarEmail(oCliente as Object)
EndClass

Class ClientePreco
  Public Method calcularDesconto(oCliente as Object) as Numeric
EndClass
```

**Open/Closed Principle (OCP) — usando herança e interfaces:**

```tlpp
Interface IRelatorio
  Public Method gerar() as Character
EndInterface

Class RelatorioVendas Implements IRelatorio
  Public Method gerar() as Character
Return "Relatório de Vendas..."

Class RelatorioEstoque Implements IRelatorio
  Public Method gerar() as Character
Return "Relatório de Estoque..."
```

**Tratamento de erros consistente:**

```tlpp
// Padrão recomendado para funções TLPP
function processarPedido(nPedido as Numeric) as Logical
  Local lOk := .T. as Logical

  TRY
    validarPedido(nPedido)
    executarProcessamento(nPedido)
  CATCH oError
    ConOut("Erro em processarPedido: " + oError:description)
    lOk := .F.
  FINALLY
    // Liberar recursos sempre
    limpezaRecursos()
  ENDTRY

Return lOk
```

**Evitar magic numbers:**

```tlpp
// ERRADO
If nStatus == 2
  // ...
EndIf

// CORRETO
#define STATUS_APROVADO  2
#define STATUS_PENDENTE  1
#define STATUS_CANCELADO 3

If nStatus == STATUS_APROVADO
  // ...
EndIf
```

---

## 15. Exemplos de Código Completos

### 15.1 Hello World em TLPP

```tlpp
// Arquivo: meu.exemplo.olaMundo.tlpp
#include "tlpp-core.th"
#include "protheus.ch"

namespace meu.exemplo

/*
  Primeiro programa em TLPP
  Execute: meu.exemplo.U_Ola_Mundo_em_TLPP
*/
function U_Ola_Mundo_em_TLPP()
  Local cMensagem := "Olá Mundo — TLPP!" as Character
  ConOut(cMensagem)
Return
```

### 15.2 Classe Completa com Herança

```tlpp
// Arquivo: custom.financeiro.conta.tlpp
#include "tlpp-core.th"
#include "protheus.ch"

namespace custom.financeiro

// Classe base abstrata
abstract Class ContaBase
  Protected Data cTitular   as Character
  Protected Data nSaldo     as Numeric
  Protected Data cAgencia   as Character
  Private   Data dAbertura  as Date

  Public Method New(cTitular as Character, cAgencia as Character) Constructor
  Public Method GetTitular() as Character
  Public Method GetSaldo()   as Numeric
  Public Method Extrato()
  Public abstract Method Sacar(nValor as Numeric) as Logical
EndClass

Method New(cTitular as Character, cAgencia as Character) Class ContaBase
  ::cTitular  := cTitular
  ::cAgencia  := cAgencia
  ::nSaldo    := 0
  ::dAbertura := Date()
Return Self

Method GetTitular() Class ContaBase as Character
Return ::cTitular

Method GetSaldo() Class ContaBase as Numeric
Return ::nSaldo

Method Extrato() Class ContaBase
  ConOut("=== EXTRATO ===")
  ConOut("Titular: " + ::cTitular)
  ConOut("Agência: " + ::cAgencia)
  ConOut("Saldo:   " + Transform(::nSaldo, "@E 9,999,999.99"))
Return

// Conta Corrente — herda ContaBase
Class ContaCorrente From ContaBase
  Private Data nLimite as Numeric

  Public Method New(cTitular as Character, cAgencia as Character, nLimite as Numeric) Constructor
  Public Method Depositar(nValor as Numeric)
  Public Method Sacar(nValor as Numeric)     as Logical
  Public Method GetLimiteSaldo()             as Numeric
EndClass

Method New(cTitular as Character, cAgencia as Character, nLimite as Numeric) Class ContaCorrente
  _Super:New(cTitular, cAgencia)
  ::nLimite := nLimite
Return Self

Method Depositar(nValor as Numeric) Class ContaCorrente
  If nValor > 0
    ::nSaldo += nValor
    ConOut("Depósito de " + cValToChar(nValor) + " realizado.")
  Else
    ConOut("Valor de depósito inválido.")
  EndIf
Return

Method Sacar(nValor as Numeric) Class ContaCorrente as Logical
  Local lOk := .F. as Logical

  If nValor <= 0
    ConOut("Valor de saque inválido.")
  ElseIf nValor > (::nSaldo + ::nLimite)
    ConOut("Saldo insuficiente (incluindo limite).")
  Else
    ::nSaldo -= nValor
    ConOut("Saque de " + cValToChar(nValor) + " realizado.")
    lOk := .T.
  EndIf

Return lOk

Method GetLimiteSaldo() Class ContaCorrente as Numeric
Return ::nSaldo + ::nLimite

// Conta Poupança — herda ContaBase
Class ContaPoupanca From ContaBase
  Private Data nRentabilidade as Numeric

  Public Method New(cTitular as Character, cAgencia as Character) Constructor
  Public Method Depositar(nValor as Numeric)
  Public Method Sacar(nValor as Numeric)       as Logical
  Public Method AplicarRendimento()
EndClass

Method New(cTitular as Character, cAgencia as Character) Class ContaPoupanca
  _Super:New(cTitular, cAgencia)
  ::nRentabilidade := 0.005   // 0.5% ao mês
Return Self

Method Depositar(nValor as Numeric) Class ContaPoupanca
  If nValor > 0
    ::nSaldo += nValor
  EndIf
Return

Method Sacar(nValor as Numeric) Class ContaPoupanca as Logical
  Local lOk := .F. as Logical

  If nValor > 0 .And. nValor <= ::nSaldo
    ::nSaldo -= nValor
    lOk := .T.
  EndIf

Return lOk

Method AplicarRendimento() Class ContaPoupanca
  ::nSaldo *= (1 + ::nRentabilidade)
  ConOut("Rendimento aplicado. Novo saldo: " + cValToChar(::nSaldo))
Return

// Uso das classes
User Function testeContas()
  Local oCC  := ContaCorrente():New("João Silva", "0001-5", 500)
  Local oCP  := ContaPoupanca():New("Maria Santos", "0001-5")

  oCC:Depositar(1000)
  oCC:Sacar(1400)     // Usa o limite
  oCC:Extrato()

  oCP:Depositar(2000)
  oCP:AplicarRendimento()
  oCP:Extrato()
Return
```

### 15.3 API REST CRUD Completa

```tlpp
// Arquivo: custom.api.produto.tlpp
#include "tlpp-core.th"
#include "tlpp-rest.th"
#include "protheus.ch"

namespace custom.api.produto

/*
  CRUD de Produtos via REST TLPP
  GET    /api/v1/produtos          → listar todos
  GET    /api/v1/produtos/:codigo  → buscar por código
  POST   /api/v1/produtos          → criar produto
  PUT    /api/v1/produtos/:codigo  → atualizar produto
  DELETE /api/v1/produtos/:codigo  → deletar produto
*/

Static Function setJsonHeader()
  oRest:setKeyHeaderResponse("Content-Type", "application/json; charset=utf-8")
Return

@Get("/api/v1/produtos")
User Function getProdutos()
  Local jQuery   as Object
  Local cCodFil  as Character
  Local cQuery   as Character
  Local oItem    as Object
  Local aRes     as Array
  Local oResp    as Object

  setJsonHeader()
  RPCSetEnv("01", "0101001")

  jQuery  := oRest:getQueryRequest()
  cCodFil := xFilial("SB1")

  cQuery  := "SELECT B1_COD, B1_DESC, B1_UM, B1_TIPO, B1_PRV1 "
  cQuery  += "FROM " + RetSQLName("SB1") + " SB1 "
  cQuery  += "WHERE D_E_L_E_T_ = ' ' AND B1_FILIAL = '" + cCodFil + "'"

  dbUseArea(.T., "TOPCONN", TCGenQry(,, cQuery), "QTMPSB1", .T., .T.)

  aRes := {}
  While QTMPSB1->(!EOF())
    oItem := JsonObject():New()
    oItem["codigo"]    := AllTrim(QTMPSB1->B1_COD)
    oItem["descricao"] := AllTrim(QTMPSB1->B1_DESC)
    oItem["um"]        := AllTrim(QTMPSB1->B1_UM)
    oItem["tipo"]      := AllTrim(QTMPSB1->B1_TIPO)
    oItem["preco"]     := QTMPSB1->B1_PRV1
    aAdd(aRes, oItem)
    QTMPSB1->(dbSkip())
  EndDo
  dbCloseArea()
  rpcClearEnv()

  oResp          := JsonObject():New()
  oResp["itens"] := aRes
  oResp["total"] := Len(aRes)

  oRest:setStatusCode(200)
  oRest:setResponse(oResp:toJSON())
Return .T.

@Get("/api/v1/produtos/:codigo")
User Function getProdutoPorCodigo()
  Local jPath   as Object
  Local cCodigo as Character
  Local oResp   as Object

  setJsonHeader()

  jPath   := oRest:getPathParamsRequest()
  cCodigo := jPath <> Nil ? AllTrim(jPath["codigo"]) : ""

  If empty(cCodigo)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "Código do produto é obrigatório"}')
    Return .F.
  EndIf

  RPCSetEnv("01", "0101001")
  dbSelectArea("SB1")
  SB1->(dbSetOrder(1))

  If SB1->(dbSeek(xFilial("SB1") + PadR(cCodigo, TamSX3("B1_COD"))))
    oResp              := JsonObject():New()
    oResp["codigo"]    := AllTrim(SB1->B1_COD)
    oResp["descricao"] := AllTrim(SB1->B1_DESC)
    oResp["um"]        := AllTrim(SB1->B1_UM)
    oResp["tipo"]      := AllTrim(SB1->B1_TIPO)
    oResp["preco"]     := SB1->B1_PRV1

    oRest:setStatusCode(200)
    oRest:setResponse(oResp:toJSON())
  Else
    oRest:setStatusCode(404)
    oRest:setResponse('{"erro": "Produto não encontrado"}')
  EndIf

  rpcClearEnv()
Return .T.

@Post("/api/v1/produtos")
User Function criarProduto()
  Local jBody   as Object
  Local cErro   as Character
  Local cCodigo as Character

  setJsonHeader()

  jBody := JsonObject():New()
  jBody:fromJson(oRest:GetBodyRequest())

  If jBody == Nil
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "JSON inválido"}')
    Return .F.
  EndIf

  cCodigo := AllTrim(jBody:GetJsonText("codigo"))

  If empty(cCodigo)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "Campo codigo é obrigatório"}')
    Return .F.
  EndIf

  // Aqui viria a lógica de negócio / MSExecAuto...
  // ...

  oRest:setStatusCode(201)
  oRest:setResponse('{"mensagem": "Produto criado", "codigo": "' + cCodigo + '"}')
Return .T.

@Delete("/api/v1/produtos/:codigo")
User Function deletarProduto()
  Local jPath   as Object
  Local cCodigo as Character

  setJsonHeader()

  jPath   := oRest:getPathParamsRequest()
  cCodigo := jPath <> Nil ? AllTrim(jPath["codigo"]) : ""

  If empty(cCodigo)
    oRest:setStatusCode(400)
    oRest:setResponse('{"erro": "Código é obrigatório"}')
    Return .F.
  EndIf

  // Lógica de remoção (soft delete)...

  oRest:setStatusCode(204)
  oRest:setResponse("")
Return .T.
```

### 15.4 Tratamento de Erro Completo

```tlpp
// Arquivo: custom.util.erros.tlpp
#include "tlpp-core.th"
#include "protheus.ch"

namespace custom.util.erros

// Função auxiliar para criar ErrorClass padronizado
function criarErro(nCodigo as Numeric, cDescricao as Character, cOperacao as Character) as Object
  Local oErro := ErrorClass():New()
  oErro:genCode    := nCodigo
  oErro:description := cDescricao
  oErro:operation  := cOperacao
Return oErro

// Exemplo de uso em camada de serviço
function processarTransferencia(cOrigem as Character, cDestino as Character, nValor as Numeric) as Logical
  Local lOk      := .T. as Logical
  Local oContaOrig as Object
  Local oContaDest as Object

  TRY
    // Validações de entrada
    If empty(cOrigem) .Or. empty(cDestino)
      throw criarErro(1001, "Contas de origem e destino são obrigatórias", "processarTransferencia")
    EndIf

    If nValor <= 0
      throw criarErro(1002, "Valor da transferência deve ser positivo", "processarTransferencia")
    EndIf

    // Buscar contas
    oContaOrig := buscarConta(cOrigem)
    If oContaOrig == Nil
      throw criarErro(1003, "Conta de origem não encontrada: " + cOrigem, "processarTransferencia")
    EndIf

    oContaDest := buscarConta(cDestino)
    If oContaDest == Nil
      throw criarErro(1004, "Conta de destino não encontrada: " + cDestino, "processarTransferencia")
    EndIf

    // Verificar saldo
    If oContaOrig:GetSaldo() < nValor
      throw criarErro(1005, "Saldo insuficiente na conta " + cOrigem, "processarTransferencia")
    EndIf

    // Executar transferência
    oContaOrig:Sacar(nValor)
    oContaDest:Depositar(nValor)

    ConOut("Transferência de " + cValToChar(nValor) + " realizada com sucesso.")

  CATCH oError
    ConOut("ERRO [" + cValToChar(oError:genCode) + "]: " + oError:description)
    ConOut("Operação: " + oError:operation)
    lOk := .F.

  FINALLY
    // Sempre executado — liberar recursos
    If oContaOrig <> Nil
      FreeObj(oContaOrig)
    EndIf
    If oContaDest <> Nil
      FreeObj(oContaDest)
    EndIf

  ENDTRY

Return lOk
```

---

## 16. Referências e Recursos

### Documentação Oficial

| Recurso | URL |
|---|---|
| TDN — TLPP Geral | https://tdn.totvs.com/display/tec/TLPP |
| TDN — TLPP Sobre | https://tdn.totvs.com/display/tec/TLPP+-+Sobre |
| TDN — Recursos de Linguagem | https://tdn.totvs.com/display/tec/TLPP+-+Recursos+de+Linguagem |
| TDN — Classes | https://tdn.totvs.com/display/tec/Classes |
| TDN — Namespace | https://tdn.totvs.com/display/tec/Namespace |
| TDN — Try...Catch | https://tdn.totvs.com/display/tec/Try...Catch |
| TDN — REST | https://tdn.totvs.com/display/tec/REST |
| TDN — REST via INI | https://tdn.totvs.com/display/tec/Via+INI |
| TDN — oRest:getBodyRequest | https://tdn.totvs.com/display/tec/oRest:getBodyRequest |
| TDN — DynCall Assinatura | https://tdn.totvs.com/display/tec/DynCall+-+Assinatura+da+chamada |
| TDN — PROBAT | https://tdn.totvs.com/display/tec/PROBAT |
| TDN — Padronização TLPP | https://tdn.totvs.com/pages/releaseview.action?pageId=633537898 |
| TDN — REST Novidades | https://tdn.totvs.com/display/framework/Entendendo+as+novidades+do+REST |

### Repositórios Oficiais GitHub TOTVS

| Repositório | Descrição |
|---|---|
| [totvs/tlpp-samples](https://github.com/totvs/tlpp-samples) | Repositório central de exemplos TLPP |
| [totvs/tlpp-sample-rest](https://github.com/totvs/tlpp-sample-rest) | Exemplos de REST nativo com TLPP |
| [totvs/tlpp-sample-rest-documentation](https://github.com/totvs/tlpp-sample-rest-documentation) | Exemplos do motor de documentação REST |
| [totvs/tlpp-dyncall-samples](https://github.com/totvs/tlpp-dyncall-samples) | Exemplos de DynCall (importação de DLL) |
| [totvs/tlpp-probat-samples](https://github.com/totvs/tlpp-probat-samples) | Exemplos de testes com PROBAT |
| [totvs/tds-vscode](https://github.com/totvs/tds-vscode) | TOTVS Developer Studio para VSCode |
| [totvs/tlpp-tools](https://github.com/totvs/tlpp-tools) | Ferramentas complementares para TLPP |
| [totvs/ablon-tlpp-unittest](https://github.com/totvs/ablon-tlpp-unittest) | Framework de testes unitários para TLPP |

### Extensões VSCode

| Extensão | ID | Descrição |
|---|---|---|
| TDS-VSCode | `totvs.tds-vscode` | IDE principal para TLPP/ADVPL/4GL |
| TLPP Tools | `totvs.tlpp-tools` | Cobertura de código e templates PROBAT |

### Artigos e Comunidade

| Recurso | URL |
|---|---|
| Blog TOTVS — TLPP | https://www.totvs.com/blog/developers/tlpp/ |
| Medium — O que muda no TL++ | https://medium.com/totvsdevelopers/tl-o-que-muda-ace5781d6c49 |
| Medium — Como migrar para TLPP | https://medium.com/totvsdevelopers/como-iniciar-e-migrar-para-o-tlpp-a60dcf871c06 |
| Medium — TLPP no Protheus | https://medium.com/totvsdevelopers/tlpp-no-protheus-a113296e29b8 |
| Medium — Try/Catch em TLPP | https://medium.com/totvsdevelopers/entendendo-a-estrutura-try-catch-em-tlpp-b01f2ce94e88 |
| Fórum TOTVS | https://forum.totvs.io |
| Terminal de Informação | https://terminaldeinformacao.com |

---

> **Nota:** Este documento foi compilado com base em pesquisas na documentação oficial da TOTVS (TDN), repositórios GitHub públicos da TOTVS, publicações no Medium TOTVS Developers, fóruns da comunidade e artigos técnicos. As informações refletem o estado da linguagem TLPP até março de 2026. Para informações mais atuais, consulte sempre a documentação oficial em [tdn.totvs.com](https://tdn.totvs.com).
