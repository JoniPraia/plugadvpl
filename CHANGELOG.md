# Changelog

Todas as mudanças notáveis estão documentadas aqui, seguindo [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/).

## [Unreleased]

## [0.4.2] - 2026-05-15

### 🎉 Universo 3 — fechamento (Feature C: Protheus.doc agregada)

**Última feature do Universo 3 (Rastreabilidade).** Indexa blocos
`/*/{Protheus.doc} ... /*/` com 16 tags canônicas TOTVS, agrega por
módulo/autor/tipo/deprecation, e oferece modo `--show <funcao>` que renderiza
doc completo em Markdown estruturado — agente IA copia direto pro contexto
sem abrir o fonte.

**Universo 3 completo:**
- ✅ **A (v0.4.0)** — execução não-direta (workflow/schedule/job/mail)
- ✅ **B (v0.4.1)** — chamada indireta (ExecAuto chain → tabelas)
- ✅ **C (v0.4.2)** — documentação inline (Protheus.doc)

### Added
- **Detector `parsing/protheus_doc.py`** — `extract_protheus_docs(content,
  arquivo=...)` extrai blocos completos com 16 tags estruturadas:
  - Single: `@type`, `@author`, `@since`, `@version`, `@description`,
    `@language`, `@deprecated` (+ reason)
  - Multi: `@param` (name+type+desc+optional), `@return` (type+desc),
    `@example`/`@sample`, `@history` (date+user+desc), `@see`, `@table`,
    `@todo`, `@obs`, `@link`
  - Tags fora do whitelist vão pro `raw_tags` catch-all (zero perda)
- **Tabela `protheus_docs`** (schema v6→v7, migration 007) — 26 colunas:
  6 quentes estruturadas (module/author/tipo/since/deprecated/funcao),
  10 JSON arrays pra multi-valor, `raw_tags_json` catch-all. 5 índices.
- **Inferência de módulo** — algoritmo dual:
  1. Path-based: regex `SIGA\w{3,4}` no caminho relativo
  2. Routine-prefix: reaproveita catálogo da Feature B (`MATA*` → SIGAFAT)
     com exact match prioritário e fallback alfabético determinístico
  3. Fallback: `null` (sem invenção)
- **Comando `plugadvpl docs [modulo]`** com 3 modos + 5 filtros:
  - **Lista**: `docs SIGAFAT` ou `docs --author X --deprecated`
  - **Show**: `docs --show MT460FIM` → Markdown estruturado (cabeçalho +
    tabela params + sections retorno/exemplos/histórico)
  - **Orphans**: `docs --orphans` → cross-ref BP-007 do lint (funções sem header)
  - Filtros: `--author` (LIKE), `--funcao` (exact), `--arquivo`,
    `--deprecated/--no-deprecated`, `--tipo`
- **Skill `/plugadvpl:docs`** — documentação completa com 6 casos de uso.
- **Counter** `protheus_docs` no contador de ingest + meta `total_protheus_docs`.

### Tests
- **28 testes unit** (`tests/unit/test_protheus_doc.py`):
  TestBlockParsing (5), TestTagExtraction (8), TestModuleInference (6),
  TestEdgeCases (6), TestFunctionResolution (3).
- **8 testes integration** (`tests/integration/test_cli.py::TestDocs`):
  fixture com 3 fontes (doc completo SIGAFAT, deprecated, órfão); cobre
  todos os modos + filtros + sanity DB.
- **470 testes verde** (era 442).

### Migration
- **Schema 6 → 7** (não-breaking; só adiciona tabela).

### Padrão TOTVS
- Spec oficial: [tds-vscode/docs/protheus-doc.md](https://github.com/totvs/tds-vscode/blob/master/docs/protheus-doc.md)
- Reaproveita o catálogo `execauto_routines.json` da Feature B pra inferência
  de módulo via prefixo de rotina (MATA*/FINA*/CTBA*/EECAP*/TMSA* → módulo).

### Casos de uso
1. *"Catálogo do módulo Faturamento"* → `/plugadvpl:docs SIGAFAT`
2. *"Quem escreveu o quê?"* → `/plugadvpl:docs --author "Fernando"`
3. *"O que está deprecated?"* → `/plugadvpl:docs --deprecated`
4. *"Doc completa sem abrir o fonte"* → `/plugadvpl:docs --show MT460FIM`
5. *"Cobertura de documentação"* → `/plugadvpl:docs --orphans`

### Notes
- **Spec aprovado** em `docs/universo3/C-protheus-doc.md` antes do código.
- **Fechamento Universo 3**: A (workflow) + B (execauto) + C (docs) entregues
  em 3 dot-releases consecutivos (v0.4.0 → v0.4.1 → v0.4.2).
- **Próximo grande tema natural**: pivot pra **Universo 4** (a definir —
  candidatos: qualidade & métricas, complexidade ciclomática, hot-paths,
  ownership analytics).
- **Limitações conhecidas** (em `skills/docs/SKILL.md`):
  - Headers legados pré-Protheus.doc (ASCII art `+--+`) não detectados
  - Inline `//{pdoc}` (associado a próxima variável) fora do MVP
  - Bloco sem `/*/` fechamento ignorado (BP-007b candidato futuro)
  - Cross-validação `@param` vs assinatura real fora do MVP (BP-009 candidato)

## [0.4.1] - 2026-05-15

### 🚀 Universo 3 — Rastreabilidade Feature B (ExecAuto chain expansion)

Resolve a indireção do `MsExecAuto({|x,y,z| MATA410(x,y,z)}, ...)` e cruza
com catálogo TOTVS (25 rotinas) pra **inferir tabelas tocadas indiretamente**.
Antes: `arch` mostrava `tabelas: []` mesmo o fonte chamando `MATA410` (que
toca SC5/SC6) via ExecAuto. Agora: `tabelas_via_execauto_resolvidas: ["SC5","SC6","SF4","SB1"]`.

### Added
- **Catálogo `lookups/execauto_routines.json`** — 25 rotinas TOTVS canônicas
  (MATA010/030/050/075/103/110/120/125/150/180/220/242/261/310/311/410/460/461,
  FINA040/050/070/080, CTBA102, EECAP100, TMSA500) com `routine`, `module`,
  `type`, `tables_primary`, `tables_secondary`, `source_url`, `verified`.
  Rotinas faltantes ainda são detectadas (com `module=null`); expansão via PR.
- **Detector `parsing/execauto.py`** — `extract_execauto_calls(content)` extrai
  chamadas `MsExecAuto`/`ExecAuto` (case-insensitive), parseia codeblock pra
  achar a rotina, detecta `op_code` (3/4/5 → inclusao/alteracao/exclusao),
  flag `dynamic_call` pra `&(cVar)` ou codeblock vazio.
- **Tabela `execauto_calls`** (schema v5→v6, migration 006) — 1 row por chamada
  com `arquivo, funcao, linha, routine, module, routine_type, op_code,
  op_label, tables_resolved_json, dynamic_call, arg_count, snippet`. 3 índices.
- **Comando `plugadvpl execauto`** com filtros `--routine`/`--modulo`/
  `--arquivo`/`--op` (inc/alt/exc)/`--dynamic`. Skill `/plugadvpl:execauto`.
- **Enrichment de `arch`** — campo novo `tabelas_via_execauto_resolvidas:
  list[str]` agregando tabelas inferidas. Campo bool antigo
  `tabelas_via_execauto` continua (não-breaking).
- **Counter** `execauto_calls` no contador de ingest + meta `total_execauto_calls`.

### Tests
- **26 testes unit** (`tests/unit/test_execauto.py`):
  TestRoutineResolution (6), TestOpCodeDetection (5), TestDynamicCall (2),
  TestEdgeCases (6), TestCatalog (3), TestMetadataFields (4).
  Cobre todas as 8 sintaxes documentadas no spec + 11 edge cases.
- **8 testes integration** (`tests/integration/test_cli.py::TestExecauto`):
  fixture com 3 fontes (MATA410 inc, FINA050 inc, dynamic), exercita
  `--routine`/`--modulo`/`--dynamic`/`--op` + arch enrichment + DB sanity.
- **434 testes verde** (era 408).

### Migration
- **Schema 5 → 6** (não-breaking; só adiciona tabela). DBs v0.4.0 são reindexados
  automaticamente no próximo `init`.

### Casos de uso
1. *"Quem inclui Pedido de Venda automaticamente?"* →
   `/plugadvpl:execauto --routine MATA410 --op inc`
2. *"Quais fontes integram com SIGAFIN via ExecAuto?"* →
   `/plugadvpl:execauto --modulo SIGAFIN`
3. *"Cobertura real de tabelas deste fonte?"* →
   `arch X.prw` agora mostra `tabelas_via_execauto_resolvidas`
4. *"Auditar exclusões automáticas"* →
   `/plugadvpl:execauto --op exc`
5. *"Calls não-resolvíveis (precisam revisão manual)?"* →
   `/plugadvpl:execauto --dynamic`

### Notes
- **Spec aprovado** em `docs/universo3/B-execauto-chain.md` antes do código
  (workflow research → spec MD → approval → code).
- **Próximo passo Universo 3**: Feature C (Protheus.doc agregada por módulo —
  `/plugadvpl:docs <modulo>`).
- **Limitações conhecidas** (em `skills/execauto/SKILL.md`):
  - Variável armazenada (`bExec := {...}; MsExecAuto(bExec, ...)`) → flag dynamic
    (precisaria data-flow analysis, fora do MVP)
  - Macro-substituição `&(cRot)` → flag dynamic (raro)
  - Rotinas fora do catálogo → detectadas com `module=null` (PR-friendly)
  - `op_code` por convenção (último arg numérico literal); `nOpc` em variável
    fica `null`

## [0.4.0] - 2026-05-15

### 🚀 Universo 3 — Rastreabilidade (Feature A: Workflow + Schedule + Job + Mail)

**Killer feature do v0.4.x**: indexação dos 4 mecanismos canônicos TOTVS de
**execução não-direta**. Antes do v0.4.0 era impossível responder via plugin
"essa rotina é alvo de workflow ou helper?", "que jobs do AppServer existem
nesse projeto?", "qual schedule dispara `FATR020`?", "onde envio email com
anexo?". Agora 1 comando responde tudo: `/plugadvpl:workflow`.

### Added
- **Tabela `execution_triggers`** (schema v5, migration `005_universo3_execution_triggers.sql`)
  com colunas `id, arquivo, funcao, linha, kind, target, metadata_json, snippet`.
  3 índices: `idx_exec_arquivo`, `idx_exec_kind`, `idx_exec_target`.
- **Detector `parsing/triggers.py`** com 4 detectores:
  - `workflow` — `TWFProcess():New(...)`, `MsWorkflow(`, `WFPrepEnv(` em callbacks.
    Metadata: `process_id`, `description`, `template`, `to`, `subject`,
    `return_callback`, `timeout_callback`, `is_legacy`.
  - `schedule` — `Static Function SchedDef()` retornando array
    `{cTipo, cPergunte, cAlias, aOrdem, cTitulo}`. Metadata: `sched_type` (P/R),
    `pergunte` (referência SX1), `alias`, `ordens`, `titulo`.
  - `job_standalone` — `Main Function` + `RpcSetEnv` + `Sleep` loop (daemon
    ONSTART). Metadata: `main_name`, `empresa`, `filial`, `modulo`,
    `sleep_seconds`, `stop_flag`, `no_license`.
  - `mail_send` — `MailAuto(`, `SEND MAIL` UDC, `TMailManager`/`TMailMessage`.
    Metadata: `variant`, `has_attachment`, `uses_mv_rel` (cross-ref com SEC-004).
- **Comando `plugadvpl workflow`** (e skill `/plugadvpl:workflow`) com filtros
  `--kind`, `--target`, `--arquivo`. Usa metadata JSON pra detalhe por tipo.
- **Resolução de `funcao`** — usa o índice de chunks (v0.3.15+) pra mapear
  cada trigger à função-pai onde foi declarado.
- **Idempotência** — DELETE+INSERT no `_clear_for_arquivo` (padrão v0.3.28).
- **Counter** `execution_triggers` no contador de ingest + `total_execution_triggers`
  em `meta` (visível via `plugadvpl status`).

### Tests
- **14 testes unit** (`tests/unit/test_triggers.py`):
  5 classes (TestWorkflowTrigger, TestScheduleTrigger, TestJobStandaloneTrigger,
  TestMailSendTrigger, TestMultiTriggerSource), positivos + negativos por kind.
- **5 testes integration** (`tests/integration/test_cli.py::TestWorkflow`):
  fixture `triggers_project` com 3 fontes (1 workflow, 1 schedule, 1 job+mail
  multi-trigger), exercita todos os filtros + sanity check no DB.
- **408 testes verde** (era 389).

### Migration
- **Schema 4 → 5** (breaking; `plugadvpl init` em DBs existentes força reindex).
  Nenhum dado de v0.3.x perdido — `chunks`, `lint_findings`, `simbolos`, etc
  continuam intactos. Apenas a tabela nova é criada.

### Casos de uso
1. *"Esta User Function `XYZAprov` é alvo de workflow?"* →
   `/plugadvpl:workflow --target XYZAprov` (se aparecer com `kind=workflow`, é callback).
2. *"Que Main Functions deste projeto são jobs daemon?"* →
   `/plugadvpl:workflow --kind job_standalone`.
3. *"Esse `FATR020.prw` é agendável?"* →
   `/plugadvpl:workflow --arquivo FATR020.prw --kind schedule`
   (metadata.pergunte aponta o grupo SX1 — cruzar com `/plugadvpl:param`).
4. *"Onde envio email com anexo?"* →
   `/plugadvpl:workflow --kind mail_send` + filtrar `metadata.has_attachment=True`.
5. *"Esse fonte usa SX6 ou hardcoded?"* →
   `mail_send` com `metadata.uses_mv_rel=True` (correto) ou `False`
   (cruzar com SEC-004 do lint).

### Notes
- **Spec aprovado** em `docs/universo3/A-workflow-schedule.md` antes do código
  (workflow novo: research → spec MD → approval → code).
- **Próximo passo Universo 3**: Feature B (ExecAuto chain expansion — primeiro
  arg do `MsExecAuto` resolvido pra alvo + tabelas) e Feature C (Protheus.doc
  agregada por módulo).
- **Limitações conhecidas** (documentadas em `skills/workflow/SKILL.md`):
  frequência de schedule (`SCHTSK`/`SCHFIL`/`SCHSERV`), AppServer.ini
  (`[ONSTART]`), e `TWebChannel` workflow webview ficam fora do MVP.

## [0.3.30] - 2026-05-15

### 🎉 Audit V4 closeout — fecha 3 dos 4 últimos itens. Sobra apenas #14 (SX-005 carrega 50-250MB corpus em monorepo gigante) que o próprio auditor classificou como "tradeoff aceitável, comment já justifica". **Backlog técnico zerado para uso prático.** 14 dos 15 achados de Audit V4 endereçados em 3 releases (v0.3.28, v0.3.29, v0.3.30).

### Fixed
- **#8 (BAIXA) — PERF-006 cross-table determinismo**. Antes iterava
  `dict.items()` (ordem não-determinística) e parava no primeiro match —
  em projeto com prefixo de coluna compartilhado entre tabelas (raro mas
  existe: `SR8` + extension `SR8XYZ`), a coluna podia ser reportada como
  não-indexada apenas porque a primeira tabela visitada não tinha o
  índice. Agora coleta TODAS as tabelas candidatas (sorted = determinístico),
  decide "indexada se em qualquer uma", reporta contra a primeira candidata
  alfabética caso negativa.
- **#9 (BAIXA) — SEC-005 ignora função homônima local**. Antes, se o
  fonte definia `User Function StaticCall(cArg)` (homônima a TOTVS-restrita
  catalogada), as chamadas a `StaticCall(...)` no mesmo fonte disparavam
  SEC-005 erroneamente. Cenário improvável mas possível em PEs canônicas
  (`MT100LOK`, `ANCTB102GR`, etc — clientes podem criar User Function
  homônima). Agora coleta nomes definidos localmente (kinds: `user_function`/
  `static_function`/`main_function`/`function`/`method`) e skipa.

### Added
- **#10 (BAIXA) — PERF-006 emite warning quando `indices` SX vazia**.
  Antes retornava `findings = []` silenciosamente — usuário rodava
  `lint --cross-file --regra PERF-006`, recebia 0 findings, e não sabia se
  era "sem problema" ou "sem dado SX ingerido". Agora detector imprime
  amarelo em stderr explicando: "WARN: PERF-006 ha N SQL com WHERE/ORDER BY
  pra avaliar, mas tabela `indices` (SIX) esta vazia. Cobertura limitada —
  rode `plugadvpl ingest-sx <pasta-csv>` com SX dictionary completo
  (incluindo six.csv) pra habilitar deteccao de coluna sem indice."
- `import sys` em `lint.py` (era ausente — necessário pro print stderr).

### Tests
- 3 testes RED→GREEN:
  - `tests/unit/test_lint.py::TestSec005LocallyDefinedFunction::test_negative_local_user_function_homonyma` (#9 negativo)
  - `tests/unit/test_lint.py::TestSec005LocallyDefinedFunction::test_positive_external_call_still_fires` (#9 positivo regressão)
  - `tests/integration/test_ingest_sx.py::TestLintCrossFile::test_lint_cross_file_perf006_warns_when_indices_empty` (#10 stderr warning)
- 389 testes verde (era 386).

### Notes
- **Audit V4 closeout — 14/15 endereçados, 1 documented tradeoff**:
  - #1, #2, #3, #5, #6, #11, #15 → v0.3.28 (lint robustness pack 1)
  - #4, #7, #12, #13 → v0.3.29 (lint robustness pack 2)
  - #8, #9, #10 → v0.3.30 (este release)
  - #14 (SX-005 corpus 50-250MB) → tradeoff documentado (auditor classificou
    como "atual eh aceitavel; nao otimizar prematuramente")
- **Total ciclo QA do projeto** (rounds 1+2+3 + audit técnico V4 = 51 achados,
  50 endereçados em 17 releases, v0.3.14 → v0.3.30). 1 deferido (não-bug).
- **Próximo grande tema natural**: pivot pra **v0.4.0 Universo 3** — workflows,
  schedules, integrações cross-fonte. Catálogo lint fechado, robustness
  fechada, ciclo QA fechado.

## [0.3.29] - 2026-05-15

### Lint robustness pack 2 — fecha mais 4 dos 8 restantes do `gaps/PLUGADVPL_LINT_AUDIT_V4.md`. Foco em precision/recall: PERF-004 hungarian estrito, BP-005 paren balance, BP-001 RecLock variável/físico, SEC-003 sufixo CamelCase. Sobram 4 de severidade média/baixa (PERF-006 determinismo, SEC-005 homônima local, PERF-006 fallback, SX-005 corpus 50-250MB).

### Fixed
- **#4 (MÉDIA) — PERF-004 hungarian estrito (`c[A-Z]\\w*`)**. Antes
  `c[A-Za-z_]\\w*` casava `cnt` (counter), `csv`, `cmd`, `crm` — siglas 3
  letras lowercase comuns em ADVPL legado. Estrito exige segunda letra
  MAIÚSCULA, eliminando FP sem perder casos hungarianos válidos
  (`cBuffer`, `cMsg`, `cAcc`, etc).
- **#13 (BAIXA) — BP-005 paren balance em params**. Antes
  `params_text.count(",") + 1` inflava contagem em defaults com array
  literal `{1,2,3}` ou função aninhada `MyFn(1,2,3)`. Função com 5 params
  reais + `cD := {1,2,3}` virava 7 params apparent → BP-005 falso
  positivo. Helper novo `_count_top_level_commas(text)` ignora vírgulas
  dentro de `()`/`{}`/`[]`.
- **#7 (MÉDIA) — BP-001 detecta RecLock com físico/variável**. Antes
  `\\w{2,3}` perdia alias físico (`SA1010`, 6 chars) e variável (`cTab`,
  sem aspas). Agora:
  - `_RECLOCK_OPEN_RE` aceita literal 2-7 chars (cobre alias lógico SA1
    + físico SA1010).
  - `_RECLOCK_OPEN_VAR_RE` (novo) captura `RecLock(<identifier>, ...)`
    sem aspas — cenário comum em scripts de migração e rotinas reuse.
  - `_RECLOCK_VIA_ALIAS_RE` também 2-7 chars.
- **#12 (BAIXA) — SEC-003 forma curta aceita sufixo CamelCase**. Antes
  `\\bc(?:Pwd|Rg|Pin|Card|Pass)\\b` exigia boundary após o termo —
  perdia variantes legítimas como `cPwdHash` (hash de senha continua
  PII), `cRgEmissor` (info do RG), `cCardNumber`, `cPinAtual`. Agora
  `\\bc(?:Pwd|Rg|Pin|Card|Pass)(?:[A-Z]\\w*)?\\b` aceita sufixo iniciado
  em maiúscula. Continua não-pegando `cPassagem`/`cCardapio` (próxima
  letra é minúscula = parte de palavra PT-BR).

### Tests
- 11 testes RED→GREEN em `test_lint.py`:
  - `TestPerf004HungarianStrict` — 4 testes (2 negativos `cnt`/`csv` +
    2 positivos `cBuffer`/`cAcc`).
  - `TestBp005ParenBalance` — 3 testes (2 negativos com `{1,2,3}` +
    `MyFn(1,2,3)` defaults + 1 positivo regressão 7 params reais).
  - `TestBp001RecLockExtended` — 2 testes (físico `SA1010` + variável
    `cTab`).
  - `TestSec003ShortFormSuffix` — 2 testes (`cPwdHash` + `cRgEmissor`).
- 386 testes verde (era 375).

### Notes
- **Backlog Audit V4 restante (4 itens, todos baixos)**:
  - #8 (PERF-006 cross-table match não-determinístico — depende de ordem
    de `dict.items()`).
  - #9 (SEC-005 não distingue função homônima custom local — improvável
    mas possível em PEs canônicos).
  - #10 (PERF-006 sem aviso quando `indices` SX vazia — UX, não bug).
  - #14 (SX-005 carrega 50-250MB corpus em memória — só problema em
    monorepo gigante; comment já justifica como aceitável).
