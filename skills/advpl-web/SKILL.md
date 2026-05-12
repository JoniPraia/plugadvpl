---
description: Interfaces web no Protheus — ADVPL ASP (.APH/.APW), módulos web Webex, métodos HTTP GET/POST/HTTPSESSION/COOKIE, threads pool JOB_WEBEX no appserver.ini, portais multi-empresa com RpcSetEnv (aceitável aqui, diferente de REST), upload/download, PEs APWEBEX. Use ao construir UI web Protheus server-rendered. Para REST/JSON, veja advpl-webservice.
---

# advpl-web — Desenvolvimento web no Protheus

ADVPL Web (ASP-style) permite o **AppServer Protheus** atuar como servidor HTTP servindo páginas dinâmicas — sem precisar de IIS/Apache na frente. Usa arquivos `.APH` (ADVPL HTML) ou `.APW` (ADVPL Web Process) que misturam HTML + tags ADVPL embarcadas.

Diferente do REST (skill `[[advpl-webservice]]`), ADVPL Web é **server-rendered**: o servidor monta HTML e devolve ao browser.

## Quando usar

- Usuário pede "página web Protheus", "portal", "tela HTML servida pelo AppServer".
- Edit em `.APH` (ADVPL HTML) ou `.APW` (ADVPL Web Process).
- Funções `ApWebEx*`, `WebPageOpen`, `WebPageProc`, `HTTPGet`, `HTTPPost`.
- Portal multi-empresa/filial com login.
- Upload/download de arquivos via HTTP no AppServer.
- **NÃO** use para API REST/JSON — para isso veja `[[advpl-webservice]]`.

## Arquivos .APH — ADVPL HTML server-rendered

```html
<%
    #include "apwebex.ch"
    Local cCod := HTTPGet("cod")
    DbSelectArea("SA1")
    DbSetOrder(1)
    DbSeek(xFilial("SA1") + cCod)
%>
<html>
<head><title>Cliente</title></head>
<body>
    <h1>Cliente: <%= SA1->A1_COD %></h1>
    <p>Nome: <%= AllTrim(SA1->A1_NOME) %></p>
    <% If !Empty(SA1->A1_CGC) %>
        <p>CNPJ: <%= SA1->A1_CGC %></p>
    <% EndIf %>
</body>
</html>
```

Sintaxe:

- `<% código ADVPL %>` — bloco ADVPL (executa, não imprime).
- `<%= expressao %>` — escreve resultado da expressão no HTML.

> **Include obrigatório:** `#include "apwebex.ch"` — sem ele, o ADVPL compila mas as funções `HTTPGet`/`HTTPPost`/etc. não resolvem.

## Diferença .APH × .APW

| Extensão | Pra que serve                                     |
|----------|---------------------------------------------------|
| `.APH`   | Página web HTML server-rendered (mistura HTML + ADVPL) |
| `.APW`   | Processo Web — User Function pura, responde request sem template HTML embarcado |

`.APW` é mais usado pra endpoints que respondem JSON/XML ou processam form sem retornar página completa. `.APH` é o "ASP-style" tradicional.

## Configuração appserver.ini para Web

```ini
[HTTPSERVER]
ENABLE=1
PORT=8080
PATH=C:\TOTVS\Protheus_Data\Web
RESPONSEJOB=JOB_WEBEX

[JOB_WEBEX]
TYPE=webex
ENVIRONMENT=ENVIRONMENT
INSTANCES=1,5                     ; min,max threads
ONSTART=STARTWEBEX                ; chamado ao criar thread
ONCONNECT=CONNECTWEBEX            ; chamado a cada request
ONEXIT=FINISHWEBEX                ; chamado ao destruir thread
SOURCEPATH=C:\TOTVS\Protheus_Data\Web\Apw
```

- `PATH` aponta para diretório raiz de `.APH`. URL `http://host:8080/index.aph` serve `<PATH>/index.aph`.
- `INSTANCES=1,5` mantém pool de 1 a 5 threads ADVPL pré-aquecidas pra responder requests.
- `ONSTART`/`ONCONNECT`/`ONEXIT` são User Functions de hook do ciclo de vida da thread Webex.

## Métodos de transporte HTTP

| Método           | Função para ler              | Para que serve                       |
|------------------|------------------------------|--------------------------------------|
| GET (querystring)| `HTTPGet("nome")`            | URL params, links                    |
| POST (form)      | `HTTPPost("nome")`           | Submissão de formulário              |
| Session          | `HTTPSession("chave")`       | Estado entre requests (login)        |
| Cookie           | `HTTPCookie("nome")`         | Preferências, tracking               |
| Header read      | `HTTPHeadIn("Authorization")`| Auth, content-type, REMOTE_PORT     |
| Header write     | `HTTPHeadOut("X-Foo", "bar")` | Custom headers                      |
| Content-Type     | `HTTPContentType("text/html")`| Define MIME da response             |
| Redirect         | `WebRedir("destino.aph")`    | 302 Location                         |
| Upload           | `HTTPUpload("campo", "dir")` | Recebe arquivo multipart            |
| Send file        | `WebSendFile("path.pdf")`    | Stream de arquivo binário            |

