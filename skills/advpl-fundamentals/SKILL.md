---
description: Fundamentos ADVPL/TLPP — notação húngara (c/n/d/l/a/o/b/x), naming convention, prefixos de módulo, User Function precisa prefixo de cliente, 195 funções restritas pela TOTVS.
---

# advpl-fundamentals — Convenções básicas ADVPL/TLPP

ADVPL (Advanced Protheus Language) e seu sucessor TLPP são linguagens proprietárias da TOTVS, derivadas do Clipper/xBase. Têm convenções fortes que **não são opcionais** em código de qualidade Protheus.

## Quando usar

- Antes de gerar qualquer função/variável ADVPL.
- Quando o usuário pede para criar `User Function`, `Static Function`, `Main Function`.
- Ao revisar nomes de variáveis ou funções existentes.
- Ao decidir se um símbolo é do customer, do TOTVS padrão, ou de uma biblioteca terceira.
- Antes de chamar qualquer função "esquisita" (consulte `funcoes_restritas`).

## Notação húngara — obrigatória

Toda variável ADVPL começa com **um prefixo de tipo (1 letra minúscula)** seguido de **PascalCase**:

| Prefixo | Tipo                | Exemplo               |
|---------|---------------------|-----------------------|
| `c`     | Character (string)  | `cCodCli`, `cNomeFor` |
| `n`     | Numeric             | `nValor`, `nQtd`      |
| `d`     | Date                | `dEmissao`, `dHoje`   |
| `l`     | Logical (bool)      | `lOk`, `lExiste`      |
| `a`     | Array               | `aDados`, `aHeader`   |
| `o`     | Object              | `oModel`, `oView`     |
| `b`     | Code block          | `bValid`, `bWhile`    |
| `x`     | Variant / qualquer  | `xValor`, `xParam`    |
| `u`     | Undefined / unknown | `uRet`                |

Violação dispara `BP-006` no lint (severidade `info`).

```advpl
// CORRETO
Local cCodCli := "000001"
Local nValor  := 1500.00
Local lOk     := .T.

// ERRADO — sem prefixo, parecido com C
Local codigo := "000001"
Local valor  := 1500.00
```

## Prefixo de cliente em `User Function`

`User Function` é o ponto de entrada de customização. Por convenção institucional, **o nome deve começar com um prefixo de 2–3 letras do cliente** para evitar colisão com customizações de outros parceiros instaladas no mesmo RPO.

```advpl
// Cliente "XYZ"
User Function XYZValCli(cCod)  // OK
    Return .T.

// Sem prefixo — risco de sobrescrever User Function homônima de outro fornecedor
User Function ValCli(cCod)     // EVITAR
    Return .T.
```

Combine com o pattern de PE: `User Function MT100LOK()` (PE oficial, sem prefixo cliente — exceção justificada).

## Prefixos de módulo (rotinas TOTVS padrão)

Funções/rotinas oficiais TOTVS seguem padrões de prefixo por módulo. Conhecer ajuda a localizar rapidamente:

| Módulo                  | Código | Prefixos de função/rotina         | Tabelas típicas         |
|-------------------------|--------|-----------------------------------|-------------------------|
| Compras                 | COM    | `MATA1`, `MATA12`, `A097`, `A120` | SC1, SC2, SC7, SC8      |
| Estoque                 | EST    | `MATA0`, `MATA2`, `MATA3`         | SB1, SB2, SD1, SD2, SD3 |
| Faturamento             | FAT    | `MATA41`, `MATA46`, `MA410`       | SC5, SC6, SC9, SF2, SD2 |
| Financeiro              | FIN    | `FINA`, `FA0`, `FA1`              | SE1, SE2, SE5           |
| Contábil                | CTB    | `CTBA`, `CTB0`                    | CT1, CT2, CT5, CT7      |
| Fiscal                  | FIS    | `MATA9`, `MTA710`, `SPED`         | SF3, SF6, CDA, CDF      |
| RH                      | GPE    | `GPEA`, `RH`                      | SRA, RCB, RCC           |
| Manufatura              | PCP    | `MATA6`, `MATA65`                 | SH6, SH7, SHB           |

Use o lookup `modulos_erp` (carregado em `/plugadvpl:init`) para a lista completa.

## Naming — funções

- **`User Function`** → customização do cliente, prefixo cliente.
- **`Static Function`** → privada ao fonte, sem prefixo cliente obrigatório.
- **`Main Function`** → entrypoint de JOB, scheduler, MainAdvpl.
- **`Class ... Method`** → OOP (preferido em TLPP).

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

## Funções restritas pela TOTVS — 195 catalogadas

TOTVS mantém uma lista de **funções, classes e variáveis internas** que **não devem ser usadas em customização**:

- Não documentadas, não suportadas.
- Podem ser removidas/alteradas sem aviso.
- Algumas têm compilação bloqueada desde release 12.1.33.

Exemplos comuns que aparecem em código legado:

- `MV_PAR01..MV_PARxx` (use `ParamBox`/`Pergunte` parametrizados em vez de leitura direta).
- `nUsado` (variável interna do framework).
- Várias funções com prefixo `__` ou `Fwk`/`FW` internas.

Antes de usar qualquer função "que parece nativa", consulte:

```
/plugadvpl:find function <nome>
```

Se aparecer em `funcoes_restritas`, **não use**. Dispara `SEC-005` (crítico) no lint.

## Tipos primitivos e operadores

- Atribuição: `:=` (não `=`).
- Igualdade: `==` (estrito) ou `=` (igualdade ADVPL, depende do contexto).
- Diferente: `!=` ou `<>`.
- `.T.` / `.F.` — true / false.
- Conversão: `cValToChar`, `Val`, `StoD` (string-to-date), `DtoC`, `DtoS`.

## Anti-padrões

- Nomes sem prefixo húngaro → lint `BP-006`.
- Declarar `Local` no meio do código (depois de `If`/`While`) → lint `BP-002` (crítico).
- Usar `Private`/`Public` quando `Local` resolveria → lint `BP-002b`.
- `User Function` sem prefixo cliente → risco de colisão entre fornecedores.
- Usar `MV_PAR01` direto sem `ParamBox` → fragil, perde controle.
- Shadowing de variável reservada (`cFilAnt`, `cEmpAnt`, `__cInternet`) → lint `BP-008` (crítico).

## Referência rápida

| Conceito                      | Regra                                           |
|-------------------------------|-------------------------------------------------|
| Prefixo variável              | 1 letra minúscula + PascalCase                  |
| Atribuição                    | `:=`                                            |
| Comparação                    | `==`                                            |
| Bloco                         | `Begin Sequence`/`Recover`/`End Sequence`       |
| Declaração de variáveis       | `Local`/`Static`/`Private`/`Public` no topo     |
| Include padrão                | `#include "TOTVS.CH"` (NUNCA `Protheus.ch`)     |
| User Function                 | Prefixo de cliente (2–3 letras)                 |
| Função restrita               | Consulte `/plugadvpl:find function <nome>`      |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <nome>` — descobre se função é nativa, restrita ou customer.
- `/plugadvpl:lint <arq>` — valida convenções (BP-001..008).
- `/plugadvpl:callers <fn>` — vê quem chama uma função antes de renomear.
