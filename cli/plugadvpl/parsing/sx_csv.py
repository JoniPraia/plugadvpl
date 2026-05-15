"""SX CSV parser — porta do parser interno do autor (parser_sx.py, 872 linhas, MIT).

Origem: projeto Protheus interno (`backend/services/parser_sx.py`) do mesmo autor
(JoniPraia). Copiado e adaptado para plugadvpl: removidos parsers ``parse_padrao_*``
(plugin só ingere CSVs custom da rotina de exportação), ``parse_jobs``, ``parse_schedules``,
``parse_mpmenu`` (escopo de v0.4+). Mantida toda lógica de detecção de encoding,
delimitador, conversão XLSX disfarçado, sanitização de surrogates Unicode.

Cada função ``parse_sxN`` recebe ``Path`` para o CSV e retorna ``list[dict[str, Any]]``
com chaves alinhadas à migration 002_universo2_sx.sql.
"""
from __future__ import annotations

import csv
import re
import sys
from typing import TYPE_CHECKING, Any

import chardet

if TYPE_CHECKING:
    from pathlib import Path

# CSVs SX podem ter campos muito grandes (validações longas, conteúdos memo).
csv.field_size_limit(10_000_000)  # 10MB

# Magic number para detectar XLSX disfarçado de .csv (header ZIP).
_XLSX_MAGIC = b"PK\x03\x04"

# Bytes lidos para sniff de encoding (chardet em chunk pequeno é tão preciso quanto
# em arquivo inteiro e infinitamente mais rápido em CSVs de centenas de MB).
_ENCODING_SNIFF_BYTES = 4096


def _detect_encoding(file_path: Path) -> str:
    """Detecta encoding do CSV via BOM + chardet (sniff dos primeiros 4KB).

    Retorna ``utf-8-sig`` se houver BOM UTF-8, caso contrário o resultado do
    chardet (default ``cp1252`` se chardet não decidir — encoding canonical
    Protheus para exports Configurador → Misc → Exportar Dicionário).
    """
    raw = file_path.read_bytes()[:_ENCODING_SNIFF_BYTES]
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    result = chardet.detect(raw)
    detected: str | None = result.get("encoding")
    return detected or "cp1252"


def _detect_delimiter(file_path: Path, encoding: str) -> str:
    """Sniff do delimitador via primeira linha do CSV.

    SX exports da rotina canonical usam vírgula. Configurador opcionalmente
    aceita ponto-e-vírgula em locales europeus — detectamos para cobertura.
    """
    with file_path.open(encoding=encoding, errors="replace") as f:
        first_line = f.readline()
    if ";" in first_line:
        return ";"
    return ","


def _is_custom_table(codigo: str) -> bool:
    """Heurística para detectar tabela custom Protheus (via padrões de nomenclatura).

    - ``SZ?`` (SZA, SZ1, ...): convenção tradicional para custom.
    - ``Q[A-Z][0-9A-Z]``: outra convenção para custom (TOTVS deixa o range Q* livre).
    - ``Z[0-9A-Z]+``: custom moderno (Z1, ZA, ZA1, ...).
    """
    if re.match(r"^SZ[0-9A-Z]$", codigo):
        return True
    if re.match(r"^Q[A-Z][0-9A-Z]$", codigo):
        return True
    return bool(re.match(r"^Z[0-9A-Z][0-9A-Z]?$", codigo))


_FIELD_PARTS_MIN = 2  # campo segue padrão TABELA_NOME (split em '_' produz >=2)


def _is_custom_field(campo: str) -> bool:
    """Detecta campo custom: 2ª parte (depois de ``_``) começa com ``X`` (ex: ``A1_XCUST``)."""
    parts = campo.split("_")
    return len(parts) >= _FIELD_PARTS_MIN and parts[1].startswith("X")


