---
description: Fundamentos ADVPL/TLPP — notação húngara (c/n/d/l/a/o/b/x/u), naming convention, escopos Local/Static/Private/Public, limite de 10 chars em .prw/.prx (250 em .tlpp), prefixo de cliente em User Function, ~195 funções restritas. Use antes de gerar/editar QUALQUER função, ao revisar nomes, ou ao decidir se símbolo é nativo/restrito/customer.
---

# advpl-fundamentals — Convenções básicas ADVPL/TLPP

ADVPL (Advanced Protheus Language) e seu sucessor TLPP (também chamado TL++) são linguagens proprietárias da TOTVS, derivadas do Clipper/xBase. Têm convenções fortes que **não são opcionais** em código de qualidade Protheus.

## Quando usar

- Antes de gerar qualquer `User Function`, `Static Function`, `Main Function`, classe ou método.
- Quando o usuário pede para criar/refatorar variáveis ou funções.
- Ao revisar nomes existentes (renomeação requer cuidado em ADVPL clássico — ver limite de 10 chars).
- Ao decidir se um símbolo é do customer, do TOTVS padrão, ou de uma biblioteca terceira.
- Antes de chamar qualquer função "esquisita" (consulte `funcoes_restritas` via `/plugadvpl:find function <nome>`).

## Limite de identificadores — depende da extensão do fonte

| Extensão | Compilador | Limite | Comportamento |
|---|---|---|---|
| `.prw`, `.prx` | ADVPL clássico | **10 chars** | Aceita nomes maiores mas usa **só os 10 primeiros**. Bug silencioso: `nTotalGeralAnual` e `nTotalGeralMensal` → ambos colapsam em `nTotalGera` → **mesma variável na memória**. Você grava em um, lê o outro. |
| `.tlpp` | TLPP / TL++ | 250 chars | Todos os chars contam, nomes distintos são distintos. |

**Cuidado especial com `User Function` em `.prw`:** o prefixo `U_` consome 2 chars → sobram **8 chars úteis**. `U_XYZMinhaFuncaoLonga` é referenciada internamente como `U_XYZMinhaF`. Risco real de colisão com qualquer outra `U_XYZMinhaFx`.

Veja `[[advpl-tlpp]]` pra detalhes do que TLPP libera (namespaces, classes com typing, access modifiers, identifiers longos).

## Notação húngara — obrigatória

Toda variável ADVPL começa com **um prefixo de tipo (1 letra minúscula)** seguido de **PascalCase**:

| Prefixo | Tipo                | Exemplo                              |
|---------|---------------------|--------------------------------------|
| `c`     | Character (string)  | `cCodCli`, `cNomeFor`                |
| `n`     | Numeric             | `nValor`, `nQtd`                     |
| `d`     | Date                | `dEmissao`, `dHoje`                  |
| `l`     | Logical (bool)      | `lOk`, `lExiste`                     |
| `a`     | Array               | `aDados`, `aHeader`                  |
| `o`     | Object              | `oModel`, `oView`                    |
| `b`     | Code block          | `bValid`, `bAcao`, `bWhen`, `bAfterCommit` |
| `x`     | Variant / qualquer tipo (uso explícito) | `xValor`, `xParam`     |
| `u`     | Undefined / unknown (retorno indefinido) | `uRet`                |

Violação dispara `BP-006` no lint (severidade `info`).

```advpl
// CORRETO
Local cCodCli := "000001"
Local nValor  := 1500.00
Local lOk     := .T.

// ERRADO — sem prefixo, parecido com C
Local codigo := "000001"
Local valor  := 1500.00

// ARMADILHA do .prw — bug silencioso por colisão de 10 chars
Local nTotalGeralAnual := 100   // vira nTotalGera
Local nTotalGeralMensal := 50   // TAMBEM vira nTotalGera (substitui!)
// Após este ponto, ambas as variáveis valem 50.
```

## Escopo de variáveis — tabela de decisão

Confusão clássica entre `Local`/`Static`/`Private`/`Public`. Regra prática:

| Escopo | Visibilidade | Vida | Quando usar |
|---|---|---|---|
| `Local` | só dentro da função | até `Return` da função | **95% dos casos** — default seguro |
| `Static` | arquivo inteiro | até unload do RPO | constantes/cache de fonte |
| `Private` | função declarante + chamadas filhas (não parent) | até `Return` da declarante | `MV_PAR*` (injetadas pelo `Pergunte`), frameworks legados |
| `Public` | todo lugar (qualquer função, qualquer fonte) | até logout/exit | **NÃO criar** — só TOTVS framework cria (`cFilAnt`, `cEmpAnt`, etc.) |

