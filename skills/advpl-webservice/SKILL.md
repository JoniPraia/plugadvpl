---
description: Web Services em ADVPL — REST (WSRESTFUL, @Get/@Post) e SOAP (WSSERVICE/WSMETHOD/WSDATA). NUNCA RpcSetEnv em REST (regra SEC crítica). Use ao criar API ou integração HTTP no Protheus.
---

# advpl-webservice — REST e SOAP no Protheus

ADVPL/TLPP suporta duas formas de Web Service:

- **REST** — preferida hoje. Sintaxe declarativa com `WSRESTFUL` + annotations `@Get`/`@Post`/`@Put`/`@Delete`. Em TLPP, mais limpo ainda com `Class ... Inherit FWRest`.
- **SOAP** — legado, mas vivo. `WSSERVICE` + `WSDATA` + `WSMETHOD` + `WSSTRUCT`.

O AppServer Protheus expõe ambos via porta HTTP configurada em `appserver.ini` (`[HTTPSERVER]`, `[HTTPV11]` para REST).

## Quando usar

- Criar API REST/SOAP no Protheus.
- Edit em fontes com `WSRESTFUL`, `WSSERVICE`, `WSMETHOD`, `WSDATA`, `WSSTRUCT`, `@Get`, `@Post`.
- Integração de Protheus com aplicação externa (mobile, e-commerce, ERP terceiro).
- Revisão de segurança em endpoint exposto (SEC-001, SEC-002).

## REST com WSRESTFUL (TLPP moderno)

```advpl
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Get(endpoint="/v1/cliente/:codigo", description="Busca cliente por código")
User Function GetCliente()
    Local oResp  := JsonObject():New()
    Local cCod   := oRest:GetUrlParam("codigo")
    Local cError := ""

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

## REST com WSRESTFUL (estilo classic)

```advpl
WSRESTFUL XYZCli DESCRIPTION "API de Clientes"

    WSMETHOD GET   DESCRIPTION "Lista clientes"   WSSYNTAX "/api/cli"
    WSMETHOD GET   DESCRIPTION "Busca por codigo" WSSYNTAX "/api/cli/{codigo}"
    WSMETHOD POST  DESCRIPTION "Cria cliente"     WSSYNTAX "/api/cli"

END WSRESTFUL

WSMETHOD GET WSSERVICE XYZCli
    Local cBody := ""
    // ... lógica
    ::SetContentType("application/json")
    ::SetResponse(cBody)
Return .T.

WSMETHOD POST WSSERVICE XYZCli
    Local cInput := ::GetContent()  // ATENÇÃO SEC-002
    // ... lógica com validação
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
    // ... popula
Return .T.
```

## Regra crítica — NUNCA `RpcSetEnv` em REST (SEC-001 família)

`RpcSetEnv` é usado para abrir ambiente Protheus (empresa, filial, usuário) em **JOB/RPC**. **Em REST, o framework já entrega o ambiente** via autenticação HTTP (`token`, `basic auth`) configurada no `appserver.ini`.

```advpl
// ERRADO — risco crítico (SEC-001 família)
@Post(endpoint="/v1/pedido")
User Function CriaPedido()
    RpcSetEnv("01", "0101", "admin", "totvs")  // BLOQUEAR
    // ...
Return .T.

// CORRETO — ambiente já vem da requisição autenticada
@Post(endpoint="/v1/pedido")
User Function CriaPedido()
    Local cEmp := cEmpAnt  // já preenchido pelo framework
    Local cFil := cFilAnt  // já preenchido pelo framework
    // ... lógica
