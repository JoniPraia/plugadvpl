"""extract_lookups — parses advpl-specialist markdown sources into 6 JSON catalogs.

Reads ``D:/IA/Projetos/advpl-specialist-main/skills/`` and writes:

* ``funcoes_nativas.json``        (~100+ TOTVS native functions)
* ``funcoes_restritas.json``      (~195 restricted functions)
* ``lint_rules.json``             (~23 lint rules)
* ``sql_macros.json``             (5 SQL macros + 6 restrictions)
* ``modulos_erp.json``            (8 ERP modules — hand-crafted seed)
* ``pontos_entrada_padrao.json``  (~25 standard entry points)

Output dir: ``cli/plugadvpl/lookups/``.

The script is meant to be run once during development; the resulting JSONs are
committed to the repo and shipped inside the wheel.

The data is sourced from `advpl-specialist <https://github.com/thalysjuvenal/advpl-specialist>`_
(MIT) and credited in ``NOTICE``.

Usage::

    python scripts/extract_lookups.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = Path("D:/IA/Projetos/advpl-specialist-main/skills")
OUTPUT_DIR = REPO_ROOT / "cli" / "plugadvpl" / "lookups"


# ---------------------------------------------------------------------------
# Categoria mapping for native functions (H2 section -> short categoria slug)
# ---------------------------------------------------------------------------

NATIVE_CATEGORIA_MAP: dict[str, str] = {
    "String Functions": "string",
    "Date/Time Functions": "datetime",
    "Numeric Functions": "numeric",
    "Array Functions": "array",
    "Database Functions": "database",
    "Interface/UI Functions": "ui",
    "File I/O Functions": "file",
    "System Functions": "system",
    "Company/Branch Management Functions (FW*)": "company",
    "Transaction Functions": "transaction",
    "Execution Functions": "execution",
    "Network/REST Functions": "network",
    "Conversion Functions": "conversion",
    "Additional Commonly Used Functions": "misc",
    "TReport Classes": "treport",
    "FWFormBrowse / FWMBrowse Classes": "fwformbrowse",
    "Jobs / Multi-Threading Functions": "jobs",
    "Email Classes": "email",
    "JsonObject Class Methods": "json",
    "TWsdlManager Class Methods": "wsdl",
    "FwBrowse Class": "browse",
    "FWMarkBrowse Class": "browse",
    "FWBrwColumn Class": "browse",
    "FWBrwRelation Class": "browse",
    "FWLegend Class": "ui",
    "FWGridProcess Class": "grid",
    "tNewProcess Class": "process",
    "FWCalendar Class": "ui",
    "FWSimpEdit Class": "ui",
    "Utility Functions": "utility",
    "Security and Authentication Classes": "security",
    "Company/Branch and Scheduling Functions": "company",
    "Chart and Tree Classes": "ui",
    "Wizard Classes": "ui",
    "Printing Classes": "print",
    "Bulk Insert and Query Cache Classes": "database",
    "Dictionary Utility Classes": "dictionary",
    "UI and Integration Classes": "ui",
    "Miscellaneous Functions": "misc",
    "Legacy / Compatibility Functions": "legacy",
}


# ---------------------------------------------------------------------------
# Functions that should set requer_unlock / requer_close_area / deprecated
# (heuristic-based — these flags are best-effort; lint rules use lookups
#  + AST for final decision)
# ---------------------------------------------------------------------------

NATIVE_REQUER_UNLOCK = {"RecLock", "MsRLock"}
NATIVE_REQUER_CLOSE_AREA = {"DbUseArea", "OpenSXs", "CriaTrab"}
NATIVE_DEPRECATED: dict[str, str] = {
    # name -> alternativa
    # (empty for now — pull TDN data in v0.2)
}


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_native_functions(src: Path) -> list[dict]:
    """Parse native-functions.md — every H3 under an H2 is one function.

    Captures:

    - ``nome``: from H3.
    - ``categoria``: derived from current H2 via ``NATIVE_CATEGORIA_MAP``.
    - ``assinatura``: first ``**Syntax:**`` line (cleaned).
    - ``descricao``: first paragraph after H3 (1 line).
    - ``params_count``: count of rows in the Param table.
    - flags: heuristics on a small known set.
    """
    text = src.read_text(encoding="utf-8")
    items: list[dict] = []

    current_h2 = ""
    # Split keeping headings as separators
    blocks = re.split(r"(?m)^(##\s+.*|###\s+.*)$", text)

    # blocks alternates: [pre, heading, body, heading, body, ...]
    pending_heading: str | None = None
    for chunk in blocks:
        if chunk is None:
            continue
        if chunk.startswith("## ") and not chunk.startswith("### "):
            current_h2 = chunk[3:].strip()
            pending_heading = None
            continue
        if chunk.startswith("### "):
            pending_heading = chunk[4:].strip()
            continue
        if pending_heading is None:
            continue

        # chunk is body for the pending H3
        nome = pending_heading
        pending_heading = None
        # Skip if H3 is a sub-heading like "How PARAMIXB Works"
        if " " in nome and not nome[0].isalpha():
            continue

        descricao_match = re.search(r"\n([^\n#|*][^\n]*)", "\n" + chunk)
        descricao = descricao_match.group(1).strip() if descricao_match else ""

        syntax_match = re.search(r"\*\*Syntax:\*\*\s*`([^`]+)`", chunk)
        assinatura = syntax_match.group(1).strip() if syntax_match else ""

        # Count param table rows: each "| param | type | desc |" after the
        # header "| Param | Type | Description |".
        params_count = 0
        in_table = False
        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("| Param") or stripped.startswith("|Param"):
                in_table = True
                continue
            if in_table:
                if not stripped.startswith("|"):
                    in_table = False
                    continue
                # Skip the separator row "|---|---|---|"
                if re.match(r"^\|[\s\-:|]+\|$", stripped):
                    continue
                params_count += 1

        items.append(
            {
                "nome": nome,
                "categoria": NATIVE_CATEGORIA_MAP.get(current_h2, "misc"),
                "assinatura": assinatura,
                "params_count": params_count,
                "requer_unlock": 1 if nome in NATIVE_REQUER_UNLOCK else 0,
                "requer_close_area": 1 if nome in NATIVE_REQUER_CLOSE_AREA else 0,
                "deprecated": 1 if nome in NATIVE_DEPRECATED else 0,
                "alternativa": NATIVE_DEPRECATED.get(nome, ""),
                "descricao": descricao,
            }
        )

    # Deduplicate by name (case-insensitive); keep first occurrence
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        key = item["nome"].upper()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def parse_restricted_functions(src: Path) -> list[dict]:
    """Parse restricted-functions.md tables.

    Two tables relevant for funcoes_restritas:

    1. **Compilation BLOCKED** (bloqueada_desde='12.1.33') — has Alternative col.
    2. **Restricted Functions** (the 193-row table) — has Category col.

    Plus the ``Common Alternatives`` table contributes an ``alternativa`` field
    for any restricted name that appears there.
    """
    text = src.read_text(encoding="utf-8")
    items: list[dict] = []

    # ------------------------------------------------------------------
    # Table 1: Compilation BLOCKED
    # ------------------------------------------------------------------
    block = re.search(
        r"## Compilation BLOCKED.*?\n(\|[^\n]+\n)+",
        text,
        re.DOTALL,
    )
    if block:
        for line in block.group(0).splitlines():
            m = re.match(r"^\|\s*\d+\s*\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+)\s*\|", line)
            if m:
                nome = m.group(1).strip().rstrip("()")
                alt = m.group(2).strip()
                items.append(
                    {
                        "nome": nome,
                        "categoria": "blocked",
                        "bloqueada_desde": "12.1.33",
                        "alternativa": alt,
                    }
                )

    # ------------------------------------------------------------------
    # Table 2: Restricted Functions (193 rows)
    # ------------------------------------------------------------------
    block2 = re.search(
        r"## Restricted Functions.*?\| # \| Function/Class \| Category \|.*?\n((?:\|[^\n]+\n)+)",
        text,
        re.DOTALL,
    )
    if block2:
        for line in block2.group(1).splitlines():
            m = re.match(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
            if m:
                nome = m.group(1).strip().strip("`")
                categoria = m.group(2).strip()
                items.append(
                    {
                        "nome": nome,
                        "categoria": categoria,
                        "bloqueada_desde": "",
                        "alternativa": "",
                    }
                )

    # ------------------------------------------------------------------
    # Table 3: Common Alternatives — fill alternativa onto existing entries.
    # ------------------------------------------------------------------
    block3 = re.search(
        r"## Common Alternatives.*?\| Restricted \| Supported Alternative \|.*?\n((?:\|[^\n]+\n)+)",
        text,
        re.DOTALL,
    )
    alt_map: dict[str, str] = {}
    if block3:
        for line in block3.group(1).splitlines():
            m = re.match(r"^\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|", line)
            if m:
                name = m.group(1).strip().rstrip("()")
                alt = m.group(2).strip()
                alt_map[name.upper()] = alt

    for item in items:
        key = item["nome"].upper().rstrip("()")
        if not item["alternativa"] and key in alt_map:
            item["alternativa"] = alt_map[key]

    # Deduplicate by name (keep first — blocked table comes first)
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        key = item["nome"].upper()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def parse_lint_rules(src_dir: Path) -> list[dict]:
    """Parse 4 rules-*.md files. Extracts ``## [XX-NNN]`` headings + Severity
    + Description + 'What to look for'."""
    items: list[dict] = []

    files: dict[str, str] = {
        "rules-best-practices.md": "best-practice",
        "rules-security.md": "security",
        "rules-performance.md": "performance",
        "rules-modernization.md": "modernization",
    }

    for filename, categoria in files.items():
        path = src_dir / filename
        if not path.exists():
            print(f"WARN: {path} not found, skipping", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        # Split per rule (H2 with [XX-NNN] tag)
        rule_blocks = re.split(r"(?m)^## \[", text)
        for raw in rule_blocks[1:]:
            head_match = re.match(r"([A-Z]+-\d+[a-z]?)\]\s*(.+)", raw)
            if not head_match:
                continue
            regra_id = head_match.group(1).strip()
            titulo = head_match.group(2).strip()

            sev_match = re.search(r"\*\*Severity:\*\*\s*([A-Z]+)", raw)
            severidade = (sev_match.group(1).strip().lower() if sev_match else "warning")
            # Normalize "error" -> "error", "critical"->"critical", "warning"->"warning",
            # "info" -> "info"
            if severidade not in {"critical", "error", "warning", "info"}:
                severidade = "warning"

            desc_match = re.search(r"\*\*Description:\*\*\s*([^\n]+)", raw)
            descricao = desc_match.group(1).strip() if desc_match else ""

            fix_match = re.search(r"\*\*What to look for:\*\*\s*([^\n]+)", raw)
            fix_guidance = fix_match.group(1).strip() if fix_match else ""

            items.append(
                {
                    "regra_id": regra_id,
                    "titulo": titulo,
                    "severidade": severidade,
                    "categoria": categoria,
                    "descricao": descricao,
                    "fix_guidance": fix_guidance,
                    "detection_kind": "regex",
                }
            )

    return items


def build_sql_macros() -> list[dict]:
    """Hand-curated SQL macros from embedded-sql/SKILL.md.

    The 5 BeginSQL macros + a few semantic restrictions documented in the SKILL.
    """
    return [
        {
            "macro": "%table:TABLE%",
            "descricao": "Resolve nome físico da tabela (com prefixo de empresa, ex: SA1010).",
            "exemplo": "FROM %table:SA1% SA1",
            "output_type": "string",
            "safe_for_injection": 1,
        },
        {
            "macro": "%xfilial:TABLE%",
            "descricao": "Valor atual da filial para a tabela (string quoted automaticamente).",
            "exemplo": "AND SA1.A1_FILIAL = %xfilial:SA1%",
            "output_type": "string",
            "safe_for_injection": 1,
        },
        {
            "macro": "%notDel%",
            "descricao": "Filtra registros não-deletados logicamente (D_E_L_E_T_ <> '*').",
            "exemplo": "WHERE SA1.%notDel%",
            "output_type": "boolean",
            "safe_for_injection": 1,
        },
        {
            "macro": "%exp:EXPRESSION%",
            "descricao": "Vincula variável/expressão ADVPL com quoting automático (anti-SQL-injection).",
            "exemplo": "AND SA1.A1_COD = %exp:cCodCli%",
            "output_type": "any",
            "safe_for_injection": 1,
        },
        {
            "macro": "%Order:TABLE%",
            "descricao": "Resolve ordering primário (chave) da tabela.",
            "exemplo": "ORDER BY %Order:SE2%",
            "output_type": "string",
            "safe_for_injection": 1,
        },
        # Restrictions / anti-patterns recorded for lint context
        {
            "macro": "concat_string",
            "descricao": "RESTRIÇÃO: concatenar variáveis em SQL via '+' sem %exp: é SQL-injection risk (regra SEC-001).",
            "exemplo": "BAD: cSql += \"AND A1_COD = '\" + cCod + \"'\"",
            "output_type": "string",
            "safe_for_injection": 0,
        },
    ]


def build_modulos_erp() -> list[dict]:
    """Hand-crafted seed of 8 Protheus ERP modules.

    TODO: improve extraction from modulo-*.md (prose-heavy, many tables of
    sub-fields). For MVP, capture (codigo, nome, prefixos_tabelas,
    prefixos_funcoes, rotinas_principais). Sources are credited in NOTICE.
    """
    return [
        {
            "codigo": "COM",
            "nome": "Compras (SIGACOM)",
            "prefixos_tabelas": ["SC1", "SC2", "SC3", "SC7", "SC8", "SCK", "SCR", "SDC"],
            "prefixos_funcoes": ["MATA1", "MATA12", "MATA14", "A097", "A120", "A130"],
            "rotinas_principais": [
                "MATA110", "MATA120", "MATA121", "MATA130", "MATA131",
                "MATA140", "MATA097",
            ],
        },
        {
            "codigo": "EST",
            "nome": "Estoque (SIGAEST)",
            "prefixos_tabelas": ["SB1", "SB2", "SB6", "SB7", "SB8", "SB9", "SBE", "SBF", "SBZ", "SD1", "SD2", "SD3"],
            "prefixos_funcoes": ["MATA0", "MATA2", "MATA3", "MATA4"],
            "rotinas_principais": [
                "MATA010", "MATA020", "MATA030", "MATA240", "MATA241", "MATA250", "MATA261", "MATA262",
            ],
        },
        {
            "codigo": "FAT",
            "nome": "Faturamento (SIGAFAT)",
            "prefixos_tabelas": ["SC5", "SC6", "SC9", "SD2", "SF2", "SE4", "SA1"],
            "prefixos_funcoes": ["MATA4", "MATA46", "MATA41", "MA410", "MA440", "MATA460"],
            "rotinas_principais": [
                "MATA410", "MATA460", "MATA461", "MATA440", "MATA463", "MATA465", "MATA456", "MATA920",
            ],
        },
        {
            "codigo": "FIN",
            "nome": "Financeiro (SIGAFIN)",
            "prefixos_tabelas": ["SE1", "SE2", "SE5", "SEA", "SEB", "SEC", "SED", "SEE", "SEF", "FK1", "FK5", "FK6"],
            "prefixos_funcoes": ["FINA0", "FINA1", "FA050", "FA080", "FINA050", "FINA080"],
            "rotinas_principais": [
                "FINA050", "FINA070", "FINA080", "FINA100", "FINA340", "FINA440", "FINA460",
            ],
        },
        {
            "codigo": "FIS",
            "nome": "Fiscal (SIGAFIS)",
            "prefixos_tabelas": ["SFT", "SF1", "SF2", "SF3", "SF6", "SF7", "SFE", "SFI", "CDA", "CDE"],
            "prefixos_funcoes": ["MATA9", "MATA93", "MATA950", "SPED"],
            "rotinas_principais": [
                "MATA930", "MATA950", "MATA951", "MATA953", "SPEDFISCAL", "SPEDCONTRIB",
            ],
        },
        {
            "codigo": "CTB",
            "nome": "Contabilidade (SIGACTB)",
            "prefixos_tabelas": ["CT1", "CT2", "CT5", "CT7", "CTT", "CTH", "CTD", "CTK"],
            "prefixos_funcoes": ["CTBA0", "CTBA1", "CTBA2"],
            "rotinas_principais": [
                "CTBA020", "CTBA025", "CTBA100", "CTBA102", "CTBA130", "CTBA180", "CTBA240",
            ],
        },
        {
            "codigo": "PCP",
            "nome": "Planejamento e Controle de Produção (SIGAPCP)",
            "prefixos_tabelas": ["SG1", "SG2", "SG5", "SC2", "SD3", "SD4", "SH1", "SH6", "SHA"],
            "prefixos_funcoes": ["MATA6", "MATA65", "MATA68", "MATA37", "MATA38"],
            "rotinas_principais": [
                "MATA370", "MATA380", "MATA650", "MATA651", "MATA680", "MATA681", "MATA700",
            ],
        },
        {
            "codigo": "MNT",
            "nome": "Manutenção de Ativos (SIGAMNT)",
            "prefixos_tabelas": ["ST9", "STJ", "STK", "STL", "STM", "STN", "STO", "STP", "STQ"],
            "prefixos_funcoes": ["MNTA0", "MNTA1", "TMKA"],
            "rotinas_principais": [
                "MNTA010", "MNTA200", "MNTA300", "MNTA310", "MNTA350", "MNTA400",
            ],
        },
    ]


def parse_pontos_entrada(src: Path) -> list[dict]:
    """Parse patterns-pontos-entrada.md.

    Each PE has an H3 ``### NAME - DESCRIPTION``. The module is the H2 that
    precedes it (e.g. ``## 3. Compras Module``).
    """
    text = src.read_text(encoding="utf-8")
    items: list[dict] = []

    # H2 -> module code map
    module_map: dict[str, str] = {
        "Compras Module": "COM",
        "Faturamento Module": "FAT",
        "Financeiro Module": "FIN",
        "Estoque Module": "EST",
        "Fiscal Module": "FIS",
    }

    current_modulo = ""
    pending: tuple[str, str] | None = None  # (nome, descricao)
    body_lines: list[str] = []

    def flush() -> None:
        nonlocal pending, body_lines
        if pending is None:
            return
        nome, descricao = pending
        body = "\n".join(body_lines)
        # Detect PARAMIXB count from any reference like ``PARAMIXB[N]``
        ixb_matches = re.findall(r"PARAMIXB\[(\d+)\]", body)
        paramixb_count = max((int(n) for n in ixb_matches), default=0)
        # Heuristic retorno_tipo: look for ``Return <type>`` or ``Logical``
        retorno_tipo = ""
        ret_m = re.search(r"\*\*Tipo de Retorno:\*\*\s*([A-Z][^\n]*)", body, re.IGNORECASE)
        if ret_m:
            ret_text = ret_m.group(1).strip().lower()
            if "lógic" in ret_text or "logic" in ret_text:
                retorno_tipo = "L"
            elif "caracter" in ret_text or "string" in ret_text:
                retorno_tipo = "C"
            elif "numeric" in ret_text or "numér" in ret_text:
                retorno_tipo = "N"
            elif "array" in ret_text:
                retorno_tipo = "A"
        if not retorno_tipo:
            # Default for validation PEs (most return Logical)
            retorno_tipo = "L" if "LOK" in nome or "VLD" in nome else ""
        items.append(
            {
                "nome": nome,
                "descricao": descricao,
                "modulo": current_modulo,
                "paramixb_count": paramixb_count,
                "retorno_tipo": retorno_tipo,
                "link_tdn": "",
            }
        )
        pending = None
        body_lines = []

    for line in text.splitlines():
        h2 = re.match(r"^##\s+(?:\d+\.\s+)?(.+?)\s*$", line)
        if h2:
            flush()
            section = h2.group(1).strip()
            current_modulo = module_map.get(section, "")
            continue
        h3 = re.match(r"^###\s+([A-Z][A-Z0-9_]+)\s*-\s*(.+?)\s*$", line)
        if h3:
            flush()
            pending = (h3.group(1).strip(), h3.group(2).strip())
            body_lines = []
            continue
        if pending is not None:
            body_lines.append(line)

    flush()
    return items


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary: dict[str, int] = {}

    # 1. funcoes_nativas
    native = parse_native_functions(SOURCE_ROOT / "protheus-reference" / "native-functions.md")
    (OUTPUT_DIR / "funcoes_nativas.json").write_text(
        json.dumps(native, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["funcoes_nativas"] = len(native)

    # 2. funcoes_restritas
    restricted = parse_restricted_functions(SOURCE_ROOT / "protheus-reference" / "restricted-functions.md")
    (OUTPUT_DIR / "funcoes_restritas.json").write_text(
        json.dumps(restricted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["funcoes_restritas"] = len(restricted)

    # 3. lint_rules
    rules = parse_lint_rules(SOURCE_ROOT / "advpl-code-review")
    (OUTPUT_DIR / "lint_rules.json").write_text(
        json.dumps(rules, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["lint_rules"] = len(rules)

    # 4. sql_macros (hand-crafted)
    macros = build_sql_macros()
    (OUTPUT_DIR / "sql_macros.json").write_text(
        json.dumps(macros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["sql_macros"] = len(macros)

    # 5. modulos_erp (hand-crafted)
    # TODO: improve extraction from modulo-*.md (prose-heavy, 8 files).
    modulos = build_modulos_erp()
    (OUTPUT_DIR / "modulos_erp.json").write_text(
        json.dumps(modulos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["modulos_erp"] = len(modulos)

    # 6. pontos_entrada_padrao
    pes = parse_pontos_entrada(SOURCE_ROOT / "advpl-code-generation" / "patterns-pontos-entrada.md")
    (OUTPUT_DIR / "pontos_entrada_padrao.json").write_text(
        json.dumps(pes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["pontos_entrada_padrao"] = len(pes)

    # Print summary
    print("Lookup extraction complete:")
    for table, count in summary.items():
        print(f"  {table}: {count} items")
    print(f"Output dir: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
