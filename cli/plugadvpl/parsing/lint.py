"""Lint findings: detecta anti-padrões single-file (regex) + cross-file (SX, v0.3.0).

Cada regra retorna list[Finding] dict com:
- arquivo: str
- funcao: str (best-effort — pode ser '' se não dentro de função clara)
- linha: int (1-based)
- regra_id: str (e.g., 'BP-001', 'SX-001')
- severidade: str ('critical'|'error'|'warning')
- snippet: str (linha problemática, <=200 chars)
- sugestao_fix: str (texto curto explicando o fix)

Estratégia:
- Single-file: cada regra é função ``_check_<id>(arquivo, parsed, content)``.
  ``lint_source`` aplica todas durante o ingest (passa o resultado para ``lint_findings``).
- Cross-file (v0.3.0): regras SX-*** dependem do dicionário SX já ingerido em DB.
  ``lint_cross_file(conn)`` é orquestrador separado, invocado via ``plugadvpl lint --cross-file``.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from plugadvpl.parsing.stripper import strip_advpl

# --- Pre-compiled module-level regexes ----------------------------------------

# BP-001: RecLock("XXX") sem MsUnlock no mesmo escopo.
_RECLOCK_OPEN_RE = re.compile(r'\bRecLock\s*\(\s*["\'](\w{2,3})["\']', re.IGNORECASE)
_RECLOCK_VIA_ALIAS_RE = re.compile(r"\b(\w{2,3})\s*->\s*\(\s*RecLock\b", re.IGNORECASE)
_MSUNLOCK_RE = re.compile(r"\bMsUnlock\s*\(", re.IGNORECASE)

# BP-002: BEGIN TRANSACTION sem END TRANSACTION.
_BEGIN_TRANS_RE = re.compile(r"\bBEGIN\s+TRANSACTION\b", re.IGNORECASE)
_END_TRANS_RE = re.compile(r"\bEND\s+TRANSACTION\b", re.IGNORECASE)

# BP-003: MsExecAuto sem checar lMsErroAuto nas próximas N linhas.
_MSEXECAUTO_RE = re.compile(r"\bMsExecAuto\s*\(", re.IGNORECASE)
_LMSERROAUTO_RE = re.compile(r"\blMsErroAuto\b", re.IGNORECASE)
_BP003_LOOKAHEAD_LINES = 10

# BP-004: Pergunte(..., .F.) sem uso imediato de MV_PAR* na sequência.
_PERGUNTE_NO_DISPLAY_RE = re.compile(
    r'\bPergunte\s*\(\s*["\']\w+["\']\s*,\s*\.F\.\s*\)', re.IGNORECASE
)
_MV_PAR_RE = re.compile(r"\bMV_PAR\d+\b", re.IGNORECASE)
_BP004_LOOKAHEAD_LINES = 5

# BP-005: função com >6 parâmetros (limite spec).
_BP005_MAX_PARAMS = 6
_FUNCTION_SIGNATURE_RE = re.compile(
    r"^[ \t]*(?:Static|User|Main)?[ \t]*Function[ \t]+(\w+)[ \t]*\(([^)]*)\)",
    re.IGNORECASE | re.MULTILINE,
)

# BP-006: mistura RecLock + DbRLock/dbAppend "raw" no mesmo escopo.
_DBRLOCK_RE = re.compile(r"\bDbRLock\s*\(", re.IGNORECASE)
_DBAPPEND_RAW_RE = re.compile(r"\bdbAppend\s*\(\s*\)", re.IGNORECASE)

# SEC-001: RpcSetEnv dentro de classe WSRESTFUL.
_RPCSETENV_RE = re.compile(r"\bRpcSetEnv\s*\(", re.IGNORECASE)
_WSRESTFUL_CLASS_RE = re.compile(
    r"^[ \t]*CLASS[ \t]+\w+[ \t]+FROM[ \t]+WSRESTFUL\b",
    re.IGNORECASE | re.MULTILINE,
)
_END_CLASS_RE = re.compile(r"^[ \t]*ENDCLASS\b|^[ \t]*END\s+CLASS\b", re.IGNORECASE | re.MULTILINE)

# SEC-002: User Function sem prefixo de cliente/PE pattern.
# Padrão Protheus PE: ^[A-Z]{2,4}\d{2,4}[A-Z_]*$ (com pelo menos 2 letras finais opcionais)
_PE_NAME_RE = re.compile(r"^[A-Z]{2,4}\d{2,4}[A-Z_]*$")
# Prefixos típicos de cliente. Note: matching feito case-insensitive sobre nome.
_CLIENT_PREFIX_RE = re.compile(
    r"^(MGF|MZF|ZZF|U_|ZF|CLI|XX|MT[A-Z]|MA\d|FAT|FIN|COM|EST|CTB|FIS|PCP|MNT)",
    re.IGNORECASE,
)

# PERF-001: SELECT * em SQL embedado.
_SELECT_STAR_RE = re.compile(r"\bSELECT\s+\*", re.IGNORECASE)

# PERF-002: SQL sem %notDel% sobre tabelas Protheus.
_NOTDEL_RE = re.compile(r"%notDel%", re.IGNORECASE)
# PERF-003: SQL sem %xfilial% ou %xfilial:TABELA%.
_XFILIAL_MACRO_RE = re.compile(r"%xfilial(?:[: ]\w*)?%", re.IGNORECASE)

# Critério para considerar uma tabela "Protheus" (3 chars + alfabeto válido).
_TABLE_CODE_LEN = 3

# MOD-001: ConOut em vez de FwLogMsg.
_CONOUT_RE = re.compile(r"\bConOut\s*\(", re.IGNORECASE)

# MOD-002: declaração PUBLIC.
_PUBLIC_DECL_RE = re.compile(r"^[ \t]*PUBLIC[ \t]+\w", re.IGNORECASE | re.MULTILINE)

# Helpers para snippet length.
_SNIPPET_MAX = 200


# --- Helpers ------------------------------------------------------------------


def _line_at(content: str, offset: int) -> int:
    """Retorna a linha 1-based de um offset (mesma fórmula do parser.py)."""
    return content.count("\n", 0, offset) + 1


def _funcao_at_line(funcoes: list[dict[str, Any]], linha: int) -> str:
    """Best-effort: retorna o nome da função cujo range cobre linha (ou '' se nenhuma)."""
    for f in funcoes:
        ini = f.get("linha_inicio", 0)
        fim = f.get("linha_fim", ini)
        if ini <= linha <= fim:
            nome: str = f.get("nome", "") or ""
            return nome
    return ""


def _snippet_at_line(content: str, linha: int) -> str:
    """Extrai snippet da linha 1-based (ou string vazia se fora do range)."""
    lines = content.splitlines()
    if 1 <= linha <= len(lines):
        return lines[linha - 1].strip()[:_SNIPPET_MAX]
    return ""


def _is_valid_protheus_table(name: str) -> bool:
    """Tabela Protheus: ou 3 chars (alias lógico) ou 6+ chars (tabela física com sufixo numérico).

    Exemplos válidos: SA1, ZA1, NDF (alias) e SA1010, ZZ1020 (físico com sufixo numérico).
    No SQL embedado o nome físico é o que aparece; em código ADVPL puro, o alias.
    """
    if len(name) < _TABLE_CODE_LEN:
        return False
    if name[0] not in "SZNQD":
        return False
    if not name[1].isalpha():
        return False
    # 3 chars: aceita qualquer alfanumérico na 3ª posição (e.g., SA1, ZA1, NDF)
    if len(name) == _TABLE_CODE_LEN:
        return name[2].isalnum()
    # 6+ chars: 3 primeiras formam o alias, restante é sufixo numérico (e.g., SA1010, ZA1020)
    return name[2].isalnum() and name[_TABLE_CODE_LEN:].isdigit()


def _funcs_with_offsets(funcoes: list[dict[str, Any]], content: str) -> list[dict[str, Any]]:
    """Anexa offsets de início/fim em chars baseado em linha_inicio/linha_fim.

    Usado para delimitar escopo de função quando precisamos varrer content por
    range. Retorna nova lista com 'char_inicio'/'char_fim' adicionados.
    """
    result: list[dict[str, Any]] = []
    # mapa: linha -> offset do início dessa linha
    line_offsets: list[int] = [0]
    for i, ch in enumerate(content):
        if ch == "\n":
            line_offsets.append(i + 1)
    total = len(content)
    for f in funcoes:
        ini_line = int(f.get("linha_inicio", 1))
        fim_line = int(f.get("linha_fim", ini_line))
        char_inicio = line_offsets[ini_line - 1] if ini_line - 1 < len(line_offsets) else total
        char_fim = (
            line_offsets[fim_line] - 1 if fim_line < len(line_offsets) else total
        )
        new_f = dict(f)
        new_f["char_inicio"] = char_inicio
        new_f["char_fim"] = char_fim
        result.append(new_f)
    return result


def _scope_for_match(
    funcs_with_offsets: list[dict[str, Any]], match_offset: int
) -> tuple[int, int, str]:
    """Retorna (start, end, funcao_nome) do escopo que contém o match.

    Se nenhum, escopo é o arquivo inteiro e funcao_nome = ''.
    """
    for f in funcs_with_offsets:
        if f["char_inicio"] <= match_offset <= f["char_fim"]:
            return f["char_inicio"], f["char_fim"], str(f.get("nome", "") or "")
    return -1, -1, ""


# --- Rule checks --------------------------------------------------------------


def _check_bp001_reclock_unbalanced(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-001 (critical): RecLock sem MsUnlock no mesmo escopo de função.

    Heurística: para cada função, conta opens (RecLock literal ou alias->RecLock)
    vs closes (MsUnlock). Se opens > closes, cada open extra além de closes é
    finding na linha do RecLock correspondente.
    """
    findings: list[dict[str, Any]] = []
    funcoes = parsed.get("funcoes", []) or []
    if not funcoes:
        return findings
    stripped = strip_advpl(content, strip_strings=False)
    funcs_off = _funcs_with_offsets(funcoes, content)

    for f in funcs_off:
        scope = stripped[f["char_inicio"] : f["char_fim"] + 1]
        opens = []
        for m in _RECLOCK_OPEN_RE.finditer(scope):
            opens.append(m.start() + f["char_inicio"])
        for m in _RECLOCK_VIA_ALIAS_RE.finditer(scope):
            opens.append(m.start() + f["char_inicio"])
        closes_count = len(_MSUNLOCK_RE.findall(scope))
        if len(opens) <= closes_count:
            continue
        # Reportar os opens "extras" (os últimos N=opens-closes em ordem).
        unbalanced = sorted(opens)[closes_count:]
        for off in unbalanced:
            linha = _line_at(content, off)
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": f.get("nome", "") or "",
                    "linha": linha,
                    "regra_id": "BP-001",
                    "severidade": "critical",
                    "snippet": _snippet_at_line(content, linha),
                    "sugestao_fix": "Adicione MsUnlock() após manipular o registro lockado.",
                }
            )
    return findings


