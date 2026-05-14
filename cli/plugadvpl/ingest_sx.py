"""Ingest pipeline para o Universo 2 — Dicionário SX exportado em CSV.

Pattern espelhado de :mod:`plugadvpl.ingest`: abre DB, aplica migrations, parseia
cada CSV via :mod:`plugadvpl.parsing.sx_csv` e grava em batches via
``executemany(INSERT OR REPLACE ...)``. Idempotente — rodar 2x produz o mesmo
estado final.

Inputs: diretório com os CSVs (busca case-insensitive por ``sx1.csv``, ``sx2.csv``,
``six.csv``, ``sxa.csv``, ..., ``sxg.csv``). Arquivos faltantes são pulados sem
falhar (counter ``csvs_skipped`` reflete).

Output: counters dict com ``csvs_total/ok/skipped``, ``total_rows``, ``duration_ms``
e ``per_table`` (rows por tabela SQL).
"""
from __future__ import annotations

import datetime as _dt
import sys
import time
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
from plugadvpl.parsing import sx_csv

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable
    from pathlib import Path

# Nome canonical do CSV → (parser, target_table, columns_in_order).
# Ordem importa: tabelas com PK que outros referenciam vêm primeiro
# (sx2 antes de sx3, sx3 antes de sx7/sxb, sx2 antes de sx9...).
_SX_INGEST_PLAN: list[tuple[str, str, list[str]]] = [
    ("sx2.csv",  "tabelas",            ["codigo", "nome", "modo", "custom"]),
    ("sx3.csv",  "campos",             [
        "tabela", "campo", "tipo", "tamanho", "decimal",
        "titulo", "descricao", "validacao", "inicializador", "obrigatorio",
        "custom", "f3", "cbox", "vlduser", "when_expr",
        "proprietario", "browse", "trigger_flag", "visual", "context",
        "folder", "grpsxg",
    ]),
    ("six.csv",  "indices",            [
        "tabela", "ordem", "chave", "descricao", "proprietario",
        "f3", "nickname", "showpesq", "custom",
    ]),
    ("sx7.csv",  "gatilhos",           [
        "campo_origem", "sequencia", "campo_destino", "regra", "tipo",
        "tabela", "condicao", "proprietario", "seek", "alias",
        "ordem", "chave", "custom",
    ]),
    ("sx6.csv",  "parametros",         [
        "filial", "variavel", "tipo", "descricao", "conteudo",
        "proprietario", "custom", "validacao", "init",
    ]),
    ("sx1.csv",  "perguntas",          [
        "grupo", "ordem", "pergunta", "variavel", "tipo",
        "tamanho", "decimal", "f3", "validacao", "conteudo_padrao",
    ]),
    ("sx5.csv",  "tabelas_genericas",  ["filial", "tabela", "chave", "descricao", "custom"]),
    ("sx9.csv",  "relacionamentos",    [
        "tabela_origem", "identificador", "tabela_destino",
        "expressao_origem", "expressao_destino", "proprietario",
        "condicao_sql", "custom",
    ]),
    ("sxa.csv",  "pastas",             ["alias", "ordem", "descricao", "proprietario", "agrupamento"]),
    ("sxb.csv",  "consultas",          ["alias", "tipo", "sequencia", "coluna", "descricao", "conteudo"]),
    ("sxg.csv",  "grupos_campo",       ["grupo", "descricao", "tamanho_max", "tamanho_min", "tamanho", "total_campos"]),
]

# Mapeamento de nome de arquivo → função de parsing (resolvida por nome).
_PARSER_BY_FILE: dict[str, Callable[[Path], list[dict[str, Any]]]] = {
    "sx1.csv": sx_csv.parse_sx1,
    "sx2.csv": sx_csv.parse_sx2,
    "sx3.csv": sx_csv.parse_sx3,
    "sx5.csv": sx_csv.parse_sx5,
    "sx6.csv": sx_csv.parse_sx6,
    "sx7.csv": sx_csv.parse_sx7,
    "sx9.csv": sx_csv.parse_sx9,
    "sxa.csv": sx_csv.parse_sxa,
    "sxb.csv": sx_csv.parse_sxb,
    "sxg.csv": sx_csv.parse_sxg,
    "six.csv": sx_csv.parse_six,
}

