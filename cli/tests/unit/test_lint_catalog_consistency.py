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


def test_catalog_has_expected_total(catalog: dict) -> None:
    """Sanity check: número total de regras catalogadas (24 active + 11 planned = 35)."""
    assert len(catalog) == 35, (
        f"esperava 35 regras catalogadas, encontrou {len(catalog)}. "
        "Se adicionou/removeu regra intencional, atualize este teste."
    )


def test_active_count_matches_impl(catalog: dict, impl: dict) -> None:
    """24 regras active no catálogo devem bater com 24 funções _check_* no impl."""
    n_active = sum(1 for r in catalog.values() if r.get("status") == "active")
    assert n_active == 24, f"esperava 24 active, encontrou {n_active}"
    assert len(impl) == 24, (
        f"esperava 24 funções _check_* em lint.py, encontrou {len(impl)}. "
        "Se adicionou/removeu detector, atualize este teste e o catálogo."
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
