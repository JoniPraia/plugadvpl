-- plugadvpl — migration 002 (Universo 2: Dicionário SX, v0.3.0)
-- Cria 11 tabelas para indexar o dicionário SX exportado em CSV (Configurador →
-- Misc → Exportar Dicionário). Schema sincronizado com cli/plugadvpl/parsing/sx_csv.py.
--
-- Encoding canonical do CSV: ISO-8859-1 / cp1252. Delimiter: comma. Header com
-- prefixos X1_/X2_/X3_/X5_/X6_/X7_/X9_/XA_/XB_ (SIX usa colunas sem prefixo).
--
-- Idempotente — usa CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.
-- Inserts são feitos via INSERT OR REPLACE (idempotente em re-ingest).

-- =============================================================================
-- SX2 — Tabelas (X2_CHAVE → modo C/E/U)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tabelas (
    codigo      TEXT PRIMARY KEY,        -- X2_CHAVE (ex: SA1, SC5, ZA1)
    nome        TEXT DEFAULT '',         -- X2_NOME
    modo        TEXT DEFAULT '',         -- X2_MODO (C=Compartilhado, E=Exclusivo, U=Misto)
    custom      INTEGER DEFAULT 0,       -- 1 se Z*/SZ*/Q[A-Z]* (custom)
    num_rows    INTEGER DEFAULT 0,       -- placeholder (futuro: total_registros_tabelas.csv)
    usada       INTEGER DEFAULT 1        -- 1 = ativa no ERP (default)
) WITHOUT ROWID;

