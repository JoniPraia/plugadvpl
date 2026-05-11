# Plugadvpl MVP — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o MVP (v0.1.0) do plugadvpl — plugin Claude Code + CLI Python que indexa fontes ADVPL/TLPP em SQLite com FTS5 e permite ao Claude consultar metadados antes de ler `.prw` cru, economizando 10–15× tokens.

**Architecture:** Mono-repo com dois "produtos" lado a lado: (1) plugin Claude Code (markdown em `skills/`, `agents/`, `hooks/`, `.claude-plugin/`) distribuído via marketplace GitHub; (2) CLI Python (`cli/plugadvpl/`) distribuída via PyPI usando hatchling + hatch-vcs. Plugin chama CLI via `uvx plugadvpl@<v> <subcomando>`. Índice fica em `<projeto-cliente>/.plugadvpl/index.db`.

**Tech Stack:** Python 3.11+, SQLite com FTS5 (tokenizer `unicode61` + trigram), typer (CLI), rich (output), hatchling+hatch-vcs (build), pytest+syrupy+pytest-benchmark (tests), ruff+mypy (quality), GitHub Actions com Trusted Publisher OIDC.

**Spec de referência:** `docs/superpowers/specs/2026-05-11-plugadvpl-design.md`

---

## Ordem de execução

Os chunks são desenhados para serem executados em ordem (dependências entre eles). Cada chunk termina com testes verdes e um commit em estado funcional.

1. **Chunk 1** — Setup do mono-repo + estrutura base
2. **Chunk 2** — Schema SQLite + db.py
3. **Chunk 3** — Parser core (strip-first + extrações de fontes)
4. **Chunk 4** — Parser avançado (capabilities, REST, HTTP, MVC hooks)
5. **Chunk 5** — Lint single-file (13 regras)
6. **Chunk 6** — Lookup tables (extração de advpl-specialist → JSONs)
7. **Chunk 7** — Ingest pipeline (paralelização adaptativa + FTS5 rebuild)
8. **Chunk 8** — Query layer + CLI (typer)
9. **Chunk 9** — Skills de comando (13 SKILL.md)
10. **Chunk 10** — Skills de conhecimento (10 SKILL.md)
11. **Chunk 11** — Agents (4)
12. **Chunk 12** — Hook session-start
13. **Chunk 13** — Testes (fixtures, unit, integration, e2e_local)
14. **Chunk 14** — CI/CD + Release workflows + validate_plugin.py

---

## Chunk 1: Setup do mono-repo + estrutura base

**Objetivo:** Criar a estrutura de pastas, arquivos de governança (LICENSE, NOTICE, CONTRIBUTING, etc.), `pyproject.toml` da CLI com hatchling+hatch-vcs, `.claude-plugin/plugin.json` e `marketplace.json`. Ao final, repo tem layout completo, vazio mas válido.

**Files:**
- Create: `LICENSE`, `NOTICE`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- Create: `.gitignore`
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Create: `cli/pyproject.toml`, `cli/plugadvpl/__init__.py`, `cli/plugadvpl/__main__.py`, `cli/README.md`
- Create: `cli/tests/__init__.py`
- Create directory placeholders (with `.gitkeep`): `skills/`, `agents/`, `hooks/`, `cli/plugadvpl/lookups/`, `cli/plugadvpl/migrations/`, `cli/plugadvpl/parsing/`, `cli/tests/unit/`, `cli/tests/integration/`, `cli/tests/bench/`, `cli/tests/e2e_local/`, `cli/tests/fixtures/synthetic/`, `cli/tests/fixtures/expected/`
- Create: `Makefile`

### Task 1.1: Inicializar git e .gitignore

- [ ] **Step 1: Inicializar git no diretório raiz**

```bash
cd d:/IA/Projetos/plugadvpl
git init
git config user.name "<owner>"
git config user.email "<owner>@example.com"
```

- [ ] **Step 2: Criar `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
*.egg-info/
build/
dist/
.venv/
.uv/

# Plugadvpl index (per-projeto-cliente — não versionar)
.plugadvpl/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Commit inicial**

```bash
git add .gitignore
git commit -m "chore: initial gitignore"
```

### Task 1.2: Arquivos de governança

- [ ] **Step 1: Criar `LICENSE` (MIT)**

```
MIT License

Copyright (c) 2026 <owner>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Criar `NOTICE`**

```
plugadvpl — Plugin Claude Code + CLI Python para análise de fontes ADVPL/TLPP

This product includes:

1. Parser de fontes ADVPL portado de projeto interno anterior do autor
   (~750 linhas, validado em aproximadamente 2.000 fontes ADVPL).

2. Lookup tables (funcoes_nativas, funcoes_restritas, lint_rules, sql_macros,
   modulos_erp, pontos_entrada_padrao) com origem no projeto advpl-specialist
   (https://github.com/thalysjuvenal/advpl-specialist) por Thalys Augusto,
   licença MIT. Conteúdo extraído e adaptado com crédito explícito.

3. Padrões de schema SQLite baseados em projeto interno anterior do autor —
   schema validado em uso interno.

Todas as fontes acima estão sob licença MIT compatível.
```

- [ ] **Step 3: Criar `README.md` (versão inicial mínima)**

```markdown
# plugadvpl

Plugin Claude Code + CLI Python que indexa fontes ADVPL/TLPP em SQLite e
permite ao Claude consultar metadados (funções, tabelas, MV_*, call graph,
SQL embedado) **antes** de abrir arquivos `.prw` inteiros, economizando
10–15× tokens em projetos Protheus.

## Status

Em desenvolvimento (v0.1.0 não publicada ainda).

## Quick start (quando lançado)

```bash
# 1. Instalar uv (se não tiver)
winget install astral-sh.uv   # Windows
# ou: curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Adicionar marketplace do plugin no Claude Code
/plugin marketplace add github.com/<owner>/plugadvpl
/plugin install plugadvpl

# 3. Abrir projeto Protheus, executar:
/plugadvpl:init
/plugadvpl:ingest

# 4. Pronto. Claude agora usa o índice.
```

Ver `docs/superpowers/specs/2026-05-11-plugadvpl-design.md` para design completo.

## Licença

MIT. Ver [LICENSE](LICENSE) e [NOTICE](NOTICE).
```

- [ ] **Step 4: Criar `CHANGELOG.md`**

```markdown
# Changelog

Todas as mudanças notáveis estão documentadas aqui, seguindo [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Estrutura inicial do projeto (mono-repo: plugin Claude Code + CLI Python).
```

- [ ] **Step 5: Criar `CONTRIBUTING.md`**

```markdown
# Contributing

## Setup local

```bash
git clone https://github.com/<owner>/plugadvpl
cd plugadvpl

# Instalar uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sincronizar deps de dev
uv sync --directory cli

# Rodar testes
cd cli && uv run pytest tests/unit tests/integration -v

# Testar plugin localmente
claude --plugin-dir .
```

## Fixtures locais (`pytest -m local`)

Os testes E2E em `cli/tests/e2e_local/` validam o ingest contra um diretório real de fontes ADVPL. Em CI esses testes são pulados automaticamente (marker `local` excluído via `addopts`). Para rodar localmente:

```bash
export PLUGADVPL_E2E_FONTES_DIR=/caminho/para/seus/fontes
export PLUGADVPL_E2E_BASELINE_DB=/caminho/para/baseline.db  # opcional
uv run pytest -m local
```

## Estilo

- `ruff format` (linhas ≤100)
- `ruff check`
- `mypy --strict`
- Mensagens de commit: Conventional Commits (`feat:`, `fix:`, `refactor:`, ...)
```