_BATCH_SIZE = 1000

# Mapa tabela → colunas PK (espelha as migrations 001 + 002 + 004). Usado pra
# detectar dedup silencioso (linhas do CSV que colidem na PK e são sobrescritas
# por INSERT OR REPLACE). v0.3.14.
_PK_COLS_BY_TABLE: dict[str, tuple[str, ...]] = {
    "tabelas":            ("codigo",),
    "campos":             ("tabela", "campo"),
    "indices":            ("tabela", "ordem"),
    "gatilhos":           ("campo_origem", "sequencia"),
    "parametros":         ("filial", "variavel"),
    "perguntas":          ("grupo", "ordem"),
    "tabelas_genericas":  ("filial", "tabela", "chave"),
    "relacionamentos":    ("tabela_origem", "identificador", "tabela_destino"),
    "pastas":             ("alias", "ordem"),
    "consultas":          ("alias", "tipo", "sequencia", "coluna"),  # v0.3.14: +tipo
    "grupos_campo":       ("grupo",),
}

# Mapa CSV → meta.* counter (apenas para os que importam para o usuário/skill).
_META_KEY_BY_TABLE: dict[str, str] = {
    "tabelas":            "total_sx_tabelas",
    "campos":             "total_sx_campos",
    "indices":            "total_sx_indices",
    "gatilhos":           "total_sx_gatilhos",
    "parametros":         "total_sx_parametros",
    "perguntas":          "total_sx_perguntas",
    "tabelas_genericas":  "total_sx_tabelas_genericas",
    "relacionamentos":    "total_sx_relacionamentos",
    "pastas":             "total_sx_pastas",
    "consultas":          "total_sx_consultas",
    "grupos_campo":       "total_sx_grupos_campo",
}


def _iso_now() -> str:
    """Timestamp ISO-8601 UTC (mesmo formato usado em :mod:`plugadvpl.ingest`)."""
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_file_ci(directory: Path, name: str) -> Path | None:
    """Localiza ``name`` em ``directory`` ignorando case (Windows-friendly)."""
    exact = directory / name
    if exact.exists():
        return exact
    name_lower = name.lower()
    try:
        for f in directory.iterdir():
            if f.name.lower() == name_lower:
                return f
    except OSError:
        return None
    return None


def _build_insert_sql(table: str, columns: list[str]) -> str:
    """``INSERT OR REPLACE INTO <table> (cols) VALUES (?, ?, ...)`` para executemany."""
    cols_sql = ", ".join(columns)
    placeholders = ", ".join("?" * len(columns))
    return f"INSERT OR REPLACE INTO {table} ({cols_sql}) VALUES ({placeholders})"


