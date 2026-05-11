# Queries SQL no Protheus -- Guia Completo

> Referencia tecnica abrangente sobre todas as formas de executar SQL dentro do ADVPL/TLPP no ERP Protheus da TOTVS.

---

## Sumario

- [1. Visao Geral -- SQL no Protheus](#1-visao-geral----sql-no-protheus)
  - [1.1 Quando usar query vs acesso ISAM](#11-quando-usar-query-vs-acesso-isam)
  - [1.2 TopConnect/DBAccess -- a camada SQL](#12-topconnectdbaccess----a-camada-sql)
  - [1.3 Performance: query vs loop ISAM](#13-performance-query-vs-loop-isam)
- [2. Embedded SQL (BeginSQL/EndSQL)](#2-embedded-sql-beginsqlendsql)
  - [2.1 Sintaxe completa](#21-sintaxe-completa)
  - [2.2 Tokens disponiveis](#22-tokens-disponiveis)
  - [2.3 Conversao de tipos com COLUMN AS](#23-conversao-de-tipos-com-column-as)
  - [2.4 ORDER BY, GROUP BY, HAVING e Subqueries](#24-order-by-group-by-having-e-subqueries)
  - [2.5 Limitacoes do Embedded SQL](#25-limitacoes-do-embedded-sql)
  - [2.6 Compatibilidade ISAM/SQL com #IFDEF TOP](#26-compatibilidade-isamsql-com-ifdef-top)
- [3. DbUseArea + TcGenQry (Forma Classica)](#3-dbusearea--tcgenqry-forma-classica)
  - [3.1 Sintaxe completa](#31-sintaxe-completa)
  - [3.2 GetNextAlias()](#32-getnextalias)
  - [3.3 RetSQLName()](#33-retsqlname)
  - [3.4 xFilial()](#34-xfilial)
  - [3.5 D_E_L_E_T_ -- filtro de deletados](#35-d_e_l_e_t_----filtro-de-deletados)
  - [3.6 ChangeQuery()](#36-changequery)
  - [3.7 TCSetField() -- conversao de tipos](#37-tcsetfield----conversao-de-tipos)
  - [3.8 Fechar alias: DbCloseArea()](#38-fechar-alias-dbclosearea)
  - [3.9 TCGenQry2 -- queries parametrizadas](#39-tcgenqry2----queries-parametrizadas)
- [4. TCSqlExec -- Execucao sem Retorno](#4-tcsqlexec----execucao-sem-retorno)
  - [4.1 Sintaxe e retorno](#41-sintaxe-e-retorno)
  - [4.2 Quando usar vs RecLock](#42-quando-usar-vs-reclock)
  - [4.3 Controle de transacao](#43-controle-de-transacao)
  - [4.4 Perigos: bypass de triggers e logs](#44-perigos-bypass-de-triggers-e-logs)
- [5. FWExecStatement (Forma Moderna e Segura)](#5-fwexecstatement-forma-moderna-e-segura)
  - [5.1 Sintaxe completa](#51-sintaxe-completa)
  - [5.2 Metodos disponiveis](#52-metodos-disponiveis)
  - [5.3 Bind de parametros e SQL Injection](#53-bind-de-parametros-e-sql-injection)
  - [5.4 Quando preferir sobre TcGenQry](#54-quando-preferir-sobre-tcgenqry)
- [6. FWPreparedStatement](#6-fwpreparedstatement)
  - [6.1 Sintaxe e uso](#61-sintaxe-e-uso)
  - [6.2 Metodos de bind](#62-metodos-de-bind)
  - [6.3 Diferenca para FWExecStatement](#63-diferenca-para-fwexecstatement)
- [7. MpSysOpenQuery](#7-mpsysopenquery)
  - [7.1 Quando usar](#71-quando-usar)
  - [7.2 Sintaxe](#72-sintaxe)
- [8. Montagem Segura de Queries](#8-montagem-segura-de-queries)
  - [8.1 SQL Injection no Protheus](#81-sql-injection-no-protheus)
  - [8.2 Concatenacao vs parametrizacao](#82-concatenacao-vs-parametrizacao)
  - [8.3 Uso correto de aspas simples](#83-uso-correto-de-aspas-simples)
  - [8.4 Validar inputs do usuario](#84-validar-inputs-do-usuario)
- [9. Performance e Boas Praticas](#9-performance-e-boas-praticas)
  - [9.1 Indices: SIX e FORCE INDEX](#91-indices-six-e-force-index)
  - [9.2 TOP / LIMIT -- paginacao](#92-top--limit----paginacao)
  - [9.3 NOLOCK -- quando usar](#93-nolock----quando-usar)
  - [9.4 Evitar SELECT *](#94-evitar-select-)
  - [9.5 Evitar funcoes no WHERE](#95-evitar-funcoes-no-where)
  - [9.6 Funcoes de agregacao no SQL](#96-funcoes-de-agregacao-no-sql)
  - [9.7 JOINs -- LEFT JOIN e INNER JOIN](#97-joins----left-join-e-inner-join)
  - [9.8 Subqueries vs JOINs](#98-subqueries-vs-joins)
  - [9.9 %NOPARSER% -- quando usar](#99-noparser----quando-usar)
  - [9.10 Temporary tables com queries](#910-temporary-tables-com-queries)
- [10. Padroes Comuns](#10-padroes-comuns)
  - [10.1 Query com parametros do SX1 (Pergunte)](#101-query-com-parametros-do-sx1-pergunte)
  - [10.2 Query com progressbar (Processa/ProcRegua)](#102-query-com-progressbar-processaprocregua)
  - [10.3 Query retornando dados para array](#103-query-retornando-dados-para-array)
  - [10.4 Query para relatorio TReport](#104-query-para-relatorio-treport)
  - [10.5 Query de RECNO para posicionamento](#105-query-de-recno-para-posicionamento)
- [11. Armadilhas](#11-armadilhas)
  - [11.1 Tabela de armadilhas comuns](#111-tabela-de-armadilhas-comuns)
  - [11.2 Detalhamento das armadilhas](#112-detalhamento-das-armadilhas)

---

## 1. Visao Geral -- SQL no Protheus

### 1.1 Quando usar query vs acesso ISAM

O Protheus historicamente utilizava o modelo ISAM (Indexed Sequential Access Method) para acessar dados atraves de funcoes como `DbSeek()`, `DbSkip()`, `DbSetOrder()` e filtros com `DbSetFilter()`. Com a migracao para bancos de dados relacionais (SQL Server, Oracle, PostgreSQL), o **DBAccess** (antigo TopConnect) passou a traduzir esses comandos ISAM em instrucoes SQL nos bastidores.

**Regra geral:**

| Cenario | Abordagem recomendada |
|---|---|
| Leitura de grandes volumes de dados | Query SQL |
| Relatorios, dashboards, consultas | Query SQL |
| Agregacoes (SUM, COUNT, MAX, AVG) | Query SQL |
| Leitura de poucos registros ja indexados | ISAM (DbSeek) pode ser aceitavel |
| Gravacao/alteracao de registros padrao | RecLock (ISAM) ou ExecAuto |
| Gravacao em tabelas customizadas (Zxx) | RecLock ou TCSqlExec |
| Rotinas que precisam de compatibilidade ISAM/SQL | `#IFDEF TOP` |

### 1.2 TopConnect/DBAccess -- a camada SQL

O **DBAccess** (anteriormente chamado TopConnect) e o middleware que conecta o Application Server do Protheus ao banco de dados relacional. Ele atua como tradutor entre dois mundos:

- **Comandos ISAM** (`DbSeek`, `DbSkip`, `DbSetOrder`, `RecLock`) -- o DBAccess traduz internamente para SELECTs, UPDATEs e INSERTs no banco SQL. Cada `DbSeek` gera um SELECT com WHERE e ORDER BY; cada `DbSkip` gera um FETCH no cursor.

- **Comandos SQL nativos** (`TcGenQry`, `TCSqlExec`, `BeginSQL`) -- sao enviados diretamente ao banco (com ou sem tratamento do `ChangeQuery`), sem a sobrecarga da traducao ISAM.

O DBAccess tambem gerencia:
- Campos de controle internos (`R_E_C_N_O_`, `D_E_L_E_T_`, `R_E_C_D_E_L_`, `INSDT`, `UPDDT`)
- Indices virtualizados (indices simulados que nao existem fisicamente no banco)
- Cache de metadados

### 1.3 Performance: query vs loop ISAM

A leitura de um result set obtido por query SQL e **significativamente mais rapida** do que a varredura ISAM equivalente:

| Abordagem | Performance | Observacao |
|---|---|---|
| Query SQL nativa | Mais rapida | Processamento no banco, retorno apenas dos dados necessarios |
| Query de RECNO + DbGoto | Intermediaria | Util quando precisa posicionar para alterar/excluir |
| MsSeek (cache em memoria) | ~4x mais rapido que DbSeek | Para posicionamentos repetidos |
| DbSeek/DbSkip (ISAM puro) | Mais lento | Cada operacao gera SELECTs no banco via DBAccess |

**Exemplo comparativo:**
Um loop ISAM que percorre 10.000 registros com `DbSeek` + `DbSkip` gera milhares de instrucoes SQL individuais no banco. A mesma operacao com uma unica query SQL retorna o result set completo em uma unica ida ao banco.

```advpl
// RUIM: Loop ISAM para somar valores (lento)
SB1->(DbSetOrder(1))
SB1->(DbSeek(xFilial("SB1")))
nTotal := 0
While SB1->(!EoF()) .And. SB1->B1_FILIAL == xFilial("SB1")
    nTotal += SB1->B1_CUSTO1
    SB1->(DbSkip())
EndDo

// BOM: Query SQL com SUM (rapido)
cQuery := "SELECT SUM(B1_CUSTO1) AS TOTAL FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
cQuery += " AND D_E_L_E_T_ = ' '"
```

---

## 2. Embedded SQL (BeginSQL/EndSQL)

O Embedded SQL e um facilitador sintatico que permite escrever queries diretamente no codigo ADVPL sem concatenacao de strings. O pre-compilador transforma o bloco em chamadas `DbUseArea` + `TcGenQry` + `TCSetField`.

**Requisito:** Build do Protheus igual ou superior a 7.00.050721P, em ambiente com RPODB=TOP.

### 2.1 Sintaxe completa

```advpl
BeginSql Alias cAlias
    COLUMN campo1 AS Date
    COLUMN campo2 AS Numeric(15,2)
    COLUMN campo3 AS Logical
    SELECT campo1, campo2, campo3
    FROM %Table:XXX% XXX
    WHERE XXX.campo_filial = %xFilial:XXX%
      AND %Exp:cVariavel%
      AND XXX.%NotDel%
    ORDER BY %Order:XXX%
EndSql
```

**Notas sobre o alias:**
- Pode ser uma variavel caractere (`cAlias`) ou uma string literal (`"QRYTMP"`)
- Se o alias ja estiver aberto, ocorre erro fatal: `"Query Argument Error: Alias [XXX] already in use"`
- Recomenda-se usar `GetNextAlias()` para evitar conflitos

### 2.2 Tokens disponiveis

| Token | Equivalente em ADVPL | Descricao |
|---|---|---|
| `%Table:XXX%` | `RetSqlName("XXX")` | Nome real da tabela no banco (ex: SB1010) |
| `%NotDel%` | `D_E_L_E_T_ = ' '` | Filtra registros nao deletados |
| `%xFilial:XXX%` | `xFilial("XXX")` | Retorna a filial corrente para a tabela, entre aspas |
| `%Exp:cVar%` | Valor da variavel `cVar` | Injeta o conteudo de uma expressao ADVPL na query |
| `%Order:XXX%` | `SqlOrder(RetSqlName("XXX"), IndexOrd())` | Ordena pela chave do indice corrente |
| `%NoParser%` | Nao aplica `ChangeQuery()` | Envia o SQL exatamente como escrito, sem conversao |

**Exemplo completo com todos os tokens:**

```advpl
Local cAlias := GetNextAlias()
Local cFiltro := "AND B1_TIPO = 'PA'"

BeginSql Alias cAlias
    COLUMN B1_CUSTO1 AS Numeric(15,2)
    COLUMN B1_DTCAD  AS Date
    SELECT B1_COD, B1_DESC, B1_TIPO, B1_CUSTO1, B1_DTCAD
    FROM %Table:SB1% SB1
    WHERE SB1.B1_FILIAL = %xFilial:SB1%
      %Exp:cFiltro%
      AND SB1.%NotDel%
    ORDER BY %Order:SB1%
EndSql

While (cAlias)->(!EoF())
    ConOut((cAlias)->B1_COD + " - " + (cAlias)->B1_DESC)
    (cAlias)->(DbSkip())
EndDo
(cAlias)->(DbCloseArea())
```

### 2.3 Conversao de tipos com COLUMN AS

Quando a query retorna campos que nao sao do tipo caractere, e necessario declarar o tipo com a diretiva `COLUMN`. Sem isso, todos os campos retornam como tipo "C" (caractere).

```advpl
BeginSql Alias cAlias
    COLUMN E2_EMISSAO AS Date
    COLUMN E2_VALOR   AS Numeric(15,2)
    COLUMN E2_FLAGPAG  AS Logical
    SELECT E2_PREFIXO, E2_NUM, E2_EMISSAO, E2_VALOR, E2_FLAGPAG
    FROM %Table:SE2% SE2
    WHERE SE2.E2_FILIAL = %xFilial:SE2%
      AND SE2.%NotDel%
EndSql
```

Internamente, o pre-compilador transforma cada `COLUMN ... AS ...` em uma chamada `TCSetField()` apos a abertura do alias.

| Tipo | Sintaxe COLUMN | TCSetField equivalente |
|---|---|---|
| Data | `COLUMN campo AS Date` | `TCSetField(cAlias, "campo", "D", 8, 0)` |
| Numerico | `COLUMN campo AS Numeric(tam,dec)` | `TCSetField(cAlias, "campo", "N", tam, dec)` |
| Logico | `COLUMN campo AS Logical` | `TCSetField(cAlias, "campo", "L", 1, 0)` |

### 2.4 ORDER BY, GROUP BY, HAVING e Subqueries

Todas as clausulas SQL padrao podem ser usadas dentro do bloco `BeginSQL`:

```advpl
BeginSql Alias cAlias
    COLUMN TOTAL AS Numeric(15,2)
    SELECT B1_TIPO, SUM(B1_CUSTO1) AS TOTAL
    FROM %Table:SB1% SB1
    WHERE SB1.B1_FILIAL = %xFilial:SB1%
      AND SB1.%NotDel%
    GROUP BY B1_TIPO
    HAVING SUM(B1_CUSTO1) > 0
    ORDER BY B1_TIPO
EndSql
```

**Subquery dentro do Embedded SQL:**

```advpl
BeginSql Alias cAlias
    SELECT C5_NUM, C5_CLIENTE, C5_EMISSAO
    FROM %Table:SC5% SC5
    WHERE SC5.C5_FILIAL = %xFilial:SC5%
      AND SC5.C5_CLIENTE IN (
          SELECT A1_COD FROM %Table:SA1% SA1
          WHERE SA1.A1_FILIAL = %xFilial:SA1%
            AND SA1.A1_TIPO = '1'
            AND SA1.%NotDel%
      )
      AND SC5.%NotDel%
EndSql
```

### 2.5 Limitacoes do Embedded SQL

1. **Nao aceita funcoes ADVPL dentro do bloco** -- toda logica deve ser resolvida antes e passada via `%Exp:variavel%`
2. **O asterisco `*` nao pode ser o primeiro caractere de uma linha** -- o pre-compilador interpreta como comentario
3. **Maximo de 99 sub-selects** -- ultrapassar causa erro fatal `"Parser Query Error: TOO MANY SUB-SELECTS"`
4. **Alias ja aberto causa erro fatal** -- sempre use `GetNextAlias()`
5. **Espacos/tabs antes de `EndSql`** -- podem causar `"Syntax Error"` na compilacao
6. **Nao suporta DML** -- apenas SELECT; para INSERT/UPDATE/DELETE use `TCSqlExec`

### 2.6 Compatibilidade ISAM/SQL com #IFDEF TOP

O padrao `#IFDEF TOP` permite que o mesmo fonte funcione tanto em ambientes SQL (DBAccess/TopConnect) quanto em ambientes ISAM (ADS, ctree, etc.). O pre-processador resolve em tempo de compilacao qual bloco sera usado.

**Exemplo real extraido do fonte DAMDFE.prw:**

```advpl
// Exemplo real: DAMDFE.prw -- Compatibilidade ISAM/SQL
#IFDEF TOP
    cWhere := '%'
    cWhere += " CC0_SERMDF = '" + MV_PAR01 + "' "
    cWhere += " AND CC0_NUMMDF >= '" + MV_PAR02 + "' AND CC0_NUMMDF <= '" + MV_PAR03 + "' "
    cWhere += " AND (CC0_STATUS = '3' OR SUBSTRING(CC0_CHVMDF, 35, 1) = '2' ) "
    cWhere += ' %'

    BeginSql Alias cAliasMDF
        SELECT CC0_FILIAL, CC0_DTEMIS, CC0_SERMDF, CC0_NUMMDF, CC0_PROTOC
        FROM %Table:CC0% CC0
        WHERE CC0.CC0_FILIAL = %xFilial:CC0% AND
        %Exp:cWhere% AND
        CC0.%notdel%
    EndSql
#ELSE
    // Fallback ISAM -- usado quando nao ha DBAccess
    cIndex := CriaTrab(NIL, .F.)
    IndRegua(cAliasMDF, cIndex, cChave, , cWhere)
#ENDIF
```

**Como funciona este padrao:**

| Elemento | Funcao |
|---|---|
| `#IFDEF TOP` | Verifica se o ambiente usa banco SQL (RPODB=TOP). Definido quando DBAccess esta configurado |
| `cWhere := '%'` e `cWhere += ' %'` | O `%` no inicio e fim e necessario para o `%Exp:cWhere%` funcionar corretamente -- delimita a expressao |
| `%Exp:cWhere%` | Injeta a string montada dinamicamente na query |
| `#ELSE` | Bloco alternativo para ambientes ISAM |
| `CriaTrab` / `IndRegua` | Cria indice temporario e filtra registros no modelo ISAM |
| `#ENDIF` | Fecha o bloco condicional |

**Boas praticas para `#IFDEF TOP`:**
- Sempre tenha o fallback ISAM se o fonte pode rodar em ambientes sem SQL
- No bloco SQL, use todos os tokens (`%Table%`, `%xFilial%`, `%NotDel%`)
- No bloco ISAM, use `DbSeek`, `DbSetFilter`, `IndRegua` conforme necessario
- Fontes modernos podem dispensar o `#ELSE` se o ambiente for exclusivamente SQL

---

## 3. DbUseArea + TcGenQry (Forma Classica)

Esta e a forma tradicional e mais amplamente utilizada de executar queries SELECT no Protheus. O resultado e aberto como uma area de trabalho (work area), permitindo navegacao com `DbSkip()` e `EoF()`.

### 3.1 Sintaxe completa

```advpl
DbUseArea(lNewArea, cDriver, cDataFile, cAlias, lShared, lReadOnly)
```

| Parametro | Tipo | Descricao |
|---|---|---|
| `lNewArea` | Logico | `.T.` para abrir em uma nova area de trabalho |
| `cDriver` | Caractere | `"TOPCONN"` para queries via DBAccess |
| `cDataFile` | Caractere | Retorno de `TcGenQry(,,cQuery)` |
| `cAlias` | Caractere | Nome do alias para o result set |
| `lShared` | Logico | `.F.` -- nao se aplica a queries |
| `lReadOnly` | Logico | `.T.` -- queries sao somente leitura |

**Padrao completo de execucao:**

```advpl
Local cAlias := GetNextAlias()
Local cQuery := ""

// 1. Montar a query
cQuery := "SELECT B1_COD, B1_DESC, B1_TIPO, B1_CUSTO1 "
cQuery += "FROM " + RetSQLName("SB1") + " SB1 "
cQuery += "WHERE SB1.B1_FILIAL = '" + xFilial("SB1") + "' "
cQuery += "AND SB1.B1_TIPO = 'PA' "
cQuery += "AND SB1.D_E_L_E_T_ = ' ' "
cQuery += "ORDER BY B1_COD "

// 2. Compatibilizar a query entre bancos
cQuery := ChangeQuery(cQuery)

// 3. Abrir a query como area de trabalho
DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)

// 4. Converter tipos (obrigatorio para nao-caractere)
TCSetField(cAlias, "B1_CUSTO1", "N", 15, 2)

// 5. Navegar nos resultados
While (cAlias)->(!EoF())
    ConOut((cAlias)->B1_COD + " - " + (cAlias)->B1_DESC)
    ConOut("Custo: " + cValToChar((cAlias)->B1_CUSTO1))
    (cAlias)->(DbSkip())
EndDo

// 6. SEMPRE fechar o alias
(cAlias)->(DbCloseArea())
```

**Funcao TcGenQry:**

```
TcGenQry(xPar1, xPar2, cQuery) -> cRet
```

Os dois primeiros parametros sao mantidos por compatibilidade e devem ser ignorados (passar `NIL` ou omitir). O terceiro parametro e a query SQL.

### 3.2 GetNextAlias()

Retorna o proximo alias disponivel no formato `"__T001"`, `"__T002"`, etc. **Sempre use esta funcao** ao abrir queries para evitar erro de alias duplicado.

```advpl
// ERRADO: alias fixo pode causar erro em recursividade
DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), "QRYTMP", .F., .T.)

// CERTO: alias dinamico
Local cAlias := GetNextAlias()
DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)
```

**Por que e necessario:** Se uma funcao que abre um alias fixo for chamada recursivamente (ou por trigger, ponto de entrada, etc.), a segunda chamada tentara abrir um alias que ja esta em uso, causando erro fatal.

### 3.3 RetSQLName()

Retorna o nome real da tabela no banco de dados. O nome varia conforme a empresa logada.

```advpl
RetSQLName("SB1")  // Retorna "SB1010" (empresa 01) ou "SB1020" (empresa 02)
RetSQLName("SA1")  // Retorna "SA1010"
RetSQLName("ZZ1")  // Retorna "ZZ1010" (tabelas customizadas)
```

**Importante:** Nunca use o nome fixo da tabela (como `"SB1010"`) na query. Sempre use `RetSQLName()` para garantir que a empresa correta seja considerada.

### 3.4 xFilial()

Retorna a filial corrente para a tabela, considerando se a tabela e compartilhada ou exclusiva por filial.

```advpl
xFilial("SB1")  // Retorna "01" (se filial 01) ou "" (se tabela compartilhada)
```

**Uso na query:**

```advpl
cQuery += "WHERE B1_FILIAL = '" + xFilial("SB1") + "' "
```

**Atencao:** Nunca compare `_FILIAL` de uma tabela com `_FILIAL` de outra diretamente. Use `xFilial()` para cada tabela separadamente, pois tabelas podem ter regras de compartilhamento diferentes.

### 3.5 D_E_L_E_T_ -- filtro de deletados

O Protheus utiliza exclusao logica: ao "deletar" um registro, o campo `D_E_L_E_T_` recebe `'*'`. Registros ativos tem `' '` (espaco).

```advpl
// CORRETO e mais rapido
cQuery += "AND D_E_L_E_T_ = ' ' "

// FUNCIONA, mas e mais lento (nao usa indice de forma otima)
cQuery += "AND D_E_L_E_T_ <> '*' "
```

**Por que `= ' '` e melhor:** O otimizador do banco consegue usar o indice de forma mais eficiente com comparacao de igualdade do que com `<>`.

### 3.6 ChangeQuery()

Padroniza a sintaxe SQL para funcionar em diferentes bancos de dados (SQL Server, Oracle, PostgreSQL). Converte funcoes especificas de banco para equivalentes ANSI.

```advpl
cQuery := ChangeQuery(cQuery)
```

**Conversoes realizadas (exemplos):**

| Funcao original | Convertida para | Banco |
|---|---|---|
| `ISNULL(campo, valor)` | `COALESCE(campo, valor)` | Oracle/PostgreSQL |
| `SUBSTRING(campo, ini, tam)` | `SUBSTR(campo, ini, tam)` | Oracle |
| Tipos de dados especificos | Equivalentes ANSI | Todos |

**Quando NAO usar:**
- Quando voce precisa de hints como `WITH (NOLOCK)` -- o `ChangeQuery` remove
- Quando voce usa funcoes especificas do banco propositalmente
- Nestes casos, use `%NOPARSER%` no Embedded SQL ou simplesmente nao chame `ChangeQuery()`

**Limitacao critica:** Se um nome de campo contiver palavras reservadas SQL (como `ZZZ_FROM`, `ZZZ_SELECT`, `ZZZ_WHERE`), o `ChangeQuery` pode parsear incorretamente a query. Nesse caso, use `FWPreparedStatement` para proteger campos e valores.

### 3.7 TCSetField() -- conversao de tipos

Quando uma query e aberta via `TcGenQry`, **todos os campos retornam como caractere** (tipo "C"), exceto campos Memo ("M"). E obrigatorio usar `TCSetField()` para converter campos de Data, Numerico e Logico.

```advpl
TCSetField(cAlias, cCampo, cTipo, nTamanho, nDecimais)
```

| Parametro | Tipo | Descricao |
|---|---|---|
| `cAlias` | Caractere | Alias da query aberta |
| `cCampo` | Caractere | Nome do campo a converter |
| `cTipo` | Caractere | "N" (Numerico), "D" (Data), "L" (Logico) |
| `nTamanho` | Numerico | Tamanho do campo |
| `nDecimais` | Numerico | Casas decimais (para numerico) |

**Exemplo:**

```advpl
TCSetField(cAlias, "E2_EMISSAO", "D", 8, 0)    // Data
TCSetField(cAlias, "E2_VALOR",   "N", 15, 2)    // Numerico
TCSetField(cAlias, "E2_BAIXA",   "L", 1, 0)     // Logico
```

**Conversao em lote usando dbStruct():**

Quando precisa converter muitos campos, pode-se usar a estrutura do dicionario:

```advpl
// Abre a query
DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)

// Converte todos os campos nao-caractere de uma vez
aStru := SB1->(DbStruct())
For nI := 1 To Len(aStru)
    If aStru[nI][2] $ "DNL"
        TCSetField(cAlias, aStru[nI][1], aStru[nI][2], aStru[nI][3], aStru[nI][4])
    EndIf
Next nI
```

**Quando e obrigatorio:**
- Campos de Data: sem TCSetField, retornam como `"20240315"` (string) em vez de `CToD("15/03/2024")`
- Campos Numericos: sem TCSetField, retornam com precisao fixa 15,8 como caractere
- Campos Logicos: sem TCSetField, retornam como `"1"` ou `"0"` (string) em vez de `.T.`/`.F.`

### 3.8 Fechar alias: DbCloseArea()

**E CRITICO fechar todo alias aberto por query.** Alias nao fechados causam:

- **Memory leak** -- cursores permanecem abertos consumindo memoria no servidor
- **Erro de alias duplicado** -- em chamadas subsequentes, o alias pode ja estar em uso
- **Esgotamento de conexoes** -- cada alias aberto consome uma conexao no DBAccess

```advpl
// SEMPRE fechar no final
(cAlias)->(DbCloseArea())
```

**Dica:** Use blocos `BEGIN SEQUENCE ... END SEQUENCE` ou `ErrorBlock` para garantir o fechamento mesmo em caso de erro:

```advpl
Local cAlias := GetNextAlias()
Local bErro  := ErrorBlock({|e| oErr := e, Break(e)})
Local oErr   := NIL

BEGIN SEQUENCE
    DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)

    While (cAlias)->(!EoF())
        // processamento
        (cAlias)->(DbSkip())
    EndDo
END SEQUENCE

ErrorBlock(bErro)

// Garante fechamento mesmo com erro
If Select(cAlias) > 0
    (cAlias)->(DbCloseArea())
EndIf

If oErr != NIL
    // tratar erro
EndIf
```

### 3.9 TCGenQry2 -- queries parametrizadas

Variante do `TcGenQry` que suporta placeholders `?` substituidos por um array de valores:

```advpl
Local aParams := {}
Local cQuery  := ""

cQuery := "SELECT BM_GRUPO, BM_DESC FROM " + RetSQLName("SBM")
cQuery += " WHERE BM_FILIAL = ? AND BM_GRUPO >= ? AND D_E_L_E_T_ = ' '"

aAdd(aParams, xFilial("SBM"))
aAdd(aParams, "0001")

DbUseArea(.T., "TOPCONN", TcGenQry2(,,cQuery, aParams), cAlias, .F., .T.)
```

**Vantagem:** Evita concatenacao de strings com valores do usuario, reduzindo risco de SQL injection no nivel do DBAccess.

---

## 4. TCSqlExec -- Execucao sem Retorno

A funcao `TCSqlExec` executa instrucoes SQL que nao retornam result set: INSERT, UPDATE, DELETE e DDL.

### 4.1 Sintaxe e retorno

```advpl
nRet := TCSqlExec(cStatement)
```

| Parametro | Tipo | Descricao |
|---|---|---|
| `cStatement` | Caractere | Instrucao SQL a executar |
| **Retorno** | Numerico | `0` = sucesso; valor negativo = erro |

Para obter a mensagem de erro:

```advpl
cErro := TCSqlError()
```

**Exemplo basico:**

```advpl
Local cQuery := ""
Local nRet   := 0

cQuery := "UPDATE " + RetSQLName("ZZ1") + " SET "
cQuery += "ZZ1_STATUS = 'F' "
cQuery += "WHERE ZZ1_FILIAL = '" + xFilial("ZZ1") + "' "
cQuery += "AND ZZ1_CODIGO = '000001' "
cQuery += "AND D_E_L_E_T_ = ' ' "

nRet := TCSqlExec(cQuery)

If nRet < 0
    MsgStop("Erro ao atualizar: " + TCSqlError(), "Erro SQL")
    Return .F.
EndIf
```

### 4.2 Quando usar vs RecLock

| Metodo | Quando usar |
|---|---|
| **ExecAuto** | Tabelas padrao do Protheus (1a opcao) |
| **RecLock** | Quando ExecAuto nao esta disponivel; tabelas padrao ou customizadas |
| **TCSqlExec** | Apenas tabelas customizadas (Zxx); atualizacoes em massa; tabelas externas |

**Regra de ouro:** Para tabelas padrao do Protheus (SA1, SC5, SD1, etc.), **nunca** use INSERT/DELETE via `TCSqlExec`. Use ExecAuto ou RecLock, que passam por validacoes, gatilhos e controles de integridade.

### 4.3 Controle de transacao

Para operacoes criticas, envolva o `TCSqlExec` em um controle de transacao:

```advpl
Begin Transaction

    cQuery := "UPDATE " + RetSQLName("ZZ1") + " SET "
    cQuery += "ZZ1_STATUS = 'P' "
    cQuery += "WHERE ZZ1_FILIAL = '" + xFilial("ZZ1") + "' "
    cQuery += "AND ZZ1_LOTE = '" + cLote + "' "
    cQuery += "AND D_E_L_E_T_ = ' ' "

    nRet := TCSqlExec(cQuery)

    If nRet < 0
        MsgStop("Erro: " + TCSqlError(), "Falha")
        DisarmTransaction()
    EndIf

End Transaction
```

### 4.4 Perigos: bypass de triggers e logs

O `TCSqlExec` envia instrucoes diretamente ao banco, **ignorando**:

- **Gatilhos do dicionario** (SX7) -- nao sao disparados
- **Validacoes de campo** (SX3) -- nao sao verificadas
- **Integridade referencial** (SX9) -- nao e checada
- **Campos de controle do DBAccess** -- `INSDT`, `UPDDT` nao sao atualizados automaticamente em INSERT
- **Log de auditoria** -- operacoes podem nao ser registradas
- **Controle de numeracao** (GetSXENum) -- nao e consumido

**Consequencias possiveis de uso inadequado:**
- Dados orfaos no banco (registros sem FK valida)
- Inconsistencia entre tabelas relacionadas
- Campos de controle desatualizados (R_E_C_N_O_, INSDT, UPDDT)
- Problemas em rotinas que dependem dos gatilhos e validacoes

---

## 5. FWExecStatement (Forma Moderna e Segura)

A classe `FWExecStatement` e a forma **recomendada** pela TOTVS para execucao de queries no Protheus moderno. Ela combina parametrizacao (bind), cache de queries e protecao contra SQL Injection.

### 5.1 Sintaxe completa

```advpl
#Include "TOTVS.CH"

Local cQuery  := ""
Local oExec   := NIL
Local cAlias  := ""

// Montar query com placeholders ?
cQuery := "SELECT B1_COD, B1_DESC, B1_CUSTO1 "
cQuery += "FROM " + RetSQLName("SB1") + " SB1 "
cQuery += "WHERE SB1.B1_FILIAL = ? "
cQuery += "AND SB1.B1_TIPO = ? "
cQuery += "AND SB1.D_E_L_E_T_ = ' ' "
cQuery += "ORDER BY B1_COD "

// Instanciar e parametrizar
oExec := FWExecStatement():New(cQuery)
oExec:SetString(1, xFilial("SB1"))
oExec:SetString(2, "PA")

// Executar e obter alias
cAlias := oExec:OpenAlias()

// Navegar resultados
While (cAlias)->(!EoF())
    ConOut((cAlias)->B1_COD + " - " + (cAlias)->B1_DESC)
    (cAlias)->(DbSkip())
EndDo

// Fechar e destruir
(cAlias)->(DbCloseArea())
oExec:Destroy()
```

### 5.2 Metodos disponiveis

| Metodo | Sintaxe | Descricao |
|---|---|---|
| `New(cQuery)` | `FWExecStatement():New(cQuery)` | Cria instancia com a query |
| `SetString(nPos, cVal)` | `oExec:SetString(1, "PA")` | Define parametro tipo String |
| `SetNumeric(nPos, nVal)` | `oExec:SetNumeric(2, 100.50)` | Define parametro tipo Numerico |
| `SetDate(nPos, dVal)` | `oExec:SetDate(3, dDataBase)` | Define parametro tipo Data |
| `SetUnsafe(nPos, cVal)` | `oExec:SetUnsafe(1, cCampo)` | Define parametro sem tratamento (nomes de colunas, etc.) |
| `OpenAlias(cAlias, cLifeTime, cTimeout)` | `cAlias := oExec:OpenAlias()` | Executa query e retorna alias |
| `ExecScalar(cColumn, cLifeTime, cTimeout)` | `xVal := oExec:ExecScalar("B1_COD")` | Executa e retorna valor de uma coluna |
| `GetFixQuery()` | `cSQL := oExec:GetFixQuery()` | Retorna a query com parametros substituidos |
| `Destroy()` | `oExec:Destroy()` | Libera recursos do objeto |

### 5.3 Bind de parametros e SQL Injection

A protecao contra SQL Injection **so funciona quando a query e executada pelos metodos internos da classe**:

```advpl
// SEGURO: bind real no banco via OpenAlias
cAlias := oExec:OpenAlias()

// SEGURO: bind real no banco via ExecScalar
xVal := oExec:ExecScalar("B1_COD")

// INSEGURO: pegar a query e executar externamente
cSQL := oExec:GetFixQuery()
DbUseArea(.T., "TOPCONN", TcGenQry(,,cSQL), cAlias, .F., .T.)  // SEM protecao!
```

**Atencao:** O metodo `GetFixQuery()` apenas substitui os `?` pelos valores formatados na string. Ele **NAO** faz bind real no banco. A protecao contra SQL Injection so existe com `OpenAlias()` e `ExecScalar()`, pois estes usam `TCGenQry2` internamente com bind de parametros.

### 5.4 Quando preferir sobre TcGenQry

| Criterio | TcGenQry | FWExecStatement |
|---|---|---|
| Protecao SQL Injection | Nao | Sim (via OpenAlias/ExecScalar) |
| Cache de queries | Nao | Sim (reutiliza plano de execucao) |
| Parametrizacao | Manual (concatenacao) | Bind tipado |
| Complexidade | Baixa | Media |
| Recomendacao TOTVS | Legado | **Recomendada** |

**Use `FWExecStatement` quando:**
- Queries recebem input do usuario
- Performance e critica (cache de plano de execucao)
- Codigo novo ou refatoracao
- Seguranca e prioridade

---

## 6. FWPreparedStatement

Classe precursora da `FWExecStatement`, focada em formatacao e preparacao de queries com placeholders.

### 6.1 Sintaxe e uso

```advpl
Local oStmt   := FWPreparedStatement():New()
Local cQuery  := ""

cQuery := "SELECT * FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_TIPO = ? AND B1_LOCPAD = ? AND D_E_L_E_T_ = ' '"

oStmt:SetQuery(cQuery)
oStmt:SetString(1, "PA")
oStmt:SetString(2, "01")

// Obtem a query com parametros substituidos
cQueryFinal := oStmt:GetFixQuery()

// Executa pela forma classica (SEM protecao contra SQL injection)
DbUseArea(.T., "TOPCONN", TcGenQry(,,cQueryFinal), cAlias, .F., .T.)
```

### 6.2 Metodos de bind

| Metodo | Descricao |
|---|---|
| `SetQuery(cQuery)` | Define a query com placeholders `?` |
| `SetString(nPos, cVal)` | Define parametro tipo String (sem aspas simples -- a classe adiciona) |
| `SetNumeric(nPos, nVal)` | Define parametro tipo Numerico |
| `SetDate(nPos, dVal)` | Define parametro tipo Data |
| `SetIn(nPos, cValues)` | Define parametro para clausula IN |
| `GetFixQuery()` | Retorna a query com parametros substituidos |

**Exemplo com SetIn:**

```advpl
oStmt:SetQuery("SELECT * FROM " + RetSQLName("SB1") + " WHERE B1_TIPO IN (?) AND D_E_L_E_T_ = ' '")
oStmt:SetIn(1, "'PA','MP','MC'")
cQuery := oStmt:GetFixQuery()
```

### 6.3 Diferenca para FWExecStatement

| Caracteristica | FWPreparedStatement | FWExecStatement |
|---|---|---|
| Executa a query | Nao (apenas formata) | Sim (OpenAlias, ExecScalar) |
| SQL Injection | **Nao protege** (apenas substitui texto) | **Protege** (bind real no banco) |
| Cache de plano | Nao | Sim |
| Performance | Normal | Melhor |
| Recomendacao | **Evitar** em codigo novo | **Preferir** sempre |

**Resumo:** A `FWPreparedStatement` e util apenas como formatador de queries. Para protecao real contra SQL Injection e melhor performance, use `FWExecStatement` com `OpenAlias()` ou `ExecScalar()`.

---

## 7. MpSysOpenQuery

### 7.1 Quando usar

A `MpSysOpenQuery` e uma funcao de conveniencia que encapsula `DbUseArea` + `TcGenQry` + `ChangeQuery` + `TCSetField` automatico (consulta o dicionario para converter tipos). Originalmente criada para o modulo PLS (Planos de Saude), mas disponivel para uso geral.

**Vantagem principal:** Nao precisa chamar `TCSetField` manualmente para cada campo -- a funcao consulta o SX3 e aplica as conversoes automaticamente.

### 7.2 Sintaxe

```advpl
MpSysOpenQuery(cQuery, cAlias)
```

| Parametro | Tipo | Descricao |
|---|---|---|
| `cQuery` | Caractere | Query SQL a executar |
| `cAlias` | Caractere | Alias para o result set |

**Exemplo:**

```advpl
Local cAlias := GetNextAlias()
Local cQuery := ""

cQuery := "SELECT B1_COD, B1_DESC, B1_CUSTO1, B1_DTCAD "
cQuery += "FROM " + RetSQLName("SB1") + " SB1 "
cQuery += "WHERE B1_FILIAL = '" + xFilial("SB1") + "' "
cQuery += "AND D_E_L_E_T_ = ' ' "

MpSysOpenQuery(cQuery, cAlias)

// B1_CUSTO1 ja vem como Numerico, B1_DTCAD ja vem como Data
// Nao precisa de TCSetField!

While (cAlias)->(!EoF())
    ConOut((cAlias)->B1_COD + " - Custo: " + cValToChar((cAlias)->B1_CUSTO1))
    (cAlias)->(DbSkip())
EndDo
(cAlias)->(DbCloseArea())
```

**Observacoes:**
- Internamente aplica `ChangeQuery()`, entao nao aceita hints como `NOLOCK`
- A conversao automatica de tipos depende do campo existir no SX3
- Para campos calculados ou aliases que nao existem no SX3, ainda e necessario `TCSetField` manual

---

## 8. Montagem Segura de Queries

### 8.1 SQL Injection no Protheus

SQL Injection pode ocorrer no Protheus quando valores informados pelo usuario sao concatenados diretamente na query sem tratamento.

**Cenario de risco:**

```advpl
// VULNERAVEL: input do usuario vai direto na query
cCodigo := Space(15)

If MsDialog("Informe o codigo", @cCodigo)
    cQuery := "SELECT * FROM " + RetSQLName("SB1")
    cQuery += " WHERE B1_COD = '" + cCodigo + "'"
    // Se o usuario digitar: ' OR '1'='1
    // A query se torna: WHERE B1_COD = '' OR '1'='1'
    // Retornando TODOS os registros!
EndIf
```

**Cenario pior (com TCSqlExec):**

```advpl
// PERIGOSO: usuario pode injetar DELETE/DROP
cQuery := "UPDATE " + RetSQLName("ZZ1") + " SET ZZ1_STATUS = 'A' "
cQuery += "WHERE ZZ1_CODIGO = '" + cInputUsuario + "'"
// Se cInputUsuario = "'; DELETE FROM SZ1010; --"
// A instrucao se torna um DELETE na tabela!
```

### 8.2 Concatenacao vs parametrizacao

```advpl
// INSEGURO: concatenacao direta
cQuery := "SELECT * FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_COD = '" + cInput + "'"

// SEGURO: FWExecStatement com bind
cQuery := "SELECT * FROM " + RetSQLName("SB1") + " WHERE B1_COD = ?"
oExec := FWExecStatement():New(cQuery)
oExec:SetString(1, cInput)
cAlias := oExec:OpenAlias()

// SEGURO: TCGenQry2 com array de parametros
cQuery := "SELECT * FROM " + RetSQLName("SB1") + " WHERE B1_COD = ?"
DbUseArea(.T., "TOPCONN", TcGenQry2(,,cQuery, {cInput}), cAlias, .F., .T.)
```

### 8.3 Uso correto de aspas simples

```advpl
// Ao concatenar strings na query, use aspas simples para delimitar valores
cQuery += "WHERE B1_COD = '" + cCodigo + "' "

// Cuidado com valores que contem aspas simples!
// O valor "O'Brien" quebraria a query
// Solucao: escapar aspas simples duplicando-as
cNome := StrTran(cNome, "'", "''")
cQuery += "WHERE A1_NOME LIKE '%" + cNome + "%' "

// Melhor solucao: usar bind de parametros
oExec := FWExecStatement():New("SELECT * FROM " + RetSQLName("SA1") + " WHERE A1_NOME LIKE ?")
oExec:SetString(1, "%" + cNome + "%")
```

### 8.4 Validar inputs do usuario

```advpl
// Validar tipo e tamanho antes de usar na query
If ValType(cInput) != "C"
    Return
EndIf

// Remover caracteres perigosos se nao usar bind
cInput := FwNoAccent(cInput)         // Remove acentos
cInput := StrTran(cInput, "'", "")   // Remove aspas simples
cInput := StrTran(cInput, ";", "")   // Remove ponto-e-virgula
cInput := StrTran(cInput, "--", "")  // Remove comentarios SQL

// Ou, melhor ainda, use FWExecStatement com bind
```

---

## 9. Performance e Boas Praticas

### 9.1 Indices: SIX e FORCE INDEX

Os indices do Protheus sao definidos no dicionario SIX. Para saber quais indices existem:

```advpl
// Consultar indices de uma tabela via SIX
DbSelectArea("SIX")
SIX->(DbSetOrder(1))
SIX->(DbSeek("SB1"))
While SIX->(!EoF()) .And. SIX->INDICE == "SB1"
    ConOut("Ordem " + SIX->ORDEM + ": " + SIX->CHAVE)
    SIX->(DbSkip())
EndDo
```

**FORCE INDEX / INDEX HINT:**

Quando o otimizador do banco nao escolhe o indice correto, pode-se forcar:

```sql
-- SQL Server
SELECT B1_COD, B1_DESC FROM SB1010 WITH (INDEX(SB1010_01))
WHERE B1_FILIAL = '01' AND B1_COD >= '000001'

-- Dentro do Embedded SQL, use %NOPARSER% para evitar que ChangeQuery remova o hint
```

**Atencao:** Usar FORCE INDEX e uma medida excepcional. Prefira manter as estatisticas do banco atualizadas e criar indices adequados via Configurador.

### 9.2 TOP / LIMIT -- paginacao

```advpl
// SQL Server: TOP
cQuery := "SELECT TOP 100 B1_COD, B1_DESC FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
cQuery += " AND D_E_L_E_T_ = ' '"
cQuery += " ORDER BY B1_COD"

// PostgreSQL: LIMIT
cQuery := "SELECT B1_COD, B1_DESC FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
cQuery += " AND D_E_L_E_T_ = ' '"
cQuery += " ORDER BY B1_COD LIMIT 100"

// Paginacao com OFFSET (SQL Server 2012+)
cQuery := "SELECT B1_COD, B1_DESC FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
cQuery += " AND D_E_L_E_T_ = ' '"
cQuery += " ORDER BY B1_COD"
cQuery += " OFFSET " + cValToChar(nPagina * nTamPag) + " ROWS"
cQuery += " FETCH NEXT " + cValToChar(nTamPag) + " ROWS ONLY"
```

**Dica:** Use `TOP` / `LIMIT` sempre que precisar apenas de uma amostra dos dados, como em validacoes de existencia ou busca do proximo numero.

### 9.3 NOLOCK -- quando usar

O hint `WITH (NOLOCK)` (SQL Server) permite leitura suja (dirty read), evitando bloqueios em tabelas que estao sendo atualizadas por outras transacoes.

```advpl
// NOLOCK nao e compativel com ChangeQuery -- use %NOPARSER%
BeginSql Alias cAlias
    %NOPARSER%
    SELECT B1_COD, B1_DESC
    FROM SB1010 WITH (NOLOCK)
    WHERE B1_FILIAL = '01'
    AND D_E_L_E_T_ = ' '
EndSql
```

**Quando usar NOLOCK:**
- Consultas de leitura que nao precisam de precisao transacional absoluta
- Relatorios que nao podem esperar por locks
- Dashboards e consultas de status

**Quando NAO usar:**
- Operacoes que dependem de dados exatos para gravacao
- Queries que alimentam calculos financeiros criticos
- Ambientes com pouca concorrencia (NOLOCK e desnecessario)

**Cuidado:** Com `%NOPARSER%`, voce perde a portabilidade entre bancos. O `NOLOCK` e especifico do SQL Server.

### 9.4 Evitar SELECT *

```advpl
// RUIM: retorna todos os campos, gera trafego desnecessario
cQuery := "SELECT * FROM " + RetSQLName("SB1")

// BOM: apenas os campos necessarios
cQuery := "SELECT B1_COD, B1_DESC, B1_TIPO FROM " + RetSQLName("SB1")
```

**Motivos:**
- Trafego de rede reduzido
- Melhor utilizacao de indices de cobertura
- Menor consumo de memoria no Application Server
- Query mais legivel e facil de manter

### 9.5 Evitar funcoes no WHERE

Funcoes aplicadas a colunas no WHERE impedem o uso de indices:

```advpl
// RUIM: SUBSTRING impede uso do indice em B1_COD
cQuery += "WHERE SUBSTRING(B1_COD, 1, 3) = 'MOT'"

// BOM: usar LIKE ou comparacao direta
cQuery += "WHERE B1_COD LIKE 'MOT%'"

// RUIM: funcao em campo de data
cQuery += "WHERE YEAR(E2_EMISSAO) = 2024"

// BOM: range de datas
cQuery += "WHERE E2_EMISSAO >= '20240101' AND E2_EMISSAO <= '20241231'"
```

### 9.6 Funcoes de agregacao no SQL

Prefira fazer calculos no banco em vez de loops ADVPL:

```advpl
// RUIM: loop ADVPL para somar
nTotal := 0
While (cAlias)->(!EoF())
    nTotal += (cAlias)->D1_TOTAL
    (cAlias)->(DbSkip())
EndDo

// BOM: SUM no SQL
cQuery := "SELECT SUM(D1_TOTAL) AS TOTAL, COUNT(*) AS QTD, MAX(D1_EMISSAO) AS ULT_EMIS "
cQuery += "FROM " + RetSQLName("SD1") + " SD1 "
cQuery += "WHERE D1_FILIAL = '" + xFilial("SD1") + "' "
cQuery += "AND D1_FORNECE = '" + cFornece + "' "
cQuery += "AND D_E_L_E_T_ = ' ' "
```

### 9.7 JOINs -- LEFT JOIN e INNER JOIN

```advpl
// INNER JOIN: retorna apenas registros que existem em ambas as tabelas
cQuery := "SELECT SC5.C5_NUM, SC5.C5_EMISSAO, SA1.A1_NOME "
cQuery += "FROM " + RetSQLName("SC5") + " SC5 "
cQuery += "INNER JOIN " + RetSQLName("SA1") + " SA1 "
cQuery += "  ON SA1.A1_FILIAL = '" + xFilial("SA1") + "' "
cQuery += "  AND SA1.A1_COD = SC5.C5_CLIENTE "
cQuery += "  AND SA1.A1_LOJA = SC5.C5_LOJACLI "
cQuery += "  AND SA1.D_E_L_E_T_ = ' ' "
cQuery += "WHERE SC5.C5_FILIAL = '" + xFilial("SC5") + "' "
cQuery += "AND SC5.D_E_L_E_T_ = ' ' "

// LEFT JOIN: retorna todos da tabela da esquerda, mesmo sem correspondencia
cQuery := "SELECT SC5.C5_NUM, SC6.C6_ITEM, SC6.C6_PRODUTO "
cQuery += "FROM " + RetSQLName("SC5") + " SC5 "
cQuery += "LEFT JOIN " + RetSQLName("SC6") + " SC6 "
cQuery += "  ON SC6.C6_FILIAL = SC5.C5_FILIAL "
cQuery += "  AND SC6.C6_NUM = SC5.C5_NUM "
cQuery += "  AND SC6.D_E_L_E_T_ = ' ' "
cQuery += "WHERE SC5.C5_FILIAL = '" + xFilial("SC5") + "' "
cQuery += "AND SC5.D_E_L_E_T_ = ' ' "
```

**Atencao ao D_E_L_E_T_ em JOINs:** O filtro de deletados deve ir no `ON` do JOIN (para tabelas da direita) e no `WHERE` (para a tabela principal). Colocar no lugar errado muda o resultado, especialmente em LEFT JOINs.

### 9.8 Subqueries vs JOINs

```advpl
// Subquery no WHERE (pode ser menos eficiente)
cQuery := "SELECT C5_NUM, C5_EMISSAO FROM " + RetSQLName("SC5")
cQuery += " WHERE C5_FILIAL = '" + xFilial("SC5") + "'"
cQuery += " AND C5_CLIENTE IN ("
cQuery += "   SELECT A1_COD FROM " + RetSQLName("SA1")
cQuery += "   WHERE A1_FILIAL = '" + xFilial("SA1") + "'"
cQuery += "   AND A1_TIPO = '1' AND D_E_L_E_T_ = ' '"
cQuery += " )"
cQuery += " AND D_E_L_E_T_ = ' '"

// Equivalente com JOIN (geralmente mais eficiente)
cQuery := "SELECT DISTINCT SC5.C5_NUM, SC5.C5_EMISSAO "
cQuery += "FROM " + RetSQLName("SC5") + " SC5 "
cQuery += "INNER JOIN " + RetSQLName("SA1") + " SA1 "
cQuery += "  ON SA1.A1_FILIAL = '" + xFilial("SA1") + "' "
cQuery += "  AND SA1.A1_COD = SC5.C5_CLIENTE "
cQuery += "  AND SA1.A1_TIPO = '1' "
cQuery += "  AND SA1.D_E_L_E_T_ = ' ' "
cQuery += "WHERE SC5.C5_FILIAL = '" + xFilial("SC5") + "' "
cQuery += "AND SC5.D_E_L_E_T_ = ' ' "
```

**Quando subquery e melhor:**
- EXISTS/NOT EXISTS com correlacao
- Subquery que retorna poucos resultados
- Logica complexa que e mais legivel como subquery

**Quando JOIN e melhor:**
- Grandes volumes de dados
- Quando precisa de campos de ambas as tabelas no SELECT
- Otimizador consegue escolher melhor plano de execucao

### 9.9 %NOPARSER% -- quando usar

O token `%NOPARSER%` no Embedded SQL impede que o `ChangeQuery()` altere a query.

**Usar quando:**
- Precisa de hints de banco (`NOLOCK`, `FORCE INDEX`)
- Usa funcoes especificas do banco que o `ChangeQuery` converteria incorretamente
- A query ja esta otimizada para um banco especifico

**NAO usar quando:**
- O sistema precisa rodar em multiplos bancos de dados
- A query usa funcoes que tem equivalentes em outros bancos (ISNULL, SUBSTRING)
- Codigo padrao que deve ser portavel

```advpl
// Com %NOPARSER%: a query vai exatamente como escrita
BeginSql Alias cAlias
    %NOPARSER%
    SELECT TOP 10 B1_COD, ISNULL(B1_DESC, '') AS B1_DESC
    FROM SB1010 WITH (NOLOCK)
    WHERE B1_FILIAL = '01' AND D_E_L_E_T_ = ' '
EndSql

// Sem %NOPARSER%: ChangeQuery converte funcoes automaticamente
BeginSql Alias cAlias
    SELECT B1_COD, B1_DESC
    FROM %Table:SB1% SB1
    WHERE SB1.B1_FILIAL = %xFilial:SB1%
      AND SB1.%NotDel%
EndSql
```

### 9.10 Temporary tables com queries

A classe `FWTemporaryTable` permite criar tabelas temporarias no banco para queries complexas:

```advpl
#Include "TOTVS.CH"

Local oTempTable := FWTemporaryTable():New("TMP_CALC")

// Definir estrutura
oTempTable:AddField("COD",   "C", 15, 0)
oTempTable:AddField("DESC",  "C", 40, 0)
oTempTable:AddField("VALOR", "N", 15, 2)

// Criar no banco
oTempTable:Create()

// Inserir dados
cInsert := "INSERT INTO " + oTempTable:GetRealName()
cInsert += " (COD, DESC, VALOR) VALUES ('001', 'Teste', 100.50)"
TCSqlExec(cInsert)

// Consultar
cQuery := "SELECT * FROM " + oTempTable:GetRealName()
MpSysOpenQuery(cQuery, "QRYTMP")

While !QRYTMP->(EoF())
    ConOut(QRYTMP->COD + " - " + cValToChar(QRYTMP->VALOR))
    QRYTMP->(DbSkip())
EndDo
QRYTMP->(DbCloseArea())

// Destruir tabela temporaria
oTempTable:Delete()
```

---

## 10. Padroes Comuns

### 10.1 Query com parametros do SX1 (Pergunte)

O padrao `Pergunte` carrega parametros do SX1 nas variaveis `MV_PAR01` a `MV_PARxx`:

```advpl
#Include "TOTVS.CH"

User Function RELQRY()
    Local cAlias := GetNextAlias()

    // Carrega parametros do SX1 (grupo "RELQRY")
    Pergunte("RELQRY", .F.)
    // MV_PAR01 = Produto De
    // MV_PAR02 = Produto Ate
    // MV_PAR03 = Tipo

    cQuery := "SELECT B1_COD, B1_DESC, B1_TIPO, B1_CUSTO1 "
    cQuery += "FROM " + RetSQLName("SB1") + " SB1 "
    cQuery += "WHERE SB1.B1_FILIAL = '" + xFilial("SB1") + "' "
    cQuery += "AND SB1.B1_COD >= '" + MV_PAR01 + "' "
    cQuery += "AND SB1.B1_COD <= '" + MV_PAR02 + "' "
    cQuery += "AND SB1.B1_TIPO = '" + MV_PAR03 + "' "
    cQuery += "AND SB1.D_E_L_E_T_ = ' ' "
    cQuery += "ORDER BY B1_COD "

    cQuery := ChangeQuery(cQuery)
    DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)
    TCSetField(cAlias, "B1_CUSTO1", "N", 15, 2)

    While (cAlias)->(!EoF())
        // processar dados
        (cAlias)->(DbSkip())
    EndDo
    (cAlias)->(DbCloseArea())
Return
```

### 10.2 Query com progressbar (Processa/ProcRegua)

```advpl
#Include "TOTVS.CH"

User Function QRYPROG()
    Processa({|| fProcessa()}, "Processando dados...")
Return

Static Function fProcessa()
    Local cAlias := GetNextAlias()
    Local nTotal := 0
    Local cQuery := ""

    // Montar query
    cQuery := "SELECT B1_COD, B1_DESC FROM " + RetSQLName("SB1")
    cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
    cQuery += " AND D_E_L_E_T_ = ' '"
    cQuery := ChangeQuery(cQuery)

    DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)

    // Contar registros para a regua
    Count To nTotal
    (cAlias)->(DbGoTop())

    // Definir tamanho da regua
    ProcRegua(nTotal)

    While (cAlias)->(!EoF())
        IncProc("Processando: " + (cAlias)->B1_COD)

        // ... processamento ...

        (cAlias)->(DbSkip())
    EndDo

    (cAlias)->(DbCloseArea())
Return
```

**Alternativa: sem contar antes (regua indeterminada):**

```advpl
ProcRegua(0)  // Barra vai e volta sem percentual
While (cAlias)->(!EoF())
    IncProc("Processando...")
    // ...
    (cAlias)->(DbSkip())
EndDo
```

### 10.3 Query retornando dados para array

```advpl
#Include "TOTVS.CH"

Static Function QueryToArray()
    Local cAlias := GetNextAlias()
    Local aResult := {}
    Local cQuery := ""

    cQuery := "SELECT B1_COD, B1_DESC, B1_TIPO "
    cQuery += "FROM " + RetSQLName("SB1")
    cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
    cQuery += " AND B1_TIPO = 'PA'"
    cQuery += " AND D_E_L_E_T_ = ' '"
    cQuery += " ORDER BY B1_COD"
    cQuery := ChangeQuery(cQuery)

    DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)

    While (cAlias)->(!EoF())
        aAdd(aResult, {;
            Alltrim((cAlias)->B1_COD),;
            Alltrim((cAlias)->B1_DESC),;
            Alltrim((cAlias)->B1_TIPO);
        })
        (cAlias)->(DbSkip())
    EndDo

    (cAlias)->(DbCloseArea())

    // aResult agora contem um array bidimensional
    // Pode ser usado em ListBox, aFill, ou qualquer processamento
Return aResult
```

### 10.4 Query para relatorio TReport

```advpl
#Include "TOTVS.CH"
#Include "TOPCONN.CH"

User Function RELSQL()
    Local oReport  := NIL
    Local oSection := NIL

    oReport := TReport():New("RELSQL", "Relatorio de Produtos", , {|| fPrintReport(oReport)}, "Relatorio de produtos via SQL")
    oReport:PrintDialog()
Return

Static Function fPrintReport(oReport)
    Local cAlias := GetNextAlias()
    Local oSection := NIL
    Local cQuery := ""

    // Carregar parametros
    Pergunte("RELSQL", .F.)

    cQuery := "SELECT B1_COD, B1_DESC, B1_TIPO, B1_UM "
    cQuery += "FROM " + RetSQLName("SB1")
    cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
    cQuery += " AND B1_COD >= '" + MV_PAR01 + "'"
    cQuery += " AND B1_COD <= '" + MV_PAR02 + "'"
    cQuery += " AND D_E_L_E_T_ = ' '"
    cQuery += " ORDER BY B1_COD"
    cQuery := ChangeQuery(cQuery)

    DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)

    oSection := TRSection():New(oReport, "Produtos", {cAlias})
    TRCell():New(oSection, "B1_COD",   cAlias, "Codigo",   , 15)
    TRCell():New(oSection, "B1_DESC",  cAlias, "Descricao", , 40)
    TRCell():New(oSection, "B1_TIPO",  cAlias, "Tipo",     , 2)
    TRCell():New(oSection, "B1_UM",    cAlias, "Unidade",  , 2)

    oSection:Print()

    (cAlias)->(DbCloseArea())
Return
```

### 10.5 Query de RECNO para posicionamento

Quando precisa posicionar em registros da tabela real para alteracao/exclusao, use a query de RECNO:

```advpl
Local cAlias := GetNextAlias()

// Query retorna R_E_C_N_O_ para posicionamento
cQuery := "SELECT R_E_C_N_O_ AS NREC "
cQuery += "FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_FILIAL = '" + xFilial("SB1") + "'"
cQuery += " AND B1_MSBLQL = '1'"
cQuery += " AND D_E_L_E_T_ = ' '"
cQuery := ChangeQuery(cQuery)

DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)
TCSetField(cAlias, "NREC", "N", 10, 0)

DbSelectArea("SB1")
While (cAlias)->(!EoF())
    // Posiciona na tabela real usando o RECNO
    SB1->(DbGoto((cAlias)->NREC))

    // Agora pode usar RecLock para alterar
    If RecLock("SB1", .F.)
        SB1->B1_MSBLQL := "2"
        MsUnlock()
    EndIf

    (cAlias)->(DbSkip())
EndDo
(cAlias)->(DbCloseArea())
```

**Vantagem:** O `DbSkip` no result set da query e muito mais rapido que na tabela real, e o `DbGoto` por `R_E_C_N_O_` e eficiente pois e a chave primaria.

---

## 11. Armadilhas

### 11.1 Tabela de armadilhas comuns

| Armadilha | Sintoma | Solucao |
|---|---|---|
| Nao fechar alias (DbCloseArea) | Memory leak, erro de alias duplicado, esgotamento de conexoes | Sempre fechar em bloco finally/sequence |
| Alias fixo em vez de GetNextAlias | Erro fatal em recursividade ou reentrada | Usar `GetNextAlias()` |
| Campos de data retornam como string | Comparacao de datas falha, formatacao incorreta | Usar `TCSetField(alias, campo, "D", 8, 0)` |
| Campos numericos com precisao errada | Calculos com arredondamento incorreto | Usar `TCSetField(alias, campo, "N", tam, dec)` |
| Campos memo truncados | Texto cortado apos X caracteres | Tratar campo IMAGE com CONVERT/CAST; campos SYP precisam de funcao MSMM |
| ChangeQuery altera query inesperadamente | Hints removidos (NOLOCK), funcoes convertidas incorretamente | Usar `%NOPARSER%` ou nao chamar `ChangeQuery()` |
| Campo com palavra reservada SQL no nome | Query parseada incorretamente pelo ChangeQuery | Usar `FWPreparedStatement` ou renomear campo |
| Query funciona no SSMS mas nao no Protheus | Sintaxe especifica do banco nao reconhecida pelo ChangeQuery | Usar `%NOPARSER%` ou adaptar sintaxe |
| UNION sem alias em campos calculados | Erro de compilacao ou dados incorretos | Sempre usar `AS ALIAS` em campos calculados |
| Limite de 99 sub-selects | Erro fatal: "TOO MANY SUB-SELECTS" | Simplificar query ou usar tabelas temporarias |
| SELECT * com asterisco no inicio da linha | Pre-compilador interpreta como comentario | Nunca iniciar linha com `*` no Embedded SQL |
| Usar GetFixQuery achando que protege de SQL Injection | Vulnerabilidade a injecao SQL | Usar `OpenAlias()` ou `ExecScalar()` da `FWExecStatement` |
| D_E_L_E_T_ com `<> '*'` em vez de `= ' '` | Performance degradada (nao usa indice de forma otima) | Usar `D_E_L_E_T_ = ' '` |
| Comparar _FILIAL entre tabelas | Resultados incorretos quando tabelas tem compartilhamento diferente | Usar `xFilial()` para cada tabela separadamente |

### 11.2 Detalhamento das armadilhas

#### Nao fechar alias

```advpl
// PROBLEMA: alias nao e fechado em caso de erro
DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)
While (cAlias)->(!EoF())
    // Se ocorrer erro aqui, o alias fica aberto!
    nValor := 1 / nDivisor  // division by zero?
    (cAlias)->(DbSkip())
EndDo
(cAlias)->(DbCloseArea())

// SOLUCAO: proteger com BEGIN SEQUENCE
BEGIN SEQUENCE
    DbUseArea(.T., "TOPCONN", TcGenQry(,,cQuery), cAlias, .F., .T.)
    While (cAlias)->(!EoF())
        // processamento
        (cAlias)->(DbSkip())
    EndDo
END SEQUENCE
If Select(cAlias) > 0
    (cAlias)->(DbCloseArea())
EndIf
```

#### Campos memo truncados

Os campos MEMO no Protheus podem ser de dois tipos:

1. **Tipo IMAGE (campo BLOB no banco):** Precisa de CAST/CONVERT para ler via SQL:
```sql
-- SQL Server
SELECT CAST(campo_memo AS VARCHAR(8000)) AS MEMO_TEXT FROM tabela
```

2. **Tipo SYP (campo fragmentado na tabela SYP):** Os dados sao quebrados em multiplos registros na tabela SYP. Para ler, use a funcao `MSMM()` do ADVPL em vez de SQL direto.

#### ChangeQuery alterando query de forma inesperada

```advpl
// PROBLEMA: campo ZZZ_FROM e confundido com clausula FROM
cQuery := "SELECT ZZZ_FROM, ZZZ_TO FROM " + RetSQLName("ZZZ")
cQuery := ChangeQuery(cQuery)  // Pode parsear incorretamente!

// SOLUCAO 1: usar FWPreparedStatement para proteger
oStmt := FWPreparedStatement():New()
oStmt:SetQuery(cQuery)
cQuery := oStmt:GetFixQuery()

// SOLUCAO 2: nao usar ChangeQuery se ambiente e homogeneo
// (todos os servidores usam o mesmo banco)
```

#### UNION / UNION ALL -- cuidados

```advpl
// UNION remove duplicatas (mais lento)
// UNION ALL mantem duplicatas (mais rapido)
cQuery := "SELECT B1_COD, B1_DESC FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_TIPO = 'PA' AND D_E_L_E_T_ = ' '"
cQuery += " UNION ALL "
cQuery += "SELECT B1_COD, B1_DESC FROM " + RetSQLName("SB1")
cQuery += " WHERE B1_TIPO = 'MP' AND D_E_L_E_T_ = ' '"

// CUIDADO: todos os SELECTs devem ter o mesmo numero e tipo de colunas
// CUIDADO: ORDER BY so pode estar no ultimo SELECT
// CUIDADO: campos calculados precisam de alias identico em todos os SELECTs
```

#### Query funciona no SQL Management mas nao no Protheus

Causas comuns:
1. **ChangeQuery** converte funcoes de forma inesperada -- use `%NOPARSER%`
2. **Aspas duplas** em nomes de objetos -- Protheus usa aspas simples
3. **Caracteres especiais** na query -- verifique encoding
4. **Limite de tamanho** da query no DBAccess -- queries muito longas podem falhar
5. **Permissoes** -- o usuario do DBAccess pode ter permissoes diferentes do usuario usado no SSMS

---

## Referencias

### Documentacao oficial (TDN)

- [Embedded SQL](https://tdn.totvs.com/display/framework/Embedded+SQL)
- [Embedded SQL - Trabalhando com arquivos](https://tdn.totvs.com/display/public/framework/Embedded+SQL+-+Trabalhando+com+arquivos)
- [Embedded SQL - Guia de Boas Praticas](https://tdn.totvs.com/pages/viewpage.action?pageId=27675608)
- [Desenvolvendo queries no Protheus](https://tdn.totvs.com/display/framework/Desenvolvendo+queries+no+Protheus)
- [FWExecStatement](https://tdn.totvs.com/display/public/framework/FWExecStatement)
- [FWPreparedStatement](https://tdn.totvs.com/display/public/framework/FWPreparedStatement)
- [TCGenQry](https://tdn.totvs.com/display/tec/TCGenQry)
- [TCSetField](https://tdn.totvs.com/display/tec/TCSetField)
- [TCSQLExec](https://tdn.totvs.com/display/tec/TCSQLExec)
- [Comando TCQUERY](https://tdn.totvs.com/display/tec/Comando+TCQUERY)
- [ChangeQuery](https://tdn.totvs.com/display/public/framework/ChangeQuery)
- [Padrao SQL do Microsiga Protheus](https://tdn.totvs.com/pages/viewpage.action?pageId=23888877)
- [Indices Virtualizados no Protheus](https://tdn.totvs.com/pages/releaseview.action?pageId=240297971)
- [Estatisticas de banco de dados - MSSQL Server](https://tdn.totvs.com/pages/viewpage.action?pageId=589788219)
- [FWTemporaryTable](https://tdn.totvs.com/display/framework/FWTemporaryTable)

### Terminal de Informacao

- [BeginSQL / EndSQL](https://terminaldeinformacao.com/knowledgebase/beginsql-endsql/)
- [Executando queries com BeginSQL e EndSQL](https://terminaldeinformacao.com/2023/10/13/executando-queries-com-os-comandos-beginsql-e-endsql-maratona-advpl-e-tl-066/)
- [GetNextAlias](https://terminaldeinformacao.com/knowledgebase/getnextalias/)
- [RetSQLName](https://terminaldeinformacao.com/2024/05/17/buscando-o-nome-da-tabela-no-banco-com-a-retsqlname-maratona-advpl-e-tl-421/)
- [ChangeQuery](https://terminaldeinformacao.com/2023/10/25/padronizando-clausulas-sql-com-a-funcao-changequery-maratona-advpl-e-tl-078/)
- [FWPreparedStatement](https://terminaldeinformacao.com/2024/02/16/formatando-e-preparando-uma-query-com-a-fwpreparedstatement-maratona-advpl-e-tl-239/)
- [TCGenQry e TCGenQry2](https://terminaldeinformacao.com/2024/06/13/preparando-a-execucao-de-uma-query-atraves-das-tcgenqry-e-tcgenqry2-maratona-advpl-e-tl-474/)
- [TCSqlExec e TCSqlError](https://terminaldeinformacao.com/2024/06/17/executando-instrucoes-no-banco-com-tcsqlexec-e-tcsqlerror-maratona-advpl-e-tl-482/)
- [Diferenca entre TCQuery e PLSQuery](https://terminaldeinformacao.com/2020/08/27/qual-a-diferenca-entre-tcquery-e-plsquery/)
- [Como fazer um UPDATE via AdvPL](https://terminaldeinformacao.com/2021/04/21/como-fazer-um-update-via-advpl/)
- [Por que nao usar DELETE ou INSERT direto](https://terminaldeinformacao.com/2022/08/03/por-qual-motivo-nao-podemos-dar-delete-ou-insert-diretamente-em-uma-tabela-do-protheus/)
- [Campos MEMO via SQL Server](https://terminaldeinformacao.com/2018/11/21/como-ver-conteudo-de-um-campo-memo-sql-server/)
- [GetLastQuery](https://terminaldeinformacao.com/knowledgebase/getlastquery/)
- [Barras de processamento em AdvPL](https://terminaldeinformacao.com/2019/05/08/como-fazer-barras-de-processamento-em-advpl/)
- [MsSeek vs DbSeek](https://terminaldeinformacao.com/2020/07/23/voce-sabia-que-o-msseek-e-mais-performatico-que-o-dbseek-em-advpl/)
- [Video Aula AdvPL 012 - Consultas SQL](https://terminaldeinformacao.com/2015/12/04/vd-advpl-012/)
- [Como usar IN no FWPreparedStatement](https://terminaldeinformacao.com/2025/07/24/como-usar-o-in-no-fwpreparedstatement-ti-responde-0171/)
- [Manutencao de indices no SQL Server para Protheus](https://terminaldeinformacao.com/2025/03/05/automatizar-a-manutencao-de-indices-no-sql-server-com-foco-para-o-erp-protheus/)

### Forum TOTVS

- [Query String ou Embedded SQL](https://forum.totvs.io/t/query-string-ou-embedded-sql/20446)
- [Insert ou Update com bind](https://forum.totvs.io/t/insert-ou-update-com-bind/17437)
- [Criar indice direto no banco](https://forum.totvs.io/t/criar-indice-direto-no-banco/16607)
- [Inclusao/alteracao/delecao via update de dados no Protheus](https://forum.totvs.io/t/inclusao-alteracao-delecao-via-update-de-dados-no-protheus/16764)
