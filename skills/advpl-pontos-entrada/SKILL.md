---
description: Pontos de Entrada (PEs) no Protheus — User Function NOME(PARAMIXB[1..N]), naming patterns, retorno por PARAMIXB[última-posição]. Use ao criar/editar PE.
---

# advpl-pontos-entrada — Customização via PE

**Ponto de Entrada (PE)** é o mecanismo oficial TOTVS para customizar comportamento de rotinas padrão **sem alterar o fonte original**. Toda rotina Protheus principal tem dezenas de PEs cadastrados em pontos estratégicos (antes de validar, antes de gravar, antes de imprimir, etc.).

O cliente implementa uma `User Function` com **nome exato e assinatura esperada** pela rotina TOTVS. Em runtime, o framework chama via reflection se a função existir no RPO.

## Quando usar

- Usuário pede "criar ponto de entrada", "implementar PE", "customizar rotina padrão TOTVS".
- Edit em arquivo cuja função casa com pattern de PE (`^[A-Z]{2,4}\d{2,4}[A-Z_]*$`).
- Investigar comportamento "modificado" de rotina TOTVS — provavelmente há PE ativa.
- Antes de copiar rotina TOTVS inteira para customizar → sempre prefira PE.

## Pattern de naming

Regex que casa a esmagadora maioria dos PEs oficiais:

```
^[A-Z]{2,4}\d{2,4}[A-Z_]*$
```

Exemplos:

- `MT100LOK` — Módulo MT (Faturamento) + 100 (rotina) + LOK (linha OK).
- `M460FIM` — MATA460 — fim do processamento.
- `MA410LOK` — MATA410 — Pedido de venda, line OK.
- `MA410BUT` — MATA410 — botões adicionais.
- `FA080INC` — FINA080 — pós-inclusão.
- `SF2100I` — SF2 + 100 + I (post Insert).

Sufixos comuns:

| Sufixo | Significa                       |
|--------|---------------------------------|
| `LOK`  | Line OK (valida linha em grid)  |
| `TOK`  | TudoOK (validação geral)        |
| `INC`  | Pós-Inclusão                    |
| `ALT`  | Pós-Alteração                   |
| `EXC`  | Pós-Exclusão                    |
| `CAN`  | Cancelamento                    |
| `BUT`  | Botões adicionais               |
| `MNU`  | Menu adicional                  |
| `FIM`  | Final do processamento          |
| `GRV`  | Gravação                        |
| `PRT`  | Impressão                       |
| `VLD`  | Validação                       |

## Assinatura padrão — PARAMIXB

PEs **não recebem parâmetros nomeados**. Recebem uma variável global `PARAMIXB` (array 1-based) preenchida pela rotina chamadora:

```advpl
#include "TOTVS.CH"

/*/{Protheus.doc} MT100LOK
PE Validacao na inclusao de NF de entrada.
Retorna .T. se valido, .F. para bloquear gravacao.
/*/
User Function MT100LOK()
    Local aArea  := GetArea()
    Local lOk    := .T.
    Local cNumNF := SF1->F1_DOC

    // Lógica de validação customizada
    If !MyValida(cNumNF)
        lOk := .F.
        Help(, , "Validacao", , "NF " + cNumNF + " bloqueada por regra interna", 1, 0)
    EndIf

    RestArea(aArea)
Return lOk
```

Quando há parâmetros, eles vêm em `PARAMIXB[N]`:

```advpl
User Function A120GRVC()
    Local aCab := PARAMIXB[1]   // array de cabeçalho do pedido
    Local aItens := PARAMIXB[2] // array de itens

    // Processa
Return Nil
```

## Indexação 1-based

ADVPL usa **arrays 1-based** (não 0-based como C/Python). `PARAMIXB[1]` é o primeiro elemento. **Ler `PARAMIXB[0]` dá erro de runtime.**

`paramixb_count` no lookup `pontos_entrada_padrao` indica quantos parâmetros a PE recebe.

## Retorno via PARAMIXB[última-posição]

Algumas PEs **modificam o último elemento** de `PARAMIXB` para devolver dado ao chamador:

```advpl
User Function MA440PGN()
    // PARAMIXB[1..N-1] são entrada
    // PARAMIXB[N] é o retorno (output)
    Local aSaida := PARAMIXB[Len(PARAMIXB)]

    aSaida[1] := nNovoValor
    PARAMIXB[Len(PARAMIXB)] := aSaida
Return Nil
```