def _check_bp002_transaction_unbalanced(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-002 (critical): BEGIN TRANSACTION sem END TRANSACTION dentro do mesmo escopo.

    Conta opens vs closes por função; se opens > closes, reporta opens extras.
    Se não há função, opera sobre o arquivo inteiro.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []
    funcs_off = _funcs_with_offsets(funcoes, content) if funcoes else []

    def _check_scope(scope_text: str, scope_offset: int, funcao: str) -> None:
        opens = [m.start() + scope_offset for m in _BEGIN_TRANS_RE.finditer(scope_text)]
        closes_count = len(_END_TRANS_RE.findall(scope_text))
        if len(opens) <= closes_count:
            return
        unbalanced = sorted(opens)[closes_count:]
        for off in unbalanced:
            linha = _line_at(content, off)
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": funcao,
                    "linha": linha,
                    "regra_id": "BP-002",
                    "severidade": "critical",
                    "snippet": _snippet_at_line(content, linha),
                    "sugestao_fix": (
                        "Pareie BEGIN TRANSACTION com END TRANSACTION para evitar "
                        "transação aberta indefinidamente."
                    ),
                }
            )

    if funcs_off:
        for f in funcs_off:
            scope = stripped[f["char_inicio"] : f["char_fim"] + 1]
            _check_scope(scope, f["char_inicio"], f.get("nome", "") or "")
    else:
        _check_scope(stripped, 0, "")
    return findings


