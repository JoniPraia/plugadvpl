---
description: Web Services em ADVPL/TLPP — REST clássico (WSRESTFUL) vs REST tlppCore (annotations @Get/@Post) vs SOAP (WSSERVICE). PrepareIn + TenantId pra multi-tenancy. JWT via /api/oauth2/v1/token. NUNCA RpcSetEnv em endpoint REST. Use ao criar/editar API REST/SOAP, integrar Protheus com sistema externo, ou revisar SEC-001 (RpcSetEnv em REST).
---

# advpl-webservice — REST e SOAP no Protheus

ADVPL/TLPP suporta três famílias de Web Service:

| Família           | Sintaxe                                    | Quando usar                                    |
|-------------------|--------------------------------------------|------------------------------------------------|
| **REST clássico** | `WSRESTFUL` + `WSMETHOD GET/POST`           | Mantida pra compat; ainda OK em código existente |
| **REST tlppCore** | `@Get(endpoint=...)` em `User Function`     | **Padrão moderno para novas APIs** (TLPP 17.3+) |
| **SOAP**          | `WSSERVICE` + `WSDATA` + `WSMETHOD`         | Legado; integração com sistema que exige WSDL  |

REST tlppCore **não é evolução do REST ADVPL** — é recurso novo, sem compat automática com autenticação user-based clássica nem pré-carga de banco. Cada cenário tem trade-offs.

O AppServer Protheus expõe ambos via porta HTTP configurada em `appserver.ini` (`[HTTPV11]` para REST 2.0).

## Quando usar

- Criar API REST/SOAP no Protheus.
- Edit em fontes com `WSRESTFUL`, `WSSERVICE`, `WSMETHOD`, `WSDATA`, `WSSTRUCT`, `@Get`, `@Post`.
- Integração de Protheus com aplicação externa (mobile, e-commerce, ERP terceiro).
- Revisão de segurança em endpoint exposto — `SEC-001` (impl: `RpcSetEnv` em REST).
- Consumir API externa do dentro do Protheus (`FwRest`, `HttpPost`).

## REST tlppCore (TLPP moderno, recomendado)

Estrutura **function-based** com annotations. Mais limpo, sem precisar de classe:

```advpl
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Get(endpoint="/v1/cliente/:codigo", description="Busca cliente por codigo")
User Function GetCliente()
    Local oResp  := JsonObject():New()
    Local cCod   := oRest:GetUrlParam("codigo")

    If Empty(cCod)
        oRest:SetStatusCode(400)
        oResp["error"] := "Codigo obrigatorio"
        oRest:SetResponse(oResp:ToJson())
        Return .F.
    EndIf

    DbSelectArea("SA1")
    SA1->(DbSetOrder(1))
    If SA1->(DbSeek(xFilial("SA1") + cCod))
        oResp["codigo"] := SA1->A1_COD
        oResp["nome"]   := AllTrim(SA1->A1_NOME)
        oResp["cnpj"]   := SA1->A1_CGC
        oRest:SetStatusCode(200)
    Else
        oRest:SetStatusCode(404)
        oResp["error"] := "Cliente nao encontrado"
    EndIf

    oRest:SetResponse(oResp:ToJson())
Return .T.
```

## REST clássico (WSRESTFUL)

```advpl
WSRESTFUL XYZCli DESCRIPTION "API de Clientes"

    WSMETHOD GET   DESCRIPTION "Lista clientes"   WSSYNTAX "/api/cli"
    WSMETHOD GET   DESCRIPTION "Busca por codigo" WSSYNTAX "/api/cli/{codigo}"
    WSMETHOD POST  DESCRIPTION "Cria cliente"     WSSYNTAX "/api/cli"

END WSRESTFUL

WSMETHOD GET WSSERVICE XYZCli
    Local cBody := ""
    // ... logica
    ::SetContentType("application/json")
    ::SetResponse(cBody)
Return .T.

WSMETHOD POST WSSERVICE XYZCli
    Local cInput := DecodeUTF8(::GetContent())   // converte UTF-8 -> cp1252
    // ... validacao + logica
Return .T.
```

## SOAP com WSSERVICE

```advpl
WSSERVICE XYZSrv DESCRIPTION "Servico XYZ"
    WSDATA cCodCliente AS STRING
    WSDATA oCliente    AS XYZCliRet

    WSMETHOD BuscaCliente DESCRIPTION "Busca cliente por codigo"
END WSSERVICE

WSSTRUCT XYZCliRet
    WSDATA cCodigo AS STRING
    WSDATA cNome   AS STRING
    WSDATA nLimite AS NUMERIC
END WSSTRUCT

WSMETHOD BuscaCliente WSRECEIVE cCodCliente WSSEND oCliente WSSERVICE XYZSrv
    ::oCliente := WSClassNew("XYZCliRet")
    ::oCliente:cCodigo := cCodCliente
    ::oCliente:cNome   := "Cliente Teste"
    ::oCliente:nLimite := 5000
Return .T.
```

