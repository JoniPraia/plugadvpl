---
description: Pontos de Entrada (PEs) no Protheus — User Function NOME(PARAMIXB[1..N]), naming patterns (MA440LOK/MT100GRV/A300STRU), retorno via Return ou PARAMIXB[última-posição], convenção _pe.prw, ExecBlock/ExistBlock no fonte TOTVS, ~280 PEs catalogadas em pontos_entrada_padrao. Use ao criar/editar PE, refatorar rotina customizada que devia ser PE, ou investigar comportamento estranho em rotina padrão.
---

# advpl-pontos-entrada — Customização via PE

**Ponto de Entrada (PE)** é o mecanismo oficial TOTVS para customizar comportamento de rotinas padrão **sem alterar o fonte original**. Toda rotina Protheus principal tem dezenas de PEs cadastrados em pontos estratégicos (antes de validar, antes de gravar, antes de imprimir, etc.).

O cliente implementa uma `User Function` com **nome exato e assinatura esperada** pela rotina TOTVS. Em runtime, o framework chama via `ExecBlock` se a função existir no RPO (`ExistBlock` confirma).

## Quando usar

- Usuário pede "criar ponto de entrada", "implementar PE", "customizar rotina padrão TOTVS".
- Edit em arquivo cuja função casa com pattern de PE (ver regex abaixo).
- Investigar comportamento "modificado" de rotina TOTVS — provavelmente há PE ativa.
- Antes de copiar rotina TOTVS inteira para customizar → **sempre prefira PE**.
- Customização de cadastro MVC padrão (PE STRU/MOD/VLD/COMMIT) — veja `[[advpl-mvc-avancado]]`.

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
- `A300STRU` — CNTA300 — estrutura MVC (model + view).

### Sufixos comuns por classe de hook

| Sufixo  | Significa                                     | Tipo de PE                   |
|---------|-----------------------------------------------|------------------------------|
| `LOK`   | Line OK (valida linha em grid `GetDados`)     | Validação grid               |
| `TOK`   | TudoOK (validação geral pré-gravação)         | Validação geral              |
| `INC`   | Pós-Inclusão                                  | Pós-commit                   |
| `ALT`   | Pós-Alteração                                 | Pós-commit                   |
| `EXC`   | Pós-Exclusão                                  | Pós-commit                   |
| `CAN`   | Cancelamento                                  | Cleanup                      |
| `BUT`   | Botões adicionais na toolbar                  | UI                           |
| `MNU`   | Menu adicional                                | UI                           |
| `FIM`   | Final do processamento                        | Post-process                 |
| `GRV`   | Gravação (durante)                            | Commit interno               |
| `PRT`   | Impressão                                     | Print                        |
| `VLD`   | Validação (custom)                            | Validação                    |
| `MOD`   | Customiza ModelDef (MVC)                      | MVC structure                |
| `STRU`  | Estrutura MVC (Model + View bifurcado)        | MVC structure                |
| `COMMIT`| Commit MVC pós-gravação                       | MVC commit                   |
| `MARK`  | Validação de marcação em MarkBrowse           | UI                           |

Veja `[[advpl-mvc-avancado]]` pra os sufixos MVC (`STRU`/`MOD`/`COMMIT`).

## Assinatura padrão — PARAMIXB

PEs **não recebem parâmetros nomeados**. Recebem uma variável global `PARAMIXB` (array 1-based) preenchida pela rotina chamadora:

```advpl
#include "TOTVS.CH"

/*/{Protheus.doc} MT100LOK
PE Validacao na inclusao de NF de entrada.
Retorna .T. se valido, .F. para bloquear gravacao.
@type function
@author Equipe XYZ
@since 2026-05-12
/*/
User Function MT100LOK()
    Local aArea  := GetArea()
    Local lOk    := .T.
    Local cNumNF := SF1->F1_DOC

    // Logica de validacao customizada
    If !U_XYZValNF(cNumNF)
        lOk := .F.
        Help(, , "Validacao", , "NF " + cNumNF + " bloqueada por regra interna", 1, 0)
    EndIf

    RestArea(aArea)
Return lOk
```

