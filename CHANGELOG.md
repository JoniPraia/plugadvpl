# Changelog

Todas as mudanças notáveis estão documentadas aqui, seguindo [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/).

## [Unreleased]

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