Return .T.
```

Razão: `RpcSetEnv` hardcoded vaza credenciais e bypassa o login do usuário REST. Auditoria perde rastreio.

## Validação de input — SEC-002

`::GetContent()` (classic) / `oRest:GetBodyRequest()` (TLPP) retorna **string raw** do body. **Toda lógica que recebe input externo precisa validar:**

```advpl
@Post(endpoint="/v1/cliente")
User Function CriaCli()
    Local cBody := oRest:GetBodyRequest()
    Local oReq  := JsonObject():New()
    Local cErr  := oReq:FromJson(cBody)

    If !Empty(cErr)
        oRest:SetStatusCode(400)
        oRest:SetResponse('{"error":"JSON invalido"}')
        Return .F.
    EndIf

    // Valida campos obrigatórios + tipos
    If Empty(oReq["codigo"]) .Or. ValType(oReq["codigo"]) != "C"
        oRest:SetStatusCode(422)
        oRest:SetResponse('{"error":"campo codigo obrigatorio"}')
        Return .F.
    EndIf

    // Valida tamanho/range
    If Len(AllTrim(oReq["codigo"])) > TamSX3("A1_COD")[1]
        oRest:SetStatusCode(422)
        oRest:SetResponse('{"error":"codigo excede tamanho"}')
        Return .F.
    EndIf

    // ... agora usa cCod com segurança
Return .T.
```

Violação dispara `SEC-002` (crítico).

## Content-Type e CORS

```advpl
oRest:SetContentType("application/json; charset=utf-8")
oRest:SetHeader("Access-Control-Allow-Origin", "*")          // ajuste conforme política
oRest:SetHeader("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
oRest:SetHeader("Access-Control-Allow-Headers", "Content-Type,Authorization")
```

Endpoints com upload binário usam `application/octet-stream`. JSON é o default.

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

## Configuração appserver.ini (resumo)

```ini
[HTTPV11]
ENABLE=1
PORT=8080
PATH=...

[HTTPURI]
URL=/rest
PrepareIn=99,01
Instances=1,5
CORSEnable=1
AllowOrigin=*
Security=1
```

`Security=1` ativa autenticação obrigatória. **Sempre ative em produção.**

## Anti-padrões

- `RpcSetEnv` em REST → SEC-001 família, vaza credenciais.
- Usar `GetContent()` direto em SQL sem validar → SEC-002 crítico.
- Devolver stack trace na response (`Errorblock`, `Try/Catch` que vaza interno) → vaza estrutura.
- Endpoint sem `Begin Sequence`/`Recover` em operações críticas → 500 sem log estruturado.
- Hardcode de credenciais no fonte (basic auth, token, conn string) → SEC-004 warning.
- Log de body cru com PII em `ConOut` → SEC-003 warning.
- Falta de `oRest:SetStatusCode` → cliente recebe 200 com erro no body (confunde monitoring).

## Referência rápida

| Funcionalidade           | TLPP `@annotation` / Classic `WSMETHOD` |
|--------------------------|------------------------------------------|
| GET                      | `@Get(endpoint="...")` / `WSMETHOD GET`  |
| POST                     | `@Post(endpoint="...")` / `WSMETHOD POST`|
| PUT                      | `@Put` / `WSMETHOD PUT`                  |
| DELETE                   | `@Delete` / `WSMETHOD DELETE`            |
| URL param                | `oRest:GetUrlParam("nome")`              |
| Query string             | `oRest:GetQueryParam("nome")`            |
| Body                     | `oRest:GetBodyRequest()` / `::GetContent()` |
| Header read              | `oRest:GetHeaderRequest("Auth")`         |
| Header write             | `oRest:SetHeader("X-Foo","bar")`         |
| Status                   | `oRest:SetStatusCode(404)`               |
| Response body            | `oRest:SetResponse(cJson)`               |
| Content-Type             | `oRest:SetContentType("application/json")`|

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <WS>` — localiza WSRESTFUL/WSSERVICE.
- A tabela `ws_services` + `ws_structures` no índice cataloga endpoints.
- `/plugadvpl:lint <arq>` — verifica SEC-001, SEC-002 e regras correlatas.

## Referência profunda

Para detalhes completos (~1.5k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Anatomia completa de `WSRESTFUL`/`WSSERVICE`/`WSMETHOD`/`WSDATA`/`WSSTRUCT`.
- Configuração detalhada de `appserver.ini` para REST + SOAP (HTTPV11, HTTPURI, Security, CORS).
- Autenticação Basic/Bearer/OAuth2 e integração com `RestAuthenticator` do framework.
- Catálogo de métodos de `oRest` (TLPP moderno) e `::Self` (classic) com exemplos.
- Padrões de paginação, streaming, upload/download binário em REST.
- Documentação automática via annotations + geração de OpenAPI/Swagger.
