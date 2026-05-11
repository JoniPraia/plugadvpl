# ADVPL WebServices – Desenvolvimento com Protheus

> **TOTVS S.A.** – Programação ADVPL WebService – Versão 12
> Todos os direitos autorais reservados pela TOTVS S.A. Proibida a reprodução total ou parcial sem prévia autorização por escrito da proprietária.

---

## Sumário

1. [Objetivo](#1-objetivo)
2. [Introdução aos WebServices](#2-introdução-aos-webservices)
   - [2.1 O que é um WebService / WSDL](#21-o-que-é-um-webservice--wsdl)
   - [2.2 O que é XML](#22-o-que-é-xml)
   - [2.3 O que é SOAP](#23-o-que-é-soap)
   - [2.4 O que é UDDI](#24-o-que-é-uddi)
3. [O Servidor Protheus como Servidor WebServices](#3-o-servidor-protheus-como-servidor-webservices)
4. [Configurando o Servidor de WebServices](#4-configurando-o-servidor-de-webservices)
5. [Módulos Web](#5-módulos-web)
6. [Explicando o INI do WebServices](#6-explicando-o-ini-do-webservices)
7. [WSINDEX – Índice de Serviços](#7-wsindex--índice-de-serviços)
   - [7.1 Processamento de Funções](#71-processamento-de-funções)
8. [Codificando o Serviço](#8-codificando-o-serviço)
9. [Testando o Serviço](#9-testando-o-serviço)
10. [Consumo de Serviços](#10-consumo-de-serviços)
11. [TWsdlManager](#11-twsdlmanager)
12. [Criando um WebService de Gravação](#12-criando-um-webservice-de-gravação)
    - [12.1 Definição de Estrutura](#121-definição-de-estrutura)
13. [Apêndices](#13-apêndices)
    - [13.1 Guia de Referência Rápida – Funções e Erros](#131-guia-de-referência-rápida--funções-e-erros)
    - [GetWSCError – Recuperação de Informações](#getwscerror--recuperação-de-informações)
    - [Códigos de Erro WSCERR000 a WSCERR073](#códigos-de-erro)
    - [Regras de Nomenclatura](#regras-de-nomenclatura)

---

## 1. Objetivo

Ao final do curso, o treinando deverá ter desenvolvido os seguintes conceitos, habilidades e atitudes:

**A) Conceitos:**
- Estruturas para implementação de aplicações ADVPL WebServices
- Introdução às técnicas de programação voltadas a múltiplos serviços baseados na estrutura de programação ADVPL
- Introdução aos conceitos de inserir, alterar, excluir e apresentação dos dados via protocolo SOAP

**B) Habilidades e técnicas:**
- Desenvolvimento de aplicações voltadas ao ERP/WebServices Protheus
- Análise de fontes de média complexidade
- Desenvolvimento de um serviço WebServices e seu Client

**D) Atitudes a serem desenvolvidas:**
- Adquirir conhecimentos através da análise das funcionalidades disponíveis no ERP Protheus
- Estudar a implementação de fontes com estruturas orientadas a objetos em WebServices

---

## 2. Introdução aos WebServices

### 2.1 O que é um WebService / WSDL

Web service é uma solução utilizada na integração de sistemas e na comunicação entre aplicações diferentes. Com esta tecnologia, é possível que novas aplicações possam interagir com aquelas que já existem e que sistemas desenvolvidos em plataformas diferentes sejam compatíveis.

Os Web services são componentes que permitem às aplicações enviar e receber dados em formato XML. Cada aplicação pode ter a sua própria "linguagem", que é traduzida para uma linguagem universal, o formato XML.

Para as empresas, os Web services podem trazer agilidade para os processos e eficiência na comunicação entre cadeias de produção ou de logística. Toda e qualquer comunicação entre sistemas passa a ser dinâmica e principalmente segura, pois não há intervenção humana.

Essencialmente, o Web Service faz com que os recursos da aplicação do software estejam disponíveis sobre a rede de uma forma normalizada. Outras tecnologias fazem a mesma coisa, como, por exemplo, os browsers da Internet acedem às páginas Web disponíveis usando por norma as tecnologias da Internet, HTTP e HTML. No entanto, estas tecnologias não são bem sucedidas na comunicação e integração de aplicações.

Utilizando a tecnologia Web Service, uma aplicação pode invocar outra para efetuar tarefas simples ou complexas, mesmo que as duas aplicações estejam em diferentes sistemas e escritas em linguagens diferentes. Os Web Services fazem com que os seus recursos estejam disponíveis para que qualquer aplicação cliente possa operar e extrair os recursos fornecidos.

Os Web Services são identificados por um URI (Uniform Resource Identifier), descritos e definidos usando XML (Extensible Markup Language). Um dos motivos que tornam os Web Services atrativos é o fato deste modelo ser baseado em tecnologias padrão, em particular XML e HTTP (Hypertext Transfer Protocol). Os Web Services são utilizados para disponibilizar serviços interativos na Web, podendo ser acessados por outras aplicações usando, por exemplo, o protocolo SOAP (Simple Object Access Protocol).

O objetivo dos Web Services é a comunicação de aplicações através da Internet. Esta comunicação é realizada com intuito de facilitar a EAI (Enterprise Application Integration) que significa a integração das aplicações de uma empresa, ou seja, interoperabilidade entre a informação que circula numa organização nas diferentes aplicações como, por exemplo, o comércio electrónico com os seus clientes e seus fornecedores. Esta interação constitui o sistema de informação de uma empresa. E, para além da interoperabilidade entre as aplicações, a EAI permite definir um workflow entre as aplicações e pode constituir uma alternativa aos ERPs (Enterprise Resource Planning).

**Tecnologias:**
As bases para a construção de um Web service são os padrões XML e SOAP. O transporte dos dados é realizado normalmente via protocolo HTTP ou HTTPS para conexões seguras (o padrão não determina o protocolo de transporte). Os dados são transferidos no formato XML, encapsulados pelo protocolo SOAP.

---

### 2.2 O que é XML

XML (eXtensible Markup Language) é uma recomendação da W3C para gerar linguagens de marcação para necessidades especiais. É um dos subtipos da SGML (Standard Generalized Markup Language) capaz de descrever diversos tipos de dados. Seu propósito principal é a facilidade de compartilhamento de informações através da internet.

Entre linguagens baseadas em XML incluem-se XHTML (formato para páginas Web), RDF, SDMX, SMIL, MathML (formato para expressões matemáticas), NCL, XBRL, XSIL e SVG (formato gráfico vetorial).

Em meados da década de 1990, o W3C começou a trabalhar em uma linguagem de marcação que combinasse a flexibilidade da SGML com a simplicidade da HTML. O princípio do projeto era criar uma linguagem que pudesse ser lida por software, e integrar-se com as demais linguagens. Sua filosofia seria composta por vários princípios importantes:

- Separação do conteúdo da formatação
- Simplicidade e legibilidade, tanto para humanos quanto para computadores
- Possibilidade de criação de tags sem limitação
- Criação de arquivos para validação de estrutura (chamados DTDs)
- Interligação de bancos de dados distintos
- Concentração na estrutura da informação, e não na sua aparência

O XML é um formato para a criação de documentos com dados organizados de forma hierárquica. Pela sua portabilidade, já que é um formato que não depende das plataformas de hardware ou de software, um banco de dados pode, através de uma aplicação, escrever em um arquivo XML, e um outro banco distinto pode ler então estes mesmos dados.

#### Vantagens e Desvantagens

**Vantagens técnicas:**
- É baseado em texto simples
- Suporta Unicode, permitindo que a maior parte da informação codificada em linguagem humana possa ser comunicada
- Pode representar as estruturas de dados relevantes da computação: listas, registros, árvores
- É auto documentado (DTDs e XML Schemas)
- A sintaxe restrita e requerimentos de parsing tornam os algoritmos de análise mais eficientes e consistentes
- É editável com diferentes níveis de automação, em qualquer ambiente

**Desvantagens técnicas:**

As desvantagens em geral se restringem às aplicações que não demandam maior complexidade, tais como vetores, listas associativas (chave-valor) e informações relativas à configuração. Os principais critérios para se avaliar a demanda por um formato mais simples são:

- **Velocidade:** a grande quantidade de informação repetida prejudicando a velocidade de transferência real de informação
- **Editabilidade txt:** o arquivo "XML simples" pode ser bem pouco intuitivo, dificultando sua edição por pessoas leigas

O formato properties é mais fácil de ser editado por leigos, e o JSON é um exemplo de um formato mais prático e rápido em contexto Javascript.

---

### 2.3 O que é SOAP

SOAP (Simple Object Access Protocol / Protocolo Simples de Acesso a Objetos) é um protocolo para troca de informações estruturadas em uma plataforma descentralizada e distribuída. Ele se baseia na Linguagem de Marcação Extensível (XML) para seu formato de mensagem, e normalmente baseia-se em outros protocolos da Camada de aplicação, notavelmente em RPC (Chamada de Procedimento Remoto) e HTTP.

SOAP pode formar a camada base de uma pilha de protocolos de web services, fornecendo um framework de mensagens básico sob o qual os serviços podem ser construídos. Este protocolo baseado em XML consiste de três partes:

1. Um **envelope**, que define o que está na mensagem e como processá-la
2. Um conjunto de **regras codificadas** para expressar instâncias dos tipos de dados definidos na aplicação
3. Uma **convenção** para representar chamadas de procedimentos e respostas

Geralmente servidores SOAP são implementados utilizando-se servidores HTTP, embora isto não seja uma restrição para funcionamento do protocolo. As mensagens SOAP são documentos XML que aderem a uma especificação fornecida pelo órgão W3C.

---

### 2.4 O que é UDDI

UDDI (Universal Description, Discovery and Integration) é um serviço de diretório onde empresas podem registrar (publicar) e buscar (descobrir) por serviços Web. UDDI é ainda um framework de plataforma independente para descrição de serviços, descobrindo as empresas, e integrar os serviços de negócios usando a internet. A comunicação é realizada através do SOAP e as interfaces web service são descritas por WSDL.

Um serviço de registro UDDI é um Web Service que gerencia informação sobre provedores, implementações e metadados de serviços. Provedores de serviços podem utilizar UDDI para publicar os serviços que eles oferecem. Usuários de serviços podem usar UDDI para descobrir serviços que lhes interessem e obter os metadados necessários para utilizar esses serviços.

A especificação UDDI define:
- APIs SOAP utilizadas para publicar e obter informações de um registro UDDI
- Esquemas XML do modelo de dados do registro e do formato das mensagens SOAP
- Definições WSDL das APIs SOAP
- Definições de registro UDDI (modelos técnicos - tModels) de diversos sistemas de identificação e categorização

---

## 3. O Servidor Protheus como Servidor WebServices

O servidor Protheus pode ser configurado para trabalhar como um servidor WebServices. O Protheus, a partir da versão AP7, possui ferramentas nativas e integradas com a LIB de Infraestrutura do ERP, para desenvolvimento de aplicações 'Cliente' e 'Server', utilizando a tecnologia dos Web Services.

Para melhor compreensão do assunto, os tópicos relacionados a ambos foram didaticamente separados em:
- **Aplicações Server**
- **Aplicações Cliente**

Nos tópicos 'Comandos' e 'Funções', são abordadas respectivamente as diretivas e funções da Lib de Infraestrutura do ERP disponibilizadas para o desenvolvimento de ambas as aplicações, Cliente e Server. No tópico 'Exemplos AdvPL', são demonstrados os exemplos 'atômicos' de uso das funções e comandos.

---

## 4. Configurando o Servidor de WebServices

Nos serviços HTTP e HTTPS, é possível especificar as configurações padrão deste protocolo, propriedades gerais aplicadas a todos os hosts e URLs de acesso utilizadas pelos projetos WebServices. A habilitação do serviço de HTTP é necessária para a instalação dos módulos WebService.

### Editando a Configuração HTTP

Para inserir / editar uma configuração HTTP:

1. Abra o Wizard localizado na pasta smartclient
2. Clique no ícone Wizard
3. No tópico "Servidor HTTP", posicionado o cursor sobre o item "HTTP", clique em "Editar Configuração" nas Ações Relacionadas
4. Clique em editar e a tela se abrirá

Será apresentada uma única janela contendo as configurações padrões atuais para o serviço de HTTP.

#### Campos da Configuração HTTP

| Campo | Descrição |
|---|---|
| **Protocolo Habilitado** | Permite desabilitar a utilização do protocolo http sem deletar as configurações atuais |
| **Nome da Instância** | Não disponível para edição. Informa que um módulo Web foi instalado no host "HTTP [default]" |
| **Path de Arquivos** | Especifica o diretório raiz a ser utilizado pelo protocolo "HTTP" para acesso a arquivos estáticos e imagens. Deve ser informado com unidade de disco e caminho completo |
| **Porta de Conexão** | Informa a porta de conexão utilizada. Para HTTP, a porta padrão é a 80 |
| **Ambiente** | Permite selecionar um ambiente (Environment) para atender às solicitações de processamento de links ".apl" |
| **Processo de Resposta** | Permite selecionar um processo WEB/WEBEX para atender às solicitações de processamento de links ".apw" |
| **Instâncias de Protocolo (mínimo e máximo)** | Especifica o número mínimo e máximo de processos internos referentes ao serviço de HTTP |
| **Path para Upload de Arquivos** | Configura o diretório a partir do qual serão gravados os arquivos enviados via http |
| **Timeout de Sessões WEBEX (em segundos)** | Define o tempo de permanência em inatividade em memória das variáveis de sessões. Padrão: 3600 segundos |

> **Nota:** Uma thread HTTP não possui, necessariamente, ligação implícita com uma Thread AdvPL. Um Web Browser, quando solicita um arquivo HTML ou uma imagem, estabelece uma conexão HTTP com o ByYou Application Server, recebe o dado solicitado e fecha esta conexão, mantendo a Thread HTTP disponível para atender outras requisições.

Para gravar as configurações atuais, deve-se clicar em "Finalizar". Ao confirmar a gravação, o arquivo `appserver.ini` será atualizado e o Assistente será reiniciado.

---

## 5. Módulos Web

Neste tópico, é possível instalar, configurar e excluir as configurações e arquivos adicionais pertinentes aos módulos Web disponibilizados pelo Sistema.

### Módulos Web Disponíveis

| Sigla | Descrição |
|---|---|
| DW | Data Warehouse |
| BSC | Balanced Scorecard |
| GE | Gestão Educacional |
| TCF | Terminal do Funcionário (RH on-line) |
| PP | Portal Protheus |
| WS | Web Services |
| WPS | WebPrint/WebSpool |
| MAK | Módulo Webex Makira (ambientes customizados) |
| GPR | Gestão de Pesquisas e Resultados |
| GAC | Gestão de Acervos |

### Instalando um Módulo Web

Para instalar um módulo Web:

1. Abra o Wizard localizado na pasta smartclient
2. Clique no ícone Wizard
3. Posicione o mouse sobre o tópico "Módulos Web" na árvore de tópicos e clique em "Novo Módulo" nas Ações Relacionadas
4. Clique em editar e a tela se abrirá

#### Campos da Tela de Instalação

**Módulo Web:** Selecione o módulo Web que deve ser instalado. Para instalação do módulo PP - Portal Protheus, GPR e GAC, é necessária a instalação prévia do módulo Web Services.

**Nome da Instância:** Informe o nome para identificação desta configuração do módulo Web; não utilize caracteres acentuados ou espaços.

**Diretório Raiz de Imagens (Web Path):** Informe o diretório para instalação das imagens e dos demais arquivos (`.css`, `.jar`, `.htm`, etc.). Este diretório será criado abaixo do diretório raiz (RootPath) do Ambiente selecionado.

**Environment:** Selecione o environment (ambiente) que será utilizado para execução do módulo.

**Habilitar processos na inicialização do Servidor:** Caso selecionado, os processos WEB/WEBEX criados serão automaticamente inseridos na configuração OnStart do ByYou Application Server.

**URL do Protheus Web Services:** Este campo somente é exibido na instalação do módulo WS - WebServices Protheus; deve ser preenchido com a URL da instalação do módulo Web Services, precedido por `HTTP://`.

5. Para prosseguir para a segunda tela, clique em "Avançar". O Assistente irá consistir as informações fornecidas.

> **Atenção:** Para instalação dos módulos Web, é necessário que os pacotes de instalação dos arquivos Web (`.MZP`) estejam disponíveis na pasta "SYSTEMLOAD" localizada abaixo do diretório raiz (RootPath) do Ambiente.

#### Configuração de Host x Empresas/Filiais

6. Informe os dados:

**Host:** Informe o endereço Web a partir do qual o módulo será acessado por meio de um browser.

Exemplos:
- `www.nomedosite.com.br` (para um ambiente Internet)
- `nomedoservidor` (para um ambiente Intranet)
- `nomedoservidor/ws` (para webservices)
- `nomedoservidor/pp` (para o Portal)

> Não se deve especificar o protocolo utilizado (como `HTTP://` ou `HTTPS://`).

**Selecione as Empresa/Filiais:** Na área "Seleção Empresas/Filiais", selecione a empresa/filial para a qual está sendo configurado este host.

7. Após informar o Host e selecionar um item, clique em "Relacionar".

> **Exemplo:** O módulo de WebServices não permite amarrar um mesmo host a mais de uma empresa/filial.

8. Se necessário excluir um relacionamento, posicione o cursor sobre este e clique em "Excluir".
9. Clique em "Avançar" para prosseguir.

#### Configuração de Processos

10. Informe os dados:

| Campo | Descrição |
|---|---|
| **Host Virtual** | Apresenta o host configurado |
| **Empresa/Filial** | Apresenta a empresa/filial relacionada |
| **Mínimo Usuários** | Informe a expectativa mínima de usuários que irão acessar o site |
| **Máximo Usuários** | Informe a expectativa máxima de usuários que irão acessar o site |

**Exemplo:** Mínimo: 5 / Máximo: 10 → O Protheus irá configurar o número mínimo de 1 processo e o máximo de 3 (média de 10 usuários por processo).

11. Para finalizar a instalação do módulo, clique em "Finalizar".

Ao confirmar a instalação, o pacote de arquivos do módulo Web será descompactado no diretório raiz de imagens informado, e o arquivo `appserver.ini` será atualizado com as definições pertinentes ao módulo (Host, Processos WEB/WEBEX).

Feche o assistente e levante o serviço em modo console para verificar o seu funcionamento.

---

## 6. Explicando o INI do WebServices

Um Web Service em AdvPL utiliza-se de working threads para atender as solicitações de processamento através do protocolo HTTP. Existem duas maneiras de habilitar um Web Service:

1. Através da criação da seção `[WebServices]` no arquivo de configuração (`appserver.ini`) do TOTVS | Application Server
2. Configuração manual de um ambiente working threads extended (WEBEX) no arquivo de configuração (`appserver.ini`)

A diferença entre ambas é que a segunda opção permite especificar mais detalhes do ambiente de execução do serviço, configurar os serviços de Web Sites simultaneamente e o atendimento diferenciado do processamento para mais de um host e diretórios virtuais.

### Configuração via Seção [WebServices]

```ini
[WebServices]
Enable=1           ; (Obrigatório) - Indica se o service está habilitado (1) ou não (0).
Environment=PROTHEUS ; (Obrigatório) - Indica qual environment do Server irá atender as requisições.
Conout=0           ; (Opcional) - Permite a exibição de informações dos status internos do serviço
                   ; (padrão=0:desabilitado). Utilizado APENAS para depuração.
Trace=0            ; (Opcional) - Habilita a gravação de um arquivo de log (wsstrace.log) (padrão=0).
PrepareIn=01,01    ; (Obrigatório) - Especifica qual a empresa e filial do ERP serão utilizados.
NameSpace=http://localhost:81  ; (Opcional) - Especifica o nome do namespace 'padrão'.
URLLocation=http://localhost:81 ; (Opcional) - Especifica a URL responsável pelo atendimento
                                ; às solicitações de processamento dos serviços.
```

> **Importante:** Esta configuração exige que a seção `[HTTP]` não esteja configurada no TOTVS | Application Server, pois a configuração irá internamente habilitar o serviço de HTTP e configurar o processo de resposta para o Web Services.

### Configuração Manual (WEBEX)

```ini
[HTTP]                ; Configuração do protocolo HTTP
Enable=1
Port=81
Path=F:\Protheus\Protheus12\Protheus_data\WEB

[Localhost]           ; Configuração do host da estação local
Defaultpage=wsindex.apw
ResponseJob=WSTeste

[WSTeste]             ; Configuração do job para atender aos Web Services.
Type=WEBEX            ; (Obrigatório) - Tipo do job para Web Services deve ser WEBEX.
OnStart=__WSSTART     ; (Obrigatório) - Configuração fixa para Web Services.
OnConnect=__WSCONNECT ; (Obrigatório) - Configuração fixa para Web Services.
Environment=ENVTeste  ; Especifique qual o ambiente do servidor Protheus.
Instances=2.5         ; (Obrigatório) - Indica a quantidade mínima e máxima de processos (Threads).
Conout=0              ; (Opcional) - Exibição de informações dos status internos (padrão=0).
Trace=1               ; (Opcional) - Habilita a gravação de um arquivo de log (wsstrace.log).
PrepareIn=99,01       ; (Obrigatório) - Especifica qual empresa e filial do ERP serão utilizadas.
NameSpace=http://localhost:81/  ; (Opcional) - Especifica o namespace 'padrão'.
URLLocation=http://localhost:81/ ; (Opcional) - Especifica a URL de atendimento.
```

---

## 7. WSINDEX – Índice de Serviços

Uma vez habilitada a configuração para Web Services, obtemos acesso a uma interface HTTP de consulta ao índice de serviços publicados. Para tal, basta:

1. Reiniciar o servidor TOTVS | Application Server após a configuração ser realizada
2. Abrir um navegador (por exemplo, Internet Explorer)
3. Acessar o link `http://<servidor>/wsindex.apw`

**Exemplo:** Caso o host configurado para os Web Services seja o host local (`localhost`), deve-se acessar:

```
http://localhost:90/ws
```

Na janela apresentada, são exibidos todos os serviços compilados e disponibilizados no repositório de objetos do ambiente configurado. Cada serviço ativo é um link para uma página que apresentará todos os métodos do serviço com um link do servidor TOTVS | Application Server que fornecerá a descrição do serviço (WSDL).

Através desta janela, é possível obter a descrição do serviço WSDL ao clicar no link disponível em "Descrição do Serviço (WSDL)". Além disso, cada método do serviço disponibilizado também é um link para uma página onde são apresentados os exemplos de pacotes SOAP que esse método espera para recepção de parâmetros e o modelo de retorno do serviço.

Caso o fonte-client AdvPL do serviço seja gerado e esteja compilado no repositório atual, a interface de consulta habilita a funcionalidade de teste do Web Services através da interface HTTP, apresentando no final da tela o botão **testar**. Ao clicar nesse botão, será montada uma tela HTML para que os parâmetros do serviço sejam preenchidos.

### 7.1 Processamento de Funções

A operação de buscar o horário atual no servidor não necessita de nenhum parâmetro para execução, tendo um retorno: o horário atual, no formato `hh:mm:ss`. A especificação de um WebService permite que um serviço seja declarado de modo a não receber nenhum parâmetro, mas exige que o Web Service sempre possua um retorno.

---

## 8. Codificando o Serviço

Para codificar um serviço, deve-se utilizar o TOTVS | Development Studio, criar um novo arquivo de programa e nele escrever o serviço.

### Exemplo: Serviço SERVERTIME

```advpl
#include "Protheus.ch"   // Linha 1
#include "ApWebSRV.ch"   // Linha 2
#include "TbiConn.ch"    // Linha 3

WSSERVICE SERVERTIME Description "VEJA O HORARIO"  // Linha 5

WSDATA Horário   AS String  // Linha 7
WSDATA Parâmetro AS String
// Tipos de dados disponíveis:
// String        - Dado AdvPL do tipo string.
// Date          - Dado AdvPL do tipo data.
// Integer       - Dado AdvPL do tipo numérico (apenas números inteiros).
// Float         - Dado AdvPL do tipo numérico (pode conter números inteiros e não-inteiros).
// Boolean       - Dado AdvPL do tipo booleano (lógico).
// Base64Binary  - Dado AdvPL do tipo string binária, aceitando todos os caracteres da tabela
//                 ASCII, de CHR(0) à CHR(255).

WSMETHOD GetServerTime Description "METHOD DE VISUALIZAÇÃO DO HORARIO"  // Linha 9
ENDWSSERVICE                                                              // Linha 10

WSMETHOD GetServerTime WSRECEIVE Parâmetro WSSEND Horário WSSERVICE SERVERTIME  // Linha 11
::Horário := TIME()  // Linha 12
Return .T.           // Linha 13
```

#### Explicação linha a linha

| Linha | Descrição |
|---|---|
| 1 | É especificada a utilização do include `Protheus.ch` ou `Totvs.ch`, contendo as definições dos comandos AdvPL e demais constantes |
| 2 | É especificada a include `APWebSrv.ch` ou `Totvswebsrv.ch`, que contém as definições de comandos e constantes utilizados nas declarações de estruturas e métodos do Web Service. **Obrigatório** para o desenvolvimento de Web Services |
| 3 | É especificada a utilização do include `TBICONN.CH`, contendo as definições dos comandos AdvPL para conectar ao banco e Protheus desejados |
| 5 | Com esta instrução, é definido o início da classe do serviço principal, à qual damos o nome de SERVERTIME |
| 6 | Dentro da estrutura deste serviço, é informado que um dos parâmetros utilizados chama-se `Horário`, e será do tipo string |
| 9 | Dentro da estrutura deste serviço, é informado que um dos métodos do serviço chama-se `GetServerTime` |
| 10 | Como não são necessárias mais propriedades ou métodos neste serviço, a estrutura do serviço é fechada |
| 11 | Aqui é declarado o fonte do método `GetServerTime`, que receberá parâmetros e informará que seu retorno será o dado `Horário` (declarado na classe do serviço como uma propriedade, do tipo string) |
| 12 | É atribuído na propriedade `::Horário` da classe deste serviço, o retorno da função AdvPL `TIME()`, que retorna a hora atual no servidor no formato `HH:MM:SS`. Deve-se utilizar "::" para alimentar a propriedade da classe atual |
| 13 | O método `GetServerTime` é finalizado nesta linha, retornando `.T.` (verdadeiro), indicando que o serviço foi executado com sucesso |

Após compilado o serviço, deve-se acessar novamente a página de índice de serviços (`wsindex.apw`) e verificar se o novo serviço compilado encontra-se lá.

---

## 9. Testando o Serviço

Para executar o teste dentro de um código, devemos primeiramente gerar um client de conexão do WS-Service. No TDS (TOTVS Development Studio), iremos criar o client.

Preencher com as informações:
- **Local:** Diretório que irá salvar o fonte
- **Nome do fonte:** Nome do arquivo PRW que será criado
- **Url:** Informar a URL do serviço que deseja criar o client

Ao clicar em concluir, o sistema irá gerar o código fonte do client do referido Services informado.

### Código Client Gerado pelo IDE

```advpl
#include "Totvs.ch"
#include "Totvswebsrv.ch"
/*
===============================================================================
WSDL Location   http://localhost:81/SERVERTTIME.apw?WSDL
Observações     Código-Fonte gerado por ADVPL WSDL Client 1.111215
                Alterações neste arquivo podem causar funcionamento incorreto
                e serão perdidas caso o código-fonte seja gerado novamente.
===============================================================================
*/
User Function _GGLXARK ; Return // "dummy" function - Internal Use

/*
-------------------------------------------------------------------------------
WSDL Service WSSERVERTTIME
-------------------------------------------------------------------------------
*/
WSCLIENT WSSERVERTTIME
    WSMETHOD NEW
    WSMETHOD INIT
    WSMETHOD RESET
    WSMETHOD CLONE
    WSMETHOD GETSERVERTTIME
    WSDATA _URL                  AS String
    WSDATA _HEADOUT              AS Array of String
    WSDATA _COOKIES              AS Array of String
    WSDATA cCPARAM               AS string
    WSDATA cGETSERVERTTIMERESULT AS string
ENDWSCLIENT

WSMETHOD NEW WSCLIENT WSSERVERTTIME
    ::Init()
    If !FindFunction("XMLCHILDEX")
        UserException("O Código-Fonte Client atual requer os executáveis do Protheus Build " + ;
                      "[7.00.111010P-20120314] ou superior. Atualize o Protheus ou gere o " + ;
                      "Código-Fonte novamente utilizando o Build atual.")
    EndIf
Return Self

WSMETHOD INIT WSCLIENT WSSERVERTTIME
Return

WSMETHOD RESET WSCLIENT WSSERVERTTIME
    ::cCPARAM            := NIL
    ::cGETSERVERTTIMERESULT := NIL
    ::Init()
Return

WSMETHOD CLONE WSCLIENT WSSERVERTTIME
    Local oClone := WSSERVERTTIME():New()
    oClone:_URL                  := ::_URL
    oClone:cCPARAM               := ::cCPARAM
    oClone:cGETSERVERTTIMERESULT := ::cGETSERVERTTIMERESULT
Return oClone

// WSDL Method GETSERVERTTIME of Service WSSERVERTTIME
WSMETHOD GETSERVERTTIME WSSEND cCPARAM WSRECEIVE cGETSERVERTTIMERESULT WSCLIENT WSSERVERTTIME
    Local cSoap := "", oXmlRet
    BEGIN WSMETHOD
        cSoap += '<GETSERVERTTIME xmlns="http://localhost:81/">'
        cSoap += WSSoapValue("CPARAM", ::cCPARAM, cCPARAM, "string", .T., .F., 0, NIL, .F.)
        cSoap += "</GETSERVERTTIME>"
        oXmlRet := SvcSoapCall(Self, cSoap, ;
                    "http://localhost:81/GETSERVERTTIME", ;
                    "DOCUMENT", "http://localhost:81/",, "1.031217", ;
                    "http://localhost:81/SERVERTTIME.apw")
        ::Init()
        ::cGETSERVERTTIMERESULT := WSAdvValue(oXmlRet, ;
            "_GETSERVERTTIMERESPONSE:_GETSERVERTTIMERESULT:TEXT", ;
            "string", NIL, NIL, NIL, NIL, NIL, NIL)
    END WSMETHOD
    oXmlRet := NIL
Return .T.
```

### Entendendo o Código Fonte do Client Gerado pelo IDE

O IDE gera o código informando os includes obrigatórios para o Client do WebService executar. Foi criada uma função `User Function _GGLXARK` aleatória para esse fonte, cujo nome poderá ser alterado pelo usuário posteriormente.

#### Método NEW

Trata-se de um processo de criação do objeto WebService para repassar todo o conteúdo do WebService gerado para uma variável definida pelo usuário. Internamente chama o método `INIT` e verifica se a build do Protheus é compatível.

#### Método INIT

Trata-se de um processo de criação do objeto WebService para disponibilizar a criação ou chamada de outros serviços disponível no repositório para complementar o WebService do cliente.

#### Método RESET

Trata-se de um processo de limpeza de variáveis do WebService para que você possa utilizá-lo novamente sem estar com as informações executadas anteriormente.

#### Método CLONE

Tratamento de gerar uma nova variável com o Objeto criado do WebService. Duplica a informação dos dados do WebService.

#### Método GETSERVERTTIME

Tratamento de executar o service disponível pelo WebService e retornar o processo executado por ele, retornando na variável `cGETSERVERTTIMERESULT`.

O código fonte utiliza a função `WSSoapValue`, que executa toda a estrutura do XML para dentro do WebService, criando as suas respectivas tags que o método solicitado exige. A função `WSAdvValue` retorna o valor que o WebService está disponibilizando.

Devemos compilar o código fonte gerado pelo DevStudio e podemos fazer tratamentos de notificações no Método com a função `SetSoapFault`.

### Exemplo com SetSoapFault

```advpl
WSMETHOD GetServerTTime WSRECEIVE cParam WSSEND Horário WSSERVICE SERVERTTIME
    Local nDay := dow(date())
    if nDay == 1 .Or. nDay == 7
        SetSoapFault("Metodo não disponível", ;
                     "Este serviço não funciona no fim de semana.")
        Return .F.
    Endif
    ::Horário := TIME()
Return .T.
```

---

## 10. Consumo de Serviços

Após gerar o client, devemos gerar um código fonte `User Function` para capturar a informação disponível do nosso WebService.

```advpl
#include "Protheus.ch"

User function XtempoX()
    Local oBj := nil
    oBj := WSSERVERTIME():new()
    oBj:GetServerTime()
    MsgStop(oBj:cGetServerTimeResult)
Return()
```

### Exemplo com tratamento de erros

```advpl
If oObj := WSXSERVERTIME():NEW()
    oObj:GETSERVERTIME(' ')
    msgAlert(oObj:cGETSERVERTIMERESULT)
Else
    cSvcError   := GetWSCError()    // Resumo do erro
    cSoapFCode  := GetWSCError(2)   // Soap Fault Code
    cSoapFDescr := GetWSCError(3)   // Soap Fault Description
    If !empty(cSoapFCode)
        // Caso a ocorrência de erro esteja com o fault_code preenchido,
        // a mesma teve relação com a chamada do serviço.
        MsgStop(cSoapFDescr, cSoapFCode)
    Else
        // Caso a ocorrência não tenha o soap_code preenchido,
        // ela está relacionada a uma outra falha, provavelmente local ou interna.
        MsgStop(cSvcError, 'FALHA INTERNA DE EXECUCAO DO SERVIÇO')
    Endif
Endif
Return(NIL)
```

---

## 11. TWsdlManager

A classe `TWsdlManager` faz o tratamento para arquivos WSDL (Web Services Description Language). Esta classe implementa métodos para identificação das informações de envio e resposta das operações definidas, além de métodos para envio e recebimento do documento SOAP.

A classe trabalha com 2 tipos de dados:
- **Tipos complexos:** seções do XML (ex.: tag "cliente" que contém dados do cliente dentro)
- **Tipos simples:** tags que recebem valor diretamente (ex.: tag "nome" que recebe o nome do cliente)

`TWsdlManager` irá realizar o parse de um WSDL, seja por uma URL ou por arquivo, e irá montar internamente uma lista com os tipos simples e outra com os tipos complexos.

A lista de tipos complexos terá somente os tipos complexos que tenham número variável de ocorrências (mínimo diferente do máximo). Através do método `NextComplex` é possível verificar quais são esses elementos, chamado em recursão até retornar Nil. Para cada elemento retornado deve-se definir a quantidade de vezes que a tag irá aparecer no XML final (SOAP) através do método `SetComplexOccurs`.

Os tipos simples podem ter seus valores definidos através dos métodos `SetValue` (para 1 valor apenas) ou `SetValues` (para mais de 1 valor).

### Exemplo de uso do TWsdlManager

```advpl
Local oWsdl
Local lOk
Local aOps    := {}
Local aComplex := {}
Local aSimple  := {}

// Cria o objeto da classe TWsdlManager
oWsdl := TWsdlManager():New()

// Faz o parse de uma URL
lOk := oWsdl:ParseURL("http://localhost:90/ws/SERVERTIME.apw?WSDL")
if lOk == .F.
    MsgStop(oWsdl:cError, "ParseURL() ERROR")
    Return
endif

// Lista os Métodos do serviço
aOps := oWsdl:ListOperations()

// Seta a operação a ser utilizada
lOk := oWsdl:SetOperation("GETSERVERTIME")
if !lOk
    MsgStop(oWsdl:cError, "SetOperation(ConversionRate) ERROR")
    Return
Endif

// Verifica o tipo de parâmetro e retorna os campos que irão receber valor
aComplex := oWsdl:NextComplex()
aSimple  := oWsdl:SimpleInput()

// Passando os valores para o parâmetro do método
xRet := oWsdl:SetValue(0, "000")

// Exibe a mensagem que será enviada
conout(oWsdl:GetSoapMsg())

// Faz a requisição ao WebService
lOk := oWsdl:SendSoapMsg()
if !lOk
    MsgStop(oWsdl:cError, "SendSoapMsg() ERROR")
    Return
endif

// Recupera os elementos de retorno, já parseados
cResp := oWsdl:GetParsedResponse()

// Monta um array com a resposta transformada
aElem := StrTokArr(cResp, chr(10))
MsgInfo(SubStr(aElem[2], AT(":", aElem[2]) + 1))

Return(NIL)
```

> **Exercício:**
> 1. Crie um WebService que apresente a data de Hoje pelo sistema.
> 2. Crie um cliente para ler esse WebService.
> 3. Crie uma rotina para capturar a data do seu WebService e o horário do WebService servertime.

---

## 12. Criando um WebService de Gravação

### 12.1 Definição de Estrutura

Iremos gerar um WebService para a gravação de Clientes. Para isso, devemos saber quais são as empresas e filiais disponíveis e a forma que o Cliente irá nos enviar os dados para serem gravados nos bancos de dados da respectiva empresa e filial.

Estrutura do trabalho:
- Gerar um método de apresentação de Empresa e Filial
- Demonstrar uma estrutura adequada para apresentar as empresas e filiais
- Demonstrar uma estrutura para receber os dados de Clientes
- Demonstrar uma estrutura para criticar a informação enviada pelo Client
- Executar a gravação dos dados

---

### Passo 1 – Método de Apresentação de Empresa e Filial

#### Declaração do WebService CTT

```advpl
#include "Totvs.ch"
#include "Totvswebsrv.ch"

WsService CTT description "Treinamento do WebService para o Curso CTT"
    Wsdata cCodEmp  as String                   // código da empresa
    Wsdata aEmpresa as array of EstruturaEmp    // estrutura inteira do sigamat.emp
    Wsdata cRet     as String                   // Mensagem de Retorno
    WsMethod LISTAEMPRESA DESCRIPTION "APRESENTA TODOS OS DADOS DO SIGAMAT.EMP DO CLIENTE"
EndWsservice
```

#### Estrutura EstruturaEmp (WsStruct)

```advpl
WsStruct EstruturaEmp
    WsData M0_CODIGO    As String
    WsData M0_CODFIL    As String
    WsData M0_FILIAL    As String
    WsData M0_NOME      As String
    WsData M0_NOMECOM   As String
    WsData M0_ENDCOB    As String
    WsData M0_CIDCOB    As String
    WsData M0_ESTCOB    As String
    WsData M0_CEPCOB    As String
    WsData M0_ENDENT    As String
    WsData M0_CIDENT    As String
    WsData M0_ESTENT    As String
    WsData M0_CEPENT    As String
    WsData M0_CGC       As String
    WsData M0_INSC      As String
    WsData M0_TEL       As String
    WsData M0_EQUIP     As String
    WsData M0_SEQUENC   As String
    WsData M0_DOCSEQ    As INTEGER
    WsData M0_FAX       As String
    WsData M0_PRODRUR   As String
    WsData M0_BAIRCOB   As String
    WsData M0_BAIRENT   As String
    WsData M0_COMPCOB   As String
    WsData M0_COMPENT   As String
    WsData M0_TPINSC    As Integer
    WsData M0_CNAE      As String
    WsData M0_FPAS      As String
    WsData M0_ACTRAB    As String
    WsData M0_CODMUN    As String
    WsData M0_NATJUR    As String
    WsData M0_DTBASE    As String
    WsData M0_NUMPROP   As Integer
    WsData M0_MODEND    As String
    WsData M0_MODINSC   As String
    WsData M0_CAUSA     As String
    WsData M0_INSCANT   As String
    WsData M0_TEL_IMP   As String
    WsData M0_FAX_IMP   As String
    WsData M0_TEL_PO    As String
    WsData M0_FAX_PO    As String
    WsData M0_IMP_CON   As String
    WsData M0_CODZOSE   As String
    WsData M0_DESZOSE   As String
    WsData M0_COD_ATV   As String
    WsData M0_INS_SUF   As String
    WsData M0_EMERGEN   As String
    WsData M0_LIBMOD    As String
    WsData M0_TPESTAB   As String
    WsData M0_DTAUTOR   As date
    WsData M0_EMPB2B    As String
    WsData M0_CAIXA     As String
    WsData M0_LICENSA   As String
    WsData M0_CORPKEY   As String
    WsData M0_CHKSUM    As Integer
    WsData M0_DTVLD     As date
    WsData M0_PSW       As String
    WsData M0_CTPSW     As String
    WsData M0_INTCTRL   As String
    WsData M0_INSCM     As String
    WsData M0_NIRE      As String
    WsData M0_DTRE      As date
    WsData M0_CNES      As String
    WsData M0_PSWSTRT   As String
    WsData M0_DSCCNA    As String
    WsData M0_ASSPAT1   As String
    WsData M0_ASSPAT2   As String
    WsData M0_ASSPAT3   As String
    WsData M0_SIZEFIL   As Integer
    WsData M0_LEIAUTE   As String
    WsData M0_PICTURE   As String
    WsData M0_STATUS    As String
    WsData M0_RNTRC     As String
    WsData M0_DTRNTRC   As date
    WsData X_MENSAGEM   As String
EndWsStruct
```

#### Implementação do Método LISTAEMPRESA

```advpl
WsMethod LISTAEMPRESA WsReceive cCodEmp WsSend aEmpresa WsService CTT
    Local cEmp   := "99"
    Local cFil   := "01"
    Local aTab   := {"SA1"}
    Local aRet   := {}
    Local nDados := 0

    // Abre a conexão com o banco e a empresa padrão
    RpcSetEnv(cEmp, cFil,,, 'FIN', 'ListEmpresa', aTab)

    if cCodEmp != 'Abrir'
        ::cRet := "Palavra Chave Invalida"
        aadd(aEmpresa, WsClassNew("EstruturaEmp"))
        aEmpresa[1]:M0_CODIGO  := ""
        aEmpresa[1]:M0_CODFIL  := ""
        aEmpresa[1]:M0_FILIAL  := ""
        aEmpresa[1]:M0_NOME    := ""
        // ... (demais campos zerados/vazios conforme necessário)
        aEmpresa[1]:X_MENSAGEM := ::cRet
        Return .t.
    endif

    aRet := SM0->(GETAREA())
    WHILE SM0->(!EOF())
        nDados += 1
        aadd(aEmpresa, WsClassNew("EstruturaEmp"))
        aEmpresa[nDados]:M0_CODIGO  := SM0->M0_CODIGO
        aEmpresa[nDados]:M0_CODFIL  := SM0->M0_CODFIL
        aEmpresa[nDados]:M0_FILIAL  := SM0->M0_FILIAL
        aEmpresa[nDados]:M0_NOME    := SM0->M0_NOME
        aEmpresa[nDados]:M0_NOMECOM := SM0->M0_NOMECOM
        // ... (demais campos lidos do SM0)
        aEmpresa[nDados]:X_MENSAGEM := "Sucesso " + strzero(nDados, 2)
        SM0->(DBSKIP())
    END
    RESTAREA(aRet)
```

---

### Passo 2 – WebService CTT: Explicação

Este código apresenta a criação do WebService chamado CTT com a Descrição "Treinamento do WebService para o Curso CTT". A variável `AEMPRESA` será um array com a estrutura definida pelo método `WsStruct`. Esta estrutura irá montar um XML com o nome de cada variável:

```xml
<aEmpresa>
    <M0_CODIGO>01</M0_CODIGO>
    <!-- ... -->
</aEmpresa>
```

O Método `LISTAEMPRESA` segue a seguinte regra:
- `WsReceive cCodEmp`: estou recebendo um código
- `WsSend aEmpresa`: Estou devolvendo um array com dados
- `WsService CTT`: Estou utilizando os métodos e variáveis do WebService CTT

Caso a palavra chave `cCodEmp` não esteja correta, ele entra no IF, alimenta a variável `::cRet` com a frase "Palavra Chave Inválida" e cria o Array `aEmpresa` com a estrutura definida anteriormente via `aadd(aEmpresa, WsClassNew("EstruturaEmp"))`.

Se a palavra chave estiver correta, o sistema abre a tabela de empresa SM0 (Sigamat.emp) e começa a fazer um loop correndo todos os registros encontrados nessa tabela.

---

### Passo 3 – WebService de Gravação de Clientes

#### Declaração das Variáveis e Estrutura

```advpl
// Declaração WSDATA
WSDATA ACLIENTE AS CLIENTES     // ESTRUTURA DE DADOS RECEBIDOS DO CLIENTE
WsData _cEmp    as String
WsData _cFil    as String
WSDATA CREGSA1  AS string       // RETORNO DA MENSAGEM DO EXECAUTO
WSDATA CCPF     AS string       // VARIAVEL PARA RECEBER O CPF DO CLIENTE

// Criação da estrutura de dados do Cliente
WsStruct CLIENTES
    WsData A1_COD     as String
    WsData A1_LOJA    as String
    WsData A1_NOME    as String
    WsData A1_NREDUZ  as String
    WsData A1_END     as String
    WsData A1_MUN     as String
    WsData A1_CGC     as String
    WsData A1_INSCRM  as String
    WsData A1_EMAIL   as String
    WsData A1_PAIS    as String
    WsData A1_ATIVO   as String
    WsData A1_CODPAIS as String
    WsData A1_SISTORI as String
    WsData A1_PESSOA  as String
    WsData A1_TIPO    as String
    WsData A1_ESTADO  as String
    WsData A1_EST     as String
    WsData A1_COD_MUN as String
    WsData A1_ENDNUM  as String
    WsData A1_BAIRRO  as String
    WsData A1_CEP     as String
EndWsStruct
```

#### Implementação do Método GRAVACLIENTE

```advpl
WSMETHOD GRAVACLIENTE WSRECEIVE ACLIENTE,CCPF,_cEmp,_cFil WSSEND CREGSA1 WSSERVICE CTT
    Local cEmp     := _cEmp
    Local cFil     := _cFil
    Local aTab     := {"SA1"}
    Local cPdCpf   := ""
    Local aDat     := {}
    Local aSa1Stru := {}
    Local aComplem := {}
    Local cCodigo  := ""
    Local cLoja    := ""
    Local NOPC     := 3
    Local bQuery   := {|X| Iif(Select(X) > 0, (X)->(dbCloseArea()), Nil), ;
                           dbUseArea(.T., "TOPCONN", TCGENQRY(,,cQuery), X, .F., .T.), ;
                           dbSelectArea(X), ;
                           (X)->(dbGoTop())}

    Private lMsErroauto   := .f.
    Private lMsHelpAuto   := .f.
    Private lautoErrNoFile := .T.
```

As 4 variáveis recebidas do client são:
- `ACLIENTE` – Estrutura criada dos dados necessários para receber do cliente a informação para ser gravada no Protheus
- `CCPF` – Variável do CPF do cliente para análise se já existe na base de dados (caso exista, será atualizado com os dados novos)
- `_cEmp` – Empresa que o cliente deve ser inserido
- `_cFil` – Filial da empresa que o cliente deve ser inserido

#### Rotina de Abertura do Ambiente

```advpl
    // Abre a conexão com o banco e a empresa padrão
    RpcSetEnv(cEmp, cFil,,, 'FIN', 'ListEmpresa', aTab)
```

#### Análise de Importação e Criação da Estrutura de Retorno

```advpl
    cPdCpf := tamsx3("A1_CGC")[1]

    // Cria estrutura de retorno
    ::ACLIENTE := WsClassNew('CLIENTES')

    DBSELECTAREA("SA1")
    SA1->(DBSETORDER(3))
    IF SA1->(DBSEEK(XFILIAL("SA1") + PADR(CCPF, cPdCpf)))
        NOPC    := 4
        cCodigo := SA1->A1_COD
        cLoja   := SA1->A1_LOJA
    ENDIF

    // Iniciando a gravação do cadastro do cliente
    AADD(aSa1Stru, {'A1_COD',     "C", 6,  0})
    AADD(aSa1Stru, {'A1_LOJA',    "C", 2,  0})
    AADD(aSa1Stru, {'A1_NOME',    "C", 50, 0})
    AADD(aSa1Stru, {'A1_NREDUZ',  "C", 40, 0})
    AADD(aSa1Stru, {'A1_END',     "C", 50, 0})
    AADD(aSa1Stru, {'A1_MUN',     "C", 10, 0})
    AADD(aSa1Stru, {'A1_COD_MUN', "C", 10, 0})
    AADD(aSa1Stru, {'A1_PESSOA',  "C", 10, 0})
    AADD(aSa1Stru, {'A1_CGC',     "C", 20, 0})
    AADD(aSa1Stru, {'A1_INSCRM',  "C", 30, 0})
    AADD(aSa1Stru, {'A1_EMAIL',   "C", 50, 0})
    AADD(aSa1Stru, {'A1_ATIVO',   "C", 50, 0})
    AADD(aSa1Stru, {'A1_CODPAIS', "C", 50, 0})
    AADD(aSa1Stru, {'A1_PAIS',    "C", 50, 0})
    AADD(aSa1Stru, {'A1_SISTORI', "C", 60, 0})
    AADD(aSa1Stru, {'A1_TIPO',    "C", 60, 0})
    AADD(aSa1Stru, {'A1_ESTADO',  "C", 60, 0})
    AADD(aSa1Stru, {'A1_EST',     "C", 60, 0})
    AADD(aSa1Stru, {'A1_ENDNUM',  "C", 60, 0})
    AADD(aSa1Stru, {'A1_BAIRRO',  "C", 60, 0})
    AADD(aSa1Stru, {'A1_CEP',     "C", 60, 0})

    // Analisa se existem outros campos obrigatórios que não estavam na estrutura
    SX3->(DBSETORDER(1))
    SX3->(DBSEEK("SA1"))
    WHILE SX3->(!EOF()) .AND. SX3->X3_ARQUIVO == "SA1"
        IF aScan(aSa1Stru, {|X| alltrim(x[1]) == alltrim(SX3->X3_CAMPO)}) = 0 ;
                .AND. X3OBRIGAT(SX3->X3_CAMPO)
            AADD(aComplem, {alltrim(SX3->X3_CAMPO), SX3->X3_TIPO, SX3->X3_TAMANHO, SX3->X3_DECIMAL})
        ENDIF
        SX3->(DBSKIP())
    END

    // Regra de gravação do Array Recebido
    aEval(aSa1Stru, {|x|
        aadd(aDat, {x[1], ;
                    iif(valtype(&('ACLIENTE:' + x[1])) != "U", &('ACLIENTE:' + x[1]), ;
                    iif(x[2] == 'C', CRIAVAR(x[1]), ;
                    iif(x[2] == 'D', DATE(), ;
                    iif(x[2] == 'N', 1, ;
                    iif(x[2] == 'L', .F., " "))))), ;
                    nil})
    })

    // Tratamento para campos que passaram a ser obrigatórios após a criação do WebService
    aEval(aComplem, {|x| aadd(aDat, {x[1], CRIAVAR(x[1]), nil})})
```

#### Identificação dos Campos e Busca de Código

```advpl
    nA1COD  := aScan(adat, {|x| alltrim(x[1]) == 'A1_COD'})
    nA1LOJ  := aScan(adat, {|x| alltrim(x[1]) == 'A1_LOJA'})

    if nA1COD > 0
        IF NOPC == 3
            cCodigo := GETSXENUM("SA1", "A1_COD")
            CONFIRMSX8()
            cLoja := CRIAVAR("A1_LOJA")
        ENDIF
        ADAT[nA1COD][2] := cCodigo
        ADAT[nA1LOJ][2] := cLoja
    ENDIF

    nA1FILI := aScan(adat, {|x| alltrim(x[1]) == 'A1_FILIAL'})
    if nA1FILI > 0
        ADAT[nA1FILI][2] := XFILIAL('SA1')
    ENDIF

    nA1CGC := aScan(adat, {|x| alltrim(x[1]) == 'A1_CGC'})
    if nA1CGC > 0
        ADAT[nA1CGC][2] := CCPF
    ENDIF

    // Busca o código do município via query
    nA1Est   := aScan(adat, {|x| alltrim(x[1]) == 'A1_EST'})
    nA1MUN   := aScan(adat, {|x| alltrim(x[1]) == 'A1_MUN'})
    nA1CDMUN := aScan(adat, {|x| alltrim(x[1]) == 'A1_COD_MUN'})
    if nA1CDMUN > 0
        cQuery := "SELECT A.CC2_CODMUN FROM " + RETSQLNAME("CC2") + " A " + ;
                  "WHERE A.CC2_FILIAL = '" + xFilial("CC2") + "' " + ;
                  "AND A.CC2_EST = '" + alltrim(ADAT[nA1Est][2]) + "' " + ;
                  "AND A.CC2_MUN = '" + alltrim(ADAT[nA1MUN][2]) + "' " + ;
                  "AND D_E_L_E_T_ = ' '"
        CONOUT(cQuery)
        Eval(bQuery, "TMP")
        ADAT[nA1CDMUN][2] := TMP->CC2_CODMUN
    ENDIF

    nA1CPAIS := aScan(adat, {|x| alltrim(x[1]) == 'A1_CODPAIS'})
    nA1PAIS  := aScan(adat, {|x| alltrim(x[1]) == 'A1_PAIS'})
    if nA1CPAIS > 0 .AND. nA1PAIS > 0
        ADAT[nA1CPAIS][2] := posicione("CCH", 2, XFILIAL("CCH") + UPPER(ADAT[nA1PAIS][2]), "CCH_PAIS")
    ENDIF
    nA1PAIS := aScan(adat, {|x| alltrim(x[1]) == 'A1_PAIS'})
    if nA1PAIS > 0
        ADAT[nA1PAIS][2] := posicione("SYA", 2, XFILIAL("SYA") + UPPER(ADAT[nA1PAIS][2]), "YA_CODGI")
        PRIVATE M->A1_PAIS := ADAT[nA1PAIS][2]
    ENDIF

    // Executa inicializador padrão (X3_RELACAO) para campos vazios
    SX3->(DBSETORDER(2))
    For nFor := 1 to len(aDat)
        if empty(aDat[nFor][2])
            SX3->(DBSEEK(aDat[nFor][1]))
            aDat[nFor][2] := &(SX3->X3_RELACAO)
        endif
    Next nFor
```

#### Normalização dos Dados

```advpl
    // Normalizando os Dados
    aDeletar := {}
    For nFor2 := 1 to len(adat)
        if VALTYPE(adat[nFor2]) <> "U"
            nLin := aScan(aSa1Stru, {|x| alltrim(x[1]) == alltrim(adat[nFor2][1])})
            if nLin <= 0 .OR. EMPTY(adat[nFor2][2])
                aadd(aDeletar, nFor2)
            else
                if valtype(adat[nFor2][2]) != aSa1Stru[nLin][2]
                    if empty(adat[nFor2][2])
                        do case
                            case aSa1Stru[nLin][2] == 'D'  :  adat[nFor2][2] := stod('')
                            case aSa1Stru[nLin][2] == 'N'  :  adat[nFor2][2] := 0
                            case aSa1Stru[nLin][2] == 'C'  :  adat[nFor2][2] := padr(" ", TAMSX3(adat[nFor2][1])[1])
                            case aSa1Stru[nLin][2] == 'L'  :  adat[nFor2][2] := .F.
                            case aSa1Stru[nLin][2] == 'M'  :  adat[nFor2][2] := " "
                        endcase
                    else
                        do case
                            case aSa1Stru[nLin][2] == 'D'  :  adat[nFor2][2] := iif(empty(stod(adat[nFor2][2])), ctod(adat[nFor2][2]), stod(adat[nFor2][2]))
                            case aSa1Stru[nLin][2] == 'N'  :  adat[nFor2][2] := VAL(adat[nFor2][2])
                            case aSa1Stru[nLin][2] == 'C'  :  adat[nFor2][2] := cValtochar(adat[nFor2][2])
                            case aSa1Stru[nLin][2] == 'L'  :  adat[nFor2][2] := iif(upper(adat[nFor2][2]) == '.F.', .f., .t.)
                            case aSa1Stru[nLin][2] == 'M'  :  adat[nFor2][2] := cValtochar(adat[nFor2][2])
                        endcase
                    endif
                ELSE
                    IF valtype(adat[nFor2][2]) == 'C'
                        adat[nFor2][2] := PADR(adat[nFor2][2], TAMSX3(adat[nFor2][1])[1])
                    ENDIF
                endif
            endif
        endif
    Next nfor2

    FOR nFor2 := len(aDeletar) to 1 step -1
        adel(aDat, aDeletar[nFor2])
    next nFor2
    aDat := asize(aDat, len(aDat) - len(aDeletar))
    DBSELECTAREA("SA1")
```

#### Gravação dos Dados via EXECAUTO

```advpl
    BeginTran()

    // Gravação de dados do Cliente
    MSEXECAUTO({|X, Y| MATA030(X, Y)}, adat, NOPC)

    IF lMsErroauto
        // Disarma a transação (rollback)
        nPx := 0
        DisarmTransaction()
        aAutoErro := GETAUTOGRLOG()
        cMsg := ""
        IF LEN(aAutoErro) >= 2
            cCpox := '- ' + alltrim(substr(aAutoErro[1], at('_', aAutoErro[1]) - 2, 10))
            nPx   := aScan(aAutoErro, {|W| cCpox $ W})
            if nPx <= 0
                nPx := aScan(aAutoErro, {|W| '< -- ' $ W})
            endif
        ENDIF
        nTotV := iif(len(aAutoErro) > 20, 20, len(aAutoErro))
        For nFor1 := 1 to nTotV
            if !empty(alltrim(STRTRAN(STRTRAN(aAutoErro[nFor1], "'", '"'), '---', '')))
                cMsg += U_TIRACENTO(alltrim(STRTRAN(STRTRAN(aAutoErro[nFor1], "'", '"'), '---', ''))) + CRLF
            endif
        Next nfor1
        if nPx > 0
            cMsg += U_TIRACENTO(alltrim(STRTRAN(STRTRAN(aAutoErro[nPx], "'", '"'), '---', ''))) + CRLF
        endif
        ::CREGSA1 := "ERRO AO GRAVAR O CLIENTE:" + CRLF + cMsg
    ELSE
        EndTran()
        ::CREGSA1 := "SUCESSO CODIGO DO CLIENTE:" + cCodigo
    ENDIF

RETURN .T.
```

**Opções do NOPC:**

| Valor | Operação |
|---|---|
| 3 | Inclusão |
| 4 | Alteração |
| 5 | Exclusão |

No ato da execução, o sistema apresenta a informação no console o XML gerado para o WebService.

> **Exercício:** Crie um WebService buscando os dados da tabela de clientes com a parametrização de quantos registros devem ser apresentados.

---

## 13. Apêndices

> **Exercício (Apêndice):** Crie um client buscando do endereço do WebService da TOTVS e alimente a sua base de dados com os dados desse client distribuído pela TOTVS na tabela SA1.

---

### 13.1 Guia de Referência Rápida – Funções e Erros

Neste guia de referência rápida, serão descritas as funções básicas da linguagem e seus respectivos ERROS do ADVPL/WebService.

---

### GetWSCError – Recuperação de Informações

Utilizada no desenvolvimento de uma aplicação 'Client' de WebServices, através desta função é possível recuperar as informações pertinentes à uma ocorrência de erro de processamento de um método 'Client', após a execução do mesmo. Caso a execução de um método 'Client' de Web Services retorne `.F.`, deve ser utilizada a função `GetWSCError()` para identificar a origem da ocorrência.

Durante a execução de um método 'Client' de WebServices, são possíveis ocorrências de erro das seguintes naturezas:

1. **Antes do pacote 'SOAP' ser enviado:** verificação de consistência dos parâmetros (obrigatoriedade, tipo AdvPL)
2. **Ao postar o pacote 'SOAP':** host do Web Service não localizado ou servidor fora do ar
3. **Após o envio e antes da obtenção do retorno:** pacote devolvido não está em conformidade com a declaração do serviço
4. **Erro Interno de execução:** qualquer ocorrência de erro fatal não tratada ou prevista

**Sintaxe:**
```
GETWSCERROR([nInfo]) --> xErrorInfo
```

**Parâmetros:**

| Nome | Tipo | Descrição | Default | Obrigatório |
|---|---|---|---|---|
| nInfo | Numérico | Especifica qual informação pertinente ao erro deve ser retornada | 1 | Não |

**Valores de nInfo:**

| Valor | Retorno |
|---|---|
| 1 | String contendo o Resumo do Erro COMPLETO (DEFAULT) |
| 2 | String contendo o `soap:fault_code`, caso disponível |
| 3 | String contendo o `soap:fault_String`, caso disponível |
| 4 | Objeto XML contendo os nodes completos com as informações do erro (apenas em caso de soap_Fault) |

---

### Códigos de Erro

#### WSCERR000 – WSDL não suportado. Existe mais de um serviço declarado

Por definição, um WSDL deve conter apenas um serviço declarado, com um ou mais métodos. Caso seja identificado mais de um serviço no mesmo WSDL, no momento da geração do código-fonte, o processo é abortado e o WSDL é considerado inválido.

#### WSCERR001 – Não há SOAP:BINDINGS para a geração do Serviço

Ocorre durante a geração do código-fonte para 'client' AdvPL a partir de uma definição de serviço (WSDL). Uma vez identificado o serviço, o gerador de código procura a declaração dos BINDINGS no WSDL. Caso esta declaração não esteja presente, a rotina considera o WSDL incompleto e aborta o processo de geração de código.

#### WSCERR003 – [XXX / YYY] Enumeration não suportado

Ocorre no processo de geração quando encontrada uma estrutura básica (SimpleType) com um 'enumeration'. São suportados os seguintes tipos básicos: `STRING`, `FLOAT`, `DOUBLE`, `DECIMAL`, `INT`, `INTEGER`, `LONG`, `UNSIGNEDINT`, `UNSIGNEDLONG`. Caso o tipo utilizado não esteja nesta lista, o processo de geração é abortado.

#### WSCERR004 – NÃO IMPLEMENTADO (001\<X\> / \<N\> / WSDLTYPE_NAME)

Ocorre quando uma estrutura contém um determinado elemento que aponta para uma outra estrutura e esta não é encontrada no WSDL (ocorrência `<X>` = A), ou é encontrada mas não registrada como uma estrutura (complextype) (ocorrência `<X>` = B).

#### WSCERR006 – WSDL inválido ou não suportado

Ocorre quando um parâmetro de primeiro nível (message) do WSDL for especificado sem nome.

#### WSCERR007 – WSDL inválido ou não suportado

Ocorre quando um parâmetro de primeiro nível (message) do WSDL for especificado sem definição de tipo.

#### WSCERR008 – Retorno NULLPARAM inválido

Ocorre quando um parâmetro de retorno do WSDL seja identificado como 'retorno nulo'. O WSDL é considerado inválido e o processo de geração é abortado.

#### WSCERR009 – INTERNAL ERROR (X)

Esta é uma ocorrência de erro interna do 'engine' de geração de código-fonte AdvPL, não reproduzida até o momento. Caso, após a análise inicial de parâmetros, algum parâmetro não seja enquadrado como entrada, saída ou entrada/saída, o processamento de geração é abortado.

#### WSCERR010 – [STRUCT_TYPE] Estrutura / Tipo incompleto

Ocorre quando uma estrutura complexa não contém a especificação de seus elementos internos e a mesma não contém nenhuma referência ao SCHEMA ou à outra estrutura.

#### WSCERR011 – Retorno NULLPARAM inválido

Semelhante à ocorrência WSCERR008, porém esta ocorrência (011) refere-se à uma **sub-estrutura** do serviço, e a primeira (008) refere-se à um parâmetro/estrutura de primeiro nível do serviço.

#### WSCERR012 – INTERNAL ERROR (X)

Semelhante à WSCERR009, porém indica uma falha em outro ponto da rotina interna de análise.

#### WSCERR013 – [SOAP_TYPE] UNEXPECTED TYPE

Ocorre quando um parâmetro de tipo básico não se encontrar entre os tipos básicos suportados pelo 'engine' Client de WebServices do ERP. Em `SOAP_TYPE` é indicado o tipo não suportado.

#### WSCERR014 – INVALID NULLPARAM INIT

Ocorre quando a rotina de geração de código-fonte recebe a instrução de inicializar a propriedade reservada 'NULLPARAM'. Pode ser causada por uma falha na validação inicial do WSDL.

#### WSCERR015 – Node [XXX] as [YYY] on SOAP Response not found

Ocorre no momento que o client está desmontando o pacote SOAP retornado pelo serviço. Caso o serviço utilize um soap-style RPC, e o node `[XXX]` correspondente ao retorno esperado do tipo `[YYY]` não for encontrado no pacote, o processamento é abortado. O método 'Client' chamado retornará `.F.` e a descrição deve ser recuperada através de `GetWSCError()`.

#### WSCERR016 – Requisição HTTPS não suportada neste Build. [XXX]

Ocorre quando informada uma URL para buscar a definição do serviço (WSDL) utilizando o protocolo HTTPS, mas a build do ERP atual não suportar o tratamento de Web Services em HTTPS.

#### WSCERR017 – HTTP[S] Requisição retornou [NIL]

Ocorre quando informada uma URL para buscar a definição do serviço (WSDL), utilizando o protocolo HTTP ou HTTPS, e não foi possível buscar o link solicitado.

#### WSCERR018 – HTTP[S] Requisição retornou [EMPTY]

Diferentemente da WSCERR017, esta ocorrência foi reproduzida quando o servidor foi localizado, a requisição foi feita com sucesso, porém o servidor recebeu como retorno um pacote HTTP incompleto ou inválido.

**Diagnóstico:** Verifique a URL digitada e realize a requisição através de um Web Browser.

#### WSCERR019 – (XXX) Arquivo não encontrado

Ocorre quando informado um local para buscar a definição do serviço (WSDL) no disco e o arquivo não for encontrado. Possíveis causas: diretório/arquivo não existente ou inválido, falta de permissão de acesso.

#### WSCERR020 – (XXX / FERROR YYY) Falha de Abertura

Ocorre quando há impossibilidade de acesso ao arquivo. Possíveis causas: arquivo aberto em modo exclusivo por outra estação ou falha de permissão de abertura.

#### WSCERR021 – [INFO] WSDL Parsing [PARSER_WARNING]

Ocorre quando o parser interno de xml do sistema identifica uma inconsistência considerada como uma advertência (warning) no documento XML.

#### WSCERR022 – [INFO] WSDL Parsing [PARSER_ERROR]

Ocorre quando o parser interno identifica um erro de sintaxe no documento WSDL.

#### WSCERR023 – [xxx] FALHA INESPERADA AO IMPORTAR WSDL

Ocorre quando o documento retornado constitui um XML sintaticamente válido, mas o parser não identifica nenhuma estrutura referente a um documento WSDL.

#### WSCERR024 – [MSG_INFO] MESSAGE não encontrada

Ocorre quando uma seção de mensagens (message) é especificada para uma operação, porém não é encontrada no WSDL.

#### WSCERR025 – [BIND_INFO] Binding não Encontrado

Ocorre quando uma seção de amarração (binding) não é localizada para uma operação especificada no WSDL.

#### WSCERR026 – TARGETNAMESPACE não definido no WSDL

Ocorre quando o documento WSDL não contém a definição do NameSpace de destino (TargetNameSpace).

#### WSCERR027 – [OPER_INFO] BIND:OPERATION não encontrado

Ocorre quando uma operação/método do WebService não é encontrada na seção de amarração (binding).

#### WSCERR028 – [PORT_INFO] PortType não Encontrado em aPort

Ocorre quando uma operação/método do WebService não é encontrada na seção de portas do WSDL (PortType).

#### WSCERR029 – [PORT_INFO] PortType não contém operações

Ocorre quando uma operação/método do WebService não contém a definição das operações na seção de portas do serviço (PortType).

#### WSCERR031 – [STRUCT_NAME] Tipo sem NAMESPACE

Ocorre quando uma determinada estrutura é identificada como sendo externa ao WSDL atual, referenciada por um IMPORT ou REF, ou se a estrutura estiver declarada no WSDL sem o referido namespace.

#### WSCERR032 – [SHORT_NS] NAMESPACE não encontrado

Ocorre quando o namespace de uma estrutura externa não está declarado no header do WSDL.

#### WSCERR033 – [LONG_NS] NameSpace sem Import declarado

Complementar ao erro WSCERR032. Reproduzido quando o namespace identificado para o parâmetro é externo ao WSDL, porém a URL para processamento não é especificada através de um Import.

#### WSCERR034 – [INFO_NS] NAMESPACE sem LOCATION informado

Complementar ao erro WSCERR033. Ocorre quando a declaração da URL/Location do NameSpace externo não está declarada no `<IMPORT...>` do WSDL.

#### WSCERR035 – [TYPE] Tipo indefinido

Ocorre no reprocessamento quando o parâmetro/estrutura pendente não é encontrado após o namespace ser importado.

#### WSCERR036 – Definição não suportada

Ocorre quando uma estrutura complexa não possui tipo definido, não é uma referência externa ao WSDL, e também não é uma referência ao próprio SCHEMA.

#### WSCERR037 – [TYPE] Estrutura Interna Inesperada

Ocorre quando uma estrutura passou por todas as interpretações cabíveis e mesmo assim não foi possível identificá-la.

#### WSCERR038 – [PARAM] WSDL inválido ou não suportado

Ocorre quando um parâmetro/retorno passou por todas as interpretações cabíveis de uma estrutura, porém não foi possível localizar ou identificar adequadamente a estrutura. Em termos práticos: ou o WSDL fornecido não é válido, ou a engine de parser WSDL do Protheus não reconheceu a estrutura como válida.

#### WSCERR039 – Unexpected DumpType [X]

Ocorre na utilização da função `XMLDataSet` quando não for passado um objeto AdvPL de tipo válido (Objeto XML ou Array). O processamento é abortado identificando o tipo de parâmetro recebido em [X].

#### WSCERR040 – Unexpected SCHEMA Type [X]

Ocorre na utilização da função `XMLDataSchema` quando não for enviado um Objeto AdvPL de Tipo Válido (Objeto XML ou Array).

#### WSCERR041 – [NOTNIL_MESSAGE]

Ocorre durante a desmontagem do pacote de retorno de um Web Service quando algum parâmetro obrigatório não está presente no pacote de retorno. Identificado em `[NOTNIL_MESSAGE]` o parâmetro/propriedade que não veio preenchida.

#### WSCERR042 – URL LOCATION não especificada

Ocorre quando a propriedade reservada `_URL` do objeto do Serviço está vazia no momento de postar o pacote SOAP.

**Diagnóstico:** Verifique o código-fonte e certifique-se que a propriedade `_URL` não esteja vazia.

#### WSCERR043 – [SOAP_STYLE] SOAPSTYLE Desconhecido

Ocorre quando o formato do pacote SOAP a ser enviado não está num formato válido. Esta propriedade é definida em fonte no momento da geração do fonte-client e não deve ser alterada.

#### WSCERR044 – Não foi possível POST: URL [URL_POST]

Ocorre quando o servidor de destino do pacote não é localizado no DNS ou não está no ar.

#### WSCERR045 – Retorno VAZIO de POST: URL \<URL\> [HEADER_RET]

Ocorre quando o servidor de WebServices foi localizado, a requisição foi feita com sucesso, porém o servidor recebeu como retorno um pacote HTTP incompleto ou inválido, ou ocorreu um erro interno no servidor.

#### WSCERR046 – XML Warning [XML_WARNING] (POST em \<URL\>)

Ocorre quando o parser interno de xml do sistema detecta uma inconsistência considerada como uma advertência (warning) no pacote SOAP retornado pelo serviço.

#### WSCERR047 – XML Error [XML_ERROR] (POST em \<URL\>)

Ocorre quando o parser interno de xml detecta um erro de sintaxe no XML do pacote SOAP retornado. Veja mais detalhes na função `GetWSCError()`.

#### WSCERR048 – SOAP FAULT [FAULT_CODE] (POST em \<URL\>): [FAULT_STRING]

Ocorre quando o pacote de retorno contém uma exceção do tipo SOAP FAULT, indicando que houve uma falha de processamento do serviço no servidor.

#### WSCERR049 – SOAP RESPONSE (RPC) NOT FOUND

Ocorre quando o serviço utiliza um soapStyle = RPC, e o node de resposta não é encontrado no pacote.

#### WSCERR050 – SOAP RESPONSE REF \<NODE_REF\> (RPC) NOT FOUND

Ocorre quando o node de resposta aponta para outro node via referência, e este novo node não é encontrado no pacote.

#### WSCERR051 – SOAP RESPONSE RETURN (RPC) NOT FOUND

Ocorre quando o node de retorno não aponta para nenhuma referência e não é encontrado no nível do node de resposta.

#### WSCERR052 – Enumeration FAILED on [STRUCT_TYPE]

Ocorre quando um parâmetro com definição de "enumeration" é alimentado com um valor que não consta na lista de parâmetros válidos.

**Diagnóstico:** Verifique o código-fonte client gerado em AdvPL para obter a lista de parâmetros válidos.

#### WSCERR053 – WSRPCGetNode (Object) not found

Ocorre quando o serviço utiliza um soapStyle = RPC e o node correspondente a uma estrutura complexa não é localizado no pacote de retorno.

#### WSCERR054 – Binding SOAP não localizado no WSDL

Ocorre durante a geração do código-fonte quando não existe nenhuma amarração no serviço que especifique a utilização do SOAP. A infraestrutura Client de WebServices do sistema não suporta a geração de fontes-client de serviços que não utilizem pacotes XML-SOAP para a troca de informações.

#### WSCERR055 – Invalid Property Type (X) for [PARAM] (Y)

Ocorre quando uma determinada propriedade [PARAM] do objeto 'Client' do serviço está alimentada com um tipo de dado AdvPL [X], porém o tipo esperado era [Y].

#### WSCERR056 – Invalid XML-Soap Server Response: soap-envelope not found

Ocorre quando o pacote SOAP retornado pelo serviço não contém um envelope (soap-Envelope) de resposta.

#### WSCERR057 – Invalid XML-Soap Server Response: soap-envelope empty

Ocorre quando não é possível determinar o prefixo do SOAP Envelope utilizado no pacote retornado.

#### WSCERR058 – Invalid XML-Soap Server Response: Invalid soap-envelope [SOAP_ENV] object as valtype [X]

Ocorre quando o soap-envelope determinado [SOAP_ENV], esperado como um Objeto, foi recebido com um tipo AdvPL [X].

#### WSCERR059 – Invalid XML-Soap Server Response: soap-body not found

Ocorre quando não é possível determinar o corpo (soap-body) do pacote SOAP retornado pelo serviço.

#### WSCERR060 – Invalid XML-Soap Server Response: soap-body envelope empty

Ocorre quando não é possível determinar o prefixo do corpo (soap-body) no pacote SOAP retornado.

#### WSCERR061 – Invalid XML-Soap Server Response: Invalid soap-body [BODY] object as valtype [TYPE]

Ocorre quando o corpo (soap-body) determinado [BODY], esperado como um Objeto, foi recebido como um tipo AdvPL [TYPE].

#### WSCERR062 – Invalid XML-Soap Server Response: Unable to determine Soap Prefix of Envelope [SOAP_ENV]

Ocorre quando o envelope (soap-envelope) determinado [SOAP_ENV] não está em um formato que permita determinar o nome do envelope.

#### WSCERR063 – Argument error: Missing field [NODE] as [TYPE]

Ocorre quando o parâmetro obrigatório determinado em [NODE], com o tipo [TYPE], não foi alimentado para a chamada da função 'client'.

#### WSCERR064 – Invalid Content-Type return (HTTP_HEAD) from \<URL\>

Ocorre quando o header HTTP de retorno do serviço indica o uso de content-type diferente de XML. Um Web Service 'client' sempre espera por um pacote de retorno com `Content-type: text/xml`.

**Causa comum:** Um WebService não está mais publicado no endereço especificado e o servidor devolve uma página HTML com uma mensagem 'Page not Found'.

#### WSCERR065 – EMPTY Content-Type return (HEADER) from \<URL\>

Ocorre quando o header HTTP retornado pelo servidor não possui a identificação do Content-Type.

#### WSCERR066 – Invalid INVALID WSDL Content-Type (HTTP_HEAD) from \<URL\>

Ocorre quando o header HTTP de retorno da requisição do WSDL vem identificando um tipo de documento (content-type) diferente de `text/plain` ou `text/xml`.

**Alternativa:** Caso o WSDL possa ser aberto através de um navegador de internet, proceda da seguinte forma:
1. Abra a URL do WSDL no navegador de internet
2. Salve o documento em um diretório do RootPath do TOTVS | Application Server
3. Gere o client novamente a partir do TOTVS | Development Studio, colocando no campo "URL do WebService" o caminho em que o arquivo se encontra no RootPath. Exemplo: `\arquivo.wsdl`

#### WSCERR067 – EMPTY WSDL Content-Type (HTTP_HEAD) from \<URL\>

Ocorre quando o header HTTP de retorno do WSDL vem sem a informação do tipo de conteúdo do documento (content-type). Um documento WSDL deve ser retornado informando no header HTTP o content-type como `text/plain` ou `text/xml`.

#### WSCERR068 – NOT XML SOURCE from \<URL\>

Ocorre quando o documento retornado pelo servidor de Web Services não se trata de um XML válido. O documento WSDL deve sempre iniciar com o node da declaração do XML (`<?XML ...>`) ou com a definição do serviço (`<DEFINITIONS`).

#### WSCERR069 – BYREF [PARAM] WITH NO INPUT ARGUMENT: UNSUPPORTED WEBSERVICE

Ocorre na geração do código-fonte quando o WSDL retornado informa um método com mais de um parâmetro de retorno (parâmetros por referência - BYREF). Após o cruzamento dos retornos do método com os parâmetros, deve restar no máximo um retorno.

#### WSCERR070 – Requisição HTTPS não suportada neste BUILD [PROTHEUS_BUILD]

Ocorre quando o protocolo HTTPS é utilizado e a build atual do servidor TOTVS | Application Server não suporta HTTPS para Web Services.

**Diagnóstico:** Caso o serviço solicitado exija HTTPS, a build do servidor TOTVS | Application Server deve ser atualizada.

#### WSCERR071 – INVALID HTTP HEADER (HTTPHEAD) from \<URL\>

Ocorre quando o servidor retorna um pacote HTTP com um header de retorno que não é identificado como HTTP.

#### WSCERR072 – HTTP REQUEST ERROR (HEADER) from \<URL\>

Ocorre quando o servidor retorna um pacote HTTP com um status diferente de 200 (OK). Causas prováveis: `403 Forbidden` (proxy que requer autenticação), `500 Internal Server Error`.

#### WSCERR073 – Build (BUILD) XML Internal Error

Ocorre quando o pacote SOAP retornado contém um erro estrutural ou sintático que não é detectado pelo parser interno como um erro ou advertência, impedindo a geração do objeto intermediário necessário para o processamento. Esta ocorrência foi reproduzida em builds do TOTVS | Application Server anteriores a Dezembro/2003 e desde então não mais foi reproduzida.

---

### Regras de Nomenclatura

#### Nomenclatura dos Serviços

```
<Nome_do_servico>
```

- Deve ser iniciado por um caractere alfabético
- Deve conter apenas caracteres alfabéticos `A...Z`, caracteres numéricos `0...9`, e o caractere `_` (underline)
- Um serviço não pode ter um nome de uma palavra reservada AdvPL
- Não pode ter o nome igual a um tipo básico de campo (`STRING`, `INTEGER`, `FLOAT`, `DATE`, `BOOLEAN`)

#### Nomenclatura de Estruturas

```advpl
WSSTRUCT <Nome_da_Estrutura>
```

`<Nome_da_Estrutura>` obedece às mesmas regras de nomenclatura de Serviços, não podendo haver uma estrutura com o mesmo nome de um serviço declarado.

Uma estrutura é um agrupamento de dados básicos, criado como uma classe especial (WSSTRUCT) em AdvPL. Procedemos com a criação de uma estrutura para um serviço quando temos a necessidade de definir que um conjunto de dados básicos pode ser agrupado em um tipo de informação.

#### Nomenclatura de Dados (Campos)

```advpl
WSDATA <Nome_Campo> as [ARRAY OF] <Tipo_campo> [OPTIONAL]
```

| Elemento | Descrição |
|---|---|
| `<Nome_Campo>` | Obedece às mesmas regras de nomenclatura de Serviços, não podendo haver um dado com o mesmo nome de um serviço ou estrutura já declarados |
| `[ARRAY OF]` | Caso especificado, indica que este dado poderá ter mais de uma ocorrência, sendo tratado como um Array em AdvPL |
| `<Tipo_Campo>` | Pode ser um tipo básico de dado (String, Date, Integer, Float, Boolean) ou pode ser uma estrutura declarada |
| `[OPTIONAL]` | Caso especificado, indica que a especificação deste dado nos pacotes de envio e/ou retorno é opcional |

> **Restrição:** Não é permitido o uso da instrução `ARRAY OF` quando declaramos dados utilizados para entrada de dados dentro da declaração do serviço. Para tal, é necessário criar uma estrutura intermediária para "encapsular" o array.

#### Tipos de Dados Básicos

| Tipo | Descrição |
|---|---|
| `String` | Dado AdvPL do tipo String |
| `Date` | Dado AdvPL do tipo Data |
| `Integer` | Dado AdvPL do tipo numérico, apenas números inteiros |
| `Float` | Dado AdvPL do tipo numérico, pode conter números inteiros e não-inteiros |
| `Boolean` | Dado AdvPL do tipo Booleano (lógico) |
| `Base64Binary` | Dado AdvPL do tipo String Binária, aceitando todos os caracteres da Tabela ASCII, de `CHR(0)` a `CHR(255)` |

> **Campos Obrigatórios / Opcionais:** Por default, um campo declarado sem a cláusula `OPTIONAL` é obrigatório. Sendo obrigatório, o node ou tag SOAP referente ao mesmo deverá ser especificado no pacote XML-SOAP. No processamento de um serviço, os dados enviados pelo client são lidos do pacote SOAP e atribuídos às propriedades do método; caso um dado não seja passado ao serviço, é atribuído ao mesmo o conteúdo `NIL`.

#### Nomenclatura de Métodos (Ações)

```advpl
WSMETHOD <Metodo> WSRECEIVE <Cpo_In>[, Cpo_In2,...] WSSEND <Cpo_Out>
```

| Elemento | Descrição |
|---|---|
| `<Metodo>` | Obedece às mesmas regras de nomenclatura de Serviços, não podendo haver um serviço ou estrutura declarados com o mesmo nome |
| `WSRECEIVE` | Obrigatoriamente deve especificar um ou mais campos declarados dentro do serviço para a entrada de dados |
| `WSSEND` | Apenas um campo para saída de dados do método |

Dentro do método, fazemos referências às propriedades da estrutura segundo a nomenclatura de acesso à propriedades de objetos AdvPL (prefixo `::`).

> Caso se deseje declarar um serviço que não requer nenhum parâmetro, deve-se especificar que o mesmo recebe o parâmetro reservado `NULLPARAM`.
