---
description: Validações ADVPL embarcadas no dicionário SX (X3_VALID, X3_INIT, X3_WHEN, X3_VLDUSER, X7_REGRA, X1_VALID). Use ao analisar customização de cadastro/dicionário ou rastrear impacto de mudança de campo via `plugadvpl impacto`.
---

# advpl-dicionario-sx-validacoes — Validações embutidas no dicionário SX

Esta skill foca nas **expressões ADVPL embarcadas no dicionário SX** — o ponto onde código vive **fora** dos `.prw` e quase ninguém audita. Mexer num campo SX3 sem entender o que está em `X3_VALID`/`X3_WHEN`/`X3_RELACAO`/`X7_REGRA` é a causa #1 de regressão silenciosa em customização Protheus.

> Para a **estrutura completa** das tabelas SX (cada coluna documentada),
> consulte a skill irmã [`advpl-dicionario-sx`](../advpl-dicionario-sx/SKILL.md)
> e seu [`reference.md`](../advpl-dicionario-sx/reference.md). Esta skill é só
> sobre as expressões ADVPL embutidas.

## Quando usar

- Vai **alterar** um campo (X3_TIPO, X3_TAMANHO, remover...) e quer saber o impacto.
- Vai **criar** validação custom (`X3_VALID`, `X3_VLDUSER`) e quer não cair em armadilha clássica.
- Está **debugando** comportamento "fantasma" — campo não habilita, gatilho não dispara, pergunta retorna vazio.
- Quer **auditar** que customizações mexem em validações vs. que poderiam ser puro UI.
- Vai rodar `/plugadvpl:lint --cross-file` (regras SX-001..SX-011) e quer entender as regras com profundidade.

## Mapa: onde mora ADVPL dentro do SX

| Coluna SX            | O que contém                                | Quando executa                              |
|----------------------|---------------------------------------------|---------------------------------------------|
| `X3_VALID`           | Expressão de validação do campo             | Após `Loose Focus` no campo                 |
| `X3_VLDUSER`         | Validação user-defined (executa após VALID) | Após `X3_VALID` retornar `.T.`              |
| `X3_WHEN`            | Habilitação condicional do campo            | A cada repaint da tela                      |
| `X3_RELACAO`         | Inicializador / fórmula (default + virtual) | Inserção de novo registro / cálculo VIRTUAL |
| `X3_CBOX`            | Conteúdo de combobox                        | Build da combo                              |
| `X3_F3`              | Alias da consulta SXB (não é ADVPL puro)    | F3 no campo                                 |
| `X7_REGRA`           | Expressão que retorna valor para destino    | Após sair do campo origem                   |
| `X7_CONDIC`          | Condição para o gatilho disparar            | Antes de avaliar X7_REGRA                   |
| `X7_CHAVE`           | Chave do DbSeek (se X7_SEEK='S')            | Setup do gatilho com seek                   |
| `X1_VALID`           | Validação da pergunta SX1                   | OK no diálogo `Pergunte`                    |
| `X1_DEF01`/`CNT01`   | Default de cada conteúdo da pergunta        | Abertura do diálogo                         |
| `X6_VALID`           | Validação ao gravar parâmetro MV_           | `PutMV` / Configurador                      |
| `X6_INIT`            | Default do parâmetro                        | `GetMV` quando vazio                        |

## X3_VALID — Validação de campo

A expressão deve **retornar `.T.`** (válido) ou **`.F.`** (inválido). Quando inválido, o ERP exibe o último `Help()`/`MsgInfo()` chamado dentro da expressão.

### Pattern canonical

```advpl
// X3_VALID (uma única linha — sem quebras dentro do dicionário!)
NaoVazio(M->A1_COD) .And. ExistChav("SA1") .And. U_MGFA1Val()
```

- `M->CAMPO` referencia o **valor sendo digitado** (memo da grid).
- `NaoVazio(x)` e `Vazio(x)` testam null/empty.
- `ExistCpo(alias, conteudo, ordem)` valida se existe na tabela apontada.
- `ExistChav(alias)` valida se a chave **NÃO** existe (para inserção sem duplicidade).
- `U_MGFA1Val()` chama validação custom em fonte ADVPL (recomendado para qualquer regra >1 linha).

### Anti-padrões clássicos

- **SQL embarcado** (`BeginSql .. EndSql`, `TCQuery(..)`) dentro de `X3_VALID` — executa em **cada Loose Focus**, custa caro. Use `Posicione()` com cache ou lookup simples.
- **Função restrita TOTVS** — quebra em update do ERP. `plugadvpl lint --cross-file --regra SX-007` detecta.
- **`U_xxx` sem fonte indexado** — runtime estoura. `plugadvpl lint --cross-file --regra SX-001`.
- **Side effects** em VALID (gravar log, enviar e-mail). VALID pode ser chamada várias vezes por digitação — torna comportamento imprevisível.

