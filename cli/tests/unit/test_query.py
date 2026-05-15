"""Testes de plugadvpl/query.py — funções de consulta sobre DB ingerido."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from plugadvpl.ingest import ingest
from plugadvpl.query import (
    arch,
    callees,
    callers,
    doctor_diagnostics,
    find_any,
    find_file,
    find_function,
    grep_fts,
    lint_query,
    param_query,
    stale_files,
    status,
    tables_query,
)


@pytest.fixture
def db_with_three_sources(tmp_path: Path) -> tuple[Path, sqlite3.Connection]:
    """Ingere 3 fontes sintéticos e retorna ``(root, conn)``.

    Fontes:

    - ``FATA050.prw`` — usa RecLock em SC5 (write/reclock).
    - ``MATA010.prw`` — chama FATA050 + SuperGetMV(MV_LOCALIZA).
    - ``WSReg.tlpp`` — WS com HttpPost.
    """
    src = tmp_path / "src"
    src.mkdir()
    (src / "FATA050.prw").write_bytes(
        b"User Function FATA050()\n"
        b'  DbSelectArea("SC5")\n'
        b'  RecLock("SC5", .T.)\n'
        b'  Replace C5_NUM With "001"\n'
        b"  MsUnlock()\n"
        b"Return .T.\n"
    )
    (src / "MATA010.prw").write_bytes(
        b"User Function MATA010()\n"
        b'  Local cMV := SuperGetMV("MV_LOCALIZA", .F., "")\n'
        b"  U_FATA050()\n"
        b"Return\n"
    )
    (src / "WSReg.tlpp").write_bytes(
        b"Namespace api\n"
        b"User Function WSReg()\n"
        b'  HttpPost("http://api.foo/x", oJson)\n'
        b"Return\n"
    )
    ingest(src, workers=0)
    conn = sqlite3.connect(str(src / ".plugadvpl" / "index.db"))
    return src, conn


class TestFindFunction:
    def test_finds_user_function_case_insensitive(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = find_function(conn, "fata050")
        assert len(rows) >= 1
        assert rows[0]["arquivo"] == "FATA050.prw"
        assert rows[0]["funcao"].upper() == "FATA050"

    def test_returns_empty_when_unknown(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        assert find_function(conn, "Inexistente9999") == []


class TestFindFile:
    def test_finds_by_basename_fragment(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = find_file(conn, "WSReg")
        assert any(r["arquivo"] == "WSReg.tlpp" for r in rows)


class TestFindAny:
    def test_composed_strategy_prefers_function(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = find_any(conn, "FATA050")
        # Função tem prioridade — kind=function.
        assert rows
        assert rows[0]["_kind"] == "function"


class TestCallers:
    def test_callers_of_fata050(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = callers(conn, "FATA050")
        assert any(r["arquivo"] == "MATA010.prw" for r in rows)


class TestCallees:
    def test_callees_of_file(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        # `funcao_origem` está vazio no MVP — fallback via basename.
        rows = callees(conn, "MATA010.prw")
        destinos = {r["destino"] for r in rows}
        assert "FATA050" in destinos

    def test_callees_resolves_innermost_chunk_with_nested_methods(
        self, tmp_path: Path
    ) -> None:
        """v0.3.22 — Bug #19 do QA round 2: docstring v0.3.15 fala de
        "chunk MAIS INTERNO em caso de nesting (Class > Method > Static)"
        mas test era happy-path. Aqui forcamos cenario com 2 funcoes
        adjacentes — Method da classe + Static helper — e validamos que
        chamadas em cada uma sao corretamente atribuidas.
        """
        from plugadvpl.db import apply_migrations, init_meta, open_db, seed_lookups
        from plugadvpl.ingest import ingest as do_ingest
        from plugadvpl.query import callees as cq

        src = tmp_path / "MgfA.prw"
        src.write_text(
            'Method M1() Class A\n'                      # 1
            '    Local x := U_ExtA()\n'                  # 2 — chamada DENTRO de M1
            'Return\n'                                    # 3
            '\n'                                          # 4
            'Static Function helper()\n'                  # 5
            '    Local y := U_ExtB()\n'                  # 6 — chamada DENTRO de helper
            'Return\n',                                   # 7
            encoding="cp1252",
        )
        do_ingest(tmp_path, workers=0)

        db = tmp_path / ".plugadvpl" / "index.db"
        conn = sqlite3.connect(str(db))
        try:
            # callees("M1") deve achar U_ExtA (chamada na linha 2 dentro de M1).
            rows_m1 = cq(conn, "M1")
            destinos_m1 = {r["destino"].upper() for r in rows_m1}
            assert "EXTA" in destinos_m1, (
                f"callees('M1') deveria achar U_ExtA. destinos={destinos_m1}"
            )
            # callees("helper") deve achar U_ExtB (chamada na linha 6 dentro de helper).
            rows_h = cq(conn, "helper")
            destinos_h = {r["destino"].upper() for r in rows_h}
            assert "EXTB" in destinos_h, (
                f"callees('helper') deveria achar U_ExtB. destinos={destinos_h}"
            )
            # E validamos isolamento: M1 NAO deve chamar U_ExtB e vice-versa.
            assert "EXTB" not in destinos_m1
            assert "EXTA" not in destinos_h
        finally:
            conn.close()

    def test_callees_by_function_name_works(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        """v0.3.15 — Bug #8 do QA report: ingest deixava funcao_origem='' em
        TODOS os 30k+ registros, então `callees <nome_funcao>` retornava vazio
        sempre. A função-pai deve ser resolvida via lookup em fonte_chunks
        (qual chunk contém linha_origem).

        Fixture: MATA010 contém uma função MATA010 que chama FATA050. Buscar
        callees de MATA010 (por nome de função, NÃO por basename) deve retornar
        FATA050."""
        _, conn = db_with_three_sources
        rows = callees(conn, "MATA010")  # nome da função, sem .prw
        destinos = {r["destino"] for r in rows}
        assert "FATA050" in destinos, (
            f"callees('MATA010') deveria achar FATA050. "
            f"Encontrou: {destinos}. Provavelmente funcao_origem ainda esta vazio."
        )


class TestTablesQuery:
    def test_query_table_sc5_returns_fata050(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = tables_query(conn, "SC5")
        assert any(r["arquivo"] == "FATA050.prw" for r in rows)

    def test_filter_by_mode_write(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = tables_query(conn, "SC5", modo="write")
        # Quem escreve em SC5 ⇒ pelo menos FATA050.
        assert all(r["modo"] == "write" for r in rows)


class TestParamQuery:
    def test_param_mv_localiza(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = param_query(conn, "MV_LOCALIZA")
        assert any(r["arquivo"] == "MATA010.prw" for r in rows)


class TestArch:
    def test_arch_returns_summary_dict(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = arch(conn, "FATA050.prw")
        assert len(rows) == 1
        a = rows[0]
        assert a["arquivo"] == "FATA050.prw"
        # SC5 deve aparecer em alguma lista de tabelas.
        tabs = a["tabelas_read"] + a["tabelas_write"] + a["tabelas_reclock"]
        assert "SC5" in tabs

    def test_arch_missing_file_returns_empty(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        assert arch(conn, "naoexiste.prw") == []


class TestLintQuery:
    def test_lint_all(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = lint_query(conn)
        # Pode estar vazio em fontes simples; só deve retornar list.
        assert isinstance(rows, list)

    def test_lint_filter_by_file(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = lint_query(conn, arquivo="FATA050.prw")
        assert all(r["arquivo"] == "FATA050.prw" for r in rows)


class TestStatus:
    def test_status_has_versions(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        src, conn = db_with_three_sources
        rows = status(conn, str(src))
        assert len(rows) == 1
        s = rows[0]
        assert s["plugadvpl_version"]
        assert s["total_arquivos"] == "3"

    def test_status_runtime_version_field_when_passed(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        """v0.3.12: status expõe runtime_version (binário rodando AGORA) — chave
        sempre presente quando o caller passa, e fica `None` se não passar (back-compat)."""
        src, conn = db_with_three_sources
        rows_with = status(conn, str(src), runtime_version="0.3.12")
        assert rows_with[0]["runtime_version"] == "0.3.12"
        rows_without = status(conn, str(src))
        assert "runtime_version" in rows_without[0]
        assert rows_without[0]["runtime_version"] is None

    def test_status_runtime_version_diverges_from_stored(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        """Caso real do feedback: índice gravado em 0.2.0, binário atual 0.3.11.
        O query devolve os dois lados — o aviso amarelo é responsabilidade da CLI."""
        src, conn = db_with_three_sources
        # db_with_three_sources grava plugadvpl_version via init_meta — vamos forçar
        # algo antigo pra simular upgrade do binário sem reingest.
        from plugadvpl.db import set_meta
        set_meta(conn, "plugadvpl_version", "0.2.0")
        rows = status(conn, str(src), runtime_version="0.3.11")
        s = rows[0]
        assert s["plugadvpl_version"] == "0.2.0"
        assert s["runtime_version"] == "0.3.11"
        # Divergência detectável pelo caller via comparação simples.
        assert s["runtime_version"] != s["plugadvpl_version"]


class TestStaleFiles:
    def test_stale_detection(
        self,
        db_with_three_sources: tuple[Path, sqlite3.Connection],
    ) -> None:
        src, conn = db_with_three_sources
        # Simula mtime maior no filesystem — todos viram stale.
        fs_state = {
            f.name: f.stat().st_mtime_ns + 10_000_000_000
            for f in (src / "FATA050.prw", src / "MATA010.prw", src / "WSReg.tlpp")
        }
        rows = stale_files(conn, fs_state)
        assert all(r["estado"] in {"stale", "new", "deleted"} for r in rows)
        assert any(r["estado"] == "stale" for r in rows)

    def test_stale_detects_new(
        self,
        db_with_three_sources: tuple[Path, sqlite3.Connection],
    ) -> None:
        _, conn = db_with_three_sources
        fs_state = {"NovoArquivo.prw": 99999}
        rows = stale_files(conn, fs_state)
        # Os 3 do DB viram "deleted" + NovoArquivo "new".
        assert any(r["arquivo"] == "NovoArquivo.prw" and r["estado"] == "new" for r in rows)
        assert any(r["estado"] == "deleted" for r in rows)


class TestDoctor:
    def test_doctor_returns_4_checks(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = doctor_diagnostics(conn)
        checks = {r["check"] for r in rows}
        assert {"encoding_missing", "orphan_chunks", "fts_sync", "lookups_loaded"}.issubset(checks)
        # Após ingest limpo, fts_sync deve estar ok.
        fts = next(r for r in rows if r["check"] == "fts_sync")
        assert fts["status"] == "ok"


class TestGrep:
    def test_grep_fts_finds_token(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = grep_fts(conn, "RecLock", mode="fts", limit=20)
        assert any(r["arquivo"] == "FATA050.prw" for r in rows)

    def test_grep_literal_substring(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = grep_fts(conn, "C5_NUM", mode="literal", limit=20)
        assert any(r["arquivo"] == "FATA050.prw" for r in rows)

    def test_grep_identifier_strips_u_prefix(
        self, db_with_three_sources: tuple[Path, sqlite3.Connection]
    ) -> None:
        _, conn = db_with_three_sources
        rows = grep_fts(conn, "U_FATA050", mode="identifier", limit=20)
        # 'FATA050' (sem U_) deve aparecer no conteúdo de MATA010 ou FATA050.
        assert any("FATA050" in (r["snippet"] or "").upper() for r in rows)
