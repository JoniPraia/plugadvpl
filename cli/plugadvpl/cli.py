"""CLI entry point — typer app expondo 13 subcomandos.

Subcomandos (além de ``version``):

1. ``init``     — cria DB + escreve fragment ``CLAUDE.md`` + atualiza ``.gitignore``.
2. ``ingest``   — wrapper de :func:`plugadvpl.ingest.ingest`.
3. ``reindex``  — re-ingest de UM arquivo (filtra ``scan_sources``).
4. ``status``   — meta + contadores.
5. ``find``     — busca composta: function -> file -> FTS.
6. ``callers``  — quem chama ``F``.
7. ``callees``  — quem ``F`` chama.
8. ``tables``   — quem usa a tabela ``T`` (read|write|reclock).
9. ``param``    — quem usa o parâmetro ``MV_*``.
10. ``arch``    — resumo arquitetural de UM fonte.
11. ``lint``    — lint findings (filtros opcionais).
12. ``doctor``  — diagnósticos do índice.
13. ``grep``    — FTS5 main / trigram-like / identifier.

Opções globais (callback ``main_callback``): ``--root``, ``--format``, ``--quiet``,
``--db``, ``--limit``, ``--offset``, ``--compact``, ``--no-next-steps``.
"""
from __future__ import annotations

import re
import sqlite3
import io
import sys
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from plugadvpl import __version__
from plugadvpl.db import (
    apply_migrations,
    close_db,
    init_meta,
    open_db,
    seed_lookups,
    set_meta,
)
from plugadvpl.ingest import PARSER_VERSION, _write_parsed
from plugadvpl.ingest import ingest as do_ingest
from plugadvpl.ingest_sx import ingest_sx as do_ingest_sx
from plugadvpl.output import render
from plugadvpl.parsing import lint as lint_module
from plugadvpl.parsing.parser import parse_source
from plugadvpl.query import (
    arch as q_arch,
)
from plugadvpl.query import (
    callees as q_callees,
)
from plugadvpl.query import (
    callers as q_callers,
)
from plugadvpl.query import (
    doctor_diagnostics,
    execauto_calls_query,
    execution_triggers_query,
    find_any,
    gatilho_query,
    grep_fts,
    impacto_query,
    lint_query,
    param_query,
    stale_files,
    sx_status,
    tables_query,
)
from plugadvpl.query import (
    status as q_status,
)
from plugadvpl.scan import scan_sources

if TYPE_CHECKING:
    from collections.abc import Callable


