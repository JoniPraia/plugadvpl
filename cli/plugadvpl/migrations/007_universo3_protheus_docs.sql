-- v0.4.2 — Universo 3 / Feature C: Protheus.doc agregado.
-- Indexa blocos /*/{Protheus.doc} <id> ... /*/ extraidos das fontes,
-- permitindo agregacao por modulo/author/tipo + show formatado por funcao.

CREATE TABLE IF NOT EXISTS protheus_docs (
  id INTEGER PRIMARY KEY,
  arquivo TEXT NOT NULL,
  funcao TEXT,                   -- nome resolvido pela proxima decl
  funcao_id TEXT,                -- <id> declarado no header (pode diferir)
  tipo TEXT,                     -- @type normalizado lowercase
  module_inferido TEXT,          -- SIGAFAT, SIGAFIN, ... ou NULL
  linha_bloco_inicio INTEGER NOT NULL,
  linha_bloco_fim INTEGER NOT NULL,
  linha_funcao INTEGER,          -- linha da decl seguinte ou NULL (orfao)
  summary TEXT,                  -- texto livre antes da primeira @tag
  description TEXT,              -- @description
  author TEXT,                   -- @author
  since TEXT,                    -- @since
  version TEXT,                  -- @version
  deprecated INTEGER NOT NULL DEFAULT 0,  -- 0/1
  deprecated_reason TEXT,        -- valor de @deprecated (se houver)
  language TEXT,                 -- @language
  params_json TEXT,              -- JSON: [{"name","type","desc","optional"}]
  returns_json TEXT,             -- JSON: [{"type","desc"}]
  examples_json TEXT,            -- JSON: [str]
  history_json TEXT,             -- JSON: [{"date","user","desc"}]
  see_json TEXT,                 -- JSON: [str]
  tables_json TEXT,              -- JSON: [str]
  todos_json TEXT,               -- JSON: [str]
  obs_json TEXT,                 -- JSON: [str]
  links_json TEXT,               -- JSON: [str]
  raw_tags_json TEXT             -- JSON: {tag: value} catch-all
);

CREATE INDEX IF NOT EXISTS idx_pdoc_arquivo ON protheus_docs(arquivo);
CREATE INDEX IF NOT EXISTS idx_pdoc_funcao  ON protheus_docs(funcao);
CREATE INDEX IF NOT EXISTS idx_pdoc_module  ON protheus_docs(module_inferido);
CREATE INDEX IF NOT EXISTS idx_pdoc_author  ON protheus_docs(author);
CREATE INDEX IF NOT EXISTS idx_pdoc_dep     ON protheus_docs(deprecated);