## X3_INIT (X3_RELACAO) — Inicializador

Duas funções:

1. **Default** ao inserir novo registro (campo Real `X3_CONTEXT='R'`).
2. **Cálculo** em campo Virtual (`X3_CONTEXT='V'`) — recalcula a cada paint.

```advpl
// Default cliente "padrão"
"000001"

// Default a partir de função
U_MGFFatPad()

// Virtual: soma de itens
GetAdvFVal("SC6", "C6_TOTAL", xFilial("SC6")+SC5->C5_NUM, 1, 0)
```

### Anti-padrões

- **Campo obrigatório** (`X3_OBRIGAT='X'`) com INIT vazio (`""`, `Space(N)`, `0`) — usuário sempre vai precisar redigitar. `plugadvpl lint --cross-file --regra SX-009`.
- **INIT lento em VIRTUAL** — recalcula a cada paint. Cache em variável Static ou use `MemoLine()`.

## X3_WHEN — Habilitação condicional

Retorna `.T.` (habilita) ou `.F.` (cinza). Avaliada **a cada repaint**.

```advpl
// Habilita campo só para clientes pessoa jurídica
M->A1_PESSOA == "J"

// Habilita só após cliente preencher CNPJ
!Vazio(M->A1_CGC)

// Habilita conforme parâmetro MV_*
GetMV("MV_XYZUSA", .F., .F.)
```

### Cuidados

- Mesmas armadilhas de `X3_VALID`: nada de SQL pesado, nada de side effects.
- WHEN === `.F.` em campo obrigatório com INIT vazio = registro impossível de gravar. Audite o trio (OBRIGAT, INIT, WHEN) junto.

## X3_VLDUSER — Validação adicional do usuário

Roda **depois** de `X3_VALID` retornar `.T.`. Convenção: usar para customização sem alterar o VALID padrão TOTVS.

```advpl
// Apenas o cliente VLDUSER (preserva X3_VALID = "ExistCpo('SA1') .And. ...")
U_MGFA1ValExtra()
```

> **Boa prática**: clientes devem usar `X3_VLDUSER` para customização e **não** alterar `X3_VALID` — evita conflito em update.

## X7_REGRA — Gatilho (Trigger)

Após terminar edição do campo origem (`X7_CAMPO`), o ERP avalia `X7_REGRA` e atribui o resultado a `X7_CDOMIN`.

### Padrões de uso

```advpl
// Tipo 1: Primário (P) — avalia direto
X7_TIPO  = P
X7_CAMPO = A1_COD
X7_REGRA = M->A1_COD + " - default"
X7_CDOMIN= A1_NREDUZ

// Tipo 2: Pesquisar (P com SEEK) — DbSeek + retorno
X7_TIPO  = P
X7_CAMPO = A1_COD
X7_SEEK  = S
X7_ALIAS = SA1
X7_ORDEM = 1
X7_CHAVE = xFilial("SA1") + M->A1_COD
X7_REGRA = SA1->A1_NREDUZ
X7_CDOMIN= A1_NREDUZ
```

### Anti-padrões

- **`X7_TIPO='P'` (Pesquisar) sem `X7_SEEK='S'`** — lookup falha silenciosamente. Detector: `SX-010`.
- **Destino inexistente em SX3** — gatilho some sem warning. Detector: `SX-002`.
- **`X7_REGRA` complexa de várias linhas** — impossível debugar. Sempre use `U_xxx`.
- **Ciclo de gatilhos** — A1_COD dispara A1_NOME que dispara A1_TEL que dispara... `plugadvpl gatilho A1_COD --depth 3` mostra a cadeia.

## X1_VALID — Validação de pergunta

Mesma semântica de `X3_VALID` mas no contexto de `Pergunte()`. A variável é a `MV_PARxx`.

```advpl
// Pergunta de "Empresa De"
X1_VARIAVL = mv_ch1
X1_VALID   = ExistCpo("SM0", MV_PAR01)
X1_DEF01   = "01"
```

## X6_VALID / X6_INIT — Parâmetros

```advpl
// Validação ao gravar parâmetro
X6_VALID = NaoVazio() .And. (Type("X6_CONTEUD") $ "CN")

// Default quando GetMV não acha registro
X6_INIT = "01"
```

## Como o `plugadvpl impacto` cruza tudo isso

```
$ plugadvpl impacto A1_COD --depth 2

Tipo  | Local                          | Contexto                                   | Severidade
------|--------------------------------|--------------------------------------------|------------
SX7   | A1_COD#01 → A1_NREDUZ          | depth=1 tipo=P regra=SA1->A1_NREDUZ        | critical
SX7   | A1_NREDUZ#01 → A1_INSCR        | depth=2 tipo=P                             | critical
SX3   | SA1.A1_COD                     | C(6) Codigo do Cliente                     | warning
SX3   | SA2.A2_REFCLI                  | VLDUSER=ExistCpo("SA1",M->A2_REFCLI,1)     | warning
fonte | MGFA1V01.prw:42::U_MGFA1V01    | Local cCod := M->A1_COD                    | warning
fonte | FATA050.prw:128::FATA050       | RecLock("SA1", .T.) ; Replace A1_COD With  | critical
SX1   | MTCRDIV#02                     | Cliente De: ExistCpo("SA1",MV_PAR02)       | warning
```