Quando há parâmetros, eles vêm em `PARAMIXB[N]` (1-based):

```advpl
User Function A120GRVC()
    Local aCab   := PARAMIXB[1]   // array de cabecalho do pedido
    Local aItens := PARAMIXB[2]   // array de itens

    // Processa
Return Nil
```

> **Indexação 1-based:** ADVPL usa **arrays 1-based** (não 0-based como C/Python). `PARAMIXB[1]` é o primeiro elemento. **Ler `PARAMIXB[0]` dá erro de runtime "Index out of range".**

`paramixb_count` no lookup `pontos_entrada_padrao` indica quantos parâmetros a PE recebe.

## Retorno via PARAMIXB[última-posição]

Algumas PEs **modificam o último elemento** de `PARAMIXB` para devolver dado ao chamador (pattern menos comum mas existe):

```advpl
User Function MA440PGN()
    // PARAMIXB[1..N-1] sao entrada
    // PARAMIXB[N] eh o retorno (output)
    Local aSaida := PARAMIXB[Len(PARAMIXB)]

    aSaida[1] := nNovoValor
    PARAMIXB[Len(PARAMIXB)] := aSaida
Return Nil
```

A coluna `retorno_tipo` do lookup indica o tipo esperado: `L` (lógico), `C` (string), `N` (numérico), `A` (array), `O` (objeto), `` (sem retorno explícito, valor passado via `PARAMIXB[última]` ou nenhum retorno).

## Como a PE é chamada no fonte TOTVS

A rotina padrão faz algo como:

```advpl
// Dentro do fonte oficial MATA460 (visivel no codigo TOTVS)
If ExistBlock("M460FIM")
    ExecBlock("M460FIM", .F., .F., {aCabec, aItens})   // 4o param = array vira PARAMIXB
EndIf
```

- `ExistBlock(nome)` — checa se a User Function existe **no RPO** (compilada).
- `ExecBlock(nome, lShowError, lShowMsg, uParam)` — invoca passando parâmetros que viram `PARAMIXB`.

**Apenas uma User Function com aquele nome pode existir no RPO** — daí a importância de prefixo de cliente em `User Function` regulares (PEs são exceção: o nome é fixo TOTVS).

### Conflito de RPO entre módulos

Quando o cliente compila PE em RPO/módulo diferente do RPO TOTVS, o framework procura na ordem:

1. RPO do cliente (custom) primeiro
2. RPO TOTVS depois

Se duas PEs com mesmo nome existem em RPOs diferentes, **a do cliente vence** (último compilado em alguns cenários). Se PE não disparou, suspeite de RPO desatualizado.

## Convenção de nome de arquivo: `<rotina>_pe.prw`

TOTVS recomenda nomear o arquivo `.prw` com sufixo `_pe.prw` (especialmente em PE MVC):

```
MATA070_pe.prw          → contem User Function MA070STRU(), MA070VLD(), etc.
MATA440_pe.prw          → contem PEs do pedido de compra
XYZPe_MT100LOK.prw      → alternativa, prefixo cliente + nome PE
```

### Caso especial MVC: nome do arquivo ≠ nome da User Function

Em MVC, **o nome do arquivo `.prw` não pode bater com o nome do `ModelDef`** do fonte TOTVS (causa conflito de compilação). TOTVS recomenda:

```
// ERRADO — fonte CRMA980 tem ModelDef CRMA980; meu arquivo seria CRMA980.prw mas conflita
CRMA980.prw                 // não criar com este nome

// CERTO
MyCRMA980.prw               // nome diferente
   ↓ dentro:
User Function CRMA980()     // nome da PE pode bater (User Function != ModelDef)
   ...
End
```

Veja `[[advpl-mvc-avancado]]` para padrões PE STRU/MOD/VLD/COMMIT em rotinas MVC.

## TLPP — mesmo PE pattern funciona

Em `.tlpp` o pattern de PE é idêntico — `User Function` continua funcionando como em ADVPL clássico. Diferença é que TLPP libera identificadores > 10 chars (veja `[[advpl-fundamentals]]`), então PE com sufixo longo (`MT100VALIDACAO`) compila mas o nome canônico TOTVS tem ≤ 10 chars de qualquer jeito.

