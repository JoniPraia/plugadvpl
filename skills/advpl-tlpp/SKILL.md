---
description: TLPP (TOTVS Language Plus Productive, também TL++) — sucessor moderno do ADVPL com OO completa, namespaces (custom.<seg>.<svc>), annotations @Get/@Post/@Test, JSON nativo, try/catch/finally, reflection, identificadores até 250 chars (vs 10 em .prw), modificador default PRIVATE (oposto do ADVPL PUBLIC). Use ao trabalhar com arquivos .tlpp/.th, código moderno, REST tlppCore, ou migração ADVPL→TLPP.
---

# advpl-tlpp — TLPP (TOTVS Language Plus Productive)

**TLPP** (também chamado **TL++**) é a evolução moderna do ADVPL lançada pela TOTVS para suportar paradigmas atuais: orientação a objetos completa, namespaces, annotations, exceções estruturadas, JSON nativo, reflection. Coexiste com ADVPL no mesmo RPO/tlpp.rpo — código TLPP chama ADVPL e vice-versa.

Diferenças críticas vs ADVPL clássico:

| Item                         | ADVPL clássico (.prw)        | TLPP (.tlpp)                          |
|------------------------------|------------------------------|----------------------------------------|
| Limite de identificador      | **10 chars** (legado Clipper)| **250 chars**                          |
| Default de visibilidade      | **PUBLIC**                   | **PRIVATE**                            |
| Sintaxe de classe            | `Class` + `Method ... Class` | `class` + `method() class` (com tipagem) |
| Namespaces                   | ❌                           | ✅ (`custom.<seg>.<svc>`)              |
| Annotations                  | ❌                           | ✅ (`@Get`, `@Post`, `@Test`, etc.)    |
| try/catch/throw              | `Begin Sequence`/`Recover`   | `try`/`catch`/`finally`/`throw`        |
| JSON nativo                  | `JsonObject` via include     | nativo                                 |
| Reflection                   | limitada                     | `FwReflection`                         |
| Header includes              | `.ch`                        | `.th`                                  |

## Quando usar

- Edit/criação de arquivos `.tlpp` ou `.th` (header TLPP).
- Endpoints REST com annotations (`@Get`, `@Post`, `@Put`, `@Delete`) — REST tlppCore.
- Classes com herança, interfaces, modificadores de acesso (`public`/`protected`/`private`).
- Testes unitários com PROBAT (`@Test`, `@Before`, `@After`).
- Migração ADVPL → TLPP.
- Uso de `JsonObject`, `try`/`catch`/`finally`, `throw`.
- Customizar cadastro novo onde quer typing + namespace pra não colidir com outros fornecedores.

## Extensões e includes

- `.tlpp` — fonte TLPP (compilado pra `tlpp.rpo` separado do RPO ADVPL).
- `.th` — header TLPP (substitui `.ch` do ADVPL).
- Includes essenciais:
  - `#include "tlpp-core.th"` — features básicas (try/catch, JsonObject, annotations, namespaces).
  - `#include "tlpp-rest.th"` — annotations REST (`@Get`, `@Post`, etc.).
  - `#include "tlpp-object.th"` — classes/interfaces.
  - `#include "tlpp-probat.th"` — testes unitários PROBAT.

Versão mínima Protheus: **17.3.0.0** (quando namespace foi liberado).

## Identifier limit — 250 chars (vs 10 em .prw)

TLPP libera o legado de 10 caracteres do Clipper. **Pode** usar nomes longos:

```tlpp
namespace custom.fat.pedidos.validacoes

class ProcessadorDePedidosDeVendaComValidacaoFiscal
    public method validarPedidoComRegrasMultipla()
endclass
```

> **Cuidado misto:** se uma User Function TLPP é chamada de `.prw` ADVPL, o `.prw` ainda tem limite de 10 chars no nome da função invocada. Quando exporta TLPP pra ser usável em ADVPL, mantenha nomes ≤ 10 chars na fronteira.

Veja `[[advpl-fundamentals]]` pra detalhe da regra de 10 chars em ADVPL clássico.

## Tipagem opcional e parâmetros nomeados

```tlpp
function processOrder(string cNumero, numeric nValor := 0.00, boolean lEmite := .T.) as logical
    return .T.
endfunction
```