app = typer.Typer(
    name="plugadvpl",
    help="Indexa fontes ADVPL/TLPP em SQLite + FTS5 para análise por LLM.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


class OutputFormat(StrEnum):
    """Formatos de saída suportados pelo renderer global."""

    json = "json"
    table = "table"
    md = "md"


class GrepMode(StrEnum):
    """Modos do subcomando ``grep``."""

    fts = "fts"
    literal = "literal"
    identifier = "identifier"


class TableMode(StrEnum):
    """Modos do filtro ``--mode`` em ``tables``."""

    read = "read"
    write = "write"
    reclock = "reclock"


# ---------------------------------------------------------------------------
# Callback global — popula ctx.obj com flags compartilhadas.
# ---------------------------------------------------------------------------


def _version_callback(value: bool) -> None:
    """Eager callback de ``--version``/`-V`: imprime e sai antes de exigir subcomando."""
    if value:
        typer.echo(f"plugadvpl {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Mostra a versão do binário e sai.",
        ),
    ] = False,
    root: Annotated[
        Path,
        typer.Option("--root", "-r", help="Raiz do projeto cliente."),
    ] = Path(),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Formato de saída."),
    ] = OutputFormat.table,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suprime mensagens decorativas."),
    ] = False,
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Caminho explícito do DB (default: <root>/.plugadvpl/index.db)."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", help="Máximo de linhas por output. 0 = sem limite."),
    ] = 20,
    offset: Annotated[
        int,
        typer.Option("--offset", help="Pular N linhas antes do limit."),
    ] = 0,
    compact: Annotated[
        bool,
        typer.Option("--compact", help="Output compacto (sem indent JSON / linhas table)."),
    ] = False,
    no_next_steps: Annotated[
        bool,
        typer.Option("--no-next-steps", help="Desliga sugestões de próximo comando."),
    ] = False,
) -> None:
    """Opções globais aplicadas a todos os subcomandos via ``ctx.obj``."""
    ctx.ensure_object(dict)
    resolved_root = root.resolve()
    ctx.obj["root"] = resolved_root
    ctx.obj["format"] = format.value
    ctx.obj["quiet"] = quiet
    ctx.obj["db"] = db.resolve() if db else (resolved_root / ".plugadvpl" / "index.db")
    ctx.obj["limit"] = limit
    ctx.obj["offset"] = offset
    ctx.obj["compact"] = compact
    ctx.obj["next_steps_enabled"] = not no_next_steps


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _open_ro(db_path: Path) -> sqlite3.Connection:
    """Abre o DB em modo read-only (URI ``mode=ro``).

    Para subcomandos puramente de leitura (``find``, ``callers``, etc.), evita
    qualquer hot-write no índice. Se o arquivo não existir, mostra mensagem
    amigável e sai com código 2.
    """
    if not db_path.exists():
        typer.secho(
            f"Erro: índice não encontrado em {db_path}.\n"
            "Rode 'plugadvpl init' e 'plugadvpl ingest' primeiro.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)
    uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _render_from_ctx(
    ctx: typer.Context,
    rows: list[dict[str, object]],
    *,
    columns: list[str] | None = None,
    title: str | None = None,
    next_steps: list[str] | None = None,
) -> None:
    """Wrapper que injeta as flags globais (``format``/``limit``/...) no render."""
    obj = ctx.obj
    render(
        rows,
        format=obj["format"],
        columns=columns,
        title=None if obj["quiet"] else title,
        limit=obj["limit"],
        offset=obj["offset"],
        compact=obj["compact"],
        next_steps=next_steps if obj["next_steps_enabled"] else None,
    )


def _with_ro_db(
    ctx: typer.Context,
    fn: Callable[[sqlite3.Connection], list[dict[str, object]]],
) -> list[dict[str, object]]:
    """Boilerplate: abre RO, executa ``fn(conn)``, fecha. Retorna rows."""
    conn = _open_ro(ctx.obj["db"])
    try:
        return fn(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Imprime versão da CLI."""
    typer.echo(f"plugadvpl {__version__}")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

_CLAUDE_FRAGMENT_BEGIN = "<!-- BEGIN plugadvpl -->"
_CLAUDE_FRAGMENT_END = "<!-- END plugadvpl -->"
# v0.3.23 (#1 do QA round 3): marker de versão dentro do fragment.
# `_write_claude_md_fragment` substitui `__VERSION__` por `__version__` real
# na hora de gravar; `_check_fragment_staleness` (em status) le este marker
# pra detectar fragments gerados por versoes antigas e avisar o usuario.
_CLAUDE_FRAGMENT_VERSION_MARKER_RE = re.compile(
    r"<!--\s*plugadvpl-fragment-version:\s*([\d.+-]\S*)\s*-->"
)
_CLAUDE_FRAGMENT_BODY = """<!-- plugadvpl-fragment-version: __VERSION__ -->
## Plugadvpl — índice ADVPL local (LEIA ANTES de qualquer Read em .prw/.tlpp)

Este projeto possui um índice SQLite em `.plugadvpl/index.db` com metadados extraídos
de TODOS os fontes ADVPL/TLPP do projeto: funções, tabelas referenciadas (read/write/reclock),
campos, parâmetros MV_*, perguntas SX1, call graph (U_*, ExecBlock, MsExecAuto, FWLoadModel,
FWExecView, métodos), SQL embarcado, includes, capabilities (MVC/JOB/REST/PE/...) e lint findings.

### REGRA DURA — SEM EXCEÇÃO

**Antes de chamar `Read` em qualquer `.prw`/`.tlpp`/`.prx`, você DEVE rodar primeiro
um comando do plugadvpl** (via `Bash plugadvpl ...` ou `/plugadvpl:*` se houver slash).
Fontes Protheus têm tipicamente 1.000–10.000 linhas; lê-los inteiros queima contexto e
produz respostas vagas. O índice te dá o resumo em ~200 tokens em vez de 10.000.

Só leia o `.prw` cru depois de localizar a faixa de linhas exata via índice
(ex: `Read FATA050.prw` com offset/limit baseados em `linha_inicio`/`linha_fim` que
o `arch` retorna).

### Tabela de decisão — qual comando usar para qual pergunta

| Pergunta do usuário                                         | Rode PRIMEIRO                                  |
|-------------------------------------------------------------|------------------------------------------------|
| "explique o fonte X" / "o que faz Y"                        | `plugadvpl arch <arq>`                         |
| "onde está a função X?" / "tem um programa MGFTAC12, ..."   | `plugadvpl find <nome>`                        |
| "quais fontes chamam X?" / "quem usa X?"                    | `plugadvpl callers <funcao>`                   |
| "o que X chama por dentro?" / "quais dependências de X?"    | `plugadvpl callees <funcao>`                   |
| "quem mexe na tabela SA1?" / "quem grava em SC5?"           | `plugadvpl tables SA1` (ou `--write/--reclock`)|
| "quais parâmetros MV_* X usa?" / "onde MV_LOCALIZA é usado?"| `plugadvpl param MV_LOCALIZA`                  |
| "achar fonte com 'RecLock' / 'BeginSql' / etc"              | `plugadvpl grep <termo>` (modos `-m fts\\|literal\\|identifier`)      |
| "tem problemas / boas práticas neste fonte?"                | `plugadvpl lint [arq] [--severity critical]`   |
| "essa função é nativa do Protheus?"                         | `plugadvpl native <nome>`                      |
| "posso usar StaticCall / função X?"                         | `plugadvpl restricted <nome>`                  |

### Workflow padrão para "explique o programa X"

Quando o usuário pedir para explicar/analisar um programa (ex: "tenho um programa MGFTAC12,
quais fontes chama, parâmetros, etc"):

1. `plugadvpl find MGFTAC12` — descobre em qual arquivo está
2. `plugadvpl arch <arquivo encontrado>` — visão geral (capabilities, funções, tabelas, includes)
3. `plugadvpl callees MGFTAC12` — o que ele chama (call graph saindo)
4. `plugadvpl callers MGFTAC12` — quem chama ele (call graph entrando)
5. `plugadvpl tables <tabela_principal>` — para cada tabela relevante, ver outros que tocam
6. `plugadvpl param <MV_X>` — para cada MV_* relevante, ver o uso global
7. **Só depois**, se ainda restar dúvida, ler com `Read <arquivo>` usando os ranges de linha
   identificados (ex: `linha_inicio`/`linha_fim` de uma função específica do `arch`).

Sintetize o que encontrar nos passos 1–6 num parágrafo: o que faz + dependências + impacto.
**NUNCA pule direto para `Read` do `.prw` inteiro.**

### Como rodar

- **Sempre disponível** (CLI Python, basta `uv` instalado):
  `Bash -> plugadvpl <subcomando> ...` ou `uvx plugadvpl@<versão> <subcomando> ...`
- **Se o plugin Claude Code estiver instalado** (recomendado para UX):
  use os slash commands `/plugadvpl:arch`, `/plugadvpl:find`, etc.

Para ver versão / status do índice: `plugadvpl status`. Para ver todos os comandos:
`plugadvpl --help`.

### Output format — IMPORTANTE para agentes IA

A flag global `--format` aceita 3 valores e **vem ANTES do subcomando** (é do callback):

- `--format table` (default) — Rich em **stderr**, **trunca** colunas em terminais
  estreitos (você vê `ar...`, `ti...`, `ca...`). OK para humano interativo.
- `--format md` — Markdown em **stdout**, **sem truncamento**. **Recomendado para Claude/agentes IA**: limpo, parseável visualmente, vai pro stdout.
- `--format json` — JSON em **stdout**, sem truncamento. Use para parsing programático (jq, scripts).

Padrões inválidos comuns (não tente):

- `plugadvpl arch X --json` → flag `--json` **não existe**. Correto: `plugadvpl --format json arch X`.
- `$env:COLUMNS=400; plugadvpl ...` → workaround frágil; mistura sintaxe PS/Bash. Correto: `--format md`.
- Posicionar `--format` depois do subcomando funciona em alguns casos mas é frágil — **sempre** antes do subcomando.

### Encoding (importante para Edit/Write)

Fontes legados são `cp1252` (.prw/.prx). TLPP moderno (.tlpp) pode ser `utf-8`.
**Preserve sempre o encoding detectado em `fontes.encoding`** quando editar — gravar em
encoding errado quebra acentuação e o compilador AppServer.

### Manutenção do índice

- `plugadvpl status [--check-stale]` — ver totais e arquivos desatualizados
- `plugadvpl reindex <arq>` — após editar um fonte
- `plugadvpl ingest --incremental` — ingest novamente arquivos modificados (default)
- `plugadvpl doctor` — diagnósticos (encoding suspeito, FTS5, órfãos)
"""


@app.command()
def init(ctx: typer.Context) -> None:
    """Cria ``./.plugadvpl/index.db``, escreve fragment em ``CLAUDE.md`` e atualiza ``.gitignore``."""
    root: Path = ctx.obj["root"]
    db_path: Path = ctx.obj["db"]
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = open_db(db_path)
    try:
        apply_migrations(conn)
        init_meta(conn, project_root=str(root), cli_version=__version__)
        seed_lookups(conn)
    finally:
        close_db(conn)

    _write_claude_md_fragment(root)
    _add_to_gitignore(root, ".plugadvpl/")

    if not ctx.obj["quiet"]:
        typer.echo(f"OK  DB criado em {db_path}")
        typer.echo("OK  CLAUDE.md atualizado (fragment plugadvpl)")
        typer.echo("OK  .plugadvpl/ adicionado ao .gitignore")


def _check_fragment_staleness(root: Path) -> str | None:
    """Retorna mensagem descritiva se o fragment CLAUDE.md está desatualizado.

    v0.3.23 (#1 do QA round 3). Lê CLAUDE.md, localiza a região BEGIN/END
    plugadvpl, extrai o marker `<!-- plugadvpl-fragment-version: X.Y.Z -->`,
    e compara com `__version__`.

    Retornos:
      - ``None``: fragment atualizado OU CLAUDE.md sem fragment (caso fresh
        sem init ainda — não polui status).
      - ``"foi gerado por v X.Y.Z"``: marker presente mas != runtime.
      - ``"é de versão pré-v0.3.23 (sem versionamento)"``: marker ausente.
    """
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        return None
    try:
        content = claude_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if _CLAUDE_FRAGMENT_BEGIN not in content or _CLAUDE_FRAGMENT_END not in content:
        return None  # sem fragment — usuário não rodou init aqui ainda.
    # Janela do fragment.
    start = content.index(_CLAUDE_FRAGMENT_BEGIN)
    end = content.index(_CLAUDE_FRAGMENT_END) + len(_CLAUDE_FRAGMENT_END)
    fragment = content[start:end]
    m = _CLAUDE_FRAGMENT_VERSION_MARKER_RE.search(fragment)
    if m is None:
        return "é de versão pré-v0.3.23 (sem marker de versionamento)"
    fragment_version = m.group(1)
    if fragment_version != __version__:
        return f"foi gerado por plugadvpl {fragment_version}"
    return None


def _write_claude_md_fragment(root: Path) -> None:
    """Escreve/atualiza idempotentemente a região ``BEGIN/END plugadvpl`` em CLAUDE.md.

    v0.3.23: substitui `__VERSION__` no body por `__version__` real do binario
    pra que o `status` consiga detectar fragment desatualizado depois.
    """
    claude_md = root / "CLAUDE.md"
    body_with_version = _CLAUDE_FRAGMENT_BODY.replace("__VERSION__", __version__)
    fragment = (
        _CLAUDE_FRAGMENT_BEGIN
        + "\n"
        + body_with_version
        + _CLAUDE_FRAGMENT_END
        + "\n"
    )

    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        if _CLAUDE_FRAGMENT_BEGIN in content and _CLAUDE_FRAGMENT_END in content:
            content = re.sub(
                re.escape(_CLAUDE_FRAGMENT_BEGIN) + r".*?" + re.escape(_CLAUDE_FRAGMENT_END),
                fragment.rstrip("\n"),
                content,
                flags=re.DOTALL,
            )
        else:
            sep = "" if content.endswith("\n") else "\n"
            content = content + sep + "\n" + fragment
        claude_md.write_text(content, encoding="utf-8")
    else:
        claude_md.write_text(fragment, encoding="utf-8")


def _add_to_gitignore(root: Path, line: str) -> None:
    """Adiciona ``line`` em ``.gitignore`` se ainda não existir.

    Não cria ``.gitignore`` se ainda não existe (evita poluir projetos sem git).
    """
    gi = root / ".gitignore"
    if not gi.exists():
        return
    existing = gi.read_text(encoding="utf-8")
    if line in existing.splitlines():
        return
    sep = "" if existing.endswith("\n") or not existing else "\n"
    with gi.open("a", encoding="utf-8") as f:
        f.write(sep + line + "\n")


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------


@app.command()
def ingest(
    ctx: typer.Context,
    workers: Annotated[
        int | None,
        typer.Option(
            "--workers",
            "-w",
            help="N workers (0 = single-thread; None = adaptive).",
        ),
    ] = None,
    incremental: Annotated[
        bool,
        typer.Option(
            "--incremental/--no-incremental",
            help="Pula arquivos cujo mtime no DB é >= ao filesystem.",
        ),
    ] = True,
    no_content: Annotated[
        bool,
        typer.Option("--no-content", help="Não persiste corpo dos chunks (apenas metadata)."),
    ] = False,
    redact_secrets: Annotated[
        bool,
        typer.Option("--redact-secrets", help="Mascara URLs com credenciais e tokens hex."),
    ] = False,
) -> None:
    """Indexa todos os fontes em ``--root`` (scan -> parse -> SQLite -> FTS5 rebuild)."""
    root: Path = ctx.obj["root"]
    counters = do_ingest(
        root,
        workers=workers,
        incremental=incremental,
        no_content=no_content,
        redact_secrets=redact_secrets,
    )

    summary: dict[str, object] = {
        "arquivos_total": counters["arquivos_total"],
        "ok": counters["arquivos_ok"],
        "skipped": counters["arquivos_skipped"],
        "failed": counters["arquivos_failed"],
        "chunks": counters["chunks"],
        "chamadas": counters["chamadas"],
        "lint_findings": counters["lint_findings"],
        "duration_ms": counters["duration_ms"],
    }
    _render_from_ctx(
        ctx,
        [summary],
        title="Ingest summary",
        next_steps=[
            "plugadvpl status",
            "plugadvpl find <termo>",
        ],
    )

    # v0.3.13 — pegadinha do --incremental após bump de lookups: arquivos pulados
    # NÃO são re-avaliados contra regras de lint novas. Detectamos via mudança no
    # lookup_bundle_hash + qualquer arquivo skipped + modo incremental.
    if (
        incremental
        and counters.get("lookup_hash_changed")
        and counters["arquivos_skipped"] > 0
        and not ctx.obj["quiet"]
    ):
        skipped = counters["arquivos_skipped"]
        typer.secho(
            f"\n⚠ Lookups (lint_rules/funcoes_restritas/...) mudaram desde o último ingest.\n"
            f"  --incremental pulou {skipped} arquivo(s) cujo mtime não mudou — "
            f"esses NÃO foram re-avaliados contra as regras novas.\n"
            f"  Para cobrir todo o codebase com as regras atualizadas, rode:\n"
            f"      plugadvpl ingest --no-incremental",
            fg=typer.colors.YELLOW,
            err=True,
        )


# ---------------------------------------------------------------------------
# reindex
# ---------------------------------------------------------------------------


@app.command()
def reindex(
    ctx: typer.Context,
    arq: Annotated[str, typer.Argument(help="Basename ou caminho relativo do arquivo.")],
) -> None:
    """Re-ingest de UM arquivo. Útil após edição manual.

    Implementação: chama :func:`plugadvpl.ingest.ingest` apontando para o
    diretório que contém o arquivo, com ``incremental=False`` para forçar
    reescrita.
    """
    root: Path = ctx.obj["root"]
    candidates = scan_sources(root)
    target = next((p for p in candidates if p.name.lower() == arq.lower()), None)
    if target is None:
        # tenta resolver como path direto
        candidate = (root / arq).resolve()
        if candidate.exists():
            target = candidate
    if target is None or not target.exists():
        typer.secho(f"Arquivo '{arq}' não encontrado em {root}.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    # Force-write apenas do alvo via _write_parsed em conexão direta.
    db_path: Path = ctx.obj["db"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = open_db(db_path)
    counters: dict[str, int] = {
        "arquivos_total": 1,
        "arquivos_ok": 0,
        "arquivos_skipped": 0,
        "arquivos_failed": 0,
        "chunks": 0,
        "chamadas": 0,
        "params": 0,
        "lint_findings": 0,
    }
    try:
        apply_migrations(conn)
        init_meta(conn, project_root=str(root), cli_version=__version__)
        seed_lookups(conn)
        set_meta(conn, "parser_version", PARSER_VERSION)
        try:
            parsed = parse_source(target)
            content = target.read_text(encoding=parsed.get("encoding", "cp1252"), errors="replace")
            findings = lint_module.lint_source(parsed, content)
            _write_parsed(
                conn, root, target, parsed, content, findings, counters,
                no_content=False, redact_secrets=False,
            )
        except Exception as exc:
            counters["arquivos_failed"] += 1
            typer.secho(f"Falha ao reindexar {target.name}: {exc}", fg=typer.colors.RED, err=True)
        # Rebuild FTS para refletir mudança.
        conn.execute("INSERT INTO fonte_chunks_fts(fonte_chunks_fts) VALUES('rebuild')")
        conn.execute("INSERT INTO fonte_chunks_fts_tri(fonte_chunks_fts_tri) VALUES('rebuild')")
        conn.commit()
    finally:
        close_db(conn)

    _render_from_ctx(
        ctx,
        [
            {
                "arquivo": target.name,
                "ok": counters["arquivos_ok"],
                "failed": counters["arquivos_failed"],
                "chunks": counters["chunks"],
                "chamadas": counters["chamadas"],
                "lint_findings": counters["lint_findings"],
            }
        ],
        title=f"Reindex {target.name}",
        next_steps=[f"plugadvpl arch {target.name}"],
    )


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@app.command()
def status(
    ctx: typer.Context,
    check_stale: Annotated[
        bool,
        typer.Option("--check-stale", help="Compara mtime do filesystem com DB."),
    ] = False,
) -> None:
    """Mostra estado do índice (versões, contadores, opcionalmente arquivos stale)."""
    root: Path = ctx.obj["root"]
    rows = _with_ro_db(ctx, lambda c: q_status(c, str(root), __version__))
    _render_from_ctx(ctx, rows, title="Status do índice")

    # Aviso de divergência runtime ↔ índice — fecha o gap "binário foi atualizado
    # via uv tool upgrade mas o status ainda mostra a versão antiga gravada".
    if rows and not ctx.obj["quiet"]:
        runtime = rows[0].get("runtime_version")
        stored = rows[0].get("plugadvpl_version")
        if runtime and stored and runtime != stored:
            typer.secho(
                f"\n⚠ Índice criado com plugadvpl {stored}, binário atual é {runtime}.\n"
                f"  Rode 'plugadvpl ingest --incremental' para atualizar o índice "
                f"com regras/parsers da versão nova.",
                fg=typer.colors.YELLOW,
                err=True,
            )

        # v0.3.23 (#1 do QA round 3): aviso quando o fragment do CLAUDE.md ficou
        # pra trás do binário (gerado por init de versão antiga). Consulta o
        # arquivo, extrai o marker `<!-- plugadvpl-fragment-version: X.Y.Z -->`,
        # e compara com __version__. Marker ausente também avisa (fragments
        # pre-v0.3.23 não tinham versionamento).
        fragment_state = _check_fragment_staleness(root)
        if fragment_state is not None:
            typer.secho(
                f"\n⚠ Fragment do CLAUDE.md {fragment_state}, binário atual é {__version__}.\n"
                f"  Rode 'plugadvpl init' para regenerar o fragment com a versão atual\n"
                f"  (sobrescreve só a região BEGIN/END plugadvpl; resto do CLAUDE.md preservado).",
                fg=typer.colors.YELLOW,
                err=True,
            )

    if check_stale:
        try:
            files = scan_sources(root)
            fs_state = {f.name: f.stat().st_mtime_ns for f in files if f.exists()}
        except OSError as exc:
            typer.secho(f"Erro ao escanear filesystem: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2) from exc
        stale = _with_ro_db(ctx, lambda c: stale_files(c, fs_state))
        _render_from_ctx(
            ctx,
            stale,
            columns=["arquivo", "estado", "db_mtime", "fs_mtime"],
            title="Arquivos stale/novos/deletados",
            next_steps=[f"plugadvpl ingest --root {root}"] if stale else None,
        )


# ---------------------------------------------------------------------------
# find
# ---------------------------------------------------------------------------


@app.command()
def find(
    ctx: typer.Context,
    termo: Annotated[str, typer.Argument(help="Nome de função, fragmento de arquivo ou texto.")],
) -> None:
    """Busca composta: tenta função -> arquivo -> conteúdo (FTS)."""

    rows = _with_ro_db(ctx, lambda c: find_any(c, termo))
    _render_from_ctx(
        ctx,
        rows,
        title=f"Resultados para '{termo}'",
        next_steps=(
            [
                f"plugadvpl arch {rows[0].get('arquivo', '<arq>')}",
                f"plugadvpl callers {termo}",
            ]
            if rows
            else None
        ),
    )


# ---------------------------------------------------------------------------
# callers / callees
# ---------------------------------------------------------------------------


@app.command()
def callers(
    ctx: typer.Context,
    funcao: Annotated[str, typer.Argument(help="Nome da função alvo.")],
) -> None:
    """Lista quem chama ``funcao`` (lookup em ``chamadas_funcao``)."""

    rows = _with_ro_db(ctx, lambda c: q_callers(c, funcao))
    _render_from_ctx(
        ctx,
        rows,
        title=f"Callers de {funcao}",
        next_steps=[f"plugadvpl find {funcao}"] if not rows else None,
    )


@app.command()
def callees(
    ctx: typer.Context,
    funcao: Annotated[str, typer.Argument(help="Nome da função (ou basename de fonte).")],
) -> None:
    """Lista quem ``funcao`` chama (lookup em ``chamadas_funcao``)."""

    rows = _with_ro_db(ctx, lambda c: q_callees(c, funcao))
    _render_from_ctx(
        ctx,
        rows,
        title=f"Callees de {funcao}",
        next_steps=[f"plugadvpl callers {rows[0]['destino']}"] if rows else None,
    )


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------


@app.command()
def tables(
    ctx: typer.Context,
    tabela: Annotated[str, typer.Argument(help="Nome da tabela ADVPL (ex: SA1, SC5, ZA1).")],
    mode: Annotated[
        TableMode | None,
        typer.Option("--mode", "-m", help="Filtra por modo (read|write|reclock)."),
    ] = None,
) -> None:
    """Lista quem usa a tabela ``T`` (lookup em ``fonte_tabela``)."""

    modo = mode.value if mode else None
    rows = _with_ro_db(ctx, lambda c: tables_query(c, tabela, modo))
    _render_from_ctx(
        ctx,
        rows,
        title=f"Uso da tabela {tabela.upper()}" + (f" ({modo})" if modo else ""),
        next_steps=[f"plugadvpl arch {rows[0]['arquivo']}"] if rows else None,
    )


# ---------------------------------------------------------------------------
# param
# ---------------------------------------------------------------------------


@app.command()
def param(
    ctx: typer.Context,
    parametro: Annotated[str, typer.Argument(help="Nome do parâmetro (ex: MV_LOCALIZA).")],
) -> None:
    """Lista quem usa o parâmetro ``MV_*``."""

    rows = _with_ro_db(ctx, lambda c: param_query(c, parametro))
    _render_from_ctx(
        ctx,
        rows,
        title=f"Uso de {parametro.upper()}",
    )


# ---------------------------------------------------------------------------
# arch
# ---------------------------------------------------------------------------


@app.command()
def arch(
    ctx: typer.Context,
    arquivo: Annotated[str, typer.Argument(help="Basename do fonte (ex: FATA050.prw).")],
) -> None:
    """Resumo arquitetural de UM fonte (capabilities + funções + tabelas + includes)."""

    rows = _with_ro_db(ctx, lambda c: q_arch(c, arquivo))
    if not rows:
        typer.secho(f"Arquivo '{arquivo}' não encontrado no índice.", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)
    _render_from_ctx(
        ctx,
        rows,
        title=f"Arquitetura: {arquivo}",
        next_steps=[
            f"plugadvpl callees {arquivo}",
            f"plugadvpl lint {arquivo}",
        ],
    )


# ---------------------------------------------------------------------------
# lint
# ---------------------------------------------------------------------------


@app.command()
def lint(
    ctx: typer.Context,
    arquivo: Annotated[str | None, typer.Argument(help="Filtra por arquivo (opcional).")] = None,
    severity: Annotated[
        str | None,
        typer.Option("--severity", "-s", help="Filtra por severidade (critical|error|warning)."),
    ] = None,
    regra: Annotated[
        str | None,
        typer.Option("--regra", help="Filtra por regra_id (ex: BP-001 ou SX-001)."),
    ] = None,
    cross_file: Annotated[
        bool,
        typer.Option(
            "--cross-file",
            help=(
                "Recalcula e grava findings cross-file SX-001..SX-011 "
                "(requer ingest + ingest-sx prévios)."
            ),
        ),
    ] = False,
) -> None:
    """Lista lint findings (filtros por arquivo/severidade/regra; ``--cross-file`` reavalia SX-*)."""
    if cross_file:
        # Modo write: precisa de conexão writable, recompute e persiste.
        db_path: Path = ctx.obj["db"]
        if not db_path.exists():
            typer.secho(
                f"Erro: índice não encontrado em {db_path}.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=2)
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            findings = lint_module.lint_cross_file(conn)
            n = lint_module.persist_cross_file_findings(conn, findings)
        finally:
            close_db(conn)
        if not ctx.obj["quiet"]:
            typer.secho(
                f"OK  {n} findings cross-file gravados (SX-001..SX-011).",
                err=True,
            )

    rows = _with_ro_db(ctx, lambda c: lint_query(c, arquivo, severity, regra))
    _render_from_ctx(
        ctx,
        rows,
        title="Lint findings",
        next_steps=[f"plugadvpl arch {rows[0]['arquivo']}"] if rows else None,
    )


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


@app.command()
def doctor(ctx: typer.Context) -> None:
    """Diagnósticos do índice (encoding, órfãos, FTS sync, lookups)."""

    rows = _with_ro_db(ctx, doctor_diagnostics)
    _render_from_ctx(
        ctx,
        rows,
        columns=["check", "status", "count", "detail"],
        title="Doctor — saúde do índice",
        next_steps=(
            ["plugadvpl ingest --no-incremental"]
            if any(r.get("status") in {"error", "warn"} for r in rows)
            else None
        ),
    )


# ---------------------------------------------------------------------------
# grep
# ---------------------------------------------------------------------------


@app.command()
def grep(
    ctx: typer.Context,
    pattern: Annotated[str, typer.Argument(help="Padrão de busca.")],
    mode: Annotated[
        GrepMode,
        typer.Option("--mode", "-m", help="Modo: fts (default), literal, identifier."),
    ] = GrepMode.fts,
) -> None:
    """Busca textual no conteúdo dos chunks (FTS5 / LIKE / identifier)."""

    limit = ctx.obj["limit"] or 50
    rows = _with_ro_db(ctx, lambda c: grep_fts(c, pattern, mode=mode.value, limit=limit))
    _render_from_ctx(
        ctx,
        rows,
        title=f"Grep ({mode.value}): {pattern}",
        next_steps=[f"plugadvpl arch {rows[0]['arquivo']}"] if rows else None,
    )


# ---------------------------------------------------------------------------
# v0.3.0 — Universo 2: ingest-sx, impacto, gatilho, sx-status
# ---------------------------------------------------------------------------


@app.command(name="ingest-sx")
def ingest_sx_cmd(
    ctx: typer.Context,
    csv_dir: Annotated[
        Path,
        typer.Argument(
            help="Pasta com CSVs SX (sx1.csv, sx2.csv, ..., sxg.csv) exportados via Configurador -> Misc -> Exportar Dicionario.",
        ),
    ],
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            "-w",
            help="Reservado para futuro paralelismo. Atualmente não usado (parser é I/O bound + executemany single-thread).",
        ),
    ] = 0,
) -> None:
    """Indexa o Dicionário SX a partir de CSVs (Universo 2)."""
    _ = workers  # explicitly unused; kept for symmetry with `ingest`
    db_path: Path = ctx.obj["db"]
    if not csv_dir.exists() or not csv_dir.is_dir():
        typer.secho(
            f"Pasta CSV inválida: {csv_dir}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    counters = do_ingest_sx(csv_dir.resolve(), db_path)
    summary_rows: list[dict[str, object]] = [
        {
            "tabela": tabela,
            "rows": counters["per_table"].get(tabela, 0),
        }
        for tabela in (
            "tabelas", "campos", "indices", "gatilhos", "parametros",
            "perguntas", "tabelas_genericas", "relacionamentos", "pastas",
            "consultas", "grupos_campo",
        )
    ]
    summary_rows.append(
        {
            "tabela": "_TOTAL",
            "rows": counters["total_rows"],
        }
    )
    if not ctx.obj["quiet"]:
        typer.secho(
            f"OK  {counters['csvs_ok']}/{counters['csvs_total']} CSVs ingeridos "
            f"({counters['csvs_skipped']} pulados, {counters.get('csvs_failed', 0)} falhos) "
            f"em {counters['duration_ms']}ms",
            err=True,
        )
    _render_from_ctx(
        ctx,
        summary_rows,
        title="Ingest SX — rows por tabela",
        next_steps=[
            "plugadvpl impacto A1_COD",
            "plugadvpl gatilho A1_COD",
        ],
    )


@app.command()
def impacto(
    ctx: typer.Context,
    campo: Annotated[
        str,
        typer.Argument(help="Nome do campo SX3 (ex: A1_COD)."),
    ],
    depth: Annotated[
        int,
        typer.Option(
            "--depth",
            "-d",
            min=1,
            max=3,
            help="Profundidade da cadeia de gatilhos SX7 (1..3).",
        ),
    ] = 1,
) -> None:
    """Cruza referencias a um campo: fontes <-> SX3 (VALID/WHEN/INIT) <-> SX7 <-> SX1.

    Killer feature do v0.3.0. Em segundos: para um campo arbitrário, lista TODA
    a cadeia de impacto (fontes que mencionam, validações que dependem,
    gatilhos que disparam, perguntas SX1 que referenciam).
    """
    rows = _with_ro_db(ctx, lambda c: impacto_query(c, campo, depth=depth))
    columns = ["tipo", "local", "contexto", "severidade"]
    _render_from_ctx(
        ctx,
        rows,
        columns=columns,
        title=f"Impacto de {campo.upper()} (depth={depth})",
        next_steps=(
            [
                f"plugadvpl gatilho {campo}",
                f"plugadvpl tables {campo.split('_')[0] if '_' in campo else campo}",
            ]
            if rows
            else None
        ),
    )


@app.command()
def gatilho(
    ctx: typer.Context,
    campo: Annotated[
        str,
        typer.Argument(help="Nome do campo SX3 (ex: A1_COD)."),
    ],
    depth: Annotated[
        int,
        typer.Option(
            "--depth",
            "-d",
            min=1,
            max=3,
            help="Profundidade da cadeia (1..3). Default 3.",
        ),
    ] = 3,
) -> None:
    """Lista cadeia de gatilhos SX7 originados/destinados ao campo."""
    rows = _with_ro_db(ctx, lambda c: gatilho_query(c, campo, depth=depth))
    columns = ["nivel", "via", "origem", "sequencia", "destino", "regra", "tipo"]
    _render_from_ctx(
        ctx,
        rows,
        columns=columns,
        title=f"Cadeia de gatilhos SX7 — {campo.upper()} (depth={depth})",
        next_steps=[f"plugadvpl impacto {campo}"] if rows else None,
    )


@app.command(name="sx-status")
def sx_status_cmd(ctx: typer.Context) -> None:
    """Mostra contadores por tabela do Dicionário SX (após ``ingest-sx``)."""
    rows = _with_ro_db(ctx, sx_status)
    _render_from_ctx(
        ctx,
        rows,
        title="Status do Dicionário SX",
        next_steps=(
            ["plugadvpl ingest-sx <pasta-csv>"]
            if rows and not rows[0].get("sx_ingerido")
            else ["plugadvpl impacto A1_COD"]
        ),
    )


# ---------------------------------------------------------------------------
# v0.4.0 — Universo 3 (Rastreabilidade) Feature A: workflow
# ---------------------------------------------------------------------------


@app.command()
def workflow(
    ctx: typer.Context,
    kind: Annotated[
        str | None,
        typer.Option(
            "--kind",
            "-k",
            help="Filtra por tipo: workflow|schedule|job_standalone|mail_send",
        ),
    ] = None,
    target: Annotated[
        str | None,
        typer.Option("--target", "-t", help="Filtra por nome alvo (callback/Main/pergunte)."),
    ] = None,
    arquivo: Annotated[
        str | None,
        typer.Option("--arquivo", "-a", help="Filtra por arquivo (basename)."),
    ] = None,
) -> None:
    """Lista execution_triggers indexados (Universo 3 / Feature A).

    Detecta 4 mecanismos canônicos TOTVS de "execução não-direta":

    - ``workflow``       — TWFProcess / MsWorkflow / WFPrepEnv (callbacks)
    - ``schedule``       — Static Function SchedDef() (configurador SIGACFG)
    - ``job_standalone`` — Main Function + RpcSetEnv (daemon ONSTART)
    - ``mail_send``      — MailAuto / SEND MAIL UDC / TMailManager

    Sem filtros: lista tudo. Com ``--kind`` mostra só uma categoria.
    """
    rows = _with_ro_db(
        ctx, lambda c: execution_triggers_query(c, kind=kind, target=target, arquivo=arquivo),
    )
    # Renderiza só os campos top-level; metadata fica em JSON.
    display_rows = [
        {
            "arquivo": r["arquivo"],
            "funcao": r["funcao"],
            "linha": r["linha"],
            "kind": r["kind"],
            "target": r["target"],
            "snippet": (r["snippet"] or "")[:80],
        }
        for r in rows
    ]
    _render_from_ctx(
        ctx,
        display_rows,
        columns=["arquivo", "funcao", "linha", "kind", "target", "snippet"],
        title=(
            f"Execution triggers"
            + (f" (kind={kind})" if kind else "")
            + (f" (target={target})" if target else "")
            + (f" (arquivo={arquivo})" if arquivo else "")
        ),
        next_steps=(
            [f"plugadvpl find {target}" for target in {r["target"] for r in rows[:3] if r["target"]}]
            if rows
            else ["plugadvpl ingest --no-incremental  # se nada detectado"]
        ),
    )


# ---------------------------------------------------------------------------
# v0.4.1 — Universo 3 (Rastreabilidade) Feature B: execauto
# ---------------------------------------------------------------------------


@app.command()
def execauto(
    ctx: typer.Context,
    routine: Annotated[
        str | None,
        typer.Option("--routine", "-r", help="Filtra por rotina TOTVS (MATA410, FINA050, ...)."),
    ] = None,
    modulo: Annotated[
        str | None,
        typer.Option("--modulo", "-m", help="Filtra por módulo (SIGAFAT, SIGACOM, SIGAFIN, ...)."),
    ] = None,
    arquivo: Annotated[
        str | None,
        typer.Option("--arquivo", "-a", help="Filtra por arquivo (basename, case-insensitive)."),
    ] = None,
    op: Annotated[
        str | None,
        typer.Option("--op", "-o", help="Filtra por operação: inc|alt|exc (op_code 3/4/5)."),
    ] = None,
    dynamic: Annotated[
        bool | None,
        typer.Option(
            "--dynamic/--no-dynamic",
            help="--dynamic só não-resolvíveis; --no-dynamic só resolvidas; default: ambos.",
        ),
    ] = None,
) -> None:
    """Lista chamadas MsExecAuto resolvidas (Universo 3 / Feature B).

    Resolve a indireção do codeblock ``{|args| Rotina(args)}`` e cruza com o
    catálogo TOTVS pra inferir tabelas tocadas, módulo, e tipo de operação
    (inclusão/alteração/exclusão).

    Sem filtros: lista todas as chamadas. Use ``--routine MATA410`` pra ver
    quem inclui Pedido de Venda; ``--dynamic`` pra revisar calls não-resolvíveis.
    """
    from plugadvpl.parsing.execauto import load_execauto_catalog  # lazy
    rows = _with_ro_db(
        ctx,
        lambda c: execauto_calls_query(
            c, routine=routine, modulo=modulo, arquivo=arquivo, op=op, dynamic=dynamic,
        ),
    )
    display_rows = [
        {
            "arquivo": r["arquivo"],
            "funcao": r["funcao"],
            "linha": r["linha"],
            "routine": r["routine"] or "(dynamic)",
            "module": r["module"] or "",
            "op": r["op_label"] or (str(r["op_code"]) if r["op_code"] is not None else ""),
            "tabelas": ",".join(r["tables_resolved"]),
            "snippet": (r["snippet"] or "")[:80],
        }
        for r in rows
    ]
    _render_from_ctx(
        ctx,
        display_rows,
        columns=["arquivo", "funcao", "linha", "routine", "module", "op", "tabelas", "snippet"],
        title=(
            f"ExecAuto calls"
            + (f" (routine={routine})" if routine else "")
            + (f" (modulo={modulo})" if modulo else "")
            + (f" (arquivo={arquivo})" if arquivo else "")
            + (f" (op={op})" if op else "")
            + (" (dynamic)" if dynamic else "")
        ),
        next_steps=(
            [
                f"plugadvpl arch {arq}"
                for arq in {r["arquivo"] for r in rows[:3]}
            ]
            if rows
            else [
                "plugadvpl ingest --no-incremental  # se esperava findings",
                "plugadvpl execauto --dynamic       # ver calls não-resolvíveis",
            ]
        ),
    )


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


_GLOBAL_FLAGS = {
    "--root", "-r", "--db", "--format", "-f", "--limit", "--offset",
    "--compact", "--quiet", "-q", "--no-next-steps", "--version", "-V",
}

# v0.3.22 (#18 do QA round 2): flags scoped a subcomando especifico.
# Caso inverso de #2: usuario poe flag de subcomando ANTES do subcomando
# (`plugadvpl --workers 8 ingest`) e Click responde "No such option" cru
# sem dica. Detectamos e sugerimos posicao correta.
_SUBCOMMAND_FLAGS = {
    # ingest
    "--workers", "-w", "--no-content", "--redact-secrets",
    "--incremental", "--no-incremental",
    # status
    "--check-stale",
    # lint
    "--severity", "--rule", "--cross-file",
    # gatilho/impacto
    "--depth",
    # tables
    "--mode", "-m", "--read", "--write", "--reclock",
}


def main() -> None:
    """Entry point para console_script ``plugadvpl``."""
    # Defense layer: força stdout/stderr para UTF-8 em Windows. Sem isto, qualquer
    # caractere fora do cp1252 (default do console PS 5.1/cmd.exe) crasha com
    # UnicodeEncodeError quando o Rich renderiza help ou output. errors='replace'
    # garante que mesmo se algo escapar, vira '?' em vez de tombar.
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, io.UnsupportedOperation):
                pass

    # v0.3.15 (#2 do QA report): hint quando usuário põe flag global APÓS
    # subcomando. Click reporta "No such option: --limit" sem dica de que a
    # flag existe mas no escopo errado. Detectamos a chamada misplaced e
    # adicionamos uma linha amarela orientando posicionamento correto.
    misplaced = _detect_misplaced_flag(sys.argv[1:])
    try:
        app()
    except SystemExit as exit_:
        if misplaced and exit_.code not in (0, None):
            flag, subcmd, scope = misplaced
            if scope == "global":
                typer.secho(
                    f"\nDica: '{flag}' eh uma flag GLOBAL — vem ANTES do subcomando.\n"
                    f"  Errado:  plugadvpl {subcmd} {flag} ...\n"
                    f"  Correto: plugadvpl {flag} ... {subcmd}",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
            else:  # scope == "subcommand"
                typer.secho(
                    f"\nDica: '{flag}' eh uma flag de SUBCOMANDO — vem DEPOIS do subcomando.\n"
                    f"  Errado:  plugadvpl {flag} ... {subcmd}\n"
                    f"  Correto: plugadvpl {subcmd} {flag} ...",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
        raise


def _detect_misplaced_flag(
    argv: list[str],
) -> tuple[str, str, str] | None:
    """Detecta flag em posicao errada. Retorna (flag, subcomando, scope).

    Dois cenarios:
      - scope="global": flag global aparece DEPOIS do subcomando.
      - scope="subcommand": flag scoped aparece ANTES do subcomando.
    """
    subcmd: str | None = None
    skip_next = False
    pre_subcmd_misplaced: tuple[str, str] | None = None  # (flag, ?)
    for tok in argv:
        if skip_next:
            skip_next = False
            continue
        if subcmd is None:
            if tok.startswith("-"):
                # Pode ser flag global no escopo certo (antes do subcmd) que
                # aceita valor. Pula o próximo token se a flag tipicamente o exige.
                if tok in _GLOBAL_FLAGS and tok not in {
                    "--compact", "--quiet", "-q", "--no-next-steps",
                    "--version", "-V",
                }:
                    skip_next = True
                # v0.3.22: flag de subcomando aparecendo antes — registramos
                # mas precisamos do subcmd pra sugerir corretamente.
                elif tok in _SUBCOMMAND_FLAGS and pre_subcmd_misplaced is None:
                    pre_subcmd_misplaced = (tok, "")
                    # Pula valor da flag (heuristica: a maioria aceita valor).
                    if tok not in {"--no-content", "--redact-secrets",
                                    "--incremental", "--no-incremental",
                                    "--check-stale", "--cross-file",
                                    "--read", "--write", "--reclock"}:
                        skip_next = True
                continue
            subcmd = tok
            if pre_subcmd_misplaced:
                return (pre_subcmd_misplaced[0], subcmd, "subcommand")
            continue
        if tok in _GLOBAL_FLAGS:
            return (tok, subcmd, "global")
    return None


# Alias retrocompat (testes antigos podem importar este nome).
_detect_misplaced_global_flag = _detect_misplaced_flag


if __name__ == "__main__":
    main()
    sys.exit(0)
