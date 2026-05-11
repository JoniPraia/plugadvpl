# ADVPL Web – Desenvolvimento Web com Protheus

> **Todos os direitos autorais reservados pela TOTVS S.A.**
> Proibida a reprodução total ou parcial, bem como a armazenagem em sistema de recuperação e a transmissão, de qualquer modo ou por qualquer outro meio, sem prévia autorização por escrito da proprietária.

---

## Sumário

- [1. Objetivo](#1-objetivo)
- [2. Introdução ao ADVPL ASP](#2-introdução-ao-advpl-asp)
- [3. O Servidor Protheus como um servidor HTTP](#3-o-servidor-protheus-como-um-servidor-http)
- [4. Configurando servidor de WEB-Protheus](#4-configurando-servidor-de-web-protheus)
- [5. Módulos Web](#5-módulos-web)
- [6. Características do ADVPL ASP - Arquivos .APH](#6-características-do-advpl-asp---arquivos-aph)
- [7. Método de Envio e Recebimento de Dados via WEB](#7-método-de-envio-e-recebimento-de-dados-via-web)
  - [7.1. Método GET](#71-método-get)
  - [7.2. Método POST](#72-método-post)
  - [7.3. Método HTTPSESSION](#73-método-httpsession)
  - [7.4. Método COOKIE](#74-método-cookie)
  - [7.5. Método HTTPHEADIN](#75-método-httpheadin)
  - [7.6. Porta da Requisição (REMOTE_PORT)](#76-porta-da-requisição-remote_port)
- [8. Criação do Portal](#8-criação-do-portal)
  - [8.1. Processamento para Várias Empresas/Filiais](#81-processamento-para-várias-empresasfiliais)
  - [8.2. Processo de Gravação de Dados via Páginas da Web](#82-processo-de-gravação-de-dados-via-páginas-da-web)
- [9. Página Modelo 2 / Modelo 3](#9-página-modelo-2--modelo-3)
- [10. Desenvolvimento e Impressão de Relatório na WEB](#10-desenvolvimento-e-impressão-de-relatório-na-web)
- [11. Upload / Download](#11-upload--download)
- [12. Funções e Comandos ADVPL (Apêndices)](#12-funções-e-comandos-advpl-apêndices)
  - [Referência de Atributos HTML de Input](#referência-de-atributos-html-de-input)
  - [Referência de Funções ApWebEx](#referência-de-funções-apwebex)
  - [Pontos de Entrada APWEBEX](#pontos-de-entrada-apwebex)

---

## 1. Objetivo

**MÓDULO 08: Introdução ao desenvolvimento WEB**

Ao final do curso o treinando deverá ter desenvolvido os seguintes conceitos, habilidades e atitudes:

**a) Conceitos a serem aprendidos**
- Estruturas para implementação de aplicações ADVPL ASP
- Introdução às técnicas de programação de desenvolvimento de telas, formulários, métodos de transporte de dados
- Introdução aos conceitos de inserir, alterar, excluir e visualizar na Web

**b) Habilidades e técnicas a serem aprendidas**
- Desenvolvimento de aplicações voltadas ao ERP/WEB Protheus
- Análise de fontes de média complexidade
- Desenvolvimento com linguagens ASP, JavaScript, HTML, ADVPL ASP

**c) Atitudes a serem desenvolvidas**
- Adquirir conhecimentos através da análise das funcionalidades disponíveis no ERP Protheus
- Estudar a implementação de fontes com estruturas orientadas a objetos em ADVPL WEB
- Embasar a realização de outros cursos relativos à linguagem ADVPL ASP e WebService

---

## 2. Introdução ao ADVPL ASP

### HTML

HTML, abreviação para *Hypertext Markup Language*, é a formatação padrão adotada para a publicação de HyperTexto na Internet (World Wide Web). O HTML consiste em uma formatação não proprietária, baseada no SGML (*Standard Generalized Markup Language*), e pode ser criada e processada por um grande número de ferramentas, desde editores de texto-plano até sofisticados softwares WYSIWYG (*What You See Is What You Get*).

Basicamente, o HTML utiliza-se dos marcadores `<` e `>` para estruturar e formatar texto. Por exemplo:

```html
Letra normal, <b>negrito</b> e <u>sublinhado</u>
```

A linha de texto acima, representada em um Web Browser, seria mostrada assim: Letra normal, **negrito** e <u>sublinhado</u>.

### HTTP

HTTP é a abreviação de *Hyper Text Transfer Protocol*. O HTTP é um protocolo em nível de aplicação para distribuição de informações. Trata-se de um protocolo genérico, que pode ser utilizado para muitas outras aplicações além de transferência de hipertexto. Uma característica importante do HTTP é a tipagem e normalização da representação da informação, permitindo a construção de sistemas independente do modo pelo qual os dados estão sendo transferidos.

### O que é uma Thread?

Uma Thread é o fluxo sequencial de controle único dentro de um programa. A grande sacada consiste no uso de **Múltiplas Threads** dentro de uma aplicação, todas em execução simultânea, porém cada uma realizando tarefas diferentes. Cada thread possui o seu próprio contexto de execução, alocação de memória e controle de pilha de execução (Stack).

#### Working Threads

Damos o nome de *working thread* quando são iniciadas mais de uma thread independente na aplicação, e todas as threads iniciadas são colocadas em "modo de espera" (idle), aguardando uma solicitação de processamento. Este recurso possibilita um ganho significativo de performance, por não haver a necessidade de criar e finalizar uma nova thread para cada solicitação de processamento.

---

## 3. O Servidor Protheus como um servidor HTTP

O servidor Protheus pode ser configurado para trabalhar como um servidor WEB, atendendo requisições dos protocolos HTTP e/ou FTP, do mesmo modo que outros servidores conhecidos no mercado (como o IIS da Microsoft ou o Apache para Linux).

### Serviço de HTTP

O protocolo HTTP é o protocolo utilizado na comunicação entre um servidor e um Web Browser. Este protocolo se baseia principalmente em dois comandos: **GET** e **POST**. O comando GET é utilizado para obter alguma informação do servidor HTTP e o POST para postar informações para o servidor.

### Páginas Dinâmicas e ADVPL ASP

Quando é utilizado o servidor Protheus para desenvolvimento de aplicações Web, é possível lançar mão do recurso de criação de páginas dinâmicas. Uma requisição HTTP realizada ao Server Protheus dispara o processamento de uma função no Servidor, e esta função encarrega-se de devolver ao usuário uma página HTML com o resultado do processamento.

Foi criado um tipo de arquivo especial no Protheus IDE com a extensão `.APH`, onde é inserido um conteúdo HTML a ser enviado ao Web Browser, e instruções ADVPL que serão processadas no momento em que a página for solicitada ao servidor Protheus.

No servidor Protheus, foram implementadas duas extensões de Link para permitir a execução de funções ADVPL através de uma requisição HTTP:

- **Extensão `.APL`** — executa funções diretamente via HTTP
- **Extensão `.APW`** — executa funções via Working Threads WEBEX

Uma função executada via link `.apl` ou `.apw` deve obrigatoriamente ter um retorno do tipo **String**, pois o Web Browser será informado pelo Server Protheus que a string retornada deverá ser interpretada como HTML.

Uma página ASP (*Active Server Pages*) é uma página HTML contendo código interpretável. No ADVPL ASP esse código é padrão xBase — portanto a preocupação maior de quem já conhece o Protheus é conhecer HTML.

---

## 4. Configurando servidor de WEB-Protheus

Nos serviços HTTP e HTTPS, é possível especificar as configurações padrões deste protocolo e propriedades gerais aplicadas a todos os hosts. O protocolo FTP (*File Transfer Protocol*) permite a transferência de arquivos entre um servidor e uma aplicação client de FTP.

### Editando a Configuração HTTP

Para inserir/editar uma configuração HTTP:

1. Abra o Wizard pelo programa inicial do SmartClient.
2. Clique no botão "OK".
3. No tópico "Servidor HTTP", posicionado o cursor sobre o item "HTTP", clique em "Editar Configuração" nas Ações Relacionadas.
4. Clique em "Editar" para abrir a tela de configuração.

Será apresentada uma janela com as configurações padrões atuais para o serviço de HTTP:

| Campo | Descrição |
|-------|-----------|
| **Protocolo Habilitado** | Habilita/desabilita a utilização do protocolo HTTP sem deletar as configurações. |
| **Nome da Instância** | Não disponível para edição. Informa se um módulo Web foi instalado no host HTTP [default]. |
| **Path de Arquivos** | Diretório raiz para acesso a arquivos estáticos e imagens. Deve ser informado com unidade de disco e caminho completo. |
| **Porta de Conexão** | Porta de conexão utilizada. Para HTTP, a porta padrão é a **80**. |
| **Ambiente** | Permite selecionar um environment (ambiente) para atender às solicitações de processamento de links `.apl`. |
| **Processo de Resposta** | Permite selecionar um processo WEB/WEBEX para atender às solicitações de links `.apw`. |
| **Instâncias de Protocolo (mínimo e máximo)** | Número mínimo e máximo de processos internos referentes ao serviço de HTTP. |
| **Path para Upload de Arquivos** | Diretório para gravação dos arquivos enviados via HTTP (relativo ao RootPath do ambiente). |
| **Time-out de Sessões WEBEX (segundos)** | Tempo de permanência em inatividade das variáveis de sessões. Padrão: **3600 segundos** (uma hora). |

Para gravar as configurações, clique em "Finalizar". O arquivo `appserver.ini` será atualizado e o Assistente será reiniciado.

### Princípio de Funcionamento do HTTP

A utilização do protocolo HTTP não envolve o uso de uma conexão persistente entre o Web Browser e o Servidor HTTP. Ao ser solicitada uma página, o Web Browser abre uma conexão com o Server HTTP, realiza a solicitação e fica aguardando o retorno. Quando o server houver enviado os dados solicitados, a conexão é **fechada**.

---

## 5. Módulos Web

Neste tópico, é possível instalar, configurar e excluir as configurações e arquivos adicionais pertinentes aos módulos Web disponibilizados pelo Sistema.

Os módulos Web disponibilizados são:

| Sigla | Descrição |
|-------|-----------|
| **DW** | Data Warehouse |
| **BSC** | Balanced Scorecard |
| **GE** | Gestão Educacional |
| **TCF** | Terminal do Funcionário (RH on-line) |
| **PP** | Portal Protheus |
| **WS** | Web Services |
| **WPS** | WebPrint/WebSpool |
| **MAK** | Módulo Webex Makira (ambientes customizados) |
| **GPR** | Gestão de Pesquisas e Resultados |
| **GAC** | Gestão de Acervos |

### Instalando um Módulo Web

1. Abra o Wizard através da tela do SmartClient.
2. Clique no ícone Wizard.
3. Posicione o mouse sobre o tópico "Módulos Web" na árvore de tópicos, e clique em "Novo Módulo" na barra de botões.

Na tela de configuração, preencha os campos:

| Campo | Descrição |
|-------|-----------|
| **Módulo Web** | Selecione o módulo Web a ser instalado. Para PP, GPR e GAC, é necessária a instalação prévia do módulo Web Services. |
| **Nome da Instância** | Nome para identificação desta configuração do módulo Web. Não utilize caracteres acentuados ou espaços. |
| **Diretório Raiz de Imagens (Web Path)** | Diretório para instalação das imagens e arquivos (.css, .jar, .htm, etc). Inicia com `\`. |
| **Environment** | Environment que será utilizado para execução do módulo. |
| **Habilitar processos na inicialização** | Se selecionado, os processos WEB/WEBEX serão inseridos automaticamente na configuração `OnStart`. |
| **URL do Protheus Web Services** | Exibido apenas na instalação do módulo PP - Portal Protheus. Deve ser precedido por `HTTP://`. |

4. Para prosseguir, clique em "Avançar". O Assistente verificará se os pacotes de instalação dos arquivos Web (`.MZP`) estão disponíveis na pasta `SYSTEMLOAD`.

5. Na janela "Configuração de Host x Empresas/Filiais", informe:

| Campo | Exemplos |
|-------|---------|
| **Host** (Internet) | `www.nomedosite.com.br` |
| **Host** (Intranet) | `nomedoservidor` |
| **Host** com diretório virtual | `nomedoservidor/ws`, `nomedoservidor/pp` |

Não especifique o protocolo (`HTTP://` ou `HTTPS://`).

6. Selecione as Empresa/Filiais e clique em "Relacionar".

7. Na próxima tela, configure o número mínimo e máximo de usuários:

| Campo | Descrição |
|-------|-----------|
| **Mínimo Usuários** | Expectativa mínima de usuários que irão acessar o site. |
| **Máximo Usuários** | Expectativa máxima de usuários. **Obrigatório.** |

> **Exemplo:** Mínimo: 5 / Máximo: 10. O Protheus configurará em média 1 processo mínimo e 3 máximo (razão de 10 usuários por processo).

8. Para finalizar a instalação do módulo, clique em "Finalizar".

Ao confirmar, o pacote de arquivos do módulo Web será descompactado no diretório raiz de imagens, e o `appserver.ini` será atualizado com as definições do módulo (Host, Processos WEB/WEBEX).

---

## 6. Características do ADVPL ASP - Arquivos .APH

Os arquivos ADVPL ASP têm a extensão padrão `.APH`. São arquivos texto e devem ser adicionados a um projeto no Protheus IDE e compilados da mesma maneira que os programas tradicionais.

O Protheus Server executará um parser antes da compilação, que irá transformar todo o arquivo em uma função única. Um arquivo APH gera no repositório de Objetos do Protheus **uma função com o mesmo nome do arquivo**, prefixada com:

```
H_ + nome_do_arquivo_apw
```

Existe também a extensão `.AHU` (*APH de Usuário*), que possui o mesmo tratamento de Parser, gerando uma função prefixada com `L_`. A diferença é que a função gerada pelo AHU pode ser gerada sem a necessidade de autorização de compilação com permissão para substituir fontes Microsiga — é equivalente a uma `User Function`.

### Delimitadores de Código

A diferenciação entre script HTML e código ADVPL é efetuada através dos delimitadores:

| Delimitador | Tipo | Uso |
|-------------|------|-----|
| `<%` | Abertura de código | Início de bloco ADVPL |
| `%>` | Fechamento de código | Fim de bloco ADVPL |
| `<%=` | Abertura de avaliação | Avalia e insere expressão no HTML |

**Exemplo de código ADVPL em APH:**

```advpl
<% While !EOF() %>
<B> Esta linha será repetida no HTML até ocorrer o fim de arquivo </B>
<%
  dbSkip()
EndDo
%>
```

**Exemplo de delimitador de avaliação:**

```advpl
<b>Esta linha é HTML, mas o horário exibido aqui: <%= Time() %> foi obtido em tempo de execução no Servidor.</b>
```

### Regras Importantes dos Delimitadores

- A abertura e fechamento dos delimitadores de execução `<% ... %>` devem estar **isoladas em suas respectivas linhas**, não devendo ter qualquer conteúdo adicional.
- Não são permitidas duas aberturas e fechamentos na mesma linha.
- Os delimitadores de avaliação `<%= ... %>` podem ter várias aberturas e fechamentos na mesma linha, porém não podem ter uma abertura e seu respectivo fechamento em linhas diferentes.
- Uma linha qualquer em um arquivo `.APH` não deve conter mais do que **150 caracteres**.

**Exemplos de uso correto e incorreto:**

```advpl
// CORRETO
<% IF !lOk
nErro++
Endif %>

// CORRETO
<% IF !lOk %>
<% nErro++ %>
<% Endif %>

// ERRADO — dois blocos na mesma linha
<% IF !lOk %><% nErro++ %>
<% Endif %>

// ERRADO — tudo em uma linha com ponto e vírgula
<% IF !lOk ; nErro++ ; Endif %>
```

---

## 7. Método de Envio e Recebimento de Dados via WEB

### 7.1. Método GET

O método GET é o método que o usuário consegue ver quais foram os dados de comunicação entre uma determinada página e outra (os dados ficam visíveis na URL). **Não é recomendado** para inserção de conteúdo entre informações de um formulário e um banco de dados.

Através do alias virtual `HttpGet`, podemos consultar parâmetros enviados através da URL.

**Consultando parâmetros:**

```advpl
// URL: http://localhost/u_TesteGet.apw?imagem=teste&cor=azul
cImagem := HttpGet->imagem
cCor    := HttpGet->cor

// Com valor default caso o parâmetro não seja enviado (NIL):
DEFAULT cImagem := 'LogoAp8'
DEFAULT cCor    := 'amarelo'
```

**Listando todos os parâmetros GET recebidos:**

```advpl
aInfo := HttpGet->aGets
For nI := 1 to Len(aInfo)
  conout('GET' + str(nI, 3) + ' = ' + aInfo[nI])
Next
```

**Exemplo de criação APW (método GET):**

```advpl
#INCLUDE "APWEBEX.CH"

User Function EXMETODOGET
  Local cHtml := ""

  WEB EXTENDED INIT cHtml

  // Exemplo do metodo GET.
  If ! Empty(HttpGET->Var1)
    // Exibe na Console do Servidor.
    ConOut(HttpGET->Var1)
    ConOut(HttpGET->Var2)
  Endif

  // Nome do arquivo APH
  cHtml := ExecInPage("METODOGET")

  WEB EXTENDED END
Return(cHtml)
```

**Exemplo de criação APH (método GET):**

```html
<html>
<head>
  <title>Metodo Get</title>
</head>
<body>
  <p>Exemplo Metodo GET</p>
  <p>
    <a href="u_EXMETODOGET.apw?Var1=Teste_do_metodo_GET&Var2=ExemploGet">
      Teste metodo GET
    </a>
  </p>
</body>
</html>
```

### 7.2. Método POST

O método POST transfere as informações de forma oculta no link. Vantagens em relação ao GET:

1. O número de caracteres enviados chega a ser quase que infinito (vários megabytes).
2. O usuário não saberá qual ou quais foram os dados enviados para a outra página.
3. É um método dinâmico — adequado para email, senha e outras informações.

Através do alias virtual `HttpPost`, podemos consultar os campos submetidos ao servidor.

**Consultando parâmetros POST:**

```advpl
Codigo := HttpPost->Codigo
```

**Listando todos os parâmetros POST:**

```advpl
aInfo := HttpPost->aPost
For nI := 1 to Len(aInfo)
  conout('POST ' + str(nI, 3) + ' = ' + aInfo[nI])
Next
```

**Exemplo de criação APW (método POST):**

```advpl
#Include "APWEBEX.CH"

User Function METODOPOST()
  Local cHtml := ""

  WEB EXTENDED INIT cHtml

  // Exemplo do metodo POST.
  If ! Empty(HttpPost->Nomevariavel)
    ConOut(HttpPost->Nomevariavel)  // Exibe na Console do Servidor.
  Endif

  cHtml := ExecInPage("METODOPOST")

  WEB EXTENDED END
Return(cHtml)
```

**Exemplo de criação APH (método POST):**

```html
<html>
<head>
  <title>AdvPL/ASP</title>
</head>
<body>
  <H1>Exemplo AdvPL/ASP - metodo POST</H1>
  <form name="Dados" action="u_METODOPOST.apw" method="POST">
    <Label>Nome:
      <input type="text" name="Nomevariavel">
    </Label>
    <input type="SUBMIT" value="Enviar">
  </form>
</body>
</html>
```

### 7.3. Método HTTPSESSION

O alias virtual `HttpSession` foi criado para possibilitar a criação de variáveis *session* por usuário do site, com controle de identificação através de um cookie chamado `SESSIONID`.

Tipos de variáveis suportados em Session: `A` (array), `C` (character), `D` (data), `L` (lógica), `N` (numérica). **Não são suportados** `O` (Objetos) e/ou `B` (Code Blocks).

#### Criando e Consultando Variáveis Session

```advpl
// Criando variáveis Session
HttpSession->UserId   := '123'
HttpSession->UserName := cUserName

// Consultando variáveis Session
If HttpSession->UserId == NIL
  // Session ainda não foi criada — usuário não está logado.
  conout('Usuario não está logado')
Else
  // Session já criada — o usuário está logado
  conout('Usuario está logado : ID = ' + HttpSession->UserId)
Endif
```

#### Exemplo de Funcionamento de Session

```advpl
#include 'Protheus.ch'
#include 'apwebex.ch'

User Function TstSession()
  Local cHtml := '', cEcho := ''

  WEB EXTENDED INIT cHtml

  If httpSession->mycounter == NIL
    cEcho := 'Inicializando contador'
    Conout(cEcho)
    cHtml += cEcho
    httpSession->mycounter := 1
  Else
    httpSession->mycounter++
    cEcho := 'contador em ' + str(httpSession->mycounter, 3)
    conout(cEcho)
  Endif

  cHtml += cEcho + '<hr>'

  WEB EXTENDED END
Return cHtml
```

> Após compilado e o Server configurado, abra um Web Browser e solicite a URL `http://localhost/u_tstsession.apw`. Será mostrado "Inicializando Contador". A cada *Refresh*, o contador será incrementado.

#### Uso de Sessions e Paralelismo

O Protheus Server trata as requisições simultâneas de links `.APW` em paralelo. Para evitar perda de dados em sessions quando acessadas simultaneamente por frames, foi implementado um esquema de **Lock de Session de Usuário automático**. A liberação da bandeira ocorre automaticamente no retorno da Working Thread, ou pode ser feita manualmente com `HttpLeaveSession()`.

#### Exemplo APW — Session com Datas e Array

```advpl
#Include "APWEBEX.CH"

User Function METODOSESSION()
  Local cHtml := ""

  WEB EXTENDED INIT cHtml

  // Criação das variáveis de Session
  HttpSession->dData  := Date()
  HttpSession->cHora  := Time()
  HttpSession->aSemana := {"Domingo", "Segunda", "Terca", ;
                           "Quarta", "Quinta", "Sexta", "Sábado"}

  cHtml := H_METODOSESSSION()

  WEB EXTENDED END
Return(cHtml)
```

**APH correspondente:**

```html
<head>
  <title>AdvPL/ASP</title>
</head>
<body>
  <p>Data: <%=HttpSession->dData%></p>
  <p>Hora: <%=HttpSession->cHora%></p>
  <p></p>
  <% For i := 1 To Len(HttpSession->aSemana) %>
    <p>
      <%=HttpSession->aSemana[I]%>
      <% If I == dow(HttpSession->dData) %>
        <===== Hoje
      <%Endif%>
    </p>
  <%Next%>
</body>
</html>
```

### 7.4. Método COOKIE

Cookie é um pequeno arquivo de texto no qual um site pode armazenar informações no disco rígido do usuário (não no servidor). A maioria dos cookies expira após um determinado tempo.

Através do alias virtual `HttpCookies`, é possível consultar os Cookies do Header HTTP enviados pelo Browser, e criar ou alterar o conteúdo de um cookie a ser devolvido ao Browser. Uma variável de Cookie retorna e aceita apenas o tipo Advpl **String**. O limite total de cookies costuma ser próximo a **1024 Bytes**.

#### Gravando um Cookie com JavaScript

```javascript
function gravaCookie(nome, value, horas) {
  var expire = "";
  if (horas != null) {
    expire = new Date((new Date()).getTime() + horas * 3600000);
    expire = "; expires=" + expire.toGMTString();
  }
  document.cookie = nome + "=" + escape(value) + expire;
}

// Para gravar:
onclick="gravaCookie('meusite', 'Curso ADVPL ASP', 24)";
```

#### Recuperando um Cookie com JavaScript

```javascript
function lerCookie(nome) {
  var valorCookie = "";
  var search = nome + "=";
  if (document.cookie.length > 0) {
    offset = document.cookie.indexOf(search);
    if (offset != -1) {
      offset += search.length;
      end = document.cookie.indexOf(";", offset);
      if (end == -1) end = document.cookie.length;
      valorCookie = unescape(document.cookie.substring(offset, end));
    }
  }
  return valorCookie;
}
```

#### Usando Cookies em ADVPL

```advpl
// Lendo cookies
cUserId := HttpCookies->USERID    // Retorna o Cookie identificador do usuário do Protheus
cIdioma := HttpCookies->SiteLang  // Retorna o conteúdo do cookie SiteLang

// Listando todos os cookies recebidos
aInfo := HttpCookies->aCookies
For nI := 1 to Len(aInfo)
  conout('Cookie' + str(nI, 3) + '=' + aInfo[nI])
Next

// Criando um Cookie
HttpCookies->MeuCookie := 'TESTE'
```

> **Atenção:** A criação de um Cookie deve ser realizada **antes** de qualquer processamento de APH/AHU, pois o Header de Retorno HTTP já teria sido enviado ao browser após esse ponto.

### 7.5. Método HTTPHEADIN

Para a recepção e tratamento das informações recebidas através do Header do pacote HTTP, foi criado o alias virtual `HttpHeadIn`. Através dele, podemos consultar os parâmetros enviados pelo Browser solicitante e propriedades da conexão atual, como o IP do usuário solicitante.

**Consultando o User-Agent:**

```advpl
cUserAgent := Httpheadin->User_Agent
// Retorno exemplo: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.0.3705)
```

> **Observação:** Qualquer parâmetro no Header HTTP que contenha caracteres inválidos para a nomenclatura de variáveis Advpl (como o hífen em `User-Agent`) são trocados pelo caractere `_` (underline).

**Propriedades especiais de `HttpHeadIn`:**

| Propriedade | Descrição |
|-------------|-----------|
| `HttpHeadIn->aHeaders` | Retorna um Array de Strings com todas as linhas do Header HTTP da requisição. |
| `HttpHeadIn->main` | Retorna o nome da função chamada através da URL, sem extensão e sem o host. |
| `HttpHeadIn->REMOTE_ADDR` | Retorna o IP da estação que realizou a requisição (formato `nnn.nnn.nnn.nnn`). |
| `httpHeadIn->REMOTE_PORT` | Retorna um valor Advpl numérico informando a porta utilizada para realizar a requisição. |

### 7.6. Porta da Requisição (REMOTE_PORT)

Através do alias virtual de retorno (`HttpHeadOut`), podemos alterar ou criar um parâmetro no Header de retorno HTTP do Protheus, a ser devolvido ao Browser solicitante de uma requisição de processamento.

> **Atenção:** O header deve ser criado **antes** de qualquer processamento de APH/AHU, pois após esse ponto o Header de Retorno HTTP já teria sido enviado ao browser.

---

## 8. Criação do Portal

### 8.1. Processamento para Várias Empresas/Filiais

Para que o usuário ao entrar na página possa escolher qual será a empresa e filial que deseja visualizar/alterar os dados, devemos criar um código fonte que permita esta escolha e valide o acesso.

**Exemplo — Fonte APW (Portal):**

```advpl
#INCLUDE "Protheus.ch"
#INCLUDE 'APWEBEX.CH'

User Function PORTAL(_cEmp_, _cFil_)
  Local aTabs := {"SA1"}
  Local cHtml := ""

  Default _cEmp_ := "99"
  Default _cFil_ := "01"

  Private aDados := {}

  WEB EXTENDED INIT cHtml

  // Seta o ambiente com a empresa 99 filial 01 com os direitos do usuario administrador, módulo Financeiro
  RpcSetEnv(_cEmp_, _cFil_,,, "FIN", "TlIniWB", aTabs,,,,)

  // Carrega empresas/filiais do SIGAMAT.EMP
  SM0->(DBGOTOP())
  While SM0->(!EOF())
    AADD(aDados, {'"' + SM0->M0_CODIGO + '-' + SM0->M0_CODFIL + '"', SM0->M0_NOME})
    SM0->(DBSKIP())
  End

  // Chama a pagina
  cHtml := h_PORTAL()

  RpcClearEnv()  // Limpa o ambiente, liberando a licença e fechando as conexões

  WEB EXTENDED END
Return(cHtml)
```

**Variáveis utilizadas:**

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `aTabs` | Array | Array com tabelas para o sistema abrir |
| `cHtml` | Caracter | String com o retorno do HTML executado por `h_Portal()` |
| `_cEmp_` | Caracter | Código da empresa a ser aberta |
| `_cFil_` | Caracter | Código da filial a ser aberta |
| `aDados` | Array (Private) | Array com dados lidos do SIGAMAT.EMP para passagem ao APH |

#### Função RpcSetEnv

Abertura do ambiente em rotinas automáticas.

```advpl
RpcSetEnv([cRpcEmp], [cRpcFil], [cEnvUser], [cEnvPass], [cEnvMod], [cFunName], [aTables], [lShowFinal], [lAbend], [lOpenSX], [lConnect]) --> lRet
```

| Parâmetro | Tipo | Descrição | Default |
|-----------|------|-----------|---------|
| `cRpcEmp` | Caracter | Código da empresa. | — |
| `cRpcFil` | Caracter | Código da filial. | — |
| `cEnvUser` | Caracter | Nome do usuário. | — |
| `cEnvPass` | Caracter | Senha do usuário. | — |
| `cEnvMod` | Caracter | Código do módulo. | `'FAT'` |
| `cFunName` | Caracter | Nome da rotina retornada por `FunName()`. | `'RPC'` |
| `aTables` | Vetor | Array com as tabelas a serem abertas. | `{}` |
| `lShowFinal` | Lógico | Alimenta a variável pública `lMsFinalAuto`. | `.F.` |
| `lAbend` | Lógico | Se `.T.`, gera mensagem de erro ao checar a licença. | `.T.` |
| `lOpenSX` | Lógico | Se `.T.`, pega a primeira filial do SM0 e abre os SXs. | `.T.` |
| `lConnect` | Lógico | Se `.T.`, faz a abertura da conexão com servidor SQL etc. | `.T.` |

#### Função RpcClearEnv

Limpa o ambiente, liberando a licença e fechando as conexões.

**Exemplo — Fonte APH (Portal, tela de login):**

```html
<HTML>
<style>
  div.Center {
    margin-top: 30%;
    margin-left: 35%;
    float: left;
    height: 510px;
    width: 340px;
    border: 1.5px solid #d9d9d9;
    background-color: white;
    position: relative;
    border-radius: 10px;
  }
  .logo {
    background-image: url('_imagens/logo.png');
    background-repeat: no-repeat;
    margin-top: 20px;
    margin-left: 80px;
    height: 60px;
    width: 200px;
  }
  .bemvindo {
    margin-top: 20%;
    margin-left: 10%;
    font-family: Arial;
    font-size: 15px;
    color: #747675;
    font-weight: bold;
  }
  .ID, .senha { position: absolute; margin-left: 10%; font-family: Arial; font-size: 14px; color: #747675; }
  .ID   { margin-top: 05%; }
  .senha { margin-top: 20%; }
  .botao { position: absolute; margin-top: 50%; margin-left: 10%; }
  img { display: block; margin: 0 auto; }
  input[type=text], input[type=PASSWORD] { width: 200px; display: block; margin-bottom: 10px; }
  input[type=submit] {
    color: #FFFFFF;
    width: 100px;
    height: 30px;
    display: block;
    margin-bottom: 10px;
    background-color: #1F739E;
    border: 1px solid #01669F;
  }
</style>
<HEAD>
  <TITLE>Pagina Inicial - ADVPL-WEB</TITLE>
</HEAD>
<script language="JavaScript">
  function cancelar() {
    document.login.action = "u_ValUser.apw";
    document.login.submit();
  }
  function ok() {
    var ok = true;
    missinginfo = '';
    if (document.login.cNome.value == '') {
      ok = false;
      missinginfo = '\n   - Nome';
    }
    if (document.login.cSenha.value == '') {
      ok = false;
      missinginfo += '\n   - Senha';
    }
    if (ok) {
      document.login.submit();
    } else {
      missinginfo = '_____________________________\n' +
                    ' Não preenchido corretamente:\n' +
                    missinginfo + '\n_____________________________' +
                    '\n Tente novamente!';
      alert(missinginfo);
    }
  }
</script>
<BODY BACKGROUND="fundo_degrade.png">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <div Class="Center">
    <div Class="logo">
      <img src="_imagens/logo.png" alt="Logo" style="width:100%;height:100%;">
    </div>
    <FORM name="login" id="login" action="u_NOMEDOPRW.apw" METHOD="POST">
      <!-- campos de login e senha aqui -->
      <input type="submit" value="Acessar Portal" onClick="javascript:ok()">
    </FORM>
  </div>
</BODY>
</HTML>
```

**Detalhes do formulário:**

- `<FORM name="login" id="login" action="u_NOMEDOPRW.apw" METHOD="POST">` — abre o formulário com nome "login" para tratamento das funções JavaScript, com ação para a próxima página e método POST (não apresenta dados na URL).

> **Exercício:** Desenvolver uma tabela `ZZ0` com campos: `ZZ0_FILIAL` (C, 02, Obrig.), `ZZ0_USUARI` (C, 10, Obrig.), `ZZ0_NOME` (C, 80, Obrig.), `ZZ0_SENHA` (C, 06, Obrig.). Índice: `ZZ0_FILIAL + ZZ0_USUARI`. Desenvolver uma página que liste as Empresas/Filiais do SIGAMAT.EMP com 2 campos (Login, Senha), 2 botões (Entrar, Cancelar) e uma seleção. Método de envio: POST.

### 8.2. Processo de Gravação de Dados via Páginas da Web

Para criar a opção Visualizar / Incluir / Alterar e Excluir, utilizamos a tabela SA1 (Clientes) nos exemplos.

**Exemplo — Fonte APW carregando a estrutura da tabela de clientes:**

```advpl
#INCLUDE "TOTVS.CH"
#INCLUDE "APWEBEX.CH"
#INCLUDE "TBICONN.CH"

User Function Listadados()
  Local cHtml   := ""
  Local cAlias  := "SA1"
  Local aDados  := {}
  Local aHeader := {}

  If Select("SX2") == 0
    Prepare Environment Empresa '99' Filial '01' Tables 'SA1'
  EndIf

  WEB EXTENDED INIT cHtml

  HTTPSESSION->aHeader  := {}
  HTTPSESSION->aCliente := {}

  dbSelectArea("SX3")
  dbSetOrder(1)
  dbSeek(cAlias)

  aAdd(aHeader, {" ", "( Recno() )"})

  While ! SX3->(EOF()) .And. SX3->X3_ARQUIVO == cAlias
    If X3Uso(SX3->X3_USADO) .And. cNivel >= SX3->X3_NIVEL .And. X3Obrigat(SX3->X3_CAMPO)
      AADD(aHeader, {Trim(X3Titulo()), SX3->X3_CAMPO})
    Endif
    SX3->(dbSkip())
  EndDo

  dbSelectArea(cAlias)
  (cAlias)->(dbSetOrder(1))
  (cAlias)->(dbGoTop())

  While ! (cAlias)->(EOF())
    AADD(aDados, Array(Len(aHeader)))
    For x := 1 To Len(aHeader)
      aDados[Len(aDados), x] := &(cAlias + "->" + aHeader[x, 2])
    Next x
    (cAlias)->(dbSkip())
  EndDo

  HTTPSESSION->aHeader := aHeader
  HTTPSESSION->aDados  := aDados

  cHtml := H_ListaDados()

  WEB EXTENDED END
Return(cHtml)
```

**Exemplo — Fonte APH listando dados:**

```html
<% Local x; Local Y %>
<!DOCTYPE html>
<html>
<head>
  <style>
    table { font-family: arial, sans-serif; border-collapse: collapse; width: 100%; }
    td { border: 1px solid RGB(119,119,119); text-align: left; padding: 8px; }
    th { border: 1px solid RGB(151,151,151); text-align: center; padding: 8px;
         color: RGB(255,255,255); background-color: RGB(115,115,115); }
    tr:nth-child(even) { background-color: RGB(109,217,255); }
    div.tabela { position: relative; margin-top: 160px; Top: 50%; border-radius: 10px; }
  </style>
</head>
<body>
  <Div Class="tabela">
    <form name="form1" action="u_xAltera.apw" method="POST">
      <table>
        <tr>
          <% For x := 1 To Len(HTTPSESSION->aHeader) %>
            <TH><%= HTTPSESSION->aHeader[x][1] %></TH>
          <% Next x %>
        </tr>
        <% For Y := 1 To Len(HTTPSESSION->aDados) %>
          <tr>
            <% For x := 1 To Len(HTTPSESSION->aHeader) %>
              <% if x = 1 %>
                <TD>
                  <input type="radio" name="recno" value=<%= HTTPSESSION->aDados[Y][X] %>>
                </TD>
              <% Else %>
                <TD><%= HTTPSESSION->aDados[Y][X] %></TD>
              <% Endif %>
            <% Next x %>
          </tr>
        <% Next Y %>
      </table>
    </Div>
    <input type="submit">
  </form>
</body>
</html>
```

O campo radio com o número do RECNO é usado para manipular o registro posicionado:

```html
<input type="radio" name="recno" value=<%= HTTPSESSION->aDados[Y][X] %> />
```

**Exemplo — xtelaA.apw (tela de edição):**

```advpl
#include "protheus.ch"
#include "apwebex.ch"

User Function xtelaA()
  Local cHtml   := ""
  Local xRecno  := HTTPGET->xRecnos
  Local xTab    := HttpSession->cTab
  Local cNome   := ""
  Local nVolta  := 0
  Local cFolder := ""

  Private aDados1 := {}
  Private aDados2 := {}
  Private INCLUI  := .F.
  Private ALTERA  := .T.
  Private DELETA  := .F.

  Default xRecno := ""

  WEB EXTENDED INIT cHtml

  CONOUT('xRecno')
  CONOUT(xRecno)

  If Empty(xRecno) .Or. Upper(xRecno) == 'UNDEFINED'
    // Gera HTML em formato String para redirecionar
    cHtml := " <html> "
    cHtml += " <body> "
    cHtml += " <form name='login' method='post' action='u_TlIniWB3.apw'> "
    cHtml += " <script language='JavaScript'><INPUT TYPE='hidden' VALUE=xRecno NAME='xRecnos'></script> "
    cHtml += " </form> "
    cHtml += " </body> "
    cHtml += " </html> "
    cHtml += " <script language='JavaScript'> "
    cHtml += " document.login.submit(); "
    cHtml += " </script> "
  Else
    HttpSession->xRecno := Val(xRecno)

    // Processo para pegar o registro
    SX3->(DBSETORDER(4))
    SX3->(DBSEEK(xTab))
    (xTab)->(dbgoto(Val(xRecno)))

    // Loop de leitura dos campos do SX3 (código completo omitido por brevidade)
    // ... (ver fonte completo no código-fonte original)

    cHtml := h_xtelaA()
  Endif

  WEB EXTENDED END
Return(cHtml)
```

**Exemplo — gravar.apw (gravação de dados):**

```advpl
#include "Protheus.ch"
#include "apwebex.ch"

User Function gravar()
  Local cHtml  := ""
  Local aDados := {}
  Local aDados1 := {}
  Local aParms := {}
  Local xRecno := HttpSession->xRecno
  Local xTab   := HttpSession->cTab

  WEB EXTENDED INIT cHtml

  // Monta array com os parametros recebidos via POST
  // no formato ( [1] = nome / [2] = conteudo )
  aEval(HttpPost->aPost, {|x| iif(x == 'SALVAR', NIL, aadd(aParms, {x, &("HttpPost->" + x)}))})

  // Tratamento dos campos virtuais
  DBSELECTAREA("SX3")
  SX3->(dbsetorder(1))
  SX3->(DBSEEK(xTab))

  While SX3->X3_ARQUIVO == (xTab)
    If EMPTY(X3_CONTEXT) .OR. X3_CONTEXT == 'R'
      AADD(aDados, SX3->X3_CAMPO)
      AADD(aDados1, SX3->X3_TIPO)
    Endif
    SX3->(dbskip())
  End

  // Gravação dos campos na tabela informada
  (xTab)->(dbgoto(xRecno))
  Reclock((xTab), .F.)
  aEval(aParms, {|x| (NN := aScan(aDados, x[1]), IIF(NN = 0, nil, (&(((xTab) + '->' + x[1])) := IIF(aDados1[NN] == 'N', VAL(x[2]), IIF(aDados1[NN] == 'D', CTOD(x[2]), x[2])))))})
  Msunlock()

  // Redireciona de volta e fecha a janela
  cHtml := " <html> "
  cHtml += " <body> "
  cHtml += " <form name='login' method='post' action='u_TELA.apw'> "
  cHtml += " <script language='JavaScript'><INPUT TYPE='hidden' VALUE=xRecno NAME='xRecnos'></script> "
  cHtml += " </form> "
  cHtml += " </body> "
  cHtml += " </html> "
  cHtml += " <script language='JavaScript'> "
  cHtml += " window.opener.parent.direita.location.reload();window.close() "
  cHtml += " </script> "

  WEB EXTENDED END
Return(cHtml)
```

**Estrutura do array `aParms`:**
- `aParms[n][1]` — nome da variável
- `aParms[n][2]` — conteúdo da variável

---

## 9. Página Modelo 2 / Modelo 3

Criação de um **Modelo 3**, com:
- Parte superior (**EnchoIce**): tabela SA1 — cadastro do Cliente
- Parte inferior (**GetDados**): tabela SE1 — títulos do cliente a Receber

O modelo utiliza frameset com 3 linhas:
- Linha 1: botões desejados
- Linha 2: EnchoIce
- Linha 3: GetDados

**Exemplo — xModel3.apw:**

```advpl
#include "Protheus.ch"
#include "ApWebex.ch"

User Function xModel3()
  Local cHtml  := ""
  Local xRecno := HTTPGET->xRecnos
  Local cNome  := ""
  Local nVolta := 0
  Local cFolder := ""
  Local cQuery := ""
  Local cTabS  := "SA1"
  Local cTabI  := "SE1"

  Private aDados0 := {}
  Private aDados1 := {}
  Private aDados2 := {}
  Private aFrame1 := {}
  Private INCLUI  := .F.
  Private ALTERA  := .T.
  Private DELETA  := .F.
  Private xTab    := "SA1"

  Default xRecno := ""

  HttpSession->cTabS  := "SA1"
  HttpSession->cTabI  := "SE1"
  HttpSession->xRecno := Val(xRecno)

  xRecno := ALLTRIM(xRecno)

  WEB EXTENDED INIT cHtml

  // Alimenta o Enchoice — lê campos do SX3 para SA1
  // (loop completo de montagem de aDados1/aDados2 aqui)

  // Query para títulos do cliente
  cQuery  := "SELECT E1_PREFIXO, E1_NUM, E1_PARCELA, E1_TIPO, E1_VALOR, E1_VENCTO, E1_HIST, R_E_C_N_O_ AS REC "
  cQuery  += " FROM " + RETSQLNAME("SE1") + " A "
  cQuery  += " WHERE A.E1_FILIAL = '" + xFilial("SE1") + "'"
  cQuery  += "   AND E1_CLIENTE = '" + SA1->A1_COD + "'"
  cQuery  += "   AND E1_LOJA = '" + SA1->A1_LOJA + "'"
  cQuery  += "   AND D_E_L_E_T_ = ' '"

  dbUseArea(.T., "TOPCONN", TcGenQry(,, cQuery), "TRBSE1", .T., .F.)
  TCSetField("TRBSE1", 'E1_PREFIXO', 'C', 3, 0)
  TCSetField("TRBSE1", 'E1_NUM',     'C', 8, 0)
  TCSetField("TRBSE1", 'E1_PARCELA', 'C', 2, 0)
  TCSetField("TRBSE1", 'E1_TIPO',    'C', 3, 0)
  TCSetField("TRBSE1", 'E1_VALOR',   'N', 14, 2)
  TCSetField("TRBSE1", 'E1_VENCTO',  'D', 8, 0)

  // Alimenta a GetDados (TRBSE1)
  HttpSession->xTelaE  := aDados0  // Enchoice
  HttpSession->xTelaG  := aDados1  // GetDados
  httpSession->aFrame1 := aFrame1  // Hidden fields

  cHtml := h_xModel3()
  TRBSE1->(dbclosearea())

  WEB EXTENDED END
Return(cHtml)
```

**APH do frameset (xModel3.aph):**

```html
<HTML>
<HEAD>
  <TITLE>modelo 3</TITLE>
</HEAD>
<frameset rows="7%,40%,*" border=0>
  <frame name="top"    src="u_xTelaG0.APW" marginwidth="10" marginheight="10" scrolling="No"   frameborder="no" noresize>
  <frame name="middle" src="U_xTelaG1.APW" marginwidth="10" marginheight="10" scrolling="Auto" frameborder="no" noresize>
  <frame name="bottom" src="U_xTelaG2.apw" marginwidth="10" marginheight="10" scrolling="Auto" frameborder="no" noresize>
  <noframes>
    <body></body>
  </noframes>
</frameset>
</HTML>
```

Cada frame usa uma sessão diferente:

| Frame | APW | Sessão utilizada |
|-------|-----|-----------------|
| `top` (botões superiores) | `u_xTelaG0.apw` | `HttpSession->aFrame1` |
| `middle` (EnchoIce) | `u_xTelaG1.apw` | `HttpSession->xTelaE` |
| `bottom` (GetDados) | `u_xTelaG2.apw` | `HttpSession->xTelaG` |

**APW do frame TOP (u_xTelaG0.apw):**

```advpl
#INCLUDE "Protheus.ch"
#INCLUDE "APWEBEX.CH"

User Function XTELAG0()
  Local cHtml   := ""
  Private aFrame1 := HttpSession->aFrame1

  WEB EXTENDED INIT cHtml
  cHtml := h_XTELAG0()
  WEB EXTENDED END
Return(cHtml)
```

**APH do frame TOP — botões e campos hidden:**

```html
<HTML>
<HEAD><TITLE>GETDADOS</TITLE></HEAD>
<script language="JavaScript">
  var aRoda = new Array();

  function ok() {
    document.modx31.action = "u_gravar3.apw";
    document.modx31.submit();
  }

  function recebi(cCpo, cValor) {
    document.getElementById(cCpo).value = cValor;
  }
</script>
<BODY BGCOLOR="#E6EEED">
  <FORM ACTION="#" METHOD="POST" TITLE="mod3" name="modx31">
    <% for nFor := 1 to len(aFrame1) %>
      <%= aFrame1[nFor]%>
    <% next nFor%>
    <TABLE BORDER="0" WIDTH="50%" CELLPADDING="0" CELLSPACING="0">
      <TR>
        <TD><INPUT TYPE="submit" VALUE="Salvar"   NAME="Salvar"   onClick="javascript:ok()"></TD>
        <TD><INPUT TYPE="submit" VALUE="Cancelar" NAME="Cancelar" onClick="javascript:parent.window.close();"></TD>
      </TR>
    </TABLE>
  </FORM>
</BODY>
</HTML>
```

A função `recebi(cCpo, cValor)` alimenta os campos Hidden da página TOP quando o usuário altera qualquer campo nos outros frames. O método `getElementById` busca o elemento pelo ID especificado.

**APH do frame MIDDLE — EnchoIce (h_XTELAG1):**

```html
<HTML>
<HEAD><TITLE></TITLE></HEAD>
<script language="JavaScript">
  function SomenteNumero(e) {
    var tecla = (window.event) ? event.keyCode : e.which;
    if ((tecla > 47 && tecla < 58) || tecla == 46 || tecla == 44) { return true; }
    else { if (tecla != 8) { return false; } else { return true; } }
  }
  function passar(campo) {
    parent.frames['top'].recebi(campo.name, campo.value);
  }
  function upperCase(campo, valor) { campo.value = valor.toUpperCase(); }
  function validaDat(campo, valor) {
    var date = valor;
    var ardt = new Array;
    var ExpReg = new RegExp("(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/[12][0-9]{3}");
    ardt = date.split("/");
    erro = false;
    if (date.search(ExpReg) == -1) { erro = true; }
    else if (((ardt[1]==4)||(ardt[1]==6)||(ardt[1]==9)||(ardt[1]==11)) && (ardt[0]>30)) erro = true;
    else if (ardt[1] == 2) {
      if ((ardt[0] > 28) && ((ardt[2] % 4) != 0)) erro = true;
      if ((ardt[0] > 29) && ((ardt[2] % 4) == 0)) erro = true;
    }
    if (erro) {
      alert('"' + valor + '" não é uma data válida!!! utilize dd/mm/aaaa');
      campo.focus();
      campo.value = " / / ";
      return false;
    }
    return true;
  }
</script>
<BODY BGCOLOR="#E6EEED">
  <FORM ACTION="#" METHOD="POST" TITLE="alterar" name="modx32" id="modx32">
    <TABLE BORDER="0" WIDTH="100%" CELLPADDING="0" CELLSPACING="0">
      <% For nFor := 1 to len(aDados) %>
        <% For nFor2 := 1 to len(aDados[nFor]) %>
          <%= aDados[nFor][nFor2] %>
        <% next nFor2 %>
      <% next nFor %>
    </TABLE>
  </FORM>
</BODY>
</HTML>
```

**APH do frame BOTTOM — GetDados (h_XTELAG2):**

A função `delet(campo, valor)` é utilizada para atribuir `"0"` quando o checkbox de deletar não for selecionado e `"1"` quando for selecionado:

```javascript
function delet(campo, valor) {
  if (valor == 1) { valor = 0; }
  else { valor = 1; }
  campo.value = valor;
}
```

**APW de gravação do Modelo 3 (gravar3.apw):**

```advpl
#include "Protheus.ch"
#include "apwebex.ch"

User Function gravar3()
  Local cHtml  := ""
  Local aDados := {}
  Local aDados1 := {}
  Local aParms := {}
  Local xRecno := HttpSession->xRecno
  Local xTabS  := HttpSession->cTabS
  Local xTabI  := HttpSession->cTabI

  WEB EXTENDED INIT cHtml

  aEval(HttpPost->aPost, {|x| iif(alltrim(x) == 'SALVAR' .AND. EMPTY(&("HttpPost->" + x)), NIL, aadd(aParms, {x, &("HttpPost->" + x)}))})

  // Tratamento dos campos virtuais — carrega tipos de ambas as tabelas
  DBSELECTAREA("SX3")
  SX3->(dbsetorder(1))
  SX3->(DBSEEK(xTabS))
  While SX3->X3_ARQUIVO == (xTabS)
    If EMPTY(X3_CONTEXT) .OR. X3_CONTEXT == 'R'
      AADD(aDados, alltrim(SX3->X3_CAMPO))
      AADD(aDados1, SX3->X3_TIPO)
    Endif
    SX3->(dbskip())
  End
  SX3->(DBSEEK(xTabI))
  While SX3->X3_ARQUIVO == (xTabI)
    If EMPTY(X3_CONTEXT) .OR. X3_CONTEXT == 'R'
      AADD(aDados, alltrim(SX3->X3_CAMPO))
      AADD(aDados1, SX3->X3_TIPO)
    Endif
    SX3->(dbskip())
  End

  // Rotina de gravação
  For nFor := 1 to Len(aParms)
    If !EMPTY(aParms[nFor][2]) .AND. aParms[nFor][1] != 'SALVAR' .And. !('DELETAR' $ aParms[nFor][1])
      // Extrai tabela, recno e campo do nome do parâmetro (formato: _TABELA_RECNO_CAMPO)
      aParms[nFor][1] := substr(aParms[nFor][1], at("_", aParms[nFor][1]) + 1)
      xTab  := substr(aParms[nFor][1], 1, at("_", aParms[nFor][1]) - 1)
      aParms[nFor][1] := substr(aParms[nFor][1], at("_", aParms[nFor][1]) + 1)
      nRec  := Val(substr(aParms[nFor][1], 1, at("_", aParms[nFor][1]) - 1))
      aParms[nFor][1] := substr(aParms[nFor][1], at("_", aParms[nFor][1]) + 1)
      cCpo  := alltrim(aParms[nFor][1])
      xValor := aParms[nFor][2]
      NN := aScan(aDados, cCpo)
      If NN > 0
        xValor := IIF(aDados1[NN] == 'N', VAL(xValor), IIF(aDados1[NN] == 'D', CTOD(xValor), xValor))
        (xTab)->(dbgoto(nRec))
        Reclock((xTab), .F.)
        &((xTab) + '->' + cCpo) := xValor
        Msunlock()
      Endif
    ElseIf 'DELETAR' $ aParms[nFor][1]
      // Processamento de exclusão
      aParms[nFor][1] := substr(aParms[nFor][1], at("_", aParms[nFor][1]) + 1)
      xTab := substr(aParms[nFor][1], 1, at("_", aParms[nFor][1]) - 1)
      aParms[nFor][1] := substr(aParms[nFor][1], at("_", aParms[nFor][1]) + 1)
      nRec := Val(substr(aParms[nFor][1], 1, at("_", aParms[nFor][1]) - 1))
      (xTab)->(dbgoto(nRec))
      xValor := aParms[nFor][2]
      If ALLTRIM(xValor) == '1'
        Reclock((xTab), .F.)
        DBDELETE()
        Msunlock()
      Endif
    Endif
  Next nFor

  // Fecha a janela
  cHtml := " <html> "
  cHtml += " <body> "
  cHtml += " <form name='login' method='post' action='u_TlIniWB3.apw'> "
  cHtml += " <script language='JavaScript'><INPUT TYPE='hidden' VALUE=xRecno NAME='xRecnos'></script> "
  cHtml += " </form> "
  cHtml += " </body> "
  cHtml += " </html> "
  cHtml += " <script language='JavaScript'> "
  cHtml += " javascript:parent.window.close(); "
  cHtml += " </script> "

  WEB EXTENDED END
Return(cHtml)
```

O nome de cada campo segue o padrão `_TABELA_RECNO_CAMPO` (ex: `NAME="_SE1_17_E1_CODIGO"`), permitindo que o código de gravação identifique dinamicamente tabela, registro e campo.

> **Exercício:** Criar uma página para apresentar os dados do fornecedor SA2 associado aos títulos SE2 que esse fornecedor possui.

---

## 10. Desenvolvimento e Impressão de Relatório na WEB

O processo de emitir relatório em uma página de internet consiste em:
1. Exibir uma página com os parâmetros de seleção (buscados do SX1)
2. Após o preenchimento, executar uma query ou DBSKIP e exibir os dados

**Exemplo — APW do relatório:**

```advpl
#INCLUDE "PROTHEUS.CH"
#INCLUDE "APWEBEX.CH"

User Function relatoMI()
  Local cHtml  := ""
  Local cQuery := ""

  Private aDados  := {}
  Private cDados1 := HttpGET->MV_PAR02
  DEFAULT cDados1 := ""

  WEB EXTENDED INIT cHtml

  If Empty(cDados1)
    // Parâmetros ainda não preenchidos — exibe formulário SX1
    SX1->(DBGOTOP())
    SX1->(DBSEEK("SA1SA1   01"))
    While SX1->(!EOF()) .AND. ALLTRIM(SX1->X1_GRUPO) == "SA1SA1"
      AADD(aDados, {SX1->X1_PERGUNT, SX1->X1_TAMANHO})
      SX1->(DBSKIP())
    End
    cHtml := H_relatoMI()
  Else
    // Parâmetros preenchidos — executa query e exibe relatório
    cQuery := " SELECT A1_COD, A1_NOME, A1_NREDUZ, A1_END, A1_EST, A1_ESTADO "
    cQuery += "   FROM " + retsqlname("SA1")
    cQuery += " WHERE A1_FILIAL = '" + XfILIAL("SA1") + "'"
    cQuery += "   AND A1_COD BETWEEN '" + HttpGET->MV_PAR01 + "' AND '" + HttpGET->MV_PAR02 + "'"
    cQuery += "   AND A1_EST BETWEEN '" + HttpGET->MV_PAR03 + "' AND '" + HttpGET->MV_PAR04 + "'"

    dbUseArea(.T., "TOPCONN", TcGenQry(,, cQuery), "TRBSA1", .T., .F.)
    CONOUT(cQuery)
    cHtml := H_relatoMI()
    TRBSA1->(dbclosearea())
  Endif

  WEB EXTENDED END
Return(cHtml)
```

**Exemplo — APH do relatório (H_relatoMI):**

```html
<HTML>
<HEAD>
  <TITLE>
    <% IF SELECT("TRBSA1") > 0 %>
      RELATORIO
    <% ELSE %>
      PARAMETROS
    <%ENDIF%>
  </TITLE>
</HEAD>
<BODY onunload="window.opener.location.reload()">
  <% IF SELECT("TRBSA1") > 0 %>
    <TABLE BORDER="1" WIDTH="100%" CELLPADDING="0" CELLSPACING="0">
      <TR>
        <TD>Codigo   </TD>
        <TD>Nome     </TD>
        <TD>N Fantasia</TD>
        <TD>Endereco  </TD>
        <TD>Estado   </TD>
        <TD>Nome Estado</TD>
      </TR>
      <% WHILE TRBSA1->(!EOF()) %>
        <TR>
          <TD><%= TRBSA1->A1_COD    %></TD>
          <TD><%= TRBSA1->A1_NOME   %></TD>
          <TD><%= TRBSA1->A1_NREDUZ %></TD>
          <TD><%= TRBSA1->A1_END    %></TD>
          <TD><%= TRBSA1->A1_EST    %></TD>
          <TD><%= TRBSA1->A1_ESTADO %></TD>
        </TR>
        <% TRBSA1->(DBSKIP()) END %>
      <TR>
        <TD COLSPAN="3" ALIGN="CENTER">
          <INPUT TYPE="submit" VALUE="IMPRIMIR" NAME="IMPRIMIR" onclick="javascript:window.print();">
        </TD>
        <TD COLSPAN="3" ALIGN="CENTER">
          <INPUT TYPE="submit" VALUE="FECHAR" NAME="FECHAR" onclick="javascript:window.close();">
        </TD>
      </TR>
    </TABLE>
  <% ELSE %>
    <FORM ACTION="U_relatoMI.APW" METHOD="GET" TITLE="PARAMETROS" NAME="PARAMETROS" ID="PARAMETROS">
      <TABLE BORDER="1" WIDTH="40%" CELLPADDING="0" CELLSPACING="0">
        <TR><TD>CLIENTE DE</TD><TD><INPUT TYPE="text" VALUE="   " NAME="MV_PAR01" SIZE="6" MAXLENGTH="7"></TD></TR>
        <TR><TD>CLIENTE ATÉ</TD><TD><INPUT TYPE="text" VALUE="ZZZZZZ" NAME="MV_PAR02" SIZE="6" MAXLENGTH="7"></TD></TR>
        <TR><TD>ESTADO DE</TD><TD><INPUT TYPE="text" VALUE="   " NAME="MV_PAR03" SIZE="2" MAXLENGTH="2"></TD></TR>
        <TR><TD>ESTADO ATÉ</TD><TD><INPUT TYPE="text" VALUE="ZZ" NAME="MV_PAR04" SIZE="2" MAXLENGTH="2"></TD></TR>
        <TR>
          <TD><INPUT TYPE="submit" VALUE="OK" NAME="OK"></TD>
          <TD><INPUT TYPE="submit" VALUE="CANCELAR" NAME="CANCELAR" onclick="opener.location.reload();window.close()"></TD>
        </TR>
      </TABLE>
    </FORM>
  <%ENDIF%>
</BODY>
</HTML>
```

A impressão utiliza `javascript:window.print()` e o fechamento usa `javascript:window.close()`.

> **Exercício:** Desenvolver um relatório com os dados da Tabela SA1.

---

## 11. Upload / Download

**Exemplo — APW de Upload:**

```advpl
#INCLUDE "PROTHEUS.CH"
#INCLUDE "APWEBEX.CH"

User Function UPLOAD()
  Local cHtml    := ""
  Local cRootWeb := GetSrvProfString("RootWeb", "\web")
  Local lUnix    := IsSrvUnix()

  Private aDir := {}

  WEB EXTENDED INIT cHtml

  nTamRoot := Len(alltrim(cRootWeb))
  cCaracter := iif(lUnix, "/", "\")

  // Retirar barra sobressalente
  If substr(cRootWeb, nTamRoot, 1) == "/" .OR. substr(cRootWeb, nTamRoot, 1) == "\"
    cRootWeb := substr(cRootWeb, 1, nTamRoot - 1)
  Endif

  // Normalizar separadores de path
  If ! lUnix
    cRootWeb := STRTRAN(cRootWeb, "/", "\")
  Else
    cRootWeb := STRTRAN(cRootWeb, "\", "/")
  Endif

  // Criar diretório "arquivos" se não existir
  nRetorno   := MAKEDIR(cRootWeb + "\arquivos", 1)
  cDiretorio := cRootWeb + "\arquivos"
  nRetorno   := MAKEDIR(cDiretorio, 1)
  cDiretorio := cDiretorio + "\"

  If lUnix
    cDiretorio := Strtran(cDiretorio, "\", "/")
  Endif

  cDiretorio := cRootWeb + "\arquivos\*.*"
  conout(cDiretorio)
  aDire := DIRECTORY(cDiretorio, "D", 1)

  For nFor := 1 to Len(aDire)
    If aDire[nFor][2] != 0
      AADD(aDir, {aDire[nFor][1], aDire[nFor][2], "http://localhost:81/PP/arquivos/" + aDire[nFor][1]})
    Endif
  Next nFor

  varinfo('aDir', aDir)
  cHtml := h_UPLOAD()

  WEB EXTENDED END
Return(cHtml)
```

**Funções utilizadas:**

| Função | Descrição |
|--------|-----------|
| `GetSrvProfString(cChave, cDefault)` | Recupera o conteúdo de uma chave do arquivo `.INI` do TOTVS Application Server. |
| `IsSrvUnix()` | Retorna `.T.` se o Application Server estiver sendo executado em ambiente Unix/Linux. |
| `MakeDir(cNovoDir, [xParam2])` | Cria um diretório. Retorna `0` se criado com sucesso. |
| `Directory(cDirEsp, [cAtributos], [xParam3], [lCaseSensitive])` | Cria um array bidimensional com o conteúdo de um diretório. |
| `VarInfo(cId, xVar, [nMargem], [lHtml], [lEcho])` | Gera texto ASCII e/ou HTML com informações sobre o conteúdo de uma variável Advpl. |

**Exemplo — APH de Upload:**

```html
<HTML>
<HEAD>
  <TITLE>UPLOAD DE ARQUIVO</TITLE>
</HEAD>
<script language="JavaScript">
  function delet(campo, valor) {
    if (campo.value != 0) { valor = 0; }
    campo.value = valor;
  }
  function OK() {
    document.form.action = "u_subir.apw";
    document.form.submit();
  }
  function SAIR() {
    document.form.action = "u_TlIniWB2.apw";
    document.form.submit();
  }
</script>
<BODY BGCOLOR="#C0EDC7">
  <FORM title="UPLOAD" NAME="form" method="GET" action="u_subir.apw" ENCTYPE="multipart/form-data">
    <TABLE border=0 cellSpacing=0 cellPadding=0 width="100%">
      <TBODY>
        <TR><TD>EXCLUIR?</TD><TD>NOME</TD><TD>TAMANHO</TD></TR>
        <% For nFor := 1 to len(aDir) %>
          <TR>
            <TD>
              <INPUT TYPE="checkbox" VALUE="0" NAME="EXCLUIR"
                onclick="javascript:delet(this,'<%= aDir[nFor][1] %>')">
            </TD>
            <TD><a href="<%= aDir[nFor][3] %>"><%= aDir[nFor][1] %></a></TD>
            <TD><a href="<%= aDir[nFor][3] %>"><%= aDir[nFor][2] %></a></TD>
          </TR>
        <% Next nFor %>
      </TBODY>
    </TABLE>
    <TABLE border=1 cellSpacing=0 cellPadding=0 width="100%">
      <TBODY>
        <TR>
          <TD>INFORME O ARQUIVO PARA FAZER O UPLOAD</TD>
          <TD>
            <INPUT style="WIDTH: 892px; HEIGHT: 22px" name="file" value=" " size=120>
          </TD>
        </TR>
      </TBODY>
    </TABLE>
    <INPUT TYPE="submit" VALUE="ATUALIZAR" NAME="Atualizar" onclick="JAVASCRIPT:OK()">
    <INPUT TYPE="submit" VALUE="Sair"      NAME="Sair"      onclick="JAVASCRIPT:SAIR()">
  </FORM>
</BODY>
</HTML>
```

**Exemplo — Subir.apw (processamento do upload):**

```advpl
#INCLUDE "APWEBEX.CH"
#INCLUDE 'PROTHEUS.CH'

User Function subir()
  Local cHtml        := ""
  Local cDiretorio   := ""
  Local cArquivo     := ""
  Local cNickArq     := ""
  Local cNickArqDest := ""
  Local cRootWeb     := GetSrvProfString("RootWeb", "\web")
  Local lUnix        := IsSrvUnix()
  Local cCaracter    := ""
  Local lStatus      := 0
  Local nRetorno     := 0
  Local i            := 0
  Local nTamRoot     := 0

  Private aDir   := {}
  Private nTotal := 0
  Private cMsg   := ""

  WEB EXTENDED INIT cHtml

  // Normalização do path (igual ao UPLOAD)
  nTamRoot  := Len(alltrim(cRootWeb))
  cCaracter := iif(lUnix, "/", "\")

  If substr(cRootWeb, nTamRoot, 1) == "/" .OR. substr(cRootWeb, nTamRoot, 1) == "\"
    cRootWeb := substr(cRootWeb, 1, nTamRoot - 1)
  Endif
  If ! lUnix
    cRootWeb := STRTRAN(cRootWeb, "/", "\")
  Else
    cRootWeb := STRTRAN(cRootWeb, "\", "/")
  Endif

  nRetorno   := MAKEDIR(cRootWeb + "\arquivos", 1)
  cDiretorio := cRootWeb + "\arquivos"
  nRetorno   := MAKEDIR(cDiretorio, 1)
  cDiretorio := cDiretorio + "\"

  If lUnix
    cDiretorio := Strtran(cDiretorio, "\", "/")
  Endif

  // Exclusão de arquivo
  If HttpGET->EXCLUIR != nil
    cNickArq     := HttpGET->EXCLUIR
    cNickArqDest := Renomeia(cNickArq)
    fErase(cDiretorio + cNickArqDest, 1)
  Endif

  // Upload de arquivo
  If HttpGET->file != nil
    cArquivo := HttpGET->file

    If ! lUnix
      cArquivo := STRTRAN(cArquivo, "/", "\")
    Else
      cArquivo := STRTRAN(cArquivo, "\", "/")
    Endif

    // Extrai o nome do arquivo do caminho completo
    i := Len(cArquivo)
    While Substr(cArquivo, i, 1) != cCaracter
      cNickArq := Substr(cArquivo, i, 1) + cNickArq
      i := i - 1
      If i <= 0
        Exit
      Endif
    End

    cNickArqDest := Renomeia(cNickArq)
    lStatus      := __COPYFILE(cArquivo, cDiretorio + cNickArqDest, 1)

    If lStatus
      fErase(cArquivo, 1)
    Endif

    // Atualiza lista de arquivos
    cDiretorio := cRootWeb + "\arquivos\*.*"
    aDire       := DIRECTORY(cDiretorio, "D", 1)

    For nFor := 1 to Len(aDire)
      If aDire[nFor][2] != 0
        AADD(aDir, {aDire[nFor][1], aDire[nFor][2], "http://localhost:81/PP/arquivos/" + aDire[nFor][1]})
      Endif
    Next nFor

    cHtml := H_upload()
  Endif

  WEB EXTENDED END
Return cHtml
```

**Função Renomeia (remove acentos e caracteres inválidos):**

```advpl
Static Function Renomeia(cCampo)
  Local cAcentos  := "áàãââÁÀÃÂéêÉÊíÍóõôÓÔÕúüÚÜçÇabcdefghijklmnopqrstuvxwyz ªº"
  Local cTraducao := "AAAAAAAAAEEEEIIOOOOOOUUUUCCABCDEFGHIJKLMNOPQRSTUVXWYZ_AO"
  Local i := 0

  For i := 0 to Len(cAcentos)
    cCampo := STRTRAN(cCampo, Substr(cAcentos, i, 1), Substr(cTraducao, i, 1))
  Next i
Return cCampo
```

> **Exercício:** Desenvolver uma página onde o usuário possa criar subpastas, inserir arquivos (Upload) e fazer o respectivo Download.

---

## 12. Funções e Comandos ADVPL (Apêndices)

### Referência de Atributos HTML de Input

#### ACCEPT
Filtra os tipos de arquivos que podem ser apresentados via upload. Formato MIME: `tipo/subtipo`.

```html
<input type="file" name="picture" id="picture" accept="image/jpeg" />
```

#### ACCESSKEY
Permite ao usuário ativar um controle usando atalho de teclado. No IE/Windows: `Alt + accesskey`; Firefox/Windows: `Alt + Shift + accesskey`; Mac: `Ctrl + accesskey`.

```html
<label for="firstname">First name [access key = f]</label>
<input type="text" name="firstname" id="firstname" accesskey="f"/>
```

#### ALIGN
Usado para alinhar imagens em inputs do tipo imagem. Prefira CSS.

#### CHECKED
Define o estado "marcado" por padrão para checkboxes e radio buttons.

```html
<input type="checkbox" name="chknewsletter" id="chknewsletter" checked="checked" />
```

#### DISABLED
Impede que o usuário interaja com o controle.

```html
<input type="checkbox" name="chknewsletter" id="chknewsletter" disabled="disabled" />
```

#### MAXLENGTH
Define o comprimento máximo de caracteres de uma entrada de texto ou senha.

```html
<input type="password" name="pin" id="pin" maxlength="4" size="6"/>
```

#### NAME
Identifica o campo no formulário. Apenas elementos com atributo `name` terão seus valores passados na ação do formulário.

#### READONLY
Impede que o usuário altere o valor, mas permite interação (clicar, destacar texto, copiar).

```html
<input type="text" name="town" id="town" readonly="readonly" value="Southampton"/>
```

#### SIZE
Define a largura de um campo de entrada de texto, senha ou arquivo (em número de caracteres). Prefira CSS.

#### SRC
Define a localização da imagem para inputs do tipo `image`.

```html
<input type="image" src="submit.jpg" alt="Submit your details"/>
```

#### TABINDEX
Define a sequência de navegação pela tecla Tab. O valor `0` indica posição inicial.

```html
<input type="password" name="pin" id="pin" tabindex="2" />
```

#### TYPE — Valores possíveis

| Valor | Descrição |
|-------|-----------|
| `button` | Botão clicável simples (requer JavaScript para ação). |
| `checkbox` | Caixa de seleção sim/não. |
| `file` | Upload de arquivos. |
| `hidden` | Campo oculto para armazenar valores sem exibição. |
| `image` | Botão de envio com imagem. |
| `password` | Campo de texto com caracteres mascarados. |
| `radio` | Botão de opção (apenas um em um grupo pode ser selecionado). |
| `reset` | Limpa todos os dados do formulário (uso com cautela). |
| `submit` | Envia os dados do formulário. |
| `text` | Campo de entrada de texto de linha única. |

**Exemplos:**

```html
<!-- Checkbox -->
<input type="checkbox" name="chknewsletter" id="chknewsletter" value="newsletter-opt-in"/>
<label for="chknewsletter">Envie-me o boletim mensal</label>

<!-- File -->
<input type="file" name="picture" id="picture" accept="image/jpeg, image/gif"/>

<!-- Hidden -->
<input type="hidden" name="hdnCustId" value="<%= RECNO %>"/>

<!-- Radio -->
<input type="radio" name="station" id="rad1" value="Radio 1"/>
<label for="rad1">Radio 1</label>

<!-- Submit -->
<input type="submit" name="cmdSubmit" id="cmdSubmit" value="Enviar esta aplicação"/>
```

#### VALUE
Comportamento por tipo:

| Tipo | Comportamento |
|------|---------------|
| `button`, `submit`, `reset` | Texto exibido no botão. |
| `text`, `password` | Valor exibido dentro do campo (pode ser alterado pelo usuário). |
| `radio`, `checkbox`, `hidden`, `image` | Não exibido para o usuário; associado ao controle e enviado no submit. |

#### Eventos de Input

| Evento | Descrição |
|--------|-----------|
| `onkeypress` | Executa um script quando uma tecla alfanumérica é pressionada. |
| `onchange` | Executa um script quando o valor de um elemento é modificado. |
| `onclick` | Ativado em um clique do mouse. |

---

### Referência de Funções ApWebEx

#### APWEXADDERR

```
APWEXADDERR([cTitulo], [cInfo]) --> .T.
```

Acrescenta uma string de informações adicionais em um buffer em memória, descarregado na geração do `ERROR.LOG` em caso de erro fatal na working thread atual. Chamada sem parâmetros, elimina a última ocorrência da pilha.

| Parâmetro | Tipo | Descrição | Limite |
|-----------|------|-----------|--------|
| `cTitulo` | Caracter | Título identificador (máx. 20 caracteres). | 20 chars |
| `cInfo` | Caracter | Informação a ser acrescentada ao ERROR.LOG. | — |

---

#### CAPITALACE

```
CAPITALACE(cString) --> cStrCapital
```

Semelhante à função `Capital()`, porém converte também caracteres acentuados. Converte todos os caracteres para minúsculo e a primeira letra das palavras significantes para maiúsculo.

---

#### CTON

```
CTON(cString, nBase) --> nNumero
```

Converte um número representado em String, de base 2 a 36, para um número em base decimal (10).

```advpl
nNum1 := CTON('01101001', 2)   // Binário para decimal
nNum2 := CTON('00DA25FE', 16)  // Hexadecimal para decimal
```

---

#### ESCAPE

```
ESCAPE(cString) --> cEscaped
```

Realiza conversões de caracteres especiais e reservados para a notação `%HH`, para uso em passagem de parâmetros via URL.

```advpl
cUrl := 'http://localhost/webinfo.apw'
cUrl += '?Par01=' + escape(cPAram1) + '&PAr02=' + escape(cPAram2)
```

---

#### EXECINPAGE

```
EXECINPAGE(cAPHPage) --> cHTMLPage
```

Executa uma página APH/AHU passada como parâmetro e retorna a String HTML correspondente.

**Prioridade de execução:**
1. Primeiro, verifica se existe um AHU com o nome especificado.
2. Se não, procura pelo APH.
3. Se nenhum dos dois existir, aborta com o erro `[APWEXERR_0007]`.
4. Antes de executar, verifica se existe um User Function (ponto de entrada) com o mesmo nome do APH.

---

#### EXISTPAGE

```
EXISTPAGE(cAphFile) --> lFound
```

Verifica se um arquivo `.APH` está compilado no RPO do ambiente atual.

```advpl
If ExistPage('teste')
  conout('teste.aph compilado neste RPO')
Else
  conout('teste.aph NAO compilado neste RPO')
Endif
```

---

#### EXISTUSRPAGE

```
EXISTUSRPAGE(cAhuFile) --> lExist
```

Verifica se um arquivo `.AHU` está compilado no RPO do ambiente atual.

---

#### GETJOBPROFSTRING

```
GETJOBPROFSTRING(cKey, cDefault) --> cKeyValue
```

Recupera as configurações do Job da Working Thread atual.

```advpl
cJobType   := GetJobProfString('type', '(empty)')
cInstances := GetJobProfString('Instances', '(empty)')
cInacTime  := GetJobProfString('InactiveTimeout', '(default)')
cExpTime   := GetJobProfString('ExpirationTime', '(default)')
```

---

#### GETWEXVERSION

```
GETWEXVERSION() --> cBuildId
```

Retorna o identificador da versão de Release das funções de Infra-Estrutura APWEBEX no formato `<LIB> V.AAMMDDHHmm`.

**Tabela de símbolos:**

| Símbolo | Descrição |
|---------|-----------|
| `AA` | Ano de geração da Lib |
| `MM` | Mês da geração da Lib |
| `DD` | Dia da geração da Lib |
| `HH` | Horário da geração da Lib |
| `mm` | Minutos do Horário de Geração da Lib |
| `(HTTP)` | Versão compilada com envio progressivo de HTML simultâneo para o browser |

Exemplo: `APWEBEX Version 3.0312021900 (HTTP)`

---

#### HEXSTRDUMP

```
HEXSTRDUMP(cString, [nStart], [nLength]) --> cHExDump
```

Gera uma string em formato de Dump Hexadecimal (16 bytes por linha em hexadecimal + separador `|` + 16 caracteres em ANSI). Caracteres de controle (ASCII < 32) são convertidos para `_` (underline).

> **Observação:** Não passar string maior que **240 Kb** — a string final gerada é em média 4,2 vezes maior que a original.

---

#### HTMLNOTAGS

```
HTMLNOTAGS(cStrHtml) --> cStrNoTags
```

Converte os caracteres `<`, `>`, `&` e `"` de uma String HTML para caracteres não interpretáveis, evitando que o browser interprete o conteúdo como tag HTML.

```advpl
cHtml += '<INPUT TYPE="text" VALUE="' + HtmlNoTags(cInput) + '">'
```

---

#### HTTPISWEBEX

```
HTTPISWEBEX() --> lIsApWEBEX
```

Retorna `.T.` caso o ambiente de execução atual seja uma Working Thread WEBEX, inicializada pela função `STARTWEBEX`.

---

#### ISEMAIL

```
ISEMAIL(cEMail) --> lEmailOk
```

Valida se uma string está em formato válido de endereço de e-mail. Regra: iniciado por um caractere, contendo apenas `a-z`, `0-9`, `@`, `.`, `-`, `_`; deve conter exatamente uma arroba e pelo menos um ponto após ela.

---

#### LOWERACE

```
LOWERACE(cString) --> cStrLower
```

Converte todos os caracteres de uma String para "minúsculo", semelhante a `LOWER()`, porém considera e converte também caracteres acentuados em ANSI.

---

#### NTOC

```
NTOC(nNumero, nBase, nTamStr) --> cString
```

Converte um número em notação decimal para um número representado por String usando uma base numérica entre 2 e 36, preenchendo com zeros à esquerda até o tamanho especificado.

```advpl
nNum1 := CTON('01101001', 2)  // Binário → decimal
nNum1++
cNum1 := NtoC(nNum1, 2, 8)   // Decimal → binário novamente
// cNum1 será "01101010"
```

---

#### REDIRPAGE

```
REDIRPAGE(cUrl, [cTarget], [nTime]) --> cScript
```

Gera um script HTML/JavaScript que, ao ser executado no Browser, redireciona para o link passado como parâmetro.

| Parâmetro | Tipo | Descrição | Default |
|-----------|------|-----------|---------|
| `cUrl` | Caracter | Link para onde deve ir o redirecionamento. | — |
| `cTarget` | Caracter | Destino do redirecionamento. | `_self` |
| `nTime` | Numérico | Delay em segundos antes do redirecionamento. | — |

```advpl
// Volta ao login se parâmetro não informado
If Empty(httpget->meuparam)
  cHtml := RedirPage('/W_Login.apw')
Else
  cHtml := ExecInPage('FormTeste')
Endif
```

---

#### RETSQLACE

```
RETSQLACE(cStrFind) --> cStrQuery
```

Auxiliar na montagem de queries de busca de caracteres acentuados. Remove acentos, converte para minúsculo e troca vogais e cedilhas por sequências para busca posicional.

```advpl
cFind := 'acentuação'
cQuery := "SELECT * FROM " + RetSqlTab('ZZ1')
cQuery += " WHERE LOWER(ZZ1_TITULO) LIKE '%" + RetSqlAce(cFind) + "%'"
```

---

#### RETSQLCOND

```
RETSQLCOND(cAliases) --> cSqlWhere
```

Auxiliar na montagem de queries para busca em tabelas no padrão ERP Microsiga. Retorna as expressões de filtro de dados considerando filial atual (`xFilial`) e registros deletados. Mantida apenas por compatibilidade — prefira `RetSqlFil()` + `RetSqlDel()` para melhor performance.

---

#### RETSQLDEL

```
RETSQLDEL(cAliases) --> cSqlWhere
```

Retorna a expressão SQL para filtrar registros deletados (`D_E_L_E_T_`) das tabelas passadas como parâmetro.

---

#### RETSQLFIL

```
RETSQLFIL(cAliases, [cCompFil]) --> cSQlWhere
```

Retorna as expressões de filtro de dados para considerar o campo filial atual (`xFilial`) de acordo com o modo de abertura do arquivo no ERP (`X2_MODO`).

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `cAliases` | Caracter | Um ou mais aliases separados por vírgula. |
| `cCompFil` | Caracter | Filial FIXA a ser comparada. Se omitido, usa `xFilial()` de cada alias. |

---

#### RETSQLTAB

```
RETSQLTAB(cAliasList) --> cStrQuery
```

Recebe um ou mais aliases separados por vírgula e retorna os nomes físicos das tabelas e seus respectivos aliases, para inserção na cláusula `FROM` da query.

---

#### SEPARA

```
SEPARA(cString, cToken, lEmpty) --> aTokens
```

Parseia uma string a partir de um determinado separador, retornando um Array com os elementos identificados.

```advpl
aInfo := Separa('1,2,,4', ',', .F.)  // Resulta {'1','2','4'}
aInfo := Separa('1,2,,4', ',', .T.)  // Resulta {'1','2','','4'}
```

---

#### UNESCAPE

```
UNESCAPE(cString) --> cUnEscaped
```

Realiza a operação inversa à função `Escape()`, convertendo os caracteres especiais em notação `%HH` de volta para ASCII.

---

#### UPPERACE

```
UPPERACE(cString) --> cStrUpper
```

Converte todos os caracteres de uma String para "maiúsculo", semelhante a `UPPER()`, porém considera e converte também caracteres acentuados em OEM e ANSI.

---

#### UPSTRTRAN

```
UPSTRTRAN(cString, cSearch, [cReplace], [nStart], [nCount]) --> cNewString
```

Similar à função `Strtran()`, porém realiza a busca da ocorrência da string **sem diferenciação de maiúsculas/minúsculas** (case-insensitive).

---

#### VALTOSQL

```
VALTOSQL(xExpressao) --> cQryExpr
```

Auxiliar na montagem de queries, convertendo um conteúdo variável Advpl para a string correspondente:

- **Caracter** → colocado entre aspas simples (aspas simples internas removidas).
- **Numérico** → convertido para caracter com 2 casas decimais.
- **Data** → convertido para formato ANSI (`AAAAMMDD`) entre aspas simples.

```advpl
cQuery := "SELECT * FROM FA2010 "
cQuery += "WHERE FA2_FILIAL = " + ValToSql('02')
cQuery += "AND FA2_DTINC <= " + ValToSql(date())
// Equivalente a:
// WHERE FA2_FILIAL = '02' AND FA2_DTINC <= DTOS(date())
```

---

#### VARINFO

```
VARINFO(cId, xVar, [nMargem], [lHtml], [lEcho]) --> cVarInfo
```

Gera um texto ASCII e/ou HTML com as informações sobre o conteúdo de uma variável de memória Advpl de qualquer tipo.

| Parâmetro | Tipo | Descrição | Default |
|-----------|------|-----------|---------|
| `cId` | Caracter | Nome atribuído à variável para análise. | — |
| `xVar` | Qualquer | Variável a ser examinada. | — |
| `nMargem` | Numérico | Margem esquerda inicial (×5 espaços). | `0` |
| `lHtml` | Lógico | `.T.` para retornar HTML, `.F.` para ASCII. | `.T.` |
| `lEcho` | Lógico | Define se o Echo deve ser enviado ao console. | `.T.` |

```advpl
cHtml += VarInfo('Date', date())
cHtml += VarInfo('Time', time())
```

---

#### WEBINFO

```
WEBINFO() --> cHtmlInfo
```

Desenvolvida para ser chamada através de uma requisição HTTP via link `.apl` ou `.apw`. Identifica e retorna uma página HTML com todos os parâmetros recebidos via requisição HTTP: GET, POST, Header HTTP, Cookies, content-type, Length, Content-disposition, SoapAction e OtherContent.

---

#### Exemplo das funções de acentuação ApWebEx

```advpl
cFrase := "não há EXPLICAÇÕES considerando excessões PARA O inexplicável."

cRetorno += "Original .......... " + cFrase           + CRLF
cRetorno += "Upper() ........... " + upper(cFrase)    + CRLF
cRetorno += "Lower() ........... " + lower(cFrase)    + CRLF
cRetorno += "Capital() ......... " + capital(cFrase)  + CRLF
cRetorno += "UPPERACE() ........ " + UPPERACE(cFrase) + CRLF
cRetorno += "LOWERACE() ........ " + LOWERACE(cFrase) + CRLF
cRetorno += "CAPITALACE() ...... " + CAPITALACE(cFrase) + CRLF

/* Resultado:
   Original .......... não há EXPLICAÇÕES considerando excessões PARA O inexplicável.
   Upper() ........... NãO Há EXPLICAÇÕES CONSIDERANDO EXCESSõES PARA O INEXPLICáVEL.
   Lower() ........... não há explicaÇÕes considerando excessões para o inexplicável.
   Capital() ......... Não Há ExplicaÇÕes Considerando Excessões Para O Inexplicável.
   UPPERACE() ........ NÃO HÁ EXPLICAÇÕES CONSIDERANDO EXCESSÕES PARA O INEXPLICÁVEL.
   LOWERACE() ........ não há explicações considerando excessões para o inexplicável.
   CAPITALACE() ...... Não Há Explicações Considerando Excessões Para O Inexplicável.
*/
```

#### Exemplos das funções NTOC e CTON

```advpl
nNum1 := CTON('01101001', 2)   // Converte binário para decimal
nNum2 := CTON('00DA25FE', 16)  // Converte Hexadecimal para decimal
nNum1++
nNum2++
cNum1 := NtoC(nNum1, 2, 8)    // Converte para binário novamente
cNum2 := NtoC(nNum2, 16, 8)   // Converte para Hexa novamente
// cNum1 = "01101010" / cNum2 = "00DA25FF"
```

---

### Comandos WEB EXTENDED

#### WEB EXTENDED INIT

```
WEB EXTENDED INIT <cHtml> [START <cFnStart>]
```

Deve ser utilizado juntamente com `WEB EXTENDED END` quando montamos uma função Web. Realiza uma pré-validação que certifica que a execução somente será realizada caso a thread atual seja uma Thread WEBEX.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `cHtml` | Caracter | Variável String (vazia) para armazenar o HTML de retorno ao Browser. |
| `START cFnStart` | Caracter | Função Advpl de pré-validação (sem parênteses). Retornando string vazia, executa normalmente. Retornando string não-vazia, desvia para após o `WEB EXTENDED END`. |

#### WEB EXTENDED END

```
WEB EXTENDED END <cHtml> [START <cFnStart>]
```

Fecha a seção aberta pelo comando `WEB EXTENDED INIT`. Deve haver exatamente **uma ocorrência** de cada comando por função.

---

#### Comandos OPEN QUERY / CLOSE QUERY

```
OPEN QUERY <cQuery> ALIAS <cAlias> [NOCHANGE]
CLOSE QUERY cAlias
```

**OPEN QUERY** abre uma query no banco de dados através do RDD TOPCONN. Observações:
- Especificar comandos SQL, aliases e nomes de campos em **letras maiúsculas**.
- A cláusula `NOCHANGE` evita que a query seja submetida à `ChangeQuery()`.
- Uma query aberta por `OPEN QUERY` deve ser **necessariamente** fechada por `CLOSE QUERY` (não por `DbCloseArea()`).

---

### Pontos de Entrada APWEBEX

#### STARTWEBEX

```
STARTWEBEX([NIL]) --> lSucess
```

Executado na **inicialização** de cada Working Thread WEBEX. Deve retornar `.T.` para continuar ou `.F.` para eliminar a Working Thread da memória.

---

#### CONNECTWEBEX

```
CONNECTWEBEX(cFnLink) --> cHtmlVld
```

Executado **imediatamente antes** do processamento de uma requisição via link `.apw`. Permite pré-validação antes de cada processamento. Retornando string em branco, a execução continua normalmente; caso contrário, a string retornada é devolvida ao Browser.

---

#### RESETWEBEX

```
RESETWEBEX(cFnLink) --> cHtmlAdd
```

Executado **imediatamente após** o processamento de uma requisição `.apw`. Permite processamento adicional e retorno de HTML adicional ao browser. **Não** será executado em caso de erro fatal no `U_CONNECTWEBEX` ou na função principal.

---

#### FINISHWEBEX

```
FINISHWEBEX() --> NIL
```

Executado quando da **finalização** (fechamento) de uma Working Thread APWEBEX — seja por timeout ou por tempo total de permanência no ar. Não recebe parâmetros e não requer retorno.

---

#### ENDSESSION

```
ENDSESSION(cSessionId) --> NIL
```

Executado quando das sessions de um usuário são finalizadas por **timeout de inatividade**. Permite executar uma rotina Advpl nesse momento. Não é chamado quando se usa `httpfreesession()` manualmente.

---

#### WEBEXERROR

```
WEBEXERROR(oErrorObj, cErrorLog, cErrorHtml) --> cMsgHtml
```

Executado em caso de **erro fatal Advpl** durante a execução de uma Working Thread WEBEX. Permite montar uma mensagem de erro HTML customizada.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `oErrorObj` | Objeto | Objeto do Erro Advpl. |
| `cErrorLog` | Caracter | Mensagem ASCII gravada no `error.log`. |
| `cErrorHtml` | Caracter | HTML de erro original da rotina de tratamento. |

Retornando NIL ou string vazia, será exibido o HTML de erro padrão. Retornando uma string HTML, ela será mostrada ao usuário.

**Observações importantes:**
- A Working Thread que apresentou erro será **derrubada** após o retorno do HTML.
- O `error.log` será gerado normalmente, independentemente do retorno.
- Este ponto de entrada não é chamado em erros no `U_STARTWEBEX`, `U_FINISHWEBEX` ou `U_ENDSESSION`.
- Não utilize recursos que dependam de ambiente, disco, banco de dados ou Session neste ponto de entrada.
