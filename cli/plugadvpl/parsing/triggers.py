"""Universo 3 / Feature A — execution triggers.

Detecta os 4 mecanismos canônicos TOTVS de "execução não-direta":

- ``workflow`` — `TWFProcess` / `MsWorkflow` / `WFPrepEnv` (callbacks de aprovação)
- ``schedule`` — `Static Function SchedDef()` (configurador SIGACFG)
- ``job_standalone`` — `Main Function` + `RpcSetEnv` (daemon ONSTART)
- ``mail_send`` — `MailAuto` / `SEND MAIL` UDC / `TMailManager`

Spec completo: ``docs/universo3/A-workflow-schedule.md``.

Uso:

.. code-block:: python

    triggers = extract_execution_triggers(content)
    # → list[dict] com kind/target/metadata/linha/snippet
"""
from __future__ import annotations

import json
import re
from typing import Any

from plugadvpl.parsing.stripper import strip_advpl

# --- Workflow ---------------------------------------------------------------

# Instanciação canônica TWFProcess (moderna).
_WF_TWFPROCESS_RE = re.compile(
    r"\bTWFProcess\s*\(\s*\)\s*:\s*New\s*\(\s*"
    r"['\"]([^'\"]*)['\"]"  # process id (opcional)
    r"(?:\s*,\s*['\"]([^'\"]*)['\"])?",  # description
    re.IGNORECASE,
)
# Legado.
_WF_MSWORKFLOW_RE = re.compile(r"\bMsWorkflow\s*\(", re.IGNORECASE)
# Helper de prep ambiente (callbacks).
_WF_PREPENV_RE = re.compile(r"\bWFPrepEnv\s*\(", re.IGNORECASE)
# Callbacks: oWF:bReturn := {|x| Foo(x)} ou :bTimeOut := {|x| Bar(x)}.
_WF_CALLBACK_RE = re.compile(
    r":\s*(b(?:Return|TimeOut))\s*:=\s*\{\s*\|[^|]*\|\s*([A-Za-z_]\w*)\s*\(",
    re.IGNORECASE,
)
# Template HTML em :NewTask("..", "/workflow/x.htm")
_WF_NEWTASK_RE = re.compile(
    r":\s*NewTask\s*\(\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]",
    re.IGNORECASE,
)
# To/Subject — propriedade simples.
_WF_TO_RE = re.compile(r":\s*cTo\s*:=\s*['\"]([^'\"]*)['\"]", re.IGNORECASE)
_WF_SUBJ_RE = re.compile(r":\s*cSubject\s*:=\s*['\"]([^'\"]*)['\"]", re.IGNORECASE)


# --- Schedule ----------------------------------------------------------------

# Static Function SchedDef() — exato.
_SCHED_DEF_RE = re.compile(
    r"^[ \t]*Static\s+Function\s+SchedDef\s*\(\s*\)",
    re.IGNORECASE | re.MULTILINE,
)
# Heurística pra extrair array de retorno: aRet := { "P", "GRP01", "SF2", {1,2}, "Titulo" }
# Capturamos o RHS do primeiro `:=` ou `Return` dentro do scope SchedDef.
_SCHED_RETURN_RE = re.compile(
    r"\{\s*['\"]([PR])['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]"
    r"\s*,\s*\{([^}]*)\}\s*,\s*['\"]([^'\"]*)['\"]\s*\}",
    re.IGNORECASE,
)


# --- Job standalone ---------------------------------------------------------