def _bulk_insert(
    conn: sqlite3.Connection,
    table: str,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> int:
    """Insere ``rows`` em batches de :data:`_BATCH_SIZE` via executemany. Retorna count."""
    if not rows:
        return 0
    sql = _build_insert_sql(table, columns)
    inserted = 0
    batch: list[tuple[Any, ...]] = []
    for row in rows:
        batch.append(tuple(row.get(c, "") for c in columns))
        if len(batch) >= _BATCH_SIZE:
            conn.executemany(sql, batch)
            inserted += len(batch)
            batch = []
    if batch:
        conn.executemany(sql, batch)
        inserted += len(batch)
    return inserted


def ingest_sx(
    csv_dir: Path,
    db_path: Path,
    *,
    progress_callback: Callable[[str, int], None] | None = None,
) -> dict[str, Any]:
    """Pipeline completo: para cada CSV SX em ``csv_dir``, parse + insert no DB.

    Args:
        csv_dir: diretório contendo os CSVs (``sx1.csv``, ``sx2.csv``, ...).
            Lookup é case-insensitive (``SX2.csv`` também funciona).
        db_path: caminho do SQLite (criado se não existir; migrations aplicadas).
        progress_callback: opcional, chamado com ``(csv_name, rows_inserted)``
            após cada CSV concluído. Útil para CLI Rich progress bar.

    Returns:
        ``{csvs_total, csvs_ok, csvs_skipped, total_rows, duration_ms,
        per_table: {tabela: rows, ...}}``.

        Exemplo:

        .. code-block:: python

            counters = ingest_sx(Path("/d/Clientes/CSV"), Path("./.plugadvpl/index.db"))
            print(counters["per_table"]["campos"])  # → 80123
    """
    start_time = time.time()
    csv_dir = csv_dir.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    counters: dict[str, Any] = {
        "csvs_total": len(_SX_INGEST_PLAN),
        "csvs_ok": 0,
        "csvs_skipped": 0,
        "csvs_failed": 0,
        "total_rows": 0,
        "per_table": {},
        "duration_ms": 0,
    }

    conn = open_db(db_path)
    try:
        apply_migrations(conn)
        # v0.3.15 (#13 do QA report): NAO chamar init_meta(project_root=csv_dir)
        # aqui — sobrescrevia o project_root real (raiz do projeto) com o csv_dir.
        # Em vez disso, so escrevemos project_root como fallback quando ainda
        # nao existe (caso usuario rode `ingest-sx` antes de `init`/`ingest`).
        # cli_version e sempre atualizada (consistente com `ingest`).
        existing_root = get_meta(conn, "project_root")
        if not existing_root:
            init_meta(conn, project_root=str(csv_dir), cli_version=_cli_version)
        else:
            set_meta(conn, "cli_version", _cli_version)
        seed_lookups(conn)

        for csv_name, table, columns in _SX_INGEST_PLAN:
            file_path = _find_file_ci(csv_dir, csv_name)
            if file_path is None:
                counters["csvs_skipped"] += 1
                counters["per_table"][table] = 0
                if progress_callback is not None:
                    progress_callback(csv_name, 0)
                continue
            parser = _PARSER_BY_FILE[csv_name]
            try:
                rows = parser(file_path)
                # v0.3.14: contar PKs distintas ANTES do bulk_insert. Quando
                # `distinct < len(rows)`, sabemos exatamente quantas linhas o
                # INSERT OR REPLACE silenciosamente sobrescreveu (sintoma do
                # bug da SXB com PK incompleta; agora detectado pra qualquer
                # tabela cujo dump tenha duplicatas).
                pk_cols = _PK_COLS_BY_TABLE.get(table, ())
                distinct = (
                    len({tuple(r.get(c, "") for c in pk_cols) for r in rows})
                    if pk_cols else len(rows)
                )
                inserted = _bulk_insert(conn, table, columns, rows)
                conn.commit()
                counters["per_table"][table] = inserted
                counters["total_rows"] += inserted
                counters["csvs_ok"] += 1
                if progress_callback is not None:
                    progress_callback(csv_name, inserted)
                # Aviso de dedup quando linhas do CSV colidiram na PK. Limite de 1
                # linha pra evitar ruído em diffs minúsculos (1 dup em 60k = ok),
                # mas com info suficiente pra IA/usuário investigar.
                lost = inserted - distinct
                if lost > 0:
                    print(
                        f"WARN: tabela '{table}': {inserted} linhas CSV "
                        f"→ {distinct} distintas após PK dedup "
                        f"({lost} duplicada(s) na PK {pk_cols} foram sobrescrita(s)).",
                        file=sys.stderr,
                    )
            except Exception as exc:  # boundary: erro em 1 CSV não derruba o batch
                counters["csvs_failed"] += 1
                counters["per_table"][table] = 0
                print(
                    f"WARN: falha ao ingerir {csv_name}: {exc}",
                    file=sys.stderr,
                )

        # Pós-processamento: atualiza grupos_campo.total_campos via JOIN em campos.grpsxg.
        # Só faz sentido se ambas as tabelas têm rows.
        if (
            counters["per_table"].get("grupos_campo", 0) > 0
            and counters["per_table"].get("campos", 0) > 0
        ):
            conn.execute(
                """
                UPDATE grupos_campo
                SET total_campos = (
                    SELECT COUNT(*) FROM campos
                    WHERE campos.grpsxg = grupos_campo.grupo
                )
                """
            )
            conn.commit()

        # Atualiza meta com totais (refletem o estado final do DB, não o batch atual).
        for table, key in _META_KEY_BY_TABLE.items():
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            set_meta(conn, key, str(n))
        set_meta(conn, "last_sx_ingest_at", _iso_now())
        set_meta(conn, "sx_csv_dir", str(csv_dir))

        counters["duration_ms"] = int((time.time() - start_time) * 1000)
        return counters
    finally:
        close_db(conn)
