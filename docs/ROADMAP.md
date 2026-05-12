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

## 🟡 v0.4.0 — Universo 3: Rastreabilidade unificada (planejado)

[Milestone v0.4.0](https://github.com/JoniPraia/plugadvpl/milestone/2)

- `expressoes_dicionario` — parser de expressões ADVPL embutidas em SX (X3_VALID,
  X3_INIT, X7_REGRA, X1_VALID) extraindo user_funcs, funcs_padrao, tabelas_ref,
  campos_ref, parametros_ref
- `rastreabilidade_unificada` — adjacência simétrica completa: dado um campo SX3,
  saber TODA cadeia de funções/gatilhos/PEs/SQL que tocam nele (e vice-versa)
- Comando novo: `plugadvpl trace <campo|funcao|tabela>` mostra grafo completo
- Comando novo: `plugadvpl impacto-completo <coisa>` com depth configurável

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