def _check_bp003_msexecauto_no_check(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-003 (error): MsExecAuto sem verificar lMsErroAuto nas próximas N linhas."""
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    lines = stripped.splitlines()
    funcoes = parsed.get("funcoes", []) or []

    for m in _MSEXECAUTO_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        # Janela: linhas [linha, linha + N] (1-based)
        end_idx = min(linha + _BP003_LOOKAHEAD_LINES, len(lines))
        window = "\n".join(lines[linha - 1 : end_idx])
        if _LMSERROAUTO_RE.search(window):
            continue
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "BP-003",
                "severidade": "error",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    "Verifique lMsErroAuto após MsExecAuto para tratar erros da rotina automática."
                ),
            }
        )
    return findings


def _check_bp004_pergunte_no_check(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-004 (warning): Pergunte(..., .F.) sem uso de MV_PAR* nas próximas linhas.

    Heurística MVP: se Pergunte é chamado com .F. (não exibe tela) e nas próximas
    N linhas não há referência a MV_PAR*, sinaliza — o resultado da pergunta
    provavelmente está sendo ignorado.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=False)
    lines = stripped.splitlines()
    funcoes = parsed.get("funcoes", []) or []

    for m in _PERGUNTE_NO_DISPLAY_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        end_idx = min(linha + _BP004_LOOKAHEAD_LINES, len(lines))
        window = "\n".join(lines[linha - 1 : end_idx])
        if _MV_PAR_RE.search(window):
            continue
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "BP-004",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    "Após Pergunte(...,.F.), use as variáveis MV_PARxx retornadas; "
                    "caso contrário a chamada é inócua."
                ),
            }
        )
    return findings


def _check_bp005_too_many_params(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-005 (warning): função com mais de 6 parâmetros (limite spec).

    Conta vírgulas top-level na lista entre parens da assinatura. Lista vazia => 0.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []

    for m in _FUNCTION_SIGNATURE_RE.finditer(stripped):
        nome = m.group(1)
        params_text = m.group(2).strip()
        if not params_text:
            continue
        # Split top-level por vírgula (parâmetros ADVPL não têm comas internas).
        n_params = params_text.count(",") + 1
        if n_params <= _BP005_MAX_PARAMS:
            continue
        linha = _line_at(stripped, m.start())
        # Tenta achar funcao_nome via parsed para garantir consistência.
        funcao = nome or _funcao_at_line(funcoes, linha)
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": funcao,
                "linha": linha,
                "regra_id": "BP-005",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    f"Função {nome} tem {n_params} parâmetros; "
                    f"considere agrupar em hash/objeto (limite recomendado: {_BP005_MAX_PARAMS})."
                ),
            }
        )
    return findings


def _check_bp006_mixed_reclock_rawapi(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-006 (error): mistura RecLock e DbRLock/dbAppend() raw na mesma função."""
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=False)
    funcoes = parsed.get("funcoes", []) or []
    if not funcoes:
        return findings
    funcs_off = _funcs_with_offsets(funcoes, content)

    for f in funcs_off:
        scope = stripped[f["char_inicio"] : f["char_fim"] + 1]
        has_reclock = bool(_RECLOCK_OPEN_RE.search(scope)) or bool(
            _RECLOCK_VIA_ALIAS_RE.search(scope)
        )
        has_raw = bool(_DBRLOCK_RE.search(scope)) or bool(_DBAPPEND_RAW_RE.search(scope))
        if not (has_reclock and has_raw):
            continue
        # Reporta na linha do primeiro raw match (mais cirúrgico do que a função inteira).
        raw_m = _DBRLOCK_RE.search(scope) or _DBAPPEND_RAW_RE.search(scope)
        off = (raw_m.start() if raw_m else 0) + f["char_inicio"]
        linha = _line_at(content, off)
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": f.get("nome", "") or "",
                "linha": linha,
                "regra_id": "BP-006",
                "severidade": "error",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    "Não misture RecLock (high-level) com DbRLock/dbAppend() raw na mesma função; "
                    "padronize em RecLock+MsUnlock."
                ),
            }
        )
    return findings


def _check_sec001_rpcsetenv_in_restful(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """SEC-001 (critical): RpcSetEnv dentro de uma classe FROM WSRESTFUL.

    Trocar empresa/filial dentro de WSRESTFUL serializa requisições e quebra
    multitenancy. Detecção: localiza blocos `CLASS X FROM WSRESTFUL ... ENDCLASS`
    e verifica se há RpcSetEnv dentro deles.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=False)

    # Coletar blocos restful: (start, end).
    restful_blocks: list[tuple[int, int]] = []
    for m_open in _WSRESTFUL_CLASS_RE.finditer(stripped):
        # Localiza próximo ENDCLASS após m_open.end()
        m_end = _END_CLASS_RE.search(stripped, m_open.end())
        end_off = m_end.start() if m_end else len(stripped)
        restful_blocks.append((m_open.start(), end_off))

    if not restful_blocks:
        return findings

    for m in _RPCSETENV_RE.finditer(stripped):
        for start, end in restful_blocks:
            if start <= m.start() <= end:
                linha = _line_at(stripped, m.start())
                funcoes = parsed.get("funcoes", []) or []
                findings.append(
                    {
                        "arquivo": arquivo,
                        "funcao": _funcao_at_line(funcoes, linha),
                        "linha": linha,
                        "regra_id": "SEC-001",
                        "severidade": "critical",
                        "snippet": _snippet_at_line(content, linha),
                        "sugestao_fix": (
                            "Não chame RpcSetEnv dentro de WSRESTFUL; isso serializa "
                            "requisições e quebra multitenancy. Use middleware/inicialização global."
                        ),
                    }
                )
                break
    return findings


def _check_sec002_user_function_no_prefix(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """SEC-002 (warning): User Function sem prefixo (PE pattern ou cliente).

    Heurística: User Function cujo nome NÃO casa nem com padrão PE Protheus
    (^[A-Z]{2,4}\\d{2,4}[A-Z_]*$) nem com prefixo de cliente conhecido (MGF, MZF, U_, ZF, ...)
    é sinalizada — risco de colisão com nomes futuros do ERP.
    """
    findings: list[dict[str, Any]] = []
    funcoes = parsed.get("funcoes", []) or []

    for f in funcoes:
        if f.get("kind") != "user_function":
            continue
        nome = (f.get("nome", "") or "").upper()
        if not nome:
            continue
        if _PE_NAME_RE.match(nome):
            continue
        if _CLIENT_PREFIX_RE.match(nome):
            continue
        linha = int(f.get("linha_inicio", 1))
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": nome,
                "linha": linha,
                "regra_id": "SEC-002",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    f"User Function '{nome}' não tem prefixo de cliente nem padrão PE; "
                    "adote convenção (e.g., MGF*, ZF*, U_<cliente>*) para evitar colisão."
                ),
            }
        )
    return findings


def _check_perf001_select_star(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """PERF-001 (warning): SELECT * em SQL embedado."""
    findings: list[dict[str, Any]] = []
    sql_blocks = parsed.get("sql_embedado", []) or []
    funcoes = parsed.get("funcoes", []) or []

    for sql in sql_blocks:
        snippet = sql.get("snippet", "") or ""
        if not _SELECT_STAR_RE.search(snippet):
            continue
        linha = int(sql.get("linha", 1))
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "PERF-001",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha) or snippet[:_SNIPPET_MAX],
                "sugestao_fix": (
                    "Evite SELECT *; liste apenas as colunas usadas para reduzir IO e "
                    "evitar regressões quando o schema mudar."
                ),
            }
        )
    return findings


def _check_perf002_no_notdel(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """PERF-002 (error): SQL contra tabelas Protheus sem %notDel% (não filtra deletados)."""
    findings: list[dict[str, Any]] = []
    sql_blocks = parsed.get("sql_embedado", []) or []
    funcoes = parsed.get("funcoes", []) or []

    for sql in sql_blocks:
        snippet = sql.get("snippet", "") or ""
        operacao = sql.get("operacao", "")
        if operacao not in ("select", "update", "delete"):
            continue
        tabelas = sql.get("tabelas", []) or []
        # Considera apenas se há ao menos uma tabela Protheus válida.
        if not any(_is_valid_protheus_table(t) for t in tabelas):
            continue
        if _NOTDEL_RE.search(snippet):
            continue
        linha = int(sql.get("linha", 1))
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "PERF-002",
                "severidade": "error",
                "snippet": _snippet_at_line(content, linha) or snippet[:_SNIPPET_MAX],
                "sugestao_fix": (
                    "Adicione %notDel% (ou D_E_L_E_T_ = ' ') no WHERE para não "
                    "trazer registros logicamente excluídos."
                ),
            }
        )
    return findings


def _check_perf003_no_xfilial(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """PERF-003 (error): SQL contra tabelas Protheus sem %xfilial% (cross-filial leak)."""
    findings: list[dict[str, Any]] = []
    sql_blocks = parsed.get("sql_embedado", []) or []
    funcoes = parsed.get("funcoes", []) or []

    for sql in sql_blocks:
        snippet = sql.get("snippet", "") or ""
        operacao = sql.get("operacao", "")
        if operacao not in ("select", "update", "delete"):
            continue
        tabelas = sql.get("tabelas", []) or []
        if not any(_is_valid_protheus_table(t) for t in tabelas):
            continue
        if _XFILIAL_MACRO_RE.search(snippet):
            continue
        linha = int(sql.get("linha", 1))
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "PERF-003",
                "severidade": "error",
                "snippet": _snippet_at_line(content, linha) or snippet[:_SNIPPET_MAX],
                "sugestao_fix": (
                    "Use %xfilial:TABELA% no WHERE para respeitar a filial corrente "
                    "(evita leak entre filiais)."
                ),
            }
        )
    return findings


def _check_mod001_conout_instead_fwlogmsg(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """MOD-001 (warning): uso de ConOut em vez de FwLogMsg.

    ConOut só escreve no console — não persiste em log estruturado, não tem
    nível/categoria. Prefira FwLogMsg para observabilidade.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=False)
    funcoes = parsed.get("funcoes", []) or []

    for m in _CONOUT_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "MOD-001",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    "Substitua ConOut por FwLogMsg(nivel, msg, ..., categoria) para "
                    "log estruturado e níveis configuráveis."
                ),
            }
        )
    return findings


