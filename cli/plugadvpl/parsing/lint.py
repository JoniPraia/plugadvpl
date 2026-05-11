"""Lint findings: detecta 13 anti-padrões single-file via regex sobre stripped content + parsed data.

Cada regra retorna list[Finding] dict com:
- arquivo: str
- funcao: str (best-effort — pode ser '' se não dentro de função clara)
- linha: int (1-based)
- regra_id: str (e.g., 'BP-001')
- severidade: str ('critical'|'error'|'warning')
- snippet: str (linha problemática, <=200 chars)
- sugestao_fix: str (texto curto explicando o fix)

Estratégia:
- Cada regra é uma função `_check_<id>(arquivo, parsed, content) -> list[Finding]`.
- `lint_source` é o orquestrador público que aplica as 13 regras.
- Apenas regras single-file/regex são implementadas no MVP. Regras que dependem
  de cross-file analysis (BP-007, BP-008, SEC-003...) são adiadas para v0.2.
"""
from __future__ import annotations

import re
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


# --- Orchestrator -------------------------------------------------------------


def lint_source(parsed: dict[str, Any], content: str) -> list[dict[str, Any]]:
    """Aplica as 13 regras single-file. Retorna list[Finding] ordenada por linha.

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
    findings.extend(_check_sec001_rpcsetenv_in_restful(arquivo, parsed, content))
    findings.extend(_check_sec002_user_function_no_prefix(arquivo, parsed, content))
    findings.extend(_check_perf001_select_star(arquivo, parsed, content))
    findings.extend(_check_perf002_no_notdel(arquivo, parsed, content))
    findings.extend(_check_perf003_no_xfilial(arquivo, parsed, content))
    findings.extend(_check_mod001_conout_instead_fwlogmsg(arquivo, parsed, content))
    findings.extend(_check_mod002_public_declaration(arquivo, parsed, content))

    findings.sort(key=lambda f: (int(f["linha"]), str(f["regra_id"])))
    return findings