- **Quase fim do backlog técnico**. Continuar com #8 + #9 fecharia 100%
  do Audit V4. #10 é UX simples. #14 é trade-off documentado.

## [0.3.28] - 2026-05-15

### Lint robustness pack — fecha 7 dos 15 achados de `gaps/PLUGADVPL_LINT_AUDIT_V4.md`. Foco em correctness técnica: persist cross-file, SQL truncation, regex frágeis. Sobram 8 médios/baixos no backlog (PERF-004 hungarian estrito, BP-001 RecLock variável, PERF-006 cross-table determinismo, etc).

### Fixed
- **#1 (CRÍTICO) — `persist_cross_file_findings` apagava só `LIKE 'SX-%'`**.
  MOD-003 (v0.3.26) e PERF-006 (v0.3.27) acumulavam findings duplicados a
  cada execução de `lint --cross-file`. Fix: deriva lista de regra_ids
  diretamente de `_CROSS_FILE_RULES` e usa `DELETE WHERE regra_id IN (...)`.
- **#2 (ALTA) — `_SQL_SNIPPET_MAX` bumpado 300 → 8000**. Antes, queries
  MVC com 2+ JOINs ultrapassavam 300 chars e tinham `%notDel%`/`%xfilial%`
  truncados pra fora do snippet → PERF-002/003/006 disparavam falso
  positivo massivo em código real Protheus de faturamento/financeiro.
  8000 cobre 99% de SQL ADVPL real; custo DB <1MB extra em projeto grande.
- **#3 (ALTA) — `_CLIENT_PREFIX_RE` removeu prefixos PT-BR ambíguos**.
  Antes incluía `FAT|FIN|COM|EST|CTB|FIS|PCP|MNT` (módulos Protheus, mas
  casavam palavras PT-BR comuns como `FATURA`, `COMPRA`, `FINALIZA`,
  `ESTOQUE`) → SEC-002 escapava o caso canônico (User Function PT-BR sem
  prefix). Removidos também `U_` (dead code: parser extrai nome SEM `U_`)
  e `MT[A-Z]/MA\\d` (já cobertos por `_PE_NAME_RE`). Sobram apenas iniciais
  genuinamente "de empresa": `MGF|MZF|ZZF|ZF|XX|XYZ|CLI`.
- **#5 (MÉDIA) — SX-009 `\\b\\.F\\.\\b` nunca casava**. `.` é non-word, então
  `\\b` antes de `.` exige um word-char à esquerda — impossível em `init=.F.`
  (`=` também é non-word). Drift catálogo×impl silencioso desde criação da
  regra. Fix: trocou por lookarounds `(?<![A-Za-z0-9_])\\.F\\.(?![A-Za-z0-9_])`.
- **#5 bonus — `inicializador` lia de `X3_RELACAO` em vez de `X3_INIT`**.
  Bug de mapping no `parse_sx3` causava SX-009 ler o campo errado. X3_INIT
  é o initializer canônico TOTVS (valor padrão); X3_RELACAO é autofill por
  expressão. Fix: lê X3_INIT prioritariamente, fallback X3_RELACAO pra
  compat com fixtures legadas.
- **#6 (BAIXA) — Mensagem SX-009 citava `X3_RELACAO` em vez de `X3_INIT`**.
  Texto do fix_guidance corrigido pra refletir o campo correto.
- **#11 (BAIXA) — BP-007 skipava `kind="mvc_hook"` que não existe**. Parser
  emite kinds `user_function/static_function/main_function/function/ws_method/method`
  — nenhum `mvc_hook`. Branch removido (dead code + comentário enganoso).
- **#15 (BAIXA) — BP-002 `fix_guidance` tinha frase de BP-006**. Última
  frase falava "NUNCA misture funções de manutenção AdvPL básicas com
  Framework dentro do mesmo bloco" — copy-paste do BP-006. Substituída
  por dica MVC apropriada (`oModel:CommitData()` em vez de Begin/End
  manual).