## Multi-tenancy: `PrepareIn` + `TenantId`

Para REST suportar múltiplas empresas/filiais sem `RpcSetEnv`:

**1.** No `appserver.ini`, declare `PrepareIn` por sócket REST:

```ini
[HTTPV11]
ENABLE=1
PORT=8080

[HTTPURI]
URL=/rest
PrepareIn=99,01     ; carrega ambiente Empresa 99 Filial 01 pra cada request
Instances=1,5       ; min,max threads (cada thread já vem com env carregado)
CORSEnable=1
Security=1          ; obriga autenticacao (sempre ative em producao!)
```

**2.** Cliente passa empresa/filial no header `TenantId`:

```http
POST /rest/v1/pedido HTTP/1.1
Host: protheus.cliente.com:8080
Authorization: Bearer eyJhbGciOi...
TenantId: 99,01            ; empresa,filial
Content-Type: application/json
```

**3.** No endpoint, `cEmpAnt` / `cFilAnt` já estão preenchidos:

```advpl
@Post(endpoint="/v1/pedido")
User Function CriaPedido()
    // cEmpAnt e cFilAnt JA vem do PrepareIn + TenantId — sem RpcSetEnv
    ConOut("Pedido criado em " + cEmpAnt + "/" + cFilAnt)
    // ...
Return .T.
```

## Autenticação JWT (Bearer Token)

REST 2.0 do Protheus tem endpoint built-in pra issuance de token:

```http
POST /api/oauth2/v1/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=admin&password=totvs
```

Retorno:

```json
{
  "access_token": "eyJhbGciOi...",
  "expires_in": 3600,
  "token_type": "bearer",
  "refresh_token": "..."
}
```

Cliente usa em todas as requests subsequentes:

```http
GET /rest/v1/cliente/000001
Authorization: Bearer eyJhbGciOi...
```

Configurar JWT em `appserver.ini`:

```ini
[HTTPURI]
Security=1
JWTSecret=meu-segredo-super-longo-do-cliente
```

## Regra crítica: NUNCA `RpcSetEnv` em REST (`SEC-001` impl)

`RpcSetEnv` é usado para abrir ambiente Protheus em **JOB/RPC** (veja `[[advpl-jobs-rpc]]`). **Em REST, o framework já entrega o ambiente** via `PrepareIn` + `TenantId`.

```advpl
// ERRADO — SEC-001 critical (impl real: RpcSetEnv em WSRESTFUL)
@Post(endpoint="/v1/pedido")
User Function CriaPedido()
    RpcSetEnv("01", "0101", "admin", "totvs")   // BLOQUEAR! Lint SEC-001 dispara
    // ...
Return .T.

// CORRETO — ambiente ja vem da requisicao autenticada via TenantId
@Post(endpoint="/v1/pedido")
User Function CriaPedido()
    Local cEmp := cEmpAnt     // ja preenchido pelo PrepareIn
    Local cFil := cFilAnt
    // ... logica
Return .T.
```

Razão: `RpcSetEnv` hardcoded vaza credenciais, bypassa o login do usuário REST, e mata auditoria — não há rastro de quem realmente fez a operação.

## Validação de input (boa prática + `SEC-002` catalog)

> **Nota:** `SEC-002` na **implementação atual** detecta "User Function sem prefixo" (não validação de input). A regra "GetContent sem validação" está **catalogada mas não detectada**. De qualquer forma, validar input é mandatório.

```advpl
@Post(endpoint="/v1/cliente")
User Function CriaCli()
    Local cBody := DecodeUTF8(oRest:GetBodyRequest())   // converte UTF-8 -> cp1252
    Local oReq  := JsonObject():New()
    Local cErr  := oReq:FromJson(cBody)

    If !Empty(cErr)
        oRest:SetStatusCode(400)
        oRest:SetResponse('{"error":"JSON invalido: ' + cErr + '"}')
        Return .F.
    EndIf

    // Valida campos obrigatorios + tipos
    If Empty(oReq["codigo"]) .Or. ValType(oReq["codigo"]) != "C"
        oRest:SetStatusCode(422)
        oRest:SetResponse('{"error":"campo codigo obrigatorio"}')
        Return .F.
    EndIf

    // Valida tamanho/range usando o proprio SX3 como verdade
    If Len(AllTrim(oReq["codigo"])) > TamSX3("A1_COD")[1]
        oRest:SetStatusCode(422)
        oRest:SetResponse('{"error":"codigo excede tamanho do SX3"}')
        Return .F.
    EndIf

    // ... agora usa oReq["codigo"] com seguranca
    // CUIDADO: ao usar em SQL, sempre %exp:cVar% — veja [[advpl-embedded-sql]]
Return .T.
```

