"""Garante que lookups/lint_rules.json e parsing/lint.py não voltem a divergir.

Issue #1 documentou drift histórico (10 severidades + 15 títulos diferentes
entre catálogo e implementação) corrigido em v0.3.4. Este teste é guardião:
qualquer commit futuro que adicione/remova/renomeie uma regra precisa atualizar
ambas as fontes de verdade ou o teste falha.

Estratégia:

1. Lê o catálogo lookups/lint_rules.json (35 regras esperadas, 24 active + 11 planned).
2. Extrai os docstrings das funções _check_* em parsing/lint.py via regex —
   procura o padrão `def _check_<id>_<topico>(...):` seguido de docstring iniciando
   com `<ID>-<n> (<severity>):` (ver constante DEF_RE abaixo).
3. Para cada regra_id que aparece em ambas as fontes:

   - severidade do catálogo deve bater com severidade do docstring impl
   - catálogo deve marcar a regra como status='active'
   - catálogo deve apontar impl_function para o nome real da função

4. Para cada regra status='active' no catálogo, deve existir a _check_* correspondente.
5. Para cada regra status='planned' no catálogo, NÃO deve existir _check_*
   (caso contrário a regra foi implementada e o status precisa ser atualizado).
"""
from __future__ import annotations

import json
import re
from importlib import resources as ir
from pathlib import Path

import pytest

# Mesma regex usada no audit script tmp/audit_lint_drift.py — extrai (fn_name, id, severity, summary).
DEF_RE = re.compile(
    r'^def\s+(_check_[a-z0-9_]+)\s*\([^)]*\)[^:]*:\s*\n\s+"""'
    r'([A-Z]+-[0-9]+[a-z]?)\s+\(([a-z]+)\):\s*([^\n]+)',
    re.MULTILINE,
)


@pytest.fixture(scope="module")
def catalog() -> dict[str, dict]:
    """Carrega lookups/lint_rules.json indexado por regra_id."""
    text = ir.files("plugadvpl").joinpath("lookups/lint_rules.json").read_text(
        encoding="utf-8"
    )
    rules = json.loads(text)
    return {r["regra_id"]: r for r in rules}


@pytest.fixture(scope="module")
def impl() -> dict[str, dict[str, str]]:
    """Extrai dict[regra_id] = {fn, severidade, summary} dos docstrings de lint.py."""
    text = ir.files("plugadvpl").joinpath("parsing/lint.py").read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {}
    for m in DEF_RE.finditer(text):
        fn_name, regra_id, severity, summary = m.groups()
        out[regra_id] = {
            "fn": fn_name,
            "severidade": severity.lower(),
            "summary": summary.strip().rstrip(".").strip(),
        }
    return out


def test_catalog_has_minimum_total(catalog: dict) -> None:
    """Sanity check: catálogo deve ter pelo menos 35 regras (mais é OK, menos não)."""
    assert len(catalog) >= 35, (
        f"catálogo encolheu: encontrou {len(catalog)} regras, mínimo esperado 35. "
        "Não remova regras planned sem ticket de discussão."
    )


def test_active_count_matches_impl(catalog: dict, impl: dict) -> None:
    """Toda regra active no catálogo deve ter `_check_*` correspondente em lint.py.

    Test dinâmico (não hardcoded): quantos active no JSON deve == quantos
    `_check_*` em lint.py. Não precisa atualizar quando promove planned→active.
    """
    n_active = sum(1 for r in catalog.values() if r.get("status") == "active")
    assert n_active == len(impl), (
        f"catalog active={n_active}, impl _check_*={len(impl)} — "
        f"toda regra active precisa ter _check_* correspondente, e vice-versa"
    )
    # Sanity floor: nunca deve cair abaixo do baseline conhecido (v0.3.4 = 24).
    assert len(impl) >= 24, (
        f"esperava pelo menos 24 funções _check_*, encontrou {len(impl)}. "
        "Regrediu? Verifique se algum detector foi removido sem aviso."
    )


def test_active_rules_have_impl_function(catalog: dict, impl: dict) -> None:
    """Toda regra active no catálogo precisa ter `impl_function` apontando pra fn real."""
    for rid, rule in catalog.items():
        if rule.get("status") != "active":
            continue
        assert rule.get("impl_function"), (
            f"regra {rid} marcada como active mas sem impl_function no catálogo"
        )
        assert rid in impl, (
            f"regra {rid} marcada active no catálogo mas não há _check_* "
            f"correspondente em lint.py"
        )
        assert rule["impl_function"] == impl[rid]["fn"], (
            f"regra {rid}: catálogo aponta impl_function='{rule['impl_function']}' "
            f"mas a função real é '{impl[rid]['fn']}'"
        )