## Workflow para criar PE

1. **Identifique a PE correta:**
   - `/plugadvpl:find function <PE>` para ver se já existe no projeto.
   - Lookup `pontos_entrada_padrao` (carregado pelo `init`, ~280 PEs catalogadas).
   - Documentação TDN da rotina TOTVS (Central de Atendimento ou pesquisa direta).
2. **Crie arquivo `.prw`** com nome `<rotina>_pe.prw` ou `XYZPe_<PE>.prw`. PEs ficam organizadas por módulo, não por arquivo único.
3. **Escreva a User Function** com nome **exato** da PE (case-insensitive em ADVPL, mas convenção é UPPERCASE).
4. **Não use prefixo de cliente** no nome da PE — o nome é fixado pela TOTVS. (Exceção justificada da regra `SEC-002`.)
5. **Cabeçalho Protheus.doc** com `@since`, autor, motivo da customização — facilita auditoria futura.
6. **`GetArea()`/`RestArea()`** no início/fim se mexer com `DbSelectArea`/`DbSetOrder` (regra `BP-003` catalogada).
7. **Tipo de retorno**: `Return .T.`/`.F.` em PEs de validação, `Return Nil` em PEs pós-evento. Confira `retorno_tipo` no catálogo.
8. **Não bloqueie execução** com `MsgInfo`/`Alert` se a PE pode rodar em JOB sem UI (veja `[[advpl-jobs-rpc]]`).

## Anti-padrões

- **Duplicar User Function com mesmo nome de PE em arquivos diferentes** → ambiguidade no compilador.
- **Esquecer de retornar `.T.` em PE de validação** → default `Nil` é frágil; alguns frameworks tratam como `.F.` e bloqueiam.
- **Misturar lógica de várias PEs num mesmo arquivo grande** sem organização → dificulta manutenção.
- **Acessar `PARAMIXB[0]`** — array é 1-based, `[0]` dá erro.
- **Não fazer `GetArea()/RestArea()`** antes/depois de mexer em alias → corrompe contexto da rotina chamadora.
- **PE com side effect lento** (HTTP síncrono, e-mail, query pesada) sem `Begin Sequence/Recover` → trava UX ou estoura timeout em runtime.
- **Usar PE em cadastro MVC novo** para fazer o que `InstallEvent`/`FWModelEvent` já oferece (veja `[[advpl-mvc]]`).
- **PE com `MsgInfo`/`Alert`** que roda em job/REST → trava o job esperando interação.
- **Renomear `User Function` no `.prw`** mas esquecer de atualizar `_pe.prw` correspondente — PE vira fantasma.
- **Compilar PE em RPO diferente do esperado** sem verificar ordem de carga — PE pode não disparar.

## Workflow de diagnóstico — "minha PE não dispara"

1. **Confirme nome exato** — typo em 1 letra invalida (case OK, mas char errado não).
2. `/plugadvpl:find function <PE>` no projeto — confirma que compila.
3. Verifique que está no RPO atual do ambiente (admin → `apsdu` ou `Inspector`).
4. `/plugadvpl:callers <PE>` no projeto TOTVS (se indexado) — confirma que rotina padrão tem `ExistBlock` chamando esse nome.
5. Adicione `ConOut("PE <NOME> disparou em " + FwTimeStamp())` como primeira linha — confirma execução.
6. Verifique RPO de origem (cliente custom × TOTVS padrão) — conflito de compilação.

## Referência rápida

| Item                     | Regra                                              |
|--------------------------|----------------------------------------------------|
| Pattern de nome          | `^[A-Z]{2,4}\d{2,4}[A-Z_]*$`                       |
| Assinatura               | `User Function NOME()` (sem args)                  |
| Entrada                  | `PARAMIXB[1..N]` (1-based)                         |
| Retorno (quando há)      | Valor de `Return` OU mudança em `PARAMIXB[última]` |
| Sem prefixo de cliente   | Nome é fixado pela TOTVS (exceção SEC-002 lint)    |
| Convenção de arquivo     | `<rotina>_pe.prw` ou `XYZPe_<PE>.prw`              |
| Mecanismo                | `ExecBlock` + `ExistBlock` no fonte TOTVS          |
| TLPP                     | Mesmo pattern (`User Function` funciona)           |

