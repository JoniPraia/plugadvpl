"""Query helpers — uma função por subcomando da CLI.

Cada função recebe uma ``sqlite3.Connection`` aberta e retorna uma lista de
dicts pronta para :func:`plugadvpl.output.render`. Sem efeitos colaterais
(somente SELECT). Aceita conexão read-only ou full — o caller decide.

Convenções:

- Identificadores ADVPL são case-insensitive: comparações via ``upper()`` e
  variantes ``COLLATE NOCASE``. Para destinos de chamada usamos ``destino_norm``
  (uppercase, sem prefixo ``U_``).
- Tabelas Protheus (SA1, SC5, ZA1) são gravadas em uppercase pela ingest;
  comparações usam ``upper(?)`` no bind.
- Funções que mexem com JSON (campos como ``capabilities``, ``funcoes``)
  desserializam via :mod:`json` para que o renderer veja list/dict nativos.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from plugadvpl.db import get_meta


def find_function(conn: sqlite3.Connection, nome: str) -> list[dict[str, Any]]:
    """Procura função por nome em ``fonte_chunks`` (case-insensitive).

    Usa ``funcao_norm`` (uppercase + trim) que é índice em ``fonte_chunks``.
    """
    rows = conn.execute(
        """
        SELECT arquivo, funcao, linha_inicio, linha_fim, assinatura, tipo_simbolo
        FROM fonte_chunks
        WHERE funcao_norm = upper(?)
        ORDER BY arquivo, linha_inicio
        LIMIT 200
        """,
        (nome,),
    ).fetchall()
    cols = ["arquivo", "funcao", "linha_inicio", "linha_fim", "assinatura", "tipo_simbolo"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def find_file(conn: sqlite3.Connection, termo: str) -> list[dict[str, Any]]:
    """Procura arquivo por basename ou parte do caminho relativo."""
    pattern = f"%{termo}%"
    rows = conn.execute(
        """
        SELECT arquivo, caminho_relativo, source_type, lines_of_code
        FROM fontes
        WHERE arquivo LIKE ? COLLATE NOCASE
           OR caminho_relativo LIKE ? COLLATE NOCASE
        ORDER BY arquivo
        LIMIT 200
        """,
        (pattern, pattern),
    ).fetchall()
    cols = ["arquivo", "caminho_relativo", "source_type", "lines_of_code"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def find_any(conn: sqlite3.Connection, termo: str) -> list[dict[str, Any]]:
    """Estratégia composta: tenta ``find_function``, depois ``find_file``, depois ``grep_fts``.

    Para o subcomando ``find <termo>`` que não sabe se é função, arquivo ou
    string genérica.
    """
    hits = find_function(conn, termo)
    if hits:
        return [dict(r, _kind="function") for r in hits]
    hits = find_file(conn, termo)
    if hits:
        return [dict(r, _kind="file") for r in hits]
    fts = grep_fts(conn, termo, mode="fts", limit=20)
    return [dict(r, _kind="content") for r in fts]


def callers(conn: sqlite3.Connection, nome: str) -> list[dict[str, Any]]:
    """Quem chama ``nome``? Lookup em ``chamadas_funcao`` (destino + destino_norm)."""
    norm = nome.upper().lstrip("U_") if nome.upper().startswith("U_") else nome.upper()
    rows = conn.execute(
        """
        SELECT arquivo_origem, funcao_origem, linha_origem, tipo, contexto
        FROM chamadas_funcao
        WHERE destino_norm = ? OR destino = ? COLLATE NOCASE
        ORDER BY arquivo_origem, linha_origem
        """,
        (norm, nome),
    ).fetchall()
    cols = ["arquivo", "funcao", "linha", "tipo", "contexto"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def callees(conn: sqlite3.Connection, nome: str) -> list[dict[str, Any]]:
    """Quem ``nome`` chama? Lookup em ``chamadas_funcao`` (funcao_origem).

    Como o ingest atual deixa ``funcao_origem`` vazio (best-effort MVP),
    fazemos fallback para ``arquivo_origem`` quando ``nome`` parece um
    basename de fonte (ex: ``FATA050.prw``).
    """
    if "." in nome and any(nome.lower().endswith(ext) for ext in (".prw", ".tlpp", ".prx", ".apw")):
        # Fallback: tratamos `nome` como basename de fonte.
        rows = conn.execute(
            """
            SELECT destino, tipo, linha_origem, contexto
            FROM chamadas_funcao
            WHERE arquivo_origem = ? COLLATE NOCASE
            ORDER BY linha_origem
            """,
            (nome,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT destino, tipo, linha_origem, contexto
            FROM chamadas_funcao
            WHERE funcao_origem = ? COLLATE NOCASE
            ORDER BY linha_origem
            """,
            (nome,),
        ).fetchall()
    cols = ["destino", "tipo", "linha", "contexto"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def tables_query(
    conn: sqlite3.Connection, tabela: str, modo: str | None = None
) -> list[dict[str, Any]]:
    """Quem usa a tabela ``X``? Lookup em ``fonte_tabela``.

    ``modo`` pode ser ``read``, ``write``, ``reclock`` ou ``None`` (todos).
    """
    if modo:
        rows = conn.execute(
            "SELECT arquivo, tabela, modo FROM fonte_tabela "
            "WHERE tabela = upper(?) AND modo = ? "
            "ORDER BY arquivo",
            (tabela, modo),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT arquivo, tabela, modo FROM fonte_tabela "
            "WHERE tabela = upper(?) "
            "ORDER BY arquivo, modo",
            (tabela,),
        ).fetchall()
    cols = ["arquivo", "tabela", "modo"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def param_query(conn: sqlite3.Connection, parametro: str) -> list[dict[str, Any]]:
    """Quem usa o parâmetro ``MV_*``? Lookup em ``parametros_uso``."""
    rows = conn.execute(
        """
        SELECT arquivo, parametro, modo, default_decl
        FROM parametros_uso
        WHERE parametro = upper(?)
        ORDER BY arquivo, modo
        """,
        (parametro,),
    ).fetchall()
    cols = ["arquivo", "parametro", "modo", "default_decl"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def arch(conn: sqlite3.Connection, arquivo: str) -> list[dict[str, Any]]:
    """Resumo arquitetural de UM fonte. Retorna lista com 0 ou 1 dict.

    Inclui: ``source_type``, ``capabilities``, ``lines_of_code``, ``encoding``,
    listas de funções/tabelas (read/write/reclock)/includes.
    """
    row = conn.execute(
        """
        SELECT arquivo, source_type, capabilities, lines_of_code, encoding,
               funcoes, user_funcs, pontos_entrada,
               tabelas_ref, write_tables, reclock_tables, includes,
               namespace, tipo_arquivo
        FROM fontes
        WHERE arquivo = ? COLLATE NOCASE
        """,
        (arquivo,),
    ).fetchone()
    if row is None:
        return []
    (
        arquivo_,
        source_type,
        caps_json,
        loc,
        enc,
        funcs_json,
        user_funcs_json,
        pe_json,
        tabs_read_json,
        writes_json,
        reclock_json,
        incs_json,
        namespace,
        tipo_arquivo,
    ) = row
    return [
        {
            "arquivo": arquivo_,
            "tipo_arquivo": tipo_arquivo,
            "source_type": source_type,
            "capabilities": _json_or_default(caps_json, []),
            "lines_of_code": loc,
            "encoding": enc,
            "namespace": namespace,
            "funcoes": _json_or_default(funcs_json, []),
            "user_funcs": _json_or_default(user_funcs_json, []),
            "pontos_entrada": _json_or_default(pe_json, []),
            "tabelas_read": _json_or_default(tabs_read_json, []),
            "tabelas_write": _json_or_default(writes_json, []),
            "tabelas_reclock": _json_or_default(reclock_json, []),
            "includes": _json_or_default(incs_json, []),
        }
    ]


def lint_query(
    conn: sqlite3.Connection,
    arquivo: str | None = None,
    severity: str | None = None,
    regra_id: str | None = None,
) -> list[dict[str, Any]]:
    """Lista lint findings, opcionalmente filtrado por arquivo/severidade/regra."""
    where: list[str] = []
    params: list[Any] = []
    if arquivo:
        where.append("arquivo = ? COLLATE NOCASE")
        params.append(arquivo)
    if severity:
        where.append("severidade = ?")
        params.append(severity)
    if regra_id:
        where.append("regra_id = ?")
        params.append(regra_id)
    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = (
        "SELECT arquivo, funcao, linha, regra_id, severidade, snippet, sugestao_fix "
        f"FROM lint_findings {where_clause} "
        "ORDER BY arquivo, linha"
    )
    rows = conn.execute(sql, params).fetchall()
    cols = ["arquivo", "funcao", "linha", "regra_id", "severidade", "snippet", "sugestao_fix"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def status(conn: sqlite3.Connection, project_root: str) -> list[dict[str, Any]]:
    """Estado do índice: meta + contadores."""
    return [
        {
            "schema_version": get_meta(conn, "schema_version"),
            "plugadvpl_version": get_meta(conn, "plugadvpl_version"),
            "cli_version": get_meta(conn, "cli_version"),
            "parser_version": get_meta(conn, "parser_version"),
            "project_root": get_meta(conn, "project_root") or project_root,
            "indexed_at": get_meta(conn, "indexed_at"),
            "lookup_bundle_hash": get_meta(conn, "lookup_bundle_hash"),
            "total_arquivos": get_meta(conn, "total_arquivos"),
            "total_chunks": get_meta(conn, "total_chunks"),
            "total_chamadas": get_meta(conn, "total_chamadas"),
            "total_lint_findings": get_meta(conn, "total_lint_findings"),
        }
    ]


def stale_files(
    conn: sqlite3.Connection, root_files: dict[str, int]
) -> list[dict[str, Any]]:
    """Lista arquivos cujo ``mtime_ns`` no DB difere do filesystem.

    Args:
        conn: conexão aberta.
        root_files: ``{basename: mtime_ns_atual}`` extraído via ``scan_sources``.
    """
    rows = conn.execute("SELECT arquivo, mtime_ns FROM fontes").fetchall()
    db_state = {a: int(m or 0) for a, m in rows}
    out: list[dict[str, Any]] = []
    for name, db_mtime in db_state.items():
        cur = root_files.get(name)
        if cur is None:
            out.append({"arquivo": name, "estado": "deleted", "db_mtime": db_mtime})
        elif cur > db_mtime:
            out.append(
                {
                    "arquivo": name,
                    "estado": "stale",
                    "db_mtime": db_mtime,
                    "fs_mtime": cur,
                }
            )
    for name, mtime in root_files.items():
        if name not in db_state:
            out.append({"arquivo": name, "estado": "new", "fs_mtime": mtime})
    return out


def doctor_diagnostics(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Diagnósticos de saúde do índice: encoding suspeito, órfãos, FTS sync."""
    diags: list[dict[str, Any]] = []

    # Encoding suspeito: arquivo sem encoding registrado.
    n_no_enc = conn.execute(
        "SELECT COUNT(*) FROM fontes WHERE coalesce(encoding, '') = ''"
    ).fetchone()[0]
    diags.append(
        {
            "check": "encoding_missing",
            "status": "ok" if n_no_enc == 0 else "warn",
            "count": n_no_enc,
            "detail": f"{n_no_enc} arquivos sem encoding em fontes.encoding",
        }
    )

    # Chunks órfãos: fonte_chunks.arquivo sem fontes correspondente.
    n_orphan = conn.execute(
        """
        SELECT COUNT(*) FROM fonte_chunks fc
        WHERE NOT EXISTS (SELECT 1 FROM fontes f WHERE f.arquivo = fc.arquivo)
        """
    ).fetchone()[0]
    diags.append(
        {
            "check": "orphan_chunks",
            "status": "ok" if n_orphan == 0 else "error",
            "count": n_orphan,
            "detail": f"{n_orphan} chunks sem registro em fontes",
        }
    )

    # FTS sync: count(fonte_chunks) vs count(fonte_chunks_fts).
    n_chunks = conn.execute("SELECT COUNT(*) FROM fonte_chunks").fetchone()[0]
    try:
        n_fts = conn.execute("SELECT COUNT(*) FROM fonte_chunks_fts").fetchone()[0]
    except sqlite3.OperationalError:
        n_fts = -1
    diags.append(
        {
            "check": "fts_sync",
            "status": "ok" if n_chunks == n_fts else "warn",
            "count": abs(n_chunks - n_fts),
            "detail": f"chunks={n_chunks} fts={n_fts}",
        }
    )

    # Lookups carregados.
    n_lookups = conn.execute("SELECT COUNT(*) FROM funcoes_nativas").fetchone()[0]
    diags.append(
        {
            "check": "lookups_loaded",
            "status": "ok" if n_lookups > 0 else "error",
            "count": n_lookups,
            "detail": f"funcoes_nativas: {n_lookups} rows",
        }
    )

    return diags


def grep_fts(
    conn: sqlite3.Connection,
    pattern: str,
    mode: str = "fts",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Busca textual em três modos.

    - ``fts`` (default): MATCH em ``fonte_chunks_fts`` (tokenize unicode61). Bom
      para identificadores e palavras inteiras. Aceita sintaxe FTS5
      (``"foo bar"``, ``foo OR bar``).
    - ``literal``: substring case-sensitive via ``LIKE`` em
      ``fonte_chunks.content``. Lento mas exato (incluindo pontuação ADVPL).
    - ``identifier``: busca case-insensitive de identificador, removendo
      prefixo ``U_`` quando presente.
    """
    if mode == "fts":
        sql = """
        SELECT fc.arquivo, fc.funcao,
               snippet(fonte_chunks_fts, 2, '[', ']', '...', 16) AS snippet
        FROM fonte_chunks_fts
        JOIN fonte_chunks fc ON fc.rowid = fonte_chunks_fts.rowid
        WHERE fonte_chunks_fts MATCH ?
        LIMIT ?
        """
        rows = conn.execute(sql, (pattern, limit)).fetchall()
    elif mode == "literal":
        sql = """
        SELECT arquivo, funcao,
               substr(content,
                      max(1, instr(content, ?) - 30),
                      200) AS snippet
        FROM fonte_chunks
        WHERE content LIKE '%' || ? || '%'
        LIMIT ?
        """
        rows = conn.execute(sql, (pattern, pattern, limit)).fetchall()
    else:  # identifier
        normalized = pattern.upper()
        if normalized.startswith("U_"):
            normalized = normalized[2:]
        sql = """
        SELECT arquivo, funcao, substr(content, 1, 200) AS snippet
        FROM fonte_chunks
        WHERE upper(content) LIKE '%' || ? || '%'
        LIMIT ?
        """
        rows = conn.execute(sql, (normalized, limit)).fetchall()
    cols = ["arquivo", "funcao", "snippet"]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def _json_or_default(raw: str | None, default: Any) -> Any:
    """Desserializa JSON do DB ou retorna ``default`` em caso de erro/vazio."""
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default
