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

# SEC-004 (v0.3.19, ajustado v0.3.21 #4 do QA round 2): hardcoded creds.
# Padroes confirmados via TDN + comunidade (Terminal de Informacao, BlackTDN).
# RpcSetEnv(emp, fil, USER, PWD, mod, ...) — slots 3 e 4 sao user/senha texto plano.
# Captura quando user E pwd sao strings literais NAO-VAZIAS (vazio = "usar admin"
# por convencao, smell mas nao leak). Slots 1+2 (emp/fil) podem ser literal OU
# variavel — caso real comum eh `RpcSetEnv(cEmp, cFil, "admin", "totvs", "FAT")`,
# user/pwd hardcoded mas emp/fil vindo de parametro.
_SEC004_ARG_RE = r"(?:\w+|['\"][^'\"]*['\"])"  # variavel OU literal
_SEC004_RPCSETENV_LITERAL_RE = re.compile(
    r"\bRpcSetEnv\s*\("
    rf"\s*{_SEC004_ARG_RE}\s*,"        # emp (var ou literal qualquer)
    rf"\s*{_SEC004_ARG_RE}\s*,"        # fil (var ou literal qualquer)
    r"\s*['\"]([^'\"]+)['\"]\s*,"      # user (LITERAL nao-vazio) — group 1
    r"\s*['\"]([^'\"]+)['\"]",         # pwd (LITERAL nao-vazio) — group 2
    re.IGNORECASE,
)
# PREPARE ENVIRONMENT ... PASSWORD '<literal>' (UDC tbiconn.ch).
# v0.3.22 (#3 do QA round 2): aceita continuacao multilinha via `;` ADVPL.
# `.*?` + DOTALL faz o gap entre PREPARE ENVIRONMENT e PASSWORD cobrir
# multiplas linhas (caso comum). Limitamos a janela com `(?=\bPASSWORD\b)`
# implicito no proprio padrao (nao-greedy garante).
_SEC004_PREPARE_ENV_RE = re.compile(
    r"\bPREPARE\s+ENVIRONMENT\b.*?\bPASSWORD\s+['\"]([^'\"]+)['\"]",
    re.IGNORECASE | re.DOTALL,
)
# SMTPAuth / MailAuth (smtp credentials). Match com 2 args literais nao-vazios.
_SEC004_SMTPAUTH_RE = re.compile(
    r"\b(?:SMTPAuth|MailAuth)\s*\("
    r"\s*['\"][^'\"]+['\"]\s*,"
    r"\s*['\"][^'\"]+['\"]",
    re.IGNORECASE,
)
# Encode64('user:pwd') — Basic Auth construido inline com literal.
# `:` no meio + qualquer coisa de cada lado nao vazia.
_SEC004_BASIC_AUTH_RE = re.compile(
    r"\bEncode64\s*\(\s*['\"][^'\":]+:[^'\"]+['\"]",
    re.IGNORECASE,
)

# SEC-003 (v0.3.19, ajustado v0.3.20 #1 do QA round 2): PII em logs (LGPD).
# Funcoes de log que mandam pro console.log do AppServer (visivel a quem tem
# acesso ao servidor). MsgInfo/MsgBox/Aviso/Help sao UI (nao log) — fora do
# escopo. Help() em particular eh dialogo modal universal em MVC; em validacao
# de campo (X3_VLDUSER, X7_REGRA) Help() concatena nome do cliente o tempo todo.
_SEC003_LOG_FUNCS_RE = re.compile(
    r"\b(?:ConOut|FwLogMsg|MsgLog|LogMsg|UserException)\s*\(",
    re.IGNORECASE,
)
# Variaveis com nome semanticamente PII (v0.3.20 #2 do QA round 2):
#   - Formas LONGAS sao matched diretamente (low FP risk):
#     Cpf, Cnpj, Senha, Password, Token, Cartao, Cvv, ApiKey, Api_Key, Secret
#   - Formas CURTAS ambiguas em PT-BR (Pass/Pin/Card/Pwd/Rg) so casam com
#     prefixo Hungarian estrito `c` literal e end-of-token: cPwd, cRg, cPin,
#     cCard, cPass — evita falso positivo em `cPassagem`/`cPintar`/`cCardapio`/
#     `cArgumento`/etc. Quem usar `nPin` num projeto nao vai ser flaggado, OK
#     (preferimos missar do que gritar massivamente).
_SEC003_PII_VAR_RE = re.compile(
    # Forma longa: prefixo opcional + termo PII completo + sufixo opcional.
    r"\b[a-z]?(?:"
    r"Cpf|Cnpj|Senha|Password|Token|Cartao|Cvv|ApiKey|Api_Key|Secret"
    r")\w*\b"
    r"|"
    # Forma curta: exige `c` literal + termo curto + boundary (sem sufixo).
    r"\bc(?:Pwd|Rg|Pin|Card|Pass)\b",
    re.IGNORECASE,
)
# Campos SX3 conhecidos como PII. Cobre os principais campos sensiveis usados
# em LGPD audits: A1_* (clientes), A2_* (fornecedores), RA_* (funcionarios),
# RH_* (folha/dependentes). v0.3.22 (#5 do QA round 2) expandiu da lista
# original A1_*/RA_* pra incluir A2_* (fornecedor PJ ou PF) e RH_* (dep folha).
_SEC003_PII_FIELDS_RE = re.compile(
    r"\b(?:"
    # Clientes (SA1)
    r"A1_CGC|A1_CPF|A1_NOME|A1_NREDUZ|A1_EMAIL|A1_TEL|A1_END|A1_DDD|"
    # Fornecedores (SA2)
    r"A2_CGC|A2_CPFRG|A2_NOME|A2_NREDUZ|A2_EMAIL|A2_TEL|A2_END|A2_DDD|"
    # Funcionarios (SRA)
    r"RA_CIC|RA_RG|RA_NOMECMP|RA_EMAIL|RA_NUMCP|RA_TELEFON|"
    # Folha — dependentes (SRH)
    r"RH_CPFDEP|RH_NOMEDEP|RH_RGDEP"
    r")\b",
    re.IGNORECASE,
)
# CPF formatado: 999.999.999-99
_SEC003_CPF_LITERAL_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
# CNPJ formatado: 99.999.999/9999-99
_SEC003_CNPJ_LITERAL_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")