## Cross-references com outras skills

- `[[advpl-mvc]]` — quando PE customiza cadastro próprio MVC, considere FWModelEvent.
- `[[advpl-mvc-avancado]]` — PEs MVC: `<rotina>STRU/MOD/VLD/COMMIT` — padrão completo.
- `[[advpl-fundamentals]]` — `User Function` no contexto geral (limite 10 chars em `.prw`).
- `[[advpl-code-review]]` — `SEC-002` (User Function sem prefixo cliente) — exceção pra PEs.
- `[[advpl-embedded-sql]]` — queries dentro de PEs (com macros).
- `[[advpl-encoding]]` — `.prw` cp1252 padrão; cuidado com acentos em mensagens.
- `[[advpl-jobs-rpc]]` — PE rodando em job sem UI (não usar MsgInfo).
- `[[advpl-debugging]]` — diagnosticar "minha PE não disparou".
- `[[plugadvpl-index-usage]]` — `/plugadvpl:find function`, `/plugadvpl:callers`.

## Comandos plugadvpl relacionados

- `/plugadvpl:find function <PE>` — verifica se PE já existe e onde.
- `/plugadvpl:callers <PE>` — vê quem dispara (provável `ExecBlock` em fonte TOTVS).
- `/plugadvpl:arch <arq>` — entende rotina principal antes de criar PE.
- `/plugadvpl:grep "ExistBlock\|ExecBlock"` — encontra invocações no projeto.
- `/plugadvpl:lint <arq>` — checa `BP-003` (GetArea/RestArea), `SEC-002` (prefixo).
- Lookup `pontos_entrada_padrao` (carregado pelo init) — referência rápida com `paramixb_count` + `retorno_tipo`.

## Referência profunda

Para detalhes completos (~1.2k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Catálogo de ~280 PEs oficiais TOTVS por módulo com `paramixb_count` e tipo de retorno.
- Diferenças entre PE pré-validação, pós-validação e pré/pós gravação.
- Padrões para PE multi-propósito (bifurcado por contexto via `PARAMIXB[1]` — caso STRU).
- Como diagnosticar conflito de PE (mesma User Function compilada em RPOs diferentes).
- PEs especiais: `OPENMENU`, `CHKFIL`, `LOGAVISO`, `FATORM`, e gatilhos APWEBEX.

## Exemplos práticos

Veja a pasta [`exemplos/`](exemplos/) ao lado deste SKILL.md para fonte real ADVPL de produção:

- `A300STRU.prw` — PE bifurcado (MODELDEF + VIEWDEF) que adiciona grid filha ao cadastro CNTA300 com gatilhos em cascata e validação preservada.

## Sources

- [ExecBlock - Execução do ponto de entrada - TDN](https://tdn.totvs.com/pages/releaseview.action?pageId=6814883)
- [Executando ExecBlock e ExistBlock - Maratona AdvPL TL++ 156](https://terminaldeinformacao.com/2024/01/06/executando-uma-funcao-se-estiver-compilada-com-execblock-e-existblock-maratona-advpl-e-tl-156/)
- [O que é PARAMIXB? - Terminal de Informação](https://terminaldeinformacao.com/2021/07/21/o-que-e-paramixb/)
- [Utilização da função Execblock - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360020902352)
- [Pontos de entrada MVC MATA070 - Terminal de Informação](https://terminaldeinformacao.com/knowledgebase/ponto-de-entrada-mata070-mvc/)
- [Ponto de entrada MVC CRMA980 - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360000146128)
- [O que é Ponto de Entrada Protheus - Bynem](https://tecnologia.bynem.com.br/ponto-de-entrada-protheus/)
- [Lista PEs MVC - Terminal de Informação](https://terminaldeinformacao.com/2015/02/09/lista-de-pontos-de-entrada-em-mvc/)
- [Pontos de entrada do Faturamento - Código Expresso](https://codigoexpresso.com/2025/07/06/pontos-de-entrada-do-faturamento-protheus/)