## Content-Type e CORS

```advpl
oRest:SetContentType("application/json; charset=utf-8")
oRest:SetHeader("Access-Control-Allow-Origin",  "*")          // ajuste conforme politica
oRest:SetHeader("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
oRest:SetHeader("Access-Control-Allow-Headers", "Content-Type,Authorization,TenantId")
```

Endpoints com upload binário usam `application/octet-stream`. JSON é o default.

> CORS é declarado uma vez no `appserver.ini` (`CORSEnable=1`, `AllowOrigin=*`) e propagado automaticamente. Override no method só se precisar de policy específica.

## Retorno de erro padronizado

Convenção: sempre devolva JSON com `error` + `code`:

```json
{
  "error": "Cliente nao encontrado",
  "code": "CLI_NOT_FOUND",
  "details": {"codigo": "999999"}
}
```

Mapeie status HTTP:

| Status | Quando                                                |
|--------|-------------------------------------------------------|
| 200    | OK                                                    |
| 201    | Criado (POST com sucesso)                             |
| 204    | OK sem body (DELETE)                                  |
| 400    | Body malformado (JSON invalido)                       |
| 401    | Não autenticado                                       |
| 403    | Autenticado mas sem permissão                         |
| 404    | Recurso não encontrado                                |
| 409    | Conflito (registro já existe)                         |
| 422    | Validação de negócio falhou                           |
| 500    | Erro interno (logge stack, NUNCA exponha em resposta) |

## Encoding em REST — `EncodeUTF8`/`DecodeUTF8`

REST é UTF-8 nativo; fontes ADVPL clássicos (`.prw`) são cp1252. Conversão é mandatória nos boundaries:

```advpl
// Lendo body REST (entra UTF-8, fonte é cp1252)
Local cBody := DecodeUTF8(oRest:GetBodyRequest())

// Escrevendo response (saída UTF-8, fonte é cp1252)
oRest:SetResponse(EncodeUTF8('{"nome":"' + AllTrim(SA1->A1_NOME) + '"}'))
```

Sem isso, acentos viram `Ã§`/`Ã£` no consumidor. Veja `[[advpl-encoding]]`.

## Anti-padrões

- **`RpcSetEnv` em REST** → `SEC-001` crítico (impl real). Use `PrepareIn` + `TenantId`.
- **`GetContent()` direto em SQL** sem validação ou bind (`%exp:`) → SQL injection (catálogo `SEC-001` legacy).
- **Devolver stack trace na response** (`Errorblock` que vaza interno) → expõe estrutura.
- **Endpoint sem `Begin Sequence`/`Recover`** em operações críticas → 500 sem log estruturado.
- **Hardcode de credenciais no fonte** (basic auth, token, conn string) → SEC-004 (catálogo).
- **Log de body cru com PII** em `ConOut` → SEC-003 (catálogo).
- **Falta de `oRest:SetStatusCode`** → cliente recebe 200 com erro no body (confunde monitoring).
- **Esquecer `EncodeUTF8`/`DecodeUTF8`** nos boundaries cp1252 ↔ UTF-8 → acentos quebram.
- **`PrepareIn` em produção apontando empresa de teste** → request multi-tenant cai no ambiente errado.
- **`Security=0` em produção** → endpoint público sem auth.
- **CORS `*` em endpoint que escreve** sem validação de origin → CSRF.

## Referência rápida