Tipos suportados: `string`, `numeric`, `boolean`, `date`, `array`, `object`, `codeblock`, `json`, `character`, `logical`.

Tipagem é **opcional** — função pode ser declarada sem tipos (`function foo(x, y)`). Mas com tipagem o compilador checa em build, evita erros em runtime.

## Namespaces

Liberado em Protheus 17.3.0.0:

```tlpp
namespace custom.mvc.customer

class Customer
    public data cCodigo as string
    method New() constructor
    method save() as logical
endclass
```

Consumidor:

```tlpp
using namespace custom.mvc.customer

local oCli := Customer():New()
oCli:cCodigo := "000001"
oCli:save()
```

### Regras de namespace

- **Lowercase**, separado por **ponto** (`.`), sem underscore.
- **Customer**: deve começar com `custom.` (ex: `custom.fat.pedidos`).
- **TOTVS reservado**: namespaces que começam com `tlpp.` são bloqueados em compilação (reservados pro `tlppCore`).
- Convenção: `custom.<segmento>.<servico>.<funcionalidade>` — ex: `custom.fat.pedido.validacao`.

## Modificadores de acesso — default é PRIVATE

**Diferente do ADVPL clássico** (onde default é PUBLIC), TLPP tem **default PRIVATE**:

| Modificador  | Acessibilidade                                        |
|--------------|-------------------------------------------------------|
| `private`    | Só dentro da própria classe (default em TLPP)         |
| `protected`  | Dentro da classe e classes derivadas                  |
| `public`     | De qualquer lugar (qualquer fonte que faça `using`)   |
| `static`     | Sempre PUBLIC por default; método de classe, não de instância |

```tlpp
class Vehicle
    public  data cPlate    as string         // acessível de fora
    private data nMileage  as numeric        // só dentro de Vehicle
    protected data dService as date          // Vehicle + classes filhas

    public  method New(cPlate) constructor
    public  method getInfo() as string
    private method recalculate() as numeric  // só dentro de Vehicle
    protected method updateService(dDate) as logical
    static  method utility() as string       // chamada sem instanciar: Vehicle.utility()
endclass

method New(cPlate) class Vehicle
    self:cPlate   := cPlate
    self:nMileage := 0
endmethod

method getInfo() class Vehicle
return "Vehicle: " + self:cPlate + " (" + cValToChar(self:nMileage) + "km)"
```

## Herança e interfaces

```tlpp
class Car from Vehicle
    public data nDoors as numeric
    public method New(cPlate, nDoors) constructor
endclass

method New(cPlate, nDoors) class Car
    _Super:New(cPlate)        // chama construtor da superclasse
    self:nDoors := nDoors
endmethod

// Interface
interface IPrintable
    method print() as logical
endinterface

class Report implements IPrintable
    public method print() as logical
endclass
```

Use `_Super:` pra chamar método da classe pai. Múltipla herança não é suportada (single inheritance + multi interface).

## Annotations

```tlpp
@Get(endpoint="/v1/customer/:id", description="Get customer by id")
@Auth(roles="admin,seller")
user function getCustomer()
    local cId := oRest:GetUrlParam("id")
    // ...
return .T.
```

Annotations padrão:
- **REST**: `@Get`, `@Post`, `@Put`, `@Delete`, `@Options`
- **Auth**: `@Auth(roles=...)`, `@Public` (skipa autenticação)
- **Testes**: `@Test`, `@Before`, `@After`, `@BeforeAll`, `@AfterAll`
- **Cache**: `@Cache(ttl=300)`
- **Sync**: `@Sync` (acesso exclusivo)

Annotations customizadas via reflection:

```tlpp
@MyAnnotation(value="x", priority=10)
function foo()
    // descobrivel via FwReflection em runtime
endfunction
```

Veja `[[advpl-webservice]]` pra REST tlppCore detalhado.

## REST com FWRest (class-based, alternativa às annotations sueltas)

```tlpp
namespace custom.api.customer
using namespace tlpp.web

class CustomerApi from FWRest
    @Get(endpoint="/v1/customers")
    method list() as json

    @Post(endpoint="/v1/customers")
    method create() as json
endclass
```

Resposta JSON nativa, sem `oRest:SetResponse(cString)` manual.