Violações:
- `Local` declarada **depois** de statement → `BP-002` (crítico)
- `Private`/`Public` quando `Local` resolveria → `BP-002b` (warning)
- Shadowing de reservada → `BP-008` (crítico) — ver lista abaixo

## Variáveis reservadas TOTVS — NUNCA declarar como Local/Private

São Public variables criadas pelo framework Protheus. Declarar como `Local`/`Private` faz **shadowing** — sua função enxerga `""` em vez do valor real.

| Reservada | O que carrega |
|---|---|
| `cFilAnt` | Filial atual (`SM0->M0_CODFIL`) |
| `cEmpAnt` | Empresa atual (`SM0->M0_CODIGO`) |
| `cUserName` | Usuário logado |
| `cModulo` | Módulo ativo (FAT, EST, COM, etc.) |
| `nProgAnt` | Programa anterior na pilha |
| `PARAMIXB` | Array de parâmetros do Ponto de Entrada |
| `aRotina` | Array de menu MVC / AxCadastro |
| `oMainWnd` | Janela principal do Protheus |
| `lMsErroAuto` | Flag de erro em rotina automática |
| `lMsHelpAuto` | Flag de help automático |
| `__cInternet` | Indicador de execução web |
| `nUsado` | Contador interno (framework) |

Lint `BP-008` (critical) pega tentativa de redeclaração.

## Prefixo de cliente em `User Function`

`User Function` é o ponto de entrada de customização. Por convenção institucional, **o nome deve começar com um prefixo de 2-3 letras do cliente** para evitar colisão com customizações de outros parceiros instaladas no mesmo RPO.

```advpl
// Cliente "XYZ"
User Function XYZValCli(cCod)  // OK
    Return .T.

// Sem prefixo — risco de sobrescrever User Function homônima de outro fornecedor
User Function ValCli(cCod)     // EVITAR
    Return .T.
```

Combine com o pattern de PE: `User Function MT100LOK()` (PE oficial TOTVS, sem prefixo cliente — exceção justificada). Veja `[[advpl-pontos-entrada]]`.

## TLPP namespace convention (resumo)

Em `.tlpp` (TLPP 17.3.0+), namespaces evitam colisões sem precisar do prefixo cliente:

```tlpp
namespace custom.fat.pedidos.validacoes

@type function
function ValidaCli(cCod as character) as logical
    return AllTrim(cCod) != ""
endfunction
```

Regras canônicas:
- Tudo lowercase, separado por **ponto**, sem underscore
- Custom começa com `custom.<segmento>.<servico>.<funcionalidade>`
- `tlpp.*` é reservado pra tlppCore — qualquer tentativa de uso bloqueia compilação

Detalhes em `[[advpl-tlpp]]`.

## Prefixos de módulo (rotinas TOTVS padrão)

Funções/rotinas oficiais TOTVS seguem padrões de prefixo por módulo. Conhecer ajuda a localizar rapidamente:

| Módulo                  | Código | Prefixos típicos                  | Tabelas chave           |
|-------------------------|--------|-----------------------------------|-------------------------|
| Compras                 | COM    | `MATA1`, `MATA12`, `A097`, `A120` | SC1, SC2, SC7, SC8      |
| Estoque                 | EST    | `MATA0`, `MATA2`, `MATA3`         | SB1, SB2, SD1, SD2, SD3 |
| Faturamento             | FAT    | `MATA41`, `MATA46`, `MA410`       | SC5, SC6, SC9, SF2, SD2 |
| Financeiro              | FIN    | `FINA`, `FA0`, `FA1`              | SE1, SE2, SE5           |
| Contábil                | CTB    | `CTBA`, `CTB0`                    | CT1, CT2, CT5, CT7      |
| Fiscal                  | FIS    | `MATA9`, `MTA710`, `SPED`         | SF3, SF6, CDA, CDF      |
| RH / GPE                | GPE    | `GPEA`, `RH`                      | SRA, RCB, RCC           |
| Manufatura / PCP        | PCP    | `MATA6`, `MATA65`                 | SH6, SH7, SHB           |
| Planejamento (alt.)     | PMS    | `PMSA`, `PMSR`                    | AF6, AF8, AFA           |
| Backoffice / Active     | APE    | `APEA`, `APEB`                    | SDP, SAU                |
| Telemarketing           | TMK    | `TMKA`, `TMK1`                    | SUA, SUB, SUC           |
| Transportes/Logística   | TMS    | `TMSA`, `TMSR`                    | DUA, DUB, DUC, GDC      |
| Jurídico                | JUR    | `JURA`, `JURJ`                    | NSZ, NSY                |
| Automação Fiscal        | TAF    | `TAFA`, `TAFE`                    | CTW, CTV (eventos)      |
| Configurador            | CFG    | `APSDU`, `MATAxxx`                | SX1..SXG, SIX           |