def _check_mod002_public_declaration(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """MOD-002 (warning): declaração PUBLIC.

    Variáveis PUBLIC poluem o escopo global e são proibidas nas best practices
    Protheus modernas. Use STATIC, LOCAL ou parâmetros.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []

    for m in _PUBLIC_DECL_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "MOD-002",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    "Evite PUBLIC; prefira STATIC/LOCAL ou parâmetros explícitos para "
                    "isolar estado e facilitar testes."
                ),
            }
        )
    return findings


# --- BP-008: shadowing de variável reservada -------------------------------

# Variáveis Public criadas pelo framework Protheus que NÃO devem ser declaradas
# como Local/Static/Private/Public em fonte custom. Comparação é case-insensitive
# (ADVPL trata identificadores assim).
_BP008_RESERVED_VARS: frozenset[str] = frozenset(
    name.upper()
    for name in (
        # Contexto de empresa/filial/usuario
        "cFilAnt", "cEmpAnt", "cUserName", "cModulo", "cTransac", "nProgAnt",
        # Janela principal e flags de execucao
        "oMainWnd", "__cInternet", "nUsado",
        # PE / MVC / ExecAuto
        "PARAMIXB", "aRotina", "lMsErroAuto", "lMsHelpAuto",
    )
)

# Detecta declaração: linha começa com (Local|Static|Private|Public) seguido de
# pelo menos um identificador. Captura group 1 = keyword, group 2 = resto da linha.
_BP008_DECL_RE = re.compile(
    r"^[ \t]*(Local|Static|Private|Public)\b[ \t]+(.+)$",
    re.IGNORECASE | re.MULTILINE,
)

# Em "cVar1, cFilAnt, cVar2 := 'x' as character", separadores são vírgula top-level.
# Pra cada peça, o identificador é o primeiro token alfanumérico (antes de :=, as, espaço).
_BP008_VAR_RE = re.compile(r"^[ \t]*([A-Za-z_][A-Za-z0-9_]*)")


def _check_bp008_shadowed_reserved(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-008 (critical): Local/Static/Private/Public com nome de variável reservada framework.

    Declarar variável local com nome de Public reservada (cFilAnt, cEmpAnt, PARAMIXB, etc.)
    faz shadowing — sua função enxerga "" / Nil em vez do valor real do framework.
    Bug clássico: programador declara `Local cFilAnt := ""` no início e depois usa cFilAnt
    achando que tem o valor da filial atual.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []

    for m_decl in _BP008_DECL_RE.finditer(stripped):
        keyword = m_decl.group(1)
        rest = m_decl.group(2)
        # Split por vírgula top-level (declarações ADVPL não têm vírgulas dentro de
        # argumentos de função aqui, pois é só lado esquerdo de declaração).
        for piece in rest.split(","):
            m_var = _BP008_VAR_RE.match(piece)
            if not m_var:
                continue
            var_name = m_var.group(1)
            if var_name.upper() not in _BP008_RESERVED_VARS:
                continue
            # Match — calcula linha + funcao + snippet
            offset = m_decl.start()
            linha = _line_at(stripped, offset)
            funcao = _funcao_at_line(funcoes, linha)
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": funcao,
                    "linha": linha,
                    "regra_id": "BP-008",
                    "severidade": "critical",
                    "snippet": _snippet_at_line(content, linha),
                    "sugestao_fix": (
                        f"`{keyword} {var_name}` faz shadowing da variável reservada "
                        f"`{var_name}` do framework Protheus. Renomeie para algo distinto "
                        f"(ex: prefixo cliente). Toda função vê valor vazio em vez do real."
                    ),
                }
            )
    return findings


# --- MOD-004: AxCadastro/Modelo2/Modelo3 (legacy) em vez de MVC ------------

# Funções de UI legacy substituídas pelo padrão MVC moderno (FWMBrowse +
# MenuDef + ModelDef + ViewDef). Detecção case-insensitive, exclui method
# calls (`obj:Modelo3()`), strings, comentários e definições homônimas.
_MOD004_LEGACY_FUNCS: frozenset[str] = frozenset({"AXCADASTRO", "MODELO2", "MODELO3"})

_MOD004_CALL_RE = re.compile(
    r"(?<![:.])"                                # not method or property access
    r"\b(AxCadastro|Modelo2|Modelo3)\s*\(",     # function name + opening paren
    re.IGNORECASE,
)

# Mensagem de migração específica por função legacy.
_MOD004_MIGRATION_HINTS: dict[str, str] = {
    "AXCADASTRO": (
        "AxCadastro é Modelo 1 legacy. Migre para MVC: User Function chama "
        "`FWMBrowse():New()` + `SetAlias` + `SetMenuDef`, e a rotina ganha "
        "`MenuDef()`/`ModelDef()`/`ViewDef()` como Static Functions."
    ),
    "MODELO2": (
        "Modelo2 é cadastro legacy de cabecalho + grid de itens. Migre para MVC: "
        "ModelDef() com `oModel:AddFields(\"MASTER\", ...)` + `oModel:AddGrid(\"DETAIL\", \"MASTER\", ...)`. "
        "ViewDef() monta tela com FwFormView + AddField/AddGrid."
    ),
    "MODELO3": (
        "Modelo3 é cadastro legacy pai/filho (cabecalho + itens relacionados). "
        "Migre para MVC: ModelDef() com `AddFields` (cabecalho) + `AddGrid` (itens) + "
        "`SetRelation` ligando filho ao pai via chaves SX9. "
        "Veja `[[advpl-mvc]]` para template completo."
    ),
}


def _check_mod004_legacy_cadastro(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """MOD-004 (info): chamada a AxCadastro/Modelo2/Modelo3 — legacy, deve migrar pra MVC.

    Detecta uso das funções de UI legacy substituídas pelo framework MVC moderno.
    Cada finding sugere o padrão MVC correspondente (Modelo 1 → AxCadastro→FWMBrowse,
    Modelo 2 → cabeçalho+grid, Modelo 3 → pai/filho). Skip strings, comments,
    method calls (`obj:Modelo3()`) e definições homônimas (`User Function AxCadastro()`).
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []
    seen: set[tuple[int, str]] = set()  # dedup por (linha, fn)

    for m in _MOD004_CALL_RE.finditer(stripped):
        name = m.group(1)
        upper = name.upper()
        if upper not in _MOD004_LEGACY_FUNCS:
            continue
        # Skip definição: olha 50 chars antes — se tem "User Function|Static Function|Function" → é definição
        prefix = stripped[max(0, m.start() - 50) : m.start()]
        if _SEC005_DEFINITION_RE.search(prefix):
            continue
        linha = _line_at(stripped, m.start())
        key = (linha, upper)
        if key in seen:
            continue
        seen.add(key)
        funcao = _funcao_at_line(funcoes, linha)
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": funcao,
                "linha": linha,
                "regra_id": "MOD-004",
                "severidade": "info",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": _MOD004_MIGRATION_HINTS[upper],
            }
        )
    return findings


