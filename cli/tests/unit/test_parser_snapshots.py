"""Snapshot tests para parse_source sobre os fixtures sintéticos.

Cobre os principais cenários (MVC, classic, PE, REST, SOAP, RecLock, ExecAuto,
SQL, namespace, HTTP outbound, hooks, multi-filial). Excluídos: ``empty.prw``,
``huge.prw``, ``corrupted.bak`` (filtrados pelo scan, não passam pelo parser),
e ``encoding_*`` (já cobertos por testes de encoding existentes).

Snapshots vivem em ``__snapshots__/test_parser_snapshots.ambr`` (gerados pelo
syrupy na primeira execução). Atualizar com ``pytest --snapshot-update``.

Campos não-determinísticos (``caminho`` absoluto, dependente da máquina) são
removidos antes da comparação.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from plugadvpl.parsing.parser import parse_source

FIXTURES = Path(__file__).parent.parent / "fixtures" / "synthetic"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "mvc_complete.prw",
        "classic_browse.prw",
        "pe_simple.prw",
        "ws_rest.tlpp",
        "ws_soap.prw",
        "job_rpc.prw",
        "reclock_pattern.prw",
        "reclock_unbalanced.prw",
        "exec_auto.prw",
        "sql_embedded.prw",
        "tlpp_namespace.tlpp",
        "http_outbound.prw",
        "mvc_hooks.prw",
        "multi_filial.prw",
        "pubvars.prw",
    ],
)
def test_parse_source_snapshot(fixture_name: str, snapshot) -> None:  # type: ignore[no-untyped-def]
    """Snapshot do output de parse_source para cada fixture sintético."""
    path = FIXTURES / fixture_name
    if not path.exists():
        pytest.skip(f"fixture missing: {fixture_name}")
    result = parse_source(path)
    # Drop non-deterministic fields (caminho é absoluto = depende da máquina).
    result.pop("caminho", None)
    assert result == snapshot
