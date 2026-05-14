# Changelog

Todas as mudanças notáveis estão documentadas aqui, seguindo [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/).

## [Unreleased]

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
