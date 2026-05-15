-- v0.4.3 (I6) — indices em `funcao` nas 3 tabelas Universo 3.
-- Antes: queries cross-ref ("quais funcoes no fonte X chamam ExecAuto?")
-- forcavam scan + filter Python. Agora idx cobre `funcao` nas 3 tables.

CREATE INDEX IF NOT EXISTS idx_exec_funcao
  ON execution_triggers(funcao);

CREATE INDEX IF NOT EXISTS idx_execauto_funcao
  ON execauto_calls(funcao);

-- protheus_docs ja tem idx_pdoc_funcao (criado em migration 007), nao precisa.
