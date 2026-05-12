-- Migration 003 — adiciona colunas status e impl_function em lint_rules.
--
-- Contexto: lookups/lint_rules.json passou a documentar (a) quais regras estão
-- realmente implementadas em parsing/lint.py vs. quais estão catalogadas-mas-não-
-- detectadas, e (b) qual função _check_<id>_<tópico> implementa cada regra ativa.
-- Antes desta migration o catálogo e a impl divergiam (issue #1) — após esta
-- migration o teste de regressão tests/integration/test_lint_catalog_consistency.py
-- protege contra novo drift.
--
-- ALTER TABLE ADD COLUMN é não-destrutivo em SQLite (registros existentes recebem
-- o DEFAULT). Re-executar não falha pois o block é envolvido em IF NOT EXISTS-
-- semantic via PRAGMA table_info check no orquestrador da migration.

ALTER TABLE lint_rules ADD COLUMN status         TEXT DEFAULT 'active';
ALTER TABLE lint_rules ADD COLUMN impl_function  TEXT DEFAULT '';

-- Index opcional pra queries do tipo "liste todas as planned"
CREATE INDEX IF NOT EXISTS idx_lint_rules_status ON lint_rules(status);
