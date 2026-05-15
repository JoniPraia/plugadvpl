-- v0.4.1 — Universo 3 / Feature B: ExecAuto chain expansion.
-- Indexa chamadas MsExecAuto resolvendo a rotina canonica TOTVS chamada
-- via codeblock e cruzando com catalogo (execauto_routines.json) pra
-- inferir tabelas tocadas indiretamente.

CREATE TABLE IF NOT EXISTS execauto_calls (
  id INTEGER PRIMARY KEY,
  arquivo TEXT NOT NULL,
  funcao TEXT,
  linha INTEGER NOT NULL,
  routine TEXT,                  -- MATA410, FINA050, NULL se dynamic
  module TEXT,                   -- SIGAFAT, NULL se rotina nao no catalogo
  routine_type TEXT,             -- cadastro/movimento, NULL se desconhecido
  op_code INTEGER,               -- 3/4/5 ou outro literal
  op_label TEXT,                 -- "inclusao"/"alteracao"/"exclusao"
  tables_resolved_json TEXT,     -- JSON array ["SC5","SC6"]
  dynamic_call INTEGER NOT NULL DEFAULT 0,  -- 0/1 (bool)
  arg_count INTEGER,             -- num args do codeblock
  snippet TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execauto_arquivo ON execauto_calls(arquivo);
CREATE INDEX IF NOT EXISTS idx_execauto_routine ON execauto_calls(routine);
CREATE INDEX IF NOT EXISTS idx_execauto_module  ON execauto_calls(module);