-- =============================================================================
-- SX3 — Campos (X3_ARQUIVO + X3_CAMPO)
-- =============================================================================
CREATE TABLE IF NOT EXISTS campos (
    tabela          TEXT NOT NULL,       -- X3_ARQUIVO (FK lógica para tabelas)
    campo           TEXT NOT NULL,       -- X3_CAMPO (ex: A1_COD, A1_NOME)
    tipo            TEXT DEFAULT '',     -- X3_TIPO (C/N/D/M/L)
    tamanho         INTEGER DEFAULT 0,   -- X3_TAMANHO
    decimal         INTEGER DEFAULT 0,   -- X3_DECIMAL
    titulo          TEXT DEFAULT '',     -- X3_TITULO (PT)
    descricao       TEXT DEFAULT '',     -- X3_DESCRIC
    validacao       TEXT DEFAULT '',     -- X3_VALID (expressao ADVPL)
    inicializador   TEXT DEFAULT '',     -- X3_RELACAO (default/fórmula)
    obrigatorio     INTEGER DEFAULT 0,   -- 1 se X3_OBRIGAT == 'x'/'S'/'1'/'.T.'
    custom          INTEGER DEFAULT 0,   -- 1 se nome ou propri indica custom
    f3              TEXT DEFAULT '',     -- X3_F3 (referência SXB)
    cbox            TEXT DEFAULT '',     -- X3_CBOX (combobox values)
    vlduser         TEXT DEFAULT '',     -- X3_VLDUSER (validação user-defined)
    when_expr       TEXT DEFAULT '',     -- X3_WHEN (habilitação condicional)
    proprietario    TEXT DEFAULT '',     -- X3_PROPRI (S = standard, U = custom)
    browse          TEXT DEFAULT '',     -- X3_BROWSE (S/N)
    trigger_flag    TEXT DEFAULT '',     -- X3_TRIGGER (S/N)
    visual          TEXT DEFAULT '',     -- X3_VISUAL
    context         TEXT DEFAULT '',     -- X3_CONTEXT (R/V — Real/Virtual)
    folder          TEXT DEFAULT '',     -- X3_FOLDER (referência SXA)
    grpsxg          TEXT DEFAULT '',     -- X3_GRPSXG (grupo de campos)
    PRIMARY KEY (tabela, campo)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_campos_tabela     ON campos(tabela);
CREATE INDEX IF NOT EXISTS idx_campos_campo      ON campos(campo);
CREATE INDEX IF NOT EXISTS idx_campos_validacao  ON campos(validacao) WHERE validacao != '';
CREATE INDEX IF NOT EXISTS idx_campos_vlduser    ON campos(vlduser)   WHERE vlduser != '';
CREATE INDEX IF NOT EXISTS idx_campos_when       ON campos(when_expr) WHERE when_expr != '';
CREATE INDEX IF NOT EXISTS idx_campos_init       ON campos(inicializador) WHERE inicializador != '';
CREATE INDEX IF NOT EXISTS idx_campos_f3         ON campos(f3) WHERE f3 != '';
CREATE INDEX IF NOT EXISTS idx_campos_grpsxg     ON campos(grpsxg) WHERE grpsxg != '';

-- =============================================================================
-- SIX — Índices (colunas sem prefixo X*: INDICE, ORDEM, CHAVE...)
-- =============================================================================
CREATE TABLE IF NOT EXISTS indices (
    tabela        TEXT NOT NULL,         -- INDICE (alias: SA1, SC5, ZA1)
    ordem         TEXT NOT NULL,         -- ORDEM (01, 02, ...)
    chave         TEXT DEFAULT '',       -- CHAVE (expressão da chave)
    descricao     TEXT DEFAULT '',       -- DESCRICAO
    proprietario  TEXT DEFAULT '',       -- PROPRI (U/S)
    f3            TEXT DEFAULT '',       -- F3 (consulta padrão)
    nickname      TEXT DEFAULT '',       -- NICKNAME (apelido)
    showpesq      TEXT DEFAULT '',       -- SHOWPESQ (S/N)
    custom        INTEGER DEFAULT 0,
    PRIMARY KEY (tabela, ordem)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_indices_tabela ON indices(tabela);

-- =============================================================================
-- SX7 — Gatilhos (X7_CAMPO + X7_SEQUENC)
-- =============================================================================
CREATE TABLE IF NOT EXISTS gatilhos (
    campo_origem  TEXT NOT NULL,         -- X7_CAMPO (campo que dispara)
    sequencia     TEXT NOT NULL,         -- X7_SEQUENC
    campo_destino TEXT DEFAULT '',       -- X7_CDOMIN (campo modificado)
    regra         TEXT DEFAULT '',       -- X7_REGRA (expressão ADVPL)
    tipo          TEXT DEFAULT '',       -- X7_TIPO (P=Primário, S=Secundário)
    tabela        TEXT DEFAULT '',       -- X7_ALIAS ou X7_ARQUIVO
    condicao      TEXT DEFAULT '',       -- X7_CONDIC (condição p/ disparar)
    proprietario  TEXT DEFAULT '',       -- X7_PROPRI
    seek          TEXT DEFAULT '',       -- X7_SEEK (S/N)
    alias         TEXT DEFAULT '',       -- X7_ALIAS
    ordem         TEXT DEFAULT '',       -- X7_ORDEM
    chave         TEXT DEFAULT '',       -- X7_CHAVE
    custom        INTEGER DEFAULT 0,
    PRIMARY KEY (campo_origem, sequencia)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_gatilhos_campo_origem  ON gatilhos(campo_origem);
CREATE INDEX IF NOT EXISTS idx_gatilhos_campo_destino ON gatilhos(campo_destino);
CREATE INDEX IF NOT EXISTS idx_gatilhos_alias         ON gatilhos(alias) WHERE alias != '';

-- =============================================================================
-- SX6 — Parâmetros MV_* (X6_FIL + X6_VAR)
-- =============================================================================
CREATE TABLE IF NOT EXISTS parametros (
    filial        TEXT NOT NULL DEFAULT '',  -- X6_FIL (pode ser '')
    variavel      TEXT NOT NULL,             -- X6_VAR (ex: MV_LOCALIZA)
    tipo          TEXT DEFAULT '',           -- X6_TIPO (C/N/L/D)
    descricao     TEXT DEFAULT '',           -- X6_DESCRIC + X6_DESC1
    conteudo      TEXT DEFAULT '',           -- X6_CONTEUD (valor default)
    proprietario  TEXT DEFAULT '',           -- X6_PROPRI
    custom        INTEGER DEFAULT 0,
    validacao     TEXT DEFAULT '',           -- X6_VALID
    init          TEXT DEFAULT '',           -- X6_INIT
    PRIMARY KEY (filial, variavel)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_parametros_variavel ON parametros(variavel);

-- =============================================================================
-- SX1 — Perguntas (X1_GRUPO + X1_ORDEM)
-- =============================================================================
CREATE TABLE IF NOT EXISTS perguntas (
    grupo            TEXT NOT NULL,       -- X1_GRUPO (ex: MTA010)
    ordem            TEXT NOT NULL,       -- X1_ORDEM (01, 02, ...)
    pergunta         TEXT DEFAULT '',     -- X1_PERGUNT
    variavel         TEXT DEFAULT '',     -- X1_VARIAVL (mv_ch1, mv_ch2)
    tipo             TEXT DEFAULT '',     -- X1_TIPO (C/N/D/L)
    tamanho          INTEGER DEFAULT 0,   -- X1_TAMANHO
    decimal          INTEGER DEFAULT 0,   -- X1_DECIMAL
    f3               TEXT DEFAULT '',     -- X1_F3
    validacao        TEXT DEFAULT '',     -- X1_VALID
    conteudo_padrao  TEXT DEFAULT '',     -- X1_DEF01
    PRIMARY KEY (grupo, ordem)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_perguntas_grupo ON perguntas(grupo);

-- =============================================================================
-- SX5 — Tabelas genéricas (X5_FILIAL + X5_TABELA + X5_CHAVE)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tabelas_genericas (
    filial      TEXT NOT NULL DEFAULT '',  -- X5_FILIAL
    tabela      TEXT NOT NULL,             -- X5_TABELA (ex: 24, X1, ZZ)
    chave       TEXT NOT NULL,             -- X5_CHAVE
    descricao   TEXT DEFAULT '',           -- X5_DESCRI
    custom      INTEGER DEFAULT 0,
    PRIMARY KEY (filial, tabela, chave)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_sx5_tabela ON tabelas_genericas(tabela);

-- =============================================================================
-- SX9 — Relacionamentos (X9_DOM + X9_IDENT + X9_CDOM)
-- =============================================================================
CREATE TABLE IF NOT EXISTS relacionamentos (
    tabela_origem      TEXT NOT NULL,       -- X9_DOM
    identificador      TEXT NOT NULL,       -- X9_IDENT
    tabela_destino     TEXT NOT NULL,       -- X9_CDOM
    expressao_origem   TEXT DEFAULT '',     -- X9_EXPDOM
    expressao_destino  TEXT DEFAULT '',     -- X9_EXPCDOM
    proprietario       TEXT DEFAULT '',     -- X9_PROPRI
    condicao_sql       TEXT DEFAULT '',     -- X9_CONDSQL
    custom             INTEGER DEFAULT 0,
    PRIMARY KEY (tabela_origem, identificador, tabela_destino)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_relac_origem  ON relacionamentos(tabela_origem);
CREATE INDEX IF NOT EXISTS idx_relac_destino ON relacionamentos(tabela_destino);

-- =============================================================================
-- SXA — Pastas (XA_ALIAS + XA_ORDEM)
-- =============================================================================
CREATE TABLE IF NOT EXISTS pastas (
    alias        TEXT NOT NULL,            -- XA_ALIAS (tabela)
    ordem        TEXT NOT NULL,            -- XA_ORDEM
    descricao    TEXT DEFAULT '',          -- XA_DESCRIC
    proprietario TEXT DEFAULT '',          -- XA_PROPRI
    agrupamento  TEXT DEFAULT '',          -- XA_AGRUP
    PRIMARY KEY (alias, ordem)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_pastas_alias ON pastas(alias);

-- =============================================================================
-- SXB — Consultas F3 (XB_ALIAS + XB_SEQ + XB_COLUNA)
-- =============================================================================
CREATE TABLE IF NOT EXISTS consultas (
    alias       TEXT NOT NULL,             -- XB_ALIAS
    tipo        TEXT DEFAULT '',           -- XB_TIPO (1/2/3/4)
    sequencia   TEXT NOT NULL,             -- XB_SEQ
    coluna      TEXT NOT NULL DEFAULT '',  -- XB_COLUNA
    descricao   TEXT DEFAULT '',           -- XB_DESCRI
    conteudo    TEXT DEFAULT '',           -- XB_CONTEM
    PRIMARY KEY (alias, sequencia, coluna)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_consultas_alias ON consultas(alias);

-- =============================================================================
-- SXG — Grupos de campos (XG_GRUPO + ...)
-- =============================================================================
-- NOTA: alguns exports de "sxg.csv" trazem na verdade um dump SX3 alternativo
-- (ver issue interna). O parser detecta o header e ingere apenas se o CSV
-- realmente contiver colunas XG_*. Caso contrário, sxg é silenciosamente
-- pulado e a tabela `grupos_campo` permanece vazia.
CREATE TABLE IF NOT EXISTS grupos_campo (
    grupo          TEXT PRIMARY KEY,       -- XG_GRUPO
    descricao      TEXT DEFAULT '',        -- XG_DESCRIC
    tamanho_max    INTEGER DEFAULT 0,      -- XG_TAMMAX
    tamanho_min    INTEGER DEFAULT 0,      -- XG_TAMMIN
    tamanho        INTEGER DEFAULT 0,      -- XG_TAMANHO
    total_campos   INTEGER DEFAULT 0       -- count(*) em campos.grpsxg
) WITHOUT ROWID;