Use o lookup `modulos_erp` (carregado em `/plugadvpl:init`) para a lista completa.

## Naming — funções

- **`User Function`** → customização do cliente, prefixo cliente (2-3 letras).
- **`Static Function`** → privada ao fonte, sem prefixo cliente obrigatório.
- **`Main Function`** → entrypoint de JOB, scheduler, MainAdvpl.
- **`Class ... Method`** → OOP (padrão em TLPP; opcional em ADVPL clássico).

Toda função (incluindo `Static`) deveria ter cabeçalho **Protheus.doc** (regra `BP-007`, severidade `info`):

```advpl
/*/{Protheus.doc} XYZValCli
Valida codigo do cliente conforme regra fiscal do cliente XYZ.
@type function
@author Equipe ABC
@since 2024-01-15
@param cCod, character, codigo do cliente
@return logical, .T. se valido
/*/
User Function XYZValCli(cCod)
    Return AllTrim(cCod) != ""
```

## Funções built-in de alta frequência (cheat sheet)

Top funções nativas que aparecem em ~todo código ADVPL — usar com precisão evita reinventar:

| Categoria | Funções comuns |
|---|---|
| String | `AllTrim`, `SubStr`, `At`, `RAt`, `StrTran`, `Upper`, `Lower`, `Padr`, `Padl`, `Replicate`, `Stuff` |
| Numérico | `Round`, `Int`, `Abs`, `Max`, `Min`, `Mod`, `Val`, `Str` |
| Data | `Date`, `StoD`, `DtoC`, `DtoS`, `Day`, `Month`, `Year`, `MonthName`, `FwTimeStamp` |
| Conversão | `cValToChar`, `cValToStr`, `Iif`, `Empty`, `Type`, `ValType` |
| Array | `Len`, `AScan`, `ASort`, `AEval`, `aAdd`, `aDel`, `aIns`, `aClone`, `AFill`, `aSize` |
| Existência | `ExistChav`, `ExistCpo`, `File`, `IsNumeric`, `IsDigit`, `IsAlpha` |
| ERP-específico (Protheus) | `xFilial`, `xMoeda`, `GetMv`/`SuperGetMv`, `GetSx8Num`, `ConfirmSx8`, `RollBackSx8`, `RecLock`, `MsUnlock`, `Posicione`, `DbSeek`, `DbSelectArea`, `DbSetOrder` |

Lista completa indexada em `funcoes_nativas` (~280 funções). Use `/plugadvpl:find function <nome>` para checar.

## Funções restritas pela TOTVS — ~195 catalogadas

TOTVS mantém uma lista de **funções, classes e variáveis internas** que **não devem ser usadas em customização**:

- Não documentadas, não suportadas.
- Podem ser removidas/alteradas sem aviso.
- Algumas têm compilação bloqueada desde release 12.1.33.

Exemplos comuns que aparecem em código legado:

- `nUsado` (variável interna do framework — também é reservada, ver tabela acima).
- Funções com prefixo `__` ou internas `FW*` não documentadas.

> **Não confunda:** `MV_PAR01..MV_PARxx` **não são** restritas TOTVS — são `Private` variables que `Pergunte()` injeta automaticamente. Não são "proibidas", são **frágeis**: dependem da ordem do grupo SX1 e quebram se o grupo mudar. Prefira `ParamBox()` para controle explícito.

Antes de usar qualquer função "que parece nativa", consulte:

```
/plugadvpl:find function <nome>
```

Se aparecer em `funcoes_restritas`, **não use**. Dispara `SEC-005` (crítico) no lint. Veja `[[advpl-code-review]]`.