# BP-002b (v0.3.25): variavel Private com nome generico em vez de Local.
# Foca em Private (Public ja eh coberto por MOD-002 — evitar duplo finding na
# mesma linha). Whitelist pra padroes legitimos:
#   - MV_PAR01..MV_PAR99 — convencao Pergunte() (variaveis injetadas)
#   - lMsErroAuto, lMsHelpAuto — convencao MsExecAuto (BP-003 cita)
# Reservadas framework (cFilAnt etc) ja sao flagadas por BP-008 — overlap aceito,
# regras tem categorias diferentes (best-practice vs critical).
_BP002B_PRIVATE_RE = re.compile(
    r"^[ \t]*Private[ \t]+(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
_BP002B_WHITELIST = {
    "lMsErroAuto", "lMsHelpAuto",
    # Reservadas framework — overlap com BP-008, mas evita duplo finding na
    # categoria best-practice (BP-008 eh critical, mensagem diferente).
    "cFilAnt", "cEmpAnt", "cUserName", "cModulo", "cTransac", "nProgAnt",
    "oMainWnd", "__cInternet", "__Language", "nUsado", "dDataBase",
    "PARAMIXB", "aRotina", "cFunBkp", "cFunName", "lAutoErrNoFile",
    "INCLUI", "ALTERA",
}
_BP002B_MV_PAR_RE = re.compile(r"^MV_PAR\d{2}$", re.IGNORECASE)

# BP-007 (v0.3.24): funcao sem header Protheus.doc.
# Pattern oficial TOTVS: bloco abre com `/*/{Protheus.doc} <NomeFn>` e fecha
# com `/*/`. Detector busca o opening nas N linhas ANTES da declaracao da
# funcao — 30 linhas eh janela conservadora (header tipico tem 10-20 linhas).
# Match loose pra evitar FP: presença do opening conta, nao exigimos que o
# nome no header bata exatamente com a funcao (algumas equipes copiam-cola).
_BP007_DOC_OPEN_RE = re.compile(
    r"/\*/\s*\{\s*Protheus\.doc\s*\}", re.IGNORECASE,
)
_BP007_WINDOW_LINES = 30  # quantas linhas antes da funcao olhar

# SEC-002: User Function sem prefixo de cliente/PE pattern.
# Padrão Protheus PE: ^[A-Z]{2,4}\d{2,4}[A-Z_]*$ (com pelo menos 2 letras finais opcionais)
_PE_NAME_RE = re.compile(r"^[A-Z]{2,4}\d{2,4}[A-Z_]*$")
# Prefixos típicos de cliente custom. v0.3.28 (Audit V4 #3 ALTA): removidos
# `FAT|FIN|COM|EST|CTB|FIS|PCP|MNT` (eram modulos Protheus, casavam palavras
# PT-BR comuns como FATURA/COMPRA/FINALIZA → falso negativo massivo) +
# `U_` (dead code: parser extrai nome SEM o U_) + `MT[A-Z]/MA\d` (sao padroes
# de PE oficial TOTVS, ja cobertos por _PE_NAME_RE). Sobram so prefixos
# que sao genuinamente "iniciais de empresa" e improvaveis em palavras PT-BR.
_CLIENT_PREFIX_RE = re.compile(
    r"^(MGF|MZF|ZZF|ZF|XX|XYZ|CLI)",
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
        # v0.3.18 (#9 do QA report): dedup por LINHA antes de contar opens.
        # `ZH3->(RecLock("ZH3",...))` casa AMBOS regexes (literal + alias-form),
        # gerando 2 opens pra 1 RecLock real → BP-001 reportava 2x na mesma linha.
        opens_by_line: dict[int, int] = {}
        for m in _RECLOCK_OPEN_RE.finditer(scope):
            off = m.start() + f["char_inicio"]
            linha = _line_at(content, off)
            opens_by_line.setdefault(linha, off)
        for m in _RECLOCK_VIA_ALIAS_RE.finditer(scope):
            off = m.start() + f["char_inicio"]
            linha = _line_at(content, off)
            opens_by_line.setdefault(linha, off)
        opens = sorted(opens_by_line.values())
        closes_count = len(_MSUNLOCK_RE.findall(scope))
        if len(opens) <= closes_count:
            continue
        # Reportar os opens "extras" (os últimos N=opens-closes em ordem).
        unbalanced = opens[closes_count:]
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


def _check_bp002b_private_when_local(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-002b (warning): `Private <var>` em vez de `Local`.

    Foca em `Private` — `Public` eh coberto por MOD-002 (evita duplo finding).
    Whitelist:
      - `MV_PAR01..MV_PAR99` (convencao Pergunte injecta no escopo)
      - `lMsErroAuto`/`lMsHelpAuto` (convencao MsExecAuto)
      - Reservadas framework (cFilAnt etc) — overlap com BP-008
    Strings/comentarios sao limpos pelo strip_advpl.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=False)
    funcoes = parsed.get("funcoes", []) or []

    for m in _BP002B_PRIVATE_RE.finditer(stripped):
        decl = m.group(1).strip()
        # Parse multi-var: extrai os identificadores ate o 1o `:=` ou `,`
        # de cada segmento (ignora valor da atribuicao). Split por `,` no nivel
        # 0 (sem balancear parens — heuristica suficiente pra `Private a,b,c`).
        names: list[str] = []
        # Pega o lado esquerdo de := se existir, antes do primeiro :=
        before_assign = decl.split(":=", 1)[0]
        for part in before_assign.split(","):
            name = part.strip()
            if not name:
                continue
            # Pode ter espacos no meio (`cA cB`?) — pega o primeiro identificador.
            name = re.split(r"\s+", name, maxsplit=1)[0].strip()
            if name and re.match(r"^[A-Za-z_]\w*$", name):
                names.append(name)
        for name in names:
            # Whitelist check (case-insensitive vs lowercase form do whitelist)
            name_lower = name.lower()
            if any(name_lower == w.lower() for w in _BP002B_WHITELIST):
                continue
            if _BP002B_MV_PAR_RE.match(name):
                continue
            linha = _line_at(stripped, m.start())
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": _funcao_at_line(funcoes, linha),
                    "linha": linha,
                    "regra_id": "BP-002b",
                    "severidade": "warning",
                    "snippet": _snippet_at_line(content, linha),
                    "sugestao_fix": (
                        f"Trocar `Private {name}` por `Local {name}`. Private "
                        "polui call stack e pode ser sobrescrita por funcoes "
                        "chamadas. Manter Private SO quando ha necessidade "
                        "explicita (MV_PAR* via Pergunte, lMsErroAuto via "
                        "MsExecAuto, ou ponte pra framework legado)."
                    ),
                }
            )
    return findings


