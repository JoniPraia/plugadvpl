"""Mini-tokenizer: substitui comentários e strings por espaços, preservando offsets.

Roda antes das regex de extração para evitar falso-positivos em código comentado
ou dentro de strings literais. Padrão da indústria (ProLeap COBOL faz idem).
"""
from __future__ import annotations


def strip_advpl(  # noqa: PLR0912, PLR0915
    content: str, *, strip_strings: bool = True
) -> str:
    """Retorna content com comentários e, opcionalmente, strings substituídos por espaços.

    Comentários reconhecidos:
    - `//` (linha) — em qualquer posição
    - `/* ... */` (bloco) — em qualquer posição
    - `*` no início de linha lógica (banner Clipper, ex.: `*-----*`, `* User Function Foo`)
    - `&&` no início de linha lógica (Harbour/xBase legacy)

    "Início de linha lógica" = após `\\n` (ou BOF) e zero-ou-mais whitespace [ \\t].

    Preserva:
    - Tamanho total (len(out) == len(content))
    - Newlines e contagem de linhas
    - Offsets de tokens não-comentário (regex pode usar match.start() na saída e
      mapear de volta para a posição original sem ajuste)

    Args:
        content: source ADVPL/TLPP
        strip_strings: se True (default), substitui conteúdo de strings literais por espaços
            também. Se False, mantém strings intactas — necessário para extratores que
            precisam ler argumentos literais (DbSelectArea("SA1"), RecLock("SA1"), etc.).

    Limitações:
    - Macros `&var.` (substituição runtime) não são resolvidas — impossível estaticamente
    - `&` único permanece intacto (necessário para `&cVar`, expansão de macro)
    - Não detecta strings raw/multilinha (ADVPL não tem)
    """
    out: list[str] = []
    i, n = 0, len(content)
    state = "code"
    # at_start_of_line: True na BOF; depois de cada \n; permanece True enquanto só whitespace.
    # Apenas line-start markers (* e &&) usam essa flag.
    at_start_of_line = True
    while i < n:
        c = content[i]
        if state == "code":
            if c == "/" and i + 1 < n and content[i + 1] == "/":
                state = "line_comment"
                out.append("  ")
                i += 2
                at_start_of_line = False
                continue
            if c == "/" and i + 1 < n and content[i + 1] == "*":
                state = "block_comment"
                out.append("  ")
                i += 2
                at_start_of_line = False
                continue
            if at_start_of_line and c == "*":
                # Comentário Clipper de banner: `*-----*` ou `* foo`.
                # Note: `*/` é tratado acima (block_comment fecha), então aqui `*` é puro.
                state = "line_comment"
                out.append(" ")
                i += 1
                at_start_of_line = False
                continue
            if at_start_of_line and c == "&" and i + 1 < n and content[i + 1] == "&":
                # Comentário Harbour/xBase: `&& ...` no início da linha.
                # `&var` único (macro substitution) NÃO casa — exige dois `&` consecutivos.
                state = "line_comment"
                out.append("  ")
                i += 2
                at_start_of_line = False
                continue
            if c == '"':
                if strip_strings:
                    state = "str_dq"
                    out.append(" ")
                else:
                    state = "str_dq_keep"
                    out.append(c)
                i += 1
                at_start_of_line = False
                continue
            if c == "'":
                if strip_strings:
                    state = "str_sq"
                    out.append(" ")
                else:
                    state = "str_sq_keep"
                    out.append(c)
                i += 1
                at_start_of_line = False
                continue
            out.append(c)
            if c == "\n":
                at_start_of_line = True
            elif c not in (" ", "\t", "\r"):
                at_start_of_line = False
        elif state == "line_comment":
            if c == "\n":
                state = "code"
                out.append("\n")
                at_start_of_line = True
            else:
                out.append(" ")
        elif state == "block_comment":
            if c == "*" and i + 1 < n and content[i + 1] == "/":
                state = "code"
                out.append("  ")
                i += 2
                at_start_of_line = False
                continue
            if c == "\n":
                out.append("\n")
                # Dentro de bloco, newline não conta para start-of-line da próxima linha
                # de código (ainda estamos no comentário).
            else:
                out.append(" ")
        elif state in ("str_dq", "str_sq"):
            quote = '"' if state == "str_dq" else "'"
            if c == "\\" and i + 1 < n:
                out.append("  ")
                i += 2
                continue
            if c == quote:
                state = "code"
                out.append(" ")
            else:
                out.append(" " if c != "\n" else "\n")
        elif state in ("str_dq_keep", "str_sq_keep"):
            quote = '"' if state == "str_dq_keep" else "'"
            if c == "\\" and i + 1 < n:
                # Preserva escape e próximo char (não interpreta)
                out.append(c)
                out.append(content[i + 1])
                i += 2
                continue
            out.append(c)
            if c == quote:
                state = "code"
        i += 1
    return "".join(out)
