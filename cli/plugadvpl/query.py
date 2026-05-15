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
import re
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
    """Quem chama ``nome``? Lookup em ``chamadas_funcao`` (destino + destino_norm).

    v0.3.18 (#12): cada row inclui ``is_self_call: bool`` indicando que a
    chamada origina do mesmo símbolo (mesma função homônima OU mesmo arquivo
    de basename igual ao nome buscado). Útil pra filtrar self-references
    quando você quer só callers externos (FwLoadModel('X') de dentro de X.prw).
    """
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
    nome_up = nome.upper()
    out: list[dict[str, Any]] = []
    for arquivo, funcao, linha, tipo, contexto in rows:
        # Self-call quando: a função-pai é o próprio nome OU o arquivo de
        # origem (sem extensão) bate com o nome buscado.
        arq_base = (arquivo or "").upper().rsplit(".", 1)[0]
        is_self = (
            (funcao or "").upper() == nome_up
            or arq_base == nome_up
        )
        out.append({
            "arquivo": arquivo,
            "funcao": funcao,
            "linha": linha,
            "tipo": tipo,
            "contexto": contexto,
            "is_self_call": is_self,
        })
    return out


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
    capabilities = _json_or_default(caps_json, [])
    return [
        {
            "arquivo": arquivo_,
            "tipo_arquivo": tipo_arquivo,
            "source_type": source_type,
            "capabilities": capabilities,
            "lines_of_code": loc,
            "encoding": enc,
            "namespace": namespace,
            "funcoes": _json_or_default(funcs_json, []),
            "user_funcs": _json_or_default(user_funcs_json, []),
            "pontos_entrada": _json_or_default(pe_json, []),
            "tabelas_read": _json_or_default(tabs_read_json, []),
            "tabelas_write": _json_or_default(writes_json, []),
            "tabelas_reclock": _json_or_default(reclock_json, []),
            # v0.3.18 (#11 do QA report): sinaliza que `tabelas_*` pode estar
            # incompleto porque o fonte usa MsExecAuto (analise estatica nao
            # expande a rotina chamada). Caller deve checar a rotina pelo nome
            # e/ou rodar `tables` na rotina alvo pra cobertura completa.
            "tabelas_via_execauto": "EXEC_AUTO_CALLER" in capabilities,
            # v0.4.1 (Universo 3 Feature B): tabelas inferidas via lookup do
            # catalogo execauto_routines.json. Lista vazia se: (a) nao ha
            # MsExecAuto no fonte; (b) rotina nao esta no catalogo; (c) call
            # eh dynamic. Cliente pode cruzar com `plugadvpl execauto --arquivo`
            # pra ver detalhe por chamada.
            "tabelas_via_execauto_resolvidas": arch_execauto_tables(conn, arquivo_),
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


def status(
    conn: sqlite3.Connection,
    project_root: str,
    runtime_version: str | None = None,
) -> list[dict[str, Any]]:
    """Estado do índice: meta + contadores.

    Args:
        conn: conexão aberta (read-only OK).
        project_root: caminho da raiz (usado como fallback se o meta não tiver).
        runtime_version: versão do binário rodando AGORA (``plugadvpl.__version__``).
            Quando passado, vira a chave ``runtime_version`` na saída — comparar
            com ``plugadvpl_version`` (= versão que tocou o índice por último)
            permite detectar upgrade sem ``ingest --incremental`` posterior.
    """
    return [
        {
            "schema_version": get_meta(conn, "schema_version"),
            "runtime_version": runtime_version,
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


# ---------------------------------------------------------------------------
# v0.3.0 — Universo 2: queries do dicionário SX (impacto + gatilho)
# ---------------------------------------------------------------------------


def _sx_tables_present(conn: sqlite3.Connection) -> bool:
    """Sentinela: ``True`` se migration 002 já criou as tabelas do dicionário SX."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='campos'"
    ).fetchone()
    return row is not None


def _truncate(text: str | None, max_len: int = 80) -> str:
    """Trunca strings para snippet display (impacto/gatilho)."""
    if not text:
        return ""
    text = " ".join(text.split())  # collapse whitespace
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


_WRITE_KEYWORDS = ("RECLOCK", "REPLACE", "UPDATE ", "INSERT ", "MSEXECAUTO")


def _word_boundary_re(termo: str) -> re.Pattern[str]:
    """Regex `\\b<TERMO>\\b` case-insensitive — boundary ADVPL-aware.

    Em ADVPL nomes de campo são tipo `A1_COD`, `BA1_CODEMP`. `\\b` em Python
    não trata `_` como boundary (`_` é `\\w`), então `\\bA1_COD\\b` NÃO casa
    em `BA1_COD` (B+A1_COD = continuação \\w) nem em `A1_CODFAT` (CO+DF =
    continuação \\w). Exatamente o comportamento desejado pra eliminar falsos
    positivos do `impacto` (v0.3.17 #3 do QA report).
    """
    return re.compile(r"\b" + re.escape(termo) + r"\b", re.IGNORECASE)


def _impacto_fontes(
    conn: sqlite3.Connection, campo_up: str, max_rows: int
) -> list[dict[str, Any]]:
    """Hits no índice de fontes (fonte_chunks.content)."""
    out: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT arquivo, funcao, linha_inicio,
               substr(content, max(1, instr(upper(content), ?) - 30), 160) AS snippet
        FROM fonte_chunks
        WHERE upper(content) LIKE '%' || ? || '%'
        LIMIT ?
        """,
        (campo_up, campo_up, max_rows),
    ).fetchall()
    for arquivo, funcao, linha, snippet in rows:
        snip_up = (snippet or "").upper()
        is_write = any(k in snip_up for k in _WRITE_KEYWORDS)
        out.append(
            {
                "tipo": "fonte",
                "local": f"{arquivo}:{linha or 1}::{funcao or ''}",
                "contexto": _truncate(snippet, 100),
                "severidade": "critical" if is_write else "warning",
            }
        )
    return out


def _impacto_sx3(
    conn: sqlite3.Connection, campo_up: str, max_rows: int
) -> list[dict[str, Any]]:
    """Hits em SX3: registro próprio + campos com VALID/INIT/WHEN/VLDUSER referenciando."""
    out: list[dict[str, Any]] = []
    own = conn.execute(
        "SELECT tabela, campo, tipo, tamanho, descricao FROM campos "
        "WHERE upper(campo) = ?",
        (campo_up,),
    ).fetchone()
    if own:
        out.append(
            {
                "tipo": "SX3",
                "local": f"{own[0]}.{own[1]}",
                "contexto": _truncate(f"{own[2]}({own[3]}) {own[4]}", 100),
                "severidade": "warning",
            }
        )
    # SQL faz prefiltro com LIKE (cheap, narrows candidates). Boundary check
    # acontece em Python pra eliminar falsos positivos de substring (v0.3.17 #3).
    sx3_refs = conn.execute(
        """
        SELECT tabela, campo, validacao, vlduser, when_expr, inicializador
        FROM campos
        WHERE upper(validacao)     LIKE '%' || ? || '%'
           OR upper(vlduser)       LIKE '%' || ? || '%'
           OR upper(when_expr)     LIKE '%' || ? || '%'
           OR upper(inicializador) LIKE '%' || ? || '%'
        LIMIT ?
        """,
        (campo_up, campo_up, campo_up, campo_up, max_rows),
    ).fetchall()
    boundary = _word_boundary_re(campo_up)
    for tabela, c, valid, vld, wh, init in sx3_refs:
        if c.upper() == campo_up:
            continue
        bits: list[str] = []
        if valid and boundary.search(valid):
            bits.append(f"VALID={_truncate(valid, 40)}")
        if vld and boundary.search(vld):
            bits.append(f"VLDUSER={_truncate(vld, 40)}")
        if wh and boundary.search(wh):
            bits.append(f"WHEN={_truncate(wh, 40)}")
        if init and boundary.search(init):
            bits.append(f"INIT={_truncate(init, 40)}")
        if not bits:
            # SQL casou via substring mas nenhum campo tem o termo com boundary —
            # falso positivo, pular.
            continue
        out.append(
            {
                "tipo": "SX3",
                "local": f"{tabela}.{c}",
                "contexto": _truncate(" | ".join(bits), 100),
                "severidade": "warning",
            }
        )
    return out


def _impacto_sx7_chain(
    conn: sqlite3.Connection, campo_up: str, depth: int, max_per_kind: int
) -> list[dict[str, Any]]:
    """Cadeia SX7 com BFS até ``depth`` níveis."""
    out: list[dict[str, Any]] = []
    visited: set[str] = {campo_up}
    frontier: list[str] = [campo_up]
    # SQL prefiltra via LIKE (cheap); Python re-valida boundary pra eliminar
    # falsos positivos como BA1_CODEMP/A1_CODFAT batendo em busca de A1_COD
    # (v0.3.17 #3 do QA report — caso real: >100KB de output em campo curto).
    for level in range(1, max(1, min(depth, 3)) + 1):
        next_frontier: list[str] = []
        for orig in frontier:
            sx7_rows = conn.execute(
                """
                SELECT campo_origem, sequencia, campo_destino, regra, condicao, tipo
                FROM gatilhos
                WHERE upper(campo_origem) = ?
                   OR upper(regra)        LIKE '%' || ? || '%'
                   OR upper(condicao)     LIKE '%' || ? || '%'
                LIMIT ?
                """,
                (orig, orig, orig, max_per_kind),
            ).fetchall()
            boundary = _word_boundary_re(orig)
            for co, seq, cd, regra, cond, tp in sx7_rows:
                # Aceita se: origem eh exatamente o termo (match SQL exato),
                # OU regra/cond contem o termo com word boundary.
                origem_match = (co or "").upper() == orig
                regra_match = bool(regra and boundary.search(regra))
                cond_match = bool(cond and boundary.search(cond))
                if not (origem_match or regra_match or cond_match):
                    continue
                ctx_parts = [f"depth={level}", f"tipo={tp or '?'}"]
                if regra:
                    ctx_parts.append(f"regra={_truncate(regra, 30)}")
                if cond:
                    ctx_parts.append(f"cond={_truncate(cond, 25)}")
                out.append(
                    {
                        "tipo": "SX7",
                        "local": f"{co}#{seq} -> {cd or '(s/destino)'}",
                        "contexto": _truncate(" | ".join(ctx_parts), 100),
                        "severidade": "critical",
                    }
                )
                if cd and cd.upper() not in visited:
                    visited.add(cd.upper())
                    next_frontier.append(cd.upper())
        frontier = next_frontier
        if not frontier:
            break
    return out


def _impacto_sx1(
    conn: sqlite3.Connection, campo_up: str, max_rows: int
) -> list[dict[str, Any]]:
    """Hits em SX1: validacao ou conteudo_padrao referenciando o campo."""
    out: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT grupo, ordem, pergunta, validacao, conteudo_padrao
        FROM perguntas
        WHERE upper(validacao)       LIKE '%' || ? || '%'
           OR upper(conteudo_padrao) LIKE '%' || ? || '%'
        LIMIT ?
        """,
        (campo_up, campo_up, max_rows),
    ).fetchall()
    boundary = _word_boundary_re(campo_up)
    for grupo, ordem, perg, val, cont in rows:
        bits: list[str] = []
        if val and boundary.search(val):
            bits.append(f"VALID={_truncate(val, 40)}")
        if cont and boundary.search(cont):
            bits.append(f"DEF={_truncate(cont, 40)}")
        if not bits:
            continue  # SQL casou via substring mas sem boundary — falso positivo.
        out.append(
            {
                "tipo": "SX1",
                "local": f"{grupo}#{ordem}",
                "contexto": _truncate(f"{perg} | {' | '.join(bits)}", 100),
                "severidade": "warning",
            }
        )
    return out


def impacto_query(
    conn: sqlite3.Connection,
    campo: str,
    *,
    depth: int = 1,
    max_per_kind: int = 50,
) -> list[dict[str, Any]]:
    """Cruza referências a ``campo`` em fontes <-> SX3 <-> SX7 <-> SX1.

    Args:
        conn: conexão SQLite (RO ok).
        campo: nome do campo (ex: ``A1_COD``, case-insensitive).
        depth: profundidade da cadeia de gatilhos a seguir (1..3). Default 1
            = só gatilhos onde ``campo_origem == campo``. ``depth=2`` segue
            também os destinos desses gatilhos como novas origens.
        max_per_kind: máximo de hits por tipo (fonte/SX3/SX7/SX1) — defesa
            contra campos muito comuns (ex: A1_FILIAL) explodirem o output.

    Returns:
        Lista de dicts ``{tipo, local, contexto, severidade}`` ordenada por
        ``severidade`` (critico/error/warning) e ``tipo``. Vazia se ``campo``
        não tem referência alguma OU se o dicionário SX ainda não foi ingerido.
    """
    campo_up = campo.upper().strip()
    if not campo_up:
        return []

    out = _impacto_fontes(conn, campo_up, max_per_kind)
    if _sx_tables_present(conn):
        out.extend(_impacto_sx3(conn, campo_up, max_per_kind))
        out.extend(_impacto_sx7_chain(conn, campo_up, depth, max_per_kind))
        out.extend(_impacto_sx1(conn, campo_up, max_per_kind))

    out.sort(key=lambda r: (_severity_rank(r["severidade"]), r["tipo"], r["local"]))
    return out


def _severity_rank(sev: str) -> int:
    """Ordem para sort: critical < error < warning < info < unknown."""
    return {"critical": 0, "error": 1, "warning": 2, "info": 3}.get(sev, 4)


def gatilho_query(
    conn: sqlite3.Connection,
    campo: str,
    *,
    depth: int = 3,
    max_rows: int = 100,
) -> list[dict[str, Any]]:
    """Lista cadeia de gatilhos SX7 originados/destinados ao ``campo``.

    Cada row representa um gatilho na cadeia: ``{nivel, origem, destino, regra,
    condicao, tipo}``. Recursivo: o destino do nível N vira origem do nível N+1.

    Args:
        conn: conexão SQLite.
        campo: nome do campo (case-insensitive).
        depth: profundidade máxima (1..3). Default 3.
        max_rows: corte defensivo no total de rows retornadas.
    """
    if not _sx_tables_present(conn):
        return []
    campo_up = campo.upper().strip()
    if not campo_up:
        return []
    out: list[dict[str, Any]] = []
    visited: set[str] = {campo_up}
    frontier: list[tuple[str, str]] = [(campo_up, "raiz")]
    for level in range(1, max(1, min(depth, 3)) + 1):
        next_frontier: list[tuple[str, str]] = []
        for origem, parent in frontier:
            # v0.3.15 (#4 do QA report): help diz "originados/destinados" mas a
            # query so casava origem. Agora cobre ambos os lados — campos que
            # apenas RECEBEM gatilhos (chaves geradas, p.ex.) ficavam invisiveis.
            rows = conn.execute(
                """
                SELECT campo_origem, sequencia, campo_destino, regra, condicao,
                       tipo, alias, seek
                FROM gatilhos
                WHERE upper(campo_origem) = ? OR upper(campo_destino) = ?
                ORDER BY sequencia
                """,
                (origem, origem),
            ).fetchall()
            for co, seq, cd, regra, cond, tp, alias, seek in rows:
                if len(out) >= max_rows:
                    break
                out.append(
                    {
                        "nivel": level,
                        "origem": co,
                        "sequencia": seq,
                        "destino": cd,
                        "regra": _truncate(regra, 60),
                        "condicao": _truncate(cond, 40),
                        "tipo": tp,
                        "alias": alias,
                        "seek": seek,
                        "via": parent if level > 1 else "",
                    }
                )
                # v0.3.22 (#6 do QA round 2): traversal bidirecional. Antes
                # so adicionava cd (downstream); rows que casavam via
                # campo_destino tinham co (upstream) ignorado, matando a
                # cadeia inversa em level 1. Agora ambos viram frontier
                # do proximo nivel — visited evita loop infinito em ciclos.
                if cd and cd.upper() not in visited:
                    visited.add(cd.upper())
                    next_frontier.append((cd.upper(), f"{co}#{seq}"))
                if co and co.upper() not in visited:
                    visited.add(co.upper())
                    next_frontier.append((co.upper(), f"{co}#{seq}"))
            if len(out) >= max_rows:
                break
        frontier = next_frontier
        if not frontier or len(out) >= max_rows:
            break
    return out


_SX_STATUS_TABLES = (
    "tabelas", "campos", "indices", "gatilhos", "parametros",
    "perguntas", "tabelas_genericas", "relacionamentos", "pastas",
    "consultas", "grupos_campo",
)


def sx_status(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Resumo do dicionário SX ingerido: counts por tabela + ``last_sx_ingest_at``.

    v0.3.22 (#16 do QA round 2): schema consistente — sempre retorna o mesmo
    set de keys, com `sx_ingerido=False` + counts zerados quando ainda nao
    foi rodado o `ingest-sx`. Antes mudavam de 2 keys (ausente) pra 14 keys
    (presente), forcando caller a branchear no `--format json`.
    """
    sx_present = _sx_tables_present(conn)
    out: dict[str, Any] = {
        "sx_ingerido": sx_present,
        "last_sx_ingest_at": get_meta(conn, "last_sx_ingest_at") if sx_present else None,
        "sx_csv_dir": get_meta(conn, "sx_csv_dir") if sx_present else None,
        "msg": None if sx_present else "Rode 'plugadvpl ingest-sx <dir>' primeiro.",
    }
    for table in _SX_STATUS_TABLES:
        if sx_present:
            out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        else:
            out[table] = 0
    return [out]


# v0.4.0 (Universo 3 Feature A) -----------------------------------------------


_EXEC_TRIGGER_KINDS = {"workflow", "schedule", "job_standalone", "mail_send"}


def execution_triggers_query(
    conn: sqlite3.Connection,
    *,
    kind: str | None = None,
    target: str | None = None,
    arquivo: str | None = None,
) -> list[dict[str, Any]]:
    """Lista execution_triggers indexados (Universo 3 Feature A).

    Args:
        conn: conexão SQLite.
        kind: filtra por tipo (`workflow`/`schedule`/`job_standalone`/`mail_send`).
        target: filtra por nome alvo (case-insensitive, exact match).
        arquivo: filtra por arquivo (case-insensitive, exact match).

    Returns:
        Lista de dicts com `arquivo`, `funcao`, `linha`, `kind`, `target`,
        `metadata` (parsed do JSON), `snippet`.
    """
    sql = "SELECT arquivo, funcao, linha, kind, target, metadata_json, snippet FROM execution_triggers"
    where: list[str] = []
    params: list[Any] = []
    if kind:
        if kind not in _EXEC_TRIGGER_KINDS:
            return []
        where.append("kind = ?")
        params.append(kind)
    if target:
        where.append("upper(target) = upper(?)")
        params.append(target)
    if arquivo:
        where.append("arquivo = ? COLLATE NOCASE")
        params.append(arquivo)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY arquivo, linha"
    rows = conn.execute(sql, params).fetchall()
    out: list[dict[str, Any]] = []
    for arq, fn, ln, k, tgt, meta_json, snippet in rows:
        # Lazy import pra não criar ciclo plugadvpl.query → plugadvpl.parsing.
        from plugadvpl.parsing.triggers import parse_metadata
        out.append({
            "arquivo": arq,
            "funcao": fn or "",
            "linha": int(ln or 0),
            "kind": k,
            "target": tgt or "",
            "metadata": parse_metadata(meta_json or "{}"),
            "snippet": snippet or "",
        })
    return out


_EXECAUTO_OP_MAP = {
    "inc": 3, "inclusao": 3, "include": 3,
    "alt": 4, "alteracao": 4, "alter": 4,
    "exc": 5, "exclusao": 5, "exclude": 5, "delete": 5,
}


def execauto_calls_query(
    conn: sqlite3.Connection,
    *,
    routine: str | None = None,
    modulo: str | None = None,
    arquivo: str | None = None,
    op: str | None = None,
    dynamic: bool | None = None,
) -> list[dict[str, Any]]:
    """Lista chamadas MsExecAuto resolvidas (Universo 3 Feature B).

    Args:
        conn: conexão SQLite.
        routine: filtra por rotina (`MATA410` etc, case-insensitive).
        modulo: filtra por módulo (`SIGAFAT` etc, case-insensitive).
        arquivo: filtra por arquivo (basename).
        op: filtra por operação (`inc`/`alt`/`exc` ou full `inclusao`/...).
        dynamic: True = só dynamic_call, False = só resolved, None = ambos.

    Returns:
        Lista de dicts com campos do schema `execauto_calls` + `tables_resolved`
        já parseado para list[str].
    """
    sql = (
        "SELECT arquivo, funcao, linha, routine, module, routine_type, "
        "op_code, op_label, tables_resolved_json, dynamic_call, arg_count, snippet "
        "FROM execauto_calls"
    )
    where: list[str] = []
    params: list[Any] = []
    if routine:
        where.append("upper(routine) = upper(?)")
        params.append(routine)
    if modulo:
        where.append("upper(module) = upper(?)")
        params.append(modulo)
    if arquivo:
        where.append("arquivo = ? COLLATE NOCASE")
        params.append(arquivo)
    if op:
        op_norm = _EXECAUTO_OP_MAP.get(op.lower())
        if op_norm is None:
            return []
        where.append("op_code = ?")
        params.append(op_norm)
    if dynamic is not None:
        where.append("dynamic_call = ?")
        params.append(1 if dynamic else 0)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY arquivo, linha"
    rows = conn.execute(sql, params).fetchall()
    out: list[dict[str, Any]] = []
    for (
        arq, fn, ln, rt, mod, rtype, opc, oplbl, tjson, dyn, argc, snippet
    ) in rows:
        from plugadvpl.parsing.execauto import parse_tables
        out.append({
            "arquivo": arq,
            "funcao": fn or "",
            "linha": int(ln or 0),
            "routine": rt,
            "module": mod,
            "routine_type": rtype,
            "op_code": opc,
            "op_label": oplbl,
            "tables_resolved": parse_tables(tjson),
            "dynamic_call": bool(dyn),
            "arg_count": argc,
            "snippet": snippet or "",
        })
    return out


def arch_execauto_tables(
    conn: sqlite3.Connection, arquivo: str
) -> list[str]:
    """Tabelas inferidas via ExecAuto pra um fonte (cross-ref Feature B).

    Retorna lista únicos+ordenada de tables_resolved de todas as chamadas
    `execauto_calls` daquele `arquivo`.
    """
    rows = conn.execute(
        "SELECT tables_resolved_json FROM execauto_calls WHERE arquivo = ? COLLATE NOCASE",
        (arquivo,),
    ).fetchall()
    from plugadvpl.parsing.execauto import parse_tables
    seen: set[str] = set()
    for (tjson,) in rows:
        for t in parse_tables(tjson):
            seen.add(t)
    return sorted(seen)
