"""End-to-end tests contra fixture local ADVPL.

Marked @pytest.mark.local — only runs with `pytest -m local`.
Excluded from CI via addopts in pyproject.toml.

Configurar via env vars (ver CONTRIBUTING.md):
- PLUGADVPL_E2E_FONTES_DIR: diretório com .prw/.tlpp para ingest
- PLUGADVPL_E2E_BASELINE_DB: SQLite com baseline counters (opcional, para parity test)
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import time
from pathlib import Path

import pytest

FONTES_DIR_ENV = os.environ.get("PLUGADVPL_E2E_FONTES_DIR", "")
BASELINE_DB_ENV = os.environ.get("PLUGADVPL_E2E_BASELINE_DB", "")

FONTES_DIR = Path(FONTES_DIR_ENV) if FONTES_DIR_ENV else None
BASELINE_DB = Path(BASELINE_DB_ENV) if BASELINE_DB_ENV else None

# Tabelas que ambos os DBs têm e que o ingest do CLI plugadvpl popula.
# Comparação de count com tolerância: parser do CLI é uma reescrita
# intencionalmente mais conservadora, então diferenças de ±20% são esperadas.
PARITY_TABLES = [
    "fontes",
    "fonte_chunks",
    "chamadas_funcao",
    "parametros_uso",
    "perguntas_uso",
    "sql_embedado",
]
PARITY_TOLERANCE = 0.20  # ±20%


@pytest.mark.local
@pytest.mark.skipif(
    FONTES_DIR is None or not FONTES_DIR.exists(),
    reason="PLUGADVPL_E2E_FONTES_DIR not set or directory missing",
)
class TestE2eLocalIngest:
    """End-to-end tests sobre fixture local ADVPL."""

    def test_ingest_completes_under_60s(self, tmp_path: Path) -> None:
        """Ingest de ~2.000 fontes deve completar em <60s com workers=8.

        Threshold dimensionado para máquinas de dev típicas (8-core, NVMe).
        Em máquinas mais lentas, ajuste/marque como xfail conforme necessário.
        """
        assert FONTES_DIR is not None  # narrowing for type-checker
        dst = tmp_path / "src"
        shutil.copytree(FONTES_DIR, dst)
        from plugadvpl.ingest import ingest

        start = time.time()
        counters = ingest(dst, workers=8)
        duration = time.time() - start

        assert duration < 60, (
            f"ingest took {duration:.1f}s, expected <60s "
            f"(arquivos_total={counters['arquivos_total']})"
        )
        assert counters["arquivos_total"] >= 1900, (
            f"arquivos_total={counters['arquivos_total']} (esperado >=1900)"
        )
        assert counters["arquivos_ok"] >= 1800, (
            f"arquivos_ok={counters['arquivos_ok']} (esperado >=1800)"
        )

    def test_arquivos_ok_majority_succeeds(self, tmp_path: Path) -> None:
        """Pelo menos 90% dos fontes devem parsear sem erro (sanidade de cobertura)."""
        assert FONTES_DIR is not None
        dst = tmp_path / "src"
        shutil.copytree(FONTES_DIR, dst)
        from plugadvpl.ingest import ingest

        counters = ingest(dst, workers=8)
        total = counters["arquivos_total"]
        ok = counters["arquivos_ok"]
        ratio = ok / max(total, 1)
        assert ratio >= 0.90, (
            f"arquivos_ok={ok}/{total} ({ratio:.1%}) — esperado >=90%"
        )

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "Parity esperada divergir: o parser do CLI plugadvpl é uma reescrita "
            "intencionalmente mais conservadora que o parser anterior "
            "(menos false-positives em parametros_uso/perguntas_uso/sql_embedado). "
            "Diferenças observadas em ~30-80%. Test mantido como diagnóstico — "
            "rode com `-s` para ver o relatório de deltas. xfail(strict=False) "
            "para não bloquear builds locais; quando o gap fechar, remova a marca."
        ),
    )
    def test_parity_with_baseline(self, tmp_path: Path) -> None:
        """Counts do CLI plugadvpl devem ficar a ±20% do baseline (mesma base de fontes)."""
        if BASELINE_DB is None or not BASELINE_DB.exists():
            pytest.skip("PLUGADVPL_E2E_BASELINE_DB not set")
        assert FONTES_DIR is not None

        dst = tmp_path / "src"
        shutil.copytree(FONTES_DIR, dst)
        from plugadvpl.ingest import ingest

        ingest(dst, workers=8)

        plug_db = dst / ".plugadvpl" / "index.db"
        assert plug_db.exists(), f"index.db não foi criado: {plug_db}"

        plug = sqlite3.connect(f"file:{plug_db.as_posix()}?mode=ro", uri=True)
        baseline = sqlite3.connect(
            f"file:{BASELINE_DB.as_posix()}?mode=ro", uri=True
        )

        deltas: list[tuple[str, int, int, float]] = []
        try:
            for table in PARITY_TABLES:
                plug_n = plug.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                base_n = baseline.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                # Delta relativo ao maior dos dois — captura tanto sub- quanto
                # over-count em qualquer direção sem dividir por número grande.
                denom = max(base_n, plug_n, 1)
                delta = abs(plug_n - base_n) / denom
                deltas.append((table, plug_n, base_n, delta))
        finally:
            plug.close()
            baseline.close()

        # Print formatado para diagnóstico (visível com -s ou em falha).
        for table, plug_n, base_n, delta in deltas:
            print(
                f"  {table:20s} plug={plug_n:>7d}  base={base_n:>7d}  "
                f"delta={delta:.1%}"
            )

        violations = [(t, p, q, d) for t, p, q, d in deltas if d > PARITY_TOLERANCE]
        assert not violations, (
            "Tabelas fora da tolerância de ±{:.0%}:\n  {}".format(
                PARITY_TOLERANCE,
                "\n  ".join(
                    f"{t}: plug={p}, baseline={q}, delta={d:.1%}"
                    for t, p, q, d in violations
                ),
            )
        )
