"""Output formatters: ``table`` / ``json`` / ``md`` + limit handling + ``next steps`` hints.

Convenções:

- **stderr** recebe o output humano (rich tables, mensagens decorativas) — assim
  a saída de dados em ``stdout`` é pipeable por scripts/LLMs.
- **stdout** é reservado para dados estruturados (``json``, ``md``).
- ``limit`` corta a lista; ``offset`` pula o início; quando há mais resultados
  o renderer adiciona uma linha ``... e mais N resultados`` para sinalizar
  truncamento.
- ``next_steps`` é uma lista opcional de comandos sugeridos (LLM hints), sempre
  impressa em stderr para não poluir o stdout JSON/MD.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

# stderr: human-readable (rich tables, hints).
# stdout: dados estruturados (json/md).
err_console = Console(stderr=True)
out_console = Console(stderr=False)


def render(
    rows: list[dict[str, Any]],
    *,
    format: str = "table",
    columns: list[str] | None = None,
    title: str | None = None,
    limit: int = 20,
    offset: int = 0,
    compact: bool = False,
    next_steps: list[str] | None = None,
) -> None:
    """Renderiza ``rows`` no formato escolhido.

    Args:
        rows: lista de dicts (cada dict = 1 linha).
        format: ``"table"`` (rich, stderr), ``"json"`` (stdout) ou
            ``"md"`` (markdown table, stdout).
        columns: ordem explícita das colunas. Se ``None``, deriva
            do primeiro item de ``rows``.
        title: título opcional impresso antes da tabela (formato ``table``).
        limit: máximo de rows mostradas. Default 20. ``0`` = ilimitado.
        offset: pula as primeiras N rows antes de aplicar ``limit``.
        compact: ``True`` desabilita ``show_lines`` (rich) e indent (json).
        next_steps: lista de strings impressas em stderr como sugestões
            de próximos comandos (hints para LLMs).
    """
    total = len(rows)
    if offset > 0:
        rows = rows[offset:]
    truncated = limit > 0 and (total - offset) > limit
    if limit > 0:
        rows = rows[:limit]
    remaining = total - offset - limit if truncated else 0

    if format == "json":
        _render_json(rows, total, truncated, compact)
    elif format == "md":
        _render_md(rows, columns, truncated, remaining)
    else:
        _render_table(rows, columns, title, compact, truncated, remaining)

    _emit_next_steps(next_steps)


def _render_json(
    rows: list[dict[str, Any]],
    total: int,
    truncated: bool,
    compact: bool,
) -> None:
    """Dump JSON em stdout (com newline final + flush)."""
    payload = {
        "rows": rows,
        "total": total,
        "shown": len(rows),
        "truncated": truncated,
    }
    sys.stdout.write(
        json.dumps(payload, ensure_ascii=False, indent=None if compact else 2)
    )
    sys.stdout.write("\n")
    sys.stdout.flush()


def _render_md(
    rows: list[dict[str, Any]],
    columns: list[str] | None,
    truncated: bool,
    remaining: int,
) -> None:
    """Tabela markdown em stdout."""
    if not rows:
        sys.stdout.write("_(sem resultados)_\n")
        sys.stdout.flush()
        return
    cols = columns or list(rows[0].keys())
    sys.stdout.write("| " + " | ".join(cols) + " |\n")
    sys.stdout.write("|" + "|".join("---" for _ in cols) + "|\n")
    for r in rows:
        sys.stdout.write(
            "| " + " | ".join(_md_cell(r.get(c, "")) for c in cols) + " |\n"
        )
    if truncated:
        sys.stdout.write(
            f"\n_... e mais {remaining} resultados; refine os filtros ou aumente --limit_\n"
        )
    sys.stdout.flush()


def _render_table(
    rows: list[dict[str, Any]],
    columns: list[str] | None,
    title: str | None,
    compact: bool,
    truncated: bool,
    remaining: int,
) -> None:
    """Tabela rich em stderr."""
    if title:
        err_console.print(f"\n[bold]{title}[/bold]")
    if not rows:
        err_console.print("[dim](sem resultados)[/dim]")
        return
    cols = columns or list(rows[0].keys())
    table = Table(show_header=True, header_style="bold", show_lines=not compact)
    for c in cols:
        table.add_column(c)
    for r in rows:
        table.add_row(*[_table_cell(r.get(c, "")) for c in cols])
    err_console.print(table)
    if truncated:
        err_console.print(
            f"[dim]... e mais {remaining} resultados; refine filtros ou aumente --limit[/dim]"
        )


def _emit_next_steps(steps: list[str] | None) -> None:
    """Imprime sugestões de próximos comandos em stderr (LLM hints)."""
    if not steps:
        return
    err_console.print("\n[dim]Próximo passo recomendado:[/dim]")
    for s in steps:
        err_console.print(f"  [cyan]{s}[/cyan]")


def _md_cell(val: Any) -> str:
    """Escapa caracteres problemáticos para markdown table cell."""
    s = str(val) if val is not None else ""
    # | quebraria a tabela; \n também.
    return s.replace("|", "\\|").replace("\n", " ")


def _table_cell(val: Any) -> str:
    """Converte qualquer valor em string segura para rich Table."""
    if val is None:
        return ""
    if isinstance(val, list | dict):
        return json.dumps(val, ensure_ascii=False)
    return str(val)