def _check_bp007_no_protheus_doc(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """BP-007 (info): funcao sem header Protheus.doc nas linhas anteriores.

    Pra cada User/Static/Main Function ou Method, busca `/*/{Protheus.doc}`
    nas N=30 linhas antes da declaracao. Match loose (so o opening) — nao
    exigimos nome do header bater com o nome da funcao porque equipes
    fazem copy-paste; a presenca do bloco ja indica intenção de documentar.
    """
    findings: list[dict[str, Any]] = []
    funcoes = parsed.get("funcoes", []) or []
    if not funcoes:
        return findings
    lines = content.splitlines()

    for f in funcoes:
        nome = f.get("nome", "") or ""
        if not nome:
            continue
        linha_inicio = int(f.get("linha_inicio", 0))
        if linha_inicio <= 0:
            continue
        # Janela: [max(0, linha_inicio - WINDOW), linha_inicio - 1] (1-indexed → slice 0-indexed).
        start = max(0, linha_inicio - 1 - _BP007_WINDOW_LINES)
        end = linha_inicio - 1
        if end <= start:
            window = ""
        else:
            window = "\n".join(lines[start:end])
        if _BP007_DOC_OPEN_RE.search(window):
            continue
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": nome.upper(),
                "linha": linha_inicio,
                "regra_id": "BP-007",
                "severidade": "info",
                "snippet": _snippet_at_line(content, linha_inicio),
                "sugestao_fix": (
                    f"Adicione header Protheus.doc antes de `{nome}`: "
                    "`/*/{Protheus.doc} <NOME>` + `@type function` + `@author` + `@since` + "
                    "`@param`/`@return` + `/*/`. Padrão TOTVS pra geracao automatica de docs."
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


def _check_sec004_hardcoded_creds(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """SEC-004 (warning): credenciais hardcoded em codigo fonte.

    Padroes detectados (TDN + comunidade ADVPL):
      - `RpcSetEnv("emp", "fil", "user", "pwd", ...)` com user E pwd literais
        nao-vazios (slots 3+4). Vazio = usar admin default por convencao
        (smell, mas nao leak).
      - `PREPARE ENVIRONMENT ... PASSWORD '<literal>'` (UDC tbiconn.ch).
      - `oMail:SMTPAuth("user", "pwd")` ou `MailAuth("user", "pwd")`.
      - `Encode64("user:pwd")` (Basic Auth literal pra REST).

    Strings sao removidas antes de buscar (`strip_advpl(strip_strings=False)`
    preserva strings; comentarios sao limpos). Assim chamadas em comentario
    nao disparam.

    Mitigacao recomendada: ler de SX6 via `SuperGetMV/GetNewPar`, ou variavel
    de ambiente, ou cofre dedicado.
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=False)
    funcoes = parsed.get("funcoes", []) or []

    def _emit(off: int, snippet_extra: str, suggestion: str) -> None:
        linha = _line_at(stripped, off)
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "SEC-004",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha) or snippet_extra,
                "sugestao_fix": suggestion,
            }
        )

    for m in _SEC004_RPCSETENV_LITERAL_RE.finditer(stripped):
        _emit(
            m.start(),
            m.group(0)[:120],
            "Mova user/senha pra MV_* em SX6 (encrypted via EncryptPwd) e leia "
            "via SuperGetMV/GetNewPar em runtime. NUNCA commitar credenciais "
            "no fonte — fica exposto no git e em qualquer fork do RPO.",
        )
    for m in _SEC004_PREPARE_ENV_RE.finditer(stripped):
        _emit(
            m.start(),
            m.group(0)[:120],
            "Substitua a senha literal em PREPARE ENVIRONMENT por leitura de "
            "MV_* via SuperGetMV/GetNewPar. Manter `PASSWORD ''` (vazio) eh "
            "OK quando o usuario eh admin default; o problema eh literal explicito.",
        )
    for m in _SEC004_SMTPAUTH_RE.finditer(stripped):
        _emit(
            m.start(),
            m.group(0)[:120],
            "Mova user/senha SMTP pra MV_RELAUSR/MV_RELAPSW em SX6 e leia via "
            "SuperGetMV. Esses parametros ja existem no Protheus exatamente "
            "pra esse uso.",
        )
    for m in _SEC004_BASIC_AUTH_RE.finditer(stripped):
        _emit(
            m.start(),
            m.group(0)[:120],
            "Encode64('user:pwd') hardcoded vaza credencial. Construa o header "
            "Basic com user/pwd vindos de MV_* (SX6) ou variavel de ambiente.",
        )

    return findings


def _check_sec003_pii_in_logs(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """SEC-003 (warning): PII / dados sensiveis em logs.

    Detecta chamadas a `ConOut/FwLogMsg/MsgLog/LogMsg/UserException/Help` cujos
    argumentos contem:
      - variavel com nome PII (`cCpf`, `cSenha`, `cToken`, `cPwd`, ...)
      - campo SX3 conhecido sensivel (`A1_CGC`, `A1_CPF`, `RA_CIC`, ...)
      - CPF/CNPJ literal formatado em string

    NAO sinaliza:
      - `MsgInfo/MsgAlert/MsgBox/Aviso` (UI modal pra usuario autenticado, nao log)
      - Strings literais sem variavel PII (ex: `ConOut("CPF invalido")`)
      - Comentarios (limpos pelo strip_advpl)

    Mitigacao: mascarar antes de logar (`Transform(cCpf,"@R 999.999.999-99")`
    + ofuscar parte; ou nao logar PII em producao).
    """
    findings: list[dict[str, Any]] = []
    # Duas variantes: com strings (pra detectar CPF/CNPJ literal) e sem strings
    # (pra detectar nome de variavel/campo sem confundir com label "CPF invalido").
    stripped_keep = strip_advpl(content, strip_strings=False)
    stripped_no_str = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []

    for m in _SEC003_LOG_FUNCS_RE.finditer(stripped_keep):
        # Extrai conteudo dos parenteses balanceados a partir do `(` do match.
        open_paren = m.end() - 1
        depth = 0
        end = open_paren
        for i in range(open_paren, len(stripped_keep)):
            ch = stripped_keep[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        args_with_str = stripped_keep[open_paren + 1 : end]
        # Mesma janela na variante sem strings (offsets coincidem ate o length total).
        args_no_str = stripped_no_str[open_paren + 1 : end]

        # Var/field PII: checar fora de strings (caso contrario "CPF invalido"
        # literal vira false positive).
        # CPF/CNPJ literal: checar com strings preservadas (esta DENTRO de string).
        signal: str | None = None
        if _SEC003_PII_VAR_RE.search(args_no_str):
            signal = "variavel com nome PII (cCpf/cSenha/cToken/...)"
        elif _SEC003_PII_FIELDS_RE.search(args_no_str):
            signal = "campo SX3 sensivel (A1_CGC/A1_CPF/RA_CIC/...)"
        elif _SEC003_CPF_LITERAL_RE.search(args_with_str):
            signal = "CPF formatado literal em string"
        elif _SEC003_CNPJ_LITERAL_RE.search(args_with_str):
            signal = "CNPJ formatado literal em string"

        if signal is None:
            continue

        linha = _line_at(stripped_keep, m.start())
        findings.append(
            {
                "arquivo": arquivo,
                "funcao": _funcao_at_line(funcoes, linha),
                "linha": linha,
                "regra_id": "SEC-003",
                "severidade": "warning",
                "snippet": _snippet_at_line(content, linha),
                "sugestao_fix": (
                    f"PII em log ({signal}): viola LGPD se cair em producao. "
                    "Mascarar antes de logar (Transform + ocultar trecho), ou "
                    "remover o log de PII e usar log estruturado de transacao "
                    "sem dado pessoal."
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
        # Data sistema (CRITICA — shadowing dela quebra qualquer date logic)
        "dDataBase",
        # Funcao name tracking (FunName/SetFunName cache)
        "cFunBkp", "cFunName",
        # Janela principal e flags de execucao
        "oMainWnd", "__cInternet", "__Language", "nUsado",
        # PE / MVC / ExecAuto / Helper
        "PARAMIXB", "aRotina", "lMsErroAuto", "lMsHelpAuto", "lAutoErrNoFile",
        # MVC operation flags (preenchidas pelo framework conforme acao do usuario)
        "INCLUI", "ALTERA",
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


# --- PERF-004: string concat com +/+= em loop (O(n²)) -----------------------

# Estratégia em 2 passes sobre o conteúdo já stripado de strings/comentários:
# 1. Encontra ranges (start, end) de cada loop body — While/EndDo, For/Next.
#    Stack-based pra suportar loops aninhados.
# 2. Em cada range, busca padrões de concat de string em variável c-prefixed
#    (hungarian notation: `c<NAME>` = character/string).

_PERF004_LOOP_KW_RE = re.compile(
    r"\b(While|For|EndDo|Next)\b",
    re.IGNORECASE,
)

# Compound: cVar += ... (variável começa com c → string por convenção húngara)
_PERF004_COMPOUND_RE = re.compile(
    r"\bc[A-Za-z_]\w*\s*\+=",
    re.IGNORECASE,
)

# Long form: cVar := cVar + ... (mesmo nome dos dois lados via backreference)
_PERF004_LONGFORM_RE = re.compile(
    r"\b(c[A-Za-z_]\w*)\s*:=\s*\1\s*\+",
    re.IGNORECASE,
)


def _perf004_loop_ranges(stripped: str) -> list[tuple[int, int]]:
    """Retorna lista de (start, end) pra cada loop body (entre While/EndDo, For/Next).

    Suporta loops aninhados via stack. Loops mal-pareados (sem closer) são ignorados.
    """
    ranges: list[tuple[int, int]] = []
    stack: list[tuple[str, int]] = []  # [(kind, body_start_pos), ...]
    for m in _PERF004_LOOP_KW_RE.finditer(stripped):
        kw = m.group(1).lower()
        if kw == "while":
            stack.append(("while", m.end()))   # body começa após "While"
        elif kw == "for":
            stack.append(("for", m.end()))     # body começa após "For"
        elif kw == "enddo":
            # Match com While mais recente
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == "while":
                    body_start = stack.pop(i)[1]
                    ranges.append((body_start, m.start()))
                    break
        elif kw == "next":
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == "for":
                    body_start = stack.pop(i)[1]
                    ranges.append((body_start, m.start()))
                    break
    return ranges


def _check_perf004_string_concat_in_loop(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """PERF-004 (warning): cVar += ou cVar := cVar + ... dentro de loop While/For (O(n²)).

    Strings ADVPL são imutáveis — cada concat aloca string nova, copia conteúdo
    antigo + novo, descarta o anterior. 1.000 concats = ~500.000 chars copiados.
    Usa hungarian notation (variável começa com `c`) pra distinguir string concat
    de accumulator numérico (`nTotal += 1` é OK — n-prefix = numeric).
    """
    findings: list[dict[str, Any]] = []
    stripped = strip_advpl(content, strip_strings=True)
    funcoes = parsed.get("funcoes", []) or []
    loop_ranges = _perf004_loop_ranges(stripped)
    if not loop_ranges:
        return findings

    seen: set[tuple[int, int]] = set()  # dedup por (linha, col-ish via match.start)

    for body_start, body_end in loop_ranges:
        body = stripped[body_start:body_end]
        # Compound (cVar +=)
        for m in _PERF004_COMPOUND_RE.finditer(body):
            offset = body_start + m.start()
            linha = _line_at(stripped, offset)
            key = (linha, m.start())
            if key in seen:
                continue
            seen.add(key)
            funcao = _funcao_at_line(funcoes, linha)
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": funcao,
                    "linha": linha,
                    "regra_id": "PERF-004",
                    "severidade": "warning",
                    "snippet": _snippet_at_line(content, linha),
                    "sugestao_fix": (
                        "Strings ADVPL são imutáveis — concat em loop é O(n²) (cada "
                        "iteração aloca string nova + copia anterior). Acumule em "
                        "array (aAdd) e use FwArrayJoin/Array2String no final, OU "
                        "use FCreate/FWrite buffer pra arquivo, OU StringBuilder."
                    ),
                }
            )
        # Long form (cVar := cVar + ...)
        for m in _PERF004_LONGFORM_RE.finditer(body):
            offset = body_start + m.start()
            linha = _line_at(stripped, offset)
            key = (linha, m.start())
            if key in seen:
                continue
            seen.add(key)
            funcao = _funcao_at_line(funcoes, linha)
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": funcao,
                    "linha": linha,
                    "regra_id": "PERF-004",
                    "severidade": "warning",
                    "snippet": _snippet_at_line(content, linha),
                    "sugestao_fix": (
                        f"`{m.group(1)} := {m.group(1)} + ...` em loop é O(n²) — "
                        "strings ADVPL são imutáveis. Acumule em array + "
                        "FwArrayJoin/Array2String no final pra O(n)."
                    ),
                }
            )
    return findings


# --- MOD-004: AxCadastro/Modelo2/Modelo3 (legacy) em vez de MVC ------------

# Funções de UI legacy substituídas pelo padrão MVC moderno (FWMBrowse +
# MenuDef + ModelDef + ViewDef). Detecção case-insensitive, exclui method
# calls (`obj:Modelo3()`), strings, comentários e definições homônimas.
_MOD004_LEGACY_FUNCS: frozenset[str] = frozenset({
    "AXCADASTRO", "MODELO2", "MODELO3", "MSNEWGETDADOS",
})

_MOD004_CALL_RE = re.compile(
    r"(?<![:.])"                                # not method or property access
    r"\b(AxCadastro|Modelo2|Modelo3|MsNewGetDados)\s*\(",    # function/class name + opening paren
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
    "MSNEWGETDADOS": (
        "MsNewGetDados é classe deprecada desde Protheus 12.1.17 (não recebe mais updates "
        "TOTVS) — TOTVS recomenda MVC. Para grid em tela MVC use `oModel:AddGrid(\"DETAIL\", \"MASTER\", oStruct)`. "
        "Para grid ad-hoc fora de MVC, considere `FWBrowse` ou tabela temporária + AddGrid em mini-MVC."
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

# Detecta `RecCount() > 0` / `LastRec() > 0` (e variantes >=1, !=0, <>0)
# com ou sem alias-call `SA1->(RecCount())`. TDN confirma que LastRec é
# idêntica a RecCount e a substitui (RecCount é obsoleta, mantida só por compat).
# NÃO detecta:
# - `RecCount() > 100` (limite específico, intencional)
# - `nTotal := RecCount()` (armazena, não checa)
_PERF005_RE = re.compile(
    r"\b(?:RecCount|LastRec)\s*\(\s*\)\s*\)?\s*"   # RecCount() ou LastRec() poss. fechando alias->()
    r"(?:>\s*0(?!\d)|>=\s*1(?!\d)|!=\s*0(?!\d)|<>\s*0(?!\d))",
    re.IGNORECASE,
)


def _check_perf005_reccount_for_existence(
    arquivo: str, parsed: dict[str, Any], content: str
) -> list[dict[str, Any]]:
    """PERF-005 (warning): RecCount() ou LastRec() para checar existência (use !Eof()).

    RecCount()/LastRec() forçam full scan do alias. Para apenas verificar se
    existe pelo menos 1 registro, ``!Eof()`` após DbSeek/DbGoTop é O(1).
    LastRec é idêntica a RecCount e a substitui (RecCount obsoleta, kept só por compat).
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
                    "RecCount()/LastRec() forçam full scan da tabela. Para checar "
                    "existência, use !Eof() após DbSeek/DbGoTop (O(1)) ou subquery "
                    "EXISTS em SQL. LastRec é idêntica a RecCount (a substitui — "
                    "RecCount é obsoleta, kept por compat)."
                ),
            }
        )
    return findings


