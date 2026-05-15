-- =============================================================================
-- v0.4.0 — Universo 3 (Rastreabilidade) Feature A: execution_triggers
-- =============================================================================
-- Indexa 4 mecanismos canônicos TOTVS de "execução não-direta":
--
--   workflow         — TWFProcess / MsWorkflow / WFPrepEnv com callbacks
--   schedule         — Static Function SchedDef() (configurador SIGACFG)
--   job_standalone   — Main Function + RpcSetEnv (ONSTART AppServer)
--   mail_send        — MailAuto / SEND MAIL UDC / TMailManager
--
-- Spec completo: docs/universo3/A-workflow-schedule.md
-- =============================================================================

CREATE TABLE IF NOT EXISTS execution_triggers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo         TEXT NOT NULL,
    funcao          TEXT DEFAULT '',
    linha           INTEGER DEFAULT 0,
    kind            TEXT NOT NULL,            -- workflow|schedule|job_standalone|mail_send
    target          TEXT DEFAULT '',          -- callback / Main name / pergunte / etc
    metadata_json   TEXT DEFAULT '{}',        -- detalhes específicos por kind
    snippet         TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_exec_arquivo ON execution_triggers(arquivo);
CREATE INDEX IF NOT EXISTS idx_exec_kind    ON execution_triggers(kind);
CREATE INDEX IF NOT EXISTS idx_exec_target  ON execution_triggers(target);