# --- SEC-005: uso de função TOTVS restrita -------------------------------

# Carrega lookup `funcoes_restritas` uma vez (lazy + lru_cache via module-level dict).
# Estrutura: { uppercase_name: alternativa_str }
_SEC005_RESTRICTED: dict[str, str] | None = None


def _sec005_load_restricted() -> dict[str, str]:
    global _SEC005_RESTRICTED
    if _SEC005_RESTRICTED is None:
        import json as _json
        from importlib import resources as _ir
        text = _ir.files("plugadvpl").joinpath("lookups/funcoes_restritas.json").read_text(
            encoding="utf-8"
        )
        _SEC005_RESTRICTED = {
            entry["nome"].upper(): entry.get("alternativa", "") or ""
            for entry in _json.loads(text)
        }
    return _SEC005_RESTRICTED


# Match `name(` precedido por algo que NÃO seja:
#   - `:` ou `.` (method/property call: oObj:Name(), pkg.name())
#   - palavras-chave de definição (Function, Method, Class, Procedure)
# Negative lookbehind controla o caso `:`/`.`. Definitons são tratadas separadamente
# checando se a linha antes do match começa com Function/Method/Class.
_SEC005_CALL_RE = re.compile(
    r"(?<![:.])"           # not after : or .
    r"\b([A-Za-z_][A-Za-z0-9_]*)"   # identifier
    r"\s*\(",                       # opening paren
)

# Padrão pra detectar contexto de declaração (não match em definição da própria fn).
_SEC005_DEFINITION_RE = re.compile(
    r"\b(?:User\s+Function|Static\s+Function|Function|Method|Class|Procedure)\s+\Z",
    re.IGNORECASE,
)


def _check_sec005_restricted_function_call(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """SEC-005 (critical): chamada de função listada em funcoes_restritas (lookup TOTVS).

    Funções TOTVS internas/restritas (~194 catalogadas) não devem aparecer em
    código custom: não documentadas, não suportadas, podem ser removidas em
    release-bump. Algumas com compilação bloqueada desde 12.1.33.

    Estratégia:
      1. Strip comentários + strings.
      2. Encontra todo `<NAME>(` com lookbehind negativo pra `:`/`.` (não pega method calls).
      3. Skip se precedida por keyword de definição (User Function NAME(...) é a própria fn).
      4. Compara uppercase contra _SEC005_RESTRICTED.
    """
    findings: list[dict[str, Any]] = []
    restricted = _sec005_load_restricted()
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []
    seen: set[tuple[int, str]] = set()  # dedup por (linha, nome) — uma chamada repetida = 1 finding

    for m in _SEC005_CALL_RE.finditer(stripped):
        name = m.group(1)
        upper = name.upper()
        if upper not in restricted:
            continue
        # Skip definição: olha 50 chars antes do match pra ver se é Function/Method/Class
        prefix = stripped[max(0, m.start() - 50) : m.start()]
        if _SEC005_DEFINITION_RE.search(prefix):
            continue
        linha = _line_at(stripped, m.start())
        key = (linha, upper)
        if key in seen:
            continue
        seen.add(key)
        funcao = _funcao_at_line(funcoes, linha)
        alternativa = restricted[upper]
        sugestao = (
            f"Função `{name}` é TOTVS-restrita (catalogada em funcoes_restritas) — "
            f"não documentada, não suportada, pode quebrar em release-bump."
        )
        if alternativa:
            sugestao += f" Alternativa sugerida: {alternativa}."
        else:
            sugestao += " Substituta por equivalente público documentado em TDN."
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": funcao,
                "linha": linha,
                "regra_id": "SEC-005",
                "severidade": "critical",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": sugestao,
            }
        )
    return findings


# --- PERF-005: RecCount() para checar existência ---------------------------

# Detecta `RecCount() > 0`, `RecCount() >= 1`, `RecCount() != 0`, `RecCount() <> 0`
# (com ou sem alias-call `SA1->(RecCount())`). NÃO detecta:
# - `RecCount() > 100` (limite específico, intencional)
# - `nTotal := RecCount()` (armazena, não checa)
# Padrão de comparação: > 0, >= 1, != 0, <> 0 (case-insensitive operadores).
_PERF005_RE = re.compile(
    r"\bRecCount\s*\(\s*\)\s*\)?\s*"        # RecCount() possivelmente fechando alias->()
    r"(?:>\s*0(?!\d)|>=\s*1(?!\d)|!=\s*0(?!\d)|<>\s*0(?!\d))",
    re.IGNORECASE,
)


