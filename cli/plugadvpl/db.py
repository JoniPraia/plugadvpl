"""Banco de dados SQLite — abertura, PRAGMAs, migrations, network share detection."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.resources as ir
import json
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA_VERSION = "5"


# Mapeamento {filename JSON -> (tabela, colunas em ordem)}.
# A primeira coluna de cada lista é a PRIMARY KEY (target do ON CONFLICT).
# Mantenha sincronizado com migration 001_initial.sql (seção Lookups).
_LOOKUP_FILES: dict[str, tuple[str, list[str]]] = {
    "funcoes_nativas.json": (
        "funcoes_nativas",
        [
            "nome", "categoria", "assinatura", "params_count",
            "requer_unlock", "requer_close_area", "deprecated",
            "alternativa", "descricao",
        ],
    ),
    "funcoes_restritas.json": (
        "funcoes_restritas",
        ["nome", "categoria", "bloqueada_desde", "alternativa"],
    ),
    "lint_rules.json": (
        "lint_rules",
        [
            "regra_id", "titulo", "severidade", "categoria", "descricao",
            "fix_guidance", "detection_kind", "status", "impl_function",
        ],
    ),
    "sql_macros.json": (
        "sql_macros",
        ["macro", "descricao", "exemplo", "output_type", "safe_for_injection"],
    ),
    "modulos_erp.json": (
        "modulos_erp",
        ["codigo", "nome", "prefixos_tabelas", "prefixos_funcoes", "rotinas_principais"],
    ),
    "pontos_entrada_padrao.json": (
        "pontos_entrada_padrao",
        ["nome", "descricao", "modulo", "paramixb_count", "retorno_tipo", "link_tdn"],
    ),
}


def _is_network_share(path: Path) -> bool:
    """Detecta se um path está em network share (SMB/CIFS/UNC).

    WAL não funciona em network filesystem (docs SQLite oficiais —
    https://sqlite.org/wal.html). Quando True, ``open_db`` usa
    ``journal_mode=DELETE`` em vez de WAL.

    Detecta:

    - UNC paths Windows: ``\\\\server\\share`` (backslash-backslash prefix).
    - POSIX-style UNC: ``//server/share`` (forward-slash prefix).
    - Mapped drives em Windows (Z: apontando para share) NÃO são detectados
      aqui por simplicidade — usuário recebe warning explícito se WAL falhar
      durante uso (SQLite retorna erro nesse caso).
    """
    s = str(path)
    return s.startswith("\\\\") or s.startswith("//")


def open_db(db_path: Path) -> sqlite3.Connection:
    """Abre/cria DB em ``db_path`` aplicando PRAGMAs corretos.

    Comportamento:

    - Em DB novo: aplica ``page_size=8192`` (só vale antes de qualquer
      CREATE TABLE — persiste no header).
    - Detecta network share via :func:`_is_network_share` no diretório-pai
      do DB. Se positivo, usa ``journal_mode=DELETE`` (rollback journal,
      compatível com SMB/CIFS). Caso contrário, usa
      ``journal_mode=WAL`` + ``journal_size_limit=64MiB``.
    - Sempre aplica: ``synchronous=NORMAL``, ``foreign_keys=ON``,
      ``temp_store=MEMORY``, ``mmap_size=256MiB``, ``cache_size=-20000``
      (~20MB), ``busy_timeout=5000`` (5s).

    Spec §4.1.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not db_path.exists()
    conn = sqlite3.connect(str(db_path))

    if is_new:
        conn.execute("PRAGMA page_size = 8192")

    if _is_network_share(db_path.parent):
        conn.execute("PRAGMA journal_mode = DELETE")
    else:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA journal_size_limit = 67108864")

    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456")
    conn.execute("PRAGMA cache_size = -20000")
    conn.execute("PRAGMA busy_timeout = 5000")

    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Aplica migrations em ordem (.sql files numerados em migrations/).

    Tracks aplicações em ``_migrations`` para skip idempotente. Atualiza
    ``meta.schema_version`` para refletir a última migration aplicada.

    Migrations são arquivos ``.sql`` numerados (``001_initial.sql``,
    ``002_xxx.sql``, ...). A primeira migration cria a tabela ``_migrations``;
    a partir da segunda, somente migrations cujo filename NÃO consta em
    ``_migrations`` são executadas. Isso é importante a partir da migration
    002 quando ALTER TABLE entra em jogo (não-idempotente).

    Carrega via :mod:`importlib.resources` para funcionar igual em
    desenvolvimento (source tree) e em wheel instalado.
    """
    migrations_dir = ir.files("plugadvpl") / "migrations"
    sql_files = sorted(
        (f for f in migrations_dir.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )

    # Bootstrap: a primeira migration cria _migrations. Tente ler — se falhar,
    # é DB virgem e aplicamos 001 sempre.
    try:
        applied: set[str] = {
            row[0] for row in conn.execute("SELECT filename FROM _migrations")
        }
    except sqlite3.OperationalError:
        applied = set()

    last_version = "0"
    for sql_file in sql_files:
        if sql_file.name in applied:
            # Migration já aplicada; mas ainda devemos atualizar last_version
            # para que schema_version reflita a mais recente conhecida.
            num = sql_file.name.split("_")[0].lstrip("0") or "0"
            last_version = num
            continue
        sql = sql_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT OR IGNORE INTO _migrations (filename) VALUES (?)",
            (sql_file.name,),
        )
        # Extrai número do filename "001_initial.sql" → "1"
        num = sql_file.name.split("_")[0].lstrip("0") or "0"
        last_version = num

    if last_version != "0":
        # Atualiza schema_version no meta (se meta já existe). Em DBs muito
        # antigos onde 001 ainda não criou meta a tabela pode faltar — toleramos
        # silenciosamente (raríssimo; apenas defensivo).
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO meta (chave, valor) VALUES (?, ?) "
                "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                ("schema_version", last_version),
            )

    conn.commit()


def init_meta(
    conn: sqlite3.Connection, *, project_root: str, cli_version: str
) -> None:
    """Grava as linhas obrigatórias em ``meta`` (idempotente via UPSERT).

    Linhas escritas:

    - ``plugadvpl_version``: ``cli_version`` informado pelo chamador.
    - ``project_root``: caminho absoluto da raiz do projeto cliente.
    - ``encoding_policy``: ``'preserve'`` (default, cf. spec §4.2).

    Nota: ``schema_version`` NÃO é gravado aqui — :func:`apply_migrations`
    deriva o valor a partir do filename da última migration aplicada e
    grava em ``meta.schema_version`` após o sucesso da aplicação.
    """
    defaults: dict[str, str] = {
        "plugadvpl_version": cli_version,
        "project_root": project_root,
        "encoding_policy": "preserve",
    }
    for k, v in defaults.items():
        set_meta(conn, k, v)


def get_meta(conn: sqlite3.Connection, chave: str) -> str | None:
    """Retorna ``meta.valor`` para ``chave``, ou ``None`` se ausente."""
    row = conn.execute(
        "SELECT valor FROM meta WHERE chave=?", (chave,)
    ).fetchone()
    if row is None:
        return None
    valor: str = row[0]
    return valor


def set_meta(conn: sqlite3.Connection, chave: str, valor: str) -> None:
    """Insere ou atualiza ``meta[chave] = valor`` (UPSERT atômico + commit)."""
    conn.execute(
        "INSERT INTO meta (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
        (chave, valor),
    )
    conn.commit()


def seed_lookups(
    conn: sqlite3.Connection, lookup_dir: Path | None = None
) -> dict[str, int]:
    """Carrega os 6 JSONs de ``lookups/`` e popula as tabelas ``WITHOUT ROWID``.

    Idempotente — usa ``INSERT ... ON CONFLICT(<PK>) DO UPDATE`` (UPSERT). As
    colunas tipo JSON list (``prefixos_tabelas``, ``prefixos_funcoes``,
    ``rotinas_principais``) são serializadas como strings JSON antes do bind.

    Após popular todas as 6 tabelas, calcula SHA-256 do bundle (concatenação
    dos arquivos JSON na ordem de :data:`_LOOKUP_FILES`) e grava em
    ``meta.lookup_bundle_hash``. Isso permite detectar drift entre o bundle
    embarcado no wheel e o estado do DB.

    Carrega via :mod:`importlib.resources` para funcionar igual em dev tree
    e em wheel instalado. Aceita ``lookup_dir`` explícito (``pathlib.Path``)
    para testes que precisam isolar o conjunto de dados.

    Retorna ``{table_name: rows_inserted}``.
    """
    bundle_hasher = hashlib.sha256()
    counts: dict[str, int] = {}

    for filename, (table, cols) in _LOOKUP_FILES.items():
        if lookup_dir is None:
            resource = ir.files("plugadvpl").joinpath("lookups", filename)
            raw = resource.read_text(encoding="utf-8")
        else:
            raw = (lookup_dir / filename).read_text(encoding="utf-8")
        bundle_hasher.update(raw.encode("utf-8"))

        items: list[dict[str, object]] = json.loads(raw)

        placeholders = ",".join("?" * len(cols))
        cols_sql = ",".join(cols)
        # Primeira coluna é PK; demais entram no DO UPDATE.
        pk = cols[0]
        update_cols = [c for c in cols if c != pk]
        if update_cols:
            updates = ",".join(f"{c}=excluded.{c}" for c in update_cols)
            sql = (
                f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders}) "
                f"ON CONFLICT({pk}) DO UPDATE SET {updates}"
            )
        else:
            sql = (
                f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders}) "
                f"ON CONFLICT({pk}) DO NOTHING"
            )

        rows: list[tuple[object, ...]] = []
        for item in items:
            row: list[object] = []
            for c in cols:
                val: object = item.get(c, "")
                # Colunas tipo list[str] são gravadas como JSON string.
                if isinstance(val, list):
                    val = json.dumps(val, ensure_ascii=False)
                row.append(val)
            rows.append(tuple(row))

        if rows:
            conn.executemany(sql, rows)
        counts[table] = len(rows)

    conn.commit()
    set_meta(conn, "lookup_bundle_hash", bundle_hasher.hexdigest())
    return counts


def close_db(conn: sqlite3.Connection) -> None:
    """Fecha conexão SQLite executando otimizações finais.

    Sequência (cf. spec §4.1, recomendação oficial SQLite >=3.46):

    1. ``commit`` — flush writes pendentes ANTES do checkpoint
       (``wal_checkpoint(TRUNCATE)`` não roda com write transaction aberta).
    2. ``PRAGMA optimize`` — coleta estatísticas e atualiza índices
       (https://sqlite.org/pragma.html#pragma_optimize).
    3. Se ``journal_mode == 'wal'``: ``PRAGMA wal_checkpoint(TRUNCATE)``
       — força sync e zera ``.db-wal`` para liberar disco.
    4. ``close`` em bloco ``finally`` mesmo se houver erro nas otimizações
       (evita vazar conexão).
    """
    try:
        conn.commit()  # flush pending writes ANTES do checkpoint
        conn.execute("PRAGMA optimize")
        mode_row = conn.execute("PRAGMA journal_mode").fetchone()
        if mode_row is not None and mode_row[0] == "wal":
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()
