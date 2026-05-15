# Roadmap

Visão pública do que vem no plugadvpl. Datas são estimativas — comunidade pode mudar prioridades.

## ✅ v0.1.x — Lançamento inicial (2026-05)

- Plugin Claude Code + CLI Python publicados (PyPI + marketplace GitHub)
- Schema SQLite com 22 tabelas + 2 FTS5 + 6 lookups embarcados
- Parser ADVPL/TLPP com strip-first, ~25 extractors
- 13 lint rules single-file (regex)
- 14 subcomandos CLI + slash commands
- 24 skills no plugin
- Onboarding via one-liner installer

## ✅ v0.2.0 — Biblioteca de referência embarcada (2026-05)

- ~23k linhas de docs ADVPL/TLPP integradas como `reference.md` em 6 skills
- 5 novas knowledge skills: `advpl-advanced`, `advpl-tlpp`, `advpl-web`,
  `advpl-dicionario-sx`, `advpl-mvc-avancado`
- 7 exemplos `.prw/.tlpp` de produção embarcados em `skills/<x>/exemplos/`
- CLAUDE.md fragment muito mais rico (tabela de decisão + workflow numerado)
- Skill `setup` com detecção de ambiente CLI vs VSCode

## ✅ v0.3.0 — Universo 2: Dicionário SX (2026-05)

[Milestone v0.3.0](https://github.com/JoniPraia/plugadvpl/milestone/1)

- Ingest do dicionário SX exportado da rotina de exportação do Protheus
  (CSV — Configurador → Misc → Exportar Dicionário). Apenas customizações
  do cliente; padrão TOTVS é ignorado por design.
- 11 tabelas populadas: `tabelas` (SX2), `campos` (SX3), `gatilhos` (SX7),
  `parametros` (SX6), `perguntas` (SX1), `consultas` (SXB), `pastas` (SXA),
  `relacionamentos` (SX9), `indices` (SIX), `tabelas_genericas` (SX5),
  `grupos_campo` (SXG).
- 3 comandos novos: `plugadvpl ingest-sx <pasta-csv>`, `plugadvpl impacto
  <campo> [--depth N]` (killer feature), `plugadvpl gatilho <campo>` +
  `plugadvpl sx-status` (auxiliar).
- 11 lint rules cross-file ativadas (`SX-001..SX-011`): valida que
  `X3_VALID`/`X7_REGRA` referenciam funções/campos/consultas que
  realmente existem.
- Skill nova: `advpl-dicionario-sx-validacoes` (X3_VALID, X3_INIT, X3_WHEN,
  X3_VLDUSER, X7_REGRA + workflow plugadvpl impacto).
- Parser portado de projeto interno do autor (872 linhas, MIT) — adaptado
  para plugadvpl removendo dependências SaaS.

## ✅ v0.4.x — Universo 3: Rastreabilidade (2026-05)

[Milestone v0.4.0](https://github.com/JoniPraia/plugadvpl/milestone/2)

Universo 3 entregue em 4 dot-releases consecutivas (3 features + polish):

### v0.4.0 — Feature A: execução não-direta
- Tabela `execution_triggers` (schema v5, migration 005)
- Detector `parsing/triggers.py` com 4 mecanismos canônicos TOTVS:
  - `workflow` — `TWFProcess`/`MsWorkflow`/`WFPrepEnv` (callbacks aprovação)
  - `schedule` — `Static Function SchedDef()` (configurador SIGACFG)
  - `job_standalone` — `Main Function` + `RpcSetEnv` (daemon ONSTART)
  - `mail_send` — `MailAuto`/`SEND MAIL` UDC/`TMailManager`
- Comando `workflow` + skill `/plugadvpl:workflow`

### v0.4.1 — Feature B: ExecAuto chain expansion
- Tabela `execauto_calls` (schema v6, migration 006)
- Catálogo `execauto_routines.json` (31 rotinas TOTVS — MATA*/FINA*/CTBA*/
  EECAP*/TMSA* com módulo + tabelas primárias/secundárias + URL fonte)
- Detector `parsing/execauto.py` resolve `MsExecAuto({|x,y,z| MATA410(x,y,z)},
  ...)` → rotina + tabelas inferidas + op_code (3/4/5 → inc/alt/exc)
- Comando `execauto` + enrichment de `arch` (campo
  `tabelas_via_execauto_resolvidas: list[str]`)

### v0.4.2 — Feature C: Protheus.doc agregada
- Tabela `protheus_docs` (schema v7, migration 007)
- Detector `parsing/protheus_doc.py` extrai 16 tags canônicas TOTVS
  (`@type`, `@author`, `@param`, `@return`, `@deprecated`, `@history`, etc)
  + `raw_tags` catch-all
- Inferência de módulo dual (path-based + routine-prefix)
- Comando `docs [modulo]` com 3 modos: lista, `--show <fn>` Markdown
  estruturado, `--orphans` (cross-ref BP-007)

### v0.4.3 — Polish pack
- Code review independente identificou 5 críticos com repro confirmado
  (todos corrigidos): callbacks misturados entre TWFProcess vizinhos,
  Protheus.doc fechando em `/*/` literal de @example, RpcSetEnv perdendo
  módulo com 6 args literais, bloco órfão puxando função distante,
  `infer_module` retornando SIGAEST silenciosamente
- 4 importantes endereçados: TMailManager solo, `--show` com homônimos,
  catálogo +6 rotinas + dup test, índices em `funcao` (migration 008)
- 489 testes verde (era 478)

## 🟡 v0.5.0 — Universo 4 (a definir)

Candidatos sob avaliação (priorizar conforme demanda da comunidade):

- **Qualidade & métricas** — complexidade ciclomática por função, hot-paths
  (top-N callers), distribuição de tamanho de fonte
- **Ownership analytics** — quem mantém o quê (cross-ref `git blame` × parser)
- **Cross-cliente diff** — comparar 2 índices (cliente A vs B) pra ver
  drift de customização sobre o mesmo módulo TOTVS
- **`expressoes_dicionario`** — parser de ADVPL embutido em SX (X3_VALID/
  INIT/WHEN/VLDUSER, X7_REGRA, X1_VALID, X6_VALID/INIT) extraindo
  user_funcs/funcs_padrao/tabelas_ref/campos_ref/parametros_ref
- **`trace <campo|funcao|tabela>`** — grafo completo cross-universo
  (rastreabilidade unificada)

## 🔵 Backlog (sem ETA)

- **`appserver.ini` parser** — ingest de `jobs` e `schedules`
- **`record_counts`** via conexão DBAccess (opcional, exige deps externas)
- **`menus`/`mpmenu_*`** — parser de menu Protheus
- **Embeddings opcionais** via `sqlite-vec` para queries semânticas
- **Skill `advpl-refactoring`** — 6 padrões de refactor com before/after
- **Skill `advpl-debugging`** — top 50 erros comuns + métodos de debug
- **Skill `advpl-testing-probat`** — framework ProBat para TLPP
- **LSP server** experimental (autocomplete em editores baseado no índice)
- **VSCode native extension** complementando o plugin Claude Code

## Como influenciar o roadmap

- **Sugerir feature**: abrir Issue com label `enhancement` no [GitHub](https://github.com/JoniPraia/plugadvpl/issues/new/choose)
- **Discussão pública**: [GitHub Discussions](https://github.com/JoniPraia/plugadvpl/discussions)
- **Pull request**: especialmente bem-vindas para parser, lint rules e skills temáticas

Comunidade ADVPL define o que vem primeiro.