| Funcionalidade           | TLPP `@annotation` / Classic `WSMETHOD`               |
|--------------------------|--------------------------------------------------------|
| GET                      | `@Get(endpoint="...")` / `WSMETHOD GET`                |
| POST                     | `@Post(endpoint="...")` / `WSMETHOD POST`              |
| PUT                      | `@Put` / `WSMETHOD PUT`                                |
| DELETE                   | `@Delete` / `WSMETHOD DELETE`                          |
| OPTIONS (CORS preflight) | `@Options` / `WSMETHOD OPTIONS`                        |
| URL param                | `oRest:GetUrlParam("nome")`                            |
| Query string             | `oRest:GetQueryParam("nome")`                          |
| Body                     | `oRest:GetBodyRequest()` / `::GetContent()`            |
| Header read              | `oRest:GetHeaderRequest("Auth")`                       |
| Header write             | `oRest:SetHeader("X-Foo","bar")`                       |
| Status                   | `oRest:SetStatusCode(404)`                             |
| Response body            | `oRest:SetResponse(cJson)`                             |
| Content-Type             | `oRest:SetContentType("application/json")`             |
| User logado              | `oRest:GetUserName()`                                  |
| JSON parse               | `JsonObject():New()` + `oJ:FromJson(cBody)`            |
| JSON build               | `oJ["chave"] := val` + `oJ:ToJson()`                   |

## Cross-references com outras skills

- `[[advpl-tlpp]]` — namespace e classes pra REST tlppCore.
- `[[advpl-encoding]]` — `EncodeUTF8`/`DecodeUTF8` obrigatórios em REST cp1252.
- `[[advpl-code-review]]` — `SEC-001` (RpcSetEnv em REST), `SEC-002`/`SEC-003`/`SEC-004` (catalog).
- `[[advpl-embedded-sql]]` — SQL injection prevention; nunca concat input REST em query.
- `[[advpl-jobs-rpc]]` — `RpcSetEnv` correto pra jobs (vs REST).
- `[[advpl-fundamentals]]` — `User Function` sem prefixo cliente em endpoint (exceção justificada se padrão WSRESTFUL).
- `[[advpl-mvc]]` — `FWMVCRotAuto` chamado de dentro de REST (PE pattern).
- `[[advpl-dicionario-sx]]` — `TamSX3()` pra validar tamanho de input via SX3.
- `[[advpl-debugging]]` — REST 500 / response vazio / encoding bagunçado.
- `[[plugadvpl-index-usage]]` — tabela `rest_endpoints` lista todos WSRESTFUL/WSMETHOD do projeto.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <WS>` — localiza WSRESTFUL/WSSERVICE.
- `/plugadvpl:grep "WSRESTFUL\|@Get\|@Post"` — encontra endpoints novos.
- `/plugadvpl:grep "RpcSetEnv"` — auditoria SEC-001 (não deve aparecer dentro de REST).
- Tabela `rest_endpoints` (não "ws_services") do índice cataloga endpoints.
- Tabela `http_calls` cataloga consumo de APIs externas (`FwRest`, `HttpPost`).
- `/plugadvpl:lint <arq>` — verifica SEC-001 (RpcSetEnv em REST) impl real.

## Referência profunda

Para detalhes completos (~1.5k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Anatomia completa de `WSRESTFUL`/`WSSERVICE`/`WSMETHOD`/`WSDATA`/`WSSTRUCT`.
- Configuração detalhada de `appserver.ini` para REST + SOAP (HTTPV11, HTTPURI, Security, CORS, JWT).
- Autenticação Basic/Bearer/OAuth2 e integração com `RestAuthenticator` do framework.
- Catálogo de métodos de `oRest` (TLPP moderno) e `::Self` (classic) com exemplos.
- Padrões de paginação, streaming, upload/download binário em REST.
- Documentação automática via annotations + geração de OpenAPI/Swagger.
- Consumo de APIs externas (`FwRest`, `HttpPost`, autenticação OAuth2 client-side).

## Sources

- [TL++ REST - Every System](https://everysys.com.br/blog/tl-rest/)
- [Diferença REST clássico vs Annotation - Terminal de Informação](https://terminaldeinformacao.com/2023/07/12/qual-diferenca-do-rest-classico-com-o-annotation/)
- [Migração WsRESTful para REST tlppCore - TDN](https://tdn.totvs.com/pages/viewpage.action?pageId=553337101)
- [Entendendo as novidades do REST - TDN](https://tdn-homolog.totvs.com/display/public/framework/Entendendo+as+novidades+do+REST)
- [Requisição para Token JWT REST - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360044883213)
- [REST com segurança - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/8919254403735)
- [PrepareIn / TenantId - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/4410465974167)
- [Criando WebService REST WsRestFul - Maratona AdvPL TL++ 535](https://terminaldeinformacao.com/2024/07/13/criando-um-webservice-rest-com-wsrestful-maratona-advpl-e-tl-535/)
- [Consumindo APIs externas REST - Terminal de Informação](https://terminaldeinformacao.com/2025/06/28/consumindo-apis-externas-em-rest-com-e-sem-token-no-protheus-via-advpl-tlpp-ti-especial-0005/)
