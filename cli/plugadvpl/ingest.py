"""Ingest pipeline: scan -> parse (parallel) -> write SQLite + FTS5 rebuild.

Orquestrador do MVP. Em arquivos pequenos (<200) roda single-thread; acima
distribui parsing entre workers (ProcessPoolExecutor) e centraliza escrita
em SQLite numa thread única (SQLite não suporta writers paralelos).

Estratégia de upsert por arquivo:
- DELETE em todas as tabelas dependentes WHERE arquivo=? (replace atômico).
- INSERT OR REPLACE em fontes (PK = arquivo).
- INSERT em massa (executemany) nas tabelas dependentes.

FTS5 é rebuildado uma vez ao final (mais barato do que insert-by-insert
para batch grande).
"""
from __future__ import annotations

import datetime as _dt
import json
import multiprocessing as mp
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any

from plugadvpl import __version__ as _cli_version
from plugadvpl.db import (
    apply_migrations,
    close_db,
    get_meta,
    init_meta,
    open_db,
    seed_lookups,
    set_meta,
)
from plugadvpl.parsing import lint as lint_module
from plugadvpl.parsing.parser import _PE_NAME_RE, parse_source
from plugadvpl.scan import scan_sources

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

PARSER_VERSION = "p1.0.0"

# Threshold para escolha automática do modo de execução. Abaixo, o overhead de
# spawn/IPC do ProcessPool ultrapassa o ganho do paralelismo.
_PARALLEL_THRESHOLD = 200

# Heurística para skip de paralelo quando workers foi explicitado (>1) mas o
# universo é pequeno demais para amortizar overhead.
_PARALLEL_MIN_FILES = 50

# Default workers cap quando não informado pelo chamador.
_DEFAULT_WORKERS_CAP = 8

# Chunksize do pool.map — balanceia overhead de IPC vs latência.
_POOL_CHUNKSIZE = 20

# Limite de prints de erro para não poluir stderr em ingest grande quebrado.
_MAX_ERROR_PRINTS = 5

# Tipos de função que NÃO viram chunk (ficam apenas em chamadas_funcao).
_NON_CHUNK_KINDS = frozenset({"mvc_hook"})

# Regex para redact secrets — URLs com user:pass, tokens hex >=40 chars.
_REDACT_URL_RE = re.compile(r"https?://[^:\s/@]+:[^@\s]+@", re.IGNORECASE)
_REDACT_TOKEN_RE = re.compile(r"\b[a-f0-9]{40,}\b", re.IGNORECASE)


def _iso_now() -> str:
    """Timestamp ISO-8601 UTC sem microssegundos (compatível com SQLite datetime)."""
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _redact(text: str) -> str:
    """Mascara segredos óbvios em snippets/contextos quando ``redact_secrets`` está ativo."""
    text = _REDACT_URL_RE.sub("https://[REDACTED]@", text)
    return _REDACT_TOKEN_RE.sub("[REDACTED]", text)


def _decide_workers(requested: int | None, num_files: int) -> int:
    """Decide número efetivo de workers.

    - ``requested == 0``: explicit single-thread.
    - ``num_files < _PARALLEL_THRESHOLD``: single-thread (overhead não compensa).
    - ``requested is None``: ``min(_DEFAULT_WORKERS_CAP, cpu_count)``.
    - caso contrário: ``requested``.
    """
    if requested == 0:
        return 0
    if num_files < _PARALLEL_THRESHOLD:
        return 0
    if requested is None:
        return min(_DEFAULT_WORKERS_CAP, os.cpu_count() or 1)
    return requested


def _normalize_destino(destino: str) -> str:
    """Forma normalizada para lookup case-insensitive: uppercase, sem prefixo ``U_``."""
    norm = destino.upper()
    if norm.startswith("U_"):
        norm = norm[2:]
    return norm


def _parse_worker(args: tuple[Path, bool]) -> tuple[Path, dict[str, Any] | None, str | None, list[dict[str, Any]] | None, str | None]:
    """Worker do ProcessPool: parse + lint do arquivo. Retorna tupla pickle-safe.

    Não toca SQLite. Em caso de erro, retorna (fp, None, None, None, msg).
    O parâmetro ``redact_secrets`` é aplicado pelo writer (não aqui) para
    garantir snippets crus consistentes entre serial e paralelo.
    """
    fp, _redact_flag = args
    try:
        parsed = parse_source(fp)
        content = fp.read_text(
            encoding=parsed.get("encoding", "cp1252"), errors="replace"
        )
        findings = lint_module.lint_source(parsed, content)
        return (fp, parsed, content, findings, None)
    except Exception as exc:  # worker boundary — qualquer falha vira registro de erro
        return (fp, None, None, None, str(exc))


