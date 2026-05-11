"""Testes do mini-tokenizer (strip_advpl).

Princípio: substituir comentários (//, /* */, * line-start, && line-start) e
strings (",') por espaços, preservando newlines e contagem de linhas/offsets.
"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from plugadvpl.parsing.stripper import strip_advpl


def _same_length(original: str, stripped: str) -> bool:
    return len(original) == len(stripped)


def _same_lines(original: str, stripped: str) -> bool:
    return original.count("\n") == stripped.count("\n")


class TestLineComment:
    def test_strips_line_comment(self) -> None:
        src = 'cFoo := "hello"   // comment\nReturn .T.'
        out = strip_advpl(src)
        assert _same_length(src, out)
        assert _same_lines(src, out)
        # comentário e string viram espaços
        assert "comment" not in out
        assert "hello" not in out
        # código preservado
        assert "cFoo" in out
        assert "Return" in out


class TestBlockComment:
    def test_strips_multiline_block_comment(self) -> None:
        src = "Function Foo()\n/* multi\nline comment */\nReturn .T."
        out = strip_advpl(src)
        assert _same_length(src, out)
        assert _same_lines(src, out)
        assert "multi" not in out
        assert "comment" not in out
        assert "Function" in out
        assert "Return" in out


class TestStrings:
    def test_strips_double_quoted(self) -> None:
        src = 'cMsg := "RecLock(\'SA1\')"'
        out = strip_advpl(src)
        assert "RecLock" not in out  # estava dentro da string
        assert "cMsg" in out

    def test_strips_single_quoted(self) -> None:
        src = "DbSelectArea('SA1')"
        out = strip_advpl(src)
        assert "SA1" not in out  # estava dentro de string single-quoted
        assert "DbSelectArea" in out


class TestNoFalsePositives:
    def test_reclock_in_comment_disappears(self) -> None:
        src = 'Function Grava()\n  // TODO: RecLock("SA1")\nReturn .T.'
        out = strip_advpl(src)
        assert "RecLock" not in out
        assert "Function" in out
        assert "Grava" in out


class TestPreserveOffsets:
    def test_offsets_preserved_exact(self) -> None:
        src = 'a := "hello world" + b'
        out = strip_advpl(src)
        assert len(src) == len(out)
        # 'b' deve estar na mesma posição
        assert out.rstrip()[-1] == "b"
        assert out.index("b") == src.index("b")


class TestStarLineComment:
    def test_star_at_start_of_line(self) -> None:
        src = "*-----------------\n* User Function Fake()\nU_REAL()"
        out = strip_advpl(src)
        assert _same_length(src, out)
        assert _same_lines(src, out)
        assert "U_REAL" in out  # code preserved
        assert "Fake" not in out  # comment stripped
        assert "----" not in out

    def test_star_only_at_start_of_line(self) -> None:
        """`*` mid-expression (e.g., multiplication) must NOT be stripped."""
        src = "nTotal := 2 * 3"
        out = strip_advpl(src)
        assert "2 * 3" in out  # * is operator here, must survive

    def test_star_with_leading_whitespace(self) -> None:
        src = "  * comment after indent\nReturn"
        out = strip_advpl(src)
        assert "comment" not in out
        assert "Return" in out


class TestAmpersandLineComment:
    def test_double_ampersand(self) -> None:
        src = "x := 1\n&& U_OLD_FUNC()\ny := 2"
        out = strip_advpl(src)
        assert "U_OLD_FUNC" not in out
        assert "x := 1" in out
        assert "y := 2" in out

    def test_single_ampersand_not_comment(self) -> None:
        """`&var.` is ADVPL macro substitution, not comment. Don't strip."""
        src = "cVar := &cName"
        out = strip_advpl(src)
        assert "&cName" in out  # single & must survive


class TestStripperProperties:
    @given(st.text())
    def test_length_preserved(self, s: str) -> None:
        assert len(strip_advpl(s)) == len(s)

    @given(st.text())
    def test_newline_count_preserved(self, s: str) -> None:
        assert strip_advpl(s).count("\n") == s.count("\n")

    @given(st.text())
    def test_idempotent(self, s: str) -> None:
        once = strip_advpl(s)
        twice = strip_advpl(once)
        assert once == twice


class TestEdgeCases:
    def test_eof_inside_block_comment(self) -> None:
        src = "code /* never closes"
        out = strip_advpl(src)
        assert len(out) == len(src)
        assert "code" in out
        # Rest after /* should all be spaces (preserves length)

    def test_eof_inside_string(self) -> None:
        src = 'x := "never closes'
        out = strip_advpl(src)
        assert len(out) == len(src)

    def test_crlf_line_endings_preserved(self) -> None:
        src = "x := 1\r\n// comment\r\ny := 2"
        out = strip_advpl(src)
        assert out.count("\n") == src.count("\n")
        assert "comment" not in out
        assert "x := 1" in out
        assert "y := 2" in out