A query interna faz JOIN/LIKE em `campos.validacao`, `campos.vlduser`,
`campos.when_expr`, `campos.inicializador`, `gatilhos.regra`, `gatilhos.condicao`,
`perguntas.validacao`, `perguntas.conteudo_padrao`, e em `fonte_chunks.content`.

## Comandos plugadvpl relacionados

- `plugadvpl ingest-sx <pasta-csv>` — popula o dicionário SX no índice.
- `plugadvpl impacto A1_COD [--depth 1..3]` — cruza fontes ↔ SX.
- `plugadvpl gatilho A1_COD [--depth 1..3]` — cadeia SX7 origem → destino.
- `plugadvpl lint --cross-file` — recalcula as 11 regras SX-001..SX-011.
- `plugadvpl lint --regra SX-007 --severity critical` — só funções restritas em VALID.
- `plugadvpl sx-status` — counts por tabela SX.

## Workflow recomendado para "vou alterar A1_COD"

1. `plugadvpl impacto A1_COD --depth 3` — vê tudo que mexe.
2. Para cada gatilho destino, `plugadvpl gatilho <destino>` — fecha cadeia.
3. Para cada `U_xxx` em VALID/INIT/REGRA, `plugadvpl find <U_xxx>` + `arch`.
4. Para cada SX1/MV_, `plugadvpl param <MV_x>` / `plugadvpl find Pergunte`.
5. **Depois** edita.

## Anti-padrões consolidados (cross-cutting)

- **SQL embarcado** em `X3_VALID` / `X3_VLDUSER` / `X3_WHEN` — executa a cada Loose Focus. Lint `SX-006` warning. Use `Posicione`/`ExistCpo`.
- **Função restrita TOTVS** em `X3_VALID` — `SX-007` critical, quebra em update do ERP.
- **`U_xxx` chamada em VALID/INIT/REGRA sem fonte indexado** — `SX-001` warning.
- **Side effects em VALID/WHEN** (gravar log, enviar e-mail, mudar variável global) — função roda múltiplas vezes por digitação, torna comportamento imprevisível.
- **Campo obrigatório com INIT vazio** — `SX-009` warning. Usuário sempre redigita.
- **Gatilho com `X7_TIPO='P'` sem `X7_SEEK='S'`** — `SX-010` error.
- **Gatilho com destino inexistente em SX3** — `SX-002` error.
- **`X3_F3` apontando para SXB inexistente** — `SX-011` error.
- **Tabela compartilhada (`X2_MODO='C'`) com `xFilial` em `X3_VALID`** — `SX-008` warning.
- **Cliente altera `X3_VALID` padrão TOTVS** — conflita em update. Use `X3_VLDUSER` separado.
- **Ciclo de gatilhos** — A→B, B→C, C→A. `/plugadvpl:gatilho A --depth 3` detecta.

## Cross-references com outras skills

- `[[advpl-dicionario-sx]]` — estrutura completa das tabelas SX (irmã desta skill).
- `[[advpl-code-review]]` — regras lint SX-001..SX-011 cross-file.
- `[[advpl-fundamentals]]` — `M->` notação (memo), `U_xxx` User Function, prefixo cliente.
- `[[advpl-embedded-sql]]` — `BeginSql` em VALID é anti-pattern SX-006.
- `[[advpl-mvc]]` — `FWFormStruct(1)` carrega X3_VALID/INIT/WHEN do dicionário.
- `[[advpl-mvc-avancado]]` — `SetErrorMessage` em vez de Help dentro de VALID custom.
- `[[advpl-pontos-entrada]]` — `<rotina>VLD` PE oferece validação fora do dicionário.
- `[[advpl-debugging]]` — "campo não aparece" / "gatilho não dispara" workflow.
- `[[plugadvpl-index-usage]]` — `/plugadvpl:impacto`, `/plugadvpl:gatilho`.

## Sources

- [Dicionário de Dados SX - TDN](https://tdn.totvs.com/display/public/framework/Dicionario+de+Dados+SX)
- [X3_VALID Boas práticas - TOTVS Central](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360018402211)
- [Gatilhos SX7 - Tudo em AdvPL](https://siga0984.wordpress.com/tag/sx7/)
- [SX1 Perguntas - Terminal de Informação](https://terminaldeinformacao.com/2017/10/10/funcao-para-criar-grupo-de-perguntas-sx1-protheus-12/)
- [Validações MVC e VLDUSER - Maratona AdvPL 019](https://terminaldeinformacao.com/2016/09/08/vd-advpl-019/)