# --- Orchestrator -------------------------------------------------------------


def lint_source(parsed: dict[str, Any], content: str) -> list[dict[str, Any]]:
    """Aplica as 18 regras single-file. Retorna list[Finding] ordenada por linha.

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
    findings.extend(_check_bp002b_private_when_local(arquivo, parsed, content))
    findings.extend(_check_bp006_mixed_reclock_rawapi(arquivo, parsed, content))
    findings.extend(_check_bp007_no_protheus_doc(arquivo, parsed, content))
    findings.extend(_check_bp008_shadowed_reserved(arquivo, parsed, content))
    findings.extend(_check_sec001_rpcsetenv_in_restful(arquivo, parsed, content))
    findings.extend(_check_sec002_user_function_no_prefix(arquivo, parsed, content))
    findings.extend(_check_sec003_pii_in_logs(arquivo, parsed, content))
    findings.extend(_check_sec004_hardcoded_creds(arquivo, parsed, content))
    findings.extend(_check_sec005_restricted_function_call(arquivo, parsed, content))
    findings.extend(_check_perf001_select_star(arquivo, parsed, content))
    findings.extend(_check_perf002_no_notdel(arquivo, parsed, content))
    findings.extend(_check_perf003_no_xfilial(arquivo, parsed, content))
    findings.extend(_check_perf004_string_concat_in_loop(arquivo, parsed, content))
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
        | (?<![A-Za-z0-9_])\.F\.(?![A-Za-z0-9_])  # bool false (v0.3.28: \b\.F\.\b nunca casava — `.` é non-word)
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
                        f"Campo {tabela}.{campo} é obrigatório mas X3_INIT inicializa "
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


# PERF-006 (v0.3.27): WHERE/ORDER BY em coluna fora dos indices SIX.
# Pseudo-colunas Protheus que NUNCA tem indice (e portanto sempre apareceriam
# como FP) — D_E_L_E_T_, R_E_C_N_O_, R_E_C_D_E_L_.
_PERF006_PSEUDO_COLS = {"D_E_L_E_T_", "R_E_C_N_O_", "R_E_C_D_E_L_"}
# Pattern de coluna Protheus: <2-3 letras/digitos><underscore><resto alfa>.
# Ex: A1_COD, B1_DESC, RA_CIC, R8_TIPO. Prefixo: 1 letra + 0-2 alfanumericos.
_PERF006_COLUMN_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,2})_([A-Z][A-Z_0-9]*)\b")
# Extrai cláusulas WHERE e ORDER BY. Captura tudo até a próxima keyword
# limítrofe (GROUP BY, HAVING, EndSql, etc) — best-effort.
_PERF006_WHERE_RE = re.compile(
    r"\bWHERE\b(.*?)(?=\bGROUP\s+BY\b|\bHAVING\b|\bORDER\s+BY\b|\bEndSql\b|$)",
    re.IGNORECASE | re.DOTALL,
)
_PERF006_ORDERBY_RE = re.compile(
    r"\bORDER\s+BY\b(.*?)(?=\bEndSql\b|$)",
    re.IGNORECASE | re.DOTALL,
)


def _check_perf006_where_orderby_no_index(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """PERF-006 (info): coluna em WHERE/ORDER BY que nao esta em nenhum
    indice SIX da tabela.

    Cross-file: depende do dicionario SX (`indices`) ingerido. Skipa
    silenciosamente quando ausente.

    Heuristica:
      1. Pra cada `sql_embedado` row com WHERE ou ORDER BY no snippet
      2. Extrai colunas estilo `<TBL>_<NOME>` da clausula
      3. Filtra pseudo-colunas (D_E_L_E_T_, etc) e *_FILIAL (sempre primeira
         chave em qualquer composto, nao precisa flagar)
      4. Pra cada (tabela, coluna): verifica se coluna aparece em qualquer
         `indices.chave` da tabela
      5. Se NAO encontrar em nenhum indice → emite PERF-006

    Cobertura intencionalmente conservadora (info, nao warning):
      - Skipa coluna sem prefixo claro de tabela (alias dinamico)
      - Skipa quando tabela nao esta em `indices` (provavelmente standard,
        SX so cobre custom)
      - 1 finding por (arquivo, linha, tabela, coluna) — dedup automatica
    """
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT arquivo, funcao, linha, snippet
        FROM sql_embedado
        WHERE upper(snippet) LIKE '%WHERE%' OR upper(snippet) LIKE '%ORDER BY%'
        """
    ).fetchall()
    if not rows:
        return findings

    # Cache de indices por tabela: {tabela.upper(): set(colunas indexadas)}.
    indices_cache: dict[str, set[str]] = {}
    for tbl, chave in conn.execute(
        "SELECT upper(tabela), upper(chave) FROM indices"
    ).fetchall():
        if not tbl:
            continue
        cols_in_chave = set(_PERF006_COLUMN_RE.findall(chave or ""))
        # findall retorna list[tuple[prefix, suffix]] — concatena de volta.
        col_names = {f"{p}_{s}" for p, s in cols_in_chave}
        indices_cache.setdefault(tbl, set()).update(col_names)

    if not indices_cache:
        return findings  # Sem indices ingeridos — nada a comparar.

    seen: set[tuple[str, int, str, str]] = set()  # dedup
    for arquivo, funcao, linha, snippet in rows:
        snippet_up = (snippet or "").upper()
        # Coleta colunas em WHERE + ORDER BY.
        clauses: list[str] = []
        for m in _PERF006_WHERE_RE.finditer(snippet_up):
            clauses.append(m.group(1))
        for m in _PERF006_ORDERBY_RE.finditer(snippet_up):
            clauses.append(m.group(1))
        if not clauses:
            continue
        clause_text = " ".join(clauses)
        cols_found = _PERF006_COLUMN_RE.findall(clause_text)
        for prefix, suffix in cols_found:
            full = f"{prefix}_{suffix}"
            if full in _PERF006_PSEUDO_COLS:
                continue
            if suffix == "FILIAL":  # *_FILIAL — sempre primeiro do composto
                continue
            tabela = prefix  # A1 → SA1 estilo? Nao — `A1` eh prefixo, tabela real
            # eh "SA1" / "SC5". Mas indices.tabela usa "SA1" estilo. Tentativas:
            # buscar em indices_cache pelas tabelas cuja chave contem o prefix.
            # Heuristica: pra cada indice cached, se algum nome de coluna comeca
            # com `<prefix>_`, esse indice eh da tabela em questao.
            matched_table = None
            for tbl, cols in indices_cache.items():
                if any(c.startswith(prefix + "_") for c in cols):
                    matched_table = tbl
                    if full in cols:
                        # Coluna esta em ALGUM indice dessa tabela — OK.
                        matched_table = "INDEXED"
                        break
            if matched_table is None or matched_table == "INDEXED":
                continue  # Sem tabela mapeada (skip) ou esta indexada (OK)
            # matched_table existe mas a coluna nao esta em nenhum indice.
            key = (arquivo, int(linha or 0), matched_table, full)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "arquivo": arquivo,
                    "funcao": funcao or "",
                    "linha": int(linha or 0),
                    "regra_id": "PERF-006",
                    "severidade": "info",
                    "snippet": f"{matched_table}.{full} em WHERE/ORDER BY (sem indice SIX)",
                    "sugestao_fix": (
                        f"Coluna `{full}` aparece em WHERE/ORDER BY mas nao "
                        f"esta em nenhum indice SIX da tabela {matched_table}. "
                        "Opcoes: (1) adicionar indice custom no SIX (`X3_INDX_NOM` "
                        f"ou `INDICE >= 21`); (2) refatorar query pra usar "
                        "coluna ja indexada (ver `tables` pra lista de indices); "
                        "(3) pre-filtrar via DbSeek antes do TCQuery."
                    ),
                }
            )
    return findings