### Tests
- 6 testes RED→GREEN em `test_lint.py` + `test_ingest_sx.py`:
  - `TestLintCrossFile::test_lint_cross_file_persist_does_not_accumulate_mod003` (#1)
  - `TestPerf002NoNotDel::test_negative_long_sql_with_notdel_after_300_chars` (#2)
  - `TestSec002UserFunctionNoPrefix::test_positive_pt_br_word_FATURA` (#3)
  - `TestSec002UserFunctionNoPrefix::test_positive_pt_br_word_COMPRA` (#3)
  - `TestSec002UserFunctionNoPrefix::test_positive_pt_br_word_FINALIZA` (#3)
  - `TestLintCrossFile::test_lint_cross_file_sx009_detects_dot_F_dot_init` (#5+#6)
- 375 testes verde (era 369).

### Notes
- **Backlog Audit V4**: dos 15 achados, 7 fechados nesta release. Continuam
  pendentes (todos médios/baixos, sem urgência):
  - #4 (PERF-004 dispara em `cnt`/`csv` — solução exigir `c[A-Z]\\w*` estrito)
  - #7 (BP-001 perde RecLock com físico/variável — recall vs precision)
  - #8 (PERF-006 cross-table match não-determinístico)
  - #9 (SEC-005 não distingue função homônima local)
  - #10 (PERF-006 sem fallback gracioso `indices` vazia)
  - #12 (SEC-003 forma curta `\\b...\\b` ignora `cPwdHash` etc)
  - #13 (BP-005 conta vírgula naive em default `{1,2}`)
  - #14 (SX-005 carrega 50-250MB corpus em memória)
- **Re-ingest recomendado**: `plugadvpl ingest --no-incremental` aplica fix
  #2 (snippet 8000) em fontes já indexados. Sem isso, snippets antigos
  continuam truncados a 300 e PERF-002/003/006 vão continuar com FP.

## [0.3.27] - 2026-05-15

### 🎉 Catálogo lint 100% ativo. Última regra `planned` (PERF-006) implementada — fecha o ciclo iniciado em v0.3.4 (catálogo × impl alignment) com **35/35 regras detectáveis automaticamente**.

### Added
- **PERF-006 (info, cross-file) — WHERE/ORDER BY em coluna sem índice SIX**.
  Detector cross-file que requer `ingest-sx` (precisa da `indices` SIX).
  Skipa graciosamente quando ausente. Heurística:
  1. Lê `sql_embedado` rows com `WHERE` ou `ORDER BY` no snippet.
  2. Extrai colunas estilo `<TBL>_<NOME>` (regex `[A-Z][A-Z0-9]{1,2}_<NOME>`
     — cobre `A1_COD`, `B1_DESC`, `RA_CIC`, `R8_TIPO`, etc).
  3. Filtra pseudo-colunas Protheus (`D_E_L_E_T_`, `R_E_C_N_O_`,
     `R_E_C_D_E_L_`) e `*_FILIAL` (sempre primeira chave em qualquer
     composto, nunca causa scan).
  4. Cruza com cache `{tabela: {colunas em qualquer chave}}` derivado
     de `indices.chave`.
  5. Coluna NÃO em nenhum índice → emite finding com `tabela.coluna`.
  
  Heurísticas conservadoras (severidade `info`, baixo FP):
  - Skipa coluna sem prefixo claro de tabela (alias dinâmico no SQL).
  - Skipa quando tabela ausente em `indices` (provável standard, não custom).
  - Dedup por `(arquivo, linha, tabela, coluna)`.
- Helpers em `lint.py`:
  - `_PERF006_PSEUDO_COLS` — set com pseudo-colunas Protheus a ignorar.
  - `_PERF006_COLUMN_RE` — regex coluna estilo `A1_COD` (suporta dígito no prefix).
  - `_PERF006_WHERE_RE` / `_PERF006_ORDERBY_RE` — extração de cláusula
    com lookahead pra próximas keywords (GROUP BY/HAVING/EndSql/$).

### Changed
- Catálogo `lookups/lint_rules.json`: PERF-006 `status="planned"` → `"active"`
  + `impl_function="_check_perf006_where_orderby_no_index"` + descrição
  expandida com algoritmo completo + lista de exclusões.
- Skill `advpl-code-review`:
  - Frontmatter: `34 → 35` regras, `12 → 13` cross-file.
    **"100% do catálogo"** explícito.
  - Tabela cross-file: nova entrada PERF-006.
  - Nova seção "Catálogo 100% ativo (v0.3.27)" substitui "regras planned".
  - "Info / Checklist mental" reescrita pra "Catálogo 100% automatizado" —
    não há mais checklist humano residual.
- 18 skills bumpadas `@0.3.26` → `@0.3.27`.

### Tests
- `tests/integration/test_ingest_sx.py::TestLintCrossFile::test_lint_cross_file_perf006_where_orderby_no_index`:
  fixture com 2 fontes — `QrySemIdx.prw` (BeginSql `WHERE A1_NOME = ...`,
  não indexado) deve disparar PERF-006; `QryComIdx.prw` (`WHERE A1_COD = ...`,
  indexado em SA1#1) NÃO deve disparar.
- 369 testes verde (era 368).

### Notes
- **Marco do projeto**: catálogo iniciou em v0.3.0 com 35 regras (24 active +
  11 planned). Após 27 releases, fechamento total: **35 active + 0 planned**.
  Total de testes cresceu de ~252 (v0.3.13) → 369 (v0.3.27), +117 testes
  cobrindo novos detectores.
- **PERF-006 é conservadora por design**: severidade `info` significa que
  não bloqueia merge/CI. Em projetos com SX rico mas standard tables não
  ingeridas, FP é baixo (skipa quando tabela ausente em `indices`).
- **Próximo grande tema natural**: pivot pra **v0.4.0 Universo 3
  (Rastreabilidade)** — workflows, schedules, integrações cross-fonte —
  com tranquilidade. Catálogo lint fechado, ciclo QA fechado.

## [0.3.26] - 2026-05-15

### MOD-003 implementado — primeira regra cross-file que NÃO requer SX. Sobra apenas PERF-006 (a mais complexa) pra fechar 100% do catálogo.

### Added
- **MOD-003 (info, cross-file) — grupos de Static Function por prefixo**.
  Detector roda no orchestrator cross-file mas opera só sobre `fonte_chunks`
  (não exige `ingest-sx`). Heurística:
  - Agrupa Static Functions por **arquivo + prefixo**.
  - Testa lengths de prefixo de **6 → 3 chars**, escolhe o maior que ainda
    forma grupo de **>=3 funções**.
  - Suprime grupos cujo prefixo já foi capturado por um mais específico
    (ex: emitir `_AppCalc` evita re-emitir `_App` redundante).
  - 1 finding por grupo, na linha da primeira função.
  - Sugestão de fix orienta refatorar pra `Class T<Nome>` com `Data` +
    `Method` (TLPP `class` com `public/private/protected`).

### Changed
- **`_CROSS_FILE_RULES` agora é tupla de 3** `(regra_id, check_fn, requires_sx)`.
  - `requires_sx=True` (SX-001..SX-011) pula quando dicionário SX não foi
    ingerido (comportamento existente).
  - `requires_sx=False` (MOD-003) sempre roda.
  - `lint_cross_file()` checa o flag por regra em vez de gate global no início.
- Catálogo `lookups/lint_rules.json`: MOD-003 `status="planned"` → `"active"`
  + `impl_function="_check_mod003_static_funcs_to_class"` + título atualizado
  + descrição expandida com heurística.
- Skill `advpl-code-review`:
  - Frontmatter: `33 → 34` regras, `2 → 1` planned. Cita "12 cross-file
    (11 SX + MOD-003)" — explicita que MOD-003 não exige SX.
  - Tabela cross-file: entrada nova MOD-003 com nota "não requer ingest-sx".
  - Bloco "Info / Checklist mental": só PERF-006 sobra.
- `tests/unit/test_lint_catalog_consistency.py::test_all_check_functions_registered_in_orchestrator`
  ajustado pra suportar tanto formato tupla antigo `(id, fn),` quanto novo
  `(id, fn, requires_sx),`.
- 18 skills bumpadas `@0.3.25` → `@0.3.26`.

### Tests
- `tests/integration/test_ingest_sx.py::TestLintCrossFile::test_lint_cross_file_mod003_groups_static_functions_by_prefix`:
  fixture com 4 Static Functions `_AppCalc*` no mesmo arquivo (esperado:
  1 finding) + arquivo separado com só 2 fns mesmo prefixo (não atinge
  threshold, sem finding). Garantia de threshold=3 + supressão de
  prefixos curtos redundantes.
- 368 testes verde (era 367).

### Notes
- **Catalog status**: 34 active + 1 planned + 5 cross-file SX adicional
  já cobertos = 35 total. Sobra **apenas PERF-006** pra fechar o catálogo
  100%. PERF-006 é a mais complexa (cross-file SQL parser + cruzamento
  com índices SIX) — release dedicada (~4-6h) vai fechar v0.3.27.
- **Por que MOD-003 não usa SX**: opera sobre `fonte_chunks.tipo_simbolo
  = 'static_function'` que é populado pelo `ingest` regular. Decisão
  arquitetural: o grupo `cross-file` engloba qualquer regra que precise
  agregar dados ENTRE fontes, não só SX. PERF-006 também será cross-file
  sem SX (precisa de `indices` table do SX dictionary, mas pode skipar
  graciosamente quando ausente).
- **Threshold de 3 escolhido**: 2 funções mesmo prefixo é coincidência
  comum em ADVPL (helper privado + variante). 3+ indica padrão deliberado.
  Configurável no futuro via `--mod003-threshold N` se houver demanda.

## [0.3.25] - 2026-05-15

### BP-002b implementado — Private quando Local resolveria. Segunda das 4 lint planned originais (sobram MOD-003 + PERF-006). Detector com whitelist conservadora pra reduzir noise em código legacy ADVPL.

### Added
- **BP-002b (warning) — `Private <var>` em vez de `Local`**. Detector com
  whitelist pra padrões legítimos:
  - `MV_PAR01..MV_PAR99` — convenção `Pergunte()` (variáveis injetadas
    no escopo Private).
  - `lMsErroAuto`/`lMsHelpAuto` — convenção `MsExecAuto` (BP-003 cita).
  - 18 reservadas framework (`cFilAnt`, `cEmpAnt`, `dDataBase`, etc) —
    overlap com BP-008 aceito (categorias diferentes: best-practice vs
    critical, mensagens distintas).
  
  **Decisão de design:** foca em `Private` apenas. `Public` é coberto
  por MOD-002 — evitar duplo finding na mesma linha. BP-002b e MOD-002
  cobrem aspectos distintos do mesmo problema (escopo amplo desnecessário).
- Helpers em `lint.py`:
  - `_BP002B_PRIVATE_RE` — captura linha completa `Private ...` ate EOL,
    parser interno extrai nomes via split por `,` e remoção do `:= valor`.
  - `_BP002B_WHITELIST` — set com lMsErroAuto/lMsHelpAuto + 18 reservadas.
  - `_BP002B_MV_PAR_RE` — `^MV_PAR\\d{2}$` (case-insensitive).

### Changed
- Catálogo `lookups/lint_rules.json`: BP-002b `status="planned"` → `"active"`
  + `impl_function="_check_bp002b_private_when_local"` + título atualizado
  pra "Private quando Local resolveria" (antes mencionava também Public,
  agora desambiguado).
- Skill `advpl-code-review`:
  - Frontmatter: `32 → 33` regras, `21 → 22` single-file, `3 → 2` planned.
  - Tabela "Single-file": entrada nova BP-002b (warning, novo em v0.3.25)
    com whitelist citada.
  - Bloco "Info / Checklist mental": BP-002b sai (agora detectado);
    sobram só MOD-003 + PERF-006 (cross-file).
- 18 skills bumpadas `@0.3.24` → `@0.3.25`.

### Tests
- 9 testes em `TestBP002bPrivateWhenLocal` (3 positivos + 6 negativos):
  - `test_positive_private_simple_var`, `test_positive_private_multivar`,
    `test_positive_private_with_assign`.
  - `test_negative_private_mv_par`, `test_negative_private_msexecauto_state`,
    `test_negative_local_decl_not_flagged`, `test_negative_static_decl_not_flagged`,
    `test_negative_public_not_flagged_handled_by_mod002` (verifica que
    `Public` dispara MOD-002 mas NÃO BP-002b — separação clean),
    `test_negative_in_comment`.
- 367 testes verde (era 358).

### Notes
- **Catalog status**: 33 active + 2 planned + 5 cross-file SX = 40
  detectores efetivos. Fechamento total exige MOD-003 (cross-file
  semântica) + PERF-006 (cross-file SQL parser). Ambos são
  implementações maiores (~3-6h cada).
- **Whitelist "MV_PAR01..MV_PAR99"**: usa regex `^MV_PAR\\d{2}$`
  case-insensitive. Cobre o range típico TOTVS (Pergunte raramente
  passa de MV_PAR99). Se algum projeto usa MV_PAR100+, vão receber
  BP-002b — fix: trocar pra `Local`/`Static` ou adicionar à whitelist.
- **Whitelist com framework reservadas (18 nomes)**: redundante com
  BP-008 (que dispara `critical` no shadowing). Mantemos o overlap
  porque BP-008 é categoria `critical`/security e BP-002b é
  `warning`/best-practice — desligar uma das duas perde sinal.

## [0.3.24] - 2026-05-15

### BP-007 implementado — falta header Protheus.doc. Primeira das 4 lint planned restantes do catálogo (sobram BP-002b, MOD-003, PERF-006). User pediu "fechar lint antes de pivotar pra Universo 3".

### Added
- **BP-007 (info) — função sem header Protheus.doc**. Detector busca o
  opening `/*/{Protheus.doc}` (case-insensitive) nas **30 linhas anteriores**
  à declaração de cada `User Function`/`Static Function`/`Main Function`/
  `Method`. Match loose (presença do bloco já conta — não exigimos que o
  nome no header bata exatamente com o da função, equipes copiam-cola).
  Skipa MVC hooks (`kind="mvc_hook"` = anonymous, não são funções reais).
- Helpers em `lint.py`:
  - `_BP007_DOC_OPEN_RE` — regex pra `/*/{Protheus.doc}` flexível
    (espaços/case opcionais).
  - `_BP007_WINDOW_LINES = 30` — janela conservadora (header típico
    tem 10-20 linhas).

### Changed
- Catálogo `lookups/lint_rules.json`: BP-007 `status="planned"` → `"active"`
  + `impl_function="_check_bp007_no_protheus_doc"`. Descrição expandida
  com detalhes do detector (window, match loose, skip de mvc_hook).
- Skill `advpl-code-review`:
  - Frontmatter: `31 → 32` regras, `20 → 21` single-file, `4 → 3` planned.
  - Tabela "Single-file": entrada nova BP-007 (info, novo em v0.3.24).
  - Bloco "Info / Checklist mental": BP-007 sai (agora detectado);
    sobram só os 3 planned restantes (BP-002b, MOD-003, PERF-006).
- 18 skills bumpadas `@0.3.23` → `@0.3.24`.

### Tests
- 8 testes em `TestBP007NoProtheusDoc` (4 positivos + 4 negativos):
  - `test_positive_user_function_without_doc`
  - `test_positive_static_function_without_doc`
  - `test_positive_method_without_doc`
  - `test_positive_multiple_undocumented_functions`
  - `test_negative_protheus_doc_present` (header completo)
  - `test_negative_doc_is_minimal_but_present` (so opening + closing)
  - `test_negative_mvc_hook_skipped`
  - `test_negative_doc_for_each_of_multiple_functions`
- `test_clean_code_returns_empty` em `TestLintSourceIntegration`
  ajustado pra incluir Protheus.doc minimal — preserva contrato
  "clean code = zero findings" agora que BP-007 está ativa.
- 358 testes verde (era 350).

### Notes
- **Catalog status**: 32 active + 3 planned + 5 cross-file (3 + 2 das
  cross-file SX já cobrem) = 35 total. Falta apenas BP-002b/MOD-003/PERF-006
  pra fechar 100%. PERF-006 é a mais complexa (cross-file, requer parser
  SQL pra mapear coluna usada vs índice SIX).
- **Severidade `info`**: BP-007 não bloqueia nem alerta — é checklist
  pra cobertura de docs. Em projetos com >>milhões de findings legados,
  use `--severity warning` ou `--severity error` pra filtrar.
- **Match loose justificado**: docstring do detector explica decisão.
  Match estrito (com nome da função) gerava FPs em equipes que
  copiavam-colavam header de função similar e esqueciam de renomear.
  A presença do bloco já indica intenção de documentar — o nome errado
  é problema separado (eventual lint futuro).

## [0.3.23] - 2026-05-15

### Fragment versioning + V3 anonymization — fecha o **único** item ainda pendente do `gaps/PLUGADVPL_QA_REPORT_V3.md` (#1 do round 1, sobreviveu até round 3 porque exigia mecanismo de detecção de stale fragment). Com este release, **todos os 35 achados dos 3 rounds de QA estão endereçados**.

### Added
- **#1 — Fragment do CLAUDE.md tem marker de versionamento + warning em `status`**.
  Comportamento novo:
  - Toda execução de `init` injeta `<!-- plugadvpl-fragment-version: X.Y.Z -->`
    como primeira linha do bloco BEGIN/END plugadvpl, onde `X.Y.Z` é o
    `__version__` do binário no momento da injeção.
  - `status` lê CLAUDE.md, extrai o marker, compara com `runtime_version`.
    Quando difere (ou está ausente em fragments pré-v0.3.23), emite warning
    amarelo em stderr: `⚠ Fragment do CLAUDE.md foi gerado por plugadvpl X.Y.Z,
    binário atual é A.B.C. Rode 'plugadvpl init' para regenerar...`
  - `init` já era idempotente (sobrescreve a região BEGIN/END preservando
    o resto do CLAUDE.md) — só precisava do marker pra detecção funcionar.
- Helper novo `_check_fragment_staleness(root) → str | None` em `cli.py`.
  Retorna `None` se atualizado ou se CLAUDE.md sem fragment (caso fresh
  pre-init não polui status); mensagem descritiva caso contrário.
- Regex `_CLAUDE_FRAGMENT_VERSION_MARKER_RE` extrai o valor do marker.

### Changed
- `_CLAUDE_FRAGMENT_BODY` ganhou linha `<!-- plugadvpl-fragment-version: __VERSION__ -->`
  no topo. `_write_claude_md_fragment` substitui `__VERSION__` por
  `__version__` real na hora de gravar.
- `gaps/PLUGADVPL_QA_REPORT copy.md` (committed acidentalmente em v0.3.22)
  foi anonimizado (`MARFRIG`/`Marfrig` → `CLIENTE_X`/`cliente real`,
  `D:\PrjProtheus\TESTE` → `D:\Projetos`) e renomeado pra
  `gaps/PLUGADVPL_QA_REPORT_V3.md` — consistente com nomenclatura do
  V1 e V2.

### Tests
- 3 testes novos em `TestStatus`:
  - `test_status_warns_when_claude_md_fragment_is_stale` — fragment com
    marker `0.0.1-old` deve disparar warning citando esse valor + `init`.
  - `test_status_no_fragment_warning_when_marker_matches` — fragment fresh
    do `init` recente não polui stderr.
  - `test_status_warns_when_claude_md_has_no_fragment_marker` — fragment
    pré-v0.3.23 sem marker deve disparar warning genérico.
- 350 testes verde (era 347).

### Notes
- **Ciclo QA fechado**: 3 rounds de QA externo + 1 round automatizado (subagent),
  35 achados totais, **35 endereçados** ao longo de 10 releases (v0.3.14-v0.3.23).
  Backlog QA zerado. Próxima direção natural: pivot pra v0.4.0 Universo 3 ou
  fechar últimas 4 lint planned (BP-007/BP-002b/MOD-003/PERF-006).
- **Para usuários existentes**: o warning vai disparar na primeira `plugadvpl status`
  pós-upgrade (porque marker estará ausente). Solução em 1 linha:
  `plugadvpl init` regenera o fragment sobrescrevendo só a região BEGIN/END
  plugadvpl — qualquer conteúdo manual no CLAUDE.md é preservado.

## [0.3.22] - 2026-05-15

### Closeout pack — fecha 9 dos 11 itens baixos restantes do `gaps/PLUGADVPL_QA_REPORT_V2.md`. Backlog QA round 2 efetivamente zerado (sobram 2 polish maiores explicitamente deferidos). Categoria SEC mais completa, gatilho com BFS bidirecional, sx-status com schema estavel.

### Fixed
- **#3 — `_SEC004_PREPARE_ENV_RE` aceita continuacao multilinha `;`**.
  Antes `[^\\n]*?` parava no `\\n` real — `PREPARE ENVIRONMENT EMPRESA cEmp ;\\n
  USER 'admin' ;\\n PASSWORD 'totvs' ;\\n MODULO 'FAT'` escapava (caso comum em
  ADVPL). Agora `.*?` + `re.DOTALL` cobre multilinhas, `?` mantem nao-greedy.
- **#5 — `_SEC003_PII_FIELDS_RE` cobre A2_*/RH_***. Antes so A1_* (clientes)
  e RA_* (funcionarios). Adicionado A2_* (fornecedores: A2_CGC/A2_CPFRG/
  A2_NOME/A2_NREDUZ/A2_EMAIL/A2_TEL/A2_END/A2_DDD) e RH_* (folha-dependentes:
  RH_CPFDEP/RH_NOMEDEP/RH_RGDEP). Cobre cenarios de leak comuns em rotinas
  de compras (CFO, NFE) e folha (declaracao IRPF).
- **#6 — `gatilho` agora faz BFS bidirecional**. v0.3.15 expandiu OR
  campo_destino na query mas o frontier so seguia downstream. Cadeia inversa
  morria em level 1: `Z → Y → X` com query por `X` retornava so `Y → X`,
  ignorava `Z → Y` (upstream do upstream). Agora ambos `cd` e `co` viram
  frontier do proximo nivel; visited evita loops.
- **#8 — `_PARAMIXB_USAGE_RE` busca em stripped_strict** (sem strings/comentarios).
  Antes scaneava `content.splitlines()` raw — fonte com
  `cMsg := "Use PARAMIXB[1] na implementacao"` ou `// PARAMIXB[2]` em
  comentario classificava equivocadamente como PE. Probabilidade pratica
  baixa mas correctness ganhada sem custo.
- **#16 — `sx_status` schema sempre consistente**. Antes mudava de 2 keys
  (sx_ingerido + msg) pra 14 keys (com counts) — caller no `--format json`
  precisava branchear. Agora sempre o mesmo set de 15 keys; quando ainda
  nao foi rodado `ingest-sx`, counts=0 e `last_sx_ingest_at`/`sx_csv_dir`
  ficam `null`. `msg` continua presente quando aplicavel.

### Added
- **#18 — Hint pra flags subcomando-scoped misplaced**. Caso inverso do #2:
  `plugadvpl --workers 8 ingest` agora detecta que `--workers` eh flag de
  subcomando (nao global) e sugere posicionamento correto:
  ```
  Dica: '--workers' eh uma flag de SUBCOMANDO — vem DEPOIS do subcomando.
    Errado:  plugadvpl --workers ... ingest
    Correto: plugadvpl ingest --workers ...
  ```
  Set `_SUBCOMMAND_FLAGS` cobre 16 flags de subcomandos (ingest/status/lint/
  gatilho/impacto/tables). `_detect_misplaced_global_flag` virou
  `_detect_misplaced_flag` (alias retrocompat mantido) com retorno
  `(flag, subcmd, scope)`.
- **#19 — Test `test_callees_resolves_innermost_chunk_with_nested_methods`**.
  v0.3.15 docstring fala de "chunk MAIS INTERNO em caso de nesting (Class >
  Method > Static)" mas testes anteriores eram happy-path. Novo test usa
  Method + Static Function adjacentes pra validar isolamento mutuo dos
  callees. Test passa sem precisar mudar codigo (regression guard).

### Changed
- Skill `impacto`: nova secao "Precisao por tipo (v0.3.17+)" documenta que
  rows tipo `fonte` usam substring (intencional — codigo pode ter `"SA1->A1_COD"`
  como string), enquanto SX3/SX7/SX1 usam word boundary. Inclui dica pra
  rodar `grep -m identifier` quando suspeitar de FP.
- Skill `arch`: lista de campos do output ganhou `tabelas_via_execauto: bool`
  (v0.3.18+) explicando significado, e nota sobre WSRESTFUL methods agora
  nomeados como `<Class>.<VERB>` desde v0.3.21.
- Skill `callers`: secao "Saida" inclui `is_self_call: bool` com exemplo
  de filtragem via `jq`.

### Tests
- 8 testes novos:
  - `tests/unit/test_lint.py::TestSEC003PIIInLogs::test_positive_a2_fornecedor_field_in_log`
  - `tests/unit/test_lint.py::TestSEC003PIIInLogs::test_positive_rh_funcionario_field_in_log`
  - `tests/unit/test_lint.py::TestSEC004HardcodedCreds::test_positive_prepare_environment_multiline_continuation`
  - `tests/unit/test_parser.py::TestParseSource::test_pe_paramixb_in_string_or_comment_does_not_trigger`
  - `tests/integration/test_ingest_sx.py::TestGatilhoCommand::test_gatilho_bidirectional_traversal_depth2`
  - `tests/integration/test_ingest_sx.py::TestSxStatusCommand::test_sx_status_schema_consistent_before_and_after_ingest`
  - `tests/integration/test_cli.py::TestGlobalFlagPositioning::test_misplaced_subcommand_flag_shows_inverse_hint`
  - `tests/unit/test_query.py::TestCallees::test_callees_resolves_innermost_chunk_with_nested_methods`
- 347 testes verde (era 339).

### Deferred (continuam no backlog)
- **#17** — `fix_guidance` longo em terminal estreito. Fix proper exigiria
  schema change (`fix_guidance_short` + `fix_guidance_long`); usuarios podem
  contornar com `--format md` que nao trunca. Out-of-scope.
- **#20** — encoding misto nas skills (`execucao` vs `execução`). Mass edit
  cosmetico; legado de geracao via terminal Windows cp1252. Não bloqueia uso.

### Notes
- **Backlog QA round 2 reduzido de 11 → 2 deferidos**. Resto fechado em
  v0.3.21 + v0.3.22. Total: round 1 (15) + round 2 (20) = 35 achados,
  33 endereçados ao longo de 9 releases (v0.3.14-v0.3.22).
- Re-ingest recomendado pra usuarios existentes (`ingest --no-incremental`)
  pra ganhar SEC-003 expandido + #8 do PARAMIXB.

## [0.3.21] - 2026-05-14

### Bug pack — fecha 3 itens técnicos médios do `gaps/PLUGADVPL_QA_REPORT_V2.md` que sobraram após v0.3.20. Foco: corrigir false negatives em SEC-004 + numero correto no summary do `ingest-sx` + nomenclatura útil pros métodos REST do WSRESTFUL no call graph.

### Fixed
- **#15 — `ingest-sx` per_table mostra numero CORRETO (distinct, não inserted)**.
  Antes: `counters["per_table"][table] = inserted` (= len(rows) processadas
  do CSV). Agora: `= distinct` (= rows que sobreviveram após PK dedup). Caso
  real cliente: summary mostrava 58.796 consultas, sx-status mostrava 46.669
  — discrepância sumiu. WARN em stderr da v0.3.14 continua mostrando o
  numero CSV original (`{csv_rows} linhas CSV → {distinct} distintas`)
  pra rastreabilidade.
- **#4 — SEC-004 RpcSetEnv aceita variável nos slots emp/fil**. Antes o
  regex exigia string literal nos 4 slots (`RpcSetEnv("01","01","admin","totvs",...)`).
  O caso real mais comum é emp/fil virem de parâmetro/argv (`cEmp`, `cFil`)
  com user/pwd hardcoded — exatamente o leak crítico. Novo helper
  `_SEC004_ARG_RE = r"(?:\\w+|['\"][^'\"]*['\"])"` aceita variável OU literal
  nos slots 1+2; user/pwd continuam exigindo literal não-vazio.
- **#13/#14 — WSRESTFUL verb-only popula `funcoes` com nome qualificado**.
  Antes: `WSMETHOD GET WSSERVICE PortaldeViagem` virava `funcao={"nome":"GET"}` —
  nome ambíguo, colidia entre classes. Cascata: `find function GET` retornava
  todos GETs misturados; chunks indexados ficavam sem distinção; call graph
  dos métodos REST corrompia. Agora: novo cross-check com
  `_WSMETHOD_REST_BARE_RE` (já existia da v0.3.16) re-nomeia matches
  verb-only pra `<Classe>.<VERB>` (ex: `PortaldeViagem.GET`,
  `PortaldeViagem.POST`) + popula `classe`. Métodos com nome explícito
  (`WSMETHOD GET clientes WSSERVICE Vendas`) continuam intactos.

### Tests
- `tests/integration/test_ingest_sx.py::TestIngestSx::test_ingest_sx_per_table_reflects_db_count_not_csv_count` (#15 RED→GREEN).
- `tests/unit/test_lint.py::TestSEC004HardcodedCreds::test_positive_rpcsetenv_var_emp_fil_literal_user_pwd` (#4 RED→GREEN).
- `tests/unit/test_parser.py::TestParseSource::test_wsrestful_methods_appear_in_funcoes` (#13/#14 RED→GREEN).
- 339 testes verde (era 336).

### Notes
- **Backlog QA round 2 reduzido**: dos 15 itens menores que sobraram após
  v0.3.20, fechamos 4 (#4, #13, #14, #15). Continuam pendentes (todos baixos):
  #3 (SEC-004 PASSWORD com `;` continuação multiline), #5 (SEC-003 cobre só
  A1_*/RA_* — falta A2_*/RH_*), #6 (gatilho upstream traversal), #7 (impacto
  fontes sem boundary docs), #8 (PARAMIXB busca em raw), #11 (skills
  arch/callers não documentam novas flags), #16 (sx_status schema instável),
  #17 (fix_guidance longo), #18 (hint só globais), #19 (callees nesting test),
  #20 (encoding skills misto).
- **WSRESTFUL ricos**: `find function PortaldeViagem.GET` agora funciona,
  `callees PortaldeViagem.GET` retorna chamadas internas (resolvendo via
  v0.3.15 chunk parent), `callers PortaldeViagem.GET` mostra quem invoca
  (raro em REST puro — geralmente vazio, é endpoint exposto).
- **Re-ingest recomendado**: `plugadvpl ingest --no-incremental` aplica
  fix #15 (per_table correto) + fix #13/#14 (nomes WSRESTFUL ricos) em
  fontes ja indexados. SEC-004 #4 só dispara em ingest novo / re-ingest.

## [0.3.20] - 2026-05-14

### SEC-003 false positives + skill drift sync — fecha os 5 itens de maior prioridade do `gaps/PLUGADVPL_QA_REPORT_V2.md` (round 2 do QA externo). Trinca crítica: `Help` interpretado como log + regex de variável PII casando palavras PT-BR comuns + skills com contagens/recomendações desatualizadas.

### Fixed
- **#1 (alta) — `Help` removido de `_SEC003_LOG_FUNCS_RE`**. `Help()` em
  ADVPL é diálogo modal universal (validação de campo X3_VLDUSER, X7_REGRA),
  equivalente a `MsgInfo` que já era excluída. As próprias skills do plugin
  documentam Help como UI. Antes do fix, qualquer fonte MVC real com
  `Help( ,, 'Erro',, 'Cliente ' + cNome, 1, 0)` disparava SEC-003 — false
  positive massivo. +1 teste negativo `test_negative_help_is_ui_not_log`.
- **#2 (alta) — `_SEC003_PII_VAR_RE` não casa mais palavras PT-BR comuns**.
  As variantes curtas `Pass`/`Pin`/`Card`/`Pwd`/`Rg` casavam `cPassagem`
  (turismo), `cPintar` (manufatura), `cCardapio` (food-service), etc.
  Reescrita em duas alternations:
  - **Forma longa** (low FP): `Cpf|Cnpj|Senha|Password|Token|Cartao|Cvv|ApiKey|Api_Key|Secret`
    — match com prefixo Hungarian opcional + sufixo livre.
  - **Forma curta** (alta ambiguidade PT-BR): `cPwd|cRg|cPin|cCard|cPass`
    — exige prefixo `c` literal + boundary final (sem sufixo). Trade-off:
    `nPin` num projeto não dispara, mas preferimos miss a gritar massivamente.
  
  +3 testes negativos (`test_negative_var_passagem_not_password`,
  `test_negative_var_pintar_not_pin`, `test_negative_var_cardapio_not_card`)
  + 1 positivo de regressão (`test_positive_password_long_form_still_works`).

### Changed
- **#9 — Skill `advpl-code-review` sincronizada com v0.3.19**:
  - Frontmatter: `24 → 31` regras, `13 → 20` single-file.
  - Linha 7: `29 são detectadas → 31 são detectadas`.
  - Header tabela "Single-file (18) → (20)".
  - "lint roda as 13 → 20 regras single-file" (2 ocorrências).
  - Bloco "Info / Checklist mental (não detectadas automaticamente)" reescrito:
    estava listando 9 itens, mas 8 deles têm detector ativo (BP-006, BP-008,
    SEC-003, SEC-004, SEC-005, PERF-004, PERF-005, MOD-004). Reduzido para
    apenas os 4 genuinamente `planned` (BP-007, BP-002b, MOD-003, PERF-006)
    + nota explícita que os outros são automatizados pelo linter.
- **#10 — Skill `help` lista os 19 subcomandos** (antes listava 13).
  Reorganizada em "Universo 1 — fontes (14 cmds)" + "Universo 2 — Dicionário
  SX (5 cmds, v0.3.0+)". Cada subcomando ganha tag das features novas
  (`is_self_call` v0.3.18+, `tabelas_via_execauto` v0.3.18+, `--cross-file`,
  word boundary v0.3.17+, etc.).
- **#12 — Skill `status` recomenda `--no-incremental` pós-upgrade**, não
  `--incremental`. Estava conflitando diretamente com a "Pegadinha do
  --incremental" da skill `ingest`. Adicionada referência cruzada.
- 18 skills bumpadas `@0.3.19` → `@0.3.20`.

### Tests
- 5 testes novos em `TestSEC003PIIInLogs` (4 negativos + 1 positivo de
  regressão). Suite total: 336 verde (era 331).

### Notes
- **Backlog QA round 2**: ficaram 15 itens menores (severidade baixa-média)
  pra v0.3.21+. Top entre esses: #4 (RpcSetEnv com variável nos slots emp/fil),
  #6 (gatilho upstream traversal), #15 (ingest-sx per_table inflado),
  #13/#14 (WSRESTFUL verb-only não vira `funcoes`).
- **Para usuários existentes**: `plugadvpl ingest --no-incremental` recomendado
  pra reprocessar com SEC-003 ajustado. `lookup_bundle_hash` mudou (descrição
  do JSON inalterada mas regex do detector mudou — não dispara warning
  automático da v0.3.13). Re-ingest manual elimina FPs de `Help`/PT-BR words.

## [0.3.19] - 2026-05-14

### Security pack — fecha a categoria SEC. Implementa as 2 ultimas regras `planned` da categoria security: SEC-003 (PII em logs, LGPD) + SEC-004 (credenciais hardcoded). Pesquisa-first contra TDN + comunidade ADVPL (Terminal de Informação, BlackTDN, MasterAdvPL) confirmou padrões antes do detector — evita shipping de regra ruidosa.

### Added
- **SEC-004 (warning) — credenciais hardcoded em código fonte**. Detecta 4
  padrões canônicos de leak via git:
  - `RpcSetEnv("emp", "fil", "USER", "PWD", ...)` com user E pwd literais
    não-vazios (slots 3+4). Vazio = "usar admin default" por convenção,
    não é leak — não sinaliza.
  - `PREPARE ENVIRONMENT ... PASSWORD '<literal>'` (UDC `tbiconn.ch`).
  - `oMail:SMTPAuth("user","pwd")` ou `MailAuth("user","pwd")` literais.
  - `Encode64("user:pwd")` (Basic Auth construído inline).
  
  Não sinaliza leitura segura via `SuperGetMV`/`GetNewPar`/`GetMV` (padrão
  recomendado TOTVS). Comentários são limpos pelo `strip_advpl`.
  Sugestão de fix orienta MV_* em SX6 (e cita `MV_RELAUSR/MV_RELAPSW` para
  SMTP especificamente).
- **SEC-003 (warning) — PII / dados sensíveis em logs (LGPD)**. Detecta 4
  sinais em chamadas a `ConOut`/`FwLogMsg`/`MsgLog`/`LogMsg`/`UserException`/`Help`:
  - Variável com nome PII (`cCpf`, `cCnpj`, `cSenha`, `cPwd`, `cToken`,
    `cCard`, `cRg`, `cApiKey`, `cSecret`, ...).
  - Campo SX3 conhecido sensível: `A1_CGC`/`A1_CPF`/`A1_NOME`/`A1_NREDUZ`/
    `A1_EMAIL`/`A1_TEL`/`A1_END` (clientes), `RA_CIC`/`RA_RG`/`RA_NOMECMP`/
    `RA_EMAIL`/`RA_NUMCP` (funcionários).
  - CPF formatado literal (`999.999.999-99`).
  - CNPJ formatado literal (`99.999.999/9999-99`).
  
  **Não sinaliza** `MsgInfo`/`MsgAlert`/`MsgBox`/`Aviso` (UI modal, não vai
  pro log do servidor — exposição diferente, fora do escopo SEC-003). Detector
  usa 2 variantes do source: com strings (pra pegar literal CPF/CNPJ) e sem
  strings (pra pegar nome de variável sem confundir com label `"CPF inválido"`).
- Helpers em `lint.py`: `_SEC003_LOG_FUNCS_RE`, `_SEC003_PII_VAR_RE`,
  `_SEC003_PII_FIELDS_RE`, `_SEC003_CPF_LITERAL_RE`, `_SEC003_CNPJ_LITERAL_RE`,
  `_SEC004_RPCSETENV_LITERAL_RE`, `_SEC004_PREPARE_ENV_RE`,
  `_SEC004_SMTPAUTH_RE`, `_SEC004_BASIC_AUTH_RE`.

### Changed
- Catálogo `lookups/lint_rules.json`:
  - SEC-003: `status="planned"` → `"active"` + `impl_function="_check_sec003_pii_in_logs"`.
    Descrição expandida com lista completa dos 4 sinais detectados + regras
    de exclusão (não sinaliza UI).
  - SEC-004: `status="planned"` → `"active"` + `impl_function="_check_sec004_hardcoded_creds"`.
    Descrição expandida com 4 padrões canônicos detectados + casos
    explicitamente excluídos (SuperGetMV, vazio = admin default, comentários).
- Skill `advpl-code-review`:
  - Tabela "Single-file" ganhou linhas SEC-003 e SEC-004 com exemplos.
  - Lista "regras planned" reduzida de 6 → 4 (sobram BP-002b, BP-007,
    PERF-006, MOD-003).
- 18 skills bumpadas `@0.3.18` → `@0.3.19`.

### Tests
- `tests/unit/test_lint.py::TestSEC004HardcodedCreds`: 8 testes (5 positivos
  + 3 negativos cobrindo SuperGetMV, vazio, comentário).
- `tests/unit/test_lint.py::TestSEC003PIIInLogs`: 7 testes (4 positivos
  + 3 negativos cobrindo log seguro, MsgBox UI, label literal).
- `test_active_count_matches_impl` (catalog consistency) detectou o gap
  durante o release — exatamente o propósito do guard.
- 331 testes verde (era 316).

### Notes
- **Categoria SEC do catálogo agora 100% ativa**: SEC-001..SEC-005 todas
  com detector. Sobram 4 planned (BP-002b, BP-007, PERF-006, MOD-003) —
  todas info/warning de menor impacto.
- Pesquisa-first metodologia (mesmo padrão da v0.3.8 MOD-004): subagent
  consultou TDN oficial + 15 fontes da comunidade ADVPL antes do detector.
  Isso evitou shipping de regra over-aggressive (ex: marcar
  `Authorization: Bearer xxx` em todo header REST literal — ficou de fora
  por gerar muitos false positives em código de teste).
- **Para usuários existentes**: `plugadvpl ingest --no-incremental` recomendado
  pra reprocessar fontes ja indexados com as 2 regras novas (lookup_bundle_hash
  mudou — warning automático da v0.3.13 vai disparar no próximo `ingest --incremental`).

## [0.3.18] - 2026-05-14

### Polish pack — fecha os 3 ultimos achados do `gaps/PLUGADVPL_QA_REPORT.md`. Com este release o backlog do QA inicial chega a zero — sobram apenas os achados ja resolvidos em v0.3.14-v0.3.17.

### Fixed
- **#9 — `lint` retornava findings duplicados**. BP-001 (RecLock sem
  MsUnlock) reportava o mesmo RecLock 2x quando vinha em forma alias
  (`<alias>->(RecLock(...))`) — casava com AMBOS regexes (`_RECLOCK_OPEN_RE`
  pra literal + `_RECLOCK_VIA_ALIAS_RE` pra alias). Fix: dedup por **linha**
  no detector antes de contar opens (`opens_by_line` dict). Mesma linha
  agora conta como 1 open mesmo casando 2 regexes.

### Added
- **#11 — `arch` expoe `tabelas_via_execauto: bool`**: quando o fonte tem
  capability `EXEC_AUTO_CALLER`, a flag fica True sinalizando que as
  listas `tabelas_read/write/reclock` podem estar incompletas (analise
  estatica nao expande a rotina chamada via MsExecAuto). Caller deve
  rodar `tables` na rotina alvo pra cobertura completa.
- **#12 — `callers` expoe `is_self_call: bool`** em cada row. Self-call
  quando `funcao_origem == nome` OU `basename(arquivo_origem) == nome`.
  Util pra filtrar self-references (FwLoadModel('X') de dentro de X.prw
  contava como caller externo no output).

### Tests
- `tests/integration/test_cli.py::TestLint`: +4 testes
  (`test_lint_findings_no_duplicates_alias_reclock` com fixture
  `reclock_alias_dup_trigger.prw`; `test_arch_flags_tabelas_via_execauto`;
  `test_arch_no_execauto_flag_when_no_capability`;
  `test_callers_flags_is_self_call`).
- 316 testes verde (era 312).

### Notes
- **QA report inicial agora 100% endereçado**:
  - Resolvidos em v0.3.14: #14 (SXG mislabel), #15 (consultas Δ).
  - Resolvidos em v0.3.15: #1 (CLAUDE.md fragment), #2 (--limit hint),
    #4 (gatilho destino), #8 (callees broken), #13 (project_root).
  - Resolvidos em v0.3.16: #5/#7 (WSRESTFUL), #6/#10 (PE canonico).
  - Resolvidos em v0.3.17: #3 (impacto boundary).
  - Resolvidos em v0.3.18: #9 (lint dups), #11 (execauto flag), #12
    (self-call flag).
- Próximo grande tema natural: v0.4.0 Universo 3 (Rastreabilidade) — ou
  promover mais regras planned restantes (SEC-004 hardcoded creds,
  SEC-003 PII em logs, BP-007 Protheus.doc, etc.).

## [0.3.17] - 2026-05-14

### Impacto preciso — fix #3 do `gaps/PLUGADVPL_QA_REPORT.md`. `plugadvpl impacto A1_COD` retornava >100KB de output em campo curto/comum, com gatilhos de campos cujo nome apenas CONTEM 'A1_COD' como substring (`BA1_CODEMP`, `BA1_CODINT`, `DA1_CODPRO`, `A1_CODSEG`, etc.). Para campos de tabelas standard (SA1, SB1, SC5...) o comando ficava praticamente inutilizavel — caso real reportado: `A1_COD` retornava ~150 resultados, ~95% falsos positivos.

### Fixed
- **#3 — `impacto` agora usa word boundary (`\\b<termo>\\b`)**. SQL continua
  fazendo prefiltro com `LIKE '%X%'` (cheap, narrows candidates) e Python
  re-valida cada match com regex `\\b<TERMO>\\b` antes de devolver. Falsos
  positivos sao silenciosamente descartados.
  - **ADVPL-aware**: `\\b` no Python NAO trata `_` como boundary (`_` eh
    `\\w`), entao `\\bA1_COD\\b` NAO casa em `BA1_COD` (B+A1 = continuacao
    `\\w`) nem em `A1_CODFAT` (CO+DF = continuacao `\\w`). Comportamento
    exato pra nomes de campo Protheus tipo `A1_COD`.
  - Aplicado em 3 lugares de `query.py`:
    - `_impacto_sx3` — campos com VALID/VLDUSER/WHEN/INIT referenciando o termo.
    - `_impacto_sx7_chain` — gatilhos com REGRA/CONDICAO referenciando o termo.
    - `_impacto_sx1` — perguntas com VALIDACAO/CONTEUDO_PADRAO referenciando.
  - Match exato em `campo_origem` SX7 (origem literal) continua aceito sempre.
- Helper novo `_word_boundary_re(termo)` em `query.py` — centraliza a logica
  pra uso futuro (qualquer query que precise de match exato em texto).

### Tests
- `tests/integration/test_ingest_sx.py::TestImpactoCommand::test_impacto_uses_word_boundary_no_substring_false_positives`
  (RED→GREEN). Fixture com 3 gatilhos: 1 real (`A1_COD->A1_NREDUZ`) +
  2 substring-fakes (`BA1_CODEMP`, `A1_CODFAT`). Antes do fix: os 3
  apareciam. Depois: so o real.
- 312 testes verde (era 311).

### Notes
- **Impacto em fontes (`fonte_chunks.content`) NAO foi alterado** — busca
  em codigo eh diferente: voce TAMBEM quer pegar `A1_COD` quando aparece
  como parte de uma string maior tipo `"SA1->A1_COD"`. Limitar a busca em
  conteudo de fonte com boundary derrubaria matches legitimos. So eh
  problema em campos textuais SX (regra/validacao/init), onde o termo eh
  um nome de campo e o boundary preserva a semantica esperada.
- **Backlog do QA report ainda restando**:
  - #9 `lint` retorna findings duplicados (UNIQUE constraint).
  - #11 flag `tabelas_via_execauto` quando `EXEC_AUTO_CALLER` set.
  - #12 flag `is_self_call` em `callers`.

## [0.3.16] - 2026-05-14

### Parser heuristics — fixes #5/#7 + #6/#10 do `gaps/PLUGADVPL_QA_REPORT.md`. WSRESTFUL classico nao virava webservice; PE canonico TOTVS (ANCTB102GR) nao era detectado. Ambos sao misclassificacoes silenciosas — usuario/IA que filtrasse "todos os webservices" ou "todos os PEs" perdia esses casos.

### Fixed
- **#5/#7 — WSRESTFUL classico classificado como webservice**: o parser
  capturava `WSSERVICE <Name>` mas nao `WSRESTFUL <Name>`. Classes
  REST puras (com `WSMETHOD GET WSSERVICE <Class>` em vez de
  `WSMETHOD GET <name> WSSERVICE <Class>`) caiam pra
  `source_type=user_function` e capability `WS-REST` ficava ausente.
  Agora:
  - Novo regex `_WSRESTFUL_HEADER_RE` captura `WSRESTFUL <Name>` e
    popula `ws_structures.ws_restfuls` (lista paralela a `ws_services`).
  - Novo regex `_WSMETHOD_REST_BARE_RE` captura `WSMETHOD <verb>
    WSSERVICE <Class>` (verb-only, padrao tipico de impl WSRESTFUL)
    e adiciona como `rest_endpoint` com `annotation_style='wsmethod_restful'`.
  - `_derive_capabilities` adiciona `WS-REST` quando `ws_restfuls` ou
    style `wsmethod_restful` aparece.
  - `_derive_source_type` agora considera `ws_restfuls` na decisao
    "eh webservice?".

- **#6/#10 — PE canonico TOTVS detectado via PARAMIXB**: o regex
  `_PE_NAME_RE` (`^[A-Z]{2,4}\\d{2,4}[A-Z_]{2,}$`) catura `MT100GRV`
  / `MA440PGN` mas nao `ANCTB102GR` (estrutura letras-letras-digitos-
  letras). Heuristica nova: User Function cujo corpo usa `PARAMIXB[N]`
  eh PE — independente do nome. PE Protheus recebe parametros via
  `PARAMIXB` (array global), entao falso-positivo eh minimo.
  - Novo helper `_derive_pontos_entrada(funcoes, content_lines)` em
    `parser.py` combina os 2 sinais (regex de nome + body scan).
  - `parse_source` agora popula `result["pontos_entrada"]` direto
    (antes vivia so em `ingest.py`).
  - `ingest.py` consome `parsed["pontos_entrada"]` em vez de recomputar.
  - `_derive_capabilities` usa `pontos_entrada` pra decidir capability
    `PE`; mantem fallback regex pra back-compat de callers que passem
    parsed dict sem `pontos_entrada` populado.

### Tests
- `tests/unit/test_parser.py::TestParseSource::test_wsrestful_classic_classified_as_webservice` (#5/#7 RED→GREEN).
- `tests/unit/test_parser.py::TestParseSource::test_pe_canonical_paramixb_detected` (#6/#10 RED→GREEN).
- Fixtures novos: `cli/tests/fixtures/synthetic/ws_restful_classic.prw` (WSRESTFUL com 2 endpoints) + `pe_paramixb.prw` (ANCTB102GR canonico usando PARAMIXB[1..5]).
- 311 testes verde (era 309).

### Notes
- **Nao incluido neste release** (ainda no backlog do QA report):
  - #3 `impacto` substring sem boundary.
  - #9 `lint` retorna findings duplicados.
  - #11 flag `tabelas_via_execauto`.
  - #12 flag `is_self_call` em callers.
- Usuarios existentes precisam re-rodar `plugadvpl ingest --no-incremental`
  para que `pontos_entrada` e `capabilities`/`source_type` sejam recalculados
  nos arquivos ja indexados (lookup_bundle_hash nao mudou — mudanca eh so
  no codigo, entao warning automatico da v0.3.13 nao dispara).

## [0.3.15] - 2026-05-14

### Correctness pack — 5 fixes derivados do `gaps/PLUGADVPL_QA_REPORT.md` (relatorio QA exploratorio rodado num projeto real Marfrig com 1.992 fontes + dicionario SX completo, 421k registros). Foco nos achados de severidade alta/critica que **bugs reais** com fix surgical (parser heuristicas e melhorias de UX maiores ficam pra v0.3.16+).

### Fixed
- **#8 (CRITICO) — `callees` totalmente quebrado**: `chamadas_funcao.funcao_origem`
  estava sendo gravado como `""` em TODOS os 30k+ registros (`# best-effort vazio
  no MVP` esquecido). Resultado: `plugadvpl callees <funcao>` retornava vazio
  pra qualquer nome de funcao. Agora resolvemos via lookup nos chunks
  (linha_origem está dentro de quais [linha_inicio, linha_fim]?), escolhendo o
  chunk MAIS INTERNO em caso de nesting (Class > Method > Static).
- **#4 — `gatilho` ignorava destinos**: query era `WHERE upper(campo_origem) = ?`
  mas o help diz "originados/destinados". Campos que apenas RECEBEM gatilhos
  (chaves geradas) ficavam invisiveis. Agora `WHERE upper(campo_origem) = ?
  OR upper(campo_destino) = ?`.
- **#13 — `ingest-sx` sobrescrevia `project_root`**: chamava
  `init_meta(project_root=str(csv_dir))` que upsertava o slot do `project_root`
  com o `csv_dir`. Sintoma observado: status mostrava `project_root=D:\...\CSV`
  em vez da raiz do projeto. Agora so chama `init_meta` se `project_root`
  ainda nao existir (caso usuario rode `ingest-sx` antes de `init`); caso
  contrario so atualiza `cli_version`. `sx_csv_dir` continua indo pro slot
  proprio.

### Added
- **#2 — Hint amigavel para flag global misplaced**: `plugadvpl status --limit 20`
  retornava `No such option: --limit` sem indicar que `--limit` eh global e
  precisa vir antes do subcomando. Agora `main()` detecta o caso heuristicamente
  (token em `_GLOBAL_FLAGS` apos o subcomando) e imprime apos o erro do click:
  ```
  Dica: '--limit' eh uma flag GLOBAL — vem ANTES do subcomando.
    Errado:  plugadvpl status --limit ...
    Correto: plugadvpl --limit ... status
  ```
- Set `_GLOBAL_FLAGS` em cli.py com as 12 flags do callback.

### Changed
- **#1 — Fragment `CLAUDE.md` desatualizado**: tabela de decisao listava modos
  do `grep` como `--fts`/`--literal`/`--identifier` (flags inexistentes — o
  correto eh `-m fts|literal|identifier`). Atualizado. Projetos novos veem
  versao certa via `plugadvpl init`; projetos existentes podem regenerar
  manualmente ou aguardar proximo init.

### Tests
- `tests/unit/test_query.py::TestCallees::test_callees_by_function_name_works` (#8 RED→GREEN).
- `tests/integration/test_ingest_sx.py::TestGatilhoCommand::test_gatilho_includes_destination_matches` (#4 RED→GREEN).
- `tests/integration/test_ingest_sx.py::TestIngestSx::test_ingest_sx_preserves_project_root` (#13 RED→GREEN).
- `tests/integration/test_cli.py::TestGlobalFlagPositioning::test_misplaced_global_flag_shows_helpful_hint` (#2 RED→GREEN).
- 309 testes verde (era 305).

### Notes
- **Nao incluido neste release** (planejado v0.3.16+):
  - #3 `impacto` substring sem boundary (false positives massivos com `A1_COD`).
  - #5/#7 WSRESTFUL nao classifica como `source_type=webservice`.
  - #6/#10 PE canonico (ANCTB102GR) nao detectado.
  - #9 `lint` retorna findings duplicados.
  - #11 flag `tabelas_via_execauto` quando `EXEC_AUTO_CALLER`.
  - #12 flag `is_self_call` em callers.
- **Dados existentes**: usuarios precisam re-rodar `plugadvpl ingest --no-incremental`
  para que `funcao_origem` seja populado nos registros existentes (warning
  da v0.3.13 ja avisa quando lookups mudam — neste caso lookups nao mudaram,
  so o codigo, entao precisa reingest manual).

## [0.3.14] - 2026-05-14

### SXB consultas — PK fix + dedup transparency. Quarta rodada do mesmo feedback de IA externa: dump real do cliente com 58.796 linhas em `sxb.csv` virava 46.669 no DB (perda de 20,6%) silenciosamente. Pesquisa contra TDN oficial confirmou: SXB tem 6 tipos (XB_TIPO 1-6: header/indice/permissao/coluna/retorno/filtro) e a PK natural inclui XB_TIPO.

### Fixed
- **SXB consultas: PK agora inclui `tipo`** (`migrations/004_consultas_pk_with_tipo.sql`).
  Antes: PK `(alias, sequencia, coluna)` fazia colidir as 6 paginas da consulta padrao
  (uma consulta full virava 1-2 rows). Agora: PK `(alias, tipo, sequencia, coluna)`
  espelha a chave natural TOTVS (TDN: `XB_FILIAL+XB_ALIAS+XB_TIPO+XB_SEQ+XB_COLUNA`;
  XB_FILIAL eh sempre vazio porque SXB eh X2_MODO='C').
  `SCHEMA_VERSION` bumpado `3 → 4`.

### Added
- **Aviso de SXG mal-rotulado** (`parse_sxg`): quando `sxg.csv` tem header `X3_*`
  (eh um dump SX3 disfarcado, comum em alguns exports do Configurador), o parser
  agora emite aviso amarelo em stderr explicando o problema em vez de pular silencioso.
  Mensagem orienta solicitar o SXG correto ao DBA.
- **Transparencia de dedup** (`ingest_sx`): para cada tabela, conta PKs distintas
  ANTES de `INSERT OR REPLACE` e compara com linhas processadas. Quando diff > 0,
  imprime aviso amarelo `WARN: tabela 'X': N linhas CSV -> M distintas apos PK dedup
  (D duplicada(s) na PK (...) foram sobrescrita(s))`. Util pra distinguir bug
  do parser (PK incompleta) de duplicatas reais no dump.
- **`_PK_COLS_BY_TABLE`** em `ingest_sx.py` — mapa tabela -> tupla de colunas PK
  (espelha as migrations 001 + 002 + 004). Usado pelo dedup detector.

### Changed
- Skill `ingest-sx`: nova secao "Avisos em stderr (v0.3.14)" documentando os 2
  diagnosticos novos + nota historica sobre o bug do SXB com cenario real
  (58k -> 46k) e link com TDN.
- 18 skills bumpadas `@0.3.13` -> `@0.3.14`.

### Tests
- `tests/integration/test_ingest_sx.py::TestIngestSx`: +4 testes
  (`test_sxb_consultas_preserves_all_tipos` — RED test do bug; `test_sxg_mislabel_emits_warning`;
  `test_ingest_sx_warns_when_dedup_lost_rows`; `test_ingest_sx_no_dedup_warning_when_clean`).
- Fixture `sxb_with_collisions.csv` — 6 linhas USRGRP, 1 por XB_TIPO, todas com
  mesmo (seq, coluna). Antes do fix: 2 rows sobreviviam. Depois: 6 (uma por tipo).
- 305 testes verde (era 301).

### Migration notes
- `apply_migrations` aplica `004_*.sql` automaticamente no primeiro `init`/`ingest`/`ingest-sx`
  apos upgrade. Dados existentes em `consultas` sao preservados via `INSERT SELECT`
  pra `consultas_new` antes do swap.
- **Usuarios existentes precisam re-rodar `ingest-sx`** para popular os ~20% de
  rows que estavam sendo silenciosamente sobrescritos antes. Trigger automatico:
  v0.3.13 ja avisa quando `lookup_bundle_hash` muda (`ingest --incremental` warning),
  e o `status` ainda mostra divergencia `runtime_version != plugadvpl_version`.

### Notes
- Foi a 4a iteracao do mesmo loop "IA externa testa, reporta sintoma, fix":
  v0.3.11 (truncamento + --json), v0.3.12 (runtime vs index version),
  v0.3.13 (--incremental sem reaplicar regras), v0.3.14 (SXB PK + dedup transparency).
- Pesquisa contra fontes oficiais (TDN paginas 22479685-22479707) confirmou a
  semantica dos 6 tipos antes do schema change — evitou shipping de fix incorreto.
- SX9/SXA/SX1 tambem tem dedup minor (321/85/13 rows) no dump do cliente, mas
  analise mostrou que sao duplicatas reais no SX (nao bug de PK). Sem migration
  pra eles; a transparencia nova ja loga quando aparecerem.

## [0.3.13] - 2026-05-14

### `--incremental` post-upgrade gotcha — terceiro round do mesmo feedback de IA externa. Apos `uv tool upgrade plugadvpl` + `ingest --incremental`, os arquivos pulados (mtime nao mudou) NAO eram re-avaliados contra regras de lint novas, mesmo apos o usuario seguir corretamente o fluxo recomendado pela v0.3.12. Resultado: `total_lint_findings` ficava frozen na versao antiga pra 99% do projeto sem aviso.

### Added
- **Warning de divergencia de lookups no `ingest --incremental`** — antes de
  `seed_lookups()` sobrescrever `meta.lookup_bundle_hash`, capturamos o valor
  anterior. Apos o ingest, se (1) modo `--incremental`, (2) `lookup_bundle_hash`
  mudou, e (3) houve `arquivos_skipped > 0`, imprime aviso amarelo em **stderr**:
  ```
  ⚠ Lookups (lint_rules/funcoes_restritas/...) mudaram desde o ultimo ingest.
    --incremental pulou N arquivo(s) cujo mtime nao mudou — esses NAO foram
    re-avaliados contra as regras novas.
    Para cobrir todo o codebase com as regras atualizadas, rode:
        plugadvpl ingest --no-incremental
  ```
  Suprimivel com `--quiet`.

### Changed
- `plugadvpl.ingest.ingest()` retorna 2 chaves novas no dict de counters:
  - `lookup_hash_changed: bool` — True se o hash do bundle de lookups mudou
    entre o ingest anterior e o atual.
  - `previous_lookup_hash: str | None` — hash gravado antes deste ingest
    (None se primeiro ingest no DB).
  Tipo do retorno mudou de `dict[str, int]` para `dict[str, Any]` (back-compat:
  todas as chaves originais continuam tendo valores int/str).
- Skill `ingest`: nova secao "Pegadinha do --incremental apos upgrade do
  binario" com cenario tipico (5 passos) + exemplo do warning. Renomeada
  `--no-incremental` na lista de opcoes pra `--incremental`/`--no-incremental`
  (mostra os dois lados do toggle).
- Skill `plugadvpl-index-usage`: secao "Versao do plugin" ganhou subsecao
  "Pegadinha do --incremental apos upgrade" com fluxo correto pos-upgrade
  (status → ingest --no-incremental → status novamente).
- 18 skills bumpadas `@0.3.12` → `@0.3.13`.

### Tests
- `tests/integration/test_cli.py::TestIngest`: +4 testes
  (`test_ingest_incremental_warns_when_lookups_changed`,
  `test_ingest_no_incremental_no_warning_even_with_hash_change`,
  `test_ingest_incremental_no_warning_when_hash_unchanged`,
  `test_ingest_warning_suppressed_by_quiet`). Cobrem matriz completa
  hash×modo×skipped + supressao por `--quiet`.
- 301 testes verde (era 297).

### Notes
- Decisao de design: NAO implementar auto-relint (re-aplicar lint sem
  re-parsear) nesta versao — seria mais ergonomico mas adiciona
  complexidade (nova flag, novo caminho, separar parser cache de lint
  cache). Avisar é suficiente; usuario decide se vale o tempo de
  `--no-incremental`. Re-avaliar se feedback de uso indicar que a dor
  recorrente justifica.
- O sinal usado (`lookup_bundle_hash`) ja existia desde antes —
  `seed_lookups` ja calculava SHA-256 do bundle. So precisava ser lido
  ANTES de `seed_lookups` sobrescrever pra detectar mudanca. Custo
  marginal: 1 query SQL extra por ingest.

## [0.3.12] - 2026-05-14

### Version-confusion fix — IA externa (mesmo feedback da v0.3.11) tinha rodado `uv tool upgrade` e ficou perdida porque `plugadvpl status` continuava mostrando a versão antiga (frozen no índice). Padrão git/hatch/dvc: mostrar **runtime + stored** lado a lado e avisar quando divergem.

### Added
- **`plugadvpl --version` / `-V`** (eager flag global no callback) — imprime
  versão do binário e sai. Padrão UNIX consagrado; antes só existia o
  subcomando `plugadvpl version`. Agora ambos funcionam.
- **`status` expõe `runtime_version`** — nova chave no output do query
  `plugadvpl.query.status()`, populada com `plugadvpl.__version__` do
  binário rodando AGORA. Convive com `plugadvpl_version` (frozen no
  init/ingest) e `cli_version` (frozen no último ingest).
- **Aviso de divergência** — quando `runtime_version != plugadvpl_version`,
  o `status` imprime em **stderr** (amarelo): `⚠ Índice criado com
  plugadvpl X.Y.Z, binário atual é A.B.C. Rode 'plugadvpl ingest
  --incremental' para atualizar o índice com regras/parsers da versão
  nova.` Suprimível com `--quiet`.

### Changed
- `plugadvpl.query.status(conn, project_root, runtime_version=None)` —
  novo parâmetro keyword opcional `runtime_version` (back-compat: chave
  vira `None` quando não passado, comportamento preservado).
- Skill `status`: tabela de campos do output, seção "Para descobrir qual
  versão está instalada" com 4 caminhos (`--version`, `version`, `status`,
  `uv tool list`) e o que cada um responde.
- Skill `help`: documenta `--version`/`-V` no topo das flags globais +
  seção "Qual versão está instalada?" com 3 caminhos.
- Skill `plugadvpl-index-usage`: nova seção "Versão do plugin — runtime
  vs índice" explicando o cenário do `uv tool upgrade` sem reingest.
- 18 skills bumpadas `@0.3.10`/`@0.3.11` → `@0.3.12`.

### Tests
- `tests/unit/test_query.py::TestStatus`: +2 testes
  (`test_status_runtime_version_field_when_passed`,
  `test_status_runtime_version_diverges_from_stored`).
- `tests/integration/test_cli.py::TestVersion`: +2 testes
  (`test_version_global_flag_long`, `test_version_global_flag_short`).
- `tests/integration/test_cli.py::TestStatus`: +4 testes
  (`test_status_includes_runtime_version`,
  `test_status_warns_when_binary_diverges_from_index`,
  `test_status_no_warning_when_versions_match`,
  `test_status_warning_suppressed_by_quiet`).
- 297 tests verde (eram 252+45 = 297; 8 novos compensam o que estava
  faltando vs o agregado anterior).

### Notes
- Decisão deliberada: NÃO reescrever `meta.plugadvpl_version` no
  `status` — manter como "versão que tocou o DB pela última vez" (resposta
  semântica da pergunta "esse índice é compatível?"). O `runtime_version`
  é a resposta complementar.
- Comportamento back-compat: caller que chame `status(conn, root)` sem
  passar `runtime_version` continua recebendo `runtime_version: None` na
  saída — testado em `test_status_runtime_version_field_when_passed`.

## [0.3.11] - 2026-05-14

### UX/docs release — feedback de outra IA usando o plugin revelou 2 fricções de discoverability + 1 maintenance gap. Sem mudança de código de produção.

### Fixed
- **18 skills com `uvx plugadvpl@0.3.1` hardcoded** — bumped pra `@0.3.10`
  em todas (`arch`, `find`, `lint`, `tables`, `callees`, `callers`,
  `doctor`, `gatilho`, `grep`, `help`, `impacto`, `ingest`, `ingest-sx`,
  `init`, `param`, `reindex`, `status`, `sx-status`). Estavam congeladas
  desde a v0.3.1 — usuários do plugin marketplace puxavam o catálogo
  sem regras BP-008/PERF-005/MOD-004/PERF-004/SEC-005.

### Added
- **Skill `plugadvpl-index-usage`**: nova seção "Output format —
  IMPORTANTE para agentes IA" documentando explicitamente as 3 opções
  (`table`/`md`/`json`), com tabela mostrando truncamento + lista de
  anti-padrões observados em sessões reais (tentar `--json` standalone,
  setar `$env:COLUMNS=400`, misturar shell PS/Bash). Recomenda
  `--format md` para Claude/agentes.
- **Skills com tabelas largas** (`arch`, `find`, `lint`, `tables`,
  `callees`, `callers`): callout no topo "Para agente IA: prefira
  `--format md`" — comando exemplo já vem com a flag para induzir cópia
  correta.
- **Skill `help`**: documentação completa das 8 flags globais com
  posicionamento (callback vem ANTES do subcomando) + aviso explícito
  "flags `--json`/`--vertical`/`--wide`/`--no-table` não existem; use
  `--format json` ou `--format md`".
- **CLAUDE.md fragment** (injetado por `/plugadvpl:init`): nova seção
  "Output format — IMPORTANTE para agentes IA" com mesma orientação
  + 3 anti-padrões. Projetos novos terão a guidance baked in.

### Notes
- Não há mudança no comportamento do CLI — todas as flags já existiam
  (`--format`, `--quiet`, `--compact`, `--no-next-steps`). Era só
  discoverability.
- Trigger: usuário compartilhou feedback de outra IA que rodou o plugin
  e identificou 3 fricções (truncamento Rich em terminal estreito,
  tentou `--json` em vez de `--format json`, misturou syntax PS/Bash em
  workaround). Análise: 1 era UX real (truncamento), 2 eram falta de
  documentação no contrato CLI.
- Não foram adicionadas novas flags (`--vertical`, `--wide`,
  `--no-truncate`) — `--format md` já resolve sem truncamento e é mais
  legível para LLM. Mantém superfície da API enxuta.

## [0.3.10] - 2026-05-13

### Audit release — sem regras novas; 4 gaps de qualidade identificados na revisão item-a-item de v0.3.4–v0.3.9 (com pesquisa em TDN/casos reais), todos corrigidos.

### Added
- **Test guard novo `test_all_check_functions_registered_in_orchestrator`**
  (8º teste em `test_lint_catalog_consistency.py`) — verifica que toda
  função `_check_*` extraída dos docstrings de `parsing/lint.py` aparece
  registrada em `lint_source()` (single-file via
  `findings.extend(_check_xxx(...))`) ou em `_CROSS_FILE_RULES` (cross-file
  SX-*). Fecha gap "F6" da auditoria: catalog dizia `active`, função
  existia no módulo, mas se ninguém chamasse no orchestrator a regra nunca
  disparava em runtime e nenhum teste pegava.
- **BP-008**: 7 reservadas adicionais cobertas (de 13 → **20**):
  - `dDataBase` (CRÍTICO — shadow quebra toda lógica de competência/data
    de movimento; achado mais grave da auditoria)
  - `INCLUI`, `ALTERA` (modo de operação em pontos de entrada/gatilhos)
  - `cFunBkp`, `cFunName` (introspecção de função corrente)
  - `lAutoErrNoFile` (controle de erro em rotinas auto)
  - `__Language` (idioma da sessão)

  +4 testes positivos novos (`test_positive_dDataBase_shadow`,
  `test_positive_INCLUI_ALTERA_shadow`, `test_positive_cFunName_cFunBkp_shadow`,
  `test_positive_lAutoErrNoFile_shadow`).
- **PERF-005**: detecta agora `LastRec()` além de `RecCount()`.
  TDN documenta `LastRec` como funcionalmente idêntico a `RecCount`
  (mesmo full-scan O(n)) — gap real da v0.3.6, qualquer codebase legacy
  que usa `LastRec() > 0` (padrão CA-Clipper/xBase histórico) escapava
  do detector. +3 testes (`test_positive_lastrec_for_existence`,
  `test_positive_lastrec_alias_call`, `test_negative_lastrec_business_limit`).
- **MOD-004**: detecta agora `MsNewGetDados` além de
  `AxCadastro`/`Modelo2`/`Modelo3`. TDN marca `MsNewGetDados` como
  **deprecated desde 12.1.17** — grid editável standalone substituído por
  `AddGrid` em ViewDef (MVC) ou `FWFormBrowse + AddGrid`. +2 testes
  (`test_positive_msnewgetdados_call`, `test_positive_msnewgetdados_assign`).

### Changed
- Catálogo `lookups/lint_rules.json`:
  - `BP-008.descricao`: lista expandida das 20 reservadas, com `dDataBase`
    explicitamente marcada como CRÍTICO.
  - `PERF-005.titulo` + `descricao`: cita `LastRec()` como alias de
    `RecCount()`.
  - `MOD-004.titulo` + `descricao`: cita `MsNewGetDados` como deprecated
    desde 12.1.17.
- Skill `advpl-code-review`:
  - Tabela "Single-file": entradas de BP-008/PERF-005/MOD-004 mencionam
    expansão em v0.3.10.
  - Sub-seção BP-008: lista das 20 reservadas agrupada por categoria
    (sessão/data/PE-state/backup) + nota sobre por que `dDataBase` é o
    shadow mais perigoso.
  - Sub-seção PERF-005: exemplo errado adicional com `LastRec() > 0`.
  - Sub-seção MOD-004: exemplo legacy adicional com `MsNewGetDados`.

### Tests
- 101 testes (era 93): 93 lint + 8 catalog consistency. Verde, zero
  regressão. `test_active_count_matches_impl` continua dinâmico — nunca
  precisa atualizar quando promove planned→active no futuro.

### Notes
- Catálogo continua em **24 active + 6 planned + 5 cross-file = 35**
  (auditoria não promoveu novas regras, só expandiu cobertura interna
  das 3 modificadas).
- Auditoria seguiu metodologia: pesquisa web (TDN, github
  nginformatica, Code Analysis docs) → identificação de gap real →
  TDD (red test) → fix → green test → catalog/skill updates.

## [0.3.9] - 2026-05-13

### Added
- **`PERF-004` (warning) implementado** — detector de string concat em loop
  (anti-pattern O(n²)). Antes catalogada como `planned`. Pesquisa contra
  NG Informática's [advpl-performance-research](https://github.com/nginformatica/advpl-performance-research)
  e [string-builder-advpl](https://github.com/nginformatica/string-builder-advpl)
  confirmou: caso real reportado de 1+ hora → 14-15s após otimização. Strings
  ADVPL imutáveis — cada `cVar += "x"` aloca string nova + copia anterior.
  
  Detecção em 2 passes:
  1. Encontra ranges (start, end) de cada loop body via stack-based parser
     (`While...EndDo`, `For...Next` — suporta loops aninhados)
  2. Em cada range, busca:
     - **Compound**: `cVar += ...` (variável c-prefix = string via hungarian)
     - **Long form**: `cVar := cVar + ...` (mesmo nome via regex backreference)
  
  Heurística hungarian notation distingue string concat (`cVar += "x"`) de
  numeric accumulator (`nTotal += 1`) — só flagga c-prefix.

  Sugestão de fix com 3 alternativas: array + FwArrayJoin/Array2String/
  ArrTokStr/CenArr2Str, FCreate+FWrite buffer, StringBuilder class custom.

- **`tests/unit/test_lint.py::TestPERF004StringConcatInLoop`** (11 asserts):
  6 positives (compound em While, em For, long form, nested loop, múltiplas
  concats, linha correta) + 5 negatives (numeric accumulator, fora de loop,
  string, comentário, long-form com vars diferentes). Validado 11/11 PASS,
  84/84 todos lint tests sem regressão.

### Changed
- **Catálogo `lint_rules.json`**: PERF-004 promovido de `status="planned"`
  para `status="active"` + `impl_function="_check_perf004_string_concat_in_loop"`.
  Total: **29 active + 6 planned = 35** (mantido).
- **Skill `advpl-code-review`**: PERF-004 movida pra "active" (18 single-file).
  Adicionado exemplo de fix com 3 alternativas (FwArrayJoin, FCreate buffer,
  StringBuilder).

## [0.3.8] - 2026-05-13

### Added
- **`MOD-004` (info) implementado** — detector de chamadas a UI legacy
  `AxCadastro` (Modelo 1), `Modelo2` (cabeçalho + grid lote) e `Modelo3`
  (pai/filho cabeçalho + itens). Antes catalogada como `planned`. Pesquisa
  contra TDN canônica confirmou as 3 assinaturas e o padrão de migração
  pra MVC moderno (FWMBrowse + MenuDef + ModelDef + ViewDef).
  
  Detecção:
  - Match `\b(AxCadastro|Modelo2|Modelo3)\s*\(` case-insensitive
  - Negative lookbehind pra `:`/`.` — exclui method calls (`obj:Modelo3()`)
  - Pula declarações de função homônima (`User Function AxCadastro()`)
  - Pula matches em strings literais e comentários
  - Pula nomes similares (`AxCadastrox`, `Modelo30`, `MyModelo2`)
  - Dedup por (linha, função) — múltiplas chamadas iguais na mesma linha = 1
  
  Sugestão de fix específica por função:
  - **AxCadastro**: migra pra Modelo 1 MVC com FWMBrowse + AddFields
  - **Modelo2**: migra pra MVC com AddFields master + AddGrid detail
  - **Modelo3**: migra pra MVC com AddFields cabeçalho + AddGrid itens + SetRelation pai/filho

- **`tests/unit/test_lint.py::TestMOD004LegacyCadastro`** (11 asserts):
  6 positives (cada uma das 3 funções, case-insensitive, múltiplas calls
  separadas, linha correta) + 5 negatives (string, comentário, definição
  homônima, similar-name, method call). Validado 11/11 PASS, 73/73 todos
  lint tests sem regressão.

### Changed
- **Catálogo `lint_rules.json`**: MOD-004 promovido de `status="planned"`
  para `status="active"` + `impl_function="_check_mod004_legacy_cadastro"`.
  Total: **28 active + 7 planned = 35** (mantido).
- **Skill `advpl-code-review`**: MOD-004 movida da tabela "planned" pra
  "active" (17 single-file agora). Adicionado exemplo de fix com 2 cenários
  completos de migração (AxCadastro→MVC Modelo 1, Modelo3→MVC pai/filho
  com SetRelation).

## [0.3.7] - 2026-05-13

### Added
- **`SEC-005` (critical) implementado** — detector de chamada de função
  TOTVS restrita. Antes catalogada como `planned`. Carrega o lookup
  `funcoes_restritas` (~194 entries: `StaticCall`, `PTInternal`, e ~192
  internas categorizadas por módulo) e cruza com chamadas de função no
  fonte. Detecção:
  - Match `<NAME>(...)` case-insensitive (ADVPL não diferencia caso)
  - Negative lookbehind pra `:`/`.` — exclui method calls (`obj:Name()`)
    e property access TLPP
  - Pula declarações de função homônima (`User Function StaticCall()`)
  - Pula matches em strings literais e comentários
  - Dedup por (linha, nome) — múltiplas chamadas iguais na mesma linha = 1 finding
  
  Sugestão de fix usa o campo `alternativa` do lookup quando disponível
  (ex: StaticCall sugere "User Function pública ou TLPP namespaced").

- **`tests/unit/test_lint.py::TestSEC005RestrictedFunctionCall`** (10 asserts):
  4 positives (StaticCall direto, case-insensitive, PTInternal interna,
  alternativa em sugestao_fix) + 6 negatives (User Function call, native
  function, function definition homônima, method call, em string, em
  comentário). Validado 10/10 PASS, 62/62 todos lint tests sem regressão.

### Changed
- **Catálogo `lint_rules.json`**: SEC-005 promovido de `status="planned"`
  para `status="active"` + `impl_function="_check_sec005_restricted_function_call"`.
  Total: **27 active + 8 planned = 35** (mantido).
- **Skill `advpl-code-review`**: SEC-005 movida da tabela "planned" pra
  "active" (16 single-file agora). Critical checklist inclui SEC-005.

## [0.3.6] - 2026-05-13

### Added
- **`PERF-005` (warning) implementado** — detector de `RecCount()` usado pra
  checar existência. Antes catalogada como `planned`. Detecta os padrões
  comuns: `RecCount() > 0`, `RecCount() >= 1`, `RecCount() != 0`,
  `RecCount() <> 0` (ADVPL legacy), incluindo variantes com alias-call
  (`SA1->(RecCount()) > 0`). NÃO sinaliza:
  - `RecCount() > 100` (limite de business intencional)
  - `nTotal := RecCount()` (apenas armazena, não checa existência)
  - `RecCount() > 0` dentro de string ou comentário
  
  Bug protegido: `RecCount()` força full scan da tabela inteira para contar
  todos os registros, mesmo quando você só quer saber se existe 1. Substituir
  por `!Eof()` após `DbSeek`/`DbGoTop` é O(1). Em SQL embarcado, `EXISTS`
  é melhor que `SELECT COUNT(*)`.
  
- **`tests/unit/test_lint.py::TestPERF005ReccountForExistence`** (10 asserts,
  TDD): 6 positives (gt-zero, gte-one, neq-zero, <>-legacy, alias-call,
  linha correta) + 4 negatives (limite real, atribuição, string, comentário).
  Validado 10/10 PASS, sem regressão (52/52 todos lint tests).

### Changed
- **Catálogo `lint_rules.json`**: PERF-005 promovido de `status="planned"`
  para `status="active"` + `impl_function="_check_perf005_reccount_for_existence"`.
  Total: **26 active + 9 planned = 35** (mantido).
- **Skill `advpl-code-review`**: PERF-005 movida da tabela "planned" pra
  "active" (15 single-file agora). Adicionado exemplo de fix com 4 cenários
  (errado, !Eof() simples, !alias->(Eof()), EXISTS em SQL).

## [0.3.5] - 2026-05-12

### Added
- **`BP-008` (critical) implementado** — detector de shadowing de variável
  reservada framework. Antes catalogada como `planned` (#1 follow-up). Agora
  detecta declarações `Local`/`Static`/`Private`/`Public` cujo nome bate
  (case-insensitive) com uma das **13 reservadas** Public criadas pelo
  framework Protheus: `cFilAnt`, `cEmpAnt`, `cUserName`, `cModulo`, `cTransac`,
  `nProgAnt`, `oMainWnd`, `__cInternet`, `nUsado`, `PARAMIXB`, `aRotina`,
  `lMsErroAuto`, `lMsHelpAuto`. Cobre declarações multi-var
  (`Local cVar1, cFilAnt, cVar2`) e TLPP-typed (`Local cFilAnt as character`).
  Bug protegido: programador declara `Local cFilAnt := ""` e depois usa
  `cFilAnt` achando que tem o valor da filial real, mas vê "" — ICMS errado,
  query cross-filial vazia, etc.
- **`tests/unit/test_lint.py::TestBP008ShadowedReserved`** (11 asserts,
  TDD red→green): 7 positives (cFilAnt simples, case-insensitive, multi-var,
  TLPP-typed, Public PARAMIXB, Private lMsErroAuto, linha correta) + 4
  negatives (similar-name `cFilAntiga`, reservada em string, reservada em
  comentário, uso correto sem declarar). Validado 11/11 PASS.

### Changed
- **Catálogo `lint_rules.json`**: BP-008 promovido de `status="planned"`
  para `status="active"` + `impl_function="_check_bp008_shadowed_reserved"`.
  Total: 25 active + 10 planned = 35 (mantido).
- **Test `test_lint_catalog_consistency`**: assert `n_active == 24`
  trocado por dinâmico `n_active == len(impl)` — futuras promoções
  planned→active não exigem update do test, só catálogo + impl.
- **Skill `advpl-code-review`**: BP-008 movida da tabela "planned" pra
  "active" (14 single-file agora). Adicionado exemplo de fix com 3 cenários
  (errado, correto com rename, correto sem declarar).
- **Skill `advpl-fundamentals`**: nota sobre BP-008 atualizada — agora
  detecta via `/plugadvpl:lint`, cobre 13 reservadas case-insensitive.

## [0.3.4] - 2026-05-12

### Fixed
- **[Issue #1](https://github.com/JoniPraia/plugadvpl/issues/1) — `lookups/lint_rules.json`
  alinhado com `parsing/lint.py`**. Antes (v0.3.0..v0.3.3), o catálogo descrevia
  comportamentos diferentes da implementação real para o mesmo `regra_id`:
  10 regras com severidade divergente, 15 com título/topic completamente outros
  (ex: catálogo dizia `BP-002` = "Local fora do header"; impl emitia `BP-002` =
  "BEGIN TRANSACTION sem END"). Resultado: usuário lia output do lint, buscava
  no catálogo e via descrição errada. Catálogo agora reflete a impl 1:1.
  Adicionados 2 campos novos: `status` (`active`/`planned`) e `impl_function`
  (nome da `_check_*` em `lint.py`). Migration 003 adiciona as colunas em
  `lint_rules` table.

### Added
- **Test de regressão** `tests/unit/test_lint_catalog_consistency.py` — 7 asserts
  que impedem novo drift catalog × impl. Falha o build se severidade, título,
  status, impl_function ou contagem de regras divergem.
- **Migration 003** `cli/plugadvpl/migrations/003_lint_rules_status.sql` —
  `ALTER TABLE lint_rules ADD COLUMN status, impl_function`. SCHEMA_VERSION
  bumped 2 → 3.

### Changed
- **24 active vs 11 planned** explicitamente declarado no catálogo:
  - **Active** (24): BP-001, BP-002, BP-003, BP-004, BP-005, BP-006,
    SEC-001, SEC-002, PERF-001, PERF-002, PERF-003, MOD-001, MOD-002,
    SX-001..SX-011.
  - **Planned** (11): BP-002b, BP-007, BP-008, SEC-003, SEC-004, SEC-005,
    PERF-004, PERF-005, PERF-006, MOD-003, MOD-004 — catalogadas como
    roadmap/checklist mental, ainda sem `_check_*` em `lint.py`.
- **Skill `advpl-code-review`** atualizada — drift footnote substituída por
  nota explicando o realinhamento + referência ao test guard.

### Changed
- **Skills overhaul completo** — todas as 16 knowledge skills (`plugadvpl-index-usage`,
  `advpl-fundamentals`, `advpl-code-review`, `advpl-mvc`, `advpl-mvc-avancado`,
  `advpl-embedded-sql`, `advpl-pontos-entrada`, `advpl-encoding`, `advpl-webservice`,
  `advpl-web`, `advpl-jobs-rpc`, `advpl-dicionario-sx`, `advpl-dicionario-sx-validacoes`,
  `advpl-matxfis`, `advpl-tlpp`, `advpl-advanced`) revisadas, pesquisadas
  contra TDN/TOTVS Central/blogs canônicos e atualizadas. Mudanças cross-cutting:
  - **Phantom command `/plugadvpl:sql` removido** de 3 skills (não existe no CLI).
  - **Nomes de tabela corrigidos** — `sources`→`fontes`, `simbolos`→`fonte_chunks`,
    `calls`→`chamadas_funcao`, `params`→`parametros_uso`, `sql_refs`→`sql_embedado`,
    `ws_services`/`ws_structures`→`rest_endpoints`/`http_calls`. `mvc_hooks` e
    `dictionary_sx` removidos (não existem no schema).
  - **bCommit/bTudoOk descontinuados** documentados — `advpl-mvc` agora lidera com
    `FWModelEvent` + `InstallEvent()` (3 momentos: BeforeTTS/InTTS/AfterTTS), padrão
    canônico TOTVS desde Protheus 12.1.17+.
  - **`FWMVCRotina` corrigido para `FWMVCRotAuto`** (canônico).
  - **Limite identificador clarificado** — `.prw`/`.prx` mantém legado 10 chars
    (truncamento silencioso causa bug `nTotalGeralAnual` ≡ `nTotalGeralMensal`);
    `.tlpp` libera 250 chars.
  - **TLPP default PRIVATE vs ADVPL PUBLIC** documentado — armadilha de port.
  - **Lint rules alinhados à impl real** (não ao catálogo) em `advpl-code-review`,
    `advpl-embedded-sql`, `advpl-jobs-rpc`, `advpl-advanced`. Discrepância
    documentada como [issue #1](https://github.com/JoniPraia/plugadvpl/issues/1)
    pra resolução em v0.3.4.
  - **Cross-refs `[[name]]`** entre skills — ~120 links bidirecionais.
  - **Sources sections** com ~80 referências externas verificáveis (TDN, TOTVS
    Central, Terminal de Informação, Medium, GitHub canônicos).

### Fixed
- **Skills com claims falsos sobre estrutura interna** — várias skills citavam
  tabelas SQLite que não existem no schema. Auditadas e corrigidas individualmente.

## [0.3.3] - 2026-05-12

### Added
- **Skill `advpl-refactoring`** — 6 padrões de refactor comuns em ADVPL/TLPP com
  before/after side-by-side: DbSeek em loop → SQL embarcado (anti-N+1), Posicione
  repetido → cache em variável, IFs hardcoded → SX5/SX6 ou User Function central,
  AxCadastro/Modelo2/3 → MVC, string concat em loop → array + FwArrayJoin,
  RecLock solto → Begin Transaction. Inclui "quando NÃO refatorar" pra cada padrão
  + workflow plugadvpl integrado.
- **Skill `advpl-debugging`** — top 30 erros comuns em produção Protheus com tabela
  rápida sintoma → causa raiz → diagnóstico → fix. Cobre `Variable does not exist`,
  `Type mismatch` pós-query, `RecLock failed`, `Index out of range`, browse vazio,
  MV_PAR não inicializado, Job não roda, REST 500, encoding bagunçado, perf
  subitamente péssima, gatilho SX7 não dispara, etc. Inclui métodos de debug manual
  (ConOut, MemoWrite, FwLogMsg, varInfo, aClone+diff) pra quando não dá pra
  anexar debugger gráfico.

### Changed
- **`install.ps1` detecta Python local existente** (via `py -3.12` / `py -3.11` que
  consulta o registro Windows, não cai na MS Store stub). Quando encontra, passa
  `--python <path>` pro `uv tool install`, evitando download de ~30MB de Python
  managed na primeira instalação (que silenciava por minutos sem progresso). Script
  agora tem 4 steps em vez de 3 (uv → Python → plugadvpl → done).
- **`release.yml`** agora anexa `.whl` + `.tar.gz` ao GitHub Release. Antes o job
  `github-release` só fazia `actions/checkout@v4` e tentava `files: cli/dist/*` que
  não existia naquele job — resultado: Release ficava vazio desde v0.3.0. Fix:
  `upload-artifact` no job `publish-pypi`, `download-artifact` no `github-release`.

## [0.3.2] - 2026-05-12

### Fixed
- **CRITICAL: `plugadvpl --help` crashava no Windows desde v0.3.0**. Docstrings
  dos comandos `impacto` e `gatilho` e o help de `ingest-sx` continham
  setas Unicode (`↔`, `→`) que não existem em cp1252. O console default
  do Windows (PS 5.1, cmd.exe) usa cp1252 e Python jogava
  `UnicodeEncodeError: 'charmap' codec can't encode character '↔'`
  no meio da renderização. Resultado: nenhum usuário Windows conseguia
  rodar `plugadvpl --help`, `plugadvpl impacto --help`, etc. Fix em duas
  camadas:
  - **App layer**: setas Unicode trocadas por ASCII (`<->`, `->`) em todas
    as strings user-facing (docstrings, help text, snippets de lint
    SX-002/SX-010, output do `impacto`/`gatilho`).
  - **I/O layer (defense)**: `main()` agora chama `sys.stdout/stderr.
    reconfigure(encoding='utf-8', errors='replace')` no Windows. Mesmo
    que algum char Unicode escape no futuro, vira `?` em vez de tombar.
- **`install.ps1` rodando via `irm | iex`** tinha o shebang `#!/usr/bin/env
  pwsh` interpretado como comando porque o arquivo estava UTF-8 BOM
  (introduzido no v0.3.1 pra PS 5.1 compat); o BOM sobrevivia ao
  Invoke-RestMethod e tornava o `#` da linha 1 invisível ao parser. Erro
  cosmético — install continuava — mas confundia quem rodasse manualmente.
  Fix: arquivo regravado UTF-8 **sem BOM**, mensagens ASCII-only
  (`não` → `nao`, em-dash → traço normal). Glifos `[OK]`/`[X]`/`[!]`
  preservados, formatação melhorada (`[OK] uv` em vez de `[OK]uv`).
- **`install.ps1` step [2/3] parecia travado** em primeira instalação.
  Adicionado aviso: "na primeira instalacao pode levar 1-3 min: uv baixa
  Python managed + deps. Sem barra de progresso ate terminar".

### Changed
- **Bump `uvx plugadvpl@0.3.0` → `@0.3.1`** em todos os assets do plugin
  (18 skills, 4 agents, hook `session-start.mjs`, `cli/README.md`). Sem
  este bump, slash commands depois do `/plugin marketplace update`
  continuavam invocando CLI v0.3.0 com o bug do `--help` e o SX-005
  quebrado (corrigidos no v0.3.1).

## [0.3.1] - 2026-05-12

### Added
- **4 slash commands faltantes do v0.3.0**: `/plugadvpl:ingest-sx`,
  `/plugadvpl:impacto`, `/plugadvpl:gatilho`, `/plugadvpl:sx-status`. Os
  comandos CLI já existiam desde v0.3.0, mas os wrappers de skill nunca
  foram criados — o README anunciava como `/plugadvpl:*` mas só funcionavam
  via CLI direta. Agora o plugin Claude Code expõe os 18 comandos completos.

### Changed
- **Bump `uvx plugadvpl@0.1.0` → `@0.3.0`** em todos os assets do plugin
  (14 skills antigas, 4 agents, hook `session-start.mjs`, `cli/README.md`).
  Como migration 002 introduziu o schema v2, qualquer slash command pinado
  em v0.1.0 contra um índice atual falharia com `OperationalError`. Specs
  históricos em `docs/superpowers/` ficaram intocados.

### Fixed
- **`install.ps1`** — compatibilidade real com Windows PowerShell 5.1.
  Três problemas atacados de uma vez: TLS default (1.0/1.1) que quebrava
  `irm https://astral.sh/uv/install.ps1`, glifos UTF-8 (`✓`/`✗`/`⚠`) que
  o parser PS 5.1 lia como cp1252 e travavam com `unexpected token`, e
  `2>&1` em executáveis nativos que disparavam `NativeCommandError` com
  `$ErrorActionPreference='Stop'`. PS 7+ continua funcionando sem mudança.
- **Lint cross-file `SX-005`** — estava silenciosamente quebrado desde
  v0.3.0. O segundo probe usava `LIMIT 1` dentro de cada perna de um
  `UNION ALL` (sintaxe inválida em SQLite), e o erro era engolido pelo
  `try/except sqlite3.OperationalError` em `lint_cross_file`. Nenhum
  finding SX-005 foi emitido em produção até este fix. De brinde, o
  N+1 query (1+N*2 LIKE scans) virou 3 queries agregadas com substring
  em memória — ~37 ms para 500 campos × 2.000 fontes em bench sintético.

## [0.3.0] - 2026-05-11

### Added — Universo 2: Dicionário SX

- **Migration 002** — 11 novas tabelas SQLite cobrindo todo o dicionário
  Protheus exportado em CSV: `tabelas` (SX2), `campos` (SX3), `indices` (SIX),
  `gatilhos` (SX7), `parametros` (SX6), `perguntas` (SX1), `tabelas_genericas`
  (SX5), `relacionamentos` (SX9), `pastas` (SXA), `consultas` (SXB),
  `grupos_campo` (SXG). Indexes específicos para cross-lookup em
  `validacao`/`vlduser`/`when_expr`/`inicializador`/`f3`.
- **Parser SX** (`plugadvpl/parsing/sx_csv.py`, ~440 linhas, type-hinted) —
  port do parser interno do autor (`parser_sx.py`, 872 linhas). Auto-detect
  encoding (cp1252/utf-8-sig), delimiter (vírgula/ponto-e-vírgula),
  conversão XLSX disfarçado de CSV, sanitização de surrogates Unicode.
  Filtra rows logicamente deletadas (`D_E_L_E_T_ = '*'`).
- **Pipeline** `plugadvpl/ingest_sx.py` — orquestrador idempotente
  (`INSERT OR REPLACE`), batches de 1000 rows, tolerante a CSVs faltantes.
- **3 novos comandos CLI**:
  - `plugadvpl ingest-sx <pasta-csv>` — popula o dicionário SX no índice.
  - `plugadvpl impacto <campo> [--depth 1..3]` — **killer feature**: cruza
    referências a um campo em fontes ↔ SX3 ↔ SX7 ↔ SX1, com cadeia de
    gatilhos configurável.
  - `plugadvpl gatilho <campo> [--depth 1..3]` — lista cadeia SX7
    origem → destino com BFS.
  - `plugadvpl sx-status` — counts por tabela do dicionário.
  - `plugadvpl lint --cross-file` — recalcula as 11 regras cross-file SX-***.
- **11 cross-file lint rules** SX-001..SX-011 (regra_id `SX-*`):
  X3_VALID com U_xxx não indexado, gatilho SX7 com destino inexistente em SX3,
  parâmetro MV_ nunca lido, pergunta SX1 nunca usada, campo custom sem
  referências, X3_VALID com SQL embarcado (BeginSql/TCQuery), função restrita
  TOTVS em validador, tabela compartilhada com xFilial em VALID, campo
  obrigatório com INIT vazio, gatilho Pesquisar sem SEEK, X3_F3 apontando
  para SXB inexistente.
- **Skill nova** `advpl-dicionario-sx-validacoes` — guia completo das
  expressões ADVPL embutidas no dicionário (X3_VALID/INIT/WHEN/VLDUSER,
  X7_REGRA/CONDIC/CHAVE, X1_VALID, X6_VALID/INIT) e workflow para
  análise de impacto.
- **Tests** — 11 novos integration tests cobrindo ingest-sx, impacto,
  gatilho, sx-status, lint --cross-file; 1 bench (~26ms para 11 CSVs
  sintéticos); 3 e2e_local contra `D:/Clientes/CSV` (gated por env var
  `PLUGADVPL_E2E_SX_DIR`).

### Changed
- `SCHEMA_VERSION` bumped to `"2"`.
- `plugin.json` / `marketplace.json` versão `0.3.0`.
- `plugadvpl --help` agora lista 18 subcomandos (14 + 4 novos).

### Notes
- Plugin agora ingere **apenas** o dicionário custom do cliente
  (`plugadvpl ingest-sx <pasta>`). Padrão TOTVS é ignorado por design
  (carga inútil para auditoria de customização).
- `sxg.csv` com header `X3_*` (export malformado) é silenciosamente
  pulado — apenas exports legítimos com header `XG_*` são ingeridos.

## [0.2.0] - 2026-05-11

### Added
- ~21k lines of curated ADVPL/TLPP reference documentation embedded as
  `reference.md` supporting files in 6 existing skills (fundamentals, mvc,
  embedded-sql, webservice, pontos-entrada, matxfis).
- 5 new knowledge skills:
  - `advpl-advanced` — threads, IPC, debug, OO em profundidade
  - `advpl-tlpp` — TLPP moderno (OO, namespaces, annotations)
  - `advpl-web` — interfaces web (Webex/HTML/WebExpress)
  - `advpl-dicionario-sx` — SX1/SX2/SX3/SX5/SX6/SX7/SIX/SXA/SXB
  - `advpl-mvc-avancado` — eventos, validações cruzadas, FWMVCRotAuto
- 7 production-grade code examples embedded in `skills/<x>/exemplos/`.

### Changed
- Plugin agora tem 30 skills total (15 knowledge + 14 command + 1 setup,
  contagem revisada após reorganização).

## [0.1.0] - 2026-05-11

### Added

- Plugin Claude Code com 24 skills (14 slash command + 10 thematic knowledge) + 4 agents + 1 SessionStart hook (Node.js)
- CLI Python `plugadvpl` (PyPI) com 14 subcomandos: `init`, `ingest`, `reindex`, `status`, `find`, `callers`, `callees`, `tables`, `param`, `arch`, `lint`, `doctor`, `grep`, `version`
- Schema SQLite com 22 tabelas + 2 FTS5 (external content + trigram) + 6 lookups pré-populados (279 funcoes_nativas, 194 funcoes_restritas, 24 lint_rules, 6 sql_macros, 8 modulos_erp, 15 pontos_entrada_padrao)
- Parser ADVPL/TLPP com strip-first pattern (ignora comentários `*`, `&&`, `//`, `/* */` + strings) e ~25 extractors module-level
- Lint engine com 13 regras single-file (BP/SEC/PERF/MOD) executadas durante ingest
- Ingest pipeline com paralelização adaptive (single-thread / ProcessPool com fork em Linux, spawn em macOS/Windows)
- CLAUDE.md fragment idempotente escrito pelo `init` (delimitado entre `<!-- BEGIN plugadvpl -->` ... `<!-- END plugadvpl -->`)
- CI matrix 3 OS × 3 Python + Trusted Publisher OIDC + github-action-benchmark
- 239 tests (unit + integration + 15 snapshots syrupy + 1 bench + 3 e2e_local)
- Docs: README, cli-reference, schema (Mermaid ER), architecture, CONTRIBUTING, SECURITY, CoC

### Known limitations

Veja [`docs/limitations.md`](docs/limitations.md) para a lista completa de gaps conhecidos
(parser, lint, schema, performance, plataforma) e o que NÃO está incluído neste MVP.
