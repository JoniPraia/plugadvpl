-- =============================================================================
-- v0.3.14 — Recria `consultas` com PK incluindo `tipo`.
-- =============================================================================
-- Bug: SXB no Protheus tem 6 tipos de registro (XB_TIPO 1-6: header, indice,
-- permissao, coluna, retorno, filtro) que coexistem para um mesmo (XB_ALIAS,
-- XB_SEQ, XB_COLUNA). A PK original `(alias, sequencia, coluna)` fazia colidir
-- as 6 paginas — uma consulta full virava 1-2 rows em vez de 6+. Em dump real
-- de cliente: 58.796 rows do CSV → 46.669 rows no DB (perda de 20.6%).
--
-- Fix: PK passa a ser `(alias, tipo, sequencia, coluna)` espelhando a PK natural
-- do Configurador TOTVS (TDN: XB_FILIAL+XB_ALIAS+XB_TIPO+XB_SEQ+XB_COLUNA;
-- XB_FILIAL eh sempre vazio porque SXB eh X2_MODO='C').
--
-- SQLite nao suporta ALTER TABLE ... ALTER PRIMARY KEY, entao seguimos o
-- pattern oficial: CREATE temp + INSERT SELECT + DROP + RENAME + recreate index.
-- Dados existentes sao preservados (mas usuarios precisam re-rodar `ingest-sx`
-- pra ganhar os ~20% de rows que estavam sendo deduplicados antes).
-- =============================================================================

CREATE TABLE consultas_new (
    alias       TEXT NOT NULL,             -- XB_ALIAS
    tipo        TEXT NOT NULL DEFAULT '',  -- XB_TIPO (1=header, 2=indice, 3=permissao, 4=coluna, 5=retorno, 6=filtro)
    sequencia   TEXT NOT NULL,             -- XB_SEQ
    coluna      TEXT NOT NULL DEFAULT '',  -- XB_COLUNA
    descricao   TEXT DEFAULT '',           -- XB_DESCRI
    conteudo    TEXT DEFAULT '',           -- XB_CONTEM
    PRIMARY KEY (alias, tipo, sequencia, coluna)
) WITHOUT ROWID;

INSERT INTO consultas_new (alias, tipo, sequencia, coluna, descricao, conteudo)
SELECT alias, tipo, sequencia, coluna, descricao, conteudo FROM consultas;

DROP TABLE consultas;
ALTER TABLE consultas_new RENAME TO consultas;

CREATE INDEX IF NOT EXISTS idx_consultas_alias ON consultas(alias);