def _sanitize_text(text: str) -> str:
    """Remove surrogates Unicode (U+D800..U+DFFF) que SQLite não consegue gravar.

    Encoding round-trip com errors=replace garante que strings vindas de CSVs
    com bytes corrompidos (ex: cp1252 mal-decodificado) não quebrem ``executemany``.
    """
    return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def _safe_int(value: str) -> int:
    """Conversão tolerante string → int (lida com aspas, espaços, vazio)."""
    try:
        return int(value.strip().strip('"') or 0)
    except (ValueError, AttributeError):
        return 0


def _is_xlsx_disguised(file_path: Path) -> bool:
    """Detecta se arquivo ``.csv`` é na verdade um ZIP/XLSX (caso comum em exports manuais)."""
    try:
        with file_path.open("rb") as f:
            magic = f.read(4)
    except OSError:
        return False
    return magic == _XLSX_MAGIC


def _convert_xlsx_to_csv(file_path: Path) -> Path:
    """Converte XLSX disfarçado de CSV para CSV real (in-place, com backup ``.xlsx.bak``).

    Falha silenciosa se ``openpyxl`` não estiver instalado — retorna o path original
    e o caller terá que lidar (CSV reader vai falhar com erro de encoding).
    """
    xlsx_path = file_path.with_suffix(".xlsx.bak")
    try:
        import openpyxl  # type: ignore[import-untyped]  # noqa: PLC0415 — optional dep, only load if needed
    except ImportError:
        return file_path
    try:
        file_path.rename(xlsx_path)
        wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
            for row in rows:
                writer.writerow(["" if c is None else str(c) for c in row])
    except Exception:  # boundary: restore backup on ANY failure (xlsx parse issues)
        if xlsx_path.exists() and not file_path.exists():
            xlsx_path.rename(file_path)
    return file_path


