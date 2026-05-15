"""Universo 3 / Feature C — Protheus.doc aggregator.

Extrai blocos ``/*/{Protheus.doc} <id> ... /*/`` de fontes ADVPL/TLPP,
parseia as 16 tags canônicas TOTVS estruturadamente, e resolve a função
associada (próxima declaração após o fechamento).

Spec completo: ``docs/universo3/C-protheus-doc.md``.
Padrão oficial TOTVS: https://github.com/totvs/tds-vscode/blob/master/docs/protheus-doc.md

Exemplo:

.. code-block:: python

    docs = extract_protheus_docs(content)
    # → list[dict] com funcao_id, summary, params, returns, author, ...
"""
from __future__ import annotations

import json
import re
from typing import Any

# --- Regex --------------------------------------------------------------

# Bloco completo: /*/{Protheus.doc} <id> ... /*/
# Non-greedy DOTALL pra capturar até o primeiro `/*/` de fechamento.
# <id> permite letras, números, _ e :: (pra Class::Method).
_PDOC_BLOCK_RE = re.compile(
    r"/\*/\s*\{\s*Protheus\.doc\s*\}"
    r"[ \t]*"  # SEM \s — id, se houver, fica na MESMA linha do opening
    r"(?P<id>[\w:]+)?"
    r"(?P<body>.*?)"
    r"/\*/",
    re.IGNORECASE | re.DOTALL,
)

# Próxima decl de função/método após o fechamento.
_NEXT_DECL_RE = re.compile(
    r"^\s*(?:User\s+|Static\s+|Main\s+)?Function\s+(\w+)\s*\("
    r"|^\s*Method\s+(\w+)\s*\(",
    re.IGNORECASE | re.MULTILINE,
)

# Split de tags por ^\s*@<tag> em start-of-line.
_TAG_SPLIT_RE = re.compile(r"(?m)^[ \t]*@(\w+)\b[ \t]*")

# Param structured: name, type, desc (vírgulas top-level).
_PARAM_OPTIONAL_RE = re.compile(r"^\s*\[\s*(\w+)\s*\]\s*$")
_PARAM_NAME_RE = re.compile(r"^\s*(\w+)\s*$")

# Inferência de módulo via path: SIGAFAT/SIGAFIN/etc.
_MODULE_PATH_RE = re.compile(r"\b(SIGA\w{3,4})\b", re.IGNORECASE)

# Tags single-value (1 por bloco).
_SINGLE_VALUE_TAGS = {
    "type", "author", "since", "version", "description",
    "language", "country", "database", "build", "source",
    "systemoper", "accesslevel",
}
# Tags com multiplicidade (lista).
_MULTI_VALUE_TAGS = {
    "param", "return", "example", "sample", "history", "see",
    "table", "todo", "obs", "link",
}
# Tags flag (sem valor → bool).
_FLAG_TAGS = {"private", "protected", "readonly"}

# Tags simples (string única, sem parsing estruturado).
_SIMPLE_LIST_TAGS = {"example", "sample", "see", "table", "todo", "obs", "link"}


# --- Catalogo execauto pra inferência de módulo ---------------------------


def _execauto_routines() -> dict[str, dict[str, Any]]:
    """Reaproveita catálogo da Feature B pra mapear prefixo de função → módulo."""
    from plugadvpl.parsing.execauto import _routines_index
    return _routines_index()


def infer_module(arquivo: str, funcao: str | None) -> str | None:
    """Infere módulo TOTVS a partir do path ou prefixo da função.

    Algoritmo:
      1. Path-based: ``SIGA\\w{3,4}`` no path → match
      2. Routine-prefix: prefixo da função bate com rotina do catálogo execauto
      3. Fallback: ``None``
    """
    m = _MODULE_PATH_RE.search(arquivo or "")
    if m:
        return m.group(1).upper()
    if funcao:
        idx = _execauto_routines()
        funcao_upper = funcao.upper()
        # 1. Exact match (rotina exata no catálogo).
        if funcao_upper in idx:
            return idx[funcao_upper]["module"]
        # 2. Prefix match (4 primeiros chars). Determinístico: ordena por
        # nome de rotina e pega o primeiro alfabético entre os matches.
        prefix4 = funcao_upper[:4]
        matches = sorted(
            (e for k, e in idx.items() if k.startswith(prefix4)),
            key=lambda e: e["routine"],
        )
        if matches:
            return matches[0]["module"]
    return None