- [ ] **Step 6: Criar `CODE_OF_CONDUCT.md`** com Contributor Covenant 2.1 (copiar de https://www.contributor-covenant.org/version/2/1/code_of_conduct.txt)

- [ ] **Step 7: Criar `SECURITY.md`**

```markdown
# Security Policy

## Reportando uma vulnerabilidade

Email: <owner>@example.com (substitua antes do release).

Não abra issue público para vulnerabilidades. Resposta esperada: 7 dias úteis.

## Escopo

- CLI `plugadvpl` (parsing, ingest, queries) — em escopo
- Plugin Claude Code (markdown que invoca a CLI) — em escopo
- Índice gerado (`.plugadvpl/index.db`) — não em escopo (dados do usuário, não responsabilidade do projeto)

## Recomendações de uso

O índice contém nomes de tabelas, SQL e potenciais credenciais literais
do código do cliente. Recomenda-se:

- `.plugadvpl/` no `.gitignore` (default em `plugadvpl init`)
- Para projetos sensíveis: `plugadvpl ingest --no-content` (metadados-only,
  sem corpo de chunk)
- `plugadvpl ingest --redact-secrets` para mascarar URLs com credenciais
  e tokens hex longos
```

- [ ] **Step 8: Commit**

```bash
git add LICENSE NOTICE README.md CHANGELOG.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md
git commit -m "chore: add governance files (LICENSE, NOTICE, README, CHANGELOG, CONTRIBUTING, CoC, SECURITY)"
```

### Task 1.3: Estrutura de diretórios

- [ ] **Step 1: Criar diretórios com `.gitkeep`**

```bash
mkdir -p skills agents hooks
mkdir -p .claude-plugin
mkdir -p cli/plugadvpl/lookups
mkdir -p cli/plugadvpl/migrations
mkdir -p cli/plugadvpl/parsing
mkdir -p cli/tests/unit cli/tests/integration cli/tests/bench cli/tests/e2e_local
mkdir -p cli/tests/fixtures/synthetic cli/tests/fixtures/expected
mkdir -p scripts
mkdir -p .github/ISSUE_TEMPLATE .github/workflows

touch skills/.gitkeep agents/.gitkeep hooks/.gitkeep
touch cli/plugadvpl/lookups/.gitkeep cli/plugadvpl/migrations/.gitkeep cli/plugadvpl/parsing/.gitkeep
touch cli/tests/unit/.gitkeep cli/tests/integration/.gitkeep cli/tests/bench/.gitkeep cli/tests/e2e_local/.gitkeep
touch cli/tests/fixtures/synthetic/.gitkeep cli/tests/fixtures/expected/.gitkeep
touch scripts/.gitkeep .github/ISSUE_TEMPLATE/.gitkeep .github/workflows/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add skills agents hooks .claude-plugin cli scripts .github
git commit -m "chore: scaffold directory structure"
```

### Task 1.4: `.claude-plugin/plugin.json` e `marketplace.json`

- [ ] **Step 1: Criar `.claude-plugin/plugin.json`**

```json
{
  "name": "plugadvpl",
  "version": "0.1.0",
  "description": "Indexa fontes ADVPL/TLPP em SQLite + FTS5 para Claude consultar metadados antes de ler .prw cru (economiza 10-15x tokens)",
  "author": { "name": "<owner>" },
  "license": "MIT",
  "homepage": "https://github.com/<owner>/plugadvpl",
  "repository": "https://github.com/<owner>/plugadvpl",
  "keywords": ["advpl", "tlpp", "protheus", "totvs", "erp", "sqlite", "fts5", "claude-code-plugin"]
}
```

- [ ] **Step 2: Criar `.claude-plugin/marketplace.json`**

```json
{
  "name": "plugadvpl-marketplace",
  "owner": { "name": "<owner>" },
  "plugins": [
    {
      "name": "plugadvpl",
      "source": ".",
      "description": "Indexa fontes ADVPL/TLPP em SQLite + FTS5 para Claude consultar antes de ler arquivo cru"
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/
git commit -m "feat(plugin): add plugin.json and marketplace.json"
```

### Task 1.5: `cli/pyproject.toml` com hatchling + hatch-vcs

- [ ] **Step 1: Criar `cli/pyproject.toml`**

```toml
[project]
name = "plugadvpl"
dynamic = ["version"]
description = "CLI que indexa fontes ADVPL/Protheus em SQLite com FTS5 para análise por LLM (companheiro do plugin Claude Code plugadvpl)"
readme = "README.md"
license-files = ["../LICENSE", "../NOTICE"]
authors = [{ name = "<owner>", email = "<owner>@example.com" }]
requires-python = ">=3.11"
keywords = ["advpl", "tlpp", "protheus", "totvs", "sqlite", "fts5", "claude-code"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Code Generators",
    "Operating System :: OS Independent",
]
dependencies = [
    "typer >=0.15",
    "rich >=13.7",
    "chardet >=5.0",
    "psutil >=5.9",
]

[project.urls]
Homepage = "https://github.com/<owner>/plugadvpl"
Issues = "https://github.com/<owner>/plugadvpl/issues"
Source = "https://github.com/<owner>/plugadvpl"
Changelog = "https://github.com/<owner>/plugadvpl/blob/main/CHANGELOG.md"

[project.scripts]
plugadvpl = "plugadvpl.cli:main"

[dependency-groups]
dev = [
    "pytest >=8.0",
    "pytest-benchmark >=5.0",
    "pytest-cov >=5.0",
    "hypothesis >=6.100",
    "syrupy >=4.0",
    "ruff >=0.6",
    "mypy >=1.10",
]

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"
raw-options = { root = ".." }

[tool.hatch.build.hooks.vcs]
version-file = "plugadvpl/_version.py"

[tool.hatch.build.targets.wheel]
packages = ["plugadvpl"]

# Defensivo: garantir que SQL/JSON de migrations e lookups vão para o wheel.
# Hatchling inclui non-Python files dentro de packages por default, mas explícito
# evita acidentes em refactor futuro.
[tool.hatch.build.targets.wheel.force-include]
"plugadvpl/migrations" = "plugadvpl/migrations"
"plugadvpl/lookups" = "plugadvpl/lookups"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "RUF",
    "PTH",   # use pathlib em vez de os.path
    "RET",   # return values consistentes
    "ARG",   # unused arguments
    "TCH",   # imports apenas para type-checking → mover para TYPE_CHECKING block
    "PL",    # pylint subset (refactor, warnings, conventions)
]
ignore = ["E501", "PLR0913"]  # line-length pelo formatter; PLR0913=too-many-args (CLI tem flags demais por design)

[tool.ruff.format]
docstring-code-format = true   # formata exemplos de código dentro de docstrings

[tool.mypy]
strict = true
python_version = "3.11"
warn_unused_ignores = true
warn_return_any = true
warn_unreachable = true
enable_error_code = ["redundant-expr", "truthy-bool", "ignore-without-code"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "-m", "not local",
    "--strict-markers",
    "--cov=plugadvpl",
    "--cov-branch",
    "--cov-fail-under=80",
    "--cov-report=term-missing",
    "--cov-report=xml",   # para Codecov upload em CI
]
markers = [
    "local: testes que precisam de fixtures locais não distribuídas. Excluídos em CI. Veja CONTRIBUTING.md.",
    "slow: testes que demoram >1s. Rodar com -m slow para incluir.",
]
```

- [ ] **Step 2: Criar `cli/plugadvpl/__init__.py`**

```python
"""plugadvpl — CLI Python para indexar fontes ADVPL/TLPP do Protheus.

Companheiro do plugin Claude Code de mesmo nome. Ver:
https://github.com/<owner>/plugadvpl
"""

try:
    from plugadvpl._version import __version__
except ImportError:
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
```

- [ ] **Step 3: Criar `cli/plugadvpl/__main__.py`**

```python
"""Permite executar via `python -m plugadvpl`."""
from plugadvpl.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Criar `cli/plugadvpl/cli.py` (stub mínimo)**

```python
"""CLI entry point — wrapper typer."""
from __future__ import annotations

import typer

from plugadvpl import __version__

app = typer.Typer(
    name="plugadvpl",
    help="Indexa fontes ADVPL/TLPP em SQLite + FTS5.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Imprime versão da CLI."""
    typer.echo(f"plugadvpl {__version__}")


def main() -> None:
    """Entry point para `plugadvpl` console_script."""
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Criar `cli/README.md`**

```markdown
# plugadvpl (CLI Python)

CLI que indexa fontes ADVPL/TLPP em SQLite com FTS5. Companheiro do plugin
Claude Code de mesmo nome.

## Instalação

```bash
# Executar uma vez (cache uvx):
uvx plugadvpl@0.1.0 --help

# Ou instalar global (PATH):
uv tool install plugadvpl@0.1.0
plugadvpl --help
```

## Comandos principais

Ver `plugadvpl --help`. Documentação completa: `docs/cli-reference.md` no
repositório principal.
```

- [ ] **Step 6: Sincronizar deps**

Run:
```bash
cd cli
uv sync
```

Expected: cria `.venv/` em `cli/`, instala typer, rich, chardet, psutil, pytest, ruff, mypy, etc.

- [ ] **Step 7: Verificar que CLI executa**

Run:
```bash
cd cli
uv run plugadvpl version
```

Expected: `plugadvpl 0.0.0+dev` (ou similar; hatch-vcs sem tag ainda).

- [ ] **Step 8: Commit**

```bash
git add cli/pyproject.toml cli/plugadvpl/ cli/README.md
git commit -m "feat(cli): scaffold typer CLI with hatch-vcs version (stub)"
```

### Task 1.6: Makefile

- [ ] **Step 1: Criar `Makefile` na raiz**

```makefile
.PHONY: help test test-fast bench lint format type validate ingest-local install-dev

help:
	@echo "plugadvpl — comandos dev"
	@echo "  test         — pytest unit + integration"
	@echo "  test-fast    — pytest unit only (-x)"
	@echo "  bench        — pytest-benchmark"
	@echo "  lint         — ruff check"
	@echo "  format       — ruff format"
	@echo "  type         — mypy --strict"
	@echo "  validate     — lint + type + test + bench"
	@echo "  ingest-local — ingest em \$$PLUGADVPL_E2E_FONTES_DIR (local only)"
	@echo "  install-dev  — uv sync"

install-dev:
	cd cli && uv sync

test:
	cd cli && uv run pytest tests/unit tests/integration -v

test-fast:
	cd cli && uv run pytest tests/unit -v -x

bench:
	cd cli && uv run pytest tests/bench --benchmark-only

lint:
	cd cli && uv run ruff check .
	python scripts/validate_plugin.py

format:
	cd cli && uv run ruff format .

type:
	cd cli && uv run mypy plugadvpl/

validate: lint type test bench

ingest-local:
	cd cli && uv run plugadvpl ingest $$PLUGADVPL_E2E_FONTES_DIR --workers 8
```

- [ ] **Step 2: Commit**

```bash
git add Makefile
git commit -m "chore: add Makefile with dev commands"
```

**Fim do Chunk 1.** Repo tem estrutura completa, CLI stub executa, governança em ordem.

---

## Chunk 2: Schema SQLite + db.py

**Objetivo:** Implementar o módulo `db.py` que cria o banco com todas as 22 tabelas + FTS5 (índice principal + trigram) + 6 lookups (WITHOUT ROWID) + tabela auxiliar `fonte_tabela`. Aplica PRAGMAs corretos (page_size, WAL, journal_size_limit, mmap, busy_timeout), detecta network share e cai para journal DELETE quando necessário. Tudo testado.

**Files:**
- Create: `cli/plugadvpl/migrations/001_initial.sql`
- Create: `cli/plugadvpl/db.py`
- Create: `cli/tests/unit/test_db.py`

### Task 2.1: Migration SQL

- [ ] **Step 1: Criar `cli/plugadvpl/migrations/001_initial.sql`**

Conteúdo: copiar literalmente as definições da Seção 4 do spec (`docs/superpowers/specs/2026-05-11-plugadvpl-design.md`), nesta ordem:

1. PRAGMAs init-time (`page_size=8192`, `journal_mode=WAL`, `journal_size_limit=67108864`).
2. Tabela `fontes` (com `caminho_relativo UNIQUE`, deltas do plugin, índices).
3. Tabela `fonte_chunks` (com `linha_inicio/linha_fim`, `tipo_simbolo`, `classe`, `assinatura`, `funcao_norm`, índices incluindo `COLLATE NOCASE`).
4. Tabela `chamadas_funcao` (com `destino_norm`, índices COLLATE NOCASE).
5. Tabela `parametros_uso`, `perguntas_uso`, `operacoes_escrita`, `sql_embedado`, `funcao_docs`.
6. Tabelas nível 2: `rest_endpoints`, `http_calls`, `env_openers`, `log_calls`, `defines`.
7. Tabela `lint_findings`.
8. Tabela `fonte_tabela` (normalizada para lookup reverso, WITHOUT ROWID).
9. 6 lookups WITHOUT ROWID: `funcoes_nativas`, `funcoes_restritas`, `lint_rules`, `sql_macros`, `modulos_erp`, `pontos_entrada_padrao`.
10. Tabelas internas: `meta`, `ingest_progress`.
11. FTS5 `fonte_chunks_fts` (external content, tokenize com `tokenchars '_-'`).
12. FTS5 `fonte_chunks_fts_tri` (external content, tokenize trigram).

Header do arquivo:
```sql
-- plugadvpl — migration 001 (initial schema, MVP v0.1.0)
-- Schema baseado em projeto interno anterior do autor + deltas para uso como plugin local.
-- Total: 22 tabelas + 2 FTS5 virtuais. As 17 tabelas reservadas para Universo 2/3/aux
-- são criadas via migrations futuras (002+, v0.2+).
```

**Checklist de tabelas a criar (auto-verificável):**

Universo 1 — Fontes (8):
- [ ] `fontes` (com `caminho_relativo UNIQUE`, deltas, `mtime_ns`, `parser_version`)
- [ ] `fonte_chunks` (com `linha_inicio/linha_fim`, `tipo_simbolo`, `funcao_norm`)
- [ ] `chamadas_funcao` (com `destino_norm`, índices COLLATE NOCASE)
- [ ] `parametros_uso`
- [ ] `perguntas_uso`
- [ ] `operacoes_escrita`
- [ ] `sql_embedado`
- [ ] `funcao_docs`

Nível 2 — Extrações novas (5):
- [ ] `rest_endpoints`
- [ ] `http_calls`
- [ ] `env_openers`
- [ ] `log_calls`
- [ ] `defines`

Nível 3 — Lint (1):
- [ ] `lint_findings`

Normalizada (1):
- [ ] `fonte_tabela` (WITHOUT ROWID, PK composta arquivo+tabela+modo)

Lookups (6) — todas WITHOUT ROWID:
- [ ] `funcoes_nativas`
- [ ] `funcoes_restritas`
- [ ] `lint_rules`
- [ ] `sql_macros`
- [ ] `modulos_erp`
- [ ] `pontos_entrada_padrao`

Internas (2):
- [ ] `meta`
- [ ] `ingest_progress`

FTS5 (2 virtuais, não contadas nas 22):
- [ ] `fonte_chunks_fts` (`content='fonte_chunks'`, `tokenize="unicode61 remove_diacritics 2 tokenchars '_-'"`)
- [ ] `fonte_chunks_fts_tri` (`content='fonte_chunks'`, `tokenize='trigram'`)

**Total: 22 tabelas físicas + 2 FTS5 virtuais.** Antes de commit, rodar:

```bash
sqlite3 /tmp/test.db < cli/plugadvpl/migrations/001_initial.sql
sqlite3 /tmp/test.db ".tables"
# Deve listar todas as 22 + as 2 FTS5 (+ shadow tables como fonte_chunks_fts_data etc.)
```

- [ ] **Step 2: Commit**

```bash
git add cli/plugadvpl/migrations/001_initial.sql
git commit -m "feat(db): add migration 001 with full v0.1 schema"
```

### Task 2.2: `db.py` — função `_is_network_share`

- [ ] **Step 1: Escrever teste falhando**

Criar `cli/tests/unit/test_db.py`:

```python
"""Testes de cli/plugadvpl/db.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from plugadvpl.db import _is_network_share


class TestIsNetworkShare:
    def test_local_drive_windows(self) -> None:
        assert _is_network_share(Path("C:/Users/foo")) is False
        assert _is_network_share(Path("C:/Users/user/proj")) is False

    def test_unc_path_windows(self) -> None:
        assert _is_network_share(Path(r"\\server\share\folder")) is True
        assert _is_network_share(Path("//server/share/folder")) is True

    def test_local_unix(self) -> None:
        assert _is_network_share(Path("/home/user/project")) is False
        assert _is_network_share(Path("/var/tmp")) is False
```

- [ ] **Step 2: Rodar teste (deve falhar — módulo não existe)**

Run: `cd cli && uv run pytest tests/unit/test_db.py -v`
Expected: `ModuleNotFoundError: No module named 'plugadvpl.db'`

- [ ] **Step 3: Implementar `_is_network_share` em `cli/plugadvpl/db.py`**

```python
"""Banco de dados SQLite — abertura, PRAGMAs, migrations, network share detection."""
from __future__ import annotations

import sqlite3
from pathlib import Path


def _is_network_share(path: Path) -> bool:
    """Detecta se um path está em network share (SMB/CIFS/UNC).

    WAL não funciona em network filesystem (docs SQLite oficiais). Quando True,
    o init usa journal_mode=DELETE em vez de WAL.

    Detecta:
    - UNC paths: \\\\server\\share ou //server/share
    - Em Windows, mapped drive (Z: apontando para share) NÃO é detectado aqui
      por simplicidade — usuário recebe warning explícito se WAL falhar.
    """
    s = str(path)
    return s.startswith("\\\\") or s.startswith("//")
```

- [ ] **Step 4: Rodar teste (deve passar)**

Run: `cd cli && uv run pytest tests/unit/test_db.py::TestIsNetworkShare -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add cli/plugadvpl/db.py cli/tests/unit/test_db.py
git commit -m "feat(db): add _is_network_share helper with tests"
```

### Task 2.3: `db.py` — função `open_db` (cria + aplica PRAGMAs)

- [ ] **Step 1: Estender `test_db.py` com testes de `open_db`**

Adicionar ao arquivo:

```python
import sqlite3

from plugadvpl.db import open_db, SCHEMA_VERSION


class TestOpenDb:
    def test_open_db_creates_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        assert db_path.exists()
        conn.close()

    def test_open_db_applies_pragmas(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert conn.execute("PRAGMA synchronous").fetchone()[0] == 1  # NORMAL
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            assert conn.execute("PRAGMA temp_store").fetchone()[0] == 2   # MEMORY
            assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        finally:
            conn.close()

    def test_open_db_page_size_8192_on_new_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            assert conn.execute("PRAGMA page_size").fetchone()[0] == 8192
        finally:
            conn.close()

    def test_open_db_uses_delete_journal_on_network_share(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Forçar detecção como network share
        from plugadvpl import db as db_module
        monkeypatch.setattr(db_module, "_is_network_share", lambda _: True)

        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode in ("delete", "persist")
        finally:
            conn.close()
```

- [ ] **Step 2: Rodar (deve falhar)**

Run: `cd cli && uv run pytest tests/unit/test_db.py::TestOpenDb -v`
Expected: `ImportError: cannot import name 'open_db'`

- [ ] **Step 3: Implementar `open_db` em `db.py`**

Adicionar:

```python
SCHEMA_VERSION = "1"


def open_db(db_path: Path) -> sqlite3.Connection:
    """Abre/cria DB em db_path com PRAGMAs corretos.

    - Em DB novo: aplica page_size=8192 e journal_mode=WAL (persistidos no header)
    - Em network share: usa journal_mode=DELETE (WAL não funciona em SMB/CIFS)
    - Sempre aplica: synchronous=NORMAL, foreign_keys=ON, temp_store=MEMORY,
      mmap_size=256MB, cache_size=-20000, busy_timeout=5000
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not db_path.exists()
    conn = sqlite3.connect(str(db_path))

    if is_new:
        conn.execute("PRAGMA page_size = 8192")

    if _is_network_share(db_path.parent):
        conn.execute("PRAGMA journal_mode = DELETE")
    else:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA journal_size_limit = 67108864")

    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456")
    conn.execute("PRAGMA cache_size = -20000")
    conn.execute("PRAGMA busy_timeout = 5000")

    return conn
```

- [ ] **Step 4: Rodar testes**

Run: `cd cli && uv run pytest tests/unit/test_db.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add cli/plugadvpl/db.py cli/tests/unit/test_db.py
git commit -m "feat(db): implement open_db with PRAGMAs and network share fallback"
```

### Task 2.4: `db.py` — função `apply_migrations`

- [ ] **Step 1: Adicionar teste**

```python
class TestApplyMigrations:
    def test_apply_migrations_creates_tables(self, tmp_path: Path) -> None:
        from plugadvpl.db import apply_migrations
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            expected_core = {
                "fontes", "fonte_chunks", "chamadas_funcao", "parametros_uso",
                "perguntas_uso", "operacoes_escrita", "sql_embedado", "funcao_docs",
                "rest_endpoints", "http_calls", "env_openers", "log_calls", "defines",
                "lint_findings", "fonte_tabela",
                "funcoes_nativas", "funcoes_restritas", "lint_rules", "sql_macros",
                "modulos_erp", "pontos_entrada_padrao",
                "meta", "ingest_progress",
            }
            missing = expected_core - tables
            assert not missing, f"Tabelas faltando: {missing}"
        finally:
            conn.close()

    def test_apply_migrations_creates_fts5(self, tmp_path: Path) -> None:
        from plugadvpl.db import apply_migrations
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            # FTS5 aparece em sqlite_master como type='table' com sql que contém 'fts5'
            fts = list(conn.execute(
                "SELECT name FROM sqlite_master WHERE sql LIKE '%fts5%' AND type='table'"
            ))
            names = {r[0] for r in fts}
            assert "fonte_chunks_fts" in names
            assert "fonte_chunks_fts_tri" in names
        finally:
            conn.close()

    def test_apply_migrations_is_idempotent(self, tmp_path: Path) -> None:
        from plugadvpl.db import apply_migrations
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            apply_migrations(conn)  # 2ª vez não pode dar erro
            count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            assert count > 20
        finally:
            conn.close()
```

- [ ] **Step 2: Rodar (deve falhar)**

Run: `cd cli && uv run pytest tests/unit/test_db.py::TestApplyMigrations -v`
Expected: `ImportError`

- [ ] **Step 3: Implementar `apply_migrations`**

Adicionar em `db.py`:

```python
import importlib.resources as ir


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Aplica todas as migrations da pasta `migrations/` em ordem.

    Migrations são .sql files numerados (001_initial.sql, 002_xxx.sql, ...).
    Cada arquivo é idempotente (usa CREATE TABLE IF NOT EXISTS, etc.).
    """
    migrations_dir = ir.files("plugadvpl") / "migrations"
    sql_files = sorted(
        f for f in migrations_dir.iterdir() if f.name.endswith(".sql")
    )
    for sql_file in sql_files:
        sql = sql_file.read_text(encoding="utf-8")
        conn.executescript(sql)
    conn.commit()
```

- [ ] **Step 4: Rodar testes**

Run: `cd cli && uv run pytest tests/unit/test_db.py -v`
Expected: 10 passed (todos os tests anteriores + 3 novos)

- [ ] **Step 5: Commit**

```bash
git add cli/plugadvpl/db.py cli/tests/unit/test_db.py
git commit -m "feat(db): implement apply_migrations from .sql files"
```

### Task 2.5: `db.py` — funções `init_meta`, `get_meta`, `set_meta`

- [ ] **Step 1: Adicionar testes**

```python
class TestMeta:
    def test_init_meta_writes_defaults(self, tmp_path: Path) -> None:
        from plugadvpl.db import apply_migrations, init_meta, get_meta
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            init_meta(conn, project_root=str(tmp_path), cli_version="0.1.0")
            assert get_meta(conn, "schema_version") == SCHEMA_VERSION
            assert get_meta(conn, "plugadvpl_version") == "0.1.0"
            assert get_meta(conn, "project_root") == str(tmp_path)
            assert get_meta(conn, "encoding_policy") == "preserve"
        finally:
            conn.close()

    def test_get_meta_returns_none_for_missing(self, tmp_path: Path) -> None:
        from plugadvpl.db import apply_migrations, get_meta
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            assert get_meta(conn, "nonexistent") is None
        finally:
            conn.close()

    def test_set_meta_upserts(self, tmp_path: Path) -> None:
        from plugadvpl.db import apply_migrations, set_meta, get_meta
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            set_meta(conn, "test_key", "value1")
            set_meta(conn, "test_key", "value2")  # upsert
            assert get_meta(conn, "test_key") == "value2"
        finally:
            conn.close()
```

- [ ] **Step 2: Rodar (falha)**

- [ ] **Step 3: Implementar em `db.py`**

```python
def init_meta(conn: sqlite3.Connection, *, project_root: str, cli_version: str) -> None:
    """Grava linhas obrigatórias em `meta` (idempotente via UPSERT)."""
    defaults = {
        "schema_version": SCHEMA_VERSION,
        "plugadvpl_version": cli_version,
        "project_root": project_root,
        "encoding_policy": "preserve",
    }
    for k, v in defaults.items():
        set_meta(conn, k, v)


def get_meta(conn: sqlite3.Connection, chave: str) -> str | None:
    row = conn.execute("SELECT valor FROM meta WHERE chave=?", (chave,)).fetchone()
    return row[0] if row else None


def set_meta(conn: sqlite3.Connection, chave: str, valor: str) -> None:
    conn.execute(
        "INSERT INTO meta (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
        (chave, valor),
    )
    conn.commit()
```

- [ ] **Step 4: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_db.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add cli/plugadvpl/db.py cli/tests/unit/test_db.py
git commit -m "feat(db): add init_meta/get_meta/set_meta helpers"
```

### Task 2.6: `db.py` — função `close_db` com `PRAGMA optimize` e `wal_checkpoint`

- [ ] **Step 1: Adicionar teste**

```python
class TestCloseDb:
    def test_close_db_truncates_wal(self, tmp_path: Path) -> None:
        from plugadvpl.db import close_db, apply_migrations
        db_path = tmp_path / "test.db"
        conn = open_db(db_path)
        try:
            apply_migrations(conn)
            conn.execute("INSERT INTO meta (chave, valor) VALUES ('test', 'data')")
            conn.commit()
        finally:
            close_db(conn)
        # Depois de fechar com checkpoint TRUNCATE, .db-wal deve estar pequeno ou ausente
        wal_path = db_path.with_suffix(".db-wal")
        if wal_path.exists():
            assert wal_path.stat().st_size < 100  # apenas header
```

- [ ] **Step 2: Implementar**

```python
def close_db(conn: sqlite3.Connection) -> None:
    """Fecha conexão com checkpoint e optimize (recomendação oficial >=3.46)."""
    try:
        # PRAGMA optimize: rodar antes de fechar (sqlite.org/pragma.html#pragma_optimize)
        conn.execute("PRAGMA optimize")
        # WAL checkpoint TRUNCATE: força sync e trunca .db-wal
        if conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal":
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 3: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_db.py -v`
Expected: 14 passed

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/db.py cli/tests/unit/test_db.py
git commit -m "feat(db): add close_db with optimize + wal_checkpoint"
```

**Fim do Chunk 2.** Schema completo, todas as funções de DB testadas e funcionando.

---

## Chunk 3: Parser core (strip-first + extrações de fontes)

**Objetivo:** Implementar `parsing/stripper.py` (mini-tokenizer que substitui comentários e strings por espaços) e `parsing/parser.py` com as extrações fundamentais portadas do parser interno anterior do autor: funções, tabelas (read/write/reclock), campos, MV_, SX1, includes, calls (U_, ExecBlock, MsExecAuto, FWLoadModel, FWExecView, METHOD). Cada extração tem suite unitária com fixtures sintéticas.

**Files:**
- Create: `cli/plugadvpl/parsing/__init__.py`
- Create: `cli/plugadvpl/parsing/stripper.py`
- Create: `cli/plugadvpl/parsing/parser.py`
- Create: `cli/tests/unit/test_stripper.py`
- Create: `cli/tests/unit/test_parser.py`

### Task 3.1: `stripper.py` — substituir comentários e strings por espaços

- [ ] **Step 1: Criar `cli/tests/unit/test_stripper.py` com testes mínimos**

```python
"""Testes do mini-tokenizer (strip_advpl).

Princípio: substituir comentários (//, /* */) e strings (",') por espaços,
preservando newlines e contagem de linhas/offsets.
"""
from __future__ import annotations

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
```

- [ ] **Step 2: Rodar (falha — módulo não existe)**

Run: `cd cli && uv run pytest tests/unit/test_stripper.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Criar `cli/plugadvpl/parsing/__init__.py` vazio**

- [ ] **Step 4: Implementar `stripper.py`**

```python
"""Mini-tokenizer: substitui comentários e strings por espaços, preservando offsets.

Roda antes das regex de extração para evitar falso-positivos em código comentado
ou dentro de strings literais. Padrão da indústria (ProLeap COBOL faz idem).
"""
from __future__ import annotations


def strip_advpl(content: str) -> str:
    """Retorna content com comentários (// e /* */) e strings ("...", '...') substituídos por espaços.

    Preserva:
    - Tamanho total (len(out) == len(content))
    - Newlines e contagem de linhas
    - Offsets de tokens não-comentário (regex pode usar match.start() na saída e
      mapear de volta para a posição original sem ajuste)

    Limitações:
    - Macros `&var.` (substituição runtime) não são resolvidas — impossível estaticamente
    - Não detecta strings raw/multilinha (ADVPL não tem)
    """
    out: list[str] = []
    i, n = 0, len(content)
    state = "code"
    while i < n:
        c = content[i]
        if state == "code":
            if c == "/" and i + 1 < n and content[i + 1] == "/":
                state = "line_comment"
                out.append("  ")
                i += 2
                continue
            if c == "/" and i + 1 < n and content[i + 1] == "*":
                state = "block_comment"
                out.append("  ")
                i += 2
                continue
            if c == '"':
                state = "str_dq"
                out.append(" ")
                i += 1
                continue
            if c == "'":
                state = "str_sq"
                out.append(" ")
                i += 1
                continue
            out.append(c)
        elif state == "line_comment":
            if c == "\n":
                state = "code"
                out.append("\n")
            else:
                out.append(" ")
        elif state == "block_comment":
            if c == "*" and i + 1 < n and content[i + 1] == "/":
                state = "code"
                out.append("  ")
                i += 2
                continue
            out.append(" " if c != "\n" else "\n")
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
        i += 1
    return "".join(out)
```

- [ ] **Step 5: Rodar testes**

Run: `cd cli && uv run pytest tests/unit/test_stripper.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add cli/plugadvpl/parsing/ cli/tests/unit/test_stripper.py
git commit -m "feat(parser): add strip_advpl mini-tokenizer (strip-first pattern)"
```

### Task 3.2: `parser.py` — `read_file` com fast-path cp1252

- [ ] **Step 1: Criar `cli/tests/unit/test_parser.py`**

```python
"""Testes de cli/plugadvpl/parsing/parser.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from plugadvpl.parsing.parser import read_file


class TestReadFile:
    def test_cp1252_fast_path(self, tmp_path: Path) -> None:
        f = tmp_path / "test.prw"
        f.write_bytes("cNome := \"João\"".encode("cp1252"))
        content, encoding = read_file(f)
        assert content == 'cNome := "João"'
        assert encoding == "cp1252"

    def test_utf8_fallback(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tlpp"
        # 字 (caracter chinês) não cabe em cp1252
        f.write_text('cNome := "字"', encoding="utf-8")
        content, encoding = read_file(f)
        assert "字" in content
        assert encoding == "utf-8"

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.prw"
        f.write_bytes(b"")
        content, encoding = read_file(f)
        assert content == ""
```

- [ ] **Step 2: Implementar `read_file` em `cli/plugadvpl/parsing/parser.py`**

```python
"""Parser ADVPL — extrações por regex sobre conteúdo strip-first.

Portado e adaptado de parser interno anterior do autor
(validado em aproximadamente 2.000 fontes ADVPL).
"""
from __future__ import annotations

import re
from pathlib import Path

import chardet


def read_file(file_path: Path) -> tuple[str, str]:
    """Lê arquivo ADVPL e retorna (content, encoding_detected).

    Fast path: tenta cp1252 (99% dos fontes Protheus). Fallback utf-8, depois chardet.
    """
    raw = file_path.read_bytes()
    if not raw:
        return "", "cp1252"
    try:
        return raw.decode("cp1252"), "cp1252"
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    detected = chardet.detect(raw[:4096])
    encoding = detected.get("encoding") or "latin-1"
    try:
        return raw.decode(encoding), encoding
    except (UnicodeDecodeError, LookupError):
        return raw.decode("latin-1"), "latin-1"
```

- [ ] **Step 3: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_parser.py -v`
Expected: 3 passed

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/parsing/parser.py cli/tests/unit/test_parser.py
git commit -m "feat(parser): add read_file with cp1252 fast-path + chardet fallback"
```

### Task 3.3: `parser.py` — `extract_functions` (User/Static/Main/WSMETHOD/METHOD)

- [ ] **Step 1: Adicionar testes**

```python
from plugadvpl.parsing.parser import extract_functions


class TestExtractFunctions:
    def test_user_function(self) -> None:
        src = "User Function FATA050()\nReturn .T."
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "FATA050" in names

    def test_static_function(self) -> None:
        src = "Static Function ValidaCampo(cCpo)\nReturn .T."
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "ValidaCampo" in names

    def test_main_function(self) -> None:
        src = "Main Function JobX()\nReturn"
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "JobX" in names

    def test_wsmethod(self) -> None:
        src = "WSMETHOD GET clientes WSSERVICE Vendas\nReturn"
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "clientes" in names

    def test_method_class(self) -> None:
        src = "METHOD New(cArg) CLASS Pedido\nReturn Self"
        result = extract_functions(src)
        funs = [(f["nome"], f.get("classe")) for f in result]
        assert ("New", "Pedido") in funs

    def test_ignores_function_in_comment(self) -> None:
        # Confirma que strip_advpl está sendo aplicado antes
        src = "// User Function CommentedOut()\nUser Function Real()\nReturn"
        result = extract_functions(src)
        names = [f["nome"] for f in result]
        assert "Real" in names
        assert "CommentedOut" not in names

    def test_returns_line_numbers(self) -> None:
        src = "// linha 1\nUser Function Foo()\nReturn .T.\n\nUser Function Bar()\nReturn .F."
        result = extract_functions(src)
        by_name = {f["nome"]: f for f in result}
        assert by_name["Foo"]["linha_inicio"] == 2
        assert by_name["Bar"]["linha_inicio"] == 5
```

- [ ] **Step 2: Implementar**

Adicionar em `parser.py`:

```python
from plugadvpl.parsing.stripper import strip_advpl

# Regexes pre-compilados em module-level (workers podem importar)
_FUNCTION_RE = re.compile(
    r"^\s*(?:(Static|User|Main)\s+)?Function\s+(\w+)",
    re.IGNORECASE | re.MULTILINE,
)
_WSMETHOD_RE = re.compile(
    r"^\s*WSMETHOD\s+(GET|POST|PUT|DELETE)?\s*(\w+)\s+WS(?:RECEIVE|SEND|SERVICE)",
    re.IGNORECASE | re.MULTILINE,
)
_METHOD_RE = re.compile(
    r"^\s*METHOD\s+(\w+)\s*\([^)]*\)\s*CLASS\s+(\w+)",
    re.IGNORECASE | re.MULTILINE,
)


def _line_at(content: str, offset: int) -> int:
    """Retorna a linha 1-based do offset."""
    return content.count("\n", 0, offset) + 1


def extract_functions(content: str) -> list[dict]:
    """Extrai todas as funções declaradas no fonte.

    Retorna lista de dicts com: nome, kind, classe, linha_inicio.
    Aplica strip_advpl primeiro para ignorar comentários e strings.
    """
    stripped = strip_advpl(content)
    result: list[dict] = []
    seen_offsets: set[int] = set()

    for m in _FUNCTION_RE.finditer(stripped):
        kind_raw = (m.group(1) or "function").lower()
        kind = {
            "user": "user_function",
            "static": "static_function",
            "main": "main_function",
            "function": "function",
        }[kind_raw]
        result.append(
            {
                "nome": m.group(2),
                "kind": kind,
                "classe": "",
                "linha_inicio": _line_at(stripped, m.start()),
                "_offset": m.start(),
            }
        )
        seen_offsets.add(m.start())

    for m in _WSMETHOD_RE.finditer(stripped):
        result.append(
            {
                "nome": m.group(2),
                "kind": "ws_method",
                "classe": "",
                "linha_inicio": _line_at(stripped, m.start()),
                "_offset": m.start(),
            }
        )

    for m in _METHOD_RE.finditer(stripped):
        result.append(
            {
                "nome": m.group(1),
                "kind": "method",
                "classe": m.group(2),
                "linha_inicio": _line_at(stripped, m.start()),
                "_offset": m.start(),
            }
        )

    result.sort(key=lambda f: f["_offset"])
    return result
```

- [ ] **Step 3: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_parser.py -v`
Expected: 10 passed

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/parsing/parser.py cli/tests/unit/test_parser.py
git commit -m "feat(parser): add extract_functions (User/Static/Main/WSMETHOD/METHOD)"
```

### Task 3.4: `parser.py` — `add_function_ranges` (linha_inicio + linha_fim por offset da próxima)

- [ ] **Step 1: Adicionar teste**

```python
from plugadvpl.parsing.parser import add_function_ranges


class TestAddFunctionRanges:
    def test_ranges_set_from_next_function(self) -> None:
        src = (
            "User Function A()\n"        # linha 1
            "  Local x := 1\n"            # 2
            "Return x\n"                  # 3
            "\n"                          # 4
            "User Function B()\n"        # 5
            "Return .T.\n"                # 6
        )
        funcs = extract_functions(src)
        funcs = add_function_ranges(funcs, src)
        by_name = {f["nome"]: f for f in funcs}
        assert by_name["A"]["linha_inicio"] == 1
        assert by_name["A"]["linha_fim"] == 4  # antes do header de B
        assert by_name["B"]["linha_inicio"] == 5
        assert by_name["B"]["linha_fim"] == 6  # última linha do arquivo
```

- [ ] **Step 2: Implementar**

```python
def add_function_ranges(funcs: list[dict], content: str) -> list[dict]:
    """Preenche linha_fim para cada função baseado no offset da próxima.

    Padrão: fim = linha do header da próxima função - 1. Para a última, fim = última linha do arquivo.
    """
    if not funcs:
        return funcs
    total_lines = content.count("\n") + 1
    for i, f in enumerate(funcs):
        if i + 1 < len(funcs):
            next_line = funcs[i + 1]["linha_inicio"]
            f["linha_fim"] = max(f["linha_inicio"], next_line - 1)
        else:
            f["linha_fim"] = total_lines
        f.pop("_offset", None)
    return funcs
```

- [ ] **Step 3: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_parser.py::TestAddFunctionRanges -v`
Expected: 1 passed

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/parsing/parser.py cli/tests/unit/test_parser.py
git commit -m "feat(parser): add add_function_ranges for linha_fim computation"
```

### Task 3.5: `parser.py` — `extract_tables` (read/write/reclock separados)

- [ ] **Step 1: Adicionar testes**

```python
from plugadvpl.parsing.parser import extract_tables


class TestExtractTables:
    def test_dbselectarea(self) -> None:
        src = 'DbSelectArea("SA1")'
        tables = extract_tables(src)
        assert "SA1" in tables["read"]

    def test_alias_arrow_read(self) -> None:
        src = "cNome := SA1->A1_NOME"
        tables = extract_tables(src)
        assert "SA1" in tables["read"]

    def test_xfilial_read(self) -> None:
        src = 'cFil := xFilial("SC5")'
        tables = extract_tables(src)
        assert "SC5" in tables["read"]

    def test_reclock_write(self) -> None:
        src = 'RecLock("SA1", .T.)\nReplace A1_NOME With "X"\nMsUnlock()'
        tables = extract_tables(src)
        assert "SA1" in tables["reclock"]
        assert "SA1" in tables["write"]

    def test_dbappend_write(self) -> None:
        src = "SA1->(dbAppend())"
        tables = extract_tables(src)
        assert "SA1" in tables["write"]

    def test_custom_table_za1(self) -> None:
        src = "DbSelectArea('ZA1')"
        tables = extract_tables(src)
        assert "ZA1" in tables["read"]

    def test_ignores_invalid_table_codes(self) -> None:
        src = 'cFoo := "ABC"->bar'
        tables = extract_tables(src)
        assert "ABC" not in tables["read"]  # ABC não é código Protheus válido
```

- [ ] **Step 2: Implementar**

```python
_DBSELECT_RE = re.compile(r'DbSelectArea\s*\(\s*["\'](\w{2,3})["\']', re.IGNORECASE)
_XFILIAL_RE = re.compile(
    r'(?:xFilial|FwxFilial|Posicione|MsSeek|dbSetOrder|ChkFile)\s*\(\s*["\'](\w{2,3})["\']',
    re.IGNORECASE,
)
_ALIAS_ARROW_RE = re.compile(r"\b([SZQNDM][A-Z][0-9A-Z])\s*->", re.IGNORECASE)
_RECLOCK_RE = re.compile(r'RecLock\s*\(\s*["\'](\w{2,3})["\']', re.IGNORECASE)
_RECLOCK_ALIAS_RE = re.compile(r"(\w{2,3})\s*->\s*\(\s*RecLock", re.IGNORECASE)
_DBAPPEND_RE = re.compile(r"(\w{2,3})\s*->\s*\(\s*dbAppend", re.IGNORECASE)
_DBDELETE_RE = re.compile(r"(\w{2,3})\s*->\s*\(\s*dbDelete", re.IGNORECASE)


def _is_valid_protheus_table(name: str) -> bool:
    """Códigos válidos: 3 chars, [SZNQD] + letra + alfanumérico (SA1, ZA1, NDF, ...)."""
    if len(name) != 3:
        return False
    return name[0] in "SZNQD" and name[1].isalpha()


def extract_tables(content: str) -> dict[str, list[str]]:
    """Extrai tabelas referenciadas, separadas por modo (read/write/reclock).

    'write' inclui reclock (todas as escritas). 'reclock' é subconjunto (apenas RecLock).
    """
    stripped = strip_advpl(content)
    read: set[str] = set()
    write: set[str] = set()
    reclock: set[str] = set()

    for m in _DBSELECT_RE.finditer(stripped):
        read.add(m.group(1).upper())
    for m in _XFILIAL_RE.finditer(stripped):
        read.add(m.group(1).upper())
    for m in _ALIAS_ARROW_RE.finditer(stripped):
        read.add(m.group(1).upper())

    for m in _RECLOCK_RE.finditer(stripped):
        t = m.group(1).upper()
        reclock.add(t)
        write.add(t)
    for m in _RECLOCK_ALIAS_RE.finditer(stripped):
        t = m.group(1).upper()
        reclock.add(t)
        write.add(t)
    for m in _DBAPPEND_RE.finditer(stripped):
        write.add(m.group(1).upper())
    for m in _DBDELETE_RE.finditer(stripped):
        write.add(m.group(1).upper())

    return {
        "read": sorted(t for t in read if _is_valid_protheus_table(t)),
        "write": sorted(t for t in write if _is_valid_protheus_table(t)),
        "reclock": sorted(t for t in reclock if _is_valid_protheus_table(t)),
    }
```

- [ ] **Step 3: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_parser.py::TestExtractTables -v`
Expected: 7 passed

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/parsing/parser.py cli/tests/unit/test_parser.py
git commit -m "feat(parser): add extract_tables (read/write/reclock split)"
```

### Task 3.6: `parser.py` — `extract_params` (MV_* com modo + default)

- [ ] **Step 1: Adicionar testes**

```python
from plugadvpl.parsing.parser import extract_params


class TestExtractParams:
    def test_supergetmv(self) -> None:
        src = 'cVal := SuperGetMV("MV_LOCALIZA", .F., "01")'
        params = extract_params(src)
        names = {(p["nome"], p["modo"]) for p in params}
        assert ("MV_LOCALIZA", "read") in names

    def test_getmv(self) -> None:
        src = 'cMoeda := GetMv("MV_SIMB1")'
        params = extract_params(src)
        names = {p["nome"] for p in params}
        assert "MV_SIMB1" in names

    def test_getnewpar(self) -> None:
        src = 'cVal := GetNewPar("MV_FOO", "default")'
        params = extract_params(src)
        names = {(p["nome"], p["default_decl"]) for p in params}
        assert ("MV_FOO", "default") in names

    def test_putmv_write(self) -> None:
        src = 'PutMV("MV_X", "newvalue")'
        params = extract_params(src)
        names = {(p["nome"], p["modo"]) for p in params}
        assert ("MV_X", "write") in names
```

- [ ] **Step 2: Implementar**

```python
_MV_READ_RE = re.compile(
    r'(?:SuperGetMV|GetMv|GetNewPar|GetMVDef|FWMVPar)\s*\(\s*["\'](MV_\w+)["\']'
    r'(?:\s*,\s*[^,)]+\s*,\s*["\']([^"\']*)["\'])?',
    re.IGNORECASE,
)
_MV_WRITE_RE = re.compile(
    r'(?:PutMV|PutMvFil)\s*\(\s*["\'](MV_\w+)["\']',
    re.IGNORECASE,
)


def extract_params(content: str) -> list[dict]:
    """Extrai usos de parâmetros MV_*. Retorna [{nome, modo, default_decl}]."""
    stripped = strip_advpl(content)
    by_name: dict[str, dict] = {}
    for m in _MV_READ_RE.finditer(stripped):
        nome = m.group(1).upper()
        default = m.group(2) or ""
        entry = by_name.setdefault(nome, {"nome": nome, "modo": "read", "default_decl": ""})
        if default and not entry["default_decl"]:
            entry["default_decl"] = default
    for m in _MV_WRITE_RE.finditer(stripped):
        nome = m.group(1).upper()
        if nome in by_name:
            by_name[nome]["modo"] = "read_write"
        else:
            by_name[nome] = {"nome": nome, "modo": "write", "default_decl": ""}
    return list(by_name.values())
```

- [ ] **Step 3: Rodar**

Run: `cd cli && uv run pytest tests/unit/test_parser.py::TestExtractParams -v`
Expected: 4 passed

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/parsing/parser.py cli/tests/unit/test_parser.py
git commit -m "feat(parser): add extract_params (MV_* with read/write/read_write + default)"
```

### Task 3.7: `parser.py` — extratores restantes

Cada sub-task abaixo segue o mesmo padrão TDD: (1) escrever testes em `test_parser.py` cobrindo caso feliz + 1 caso de "padrão em comentário não é capturado" (valida que strip-first roda antes da regex); (2) rodar testes e ver falha; (3) implementar regex pre-compilada em module-level top + função; (4) rodar testes e ver verde; (5) commit individual.

#### Task 3.7.1: `extract_perguntas`

- [ ] **Step 1: Test**

```python
from plugadvpl.parsing.parser import extract_perguntas


class TestExtractPerguntas:
    def test_pergunte(self) -> None:
        src = 'Pergunte("FAT050", .F.)'
        assert "FAT050" in extract_perguntas(src)

    def test_fwgetsx1(self) -> None:
        src = 'aGrp := FWGetSX1("FIN001")'
        assert "FIN001" in extract_perguntas(src)

    def test_ignores_in_comment(self) -> None:
        src = '// Pergunte("FAKE")\nPergunte("REAL", .F.)'
        result = extract_perguntas(src)
        assert "REAL" in result
        assert "FAKE" not in result
```

- [ ] **Step 2:** Rodar, ver falhar.
- [ ] **Step 3: Impl**

```python
_PERGUNTE_RE = re.compile(
    r'(?:Pergunte|FWGetSX1)\s*\(\s*["\'](\w+)["\']',
    re.IGNORECASE,
)


def extract_perguntas(content: str) -> list[str]:
    stripped = strip_advpl(content)
    return sorted({m.group(1).upper() for m in _PERGUNTE_RE.finditer(stripped)})
```

- [ ] **Step 4:** Rodar, ver verde.
- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_perguntas (Pergunte/FWGetSX1)"
```

#### Task 3.7.2: `extract_includes`

- [ ] **Step 1: Test**

```python
from plugadvpl.parsing.parser import extract_includes


class TestExtractIncludes:
    def test_basic_include(self) -> None:
        src = '#Include "protheus.ch"\n#include \'topconn.ch\''
        result = extract_includes(src)
        assert "protheus.ch" in result
        assert "topconn.ch" in result

    def test_ignores_in_comment(self) -> None:
        src = '// #Include "fake.ch"\n#Include "real.ch"'
        result = extract_includes(src)
        assert "real.ch" in result
        assert "fake.ch" not in result
```

- [ ] **Step 2-4:** falha → impl → verde

```python
_INCLUDE_RE = re.compile(r'^\s*#Include\s+["\']([^"\']+)["\']', re.IGNORECASE | re.MULTILINE)


def extract_includes(content: str) -> list[str]:
    stripped = strip_advpl(content)
    return sorted({m.group(1) for m in _INCLUDE_RE.finditer(stripped)})
```

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_includes"
```

#### Task 3.7.3: `extract_calls_user_func` (`U_xxx`)

- [ ] **Step 1: Test**

```python
from plugadvpl.parsing.parser import extract_calls_user_func


class TestExtractCallsUserFunc:
    def test_basic_call(self) -> None:
        src = "U_FATA060()"
        calls = extract_calls_user_func(src)
        names = [c["destino"] for c in calls]
        assert "FATA060" in names

    def test_records_line(self) -> None:
        src = "Function X()\n  U_FOO()\nReturn"
        calls = extract_calls_user_func(src)
        assert calls[0]["linha_origem"] == 2

    def test_ignores_in_string(self) -> None:
        src = 'cMsg := "U_FAKE() blocked"'
        assert extract_calls_user_func(src) == []
```

- [ ] **Step 2-4:** falha → impl

```python
_CALL_U_RE = re.compile(r"\bU_(\w+)\s*\(", re.IGNORECASE)


def extract_calls_user_func(content: str) -> list[dict]:
    stripped = strip_advpl(content)
    result = []
    for m in _CALL_U_RE.finditer(stripped):
        result.append(
            {
                "destino": m.group(1).upper(),
                "tipo": "user_func",
                "linha_origem": _line_at(stripped, m.start()),
                "contexto": stripped[max(0, m.start() - 30) : m.end() + 30][:200],
            }
        )
    return result
```

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_calls_user_func"
```

#### Task 3.7.4: `extract_calls_execauto` (`MsExecAuto`)

- [ ] **Step 1: Test**

```python
class TestExtractCallsExecAuto:
    def test_execauto_with_rotina(self) -> None:
        src = 'MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCabec, aItens, 3)'
        result = extract_calls_execauto(src)
        assert any(c["destino"] == "MATA410" for c in result)
```

- [ ] **Step 2-4:** falha → impl

```python
_EXECAUTO_RE = re.compile(
    r"MsExecAuto\s*\(\s*\{\s*\|[^|]*\|\s*(\w+)\s*\(",
    re.IGNORECASE,
)


def extract_calls_execauto(content: str) -> list[dict]:
    stripped = strip_advpl(content)
    result = []
    for m in _EXECAUTO_RE.finditer(stripped):
        result.append(
            {
                "destino": m.group(1).upper(),
                "tipo": "execauto",
                "linha_origem": _line_at(stripped, m.start()),
                "contexto": stripped[max(0, m.start() - 30) : m.end() + 30][:200],
            }
        )
    return result
```

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_calls_execauto"
```

#### Task 3.7.5: `extract_calls_execblock` (`ExecBlock("PE", ...)`)

- [ ] **Step 1: Test**

```python
class TestExtractCallsExecBlock:
    def test_execblock(self) -> None:
        src = 'ExecBlock("MT410GRV", .F., .F.)'
        result = extract_calls_execblock(src)
        assert any(c["destino"] == "MT410GRV" for c in result)
```

- [ ] **Step 2-4:** falha → impl com `_EXECBLOCK_RE = re.compile(r'ExecBlock\s*\(\s*["\'](\w+)["\']', re.IGNORECASE)` e função análoga à 3.7.4 com `tipo="execblock"`.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_calls_execblock"
```

#### Task 3.7.6: `extract_calls_fwloadmodel`

- [ ] **Step 1: Test**

```python
class TestExtractCallsFWLoadModel:
    def test_fwloadmodel(self) -> None:
        src = 'oModel := FWLoadModel("MATA010")'
        result = extract_calls_fwloadmodel(src)
        assert any(c["destino"] == "MATA010" for c in result)
```

- [ ] **Step 2-4:** impl com `_FWLOADMODEL_RE = re.compile(r'FWLoadModel\s*\(\s*["\'](\w+)["\']', re.IGNORECASE)` e `tipo="fwloadmodel"`.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_calls_fwloadmodel"
```

#### Task 3.7.7: `extract_calls_fwexecview`

- [ ] **Step 1: Test**

```python
class TestExtractCallsFWExecView:
    def test_fwexecview(self) -> None:
        src = 'FWExecView("Cadastro Cliente", "MATA010", MODEL_OPERATION_INSERT, , {})'
        result = extract_calls_fwexecview(src)
        assert any(c["destino"] == "MATA010" for c in result)
```

- [ ] **Step 2-4:** impl com `_FWEXECVIEW_RE = re.compile(r'FWExecView\s*\([^,)]+,\s*["\'](\w+)["\']', re.IGNORECASE)` e `tipo="fwexecview"`.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_calls_fwexecview"
```

#### Task 3.7.8: `extract_calls_method`

- [ ] **Step 1: Test**

```python
class TestExtractCallsMethod:
    def test_obj_method(self) -> None:
        src = "oModel:Activate()"
        result = extract_calls_method(src)
        assert any(c["destino"] == "oModel:Activate" for c in result)

    def test_self_method(self) -> None:
        src = "::Init()"
        result = extract_calls_method(src)
        assert any("Init" in c["destino"] for c in result)
```

- [ ] **Step 2-4:** impl com 2 regex (object e self) e `tipo="method"`. **Atenção:** método tem MUITO false-positive — limitar a casos `\w+:\w+\s*\(` e `::\w+\s*\(`.

```python
_METHOD_OBJ_RE = re.compile(r"\b(\w+:\w+)\s*\(", re.IGNORECASE)
_METHOD_SELF_RE = re.compile(r"::(\w+)\s*\(", re.IGNORECASE)
```

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_calls_method (obj:m and ::m)"
```

#### Task 3.7.9: `extract_fields_ref`

- [ ] **Step 1: Test**

```python
from plugadvpl.parsing.parser import extract_fields_ref


class TestExtractFieldsRef:
    def test_alias_arrow_field(self) -> None:
        src = "cNome := SA1->A1_NOME"
        assert "A1_NOME" in extract_fields_ref(src)

    def test_replace_field(self) -> None:
        src = 'Replace A1_NOME With "X"'
        assert "A1_NOME" in extract_fields_ref(src)

    def test_ignores_invalid_field_pattern(self) -> None:
        src = "x := abc_def"  # não é padrão XX_NOME ADVPL
        assert "ABC_DEF" not in extract_fields_ref(src)
```

- [ ] **Step 2-4:** impl

```python
_FIELD_ARROW_RE = re.compile(r"\w{2,3}->([A-Z][A-Z0-9]_\w+)", re.IGNORECASE)
_FIELD_REPLACE_RE = re.compile(r"\bReplace\s+([A-Z][A-Z0-9]_\w+)", re.IGNORECASE)


def extract_fields_ref(content: str) -> list[str]:
    stripped = strip_advpl(content)
    fields: set[str] = set()
    for m in _FIELD_ARROW_RE.finditer(stripped):
        fields.add(m.group(1).upper())
    for m in _FIELD_REPLACE_RE.finditer(stripped):
        fields.add(m.group(1).upper())
    return sorted(fields)
```

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(parser): add extract_fields_ref"
```

### Task 3.8: `parser.py` — função orquestradora `parse_source`

- [ ] **Step 1: Teste de integração**

```python
class TestParseSource:
    def test_parse_returns_dict_with_all_fields(self, tmp_path: Path) -> None:
        f = tmp_path / "FATA050.prw"
        f.write_bytes(
            b'#Include "protheus.ch"\n'
            b'User Function FATA050()\n'
            b'  Local cMV := SuperGetMV("MV_LOCALIZA", .F., "")\n'
            b'  DbSelectArea("SC5")\n'
            b'  RecLock("SC5", .T.)\n'
            b'  Replace C5_NUM With "001"\n'
            b'  MsUnlock()\n'
            b'  U_FATA060()\n'
            b'Return .T.'
        )
        from plugadvpl.parsing.parser import parse_source
        result = parse_source(f)
        assert result["arquivo"] == "FATA050.prw"
        assert result["encoding"] == "cp1252"
        assert "FATA050" in [fn["nome"] for fn in result["funcoes"]]
        assert "SC5" in result["tabelas_ref"]["read"]
        assert "SC5" in result["tabelas_ref"]["write"]
        assert "MV_LOCALIZA" in [p["nome"] for p in result["parametros_uso"]]
        assert any(c["destino"] == "FATA060" for c in result["chamadas"])
        assert "protheus.ch" in result["includes"]
        # Hash deve estar populado (usado para stale detection — spec §11.2 #23)
        assert result["hash"]
        assert len(result["hash"]) == 40  # SHA-1 hex

    def test_hash_is_stable_for_same_content(self, tmp_path: Path) -> None:
        """Mesmo bytes → mesmo hash (necessário para incremental e UPSERT WHERE hash != old)."""
        from plugadvpl.parsing.parser import parse_source
        f1 = tmp_path / "a.prw"
        f2 = tmp_path / "b.prw"
        bytes_ = b'User Function X()\nReturn .T.'
        f1.write_bytes(bytes_)
        f2.write_bytes(bytes_)
        r1 = parse_source(f1)
        r2 = parse_source(f2)
        assert r1["hash"] == r2["hash"]

    def test_hash_differs_for_different_content(self, tmp_path: Path) -> None:
        from plugadvpl.parsing.parser import parse_source
        f1 = tmp_path / "a.prw"
        f2 = tmp_path / "b.prw"
        f1.write_bytes(b"User Function A()\nReturn")
        f2.write_bytes(b"User Function B()\nReturn")
        assert parse_source(f1)["hash"] != parse_source(f2)["hash"]
```

- [ ] **Step 2: Implementar**

```python
def parse_source(file_path: Path) -> dict:
    """Orquestra todas as extrações sobre um fonte. Retorna dict completo."""
    content, encoding = read_file(file_path)
    if not content:
        return {
            "arquivo": file_path.name,
            "caminho": str(file_path),
            "encoding": encoding,
            "lines_of_code": 0,
            "funcoes": [],
            "tabelas_ref": {"read": [], "write": [], "reclock": []},
            "parametros_uso": [],
            "perguntas_uso": [],
            "includes": [],
            "chamadas": [],
            "campos_ref": [],
            "hash": "",
        }
    import hashlib

    funcs = extract_functions(content)
    funcs = add_function_ranges(funcs, content)

    return {
        "arquivo": file_path.name,
        "caminho": str(file_path),
        "encoding": encoding,
        "lines_of_code": content.count("\n") + 1,
        "funcoes": funcs,
        "tabelas_ref": extract_tables(content),
        "parametros_uso": extract_params(content),
        "perguntas_uso": extract_perguntas(content),
        "includes": extract_includes(content),
        "chamadas": (
            extract_calls_user_func(content)
            + extract_calls_execauto(content)
            + extract_calls_execblock(content)
            + extract_calls_fwloadmodel(content)
            + extract_calls_fwexecview(content)
            + extract_calls_method(content)
        ),
        "campos_ref": extract_fields_ref(content),
        "hash": hashlib.sha1(content.encode(encoding, errors="replace")).hexdigest(),
    }
```

- [ ] **Step 3: Rodar testes**

Run: `cd cli && uv run pytest tests/unit/test_parser.py -v`
Expected: todos passam (~30 testes)

- [ ] **Step 4: Commit**

```bash
git add cli/plugadvpl/parsing/parser.py cli/tests/unit/test_parser.py
git commit -m "feat(parser): add parse_source orchestrator"
```

**Fim do Chunk 3.** Parser core completo, ~30 testes verdes.

---

## Chunks restantes — placeholders

Os chunks abaixo seguem o mesmo padrão (testes → implementação → commit). Vou expandi-los em arquivos separados para manter este plano gerenciável (cada chunk fica em ~600 linhas).

### Chunk 4: Parser avançado

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk04.md` (a criar)

Cobre:
- Detecção de capabilities (MVC, BROWSE, JOB, RPC, WS-REST, WS-SOAP, PE, WEBVIEW, SCHEDULE, WORKFLOW, COMPATIBILIZADOR, TESTE_UNITARIO, REPORT_TR, REST_CLIENT, EXEC_AUTO_CALLER, ENV_OPENER, JSON_AWARE, MULTI_FILIAL)
- `extract_rest_endpoints` (WSMETHOD GET/POST com path + annotation `@Get`/`@Post`)
- `extract_http_calls` (HttpPost/HttpGet/HttpsPost/MsAGetUrl)
- `extract_env_openers` (RpcSetEnv com empresa/filial/env)
- `extract_log_calls` (FwLogMsg com severity, ConOut)
- `extract_defines` (#DEFINE)
- `extract_mvc_hooks` (bCommit/bTudoOk/bLineOk/bPosVld/bPreVld em chamadas)
- `extract_ws_structures` (WSSTRUCT/WSSERVICE/WSMETHOD com WSDATA fields)
- `extract_namespace` (TLPP `Namespace x.y.z`)
- `extract_sql_embedado` (BeginSQL/EndSQL, TCQuery, TCSqlExec)

### Chunk 5: Lint 13 regras single-file

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk05.md`

Cobre `parser_lint.py` com função `lint_source(parsed, content) -> list[Finding]` que aplica as 13 detecções:

- BP-001: RecLock sem MsUnlock no escopo
- BP-002: BEGIN TRANSACTION sem END TRANSACTION
- BP-003: MsExecAuto sem check lMsErroAuto nas próximas N linhas
- BP-004: Pergunte sem variável de retorno
- BP-005: Função com >6 parâmetros
- BP-006: RecLock + DbRLock/dbAppend cru no mesmo bloco
- SEC-001: RpcSetEnv dentro de WSRESTFUL
- SEC-002: User Function sem prefixo de cliente (regex heurístico)
- PERF-001: SELECT *
- PERF-002: SQL sem %notDel%
- PERF-003: SQL sem %xfilial%
- MOD-001: ConOut em vez de FwLogMsg
- MOD-002: PUBLIC declarado

### Chunk 6: Lookup tables

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk06.md`

Cobre:
- `scripts/extract_lookups.py` — script que lê markdown do `advpl-specialist-main` e gera 6 JSONs
- `cli/plugadvpl/lookups/funcoes_nativas.json`
- `cli/plugadvpl/lookups/funcoes_restritas.json`
- `cli/plugadvpl/lookups/lint_rules.json`
- `cli/plugadvpl/lookups/sql_macros.json`
- `cli/plugadvpl/lookups/modulos_erp.json`
- `cli/plugadvpl/lookups/pontos_entrada_padrao.json`
- `db.py` recebe função `seed_lookups(conn, lookup_bundle_path)` que carrega JSONs e popula tabelas WITHOUT ROWID
- Computa `lookup_bundle_hash` e grava em `meta`

### Chunk 7: Ingest pipeline

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk07.md`

Cobre:
- `ingest.py` com `scan_files` (os.walk, filtro extensão `.prw/.tlpp/.prx/.apw`, dedup case-insensitive, **skip `.bak`/`.corrupted.bak`/`.old`/`.bak2`/`.tmp`**)
- `stale_filter` (mtime_ns + size_bytes + versões parser/lookup/schema)
- **Paralelização adaptativa corrigida** (após pesquisa: `re` stdlib NÃO libera GIL — Python bug 23690):
  - **single-thread** se ≤200 arquivos OR estimativa <2s total
  - **ProcessPoolExecutor** acima disso (única forma de paralelismo real para regex em CPython com GIL). ThreadPool foi removido da estratégia — não dá ganho para regex puro.
  - **`mp_context` por plataforma:** `fork` em Linux (mais leve), `spawn` em macOS (fork é "unsafe" desde Python 3.8 — emite warning) e Windows (não tem fork). Detectar:
    ```python
    import sys, multiprocessing as mp
    method = "fork" if sys.platform.startswith("linux") else "spawn"
    ctx = mp.get_context(method)
    pool = ProcessPoolExecutor(max_workers=N, mp_context=ctx)
    ```
  - Spawn overhead em Windows ~200ms/worker; manter threshold de 200 arquivos para compensar.
- Writer único enfileira via `queue.Queue` (SQLite é single-writer por design)
- Batch commit a cada 500–1000 chunks
- UPSERT `ON CONFLICT DO UPDATE SET ... WHERE excluded.hash != fontes.hash` (skip quando idêntico)
- FTS5 populate em massa via `INSERT INTO fonte_chunks_fts(fonte_chunks_fts) VALUES('rebuild')` (e idem `_tri`) ao final
- Reindex transacional por arquivo (DELETE FTS + DELETE deps + UPSERT + INSERT deps + INSERT FTS)
- Module detection (prefixo + tabelas — usa `modulos_erp` lookup populado em Chunk 6, **dependency order: 6 antes de 7**)
- **`caminho_relativo` sempre forward-slash:** usar `path.relative_to(root).as_posix()` antes de gravar no SQLite, garante consistência Win/Mac/Linux
- **`--no-content`** (spec §13.6): popula tudo exceto `fonte_chunks.content` (modo metadata-only para projetos sensíveis)
- **`--redact-secrets`** (spec §13.6): regex que detecta URLs com `user:pass@`, tokens hex >40 chars, `cKey := "..."` e substitui por `[REDACTED]` em snippets antes de gravar

**Dependency:** este chunk requer Chunk 6 completo (lookups seedadas) para que `detect_module` funcione.

### Chunk 8: Query layer + CLI typer

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk08.md`

Cobre:
- `query.py` com funções para cada subcomando (find_function, callers, callees, tables, param, arch, grep com 3 modos, lint, doctor)
- `output.py` com formatadores table/json/md, `--limit`, `--compact`, `--next-steps`
  - **Pattern obrigatório:** `Console(stderr=True)` para progress/tabelas/cores; `print(json.dumps(...))` puro para stdout. **NUNCA** usar `rich.print()` ou `Console()` (sem stderr) em stdout — vazaria ANSI quando Claude pipes o output. Rich auto-detecta `is_terminal` e suprime cores em pipe, mas usar stderr-only é mais defensivo.
- `cli.py` typer com:
  - 13 subcomandos via `@app.command()` (flat, não subgrupos — fonte: typer.tiangolo.com/tutorial/subcommands)
  - `@app.callback()` com `typer.Context` para opções globais `--root`, `--format`, `--quiet`, `--db`. Globais aparecem ANTES do subcomando: `plugadvpl --root /x find foo`
  - `--format` como `Enum(str, Enum)` (type-safe) ou `Literal["json","table","md"]`
  - `--limit`, `--offset`, `--compact`, `--no-content`, `--next-steps` como opções por-comando (cada um declara via `typer.Option`)

### Chunk 9: Skills de comando (13 SKILL.md)

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk09.md`

Cobre:
- Template de SKILL.md para slash command
- 13 SKILL.md (init, ingest, reindex, status, find, callers, callees, tables, param, arch, lint, doctor, help)
- Cada um com frontmatter `disable-model-invocation: true`, body que invoca `uvx plugadvpl@{{plugadvpl_version}} ...`
- Script `scripts/render_skill_templates.py` que substitui `{{plugadvpl_version}}` no build de release

### Chunk 10: Skills de conhecimento (10 SKILL.md)

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk10.md`

Cobre conteúdo das 10 skills temáticas (plugadvpl-index-usage, advpl-encoding, advpl-fundamentals, advpl-mvc, advpl-embedded-sql, advpl-matxfis, advpl-pontos-entrada, advpl-webservice, advpl-jobs-rpc, advpl-code-review).

### Chunk 11: Agents (4)

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk11.md`

Cobre os 4 agents conforme **spec §8**:

| Arquivo | Descrição |
|---|---|
| `agents/advpl-analyzer.md` | "explique como funciona X" — `arch → callers/callees → chunks → resumo` |
| `agents/advpl-impact-analyzer.md` | "se eu mudar X, o que quebra?" — `callers/tables/param` cruza dados |
| `agents/advpl-code-generator.md` | "crie User Function/MVC/REST/PE para X" — consulta skill apropriada + auto-lint |
| `agents/advpl-reviewer-bot.md` | "revise este código" — `arch + lint + restricted` + sugestão fix |

### Chunk 12: Hook session-start

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk12.md`

Cobre:
- `hooks/hooks.json` (formato oficial conforme **spec §9.1**)
- **`hooks/session-start.mjs` ÚNICO** (Node.js cross-platform) — Node é dependência obrigatória do Claude Code em todas as plataformas, então um único arquivo `.mjs` substitui o duplo `.sh`+`.cmd`. Padrão recomendado 2026: https://claudefa.st/blog/tools/hooks/cross-platform-hooks. Vantagens:
  - Parsing JSON nativo (sem `jq`)
  - Zero duplicação de lógica
  - `fs.readdirSync` + filter de extensão funciona igual Win/Mac/Linux
  - Sem PowerShell execution policy issues
- Lógica:
  1. Resolve project root via `process.env.CLAUDE_PROJECT_DIR ?? process.cwd()` (fallback porque `CLAUDE_PLUGIN_ROOT` tem bug conhecido em SessionStart — issue Anthropic/claude-code#27145)
  2. Scan `.prw|.tlpp|.prx` no project root (depth ≤2)
  3. Se nenhum: `process.exit(0)` com stdout vazio (silencioso)
  4. Se há e `.plugadvpl/index.db` não existe: emit `additionalContext` sugerindo `/plugadvpl:init` + `/plugadvpl:ingest`
  5. Se existe: chama `child_process.execSync("uvx plugadvpl@0.1.0 status --check-stale --quiet --format json")`, parse JSON, decide msg ou silêncio
- Output JSON oficial: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}` quando há algo útil; exit 0 com stdout vazio caso contrário
- Limite oficial: `additionalContext` ≤10.000 chars

### Chunk 13: Testes (fixtures + suites)

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk13.md`

Cobre:
- 20 fixtures sintéticas em `cli/tests/fixtures/synthetic/`
- **Snapshot testing com syrupy idiomático:** snapshots ficam em `__snapshots__/<test_file>.ambr` ao lado de cada teste (gerenciado pelo plugin). **REMOVIDO** `fixtures/expected/` e `scripts/regenerate_expected.py` (eram redundantes — syrupy já faz isso). Update via `pytest --snapshot-update`. Pattern: `assert parsed == snapshot` em vez de 11 asserts manuais.
- **Property-based tests com hypothesis** (1 por extractor): garante que parser não crasha com inputs adversariais e que `strip_advpl` preserva offsets em qualquer string.
- Suite integration em `cli/tests/integration/` (test_ingest_synthetic, test_incremental, test_reindex_single, test_idempotency, test_cli_commands, test_claude_md_fragment, test_doctor, test_schema_create)
- Suite bench em `cli/tests/bench/` (test_perf_ingest, test_perf_queries) com `pytest-benchmark` + persistência via `github-action-benchmark` em CI
- Suite e2e_local em `cli/tests/e2e_local/` (test_e2e_local_ingest, test_e2e_local_parity, test_e2e_local_smoke)
- conftest.py com fixtures comuns
- **Coverage threshold ≥80%** via `pytest-cov`, configurado no `pyproject.toml`. CI sobe XML para Codecov (free para OSS) para diff coverage por PR

### Chunk 14: CI/CD + Release + validate_plugin

Localização: `docs/superpowers/plans/2026-05-11-plugadvpl-mvp-chunk14.md`

Cobre:

**Validação do plugin:**
- `scripts/validate_plugin.py` é **wrapper fino** sobre `claude plugin validate ./` (CLI oficial Anthropic — fonte: github.com/anthropics/claude-code plugin-dev). Adiciona apenas validações específicas de plugadvpl que o validator oficial não cobre (presença de fixtures sintéticas, consistência entre `plugin.json.version` e `cli/pyproject.toml` derivado de `hatch version`). Usa JSON Schemas oficiais publicados em schemastore.org (`claude-code-plugin-manifest.json`, `claude-code-marketplace.json`) via `jsonschema` lib.

**Conventional Commits + CHANGELOG automático:**
- `.pre-commit-config.yaml` com hook `compilerla/conventional-pre-commit` (puro Python, sem Node) para validar mensagens
- `cliff.toml` configurando `git-cliff` (Rust binary, leve, 2026 standard)
- Workflow `update-changelog.yml` que regenera CHANGELOG.md a partir de commits no PR de release-prepare

**Scripts:**
- `scripts/bump_marketplace_version.py` (lê `hatch version` e atualiza `plugin.json.version` + `marketplace.json`)
- `scripts/render_skill_templates.py` (substitui `{{plugadvpl_version}}` nos 13 SKILL.md de comando)

**Workflows com correções:**

`.github/workflows/ci.yml` — todo PR:
```yaml
jobs:
  lint-plugin:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0     # hatch-vcs precisa de TODAS as tags
      - uses: astral-sh/setup-uv@v8   # v8.x atual (era v3 errado)
      - run: pipx install pre-commit && pre-commit run --all-files
      - run: python scripts/validate_plugin.py

  test-cli:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ["3.11", "3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: astral-sh/setup-uv@v8
      - run: cd cli && uv sync --frozen
      - run: cd cli && uv run pytest tests/unit tests/integration -v
      - uses: codecov/codecov-action@v4
        with: { files: cli/coverage.xml }

  bench:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: astral-sh/setup-uv@v8
      - run: cd cli && uv sync --frozen
      - run: cd cli && uv run pytest tests/bench --benchmark-only --benchmark-json=output.json
      - uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: pytest
          output-file-path: cli/output.json
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
          alert-threshold: '110%'   # falha se 10% mais lento
          comment-on-alert: true

  smoke-uvx:
    runs-on: ubuntu-latest
    needs: test-cli
    steps:
      - uses: astral-sh/setup-uv@v8
      - run: uvx --from . plugadvpl --help
      - run: uvx --from . plugadvpl version
```

`.github/workflows/release.yml` — tag `v*`:
```yaml
on:
  push:
    tags: ['v*']

permissions:
  contents: write
  id-token: write    # OIDC

jobs:
  publish-pypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: astral-sh/setup-uv@v8
      - run: cd cli && uv build
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: cli/dist/   # crítico: uv build cli/ gera em cli/dist, não dist/

  github-release:
    runs-on: ubuntu-latest
    needs: publish-pypi
    steps:
      - uses: actions/checkout@v4
      - uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: cli/dist/*
```

**Trusted Publisher config em pypi.org:**
- Manage account → Publishing → Add pending publisher
- Workflow filename: `release.yml`
- Environment name: `production` (criar em GitHub Settings → Environments com required reviewers)

**Templates GitHub:**
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/pull_request_template.md`

---

## Critérios de "MVP done"

Após completar os 14 chunks, validar contra os critérios da Seção 14 do spec:

- [ ] `uvx plugadvpl@0.1.0 --help` funciona em Windows/Mac/Linux
- [ ] `init` cria DB com 22 tabelas + FTS5, escreve fragmento CLAUDE.md, adiciona .plugadvpl/ ao .gitignore
- [ ] `ingest` em fixture local (~2.000 fontes) completa em <60s com `--workers 8`
- [ ] Parity test ≤10% nas 7 tabelas comparáveis com baseline interno
- [ ] FTS5 com 3 modos (`--fts`, `--literal`, `--identifier`) testado em `SA1->A1_COD`, `%xfilial%`, `U_FATA050`, `::New`, `PARAMIXB[1]`
- [ ] Reindex × 3 mantém DB consistente (idempotência)
- [ ] `status --check-stale` detecta stale por mtime/size **e** versões
- [ ] Token-budget manual: explicar FATA050 ≤2.000 tokens
- [ ] Lint 13 regras: precisão ≥90%, recall ≥80% em fixtures
- [ ] Plugin instalável via `/plugin marketplace add` end-to-end
- [ ] 23 skills + 4 agents + 1 hook presentes e validados via `validate_plugin.py`
- [ ] CI passa em matriz 3 OS × 3 Python
- [ ] **Coverage ≥80%** (pytest-cov `--cov-fail-under=80`)
- [ ] github-action-benchmark configurado e PR comment funcionando (alerta em +10% slower)
- [ ] `pre-commit` hook valida Conventional Commits localmente
- [ ] `claude plugin validate ./` passa sem erro (CLI oficial Anthropic)
- [ ] PyPI publica `plugadvpl 0.1.0` via Trusted Publisher OIDC
- [ ] Wheel publicado de `cli/dist/` (não `dist/` raiz)
- [ ] README, LICENSE, NOTICE, CONTRIBUTING, CoC, SECURITY, CHANGELOG presentes
- [ ] CHANGELOG auto-gerado via git-cliff a partir de commits Conventional

---

## Notas para o executor

- **Use TDD estrito:** teste falha → implementação mínima → teste passa → refactor → commit.
- **Commits pequenos e frequentes:** uma feature = um ou mais commits, não acumular.
- **Skip work que viola YAGNI:** se um critério parece "nice to have" mas não está nos acceptance criteria, pule.
- **Não adicione recursos não solicitados:** o spec é a fonte da verdade. Se achar que falta algo, pergunte antes de implementar.
- **Preserve encoding cp1252** em fixtures sintéticas que precisam representar fontes ADVPL típicas.
- **Use `uv run` para tudo:** `uv run pytest`, `uv run plugadvpl`, `uv run ruff check`.
- **Reference spec sections em commits:** `git commit -m "feat(db): add fonte_tabela for reverse lookup (spec §4.2)"`.
