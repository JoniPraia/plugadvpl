"""Performance regression tests para o pipeline de ingest.

Roda apenas com ``pytest --benchmark-only`` (ou ``--benchmark-enable`` em outras
suites). Em CI sem flag, o pytest-benchmark NÃO executa esses testes — eles são
opt-in para evitar inflar o tempo do test runner padrão.

Threshold (5s para 17 fixtures sintéticos, single-thread): folga ampla — em
máquinas de dev o ingest completo gira em <0.5s. O assert apenas pega
regressões grosseiras (e.g., parser O(N²) acidentalmente introduzido).
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from plugadvpl.ingest import ingest

if TYPE_CHECKING:
    from collections.abc import Callable

FIXTURES = Path(__file__).parent.parent / "fixtures" / "synthetic"


@pytest.fixture
def cloned_fixtures(tmp_path: Path) -> Path:
    """Copia as fixtures sintéticas para tmp_path (ingest cria .plugadvpl/ no root)."""
    dst = tmp_path / "src"
    dst.mkdir()
    for src in FIXTURES.glob("*.prw"):
        shutil.copy(src, dst)
    for src in FIXTURES.glob("*.tlpp"):
        shutil.copy(src, dst)
    return dst


def test_ingest_synthetic_fixtures_under_5s(
    benchmark: Callable[..., dict[str, int]],  # pytest-benchmark fixture
    cloned_fixtures: Path,
) -> None:
    """Ingest dos 17 fixtures sintéticos válidos deve rodar em <5s."""
    def run() -> dict[str, int]:
        # workers=0 → single-thread (universo pequeno; ProcessPool overhead não compensa)
        # incremental=False → mede sempre o ingest completo; com incremental=True
        # o pytest-benchmark roda N iterações e a 2ª em diante pula tudo (mtime
        # não muda) zerando arquivos_ok do resultado final.
        return ingest(cloned_fixtures, workers=0, incremental=False)

    result = benchmark(run)
    # 17 arquivos válidos; tolerância: aceita >=15 (filtros de scan podem mudar).
    assert result["arquivos_ok"] >= 15
    # arquivos_total inclui empty.prw/huge.prw/corrupted.bak? Não — scan já filtra.
    # 17 = 20 fixtures - empty - huge - corrupted.bak.
    assert result["arquivos_total"] == 17