def _read_csv(file_path: Path) -> list[dict[str, str]]:
    """Lê CSV inteiro em lista de dicts {coluna: valor}.

    Pipeline: detect-xlsx → convert → detect-encoding → detect-delimiter → DictReader.
    Sanitiza valores via :func:`_sanitize_text` para garantir compat com SQLite.
    """
    if _is_xlsx_disguised(file_path):
        file_path = _convert_xlsx_to_csv(file_path)
    encoding = _detect_encoding(file_path)
    delimiter = _detect_delimiter(file_path, encoding)
    rows: list[dict[str, str]] = []
    with file_path.open(encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            clean: dict[str, str] = {}
            for k, v in row.items():
                if k is None:
                    continue
                if isinstance(v, str):
                    clean[k] = _sanitize_text(v)
                else:
                    clean[k] = ""
            rows.append(clean)
    return rows


def _row_is_deleted(row: dict[str, str]) -> bool:
    """Filtra rows logicamente deletados (D_E_L_E_T_ == '*')."""
    deleted = row.get("D_E_L_E_T_", "").strip().strip('"').strip()
    return deleted == "*"


# ---------------------------------------------------------------------------
# Parsers de cada tabela SX. Cada um retorna list[dict] alinhado à migration 002.
# ---------------------------------------------------------------------------


def parse_sx2(file_path: Path) -> list[dict[str, Any]]:
    """SX2 — Tabelas (X2_CHAVE, X2_NOME, X2_MODO)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        codigo = row.get("X2_CHAVE", "").strip()
        if not codigo:
            continue
        result.append(
            {
                "codigo": codigo,
                "nome": row.get("X2_NOME", "").strip(),
                "modo": row.get("X2_MODO", "").strip(),
                "custom": 1 if _is_custom_table(codigo) else 0,
            }
        )
    return result


def parse_sx3(file_path: Path) -> list[dict[str, Any]]:
    """SX3 — Campos (full metadata: F3, CBOX, validações, owner)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        campo = row.get("X3_CAMPO", "").strip()
        if not campo:
            continue
        # X3_OBRIGAT é uma máscara de contexto: 'x' / 'xxxx' = obrigatório,
        # '' = opcional. Legacy aceita 'S', 'SIM', '1', '.T.'.
        obrig_raw = row.get("X3_OBRIGAT", "").strip().strip('"').strip()
        obrigatorio = (
            1
            if obrig_raw.lower().startswith("x")
            or obrig_raw.upper() in ("S", "SIM", "1", ".T.")
            else 0
        )
        proprietario = row.get("X3_PROPRI", "").strip().strip('"')
        is_custom = 1 if _is_custom_field(campo) else 0
        # Se X3_PROPRI explicitamente != "S" (standard), marca como custom.
        if proprietario and proprietario != "S":
            is_custom = 1
        result.append(
            {
                "tabela": row.get("X3_ARQUIVO", "").strip(),
                "campo": campo,
                "tipo": row.get("X3_TIPO", "").strip(),
                "tamanho": _safe_int(row.get("X3_TAMANHO", "0")),
                "decimal": _safe_int(row.get("X3_DECIMAL", "0")),
                "titulo": row.get("X3_TITULO", "").strip(),
                "descricao": row.get("X3_DESCRIC", "").strip(),
                "validacao": row.get("X3_VALID", "").strip(),
                # v0.3.28 (Audit V4 #5): X3_INIT eh o initializer canonico TOTVS
                # (valor padrao do campo). X3_RELACAO eh outra coisa (autofill por
                # expressao/relacao). Lemos X3_INIT prioritariamente, fallback pra
                # X3_RELACAO so pra suportar dumps legados/fixtures antigas.
                "inicializador": (
                    row.get("X3_INIT", "").strip()
                    or row.get("X3_RELACAO", "").strip()
                ),
                "obrigatorio": obrigatorio,
                "custom": is_custom,
                "f3": row.get("X3_F3", "").strip(),
                "cbox": row.get("X3_CBOX", "").strip(),
                "vlduser": row.get("X3_VLDUSER", "").strip(),
                "when_expr": row.get("X3_WHEN", "").strip(),
                "proprietario": proprietario,
                "browse": row.get("X3_BROWSE", "").strip(),
                "trigger_flag": row.get("X3_TRIGGER", "").strip(),
                "visual": row.get("X3_VISUAL", "").strip(),
                "context": row.get("X3_CONTEXT", "").strip(),
                "folder": row.get("X3_FOLDER", "").strip(),
                "grpsxg": row.get("X3_GRPSXG", "").strip(),
            }
        )
    return result


def parse_six(file_path: Path) -> list[dict[str, Any]]:
    """SIX — Índices. ATENÇÃO: colunas SEM prefixo (INDICE, ORDEM, CHAVE...)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        tabela = row.get("INDICE", "").strip()
        ordem = row.get("ORDEM", "").strip()
        if not tabela or not ordem:
            continue
        proprietario = row.get("PROPRI", "").strip()
        result.append(
            {
                "tabela": tabela,
                "ordem": ordem,
                "chave": row.get("CHAVE", "").strip(),
                "descricao": row.get("DESCRICAO", "").strip(),
                "proprietario": proprietario,
                "f3": row.get("F3", "").strip(),
                "nickname": row.get("NICKNAME", "").strip(),
                "showpesq": row.get("SHOWPESQ", "").strip(),
                "custom": 1 if proprietario and proprietario != "S" else 0,
            }
        )
    return result


def parse_sx7(file_path: Path) -> list[dict[str, Any]]:
    """SX7 — Gatilhos. Inclui condition (X7_CONDIC) e seek metadata."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        campo_origem = row.get("X7_CAMPO", "").strip()
        if not campo_origem:
            continue
        campo_destino = row.get("X7_CDOMIN", "").strip()
        proprietario = row.get("X7_PROPRI", "").strip()
        is_custom = 1 if _is_custom_field(campo_destino) else 0
        if proprietario and proprietario != "S":
            is_custom = 1
        result.append(
            {
                "campo_origem": campo_origem,
                "sequencia": row.get("X7_SEQUENC", "").strip(),
                "campo_destino": campo_destino,
                "regra": row.get("X7_REGRA", "").strip(),
                "tipo": row.get("X7_TIPO", "").strip(),
                "tabela": row.get("X7_ALIAS", "").strip()
                or row.get("X7_ARQUIVO", "").strip(),
                "condicao": row.get("X7_CONDIC", "").strip(),
                "proprietario": proprietario,
                "seek": row.get("X7_SEEK", "").strip(),
                "alias": row.get("X7_ALIAS", "").strip(),
                "ordem": row.get("X7_ORDEM", "").strip(),
                "chave": row.get("X7_CHAVE", "").strip(),
                "custom": is_custom,
            }
        )
    return result


def parse_sx1(file_path: Path) -> list[dict[str, Any]]:
    """SX1 — Perguntas (groups + individual questions in MV_PARxx scheme)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        grupo = row.get("X1_GRUPO", "").strip()
        ordem = row.get("X1_ORDEM", "").strip()
        if not grupo or not ordem:
            continue
        result.append(
            {
                "grupo": grupo,
                "ordem": ordem,
                "pergunta": row.get("X1_PERGUNT", "").strip(),
                "variavel": row.get("X1_VARIAVL", "").strip(),
                "tipo": row.get("X1_TIPO", "").strip(),
                "tamanho": _safe_int(row.get("X1_TAMANHO", "0")),
                "decimal": _safe_int(row.get("X1_DECIMAL", "0")),
                "f3": row.get("X1_F3", "").strip(),
                "validacao": row.get("X1_VALID", "").strip(),
                "conteudo_padrao": row.get("X1_DEF01", "").strip(),
            }
        )
    return result


def parse_sx5(file_path: Path) -> list[dict[str, Any]]:
    """SX5 — Tabelas genéricas (códigos auxiliares: estado civil, tipo NF, ...)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        tabela = row.get("X5_TABELA", "").strip()
        chave = row.get("X5_CHAVE", "").strip()
        if not tabela or not chave:
            continue
        result.append(
            {
                "filial": row.get("X5_FILIAL", "").strip(),
                "tabela": tabela,
                "chave": chave,
                "descricao": row.get("X5_DESCRI", "").strip(),
                "custom": 1 if tabela.startswith(("Z", "X")) else 0,
            }
        )
    return result


def parse_sx6(file_path: Path) -> list[dict[str, Any]]:
    """SX6 — Parâmetros MV_*. Inclui validacao e init (cada vez mais comuns em ERP moderno)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        variavel = row.get("X6_VAR", "").strip()
        if not variavel:
            continue
        descricao = (
            row.get("X6_DESCRIC", "").strip() + " " + row.get("X6_DESC1", "").strip()
        ).strip()
        proprietario = row.get("X6_PROPRI", "").strip()
        result.append(
            {
                "filial": row.get("X6_FIL", "").strip(),
                "variavel": variavel,
                "tipo": row.get("X6_TIPO", "").strip(),
                "descricao": descricao,
                "conteudo": row.get("X6_CONTEUD", "").strip(),
                "proprietario": proprietario,
                "custom": 1 if proprietario != "S" else 0,
                "validacao": row.get("X6_VALID", "").strip(),
                "init": row.get("X6_INIT", "").strip(),
            }
        )
    return result


def parse_sx9(file_path: Path) -> list[dict[str, Any]]:
    """SX9 — Relacionamentos (FK lógicas entre tabelas)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        tabela_origem = row.get("X9_DOM", "").strip()
        tabela_destino = row.get("X9_CDOM", "").strip()
        if not tabela_origem or not tabela_destino:
            continue
        proprietario = row.get("X9_PROPRI", "").strip()
        result.append(
            {
                "tabela_origem": tabela_origem,
                "identificador": row.get("X9_IDENT", "").strip(),
                "tabela_destino": tabela_destino,
                "expressao_origem": row.get("X9_EXPDOM", "").strip(),
                "expressao_destino": row.get("X9_EXPCDOM", "").strip(),
                "proprietario": proprietario,
                "condicao_sql": row.get("X9_CONDSQL", "").strip(),
                "custom": 1 if proprietario != "S" else 0,
            }
        )
    return result


def parse_sxa(file_path: Path) -> list[dict[str, Any]]:
    """SXA — Pastas/folders (organização visual de campos no cadastro)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        alias = row.get("XA_ALIAS", "").strip()
        ordem = row.get("XA_ORDEM", "").strip()
        if not alias or not ordem:
            continue
        result.append(
            {
                "alias": alias,
                "ordem": ordem,
                "descricao": row.get("XA_DESCRIC", "").strip(),
                "proprietario": row.get("XA_PROPRI", "").strip(),
                "agrupamento": row.get("XA_AGRUP", "").strip(),
            }
        )
    return result


def parse_sxb(file_path: Path) -> list[dict[str, Any]]:
    """SXB — Consultas F3 (telas de pesquisa para campos)."""
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        alias = row.get("XB_ALIAS", "").strip()
        sequencia = row.get("XB_SEQ", "").strip()
        if not alias or not sequencia:
            continue
        result.append(
            {
                "alias": alias,
                "tipo": row.get("XB_TIPO", "").strip(),
                "sequencia": sequencia,
                "coluna": row.get("XB_COLUNA", "").strip(),
                "descricao": row.get("XB_DESCRI", "").strip(),
                "conteudo": row.get("XB_CONTEM", "").strip(),
            }
        )
    return result


def parse_sxg(file_path: Path) -> list[dict[str, Any]]:
    """SXG — Grupos de campos.

    Em alguns exports do Configurador, ``sxg.csv`` é na verdade um dump SX3
    alternativo (mesmo header X3_*). Nesse caso retornamos lista vazia — o
    ingest pula sem ruído. Apenas processa quando o header começa com ``XG_*``.
    """
    encoding = _detect_encoding(file_path)
    delimiter = _detect_delimiter(file_path, encoding)
    with file_path.open(encoding=encoding, errors="replace") as f:
        first_line = f.readline()
    first_col = first_line.split(delimiter)[0].strip().strip('"').strip()
    if not first_col.upper().startswith("XG_"):
        # v0.3.14: feedback de IA externa mostrou que o silent skip aqui virava
        # mistério "por que grupos_campo=0?". Logamos pra deixar claro o que aconteceu.
        upper = first_col.upper()
        suspect = "SX3" if upper.startswith("X3_") else f"header={first_col!r}"
        print(
            f"WARN: '{file_path.name}' nao parece SXG (1a coluna={first_col!r}, "
            f"esperado XG_*) — provavelmente dump {suspect} disfarcado. "
            "Tabela grupos_campo ficara vazia. Solicite o SXG correto ao DBA "
            "(deve ter colunas XG_GRUPO/XG_DESCRIC/XG_TAMANHO).",
            file=sys.stderr,
        )
        return []
    rows = _read_csv(file_path)
    result: list[dict[str, Any]] = []
    for row in rows:
        if _row_is_deleted(row):
            continue
        grupo = row.get("XG_GRUPO", "").strip()
        if not grupo:
            continue
        result.append(
            {
                "grupo": grupo,
                "descricao": row.get("XG_DESCRIC", "").strip(),
                "tamanho_max": _safe_int(row.get("XG_TAMMAX", "0")),
                "tamanho_min": _safe_int(row.get("XG_TAMMIN", "0")),
                "tamanho": _safe_int(row.get("XG_TAMANHO", "0")),
                "total_campos": 0,  # preenchido pelo ingest_sx via SQL
            }
        )
    return result