A coluna `retorno_tipo` do lookup indica o tipo esperado: `L` (lógico), `C` (string), `N` (numérico), `A` (array), `O` (objeto), `` (sem retorno).

## Onde a PE é chamada

A rotina TOTVS faz algo como:

```advpl
// Dentro do fonte oficial MATA460
If ExistBlock("M460FIM")
    ExecBlock("M460FIM", .F., .F., {aCabec, aItens})
EndIf
```

`ExistBlock` checa se a User Function existe no RPO; `ExecBlock` invoca passando parâmetros que viram `PARAMIXB`. **Apenas uma User Function com aquele nome pode existir no RPO** — daí a importância de prefixo de cliente em `User Function` regulares (PEs são exceção: o nome é fixo).

## Workflow para criar PE

1. **Identifique a PE correta.** Consulte:
   - Documentação TDN da rotina TOTVS.
   - `/plugadvpl:find function <PE>` para ver se já existe no projeto.
   - Lookup `pontos_entrada_padrao` (catalogadas com `paramixb_count` e `retorno_tipo`).
2. **Crie arquivo `.prw`** com nome livre (ex: `XYZPE_MT100LOK.prw`). PEs ficam organizadas por módulo, não por arquivo.
3. **Escreva a User Function** com nome **exato** da PE (case-insensitive, mas convenção é UPPERCASE).
4. **Não use prefixo de cliente** no nome da PE — o nome é fixado pela TOTVS.
5. Cabeçalho Protheus.doc com `@since`, autor, motivo da customização.
6. **Salve e restaure área** se mexer com `DbSelectArea`/`DbSetOrder` (regra `BP-003`).
7. **Não bloqueie execução** com `MsgInfo`/`Alert` se a PE roda em JOB.

## Anti-padrões

- Duplicar User Function com mesmo nome de PE em arquivos diferentes → ambiguidade no compilador.
- Esquecer de retornar `.T.` em PE de validação (default `Nil` é truthy às vezes, mas é frágil).
- Misturar lógica de várias PEs num mesmo arquivo grande → dificulta manutenção.
- Acessar `PARAMIXB[0]` (1-based, dá erro).
- Não fazer `GetArea/RestArea` antes/depois → corrompe contexto da rotina chamadora.
- PE com side effect lento (HTTP síncrono, e-mail) sem tratamento → trava UX.
- Usar PE para fazer o que MVC já oferece via hook `bCommit`/`bTudoOk` (em cadastros MVC novos).

## Referência rápida

| Item                     | Regra                                    |
|--------------------------|------------------------------------------|
| Pattern de nome          | `^[A-Z]{2,4}\d{2,4}[A-Z_]*$`             |
| Assinatura               | `User Function NOME()` (sem args)        |
| Entrada                  | `PARAMIXB[1..N]` (1-based)               |
| Retorno (quando há)      | Valor retornado por `Return` OU `PARAMIXB[N]` |
| Sem prefixo de cliente   | Nome é fixado pela TOTVS                 |
| Onde colocar             | `.prw` qualquer (organize por módulo)    |

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <PE>` — verifica se PE já existe e onde.
- `/plugadvpl:callers <PE>` — vê quem dispara (provável `ExecBlock` em fonte TOTVS).
- `/plugadvpl:arch <arq>` — entende rotina principal antes de criar PE.
- Lookup `pontos_entrada_padrao` (carregado pelo init) — referência rápida.

## Referência profunda

Para detalhes completos (~1.2k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Catálogo de 200+ PEs oficiais TOTVS por módulo com `paramixb_count` e tipo de retorno.
- Diferenças entre PE pré-validação, pós-validação e pré/pós gravação.
- Padrões para PE multi-propósito (bifurcado por contexto via `PARAMIXB[1]`).
- Como diagnosticar conflito de PE (mesma User Function compilada em RPOs diferentes).
- PEs especiais: `OPENMENU`, `CHKFIL`, `LOGAVISO`, `FATORM`, e gatilhos APWEBEX.

## Exemplos práticos

Veja a pasta [`exemplos/`](exemplos/) ao lado deste SKILL.md para fonte real ADVPL de produção:

- `A300STRU.prw` — PE bifurcado (MODELDEF + VIEWDEF) que adiciona grid filha ao cadastro CNTA300 com gatilhos em cascata e validação preservada.
