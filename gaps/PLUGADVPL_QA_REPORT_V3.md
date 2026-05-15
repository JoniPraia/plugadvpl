# Relatório QA — plugadvpl

**Versão original do relatório:** plugadvpl `0.3.14` (2026-05-14)
**Versão re-testada (1º ciclo):** plugadvpl `0.3.20` (2026-05-15)
**Versão re-testada (2º ciclo):** plugadvpl **`0.3.21`** (2026-05-15)
**Projeto-base:** `D:\Projetos\CLIENTE_X` (1.992 fontes ADVPL/TLPP indexados)
**Dicionário SX:** ingerido (`tabelas=11.264`, `campos=187.633`, `gatilhos=18.051`, `parametros=18.435`)

---

## ⭐ Resultado consolidado do reteste 0.3.14 → 0.3.21

| # | Bug | Severidade | Status (0.3.20) | Status (0.3.21) |
|---:|---|---|---|---|
| 1 | `CLAUDE.md` documenta flags antigas de `grep` | baixa | ❌ | ❌ **AINDA PENDENTE** (linha 30 continua com `--fts/--literal/--identifier`; init sem `--force-fragment`) |
| 2 | `--limit` global, posição não-óbvia | baixa | ✅ melhorado | ✅ (mensagem de erro com dica) |
| 3 | `impacto` substring sem boundary | **alta** | ✅ corrigido | ✅ |
| 4 | `gatilho` ignora destinos | **alta** | ✅ corrigido | ✅ |
| 5 | REST não vira `source_type=webservice` | média | ❌ | ✅ **CORRIGIDO no 0.3.21** (`MGFWSS21` agora `source_type=webservice`, `capabilities=["JSON_AWARE","WS-REST"]`) |
| 6 | PE canônico (ANCTB102GR) não detectado | **alta** | ✅ corrigido | ✅ |
| 7 | REST capabilities incompletas | baixa | ❌ | ✅ **CORRIGIDO no 0.3.21** (junto com #5; `WS-REST` agora presente) |
| 8 | `callees` quebrado | **crítica** | ✅ corrigido | ✅ |
| 9 | `lint` retorna duplicados | média | ✅ corrigido | ✅ |
| 10 | `pontos_entrada` heurística não-uniforme | média | ✅ corrigido | ✅ |
| 11 | `tabelas_*` vazias em ExecAuto | baixa | ✅ impl. | ✅ (`tabelas_via_execauto: True/False`) |
| 12 | `callers` mistura self-calls sem flag | baixa | ❌ | ✅ **CORRIGIDO no 0.3.21** (coluna nova `is_self_call: True/False` + coluna `funcao` agora populada com o chamador real, e.g. `XMC14Bloqu`, `XMC14Libe`) |
| 13 | `ingest-sx` sobrescreve `project_root` | média | ✅ corrigido | ✅ |
| 14 | `grupos_campo = 0` (sxg.csv quebrado) | — | ✅ diagnóstico | ✅ |
| 15 | Δ 12k linhas em `consultas` | média | ✅ corrigido | ✅ |

**Placar final:** **14 dos 15 corrigidos** (+1 melhorado). Apenas o **#1** continua pendente. Dos 4 bugs marcados originalmente como **alta** ou **crítica**, **todos os 4 foram resolvidos**.

### Detalhe das correções do ciclo 0.3.21 (em cima do 0.3.20)

`lookup_bundle_hash` não mudou entre 0.3.20 e 0.3.21 → confirma que **regras de lint/parsers de fonte continuam iguais**; as mudanças foram em **detecção de capabilities e na tabela `chamadas_funcao`**:

#### ✅ #5 + #7 — REST agora detectado
```
ANTES (0.3.20)
  source_type    : user_function
  capabilities   : ["JSON_AWARE"]

DEPOIS (0.3.21)
  source_type    : webservice
  capabilities   : ["JSON_AWARE", "WS-REST"]
```
Funcionou com `WSRESTFUL PortaldeViagem` no `MGFWSS21.PRW`.

#### ✅ #12 — Self-calls identificados
```
ANTES (0.3.20)
  callers MGFCOM14 → 6 entradas, coluna `funcao` VAZIA em todas

DEPOIS (0.3.21)
  callers MGFCOM14 → 6 entradas, com colunas novas:
    funcao        = "XMC14Bloqu" | "XMC14Libe" | "XMC14Rej" | "xOldProLote" | "xProLote"
    is_self_call  = True (todas as 6, neste caso)
```
A coluna `funcao` agora identifica QUEM dentro do arquivo está chamando, e `is_self_call` resolve o ruído documentado no relatório original — filtrar self vs externo passa a ser trivial. Não há flag `--external` explícita, mas a coluna torna isso desnecessário.

### Melhorias bônus encontradas durante o reteste

1. **`--version` / `version`** — flag global `-V` e subcomando `version` (antes só dava pra ler via `status`).
2. **Aviso "lookups mudaram, use `--no-incremental`"** — após bump de versão, o `ingest --incremental` avisa que regras novas não foram aplicadas em arquivos com mtime antigo. Evita falsos negativos silenciosos.
3. **Warnings detalhados de dedup no `ingest-sx`** — cada tabela SX mostra `linhas CSV → distintas após PK dedup` com a chave usada.
4. **Mais regras de lint**: `total_lint_findings` passou de **3.834 → 8.540** (+122%). Novas regras `SEC-005` (TOTVS-restritas tipo `ParamBox`), `PERF-004` (concat de string em loop), `BP-008` (shadowing de `aRotina`).
5. **`callees` formato novo** — `destino | tipo | linha | contexto` com classificação `method`/`user_func`/`execauto`/`fwloadmodel`/`fwexecview`.
6. **Schema migração 3→4 sem perdas** — preservou os 421k registros SX intactos.

### Único bug ainda em aberto

#### ❌ #1 — Fragment do `CLAUDE.md` desatualizado
A linha 30 do `CLAUDE.md` do projeto continua dizendo `(modos `--fts`/`--literal`/`--identifier`)`. A CLI usa `-m fts|literal|identifier`. **Sugestão:** o `ingest` deveria detectar fragment desatualizado (comparando versão gravada no fragment vs `runtime_version`) e oferecer atualização opt-in (`plugadvpl init --force-fragment`), ou no mínimo emitir warning no `status`.

---

## Documentação original do levantamento (referência)

> O texto a seguir descreve o estado em `0.3.14`. Os achados resolvidos estão sinalizados acima.

## Metodologia

Exercício de QA exploratório com **5 campos sortidos** e **7 fontes de tipos/módulos diferentes**, executando os comandos do plugin contra dados reais do cliente cliente real e cruzando com leitura manual dos `.prw` para identificar divergências.

### Amostra de campos (variedade de prefixo, tipo e ocorrência)

| Campo | Tabela | Módulo | Tipo | Característica |
|---|---|---|---|---|
| `A1_COD` | SA1 | Faturamento | C, chave | Campo comum, nome curto (prefixo de muitos outros) |
| `B1_DESC` | SB1 | Estoque | C, longa | Descrição usada em muitas regras de gatilho |
| `D2_QUANT` | SD2 | Faturamento | N | Numérico de detalhe NF |
| `E1_VENCTO` | SE1 | Financeiro | D | Data |
| `ZEG_CODCLA` | ZEG | Customizado cliente real | C(6) | Custom, nome único, baixa ocorrência |

### Amostra de fontes (tipos diferentes)

| Arquivo | Tipo esperado | Particularidade |
|---|---|---|
| `MGFTAC12.prw` | WSSERVICE SOAP | Customizado, 172 LOC |
| `MGFWSS21.PRW` | WSRESTFUL REST | Customizado, 174 LOC |
| `BRWFIS02.PRW` | MVC com ViewDef/MenuDef | 186 LOC |
| `IncPedExp.prw` | User Function / ExecAuto Caller | 422 LOC, chama `MsExecAuto` |
| `mat10.PRW` | TReport (impressão) | Standard Protheus, 3.309 LOC |
| `ANCTB102GR.prw` | Ponto de Entrada (PE) | 33 LOC, assinatura PARAMIXB, nome canônico |
| `MGFCOM14.prw` | MVC + PE + ExecAuto + RPC + Dialog | 4.286 LOC, customização cliente real pesada |

---

## Bugs / inconsistências encontrados

A numeração reflete a ordem em que cada problema apareceu; **a criticidade está marcada em cada seção**.

### #1 — `CLAUDE.md` documenta flags inexistentes de `grep` *(documentação obsoleta)*

**Severidade:** baixa (UX/documentação)
**Evidência:**
- O `CLAUDE.md` do projeto (linha sobre `plugadvpl grep`) diz: *"modos `--fts`/`--literal`/`--identifier`"*.
- A CLI atual aceita `-m fts|literal|identifier` (`--mode`). Usar `--identifier` resulta em `No such option: --identifier`.

**Reprodução:**
```powershell
plugadvpl grep 'WSRESTFUL' --identifier   # ❌ erro
plugadvpl grep 'WSRESTFUL' -m identifier  # ✅ funciona
```

**Recomendação:** atualizar o fragment do `CLAUDE.md` (provavelmente gerado em `plugadvpl init` em versão anterior) na próxima execução de `init`/`ingest` para refletir `-m {fts|literal|identifier}`.

---

### #2 — `--limit` é flag global, posição não-óbvia *(UX)*

**Severidade:** baixa
**Evidência:** rodar `plugadvpl impacto A1_COD --limit 20` dá `No such option: --limit`. O flag existe, mas precisa vir **antes** do subcomando: `plugadvpl --limit 20 impacto A1_COD`. O `--help` do `impacto` não cita.

**Recomendação:** ou aceitar `--limit` também no subcomando, ou documentar nos `--help` dos subcomandos que aceita `--limit` global, ou adicionar dica no erro ("did you mean `plugadvpl --limit N impacto …`?").

---

### #3 — `impacto` busca por substring sem boundary, gera **falsos positivos massivos** em nomes curtos/comuns *(crítico para usabilidade)*

**Severidade:** alta
**Evidência:** `plugadvpl impacto A1_COD` retornou **>100 KB de output**, com gatilhos de campos cujo nome apenas *contém* "A1_COD" como substring:

| Resultado mostrado | Origem do match (substring de "A1_COD") |
|---|---|
| `BA1_CODEMP#001 -> ...` (regra `BA1->BA1_CODEMP`) | `B`**`A1_COD`**`EMP` |
| `BA1_CODINT#001 -> ...` | `B`**`A1_COD`**`INT` |
| `BA1_CODPLA`, `BA1_CODMUN` | idem |
| `DA1_CODPRO#002 -> DA1_GRUPO` | `D`**`A1_COD`**`PRO` |
| `A1_CODSEG`, `A1_CODSIAF`, `A1_COD_MUN`, `A1_SUBCOD` | prefixo/sufixo na própria SA1 |
| `BJF_MATRIC#005 -> BJF_CODMUN` (regra `BA1->BA1_CODMUN`) | `B`**`A1_COD`**`MUN` |

Para campos com nome único (`ZEG_CODCLA`) o comando retorna 3 resultados precisos. Para campos como `A1_COD`, fica praticamente inutilizável.

**Comparativo do mesmo comando em campos da amostra:**

| Campo | Total resultados | % aproximada de match legítimo |
|---|---:|---:|
| `A1_COD` | >150 | ~5% (massa de `B*A1_COD*…`, `D*A1_COD*…`) |
| `B1_DESC` | 153 | ~100% (gatilhos legítimos usando `SB1->B1_DESC`) |
| `D2_QUANT` | 53 | ~100% |
| `E1_VENCTO` | 50+ | ~100% |
| `ZEG_CODCLA` | 3 | 100% |

**Causa-raiz provável:** o SQL do `impacto` usa `LIKE '%A1_COD%'` (ou `INSTR`) em campos textuais como `sx7.regra`, `sx7.cond`, `sx3.valid`, sem **regex boundary** (`\bA1_COD\b`). Campos de outras tabelas cuja regra referencia `SA1->A1_COD` viram match correto; campos cujo *nome* contém literalmente `A1_COD` como substring viram match espúrio.

**Recomendação:**
- Em SQLite isso é resolvível com regex (`REGEXP` extension) ou validação Python pós-query.
- Alternativa pragmática: separar busca em dois passos — match exato no nome do campo (`sx3.campo = 'A1_COD'`) + busca em regras com padrão `\bA1_COD\b`.

---

### #4 — `gatilho` ignora gatilhos *destinados* ao campo *(bug funcional + doc divergente)*

**Severidade:** alta
**Evidência:**
- Help diz: *"Lista cadeia de gatilhos SX7 **originados/destinados** ao campo."*
- `plugadvpl gatilho A1_COD` → `(sem resultados)`.
- `plugadvpl gatilho A1_SUBCOD` → retorna `A1_SUBCOD#001 -> A1_COD | regra=GSPFNVCOD1("SA1","A1_COD",1,...)`.

A relação `A1_SUBCOD → A1_COD` existe e é *destinada* a `A1_COD`, mas é invisível pelo comando ao consultar pelo destino. Para um campo que **só recebe gatilhos** (cenário comum em chaves geradas), o usuário acredita não haver gatilho algum.

**Recomendação:** ou corrigir a query (`WHERE origem = ? OR destino = ?`), ou ajustar o help para "originados ao campo" se a omissão for proposital — mas o ideal é a primeira.

---

### #5 — WS REST não é classificado como `webservice` *(parser/heurística)*

**Severidade:** média
**Evidência:**

| Arquivo | Construct | `source_type` retornado | `capabilities` |
|---|---|---|---|
| `MGFTAC12.prw` | `WSSERVICE MGFTAC12` (SOAP) | `webservice` ✓ | `["MULTI_FILIAL","WS-SOAP"]` ✓ |
| `MGFWSS21.PRW` | `WSRESTFUL PortaldeViagem` (REST) | `user_function` ❌ | `["JSON_AWARE"]` (faltando `WS-REST`) |
| `MGFWSS23.PRW` | `WSRESTFUL MercadoExternoAPI` (REST) | `user_function` ❌ | idem |
| `MGFWSS37.PRW` | `WSRESTFUL IntegracaoBooking` | `user_function` ❌ | idem |

O parser reconhece `WSSERVICE` mas não `WSRESTFUL` para definir `source_type`. Consequência: filtros/relatórios futuros baseados em "todos os webservices" perderão silenciosamente os REST endpoints.

**Recomendação:** adicionar regra de detecção `WSRESTFUL <nome>` → `source_type='webservice'` + capability `'WS-REST'`.

---

### #6 — Ponto de Entrada canônico não detectado *(parser/heurística)*

**Severidade:** alta
**Evidência:** `ANCTB102GR.prw`:
- Cabeçalho literal: *"O **ponto de entrada** ANCTB102GR utilizado Antes a gravação dos dados da tabela de lançamento."*
- Nome `ANCTB102GR` é PE canônico documentado em TDN da TOTVS (`http://tdn.totvs.com/display/public/mp/ANCTB102GR`).
- Assinatura clássica: `PARAMIXB[1]..[5]`.

Mas o `arch` retorna:
```
source_type    : user_function
capabilities   : []
pontos_entrada : []
```

**Paradoxalmente**, em `MGFCOM14.prw` o plugin **detecta** PEs custom pelo prefixo `XMC14*` (não-canônicos), mas falha no padrão canônico Protheus.

**Recomendação:** complementar a heurística atual com:
1. Match contra lista de PEs nativos do Protheus (`MT100GRV`, `ANCTB102GR`, etc.) — lista pública pode vir do TDN.
2. Detecção por uso de `PARAMIXB` no corpo (campo necessário mas não suficiente).
3. Padrão de nome `<MODULO><função><posicao>` (e.g., `MT*GRV`, `*ANTES`, `*DEPOIS`).

---

### #7 — Capabilities incompletas no parser de REST *(parser)*

**Severidade:** baixa
**Evidência:** `MGFWSS21.PRW` `capabilities=["JSON_AWARE"]`. Mas o fonte:
- Usa `xFilial(...)` implicitamente em `ZH3->`?  (não confirmado, mas a tabela ZH3 com `tabelas_reclock` indica filial)
- É REST (deveria ter `WS-REST`)
- Lida com JSON (`JSON_AWARE` ✓)

Apenas uma capability marcada, omitindo `WS-REST`. Ver também #5.

---

### #8 — **`callees` completamente quebrado neste índice** *(bug crítico)*

**Severidade:** crítica
**Evidência:**

```text
plugadvpl callers MFCONOUT
→ 2.495 resultados (CN300PCMT, M4601DUP, M460FIL, M460FIM, …)

plugadvpl callees MFCONOUT
→ (sem resultados)

plugadvpl callees MGFWSS21         → vazio
plugadvpl callees U_MGFWSS21       → vazio
plugadvpl callees A094Commit       → vazio
plugadvpl callees MGFCOM14         → vazio
plugadvpl callees MGFTAC12         → vazio
```

**Causa-raiz observada:** na saída de `callers`, a coluna `funcao` (que deveria conter o nome da função *chamadora* dentro do `arquivo`) está **vazia em todos os 2.495+ registros retornados**:

```
arquivo: M460FIM.PRW   funcao: (vazio)   linha: 39   tipo: user_func
```

O índice gravou **onde** está cada chamada (arquivo + linha + tipo + snippet), mas **não associou** a chamada à função que a contém. Como `callees X` filtra `WHERE funcao = X` (origem), e a coluna está vazia em todos os 30.946 registros, **nenhum `callees` consegue retornar nada**.

**Impacto prático:** uma das features anunciadas do plugin ("call graph") está parcialmente quebrada. `callers` funciona porque consulta a coluna *destino* (a função chamada, preenchida). `callees` está inutilizado.

**Recomendação:** revisar o passo de ingest de chamadas (`plugadvpl ingest`) para popular `chamadas_funcao.funcao` (ou nome equivalente) com a função-pai do callsite. Sem isso, qualquer análise direcional de quem-chama-quem fica unidirecional.

---

### #9 — `lint` retorna findings duplicados *(parser/lint)*

**Severidade:** média
**Evidência:** `plugadvpl lint MGFWSS21.PRW --severity critical`:

```text
MGFWSS21.PRW | centrodecusto | 89 | BP-001 | critical | ZH3->(RecLock("ZH3",.t.)) | Adicione MsUnlock()...
MGFWSS21.PRW | centrodecusto | 89 | BP-001 | critical | ZH3->(RecLock("ZH3",.t.)) | Adicione MsUnlock()...
```

A **mesma linha, mesma regra, mesma severidade** aparece duas vezes. Pode ser:
- Regra executada duas vezes durante ingest.
- Falta de UNIQUE constraint em `lint_findings` por `(arquivo, linha, regra_id)`.

Possivelmente relacionado às discrepâncias de contagem entre `ingest summary` e `sx-status` (vide #15 abaixo).

**Recomendação:** adicionar UNIQUE/dedup ao final do ingest.

---

### #10 — `pontos_entrada` heurística não-uniforme *(parser/UX)*

**Severidade:** média
**Evidência:**
- `MGFCOM14.prw` → `pontos_entrada=["XMC14Bloqu","XMC14Libe","XMC14Rej","xC14BLot","xC14LLot","xC14RLot","xMC14Atu","xMC14CCAP","xMC14CTit","xMC14Ref"]` — detectados pelo prefixo X custom da cliente real.
- `ANCTB102GR.prw` → `pontos_entrada=[]` — PE canônico Protheus não detectado.

Critério atual privilegia padrão custom do cliente e ignora padrão da plataforma. Ver também #6.

---

### #11 — `tabelas_*` ficam vazias em programas que usam ExecAuto *(limitação)*

**Severidade:** baixa (limitação conhecida do parser estático)
**Evidência:** `IncPedExp.prw` (422 LOC, capability `EXEC_AUTO_CALLER`) → `tabelas_read=[]`, `tabelas_write=[]`, `tabelas_reclock=[]`. Mas o programa monta `aCab/aIt` para `MSExecAuto("MATA460", ...)` que claramente toca SC5/SC6/SF4/etc.

Não é bug formal — análise estática sem expansão de `MsExecAuto` é uma limitação aceitável. Mas pode levar o usuário a conclusões erradas se confiar só nas `tabelas_*` do `arch`.

**Recomendação:** marcar com flag clara, e.g., `tabelas_via_execauto=true` quando `EXEC_AUTO_CALLER` está set, para sinalizar que a lista pode estar incompleta. Ou adicionar comando dedicado `plugadvpl execauto <arq>` que extrai a rotina chamada do primeiro argumento.

---

### #12 — `callers` mistura self-calls com calls externos sem distinção *(UX)*

**Severidade:** baixa
**Evidência:** `plugadvpl callers MGFCOM14` retornou 6 callsites, **todos dentro do próprio `MGFCOM14.prw`**:
```
MGFCOM14.prw | linha 1876 | fwexecview  | FWExecView("Bloquear", "MGFCOM14", ...)
MGFCOM14.prw | linha 1947 | fwloadmodel | oModel := FwLoadModel('MGFCOM14')
...
```

São chamadas legítimas (a rotina chama a si mesma via FwLoadModel/FWExecView), mas o usuário tipicamente espera ver "quem **chama de fora**". Sem filtro `--exclude-self` ou agrupamento por `arquivo_origem != arquivo_destino`, fica ambíguo.

**Recomendação:** adicionar coluna `is_self_call` ou flag `--external` no `callers`.

---

### #13 — `ingest-sx` parece sobrescrever `project_root` no DB *(bug funcional)*

**Severidade:** média (já contornável)
**Evidência (sessão anterior):** após rodar `plugadvpl ingest-sx D:\Projetos\CLIENTE_X\CSV`, o campo `project_root` no `status` mudou de `D:\Projetos\CLIENTE_X` para `D:\Projetos\CLIENTE_X\CSV` (que é o `sx_csv_dir`). Os DBs físicos permaneceram no lugar certo (raiz do projeto). Um `plugadvpl ingest --incremental` posterior reescreveu `project_root` corretamente.

**Hipótese:** `ingest-sx` está escrevendo no slot errado da tabela `meta` (sobrescrevendo `project_root` em vez de gravar só `sx_csv_dir`).

**Recomendação:** auditar o INSERT/UPDATE em `meta` no ingest-sx para garantir que só os campos SX sejam tocados.

---

### #14 — `grupos_campo = 0` após `ingest-sx` *(NÃO é bug do plugin)*

**Severidade:** N/A
**Evidência:** `sx-status` retorna `grupos_campo=0`. O usuário confirmou que o `sxg.csv` exportado pelo Configurador deste ambiente está vazio/quebrado na origem. Mantido no relatório só para registro: se outro projeto reportar o mesmo, vale checar a origem antes de suspeitar do plugin.

---

### #15 — Discrepância entre `ingest summary` e `sx-status` para `consultas` *(não investigado a fundo)*

**Severidade:** média
**Evidência (sessão anterior):**

| Tabela SX | Linhas reportadas pelo `ingest-sx` (summary) | Linhas em `sx-status` | Δ |
|---|---:|---:|---:|
| `perguntas` | 59.498 | 59.485 | −13 |
| `relacionamentos` | 26.251 | 25.930 | −321 |
| `pastas` | 1.918 | 1.833 | −85 |
| **`consultas`** | **58.796** | **46.669** | **−12.127** |

~12 mil linhas "somem" entre o processamento e o estado final do banco. Hipótese: `ON CONFLICT REPLACE` deduplicando linhas com mesma chave. Não confirmado — exigiria abrir o SQLite e contar manualmente. Pode estar relacionado a #9 (duplicação não-deduplicada em `lint_findings` apontaria que `lint` não tem dedup, então **falta de dedup é um padrão consistente**; ou então é o oposto — dedup excessivo no SXB).

**Recomendação:** documentar o comportamento esperado (deduplica ou não? por qual chave?) e tornar o summary do ingest coerente com o estado pós-commit.

---

## Resumo executivo

| # | Achado | Severidade | Tipo |
|---:|---|---|---|
| 1 | `CLAUDE.md` documenta flags antigas de `grep` | baixa | doc |
| 2 | `--limit` global, posição não-óbvia | baixa | UX |
| 3 | `impacto` faz substring sem boundary | **alta** | bug funcional |
| 4 | `gatilho` ignora destinos (help mente) | **alta** | bug funcional |
| 5 | WS REST não vira `source_type=webservice` | média | parser |
| 6 | PE canônico (ANCTB102GR) não detectado | **alta** | parser/heurística |
| 7 | REST com capabilities incompletas | baixa | parser |
| 8 | **`callees` totalmente quebrado** | **crítica** | bug funcional |
| 9 | `lint` retorna duplicados | média | parser/lint |
| 10 | `pontos_entrada` heurística não-uniforme | média | parser |
| 11 | `tabelas_*` vazias em ExecAuto | baixa | limitação |
| 12 | `callers` mistura self-calls sem flag | baixa | UX |
| 13 | `ingest-sx` sobrescreve `project_root` | média | bug funcional |
| 14 | `grupos_campo=0` | — | não é bug do plugin |
| 15 | Δ 12k linhas em `consultas` (summary vs estado final) | média | parser/UX |

### Top-3 a priorizar

1. **#8 — `callees` quebrado**: usuário acredita ter call graph; metade dele não funciona. Provavelmente um campo do parser não está sendo populado.
2. **#3 — `impacto` com substring noise**: torna o comando praticamente inútil para campos de tabelas standard (SA1, SB1, SC5…). Boundary regex resolve.
3. **#6 + #10 — Heurística de PE**: complementar com lista canônica + detecção por `PARAMIXB` resolveria a maior parte.

### O que funcionou bem (importante registrar)

- `find`, `arch`, `lint` (com filtros), `callers`, `tables`, `param` retornaram resultados corretos e úteis.
- `impacto` em campos de nome único (ZEG_*, etc.) funciona perfeitamente.
- Migração de schema 3→4 preservou todos os dados SX (421k registros).
- Detecção de staleness entre `runtime_version` e `plugadvpl_version` (com hint do comando correto) é UX excelente — economiza tempo a cada upgrade.
- Ingest dos 11 CSVs SX em 18s para 421k registros (sem erros de encoding em CP1252).