# Main Function — entry point sem licença.
_JOB_MAIN_RE = re.compile(
    r"^[ \t]*Main\s+Function\s+(\w+)\s*\(",
    re.IGNORECASE | re.MULTILINE,
)
# RpcSetEnv — só localiza o início; args extraídos via _parse_rpcsetenv_args
# (v0.4.3 C3: regex única era frágil quando os 6 args vinham literais consecutivos).
_JOB_RPCSETENV_RE = re.compile(r"\bRpcSetEnv\s*\(", re.IGNORECASE)
# RpcSetType(3) — sem licença.
_JOB_RPCSETTYPE_RE = re.compile(r"\bRpcSetType\s*\(\s*3\s*\)", re.IGNORECASE)
# Sleep(N*1000) ou Sleep(N) em ms — extrai segundos.
_JOB_SLEEP_RE = re.compile(r"\bSleep\s*\(\s*(\d+)(?:\s*\*\s*(\d+))?\s*\)", re.IGNORECASE)
# Stop flag tipica: File("\stop_*.flg") ou File("...") em condicao.
_JOB_STOP_FLAG_RE = re.compile(
    r"\bFile\s*\(\s*['\"]([^'\"]*)['\"]\s*\)", re.IGNORECASE,
)


# --- Mail send --------------------------------------------------------------

# Variantes de envio.
_MAIL_AUTO_RE = re.compile(r"\bMailAuto\s*\(", re.IGNORECASE)
_MAIL_UDC_SEND_RE = re.compile(r"^\s*SEND\s+MAIL\b", re.IGNORECASE | re.MULTILINE)
_MAIL_UDC_CONNECT_RE = re.compile(r"^\s*CONNECT\s+SMTP\b", re.IGNORECASE | re.MULTILINE)
_MAIL_TMAILMANAGER_RE = re.compile(r"\bTMailManager\s*\(", re.IGNORECASE)
_MAIL_TMAILMESSAGE_RE = re.compile(r"\bTMailMessage\s*\(", re.IGNORECASE)
_MAIL_SEND_METHOD_RE = re.compile(r":\s*Send\s*\(", re.IGNORECASE)
# v0.4.3 (I1): TMailManager:SendMail/SmtpConnect — variantes legadas (sem TMailMessage).
_MAIL_TMM_SEND_METHODS_RE = re.compile(
    r":\s*(?:SendMail|SmtpConnect|Send)\s*\(", re.IGNORECASE,
)
# Anexo: ATTACHMENT (UDC) ou :AttachFile(
_MAIL_ATTACH_RE = re.compile(
    r"\bATTACHMENT\b|:\s*AttachFile\s*\(", re.IGNORECASE,
)
# MV_REL* params (sinal de envio real, não mock).
_MAIL_MV_REL_RE = re.compile(r"\bMV_REL[A-Z]+\b", re.IGNORECASE)


# --- Helper interno ---------------------------------------------------------


def _line_at(content: str, offset: int) -> int:
    """1-indexed line number do offset."""
    return content.count("\n", 0, offset) + 1


def _snippet_at(content: str, linha: int, max_len: int = 200) -> str:
    """Linha completa em torno de ``linha``."""
    lines = content.splitlines()
    if 1 <= linha <= len(lines):
        s = lines[linha - 1].strip()
        return s[:max_len]
    return ""


# --- Helpers ----------------------------------------------------------------


def _split_top_level_commas(s: str) -> list[str]:
    """Split por vírgulas top-level (ignora dentro de (), {}, []).

    Usado pra extrair args de chamadas com aridade variável onde regex única
    fica frágil (vide RpcSetEnv com 6 literais consecutivos — C3 v0.4.3).
    Caller espera passar conteúdo já stripado (strings → spaces).
    """
    parts: list[str] = []
    depth_paren = depth_brace = depth_bracket = 0
    last = 0
    for i, c in enumerate(s):
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        elif c == "{":
            depth_brace += 1
        elif c == "}":
            depth_brace -= 1
        elif c == "[":
            depth_bracket += 1
        elif c == "]":
            depth_bracket -= 1
        elif (
            c == ","
            and depth_paren == 0
            and depth_brace == 0
            and depth_bracket == 0
        ):
            parts.append(s[last:i])
            last = i + 1
    parts.append(s[last:])
    return parts