## try/catch/finally + throw

```tlpp
try
    if Empty(cId)
        throw ErrorClass():New("400", "ID obrigatorio")
    endif
    // ... logica
catch oErr
    conout("Erro: " + oErr:getDescription())
    oRest:SetStatusCode(500)
finally
    if oFile != nil
        oFile:close()
    endif
endtry
```

`ErrorClass` permite codes estruturados (HTTP-style). `finally` sempre executa, mesmo se houver `throw` ou `return` no try/catch.

> Equivalente ADVPL clássico: `Begin Sequence` / `Recover Using oErr` / `End Sequence`. Veja `[[advpl-fundamentals]]`.

## JSON nativo

```tlpp
local oJson := JsonObject():New()
oJson["nome"]      := "ACME"
oJson["itens"]     := {1, 2, 3}
oJson["sub"]       := JsonObject():New()
oJson["sub"]["x"]  := 10
oJson["ativo"]     := .T.

local cStr := oJson:ToJson()              // serializa pra string
local oOut := JsonObject():New()
local cErr := oOut:FromJson(cInput)        // desserializa
if !Empty(cErr)
    throw ErrorClass():New("400", "JSON invalido: " + cErr)
endif
```

Listas (`array` nativo), Booleano (`.T.`/`.F.`), Null (`nil`).

## PROBAT — testes unitários

```tlpp
#include "tlpp-probat.th"

namespace custom.test.calculator

class CalculatorTest
    @Before
    method setUp()
    
    @Test
    method testAddition()
    
    @After
    method tearDown()
endclass

method testAddition() class CalculatorTest
    local nResult := 2 + 2
    paAssertEqual(4, nResult, "2+2 deve ser 4")
endmethod
```

Rode via TDS (TOTVS Developer Studio) ou `tdscli probat`. Métodos de assert: `paAssertEqual`, `paAssertTrue`, `paAssertFalse`, `paAssertNotNil`, `paAssertNotEqual`, `paFail`.

## Interoperabilidade com ADVPL

| Direção            | Como funciona                                              |
|--------------------|-----------------------------------------------------------|
| TLPP → ADVPL       | Chamada direta de `User Function` ADVPL existente.        |
| ADVPL → TLPP function | `User Function` em `.tlpp` é chamada de `.prw` direto. |
| ADVPL → TLPP class | `using namespace` (em TLPP); ADVPL chama `MyClass():New()` se a classe for compilada e namespace exportado. |
| **`StaticCall`**   | **Deprecado em TLPP** — use namespaces explícitos.        |

```advpl
// ADVPL .prw consumindo TLPP class
#include "TOTVS.CH"

User Function ZUsaTlpp()
    Local oCli := Nil

    // sintaxe completa com namespace inline
    oCli := custom.mvc.customer.Customer():New()
    oCli:setCodigo("000001")
    oCli:save()
Return Nil
```

## Anti-padrões

- **Misturar TLPP e ADVPL clássico** no mesmo arquivo `.tlpp` desnecessariamente — compila, mas perde idiomática.
- **Esquecer `endclass`/`endmethod`/`endtry`** — TLPP é stricter que ADVPL, exige fechamento explícito.
- **`Public` global em TLPP** — viola encapsulamento; use `static` na classe ou variável de instância.
- **`throw` sem `try/catch`** no ponto chamador → derruba thread inteira.
- **Annotations sem `tlpp-core.th`** no include → erro de compilação.
- **Nome de identificador > 10 chars** quando consumido por ADVPL `.prw` → quebra na fronteira (`.prw` só usa 10 chars).
- **Namespace `tlpp.*`** → bloqueado pelo compilador (reservado pro core).
- **Modificador default em classe** assumindo PUBLIC (como ADVPL) → métodos sumiriam de chamadas externas (TLPP default é PRIVATE).
- **`StaticCall` em código novo** — deprecado, use namespace direto.
- **Multi inheritance** com `from A, B` — não suportado. Use composition ou interface.

## Cross-references com outras skills