def _check_mod003_static_funcs_to_class(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """MOD-003 (info): grupos de Static Function com prefixo comum em mesmo arquivo.

    Heuristica:
      - Grupo = >= 3 Static Functions cujo nome compartilha prefixo de >= 3 chars
        no mesmo arquivo.
      - Prefixo derivado dos primeiros 3-6 chars (testa 6→3 e pega o maior
        que ainda agrupa >=3 fns).
      - Static = scope file-level, indica que dados/state SAO compartilhados
        no fonte (Static Function geralmente coexiste com Static var no topo).

    Emite 1 finding por grupo, na linha da PRIMEIRA funcao do grupo.
    """
    findings: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT arquivo, funcao, linha_inicio
        FROM fonte_chunks
        WHERE tipo_simbolo = 'static_function'
        ORDER BY arquivo, linha_inicio
        """
    ).fetchall()
    if not rows:
        return findings

    # Agrupa por arquivo.
    by_file: dict[str, list[tuple[str, int]]] = {}
    for arquivo, funcao, linha in rows:
        by_file.setdefault(arquivo, []).append((funcao, int(linha or 1)))

    for arquivo, fns in by_file.items():
        if len(fns) < 3:
            continue
        # Pra cada candidato de prefix len (6 → 3), agrupa e ve se algum
        # grupo bate threshold. Parar no primeiro tamanho que produz grupo
        # >=3 (preferencia por prefixo mais longo = mais especifico).
        emitted_prefixes: set[str] = set()
        for prefix_len in (6, 5, 4, 3):
            groups: dict[str, list[tuple[str, int]]] = {}
            for nome, linha in fns:
                if len(nome) < prefix_len:
                    continue
                key = nome[:prefix_len].lower()
                groups.setdefault(key, []).append((nome, linha))
            for prefix, group_fns in groups.items():
                if len(group_fns) < 3:
                    continue
                # Evita re-emitir grupo que ja foi capturado por prefix mais longo.
                # `any(p.startswith(prefix))`: algum prefix ja emitido eh MAIS
                # ESPECIFICO que o atual (i.e., o atual eh prefixo dele) → skip.
                if any(p.startswith(prefix) for p in emitted_prefixes):
                    continue
                emitted_prefixes.add(prefix)
                # Primeira funcao do grupo (linha mais baixa).
                first_nome, first_linha = min(group_fns, key=lambda x: x[1])
                fn_names = ", ".join(sorted(n for n, _ in group_fns))
                findings.append(
                    {
                        "arquivo": arquivo,
                        "funcao": first_nome,
                        "linha": first_linha,
                        "regra_id": "MOD-003",
                        "severidade": "info",
                        "snippet": f"{len(group_fns)} Static Functions com prefixo `{prefix}*`",
                        "sugestao_fix": (
                            f"Grupo de {len(group_fns)} Static Functions com prefixo "
                            f"`{prefix}*` no mesmo fonte ({fn_names}) sao candidatos a "
                            "refatorar pra `Class ... Method`. OOP melhora encapsulamento, "
                            "facilita testabilidade e elimina dependencia de state Static "
                            "compartilhado. Em TLPP use `class` com modificadores "
                            "`public`/`private`/`protected`."
                        ),
                    }
                )
    return findings


# Tupla: (regra_id, check_fn, requires_sx).
# requires_sx=True → so roda quando dicionario SX foi ingerido.
# requires_sx=False → roda sempre (ex: MOD-003 usa so fonte_chunks).
_CROSS_FILE_RULES: list[tuple[str, Any, bool]] = [
    ("SX-001", _check_sx001_x3_valid_unknown_func, True),
    ("SX-002", _check_sx002_x7_destino_inexistente, True),
    ("SX-003", _check_sx003_mv_param_unused_in_fontes, True),
    ("SX-004", _check_sx004_pergunta_unused_in_fontes, True),
    ("SX-005", _check_sx005_campo_usado_zero_refs, True),
    ("SX-006", _check_sx006_perf_sql_in_x3_valid, True),
    ("SX-007", _check_sx007_restricted_func_in_x3_valid, True),
    ("SX-008", _check_sx008_xfilial_in_modo_c, True),
    ("SX-009", _check_sx009_obrigat_with_empty_init, True),
    ("SX-010", _check_sx010_pesquisar_sem_seek, True),
    ("SX-011", _check_sx011_x3_f3_consulta_inexistente, True),
    ("MOD-003", _check_mod003_static_funcs_to_class, False),
    ("PERF-006", _check_perf006_where_orderby_no_index, True),
]


def lint_cross_file(
    conn: sqlite3.Connection,
    *,
    rules: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Aplica regras cross-file. Retorna lista ordenada.

    v0.3.26: regras com `requires_sx=True` (SX-001..SX-011) skipam quando
    migration 002 nao foi aplicada / `ingest-sx` nao rodou. Regras
    `requires_sx=False` (MOD-003+) rodam sempre, usam so `fonte_chunks`.

    Args:
        conn: conexão SQLite.
        rules: filtro opcional (lista de regra_ids). ``None`` = todas.
    """
    sx_available = _sx_present(conn)
    findings: list[dict[str, Any]] = []
    selected = set(rules) if rules else None
    for regra_id, check_fn, requires_sx in _CROSS_FILE_RULES:
        if selected is not None and regra_id not in selected:
            continue
        if requires_sx and not sx_available:
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
    anteriores antes de inserir os novos.

    v0.3.28 (#1 Audit V4 CRITICO): deriva lista de regra_ids do _CROSS_FILE_RULES
    em vez de hardcode `LIKE 'SX-%'`. Antes, MOD-003 e PERF-006 (cross-file
    desde v0.3.26/27) acumulavam findings duplicados a cada execucao.
    """
    cross_ids = [regra_id for regra_id, _, _ in _CROSS_FILE_RULES]
    placeholders = ",".join("?" * len(cross_ids))
    conn.execute(
        f"DELETE FROM lint_findings WHERE regra_id IN ({placeholders})",
        cross_ids,
    )
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