## Portal multi-empresa com login

```advpl
<%
    #include "apwebex.ch"

    Local cUser  := HTTPPost("user")
    Local cPass  := HTTPPost("pass")
    Local cEmp   := HTTPPost("emp")
    Local cFil   := HTTPPost("fil")

    If ValidUser(cUser, cPass)
        // Persiste contexto na session
        HTTPSession("USR", cUser)
        HTTPSession("EMP", cEmp)
        HTTPSession("FIL", cFil)

        // ADVPL Web aceita RpcSetEnv (diferente de REST onde dispara SEC-001)
        // Cada request reabre o contexto baseado na session.
        RpcSetEnv(cEmp, cFil, cUser, cPass)

        WebRedir("home.aph")
    Else
        WebRedir("login.aph?err=1")
    EndIf
%>
```

> **Importante:** em ADVPL Web ASP-style, `RpcSetEnv` é aceitável (diferente de REST onde é proibido — `SEC-001` impl). A diferença é que o threading model Webex carrega ambiente per-request, então é o caminho oficial. Em REST 2.0, `PrepareIn` + `TenantId` resolvem sem precisar de `RpcSetEnv`.

## Upload / Download de arquivos

```advpl
// Upload — recebe multipart/form-data, grava em diretorio configurado
<%
    Local cFile := HTTPUpload("arquivo", "C:\TOTVS\Uploads\")
    If !Empty(cFile)
        // arquivo gravado em cFile (path completo)
        HTTPContentType("text/html")
        ShowResultado("Arquivo recebido: " + cFile)
    Else
        ShowResultado("Falha no upload")
    EndIf
%>

// Download — serve arquivo binario com nome amigavel
<%
    HTTPContentType("application/pdf")
    HTTPHeadOut("Content-Disposition", "attachment; filename=relatorio.pdf")
    WebSendFile("C:\TOTVS\Relatorios\rel.pdf")
%>
```

> **Cuidado com path traversal:** `WebSendFile(HTTPGet("file"))` direto é vulnerável — usuário pode passar `../../config/appserver.ini`. Sempre valide path: normalize, restrinja diretório raiz, blacklist `../`.

## Pontos de Entrada APWEBEX

PEs específicas para o pipeline Web (ver tabela em `appserver.ini` acima):

| PE             | Quando                                          |
|----------------|-------------------------------------------------|
| `APWEBINI` / `STARTWEBEX` | Inicialização da thread Web              |
| `APWEBLOG`     | Login do usuário web (autenticação custom)      |
| `APWEBOUT` / `FINISHWEBEX` | Fim do processamento de uma requisição |
| `APWEBVLD`     | Validação custom de sessão (cada request)       |
| `CONNECTWEBEX` | Hook a cada nova conexão                        |

Veja `[[advpl-pontos-entrada]]` pra padrão geral de PE; `APWEBEX` segue o mesmo modelo (`User Function NOME()` + `PARAMIXB[]`).

## XSS — escapar HTML em variáveis do usuário

```advpl
// VULNERAVEL — input do usuario rendera como HTML
<p>Olá <%= HTTPGet("nome") %>!</p>

// CORRETO — escapar antes de render
Function HTMLEscape(cStr)
    Local cOut := cStr
    cOut := StrTran(cOut, "&", "&amp;")
    cOut := StrTran(cOut, "<", "&lt;")
    cOut := StrTran(cOut, ">", "&gt;")
    cOut := StrTran(cOut, '"', "&quot;")
    cOut := StrTran(cOut, "'", "&#39;")
Return cOut

<p>Olá <%= HTMLEscape(HTTPGet("nome")) %>!</p>
```

## Encoding em ADVPL Web

`.APH` segue o mesmo padrão dos fontes ADVPL — tipicamente cp1252. Mas o browser espera UTF-8 hoje em dia. Set Content-Type explícito:

```advpl
<%
    HTTPContentType("text/html; charset=ISO-8859-1")  // cp1252 / latin-1
    // OU
    HTTPContentType("text/html; charset=UTF-8")
    // Se UTF-8, converta a saida:
    cHtml := EncodeUTF8(cHtml)
%>
```

Mismatch causa mojibake (`Ã§`, `Ã£` no browser). Veja `[[advpl-encoding]]`.

## Anti-padrões