- `[[advpl-fundamentals]]` — 10-char limit em `.prw`, escopos, reservadas.
- `[[advpl-webservice]]` — REST tlppCore (annotations) vs WSRESTFUL clássico.
- `[[advpl-encoding]]` — `.tlpp` é UTF-8 por padrão (vs cp1252 em `.prw`).
- `[[advpl-mvc]]` — Cadastros MVC TLPP-style com `Class ... Inherit FWFormModel`.
- `[[advpl-mvc-avancado]]` — TLPP em PE STRU.
- `[[advpl-advanced]]` — OO avançado, reflection, generics (futuro).
- `[[advpl-debugging]]` — try/catch/throw + ErrorClass para tratamento estruturado.
- `[[plugadvpl-index-usage]]` — `/plugadvpl:find function`, `/plugadvpl:grep "@Get|@Post"`.

## Referência rápida

| Item                       | Sintaxe TLPP                                          |
|----------------------------|-------------------------------------------------------|
| Função tipada              | `function f(string s, numeric n) as logical`          |
| Classe                     | `class Foo` ... `endclass`                            |
| Método de classe           | `method bar() class Foo` ... `endmethod`              |
| Herança                    | `class Bar from Foo`                                  |
| Interface                  | `interface IDoer` + `implements IDoer`                |
| Acesso                     | `public`/`protected`/`private`/`static`               |
| Constructor                | `method New() constructor`                            |
| Super                      | `_Super:New(...)`                                     |
| Try/Catch                  | `try` ... `catch oErr` ... `finally` ... `endtry`     |
| Throw                      | `throw ErrorClass():New(code, msg)`                   |
| Namespace                  | `namespace custom.seg.svc` (no topo)                  |
| Using                      | `using namespace custom.seg.svc`                      |
| Annotation                 | `@Get(endpoint="...")` antes da função/método         |
| JSON build                 | `JsonObject():New()` + `oJ["k"] := v`                 |
| JSON parse                 | `oJ:FromJson(cStr)` retorna `""` ou mensagem de erro  |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <metodo>` — localiza classes/métodos TLPP.
- `/plugadvpl:grep "namespace custom"` — lista namespaces customizados no projeto.
- `/plugadvpl:grep "@Get\|@Post\|@Test"` — lista annotations REST/PROBAT.
- `/plugadvpl:lint <arq.tlpp>` — checagens específicas TLPP.
- `/plugadvpl:arch <arq.tlpp>` — overview de classe + métodos + namespace.

## Referência profunda

Para detalhes completos (~2.4k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Comparativo lado-a-lado TLPP × ADVPL (sintaxe, tipos, OO, exceções).
- Catálogo de annotations padrão (`@Get`, `@Post`, `@Put`, `@Delete`, `@Test`, `@Auth`, `@Cache`, `@Sync`).
- Hierarquia completa de `ErrorClass` e como criar exceções customizadas.
- Reflection API (`FwReflection`, leitura de annotations em runtime).
- TDS (TOTVS Developer Studio) — workflow de compilação, debug, patches via VSCode.
- Estratégias de migração ADVPL → TLPP com armadilhas comuns documentadas.

## Sources

- [Linguagem TLPP ou TL++ - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/28424631692055)
- [Padronização para nomenclaturas TLPP - TDN](https://tdn.totvs.com/pages/releaseview.action?pageId=633537898)
- [TL++ Modificador de Acesso - TOTVS DevForum](https://devforum.totvs.com.br/764-tl-modificador-de-acesso)
- [Herança no TL++ com namespace - TOTVS Forum](https://forum.totvs.io/t/heranca-no-tl-com-namespace/17517)
- [Classe no PRW vs Classe no TLPP - Universo do Desenvolvedor](https://udesenv.com.br/post/advpl-classe-no-prw-vs-classe-no-tlpp)
- [TL++ A Evolução do AdvPL - Six IT](https://sixit.com.br/tl-plus-plus-evolucao-do-advpl/)
- [TL++ REST - Every System](https://everysys.com.br/blog/tl-rest/)
- [TL++ Reflection & Annotation - Every System](https://everysys.com.br/blog/protheus-news-tl-reflection-annotation/)
- [TL++ — O que muda? - Medium](https://medium.com/totvsdevelopers/tl-o-que-muda-ace5781d6c49)
- [Suporte a TLPP no Protheus - TDN](https://tdn.totvs.com/display/public/framework/Suporte+a+TLPP+no+Protheus)