def _check_perf005_reccount_for_existence(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """PERF-005 (warning): RecCount() > 0 / >= 1 / != 0 / <> 0 para checar existência.

    RecCount() força full scan do alias. Para apenas verificar se existe pelo
    menos 1 registro, ``!Eof()`` após DbSeek/DbGoTop é O(1).
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []

    for m in _PERF005_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        funcao = _funcao_at_line(funcoes, linha)
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": funcao,
                "linha": linha,
                "regra_id": "PERF-005",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    "RecCount() força full scan da tabela. Para checar existência, "
                    "use !Eof() após DbSeek/DbGoTop (O(1)) ou subquery EXISTS em SQL."
                ),
            }
        )
    return findings


# --- Orchestrator -------------------------------------------------------------


def lint_source(parsed: dict[str, Any], content: str) -> list[dict[str, Any]]:
    """Aplica as 17 regras single-file. Retorna list[Finding] ordenada por linha.

    Args:
        parsed: dict produzido por parse_source() (com funcoes, sql_embedado, etc.).
        content: conteúdo bruto do fonte (não stripado — os checks fazem strip
            internamente conforme necessidade).

    Retorna lista ordenada por (linha, regra_id) para output determinístico.
    """
    arquivo = parsed.get("arquivo", "") or ""
    findings: list[dict[str, Any]] = []

    findings.extend(_check_bp001_reclock_unbalanced(arquivo, parsed, content))
    findings.extend(_check_bp002_transaction_unbalanced(arquivo, parsed, content))
    findings.extend(_check_bp003_msexecauto_no_check(arquivo, parsed, content))
    findings.extend(_check_bp004_pergunte_no_check(arquivo, parsed, content))
    findings.extend(_check_bp005_too_many_params(arquivo, parsed, content))
    findings.extend(_check_bp006_mixed_reclock_rawapi(arquivo, parsed, content))
    findings.extend(_check_bp008_shadowed_reserved(arquivo, parsed, content))
    findings.extend(_check_sec001_rpcsetenv_in_restful(arquivo, parsed, content))
    findings.extend(_check_sec002_user_function_no_prefix(arquivo, parsed, content))
    findings.extend(_check_sec005_restricted_function_call(arquivo, parsed, content))
    findings.extend(_check_perf001_select_star(arquivo, parsed, content))
    findings.extend(_check_perf002_no_notdel(arquivo, parsed, content))
    findings.extend(_check_perf003_no_xfilial(arquivo, parsed, content))
    findings.extend(_check_perf005_reccount_for_existence(arquivo, parsed, content))
    findings.extend(_check_mod001_conout_instead_fwlogmsg(arquivo, parsed, content))
    findings.extend(_check_mod002_public_declaration(arquivo, parsed, content))
    findings.extend(_check_mod004_legacy_cadastro(arquivo, parsed, content))

    findings.sort(key=lambda f: (int(f["linha"]), str(f["regra_id"])))
    return findings


# =============================================================================
# v0.3.0 — Cross-file lint rules (SX dictionary required, depends on migration 002)
# =============================================================================
# Cada regra é função ``_check_sxNNN(conn) -> list[Finding]``. Findings têm os
# mesmos campos do lint single-file, mas ``arquivo`` pode ser sintético no
# formato ``SX:<tabela>`` (quando o problema vive no dicionário, não em fonte).

# Regex usadas pelas regras cross-file.
_SX005_MAX_FINDINGS = 100  # corte defensivo para SX-005 em DBs grandes
_USER_FUNC_CALL_RE = re.compile(r"\bU_([A-Z][A-Z0-9_]{1,30})\b", re.IGNORECASE)
_SQL_IN_VALID_RE = re.compile(
    r"\b(?:BeginSql|TCQuery|TCSqlExec|MPSysOpenQuery)\b",
    re.IGNORECASE,
)
_INIT_RETURNS_EMPTY_RE = re.compile(
    r"""(['"])\s*\1                    # ""  ou  ''  literal
        | \bSpace\s*\(\s*\d+\s*\)       # Space(N)
        | \bCToD\s*\(\s*['"]\s*['"]\s*\) # CToD("")
        | \bNil\b
        | \b\.F\.\b                     # bool false
        | \b0\s*$                       # apenas zero
    """,
    re.IGNORECASE | re.VERBOSE,
)
_XFILIAL_IN_VALID_RE = re.compile(r"\bxFilial\b", re.IGNORECASE)


def _sx_present(conn: sqlite3.Connection) -> bool:
    """``True`` se migration 002 já foi aplicada (tabela ``campos`` existe)."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='campos'"
    ).fetchone()
    return row is not None


def _index_known_user_funcs(conn: sqlite3.Connection) -> set[str]:
    """Coleta todas as user-functions indexadas (case-insensitive, sem ``U_``)."""
    known: set[str] = set()
    rows = conn.execute(
        "SELECT funcao_norm FROM fonte_chunks WHERE tipo_simbolo IN ('user_function', 'main_function')"
    ).fetchall()
    for (norm,) in rows:
        known.add((norm or "").upper())
    return known


def _index_campos_set(conn: sqlite3.Connection) -> set[str]:
    """``set`` de todos os campos do dicionário (uppercase)."""
    rows = conn.execute("SELECT campo FROM campos").fetchall()
    return {(c[0] or "").upper() for c in rows}


def _index_consultas_aliases(conn: sqlite3.Connection) -> set[str]:
    """``set`` de aliases SXB conhecidos (uppercase)."""
    rows = conn.execute("SELECT DISTINCT alias FROM consultas").fetchall()
    return {(c[0] or "").upper() for c in rows}


def _index_funcoes_restritas(conn: sqlite3.Connection) -> set[str]:
    """``set`` de nomes de funções restritas (uppercase)."""
    try:
        rows = conn.execute("SELECT nome FROM funcoes_restritas").fetchall()
    except sqlite3.OperationalError:
        return set()
    return {(c[0] or "").upper() for c in rows}


def _check_sx001_x3_valid_unknown_func(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-001 (warning): ``X3_VALID`` chama ``U_XYZ`` que não existe nos fontes indexados."""
    findings: list[dict[str, Any]] = []
    known = _index_known_user_funcs(conn)
    rows = conn.execute(
        "SELECT tabela, campo, validacao FROM campos "
        "WHERE validacao LIKE '%U_%' AND validacao != ''"
    ).fetchall()
    for tabela, campo, valid in rows:
        for m in _USER_FUNC_CALL_RE.finditer(valid):
            func = m.group(1).upper()
            if func not in known:
                findings.append(
                    {
                        "arquivo": f"SX:{tabela}",
                        "funcao": campo,
                        "linha": 0,
                        "regra_id": "SX-001",
                        "severidade": "warning",
                        "snippet": valid[:200],
                        "sugestao_fix": (
                            f"X3_VALID de {tabela}.{campo} chama U_{func} que não foi indexada. "
                            "Verifique se o fonte está no projeto ou rode 'plugadvpl ingest'."
                        ),
                    }
                )
                break  # 1 finding por campo basta
    return findings


def _check_sx002_x7_destino_inexistente(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-002 (error): SX7 ``X7_REGRA`` referencia ``X_FIELD`` que não existe em ``campos``."""
    findings: list[dict[str, Any]] = []
    known_campos = _index_campos_set(conn)
    if not known_campos:
        return findings
    rows = conn.execute(
        "SELECT campo_origem, sequencia, campo_destino FROM gatilhos "
        "WHERE campo_destino != ''"
    ).fetchall()
    for orig, seq, dest in rows:
        if dest.upper() not in known_campos:
            findings.append(
                {
                    "arquivo": f"SX:gatilho:{orig}",
                    "funcao": f"#{seq}",
                    "linha": 0,
                    "regra_id": "SX-002",
                    "severidade": "error",
                    "snippet": f"{orig} -> {dest}",
                    "sugestao_fix": (
                        f"Gatilho {orig}#{seq} aponta para campo destino {dest} que não existe "
                        "em campos (SX3). Pode ser typo ou export incompleto."
                    ),
                }
            )
    return findings


def _check_sx003_mv_param_unused_in_fontes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-003 (warning): parâmetro SX6 declarado mas nunca lido em fonte algum."""
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT p.variavel, p.descricao
        FROM parametros p
        WHERE p.custom = 1
          AND NOT EXISTS (
              SELECT 1 FROM parametros_uso pu
              WHERE upper(pu.parametro) = upper(p.variavel)
          )
        LIMIT 200
        """
    ).fetchall()
    for var, desc in rows:
        findings.append(
            {
                "arquivo": f"SX:param:{var}",
                "funcao": "",
                "linha": 0,
                "regra_id": "SX-003",
                "severidade": "warning",
                "snippet": (desc or "")[:200],
                "sugestao_fix": (
                    f"Parâmetro {var} declarado em SX6 mas nenhum fonte indexado o consulta "
                    "(GetMV/SuperGetMV/PutMV). Possível dead code."
                ),
            }
        )
    return findings


def _check_sx004_pergunta_unused_in_fontes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-004 (warning): grupo SX1 sem nenhum ``Pergunte()`` correspondente nos fontes."""
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT DISTINCT p.grupo
        FROM perguntas p
        WHERE NOT EXISTS (
            SELECT 1 FROM perguntas_uso pu
            WHERE upper(pu.grupo) = upper(p.grupo)
        )
        LIMIT 200
        """
    ).fetchall()
    for (grupo,) in rows:
        findings.append(
            {
                "arquivo": f"SX:pergunta:{grupo}",
                "funcao": "",
                "linha": 0,
                "regra_id": "SX-004",
                "severidade": "warning",
                "snippet": grupo,
                "sugestao_fix": (
                    f"Grupo de perguntas {grupo} declarado em SX1 mas nenhum fonte chama "
                    "Pergunte('{grupo}'). Possível dead code."
                ),
            }
        )
    return findings


def _check_sx005_campo_usado_zero_refs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-005 (info): campo SX3 com ``X3_USADO`` mas zero referências em fontes/SX/SX7.

    Anterior fazia 1+N*2 queries com ``LIKE '%campo%'`` (full-table scan a cada campo).
    Agora: 3 queries totais — pré-agrega o corpo onde um campo pode aparecer
    (fonte_chunks.content + campos.validacao + gatilhos.regra) em strings na memória
    e checa substring em Python. Heurística idêntica, ~100-1000× mais rápida em DBs
    grandes (typical Protheus: ~2k fontes × dezenas de KB cada).
    """
    findings: list[dict[str, Any]] = []
    custom_rows = conn.execute(
        "SELECT tabela, campo FROM campos WHERE custom = 1 LIMIT 500"
    ).fetchall()
    if not custom_rows:
        return findings

    fonte_corpus = "\n".join(
        (r[0] or "").upper()
        for r in conn.execute("SELECT content FROM fonte_chunks")
    )
    sx_validacoes = "\n".join(
        (r[0] or "").upper()
        for r in conn.execute("SELECT validacao FROM campos WHERE validacao != ''")
    )
    sx_gatilhos = "\n".join(
        (r[0] or "").upper()
        for r in conn.execute("SELECT regra FROM gatilhos WHERE regra != ''")
    )

    for tabela, campo in custom_rows:
        c = (campo or "").upper()
        if not c:
            continue
        if c in fonte_corpus or c in sx_validacoes or c in sx_gatilhos:
            continue
        findings.append(
            {
                "arquivo": f"SX:{tabela}",
                "funcao": campo,
                "linha": 0,
                "regra_id": "SX-005",
                "severidade": "warning",
                "snippet": f"{tabela}.{campo}",
                "sugestao_fix": (
                    f"Campo custom {tabela}.{campo} não é referenciado em fonte algum nem em "
                    "outras entradas SX. Provável legado — considerar remoção."
                ),
            }
        )
        if len(findings) >= _SX005_MAX_FINDINGS:
            break
    return findings


def _check_sx006_perf_sql_in_x3_valid(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-006 (warning): ``X3_VALID`` faz query SQL (BeginSql/TCQuery) — anti-pattern."""
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        "SELECT tabela, campo, validacao FROM campos "
        "WHERE validacao != ''"
    ).fetchall()
    for tabela, campo, valid in rows:
        if _SQL_IN_VALID_RE.search(valid or ""):
            findings.append(
                {
                    "arquivo": f"SX:{tabela}",
                    "funcao": campo,
                    "linha": 0,
                    "regra_id": "SX-006",
                    "severidade": "warning",
                    "snippet": valid[:200],
                    "sugestao_fix": (
                        f"X3_VALID de {tabela}.{campo} faz query SQL (BeginSql/TCQuery). "
                        "Isso executa em CADA validação — caro. Considere ExistCpo() ou "
                        "Posicione() com cache."
                    ),
                }
            )
    return findings


def _check_sx007_restricted_func_in_x3_valid(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-007 (critical): função em ``X3_VALID`` é uma das ``funcoes_restritas`` TOTVS."""
    findings: list[dict[str, Any]] = []
    restritas = _index_funcoes_restritas(conn)
    if not restritas:
        return findings
    rows = conn.execute(
        "SELECT tabela, campo, validacao FROM campos "
        "WHERE validacao != ''"
    ).fetchall()
    # Padrão para extrair nomes de função do validador (não captura U_).
    func_re = re.compile(r"\b([A-Z][A-Z0-9_]{2,30})\s*\(", re.IGNORECASE)
    for tabela, campo, valid in rows:
        for m in func_re.finditer(valid or ""):
            fname = m.group(1).upper()
            if fname in restritas:
                findings.append(
                    {
                        "arquivo": f"SX:{tabela}",
                        "funcao": campo,
                        "linha": 0,
                        "regra_id": "SX-007",
                        "severidade": "critical",
                        "snippet": valid[:200],
                        "sugestao_fix": (
                            f"X3_VALID de {tabela}.{campo} chama {fname}, função restrita TOTVS "
                            "(não documentada/suportada). Pode quebrar em update do ERP."
                        ),
                    }
                )
                break
    return findings


def _check_sx008_xfilial_in_modo_c(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-008 (warning): tabela ``X2_MODO='C'`` (compartilhada) tem campo SX3 usando ``xFilial``."""
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT c.tabela, c.campo, c.validacao
        FROM campos c
        JOIN tabelas t ON t.codigo = c.tabela
        WHERE t.modo = 'C'
          AND c.validacao != ''
        """
    ).fetchall()
    for tabela, campo, valid in rows:
        if _XFILIAL_IN_VALID_RE.search(valid or ""):
            findings.append(
                {
                    "arquivo": f"SX:{tabela}",
                    "funcao": campo,
                    "linha": 0,
                    "regra_id": "SX-008",
                    "severidade": "warning",
                    "snippet": valid[:200],
                    "sugestao_fix": (
                        f"Tabela {tabela} tem X2_MODO='C' (compartilhada), mas X3_VALID de "
                        f"{campo} usa xFilial(). Inconsistência: dado é único, validação "
                        "tenta filtrar por filial."
                    ),
                }
            )
    return findings


def _check_sx009_obrigat_with_empty_init(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-009 (warning): campo obrigatório mas ``X3_INIT`` retorna vazio (heurística regex)."""
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        "SELECT tabela, campo, inicializador FROM campos "
        "WHERE obrigatorio = 1 AND inicializador != ''"
    ).fetchall()
    for tabela, campo, init in rows:
        if _INIT_RETURNS_EMPTY_RE.search(init or ""):
            findings.append(
                {
                    "arquivo": f"SX:{tabela}",
                    "funcao": campo,
                    "linha": 0,
                    "regra_id": "SX-009",
                    "severidade": "warning",
                    "snippet": init[:200],
                    "sugestao_fix": (
                        f"Campo {tabela}.{campo} é obrigatório mas X3_RELACAO inicializa "
                        "com vazio/zero — usuário sempre vai precisar digitar. Considere "
                        "default real ou tornar opcional."
                    ),
                }
            )
    return findings


def _check_sx010_pesquisar_sem_seek(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-010 (error): gatilho SX7 ``X7_TIPO='P'`` (Pesquisar) sem ``X7_SEEK`` válido."""
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT campo_origem, sequencia, alias, seek
        FROM gatilhos
        WHERE upper(tipo) = 'P'
        """
    ).fetchall()
    for orig, seq, alias, seek in rows:
        if not seek or seek.upper() not in ("S", "1", ".T."):
            findings.append(
                {
                    "arquivo": f"SX:gatilho:{orig}",
                    "funcao": f"#{seq}",
                    "linha": 0,
                    "regra_id": "SX-010",
                    "severidade": "error",
                    "snippet": f"alias={alias} seek={seek}",
                    "sugestao_fix": (
                        f"Gatilho {orig}#{seq} é tipo Pesquisar (P) mas não tem X7_SEEK='S'. "
                        "Marque seek ou troque para tipo Primário (P->S inválido sem SEEK)."
                    ),
                }
            )
    return findings


def _check_sx011_x3_f3_consulta_inexistente(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """SX-011 (error): ``X3_F3`` aponta para alias SXB que não existe."""
    findings: list[dict[str, Any]] = []
    aliases = _index_consultas_aliases(conn)
    if not aliases:
        return findings
    rows = conn.execute(
        "SELECT tabela, campo, f3 FROM campos WHERE f3 != ''"
    ).fetchall()
    for tabela, campo, f3 in rows:
        # X3_F3 pode ter prefixo/sufixo; usamos uppercase exato.
        if f3.upper() not in aliases:
            findings.append(
                {
                    "arquivo": f"SX:{tabela}",
                    "funcao": campo,
                    "linha": 0,
                    "regra_id": "SX-011",
                    "severidade": "error",
                    "snippet": f"X3_F3={f3}",
                    "sugestao_fix": (
                        f"X3_F3 de {tabela}.{campo} aponta para consulta '{f3}' que não existe "
                        "em SXB (consultas). F3 não vai abrir nada."
                    ),
                }
            )
    return findings


# --- Orchestrator cross-file --------------------------------------------------


_CROSS_FILE_RULES: list[tuple[str, Any]] = [
    ("SX-001", _check_sx001_x3_valid_unknown_func),
    ("SX-002", _check_sx002_x7_destino_inexistente),
    ("SX-003", _check_sx003_mv_param_unused_in_fontes),
    ("SX-004", _check_sx004_pergunta_unused_in_fontes),
    ("SX-005", _check_sx005_campo_usado_zero_refs),
    ("SX-006", _check_sx006_perf_sql_in_x3_valid),
    ("SX-007", _check_sx007_restricted_func_in_x3_valid),
    ("SX-008", _check_sx008_xfilial_in_modo_c),
    ("SX-009", _check_sx009_obrigat_with_empty_init),
    ("SX-010", _check_sx010_pesquisar_sem_seek),
    ("SX-011", _check_sx011_x3_f3_consulta_inexistente),
]


def lint_cross_file(
    conn: sqlite3.Connection,
    *,
    rules: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Aplica as 11 regras cross-file (SX-001..SX-011). Retorna lista ordenada.

    Pré-requisito: migration 002 aplicada e dicionário SX ingerido (``ingest-sx``).
    Se as tabelas SX não existirem, retorna lista vazia silenciosamente (não é erro).

    Args:
        conn: conexão SQLite.
        rules: filtro opcional (lista de regra_ids). ``None`` = todas as 11.
    """
    if not _sx_present(conn):
        return []
    findings: list[dict[str, Any]] = []
    selected = set(rules) if rules else None
    for regra_id, check_fn in _CROSS_FILE_RULES:
        if selected is not None and regra_id not in selected:
            continue
        try:
            findings.extend(check_fn(conn))
        except sqlite3.OperationalError:
            # Tabela ausente (ingest_sx incompleto) — pula esta regra.
            continue
    findings.sort(
        key=lambda f: (str(f["regra_id"]), str(f["arquivo"]), str(f["funcao"]))
    )
    return findings


def persist_cross_file_findings(
    conn: sqlite3.Connection, findings: list[dict[str, Any]]
) -> int:
    """Grava findings cross-file na tabela ``lint_findings`` (DELETE + INSERT por regra_id).

    Retorna ``count`` de rows inseridas. Idempotente: deleta findings cross-file
    anteriores antes de inserir os novos (compara por ``regra_id LIKE 'SX-%'``).
    """
    conn.execute("DELETE FROM lint_findings WHERE regra_id LIKE 'SX-%'")
    if not findings:
        conn.commit()
        return 0
    rows = [
        (
            f.get("arquivo", ""),
            f.get("funcao", ""),
            int(f.get("linha", 0)),
            f.get("regra_id", ""),
            f.get("severidade", "warning"),
            (f.get("snippet", "") or "")[:500],
            f.get("sugestao_fix", "") or "",
        )
        for f in findings
    ]
    conn.executemany(
        """
        INSERT INTO lint_findings (
            arquivo, funcao, linha, regra_id, severidade, snippet, sugestao_fix
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)