def _find_balanced_paren(s: str, open_idx: int) -> int:
    """Dado idx de `(`, retorna idx do `)` casado. -1 se não casar."""
    depth = 0
    for i in range(open_idx, len(s)):
        c = s[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _parse_rpcsetenv_args(content: str, original: str, open_paren_offset: int) -> dict[str, str]:
    """Extrai (empresa, filial, modulo) de uma chamada RpcSetEnv pelos args
    posicionais. v0.4.3 (C3): substitui regex frágil que falhava com 6 args
    literais consecutivos.

    Args:
        content: source stripado (strings → spaces) onde o match foi encontrado.
        original: source original (não usado aqui — kept simples).
        open_paren_offset: índice do `(` em ``content``.
    """
    close = _find_balanced_paren(content, open_paren_offset)
    if close == -1:
        return {"empresa": "", "filial": "", "modulo": ""}
    args = _split_top_level_commas(content[open_paren_offset + 1 : close])

    def _arg(idx: int) -> str:
        if idx >= len(args):
            return ""
        token = args[idx].strip()
        # Remove aspas se literal; caso contrário devolve identificador (variável).
        if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
            return token[1:-1]
        return token

    return {
        "empresa": _arg(0),
        "filial": _arg(1),
        "modulo": _arg(4),  # 5º arg (0-indexed)
    }


# --- Detectores -------------------------------------------------------------


def _detect_workflow(content: str, stripped: str) -> list[dict[str, Any]]:
    """Detecta `TWFProcess`, `MsWorkflow`, `WFPrepEnv` + extrai metadata."""
    out: list[dict[str, Any]] = []
    # TWFProcess (moderno) — emite 1 trigger por chamada com process_id.
    # v0.4.3 (C1): coleta TODAS as posições primeiro pra calcular scope_end como
    # próxima instanciação (vs janela fixa de 5000 chars que misturava callbacks
    # entre TWFProcess vizinhos no mesmo fonte).
    twfprocess_matches = list(_WF_TWFPROCESS_RE.finditer(stripped))
    for i, m in enumerate(twfprocess_matches):
        process_id = m.group(1) or ""
        description = m.group(2) or ""
        linha = _line_at(stripped, m.start())
        scope_start = m.start()
        if i + 1 < len(twfprocess_matches):
            # Cap pelo próximo TWFProcess (preserva isolamento entre workflows).
            scope_end = twfprocess_matches[i + 1].start()
        else:
            # Último — vai até EOF (mas com cap defensivo de 5000 chars).
            scope_end = min(len(stripped), scope_start + 5000)
        scope = stripped[scope_start:scope_end]
        callbacks: dict[str, str] = {}
        for cm in _WF_CALLBACK_RE.finditer(scope):
            prop_name = cm.group(1).lower()  # bReturn / btimeout
            callback_fn = cm.group(2)
            if prop_name == "breturn":
                callbacks["return_callback"] = callback_fn
            elif prop_name == "btimeout":
                callbacks["timeout_callback"] = callback_fn
        # Template HTML.
        template = ""
        nm = _WF_NEWTASK_RE.search(scope)
        if nm:
            template = nm.group(2)
        # To / Subject.
        to_m = _WF_TO_RE.search(scope)
        subj_m = _WF_SUBJ_RE.search(scope)
        meta = {
            "process_id": process_id,
            "description": description,
            "template": template,
            "to": to_m.group(1) if to_m else "",
            "subject": subj_m.group(1) if subj_m else "",
            "is_legacy": False,
            **callbacks,
        }
        target = callbacks.get("return_callback") or process_id
        out.append({
            "kind": "workflow",
            "target": target,
            "linha": linha,
            "snippet": _snippet_at(content, linha),
            "metadata": meta,
        })
    # MsWorkflow legado — 1 trigger por chamada, metadata mais pobre.
    for m in _WF_MSWORKFLOW_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        out.append({
            "kind": "workflow",
            "target": "",
            "linha": linha,
            "snippet": _snippet_at(content, linha),
            "metadata": {"is_legacy": True},
        })
    # WFPrepEnv — geralmente em callback; emite trigger separado pra
    # mostrar "este fonte é executado em contexto de workflow callback".
    for m in _WF_PREPENV_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        out.append({
            "kind": "workflow",
            "target": "wf_callback",
            "linha": linha,
            "snippet": _snippet_at(content, linha),
            "metadata": {"is_callback_env": True},
        })
    return out


def _detect_schedule(content: str, stripped: str) -> list[dict[str, Any]]:
    """Detecta `Static Function SchedDef()` + extrai array de retorno."""
    out: list[dict[str, Any]] = []
    for m in _SCHED_DEF_RE.finditer(stripped):
        linha = _line_at(stripped, m.start())
        # Procurar array de retorno até próxima `Return` (ou 50 linhas).
        scope_start = m.start()
        scope_end = min(len(stripped), scope_start + 3000)
        scope = stripped[scope_start:scope_end]
        rm = _SCHED_RETURN_RE.search(scope)
        meta: dict[str, Any] = {
            "sched_type": "",
            "pergunte": "",
            "alias": "",
            "ordens": [],
            "titulo": "",
        }
        target = "SchedDef"
        if rm:
            meta["sched_type"] = rm.group(1).upper()
            meta["pergunte"] = rm.group(2)
            meta["alias"] = rm.group(3)
            ordens_raw = rm.group(4).strip()
            try:
                meta["ordens"] = [
                    int(x.strip()) for x in ordens_raw.split(",") if x.strip().isdigit()
                ]
            except (ValueError, AttributeError):
                meta["ordens"] = []
            meta["titulo"] = rm.group(5)
            target = meta["pergunte"] or "SchedDef"
        out.append({
            "kind": "schedule",
            "target": target,
            "linha": linha,
            "snippet": _snippet_at(content, linha),
            "metadata": meta,
        })
    return out


def _detect_job_standalone(content: str, stripped: str) -> list[dict[str, Any]]:
    """Detecta `Main Function` + `RpcSetEnv`/`RpcSetType(3)` no body.

    Heurística: Main Function só vira trigger se o body contém RpcSetEnv OU
    RpcSetType(3) — caso contrário pode ser entry point não-job (raro mas
    existe em integrações antigas).
    """
    out: list[dict[str, Any]] = []
    main_matches = list(_JOB_MAIN_RE.finditer(stripped))
    for i, m in enumerate(main_matches):
        main_name = m.group(1)
        linha = _line_at(stripped, m.start())
        # Body = do match até próxima Main Function (ou EOF).
        body_start = m.start()
        body_end = main_matches[i + 1].start() if i + 1 < len(main_matches) else len(stripped)
        body = stripped[body_start:body_end]
        # Exigir RpcSetEnv ou RpcSetType(3) pra qualificar como job.
        rpc_match = _JOB_RPCSETENV_RE.search(body)
        no_license = bool(_JOB_RPCSETTYPE_RE.search(body))
        if not rpc_match and not no_license:
            continue
        empresa = filial = modulo = ""
        if rpc_match:
            # v0.4.3 (C3): args via paren-balanced split (regex única era frágil
            # quando 6 args vinham literais consecutivos sem vírgulas vazias).
            # rpc_match.end() é offset em `body` (slice de `stripped`).
            parsed_args = _parse_rpcsetenv_args(body, body, rpc_match.end() - 1)
            empresa = parsed_args["empresa"]
            filial = parsed_args["filial"]
            modulo = parsed_args["modulo"]
        # Sleep — extrai intervalo em segundos (assume Sleep(N*1000) = N segundos).
        sleep_seconds = 0
        sm = _JOB_SLEEP_RE.search(body)
        if sm:
            n = int(sm.group(1))
            mult = int(sm.group(2)) if sm.group(2) else 1
            total_ms = n * mult
            sleep_seconds = total_ms // 1000 if total_ms >= 1000 else total_ms
        # Stop flag.
        stop_flag = ""
        sf = _JOB_STOP_FLAG_RE.search(body)
        if sf:
            stop_flag = sf.group(1)
        meta = {
            "main_name": main_name,
            "empresa": empresa,
            "filial": filial,
            "modulo": modulo,
            "sleep_seconds": sleep_seconds,
            "stop_flag": stop_flag,
            "no_license": no_license,
        }
        out.append({
            "kind": "job_standalone",
            "target": main_name,
            "linha": linha,
            "snippet": _snippet_at(content, linha),
            "metadata": meta,
        })
    return out


def _detect_mail_send(content: str, stripped: str) -> list[dict[str, Any]]:
    """Detecta envio de email em 3 variantes: MailAuto, UDC, TMailManager.

    Emite 1 trigger por OCORRÊNCIA — fontes com várias chamadas geram
    múltiplos rows (ex: helper que envia + chamada de retry).
    """
    out: list[dict[str, Any]] = []
    has_attach = bool(_MAIL_ATTACH_RE.search(stripped))
    uses_mv_rel = bool(_MAIL_MV_REL_RE.search(stripped))
    seen_lines: set[int] = set()

    def _emit(start: int, variant: str) -> None:
        linha = _line_at(stripped, start)
        if linha in seen_lines:
            return
        seen_lines.add(linha)
        out.append({
            "kind": "mail_send",
            "target": variant,
            "linha": linha,
            "snippet": _snippet_at(content, linha),
            "metadata": {
                "variant": variant,
                "has_attachment": has_attach,
                "uses_mv_rel": uses_mv_rel,
            },
        })

    # MailAuto — disparo direto.
    for m in _MAIL_AUTO_RE.finditer(stripped):
        _emit(m.start(), "MailAuto")
    # SEND MAIL — UDC (CONNECT SMTP é prep).
    for m in _MAIL_UDC_SEND_RE.finditer(stripped):
        _emit(m.start(), "UDC")
    # TMailMessage:Send (preferido — TMailManager sozinho é só conexão).
    for m in _MAIL_TMAILMESSAGE_RE.finditer(stripped):
        _emit(m.start(), "TMailManager")
    # v0.4.3 (I1): TMailManager solo (sem TMailMessage) — legacy. Detecta se há
    # TMailManager + chamada de envio (`:SendMail`/`:Send`) no mesmo fonte e
    # ainda nao temos trigger no fonte.
    if not any(t["target"] == "TMailManager" for t in out):
        tmm_match = _MAIL_TMAILMANAGER_RE.search(stripped)
        send_match = _MAIL_TMM_SEND_METHODS_RE.search(stripped)
        if tmm_match and send_match:
            _emit(tmm_match.start(), "TMailManager")
    return out


# --- Função pública --------------------------------------------------------


def extract_execution_triggers(content: str) -> list[dict[str, Any]]:
    """Extrai todos os execution triggers do conteúdo do fonte.

    Roda os 4 detectores e retorna lista combinada. Cada item:

    .. code-block:: python

        {
            "kind": "workflow|schedule|job_standalone|mail_send",
            "target": "<callback name | Main name | pergunte | variant>",
            "linha": int,
            "snippet": "<linha completa do match>",
            "metadata": dict,  # campos por kind, vide spec
        }

    Strings preservadas pra extrair literais (process_id, paths, etc);
    comentários removidos (não disparar em código comentado).
    """
    stripped = strip_advpl(content, strip_strings=False)
    triggers: list[dict[str, Any]] = []
    triggers.extend(_detect_workflow(content, stripped))
    triggers.extend(_detect_schedule(content, stripped))
    triggers.extend(_detect_job_standalone(content, stripped))
    triggers.extend(_detect_mail_send(content, stripped))
    triggers.sort(key=lambda t: (t["linha"], t["kind"]))
    return triggers


def serialize_metadata(metadata: dict[str, Any]) -> str:
    """Serializa metadata pra TEXT no DB (JSON minified)."""
    return json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))


def parse_metadata(metadata_json: str) -> dict[str, Any]:
    """Deserializa metadata do DB (defensivo: retorna {} se inválido)."""
    if not metadata_json:
        return {}
    try:
        return json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}
