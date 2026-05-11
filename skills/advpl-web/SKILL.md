---
description: Interfaces web no Protheus — ADVPL ASP (.APH), módulos web Webex/SmartClient HTML, métodos HTTP GET/POST/HTTPSESSION/COOKIE, portais multi-empresa, upload/download via HTTP. Use ao construir UI web Protheus, .APH, ApWebEx, ou portais HTTP (não REST/API — para isso veja advpl-webservice).
---

# advpl-web — Desenvolvimento web no Protheus

ADVPL Web (ASP-style) permite o **AppServer Protheus** atuar como servidor HTTP servindo páginas dinâmicas — sem precisar de IIS/Apache na frente. Usa arquivos `.APH` (ADVPL HTML) que misturam HTML + tags ADVPL embarcadas.

Diferente do REST (skill `advpl-webservice`), ADVPL Web é **server-rendered**: o servidor monta HTML e devolve ao browser.

## Quando usar

- Usuário pede "página web Protheus", "portal", "tela HTML servida pelo AppServer".
- Edit em `.APH` (ADVPL HTML).
- Funções `ApWebEx*`, `WebPageOpen`, `WebPageProc`.
- Métodos HTTP em contexto Protheus (`HTTPGet`, `HTTPPost`, `HTTPSession`).
- Portal multi-empresa/filial com login.
- Upload/download de arquivos via HTTP no AppServer.
- **NÃO** use para API REST/JSON — para isso veja `advpl-webservice`.

## Arquivos .APH — ADVPL HTML

```html
<%
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

- `<% código ADVPL %>` — bloco ADVPL.
- `<%= expressao %>` — escreve resultado da expressão no HTML.

## Configuração appserver.ini para Web

```ini
[HTTPSERVER]
ENABLE=1
PORT=8080
PATH=C:\TOTVS\Protheus_Data\Web

[WEBEX]
INSTANCES=1,5
SOURCEPATH=C:\TOTVS\Protheus_Data\Web\Apw
ENVIRONMENT=ENVIRONMENT
```

`PATH` aponta para diretório raiz de arquivos `.APH`. URL `http://host:8080/index.aph` serve `<PATH>/index.aph`.

## Métodos de transporte

| Método           | Função para ler              | Para que serve                       |
|------------------|------------------------------|--------------------------------------|
| GET (querystring)| `HTTPGet("nome")`            | URL params, links                    |
| POST (form)      | `HTTPPost("nome")`           | Submissão de formulário              |
| Session          | `HTTPSession("chave")`       | Estado entre requests (login)        |
| Cookie           | `HTTPCookie("nome")`         | Preferências, tracking               |
| Header           | `HTTPHeadIn("Authorization")`| Auth, content-type                   |
| Porta            | `HTTPHeadIn("REMOTE_PORT")`  | Identificar contexto                 |

## Portal multi-empresa

```advpl
// pagina_login.aph processa autenticação
<%
    Local cUser  := HTTPPost("user")
    Local cPass  := HTTPPost("pass")
    Local cEmp   := HTTPPost("emp")
    Local cFil   := HTTPPost("fil")

    If ValidUser(cUser, cPass)
        HTTPSession("USR", cUser)
        HTTPSession("EMP", cEmp)
        HTTPSession("FIL", cFil)
        // RpcSetEnv é aceitável em WEB (não REST) para abrir contexto da empresa
        RpcSetEnv(cEmp, cFil, cUser, cPass)
        WebRedir("home.aph")
    Else
        WebRedir("login.aph?err=1")
    EndIf
%>
```

Note: em ADVPL Web ASP-style, `RpcSetEnv` é aceitável (diferente de REST onde é proibido — ver `advpl-webservice`).

## Upload / Download

```advpl
// Upload
<%
    Local cFile := HTTPUpload("arquivo", "C:\TOTVS\Uploads\")
    If !Empty(cFile)
        // arquivo gravado em cFile
    EndIf
%>

// Download
<%
    HTTPContentType("application/pdf")
    HTTPHeadOut("Content-Disposition", "attachment; filename=relatorio.pdf")
    WebSendFile("C:\TOTVS\Relatorios\rel.pdf")
%>
```

## Pontos de Entrada APWEBEX

PEs específicas para o pipeline Web:

| PE             | Quando                                   |
|----------------|------------------------------------------|
| `APWEBINI`     | Inicialização da thread Web              |
| `APWEBLOG`     | Login do usuário web                     |
| `APWEBOUT`     | Fim do processamento de uma requisição   |
| `APWEBVLD`     | Validação custom de sessão               |

## Anti-padrões

- Misturar lógica de negócio dentro do `.APH` em vez de extrair User Function → vira spaghetti.
- Não validar `HTTPGet`/`HTTPPost` antes de usar em SQL → SQL injection (use `%exp:`).
- Não escapar HTML em variáveis vindas do usuário → XSS.
- Esquecer `HTTPSession` para autenticação — exposição de página sem login.
- Usar `MsgInfo`/`Alert` no `.APH` → tenta abrir UI no servidor (não funciona).
- WebSendFile com path concatenando input do usuário → path traversal.

## Referência profunda

Para detalhes completos (~2.4k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Apostila ADVPL Web completa (TOTVS) com módulos, threads, configuração HTTPSERVER/WEBEX.
- Catálogo de atributos HTML de input suportados em `.APH`.
- Lista completa de funções `ApWebEx*` (envio de e-mail, formatação, conversão).
- Padrão de gravação de dados via web (transações, controle de concorrência).
- Página Modelo 2/Modelo 3 web (CRUD HTML automático).
- Relatórios na Web (impressão server-side enviada por download).
- Catálogo completo de PEs APWEBEX.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function ApWebEx` — funções web no projeto.
- `/plugadvpl:grep "<%.*%>"` — localiza fontes `.APH`.
- `/plugadvpl:lint <arq.aph>` — checagens de SEC-001/SEC-002.