## Tipos primitivos e operadores

- Atribuição: `:=` (não `=`).
- Igualdade: `==` (estrito, comparação caractere-a-caractere) ou `=` (igualdade ADVPL: trim + case-insensitive em strings com `SET EXACT OFF`).
- Diferente: `!=` ou `<>`.
- `.T.` / `.F.` — true / false.
- Conversão: `cValToChar`, `Val`, `StoD` (string-to-date), `DtoC`, `DtoS`.
- Ternário: `Iif(cond, valIfTrue, valIfFalse)`.

## Anti-padrões

- **Nomes sem prefixo húngaro** → lint `BP-006`.
- **Declarar `Local` no meio do código** (depois de `If`/`While`) → lint `BP-002` (crítico).
- **Usar `Private`/`Public` quando `Local` resolveria** → lint `BP-002b`.
- **`User Function` sem prefixo cliente** → risco de colisão entre fornecedores no mesmo RPO.
- **Usar `MV_PAR01` direto sem `ParamBox`/`Pergunte`** → frágil, dependente de ordem do SX1.
- **Shadowing de variável reservada** (`cFilAnt`, `cEmpAnt`, `__cInternet`, `PARAMIXB`, `lMsErroAuto`) → lint `BP-008` (crítico).
- **Identificadores com acento** (`cNomeCliênte`) — compilador aceita mas quebra deserialização cross-encoding (CSV exports, REST payloads). Use sempre ASCII em nome.
- **Em `.prw`, nomes > 10 chars muito parecidos** → bug silencioso de colisão (ver tabela de limite no topo).

## Referência rápida

| Conceito                      | Regra                                           |
|-------------------------------|-------------------------------------------------|
| Prefixo variável              | 1 letra minúscula + PascalCase                  |
| Atribuição                    | `:=`                                            |
| Comparação                    | `==`                                            |
| Bloco protegido               | `Begin Sequence`/`Recover`/`End Sequence`       |
| Declaração de variáveis       | `Local`/`Static`/`Private`/`Public` no topo     |
| Include moderno               | `#include "TOTVS.CH"` (preferido; `Protheus.ch` é legado mas ainda compila) |
| User Function (`.prw`)        | Prefixo cliente (2-3 letras), ≤ 8 chars úteis após `U_` |
| TLPP function (`.tlpp`)       | namespace + identifier longo OK                 |
| Função restrita               | Consulte `/plugadvpl:find function <nome>`      |
| ASCII-only em identificadores | sempre — acento quebra encoding cross-tools     |

## Cross-references com outras skills

- `[[advpl-tlpp]]` — TLPP/TL++ namespaces, OO, annotations, typing.
- `[[advpl-mvc]]` / `[[advpl-mvc-avancado]]` — convenções específicas de MVC (aRotina, ModelDef, etc.).
- `[[advpl-pontos-entrada]]` — User Function como PE (sem prefixo cliente, exceção justificada).
- `[[advpl-encoding]]` — `.prw` cp1252 vs `.tlpp` utf-8 (afeta acentos no source).
- `[[advpl-code-review]]` — regras BP/SEC/PERF/MOD detalhadas.
- `[[advpl-debugging]]` — quando uma "variável some" pode ser shadow ou colisão de 10 chars.
- `[[plugadvpl-index-usage]]` — comandos plugadvpl pra investigar nomenclatura no projeto.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <nome>` — descobre se função é nativa, restrita ou customer.
- `/plugadvpl:lint <arq>` — valida convenções (BP-001..008).
- `/plugadvpl:callers <fn>` — vê quem chama antes de renomear (especialmente em .prw onde colisão de 10 chars é risco).
- `/plugadvpl:grep "<termo>"` — busca textual no projeto.

## Referência profunda

Para detalhes completos (~2.9k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Histórico ADVPL/Clipper e arquitetura do RPO/APO compilado.
- Diretivas de pré-processamento (`#include`, `#define`, `#command`, `#xcommand`, `#translate`) com exemplos.
- Catálogo expandido de funções de string, data, array, conversão (Substr, At, Asc, Time, MonthName, AScan, ASort, AEval).
- Estruturas de controle avançadas (`Begin Sequence`/`Break`/`Recover`, `For Each`, code blocks).
- Tabela completa de prefixos de módulo (50+ módulos com tabelas/rotinas típicas) e regras de naming.
