"""Performance regression para o pipeline ``ingest-sx`` (synthetic fixtures).

Roda apenas com ``pytest --benchmark-only``. Threshold: <2s para 11 CSVs sintéticos
totalizando ~50 rows.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from plugadvpl.ingest_sx import ingest_sx

if TYPE_CHECKING:
    from collections.abc import Callable

SX_FIXTURES = Path(__file__).parent.parent / "fixtures" / "sx_synthetic"


@pytest.fixture
def cloned_sx_fixtures(tmp_path: Path) -> Path:
    """Copia fixtures SX para tmp_path (sem mistura com outras invocações)."""
    dst = tmp_path / "csv"
    dst.mkdir()
    for src in SX_FIXTURES.glob("*.csv"):
        shutil.copy(src, dst)
    return dst


def test_ingest_sx_synthetic_under_2s(
    benchmark: Callable[..., dict[str, Any]],
    cloned_sx_fixtures: Path,
    tmp_path: Path,
) -> None:
    """11 CSVs sintéticos (~50 rows total) devem ingerir em <2s."""
    db_path = tmp_path / "sx.db"

    def run() -> dict[str, Any]:
        # Cada chamada usa o mesmo db_path; ingest_sx é idempotente (INSERT OR REPLACE).
        return ingest_sx(cloned_sx_fixtures, db_path)

    result = benchmark(run)
    assert result["csvs_ok"] >= 10
    assert result["per_table"]["campos"] == 10
    assert result["duration_ms"] < 2000