def test_severity_matches_between_catalog_and_impl(catalog: dict, impl: dict) -> None:
    """Severidade do catálogo deve bater com severidade declarada no docstring impl."""
    drifts = []
    for rid, impl_data in impl.items():
        if rid not in catalog:
            drifts.append(f"{rid}: existe em lint.py mas NÃO no catálogo")
            continue
        cat_sev = catalog[rid].get("severidade", "?")
        if cat_sev != impl_data["severidade"]:
            drifts.append(
                f"{rid}: catálogo='{cat_sev}' impl='{impl_data['severidade']}'"
            )
    assert not drifts, "Drift de severidade detectado:\n  - " + "\n  - ".join(drifts)


def test_planned_rules_have_no_impl(catalog: dict, impl: dict) -> None:
    """Regras planned no catálogo NÃO devem ter _check_* — se tiver, marque como active."""
    leaks = []
    for rid, rule in catalog.items():
        if rule.get("status") == "planned" and rid in impl:
            leaks.append(
                f"{rid}: marcada planned mas existe {impl[rid]['fn']} em lint.py — "
                "mude status para 'active' e adicione impl_function"
            )
    assert not leaks, "Regras planned com impl real:\n  - " + "\n  - ".join(leaks)


def test_planned_rules_have_no_impl_function(catalog: dict) -> None:
    """Regras planned não devem ter `impl_function` setado (deve ser '' ou ausente)."""
    for rid, rule in catalog.items():
        if rule.get("status") == "planned":
            assert not rule.get("impl_function"), (
                f"regra {rid} marcada planned mas tem impl_function='{rule['impl_function']}' "
                "— remova o campo ou marque como active"
            )


def test_all_rules_have_required_fields(catalog: dict) -> None:
    """Schema mínimo: toda regra precisa de regra_id/titulo/severidade/categoria/descricao/status."""
    required = ["regra_id", "titulo", "severidade", "categoria", "descricao", "status"]
    for rid, rule in catalog.items():
        for field in required:
            assert field in rule, f"regra {rid} sem campo obrigatório '{field}'"
        assert rule["status"] in ("active", "planned"), (
            f"regra {rid}: status='{rule['status']}' inválido (use 'active' ou 'planned')"
        )
        assert rule["severidade"] in ("critical", "error", "warning", "info"), (
            f"regra {rid}: severidade='{rule['severidade']}' inválida"
        )


def test_all_check_functions_registered_in_orchestrator(impl: dict) -> None:
    """F6 (audit v0.3.10): toda `_check_*` função deve aparecer em `lint_source()`.

    Evita o gap onde se cria um detector mas esquece de registrar no orchestrator —
    catalog diz 'active', função existe, mas nunca dispara em runtime.

    Verifica que para cada `_check_xxx` extraída de docstrings (impl dict), existe
    uma chamada `findings.extend(_check_xxx(arquivo, parsed, content))` ou similar
    no source de `parsing/lint.py`. Para cross-file SX-* a chamada está no loop
    `_CROSS_FILE_RULES` em `lint_cross_file()`.
    """
    text = ir.files("plugadvpl").joinpath("parsing/lint.py").read_text(encoding="utf-8")
    not_registered = []
    for rid, data in impl.items():
        fn = data["fn"]
        # Single-file: aparece em lint_source() como `findings.extend(_check_xxx(...))`
        # Cross-file: aparece em _CROSS_FILE_RULES tuple list. Suporta tanto o
        # formato antigo `(id, fn),` quanto o novo `(id, fn, requires_sx),` (v0.3.26).
        single_file_pattern = f"findings.extend({fn}("
        cross_file_pattern_old = f"{fn}),"
        cross_file_pattern_new = f"{fn},"
        if (
            single_file_pattern not in text
            and cross_file_pattern_old not in text
            and cross_file_pattern_new not in text
        ):
            not_registered.append(
                f"{rid}: função {fn} existe mas NÃO está registrada em "
                f"lint_source() nem em _CROSS_FILE_RULES — adicione "
                f"`findings.extend({fn}(arquivo, parsed, content))` ou entrada em _CROSS_FILE_RULES"
            )
    assert not not_registered, "Detectores não-registrados:\n  - " + "\n  - ".join(
        not_registered
    )
