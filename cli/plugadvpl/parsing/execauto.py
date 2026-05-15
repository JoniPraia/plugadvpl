"""Universo 3 / Feature B — ExecAuto chain expansion.

Detecta chamadas ``MsExecAuto`` / ``ExecAuto`` em fontes ADVPL/TLPP, resolve
a rotina TOTVS canônica chamada via codeblock, e cruza com catálogo
``execauto_routines.json`` pra inferir tabelas tocadas indiretamente.

Spec completo: ``docs/universo3/B-execauto-chain.md``.

Exemplo:

.. code-block:: python

    calls = extract_execauto_calls(content)
    # → list[dict] com routine/module/op_code/tables_resolved/...
"""
from __future__ import annotations

import json
import re
from importlib import resources
from typing import Any

from plugadvpl.parsing.stripper import strip_advpl

# `MsExecAuto(` ou `ExecAuto(` (Ms opcional, case-insensitive).
_EXECAUTO_RE = re.compile(r"\b(?:Ms)?ExecAuto\b\s*\(", re.IGNORECASE)
# Codeblock `{|args| body}` — não-greedy DOTALL para multi-linha.
_CODEBLOCK_RE = re.compile(r"\{\s*\|([^|]*)\|(.*?)\}", re.DOTALL)
# Primeiro identificador seguido de `(` no body — encontra a rotina chamada.
_FIRST_IDENT_CALL_RE = re.compile(r"([A-Za-z_]\w*)\s*\(")
# Argumento puramente numérico (op_code).
_NUMERIC_ARG_RE = re.compile(r"^\s*(\d+)\s*$")

_OP_LABELS = {3: "inclusao", 4: "alteracao", 5: "exclusao"}

_CATALOG_CACHE: dict[str, Any] | None = None
_ROUTINES_INDEX_CACHE: dict[str, dict[str, Any]] | None = None


def load_execauto_catalog() -> dict[str, Any]:
    """Carrega o catálogo ``execauto_routines.json`` (uma vez por processo)."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        path = resources.files("plugadvpl.lookups").joinpath("execauto_routines.json")
        _CATALOG_CACHE = json.loads(path.read_text(encoding="utf-8"))
    return _CATALOG_CACHE


def _routines_index() -> dict[str, dict[str, Any]]:
    """Indexa o catálogo por nome (uppercase) pra lookup O(1)."""
    global _ROUTINES_INDEX_CACHE
    if _ROUTINES_INDEX_CACHE is None:
        cat = load_execauto_catalog()
        _ROUTINES_INDEX_CACHE = {r["routine"].upper(): r for r in cat["routines"]}
    return _ROUTINES_INDEX_CACHE


def _find_balanced_paren(s: str, open_idx: int) -> int:
    """Dado idx de `(`, retorna idx do `)` casado. -1 se não casar."""
    depth = 0
    for i in range(open_idx, len(s)):
        c = s[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _split_top_level_commas(s: str) -> list[str]:
    """Split por vírgulas de top-level (ignora dentro de (), {}, [])."""
    parts: list[str] = []
    depth_paren = depth_brace = depth_bracket = 0
    last = 0
    for i, c in enumerate(s):
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        elif c == "{":
            depth_brace += 1
        elif c == "}":
            depth_brace -= 1
        elif c == "[":
            depth_bracket += 1
        elif c == "]":
            depth_bracket -= 1
        elif (
            c == ","
            and depth_paren == 0
            and depth_brace == 0
            and depth_bracket == 0
        ):
            parts.append(s[last:i])
            last = i + 1
    parts.append(s[last:])
    return parts


def _line_at(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _snippet_at(content: str, offset: int) -> str:
    line_start = content.rfind("\n", 0, offset) + 1
    line_end = content.find("\n", offset)
    if line_end == -1:
        line_end = len(content)
    return content[line_start:line_end].strip()


def extract_execauto_calls(content: str) -> list[dict[str, Any]]:
    """Extrai chamadas ``MsExecAuto`` resolvidas + tabelas inferidas.

    Retorna lista de dicts com:

    - ``linha`` (int) — linha 1-based do match
    - ``routine`` (str | None) — nome da rotina chamada (None se dynamic)
    - ``module`` (str | None) — módulo TOTVS (SIGAFAT/etc) ou None
    - ``routine_type`` (str | None) — cadastro/movimento ou None
    - ``op_code`` (int | None) — 3/4/5 ou outro literal
    - ``op_label`` (str | None) — inclusao/alteracao/exclusao
    - ``tables_resolved`` (list[str]) — primary + secondary do catálogo
    - ``dynamic_call`` (bool) — True se rotina não-resolvível (& macro, etc)
    - ``arg_count`` (int) — número de args do codeblock
    - ``snippet`` (str) — linha original do match
    """
    stripped = strip_advpl(content)
    routines_idx = _routines_index()
    calls: list[dict[str, Any]] = []

    for m in _EXECAUTO_RE.finditer(stripped):
        open_paren_idx = m.end() - 1
        close_paren_idx = _find_balanced_paren(stripped, open_paren_idx)
        if close_paren_idx == -1:
            continue
        outer_args_str = stripped[open_paren_idx + 1 : close_paren_idx]
        parts = _split_top_level_commas(outer_args_str)
        if not parts:
            continue
        block_part = parts[0].strip()
        cb_match = _CODEBLOCK_RE.match(block_part)
        if not cb_match:
            continue
        pipe_args = cb_match.group(1).strip()
        body = cb_match.group(2)

        if pipe_args == "":
            arg_count = 0
        else:
            arg_count = len([a for a in pipe_args.split(",") if a.strip()])

        body_lstrip = body.lstrip()
        routine: str | None = None
        dynamic = False
        if body_lstrip.startswith("&"):
            dynamic = True
        else:
            mc = _FIRST_IDENT_CALL_RE.search(body)
            if mc:
                routine = mc.group(1)
            else:
                dynamic = True

        module: str | None = None
        routine_type: str | None = None
        tables_resolved: list[str] = []
        if routine:
            entry = routines_idx.get(routine.upper())
            if entry:
                module = entry["module"]
                routine_type = entry["type"]
                tables_resolved = list(entry["tables_primary"]) + list(
                    entry.get("tables_secondary", [])
                )

        op_code: int | None = None
        for arg in reversed(parts[1:]):
            mn = _NUMERIC_ARG_RE.match(arg)
            if mn:
                op_code = int(mn.group(1))
                break
        op_label = _OP_LABELS.get(op_code) if op_code is not None else None

        linha = _line_at(content, m.start())
        snippet = _snippet_at(content, m.start())

        calls.append(
            {
                "linha": linha,
                "routine": routine,
                "module": module,
                "routine_type": routine_type,
                "op_code": op_code,
                "op_label": op_label,
                "tables_resolved": tables_resolved,
                "dynamic_call": dynamic,
                "arg_count": arg_count,
                "snippet": snippet,
            }
        )

    return calls


def serialize_tables(tables: list[str]) -> str:
    """JSON-serializa list[str] pra coluna `tables_resolved_json`."""
    return json.dumps(tables, ensure_ascii=False)


def parse_tables(value: str | None) -> list[str]:
    """Inverso de :func:`serialize_tables`."""
    if not value:
        return []
    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        return []
    return list(result) if isinstance(result, list) else []