def _delete_dependents(conn: sqlite3.Connection, arquivo: str) -> None:
    """Remove rows dependentes de ``arquivo`` em todas as tabelas filho.

    Tabelas com FK ON DELETE CASCADE (fonte_chunks, fonte_tabela) seriam limpas
    automaticamente quando ``fontes`` é deletado, mas usamos REPLACE em fontes
    (que NÃO dispara CASCADE no SQLite) — então limpamos explicitamente.
    """
    # chamadas_funcao usa coluna arquivo_origem em vez de arquivo.
    for table in (
        "fonte_chunks",
        "fonte_tabela",
        "parametros_uso",
        "perguntas_uso",
        "operacoes_escrita",
        "sql_embedado",
        "rest_endpoints",
        "http_calls",
        "env_openers",
        "log_calls",
        "defines",
        "lint_findings",
    ):
        conn.execute(f"DELETE FROM {table} WHERE arquivo=?", (arquivo,))
    conn.execute(
        "DELETE FROM chamadas_funcao WHERE arquivo_origem=?", (arquivo,)
    )


def _write_parsed(  # noqa: PLR0912, PLR0915 — escrita verbosa: 12 tabelas dependentes
    conn: sqlite3.Connection,
    root: Path,
    fp: Path,
    parsed: dict[str, Any],
    content: str,
    findings: list[dict[str, Any]],
    counters: dict[str, int],
    no_content: bool,
    redact_secrets: bool,
) -> None:
    """Escreve um fonte parseado em todas as tabelas dependentes.

    Estratégia: DELETE WHERE arquivo=? em filhos, REPLACE em fontes. Tudo
    dentro da transação aberta pelo caller — caller faz commit.
    """
    arquivo = parsed["arquivo"]
    try:
        caminho_relativo = fp.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        # fp não está sob root (não esperado no fluxo normal — defensivo).
        caminho_relativo = fp.as_posix()
    tipo_arquivo = fp.suffix.lower().lstrip(".")

    # Stat para mtime/size (necessário para incremental).
    try:
        st = fp.stat()
        mtime_ns = st.st_mtime_ns
        size_bytes = st.st_size
    except OSError:
        mtime_ns = 0
        size_bytes = 0

    _delete_dependents(conn, arquivo)

    # Tabelas referenciadas: dict {read, write, reclock} -> JSON.
    tabelas_ref = parsed.get("tabelas_ref", {}) or {}

    # Listas de funcoes/user_funcs/pontos_entrada (nomes simples).
    funcoes_list = parsed.get("funcoes", []) or []
    funcoes_nomes = sorted({f["nome"] for f in funcoes_list if f.get("nome")})
    user_funcs = sorted(
        {f["nome"] for f in funcoes_list if f.get("kind") == "user_function"}
    )

    # Pontos de entrada — User Functions com nome em padrão PE.
    # Reusa _PE_NAME_RE do parser (importado em top-level).
    pontos_entrada = sorted(
        {
            f["nome"]
            for f in funcoes_list
            if f.get("kind") == "user_function" and _PE_NAME_RE.match(f.get("nome", "").upper())
        }
    )

    # Calls auxiliares para fontes.calls_u / calls_execblock
    chamadas_list = parsed.get("chamadas", []) or []
    calls_u = sorted(
        {c["destino"] for c in chamadas_list if c.get("tipo") == "user_func"}
    )
    calls_execblock = sorted(
        {c["destino"] for c in chamadas_list if c.get("tipo") == "execblock"}
    )

    # UPSERT na tabela fontes (REPLACE atômico via INSERT OR REPLACE).
    conn.execute(
        """
        INSERT OR REPLACE INTO fontes (
            arquivo, caminho, caminho_relativo, tipo, modulo,
            funcoes, user_funcs, pontos_entrada, tabelas_ref, write_tables,
            includes, calls_u, calls_execblock, fields_ref, lines_of_code,
            hash, source_type, capabilities, ws_structures, encoding,
            reclock_tables, mtime_ns, size_bytes, indexed_at, namespace,
            tipo_arquivo, parser_version
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?
        )
        """,
        (
            arquivo,
            str(fp),
            caminho_relativo,
            "custom",
            "",
            json.dumps(funcoes_nomes, ensure_ascii=False),
            json.dumps(user_funcs, ensure_ascii=False),
            json.dumps(pontos_entrada, ensure_ascii=False),
            json.dumps(tabelas_ref.get("read", []), ensure_ascii=False),
            json.dumps(tabelas_ref.get("write", []), ensure_ascii=False),
            json.dumps(parsed.get("includes", []), ensure_ascii=False),
            json.dumps(calls_u, ensure_ascii=False),
            json.dumps(calls_execblock, ensure_ascii=False),
            json.dumps(parsed.get("campos_ref", []), ensure_ascii=False),
            int(parsed.get("lines_of_code", 0)),
            parsed.get("hash", ""),
            parsed.get("source_type", "outro"),
            json.dumps(parsed.get("capabilities", []), ensure_ascii=False),
            json.dumps(parsed.get("ws_structures", {}), ensure_ascii=False),
            parsed.get("encoding", ""),
            json.dumps(tabelas_ref.get("reclock", []), ensure_ascii=False),
            mtime_ns,
            size_bytes,
            _iso_now(),
            parsed.get("namespace", ""),
            tipo_arquivo,
            PARSER_VERSION,
        ),
    )

    # fonte_chunks — uma row por função (skip mvc_hook que não vira chunk real).
    lines = content.splitlines()
    chunk_rows: list[tuple[Any, ...]] = []
    for f in funcoes_list:
        kind = f.get("kind", "function")
        if kind in _NON_CHUNK_KINDS:
            continue
        nome = f.get("nome", "")
        ini = int(f.get("linha_inicio", 1))
        fim = int(f.get("linha_fim", ini))
        # Assinatura = primeira linha do header (best-effort)
        assinatura = lines[ini - 1].strip() if 1 <= ini <= len(lines) else ""
        if no_content:
            chunk_content = ""
        else:
            chunk_content = "\n".join(lines[ini - 1 : fim])
            if redact_secrets:
                chunk_content = _redact(chunk_content)
        chunk_rows.append(
            (
                # ID inclui linha_inicio para distinguir funções com mesmo nome no
                # mesmo arquivo (Static + User, redefinições, overloads).
                f"{arquivo}::{nome}@{ini}",
                arquivo,
                nome,
                nome.upper().strip(),
                kind,
                f.get("classe", "") or "",
                ini,
                fim,
                assinatura[:500],
                chunk_content,
                "",
            )
        )
        counters["chunks"] += 1
    if chunk_rows:
        # INSERT OR REPLACE: idempotente; se mesmo (arquivo, funcao, linha) reaparece
        # após reindex, substitui em vez de levantar UNIQUE constraint.
        conn.executemany(
            """
            INSERT OR REPLACE INTO fonte_chunks (
                id, arquivo, funcao, funcao_norm, tipo_simbolo, classe,
                linha_inicio, linha_fim, assinatura, content, modulo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            chunk_rows,
        )

    # fonte_tabela — normaliza tabelas_ref em rows (arquivo, tabela, modo).
    ft_rows: list[tuple[str, str, str]] = []
    seen_ft: set[tuple[str, str, str]] = set()
    for modo in ("read", "write", "reclock"):
        for tabela in tabelas_ref.get(modo, []) or []:
            key = (arquivo, tabela, modo)
            if key in seen_ft:
                continue
            seen_ft.add(key)
            ft_rows.append(key)
    if ft_rows:
        conn.executemany(
            "INSERT INTO fonte_tabela (arquivo, tabela, modo) VALUES (?, ?, ?)",
            ft_rows,
        )

    # chamadas_funcao
    cf_rows: list[tuple[Any, ...]] = []
    for c in chamadas_list:
        destino = c.get("destino", "")
        contexto = c.get("contexto", "") or ""
        if redact_secrets and contexto:
            contexto = _redact(contexto)
        cf_rows.append(
            (
                arquivo,
                "",  # funcao_origem (best-effort vazio no MVP)
                int(c.get("linha_origem", 0)),
                c.get("tipo", ""),
                destino,
                _normalize_destino(destino),
                None,
                None,
                contexto[:500],
            )
        )
        counters["chamadas"] += 1
    if cf_rows:
        conn.executemany(
            """
            INSERT INTO chamadas_funcao (
                arquivo_origem, funcao_origem, linha_origem, tipo, destino,
                destino_norm, arquivo_destino, funcao_destino, contexto
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            cf_rows,
        )

    # parametros_uso
    pu_rows: list[tuple[Any, ...]] = []
    for p in parsed.get("parametros_uso", []) or []:
        pu_rows.append(
            (
                arquivo,
                p.get("nome", ""),
                p.get("modo", "read"),
                p.get("default_decl", "") or "",
            )
        )
        counters["params"] += 1
    if pu_rows:
        conn.executemany(
            "INSERT INTO parametros_uso (arquivo, parametro, modo, default_decl) "
            "VALUES (?, ?, ?, ?)",
            pu_rows,
        )

    # perguntas_uso
    pgu_rows = [(arquivo, g) for g in parsed.get("perguntas_uso", []) or []]
    if pgu_rows:
        conn.executemany(
            "INSERT INTO perguntas_uso (arquivo, grupo) VALUES (?, ?)",
            pgu_rows,
        )

    # sql_embedado
    sqle_rows: list[tuple[Any, ...]] = []
    for s in parsed.get("sql_embedado", []) or []:
        snippet = s.get("snippet", "") or ""
        if redact_secrets and snippet:
            snippet = _redact(snippet)
        sqle_rows.append(
            (
                arquivo,
                s.get("funcao", "") or "",
                int(s.get("linha", 0)),
                s.get("operacao", "select"),
                json.dumps(s.get("tabelas", []), ensure_ascii=False),
                snippet,
            )
        )
    if sqle_rows:
        conn.executemany(
            """
            INSERT INTO sql_embedado (
                arquivo, funcao, linha, operacao, tabelas, snippet
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            sqle_rows,
        )

    # rest_endpoints
    rest_rows: list[tuple[Any, ...]] = []
    for ep in parsed.get("rest_endpoints", []) or []:
        rest_rows.append(
            (
                arquivo,
                ep.get("classe", "") or "",
                ep.get("funcao", "") or "",
                ep.get("verbo", "") or "",
                ep.get("path", "") or "",
                ep.get("annotation_style", "") or "",
            )
        )
    if rest_rows:
        conn.executemany(
            """
            INSERT INTO rest_endpoints (
                arquivo, classe, funcao, verbo, path, annotation_style
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rest_rows,
        )

    # http_calls
    hc_rows: list[tuple[Any, ...]] = []
    for h in parsed.get("http_calls", []) or []:
        url = h.get("url_literal", "") or ""
        if redact_secrets and url:
            url = _redact(url)
        hc_rows.append(
            (
                arquivo,
                h.get("funcao", "") or "",
                int(h.get("linha", 0)),
                h.get("metodo", ""),
                url,
            )
        )
    if hc_rows:
        conn.executemany(
            """
            INSERT INTO http_calls (
                arquivo, funcao, linha, metodo, url_literal
            ) VALUES (?, ?, ?, ?, ?)
            """,
            hc_rows,
        )

    # env_openers
    env_rows: list[tuple[Any, ...]] = []
    for e in parsed.get("env_openers", []) or []:
        env_rows.append(
            (
                arquivo,
                e.get("funcao", "") or "",
                int(e.get("linha", 0)),
                e.get("empresa", "") or "",
                e.get("filial", "") or "",
                e.get("environment", "") or "",
                e.get("modulo", "") or "",
            )
        )
    if env_rows:
        conn.executemany(
            """
            INSERT INTO env_openers (
                arquivo, funcao, linha, empresa, filial, environment, modulo
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            env_rows,
        )

    # log_calls
    log_rows: list[tuple[Any, ...]] = []
    for log in parsed.get("log_calls", []) or []:
        log_rows.append(
            (
                arquivo,
                log.get("funcao", "") or "",
                int(log.get("linha", 0)),
                log.get("nivel", "") or "",
                log.get("categoria", "") or "",
            )
        )
    if log_rows:
        conn.executemany(
            "INSERT INTO log_calls (arquivo, funcao, linha, nivel, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            log_rows,
        )

    # defines
    def_rows: list[tuple[Any, ...]] = []
    for d in parsed.get("defines", []) or []:
        def_rows.append(
            (
                arquivo,
                d.get("nome", ""),
                d.get("valor", "") or "",
                int(d.get("linha", 0)),
            )
        )
    if def_rows:
        conn.executemany(
            "INSERT INTO defines (arquivo, nome, valor, linha) VALUES (?, ?, ?, ?)",
            def_rows,
        )

    # lint_findings
    lint_rows: list[tuple[Any, ...]] = []
    for f in findings:
        snippet = f.get("snippet", "") or ""
        if redact_secrets and snippet:
            snippet = _redact(snippet)
        lint_rows.append(
            (
                arquivo,
                f.get("funcao", "") or "",
                int(f.get("linha", 0)),
                f.get("regra_id", ""),
                f.get("severidade", "warning"),
                snippet,
                f.get("sugestao_fix", "") or "",
            )
        )
        counters["lint_findings"] += 1
    if lint_rows:
        conn.executemany(
            """
            INSERT INTO lint_findings (
                arquivo, funcao, linha, regra_id, severidade, snippet, sugestao_fix
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            lint_rows,
        )

    counters["arquivos_ok"] += 1


def _ingest_serial(
    conn: sqlite3.Connection,
    files: list[Path],
    root: Path,
    counters: dict[str, int],
    no_content: bool,
    redact_secrets: bool,
) -> None:
    """Single-thread: parse + write inline. Commits a cada 50 arquivos."""
    error_prints = 0
    for i, fp in enumerate(files, 1):
        try:
            parsed = parse_source(fp)
            content = fp.read_text(
                encoding=parsed.get("encoding", "cp1252"), errors="replace"
            )
            findings = lint_module.lint_source(parsed, content)
            _write_parsed(
                conn, root, fp, parsed, content, findings,
                counters, no_content, redact_secrets,
            )
        except Exception as exc:  # engolimos para continuar batch
            counters["arquivos_failed"] += 1
            if error_prints < _MAX_ERROR_PRINTS:
                print(f"WARN: falha em {fp.name}: {exc}", file=sys.stderr)
                error_prints += 1
        if i % 50 == 0:
            conn.commit()
    conn.commit()


def _ingest_parallel(
    conn: sqlite3.Connection,
    files: list[Path],
    root: Path,
    counters: dict[str, int],
    workers: int,
    no_content: bool,
    redact_secrets: bool,
) -> None:
    """ProcessPool: workers parseiam + lintam em paralelo, writer único faz INSERTs."""
    method = "fork" if sys.platform.startswith("linux") else "spawn"
    ctx = mp.get_context(method)
    error_prints = 0

    args_list = [(fp, redact_secrets) for fp in files]
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
        results = list(pool.map(_parse_worker, args_list, chunksize=_POOL_CHUNKSIZE))

    for i, (fp, parsed, content, findings, error) in enumerate(results, 1):
        if error or parsed is None or content is None or findings is None:
            counters["arquivos_failed"] += 1
            if error_prints < _MAX_ERROR_PRINTS:
                print(f"WARN: falha em {fp.name}: {error}", file=sys.stderr)
                error_prints += 1
            continue
        try:
            _write_parsed(
                conn, root, fp, parsed, content, findings,
                counters, no_content, redact_secrets,
            )
        except Exception as exc:  # writer-side falha = registro contável
            counters["arquivos_failed"] += 1
            counters["arquivos_ok"] = max(0, counters["arquivos_ok"])  # safe
            if error_prints < _MAX_ERROR_PRINTS:
                print(f"WARN: write falhou em {fp.name}: {exc}", file=sys.stderr)
                error_prints += 1
        if i % 50 == 0:
            conn.commit()
    conn.commit()


def ingest(
    root: Path,
    *,
    workers: int | None = None,
    incremental: bool = True,
    no_content: bool = False,
    redact_secrets: bool = False,
) -> dict[str, Any]:
    """Pipeline completo: scan -> parse -> write -> FTS5 rebuild.

    Args:
        root: raiz do projeto cliente (contém ``.prw``/``.tlpp``/...).
        workers: ``0`` = single-thread; ``None`` = adaptive (single-thread se
            <200 arquivos, senão ProcessPool com ``min(8, cpu_count)``); ``N`` =
            ProcessPool com N workers (clamp para 0 se universo <200).
        incremental: se True, pula arquivos cujo ``mtime_ns`` no DB já é >=
            o atual no FS (default True).
        no_content: se True, persiste ``fonte_chunks.content = ''`` (apenas
            metadata — útil para reduzir DB size).
        redact_secrets: se True, regex-mask URLs com credenciais e tokens
            hex >=40 chars em snippets/contextos antes de gravar.

    Returns:
        Dict com counters: ``arquivos_total``, ``arquivos_ok``,
        ``arquivos_skipped``, ``arquivos_failed``, ``chunks``, ``chamadas``,
        ``params``, ``lint_findings``, ``duration_ms``, e (v0.3.13)
        ``lookup_hash_changed`` (bool — True se o bundle de lookups mudou
        desde o ingest anterior, sinaliza pegadinha do ``--incremental``)
        + ``previous_lookup_hash`` (str | None).
    """
    start_time = time.time()

    db_path = root / ".plugadvpl" / "index.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = open_db(db_path)
    try:
        apply_migrations(conn)
        init_meta(conn, project_root=str(root), cli_version=_cli_version)
        # Captura o hash ANTES de seed_lookups sobrescrever — permite detectar
        # se o bundle de lookups (lint_rules, funcoes_restritas, ...) mudou
        # entre a versão do binário antiga (que gravou o índice) e a atual.
        previous_lookup_hash = get_meta(conn, "lookup_bundle_hash")
        seed_lookups(conn)
        current_lookup_hash = get_meta(conn, "lookup_bundle_hash")
        set_meta(conn, "parser_version", PARSER_VERSION)
        set_meta(conn, "cli_version", _cli_version)

        all_files = scan_sources(root)

        # Stale filter (incremental).
        if incremental:
            already: dict[str, int] = {
                row[0]: int(row[1] or 0)
                for row in conn.execute("SELECT arquivo, mtime_ns FROM fontes")
            }
            files_to_parse: list[Path] = []
            for f in all_files:
                try:
                    cur_mtime = f.stat().st_mtime_ns
                except OSError:
                    continue
                if f.name not in already or cur_mtime > already[f.name]:
                    files_to_parse.append(f)
        else:
            files_to_parse = list(all_files)

        effective_workers = _decide_workers(workers, len(files_to_parse))

        counters: dict[str, Any] = {
            "arquivos_total": len(all_files),
            "arquivos_ok": 0,
            "arquivos_skipped": len(all_files) - len(files_to_parse),
            "arquivos_failed": 0,
            "chunks": 0,
            "chamadas": 0,
            "params": 0,
            "lint_findings": 0,
            "duration_ms": 0,
            # v0.3.13: caller (CLI) usa esses campos pra detectar a pegadinha do
            # `--incremental` após `uv tool upgrade` — quando lookup_bundle muda
            # mas os arquivos pulados não foram re-avaliados contra as regras novas.
            "lookup_hash_changed": (
                previous_lookup_hash is not None
                and previous_lookup_hash != current_lookup_hash
            ),
            "previous_lookup_hash": previous_lookup_hash,
        }

        if effective_workers <= 1 or len(files_to_parse) < _PARALLEL_MIN_FILES:
            _ingest_serial(
                conn, files_to_parse, root, counters, no_content, redact_secrets,
            )
        else:
            _ingest_parallel(
                conn, files_to_parse, root, counters, effective_workers,
                no_content, redact_secrets,
            )

        # FTS5 rebuild — uma única vez ao final, mais barato do que insert-by-insert.
        conn.execute(
            "INSERT INTO fonte_chunks_fts(fonte_chunks_fts) VALUES('rebuild')"
        )
        conn.execute(
            "INSERT INTO fonte_chunks_fts_tri(fonte_chunks_fts_tri) VALUES('rebuild')"
        )
        conn.commit()

        # Update meta totals — refletem o estado final do DB.
        for table, key in (
            ("fontes", "total_arquivos"),
            ("fonte_chunks", "total_chunks"),
            ("chamadas_funcao", "total_chamadas"),
            ("lint_findings", "total_lint_findings"),
        ):
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            set_meta(conn, key, str(n))
        set_meta(conn, "indexed_at", _iso_now())

        counters["duration_ms"] = int((time.time() - start_time) * 1000)
        return counters
    finally:
        close_db(conn)
