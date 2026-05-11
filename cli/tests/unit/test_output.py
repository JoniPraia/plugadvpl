"""Testes de plugadvpl/output.py — formatters table/json/md."""
from __future__ import annotations

import json
import sys

import pytest

from plugadvpl.output import _md_cell, _table_cell, render


@pytest.fixture
def sample_rows() -> list[dict[str, object]]:
    return [
        {"arquivo": "FATA050.prw", "funcao": "FATA050", "linha": 1},
        {"arquivo": "MATA010.prw", "funcao": "MATA010", "linha": 12},
        {"arquivo": "WSReg.tlpp", "funcao": "WSReg", "linha": 7},
    ]


class TestRenderJSON:
    def test_json_output_to_stdout(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="json", limit=10)
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["total"] == 3
        assert payload["shown"] == 3
        assert payload["truncated"] is False
        assert payload["rows"][0]["arquivo"] == "FATA050.prw"

    def test_json_truncates_with_limit(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="json", limit=2)
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["total"] == 3
        assert payload["shown"] == 2
        assert payload["truncated"] is True

    def test_json_compact_no_indent(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="json", compact=True, limit=10)
        out = capsys.readouterr().out
        # Sem indent ⇒ uma linha só (mais 1 newline final).
        assert "\n" in out
        # Mas sem indent interno ⇒ json.dumps sem espaços extras.
        compact_lines = [ln for ln in out.split("\n") if ln.strip()]
        assert len(compact_lines) == 1


class TestRenderMD:
    def test_md_output_basic(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="md", limit=10)
        out = capsys.readouterr().out
        assert "| arquivo | funcao | linha |" in out
        assert "| FATA050.prw | FATA050 | 1 |" in out
        assert "|---|---|---|" in out

    def test_md_truncated_marker(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="md", limit=1)
        out = capsys.readouterr().out
        assert "... e mais 2 resultados" in out

    def test_md_empty_rows(self, capsys: pytest.CaptureFixture[str]) -> None:
        render([], format="md")
        out = capsys.readouterr().out
        assert "(sem resultados)" in out


class TestRenderTable:
    def test_table_to_stderr(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="table", limit=10, title="Demo")
        cap = capsys.readouterr()
        # Tabela rich vai para stderr; stdout deve estar vazio.
        assert cap.out == ""
        assert "FATA050.prw" in cap.err
        assert "Demo" in cap.err

    def test_table_empty_shows_dim_message(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        render([], format="table")
        cap = capsys.readouterr()
        assert "(sem resultados)" in cap.err

    def test_next_steps_emitted_to_stderr(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(
            sample_rows,
            format="table",
            limit=10,
            next_steps=["plugadvpl arch FATA050.prw", "plugadvpl callers FATA050"],
        )
        cap = capsys.readouterr()
        assert "Próximo passo recomendado" in cap.err
        assert "plugadvpl arch FATA050.prw" in cap.err


class TestOffsetAndLimit:
    def test_offset_skips_rows(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="json", offset=1, limit=10)
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["rows"][0]["arquivo"] == "MATA010.prw"
        assert payload["shown"] == 2

    def test_limit_zero_means_unlimited(
        self,
        capsys: pytest.CaptureFixture[str],
        sample_rows: list[dict[str, object]],
    ) -> None:
        render(sample_rows, format="json", limit=0)
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["truncated"] is False
        assert payload["shown"] == 3


class TestCellHelpers:
    def test_md_cell_escapes_pipe(self) -> None:
        assert _md_cell("a|b") == "a\\|b"
        assert _md_cell("line1\nline2") == "line1 line2"
        assert _md_cell(None) == ""

    def test_table_cell_serializes_complex(self) -> None:
        assert _table_cell([1, 2, 3]) == "[1, 2, 3]"
        assert _table_cell({"x": 1}) == '{"x": 1}'
        assert _table_cell(None) == ""
        assert _table_cell(42) == "42"


def test_stdout_is_flushed(
    capsys: pytest.CaptureFixture[str], sample_rows: list[dict[str, object]]
) -> None:
    """Garantia de flush — pipes esperam JSON completo sem buffering."""
    render(sample_rows, format="json", limit=10)
    sys.stdout.flush()
    out = capsys.readouterr().out
    assert out.endswith("\n")