# --- Parser de tags estruturadas ----------------------------------------


def _split_top_level_commas(s: str, max_parts: int = -1) -> list[str]:
    """Split por vírgulas top-level (ignora dentro de aspas e parens)."""
    parts: list[str] = []
    depth_paren = depth_brace = depth_bracket = 0
    in_str: str | None = None
    last = 0
    count = 0
    for i, c in enumerate(s):
        if in_str:
            if c == in_str:
                in_str = None
            continue
        if c in ("'", '"'):
            in_str = c
        elif c == "(":
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
            count += 1
            if max_parts > 0 and count >= max_parts - 1:
                break
    parts.append(s[last:])
    return parts


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _parse_param(value: str) -> dict[str, Any]:
    """`<name>, <type>, <desc>` → dict. Suporta `[name]` opcional."""
    parts = _split_top_level_commas(value, max_parts=3)
    name_raw = parts[0].strip() if parts else ""
    optional = False
    name: str | None = None
    m_opt = _PARAM_OPTIONAL_RE.match(name_raw)
    if m_opt:
        optional = True
        name = m_opt.group(1)
    else:
        m_name = _PARAM_NAME_RE.match(name_raw)
        name = m_name.group(1) if m_name else (name_raw or None)
    type_str = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
    desc = _strip_quotes(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else None
    return {"name": name, "type": type_str, "desc": desc, "optional": optional}


def _parse_return(value: str) -> dict[str, Any]:
    """`<type>, <desc>` → dict."""
    parts = _split_top_level_commas(value, max_parts=2)
    type_str = parts[0].strip() if parts and parts[0].strip() else None
    desc = _strip_quotes(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
    return {"type": type_str, "desc": desc}


def _parse_history(value: str) -> dict[str, Any]:
    """`<date>, <user>, <desc>` → dict."""
    parts = _split_top_level_commas(value, max_parts=3)
    date = parts[0].strip() if parts else ""
    user = parts[1].strip() if len(parts) > 1 else ""
    desc = _strip_quotes(parts[2].strip()) if len(parts) > 2 else ""
    return {"date": date, "user": user, "desc": desc}


# --- Block extraction ----------------------------------------------------


def _line_at(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _resolve_next_decl(
    content: str, after_offset: int
) -> tuple[str | None, int | None]:
    """Acha próxima decl de função/método após offset. Retorna (nome, linha_1based)."""
    m = _NEXT_DECL_RE.search(content, after_offset)
    if not m:
        return None, None
    name = m.group(1) or m.group(2)
    return name, _line_at(content, m.start())


def _parse_body(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Separa body em (summary, [(tag, content), ...])."""
    first_tag_match = _TAG_SPLIT_RE.search(body)
    if not first_tag_match:
        return body.strip(), []
    summary = body[: first_tag_match.start()].strip()
    tags_section = body[first_tag_match.start() :]
    parts = _TAG_SPLIT_RE.split(tags_section)
    # parts[0] é vazio/pre; depois alterna tag, content.
    # Preserva o case original do tag (raw_tags usa case do header).
    pairs: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        tag = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        pairs.append((tag, content.rstrip()))
    return summary, pairs


def _empty_doc() -> dict[str, Any]:
    return {
        "funcao_id": None,
        "funcao": None,
        "tipo": None,
        "module_inferido": None,
        "linha_bloco_inicio": 0,
        "linha_bloco_fim": 0,
        "linha_funcao": None,
        "summary": None,
        "description": None,
        "author": None,
        "since": None,
        "version": None,
        "deprecated": False,
        "deprecated_reason": None,
        "language": None,
        "params": [],
        "returns": [],
        "examples": [],
        "history": [],
        "see": [],
        "tables": [],
        "todos": [],
        "obs": [],
        "links": [],
        "raw_tags": {},
    }


def extract_protheus_docs(
    content: str, *, arquivo: str | None = None
) -> list[dict[str, Any]]:
    """Extrai blocos Protheus.doc estruturados.

    Args:
        content: source ADVPL/TLPP cru.
        arquivo: path do arquivo (usado pra inferência de módulo via path).

    Returns:
        Lista de dicts. Cada dict tem campos:

        - ``funcao_id`` (str | None): <id> declarado no header
        - ``funcao`` (str | None): nome resolvido pela próxima decl
        - ``tipo`` (str | None): @type normalizado (lowercase)
        - ``module_inferido`` (str | None): SIGAFAT/SIGAFIN/...
        - ``linha_bloco_inicio`` / ``linha_bloco_fim`` (int)
        - ``linha_funcao`` (int | None): linha da próxima decl
        - ``summary`` (str): texto antes da primeira @tag
        - ``description``/``author``/``since``/``version``/``language``: single
        - ``deprecated`` (bool) + ``deprecated_reason`` (str | None)
        - ``params`` (list[{name,type,desc,optional}])
        - ``returns`` (list[{type,desc}])
        - ``examples``, ``see``, ``tables``, ``todos``, ``obs``, ``links`` (list[str])
        - ``history`` (list[{date,user,desc}])
        - ``raw_tags`` (dict[str, str]): catch-all pra tags fora do whitelist
    """
    docs: list[dict[str, Any]] = []
    for m in _PDOC_BLOCK_RE.finditer(content):
        funcao_id = m.group("id") or None
        body = m.group("body") or ""
        summary, tag_pairs = _parse_body(body)

        d = _empty_doc()
        d["funcao_id"] = funcao_id
        d["summary"] = summary or None
        d["linha_bloco_inicio"] = _line_at(content, m.start())
        d["linha_bloco_fim"] = _line_at(content, m.end() - 1)

        for tag_raw, value in tag_pairs:
            value_stripped = value.strip()
            tag = tag_raw.lower()
            if tag == "type":
                d["tipo"] = value_stripped.lower() or None
            elif tag in ("author", "since", "version", "description", "language"):
                d[tag] = value_stripped or None
            elif tag == "deprecated":
                d["deprecated"] = True
                d["deprecated_reason"] = value_stripped or None
            elif tag == "param":
                d["params"].append(_parse_param(value))
            elif tag == "return":
                d["returns"].append(_parse_return(value))
            elif tag == "history":
                d["history"].append(_parse_history(value))
            elif tag in ("example", "sample"):
                d["examples"].append(value_stripped)
            elif tag == "see":
                d["see"].append(value_stripped)
            elif tag == "table":
                d["tables"].append(value_stripped)
            elif tag == "todo":
                d["todos"].append(value_stripped)
            elif tag == "obs":
                d["obs"].append(value_stripped)
            elif tag == "link":
                d["links"].append(value_stripped)
            else:
                # Catch-all preserva nome original do tag (case-sensitive).
                # Se aparecer 2x, concatena com newline.
                existing = d["raw_tags"].get(tag_raw)
                if existing:
                    d["raw_tags"][tag_raw] = existing + "\n" + value_stripped
                else:
                    d["raw_tags"][tag_raw] = value_stripped

        # Resolve função associada (próxima decl após /*/ fechamento).
        funcao, linha_funcao = _resolve_next_decl(content, m.end())
        d["funcao"] = funcao
        d["linha_funcao"] = linha_funcao

        # Módulo inferido (path + prefix).
        d["module_inferido"] = infer_module(
            arquivo or "", funcao or funcao_id
        )

        docs.append(d)

    return docs


# --- Serialização pra DB --------------------------------------------------


def serialize_json(value: Any) -> str | None:
    """JSON-serializa pra colunas *_json. Retorna None se vazio."""
    if not value:
        return None
    return json.dumps(value, ensure_ascii=False)


def parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        return []
    return list(result) if isinstance(result, list) else []


def parse_json_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return dict(result) if isinstance(result, dict) else {}
