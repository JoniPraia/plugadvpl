-- plugadvpl — migration 001 (initial schema, MVP v0.1.0)
-- Schema baseado em projeto interno anterior do autor + deltas para uso como plugin local.
-- Total: 23 tabelas (22 dados + 1 auxiliar normalizada fonte_tabela) + 2 FTS5 virtuais.
-- As 17 tabelas reservadas para Universo 2/3/aux
-- são criadas via migrations futuras (002+, v0.2+).
--
-- PRAGMAs init-time (page_size, journal_mode, journal_size_limit) são aplicados
-- programaticamente em open_db() — NÃO neste arquivo, pois page_size só vale em DB
-- vazio e journal_mode depende da detecção de network share.

-- Tabela interna de tracking de migrations. Permite skip de migrations
-- já aplicadas (importante a partir da migration 002 quando ALTER TABLE entra).
CREATE TABLE IF NOT EXISTS _migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TEXT DEFAULT (datetime('now'))
) WITHOUT ROWID;

-- =============================================================================
-- Universo 1 — Fontes (8 tabelas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS fontes (
    arquivo            TEXT PRIMARY KEY,           -- basename (paridade Protheus)
    caminho            TEXT,                       -- caminho original do FS
    caminho_relativo   TEXT NOT NULL,              -- normalizado: lowercase, forward slashes, relativo ao project_root
    tipo               TEXT,                       -- 'custom'|'padrao'
    modulo             TEXT,
    funcoes            TEXT,                       -- JSON list
    user_funcs         TEXT,                       -- JSON list
    pontos_entrada     TEXT,                       -- JSON list
    tabelas_ref        TEXT,                       -- JSON list (read)
    write_tables       TEXT,                       -- JSON list
    includes           TEXT,                       -- JSON list
    calls_u            TEXT DEFAULT '',            -- JSON list
    calls_execblock    TEXT DEFAULT '',            -- JSON list
    fields_ref         TEXT DEFAULT '',            -- JSON list
    lines_of_code      INTEGER DEFAULT 0,
    hash               TEXT,
    source_type        TEXT DEFAULT '',
    capabilities       TEXT DEFAULT '[]',          -- JSON
    ws_structures      TEXT DEFAULT '{}',
    encoding           TEXT DEFAULT '',
    reclock_tables     TEXT DEFAULT '[]',
    -- deltas do plugin
    mtime_ns           INTEGER NOT NULL DEFAULT 0,
    size_bytes         INTEGER NOT NULL DEFAULT 0,
    indexed_at         TEXT DEFAULT (datetime('now')),
    namespace          TEXT DEFAULT '',            -- TLPP
    tipo_arquivo       TEXT DEFAULT '',            -- 'prw'|'tlpp'|'prx'|'apw'
    parser_version     TEXT DEFAULT '',            -- versão do parser usada na ingestão deste fonte
    UNIQUE (caminho_relativo)                      -- previne colisão se houver subpastas com nomes duplicados
);
CREATE INDEX IF NOT EXISTS idx_fontes_modulo       ON fontes(modulo);
CREATE INDEX IF NOT EXISTS idx_fontes_source_type  ON fontes(source_type);
CREATE INDEX IF NOT EXISTS idx_fontes_caminho_rel  ON fontes(caminho_relativo);

CREATE TABLE IF NOT EXISTS fonte_chunks (
    id              TEXT PRIMARY KEY,           -- '<arquivo>::<funcao>'
    arquivo         TEXT REFERENCES fontes(arquivo) ON DELETE CASCADE,
    funcao          TEXT,
    funcao_norm     TEXT,                       -- uppercase + trim (case-insensitive lookup)
    tipo_simbolo    TEXT DEFAULT 'function',    -- function|static_function|user_function|main_function|method|ws_method|mvc_hook|class|header
    classe          TEXT DEFAULT '',            -- preenchido se METHOD ... CLASS X
    linha_inicio    INTEGER NOT NULL DEFAULT 0,
    linha_fim       INTEGER NOT NULL DEFAULT 0,
    assinatura      TEXT DEFAULT '',            -- linha do header (mesma info de funcao_docs.assinatura, mas aqui pra evitar join)
    content         TEXT,
    modulo          TEXT
);
CREATE INDEX IF NOT EXISTS idx_chunks_arquivo     ON fonte_chunks(arquivo);
CREATE INDEX IF NOT EXISTS idx_chunks_funcao      ON fonte_chunks(funcao COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_chunks_funcao_norm ON fonte_chunks(funcao_norm);
CREATE INDEX IF NOT EXISTS idx_chunks_tipo        ON fonte_chunks(tipo_simbolo);

CREATE TABLE IF NOT EXISTS chamadas_funcao (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem  TEXT NOT NULL,
    funcao_origem   TEXT NOT NULL,
    linha_origem    INTEGER DEFAULT 0,
    tipo            TEXT NOT NULL,
    destino         TEXT NOT NULL,
    destino_norm    TEXT NOT NULL,              -- uppercase + sem prefixo U_ (lookup case-insensitive)
    arquivo_destino TEXT DEFAULT NULL,
    funcao_destino  TEXT DEFAULT NULL,
    contexto        TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_cf_origem       ON chamadas_funcao(arquivo_origem, funcao_origem COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_cf_destino      ON chamadas_funcao(destino COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_cf_destino_norm ON chamadas_funcao(destino_norm);

CREATE TABLE IF NOT EXISTS parametros_uso (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    parametro       TEXT NOT NULL,
    modo            TEXT DEFAULT 'read',        -- read|write|read_write
    default_decl    TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pu_param   ON parametros_uso(parametro);
CREATE INDEX IF NOT EXISTS idx_pu_arquivo ON parametros_uso(arquivo);

CREATE TABLE IF NOT EXISTS perguntas_uso (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    grupo           TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pgu_grupo   ON perguntas_uso(grupo);
CREATE INDEX IF NOT EXISTS idx_pgu_arquivo ON perguntas_uso(arquivo);

CREATE TABLE IF NOT EXISTS operacoes_escrita (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT NOT NULL,
    tipo            TEXT NOT NULL,
    tabela          TEXT NOT NULL,
    campos          TEXT DEFAULT '[]',
    origens         TEXT DEFAULT '{}',
    condicao        TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_oe_tabela  ON operacoes_escrita(tabela);
CREATE INDEX IF NOT EXISTS idx_oe_arquivo ON operacoes_escrita(arquivo);

CREATE TABLE IF NOT EXISTS sql_embedado (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0,
    operacao        TEXT DEFAULT 'select',
    tabelas         TEXT DEFAULT '[]',
    snippet         TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sqle_arquivo ON sql_embedado(arquivo);

CREATE TABLE IF NOT EXISTS funcao_docs (
    arquivo     TEXT,
    funcao      TEXT,
    tipo        TEXT,
    assinatura  TEXT,
    resumo      TEXT,
    tabelas_ref TEXT,
    campos_ref  TEXT,
    chama       TEXT,
    chamada_por TEXT,
    retorno     TEXT,
    params      TEXT,
    fonte       TEXT DEFAULT 'auto',
    updated_at  TEXT DEFAULT (datetime('now')),
    resumo_auto TEXT DEFAULT '',
    PRIMARY KEY (arquivo, funcao)
);

-- =============================================================================
-- Nível 2 — Extrações novas (5 tabelas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS rest_endpoints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    classe          TEXT DEFAULT '',            -- WSSERVICE name
    funcao          TEXT NOT NULL,
    verbo           TEXT NOT NULL,              -- GET|POST|PUT|DELETE
    path            TEXT DEFAULT '',
    annotation_style TEXT NOT NULL              -- 'wsmethod_classico'|'@verb_tlpp'
);
CREATE INDEX IF NOT EXISTS idx_rest_verb ON rest_endpoints(verbo);
CREATE INDEX IF NOT EXISTS idx_rest_path ON rest_endpoints(path);

CREATE TABLE IF NOT EXISTS http_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0,
    metodo          TEXT NOT NULL,              -- HttpGet|HttpPost|HttpsPost|MsAGetUrl
    url_literal     TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_http_arquivo ON http_calls(arquivo);

CREATE TABLE IF NOT EXISTS env_openers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT NOT NULL,
    linha           INTEGER DEFAULT 0,
    empresa         TEXT DEFAULT '',
    filial          TEXT DEFAULT '',
    environment     TEXT DEFAULT '',
    modulo          TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_env_arquivo ON env_openers(arquivo);

CREATE TABLE IF NOT EXISTS log_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0,
    nivel           TEXT DEFAULT '',            -- INFO|WARN|ERROR|DEBUG (de FwLogMsg) ou 'conout'
    categoria       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_log_arquivo ON log_calls(arquivo);

CREATE TABLE IF NOT EXISTS defines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    nome            TEXT NOT NULL,
    valor           TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_define_arquivo ON defines(arquivo);
CREATE INDEX IF NOT EXISTS idx_define_nome    ON defines(nome);

-- =============================================================================
-- Nível 3 — Lint (1 tabela)
-- =============================================================================

CREATE TABLE IF NOT EXISTS lint_findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0,
    regra_id        TEXT NOT NULL,              -- BP-001, SEC-001, etc.
    severidade      TEXT NOT NULL,              -- critical|error|warning
    snippet         TEXT DEFAULT '',
    sugestao_fix    TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_lint_arquivo  ON lint_findings(arquivo);
CREATE INDEX IF NOT EXISTS idx_lint_regra    ON lint_findings(regra_id);
CREATE INDEX IF NOT EXISTS idx_lint_sev      ON lint_findings(severidade);

-- =============================================================================
-- Tabela auxiliar normalizada — lookup reverso por tabela ADVPL
-- =============================================================================

CREATE TABLE IF NOT EXISTS fonte_tabela (
    arquivo     TEXT NOT NULL REFERENCES fontes(arquivo) ON DELETE CASCADE,
    tabela      TEXT NOT NULL,                  -- 'SA1', 'SC5', 'ZA1'
    modo        TEXT NOT NULL,                  -- 'read'|'write'|'reclock'
    PRIMARY KEY (arquivo, tabela, modo)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_ft_tabela ON fonte_tabela(tabela COLLATE NOCASE, modo);

-- =============================================================================
-- Nível 1 — Lookups embarcadas (6 tabelas, todas WITHOUT ROWID)
-- Pré-populadas via lookups/*.json no init.
-- =============================================================================

CREATE TABLE IF NOT EXISTS funcoes_nativas (
    nome            TEXT PRIMARY KEY,
    categoria       TEXT NOT NULL,
    assinatura      TEXT DEFAULT '',
    params_count    INTEGER DEFAULT 0,
    requer_unlock   INTEGER DEFAULT 0,
    requer_close_area INTEGER DEFAULT 0,
    deprecated      INTEGER DEFAULT 0,
    alternativa     TEXT DEFAULT '',
    descricao       TEXT DEFAULT ''
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS funcoes_restritas (
    nome            TEXT PRIMARY KEY,
    categoria       TEXT NOT NULL,
    bloqueada_desde TEXT DEFAULT '',
    alternativa     TEXT DEFAULT ''
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS lint_rules (
    regra_id        TEXT PRIMARY KEY,
    titulo          TEXT NOT NULL,
    severidade      TEXT NOT NULL,
    categoria       TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    fix_guidance    TEXT DEFAULT '',
    detection_kind  TEXT DEFAULT 'regex'
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS sql_macros (
    macro           TEXT PRIMARY KEY,
    descricao       TEXT NOT NULL,
    exemplo         TEXT DEFAULT '',
    output_type     TEXT DEFAULT '',
    safe_for_injection INTEGER DEFAULT 1
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS modulos_erp (
    codigo          TEXT PRIMARY KEY,
    nome            TEXT NOT NULL,
    prefixos_tabelas TEXT DEFAULT '[]',
    prefixos_funcoes TEXT DEFAULT '[]',
    rotinas_principais TEXT DEFAULT '[]'
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS pontos_entrada_padrao (
    nome            TEXT PRIMARY KEY,
    descricao       TEXT DEFAULT '',
    modulo          TEXT DEFAULT '',
    paramixb_count  INTEGER DEFAULT 0,
    retorno_tipo    TEXT DEFAULT '',
    link_tdn        TEXT DEFAULT ''
) WITHOUT ROWID;

-- =============================================================================
-- Internas (2 tabelas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS meta (
    chave   TEXT PRIMARY KEY,
    valor   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_progress (
    item        TEXT PRIMARY KEY,
    fase        INTEGER,
    status      TEXT,
    error_msg   TEXT,
    updated_at  TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- FTS5 virtuais (2) — external content sobre fonte_chunks
-- =============================================================================

-- Índice A: tokens lógicos (palavras + identificadores com underscore/hífen).
-- tokenchars '_-' mantém "A1_COD" e "FW-Browse" como UM token (não quebra).
CREATE VIRTUAL TABLE IF NOT EXISTS fonte_chunks_fts USING fts5(
    arquivo,
    funcao,
    content,
    content='fonte_chunks',
    content_rowid='rowid',
    tokenize = "unicode61 remove_diacritics 2 tokenchars '_-'"
);

-- Índice B: trigram — para busca substring exata com pontuação ADVPL
-- (SA1->A1_COD, %xfilial%, ::New, PARAMIXB[1]). Disponível desde SQLite 3.34.
CREATE VIRTUAL TABLE IF NOT EXISTS fonte_chunks_fts_tri USING fts5(
    content,
    content='fonte_chunks',
    content_rowid='rowid',
    tokenize = 'trigram'
);
