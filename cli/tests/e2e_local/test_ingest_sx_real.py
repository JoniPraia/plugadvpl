"""E2E local tests para ``ingest-sx`` contra CSVs SX reais (não distribuídos).

Mark @pytest.mark.local — só roda com `pytest -m local`.

Configurar via env vars:
- PLUGADVPL_E2E_SX_DIR: pasta com sx1.csv..sxg.csv (default: D:/Clientes/CSV)
"""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

import pytest

SX_DIR_ENV = os.environ.get("PLUGADVPL_E2E_SX_DIR", "D:/Clientes/CSV")
SX_DIR = Path(SX_DIR_ENV) if SX_DIR_ENV else None


@pytest.mark.local
@pytest.mark.skipif(
    SX_DIR is None or not SX_DIR.exists() or not (SX_DIR / "sx2.csv").exists(),
    reason=(
        f"PLUGADVPL_E2E_SX_DIR not set or sx2.csv missing in {SX_DIR}. "
        "Set PLUGADVPL_E2E_SX_DIR to a folder containing sx1.csv..sxg.csv."
    ),
)
class TestIngestSxReal:
    """E2E contra dump SX completo (sx3.csv pode ter 400MB+)."""

    def test_ingest_sx_completes_under_5min(self, tmp_path: Path) -> None:
        """Ingest dos 11 CSVs SX deve completar em <5min (sx3.csv pode ter 400MB)."""
        assert SX_DIR is not None
        from plugadvpl.ingest_sx import ingest_sx

        db_path = tmp_path / "sx.db"
        start = time.time()
        counters = ingest_sx(SX_DIR, db_path)
        duration = time.time() - start

        assert duration < 300, (
            f"ingest-sx took {duration:.1f}s, expected <300s "
            f"(per_table={counters['per_table']})"
        )
        assert counters["csvs_ok"] >= 9, f"esperado >=9 CSVs ok, got {counters}"
        # sx3 sempre deve ter >100k campos para um Protheus standard de tamanho real.
        assert counters["per_table"]["campos"] >= 50000, (
            f"campos={counters['per_table']['campos']} (esperado >=50k)"
        )

    def test_ingest_sx_populates_critical_tables(self, tmp_path: Path) -> None:
        """As tabelas core (campos, gatilhos, parametros) devem ter cardinalidade real."""
        assert SX_DIR is not None
        from plugadvpl.ingest_sx import ingest_sx

        db_path = tmp_path / "sx.db"
        ingest_sx(SX_DIR, db_path)

        conn = sqlite3.connect(str(db_path))
        try:
            n_tab = conn.execute("SELECT COUNT(*) FROM tabelas").fetchone()[0]
            n_cmp = conn.execute("SELECT COUNT(*) FROM campos").fetchone()[0]
            n_gat = conn.execute("SELECT COUNT(*) FROM gatilhos").fetchone()[0]
            n_par = conn.execute("SELECT COUNT(*) FROM parametros").fetchone()[0]
            assert n_tab >= 1000, f"tabelas={n_tab} (esperado >=1000)"
            assert n_cmp >= 50000, f"campos={n_cmp} (esperado >=50000)"
            assert n_gat >= 500, f"gatilhos={n_gat} (esperado >=500)"
            assert n_par >= 1000, f"parametros={n_par} (esperado >=1000)"
        finally:
            conn.close()

    def test_impacto_query_works_on_real_data(self, tmp_path: Path) -> None:
        """``impacto A1_COD`` deve retornar pelo menos algumas referências SX em base real."""
        assert SX_DIR is not None
        from plugadvpl.ingest_sx import ingest_sx
        from plugadvpl.query import impacto_query

        db_path = tmp_path / "sx.db"
        ingest_sx(SX_DIR, db_path)

        conn = sqlite3.connect(str(db_path))
        try:
            rows = impacto_query(conn, "A1_COD", depth=1, max_per_kind=20)
            tipos = {r["tipo"] for r in rows}
            # Em qualquer ERP Protheus, A1_COD tem dúzias de referências SX (gatilhos
            # de SA1, validações de SA2-SE6, etc).
            assert "SX3" in tipos or "SX7" in tipos, (
                f"esperado SX3 ou SX7 em tipos, got {tipos} ({len(rows)} rows)"
            )
        finally:
            conn.close()
