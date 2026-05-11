---
description: TLPP (TOTVS Language Plus Productive) — sucessor moderno do ADVPL com OO completa, namespaces, annotations @Get/@Post/@Test, JSON nativo, try/catch, reflection. Use ao trabalhar com arquivos .tlpp/.th, código TLPP novo, REST moderno, classes com herança/interfaces, ou migração ADVPL→TLPP.
---

# advpl-tlpp — TLPP (TOTVS Language Plus Productive)

**TLPP** é a evolução moderna do ADVPL lançada pela TOTVS para suportar paradigmas atuais: orientação a objetos completa, namespaces, annotations, exceções estruturadas, JSON nativo, reflection. Coexiste com ADVPL no mesmo RPO/tlpp.rpo — código TLPP chama ADVPL e vice-versa.

## Quando usar

- Edit/criação de arquivos `.tlpp` ou `.th` (header TLPP).
- Endpoints REST com annotations (`@Get`, `@Post`, `@Put`, `@Delete`).
- Classes com herança, interfaces, modificadores de acesso (`public`/`protected`/`private`).
- Testes unitários com PROBAT (`@Test`, `@Before`, `@After`).
- Migração ADVPL → TLPP.
- Uso de `JsonObject`, `try`/`catch`/`finally`, `throw`.

## Extensões e includes

- `.tlpp` — fonte TLPP (compilado para `tlpp.rpo`).
- `.th` — header TLPP (substitui `.ch` do ADVPL).
- Includes essenciais:
  - `#include "tlpp-core.th"` — features básicas (try/catch, JsonObject, annotations).
  - `#include "tlpp-rest.th"` — annotations REST.
  - `#include "tlpp-object.th"` — classes/interfaces.

## Tipagem opcional e parâmetros nomeados

```tlpp
function processOrder(string cNumero, numeric nValor := 0.00, boolean lEmite := .T.) as logical
    return .T.
endfunction
```

Tipos: `string`, `numeric`, `boolean`, `date`, `array`, `object`, `codeblock`, `json`, `character`, `logical`.

## Namespaces

```tlpp
namespace custom.mvc.customer

class Customer
    public data cCodigo as string
    method New() constructor
    method save() as logical
endclass
```

`using namespace custom.mvc.customer` no consumidor. Convenção: minúsculo, dot-separated, começa pelo cliente.

## Orientação a objetos completa

```tlpp
class Vehicle
    public  data cPlate    as string
    private data nMileage  as numeric
    protected data dService as date

    public method New(cPlate) constructor
    public method getInfo() as string
    protected method updateService(dDate) as logical
endclass

method New(cPlate) class Vehicle
    self:cPlate := cPlate
endmethod

method getInfo() class Vehicle
return "Vehicle: " + self::cPlate
```

- Herança: `class Car from Vehicle`.
- Interfaces: `interface IPrintable` + `class Foo implements IPrintable`.
- Métodos estáticos: `static method utility() class Foo`.

## Annotations

```tlpp
@Get(endpoint="/v1/customer/:id", description="Get customer by id")
@Auth(roles="admin,seller")
user function getCustomer()
    local cId := oRest:GetUrlParam("id")
    // ...
return .T.
```

Annotations customizadas via reflection:

```tlpp
@MyAnnotation(value="x")
function foo()
    // descobrível via FwReflection
endfunction
```

## REST moderno (FWRest)

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
        throw ErrorClass():New("400", "ID obrigatório")
    endif
    // ...
catch oErr
    conout("Erro: " + oErr:getDescription())
    oRest:SetStatusCode(500)
finally
    if oFile != nil
        oFile:close()
    endif
endtry
```

`ErrorClass` permite codes estruturados (HTTP-style).

## JSON nativo

```tlpp
local oJson := JsonObject():New()
oJson["nome"]  := "ACME"
oJson["itens"] := {1, 2, 3}
oJson["sub"]   := JsonObject():New()
oJson["sub"]["x"] := 10

local cStr := oJson:ToJson()
local cErr := oJson:FromJson(cInput)
```

Listas: `array` nativo. Booleano: `.T./.F.`. Null: `nil`.

## PROBAT — testes unitários

```tlpp
@Test
function testAddition()
    local nResult := 2 + 2
    paAssertEqual(4, nResult, "2+2 deve ser 4")
endfunction
```

Rode via TDS ou `tdscli probat`.

## Interoperabilidade com ADVPL

- TLPP chama ADVPL: chamada direta de `User Function` ADVPL existente.
- ADVPL chama TLPP: precisa `using namespace` no fonte TLPP exportado; ADVPL chama `MyClass():New()` se a classe for compilada.
- `StaticCall` está deprecado em TLPP — use namespaces.

## Anti-padrões

- Misturar TLPP e ADVPL clássico no mesmo arquivo `.tlpp` desnecessariamente (compila, mas perde idiomática).
- Esquecer `endclass`/`endmethod` — TLPP é stricter que ADVPL.
- `Public` global em TLPP — viola encapsulamento; use `static` na classe.
- `throw` sem `try/catch` no ponto chamador → derruba thread.
- Annotations sem `tlpp-core.th` no include → erro de compilação.

## Referência profunda

Para detalhes completos (~2.4k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Comparativo lado-a-lado TLPP × ADVPL (sintaxe, tipos, OO, exceções).
- Catálogo de annotations padrão (`@Get`, `@Post`, `@Put`, `@Delete`, `@Test`, `@Auth`, `@Cache`, `@Sync`).
- Hierarquia completa de `ErrorClass` e como criar exceções customizadas.
- Reflection API (`FwReflection`, leitura de annotations em runtime).
- TDS (TOTVS Developer Studio) — workflow de compilação, debug, patches via VSCode.
- Estratégias de migração ADVPL → TLPP com armadilhas comuns documentadas.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <metodo>` — localiza classes/métodos TLPP.
- `/plugadvpl:lint <arq.tlpp>` — checagens específicas TLPP.
- `/plugadvpl:grep "@Get|@Post"` — lista endpoints REST.