- **Lógica de negócio no `.APH`** em vez de extrair `User Function` → vira spaghetti impossível de manter/testar.
- **Não validar `HTTPGet`/`HTTPPost`** antes de usar em SQL → SQL injection. Use `%exp:cVar%` em BeginSql.
- **Não escapar HTML** em variáveis vindas do usuário → XSS. Sempre `HTMLEscape()`.
- **Esquecer `HTTPSession`** para autenticação — exposição de página sem login.
- **`MsgInfo`/`Alert` no `.APH`** → tenta abrir UI no servidor (não funciona, trava thread).
- **`WebSendFile` com path concatenando input** do usuário → path traversal vulnerability.
- **Sem `HTTPContentType` explícito** → browser pode escolher charset errado, mojibake.
- **Logs com PII** no `console.log` durante request — visível em `tail -f`. Use `FwLogMsg` com mascarar.
- **`RpcSetEnv` sem `RpcClearEnv`** no fim — thread fica com env carregado, próxima request herda contexto errado.
- **Stateful em variável `Static`** dentro de thread Webex — request 2 da mesma thread herda estado da request 1 (memória vazada).

## Cross-references com outras skills

- `[[advpl-webservice]]` — pra REST/JSON, não use `.APH`/`HTTPGet`.
- `[[advpl-pontos-entrada]]` — APWEBEX PEs seguem padrão User Function PARAMIXB.
- `[[advpl-encoding]]` — `.APH` cp1252 + Content-Type UTF-8 obriga `EncodeUTF8`.
- `[[advpl-jobs-rpc]]` — `RpcSetEnv` é OK em Web mas tem padrão de uso (RpcClearEnv).
- `[[advpl-embedded-sql]]` — SQL injection via `HTTPGet` é o mesmo padrão do REST.
- `[[advpl-code-review]]` — SEC-001 não fira em `.APH` (impl é REST-specific), mas SQL injection ainda é problema real.
- `[[advpl-debugging]]` — debug de session/cookie/upload via ConOut em ONCONNECT.
- `[[plugadvpl-index-usage]]` — `/plugadvpl:grep "<%.*%>"` localiza `.APH`.

## Referência rápida

| Função / Comando            | Para que serve                                       |
|-----------------------------|------------------------------------------------------|
| `<% código %>`              | Bloco ADVPL no `.APH` (executa, não imprime)         |
| `<%= expr %>`               | Imprime resultado no HTML                            |
| `#include "apwebex.ch"`     | Header mandatório pra resolver `HTTPGet`/etc.        |
| `HTTPGet("nome")`           | Lê querystring                                       |
| `HTTPPost("nome")`          | Lê POST form field                                   |
| `HTTPSession("chave")`      | Set/get session value (login state)                  |
| `HTTPCookie("nome")`        | Set/get cookie                                       |
| `HTTPHeadIn("X-Foo")`       | Lê header de request                                 |
| `HTTPHeadOut("X-Foo","bar")`| Set header de response                               |
| `HTTPContentType("...")`    | Set Content-Type da response                         |
| `WebRedir("destino.aph")`   | Redirect 302                                         |
| `HTTPUpload("c","dir")`     | Recebe upload multipart                              |
| `WebSendFile("path")`       | Stream arquivo binário                               |
| `RpcSetEnv(cEmp,cFil,...)`  | Abre contexto Protheus (OK em Web, NÃO em REST)      |
| `EncodeUTF8(cStr)`          | Converte cp1252 → UTF-8 antes de devolver            |
| `JOB_WEBEX` em ini          | Section do appserver pra thread pool web             |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function ApWebEx` — funções web no projeto.
- `/plugadvpl:grep "<%.*%>"` — localiza fontes `.APH`/`.APW`.
- `/plugadvpl:grep "HTTPGet\|HTTPPost"` — handlers de input web.
- `/plugadvpl:grep "RpcSetEnv"` — auditoria (deve aparecer em web/job, NÃO em REST).
- `/plugadvpl:lint <arq>` — checagens gerais; `.APH` específico depende da indexação.

## Referência profunda

Para detalhes completos (~2.4k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Apostila ADVPL Web completa (TOTVS) com módulos, threads, configuração HTTPSERVER/WEBEX.
- Catálogo de atributos HTML de input suportados em `.APH`.
- Lista completa de funções `ApWebEx*` (envio de e-mail, formatação, conversão).
- Padrão de gravação de dados via web (transações, controle de concorrência).
- Página Modelo 2/Modelo 3 web (CRUD HTML automático).
- Relatórios na Web (impressão server-side enviada por download).
- Catálogo completo de PEs APWEBEX (`APWEBINI`/`APWEBLOG`/`APWEBOUT`/`APWEBVLD`).

## Sources

- [Protheus e AdvPL ASP - Parte 01 - Tudo em AdvPL](https://siga0984.wordpress.com/2018/11/12/protheus-e-advpl-asp-parte-01/)
- [Microsiga AdvPL Web Services Estrutura APWEBEX (PDF)](https://www.scribd.com/doc/164293393/Advpl-WebServices-Estrutura-APWEBEX)
- [Configuração de Portais e WebServices - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360026453811)
- [WebServices - Tudo em AdvPL Tag](https://siga0984.wordpress.com/tag/webservices/)
- [appserver.ini examples - ndserra/advpl GitHub](https://github.com/ndserra/advpl/blob/master/_AULAS/appserver.ini)
