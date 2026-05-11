# Contributing

## Setup local

```bash
git clone https://github.com/JoniPraia/plugadvpl
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
# Aponte para um diretório com .prw/.tlpp
export PLUGADVPL_E2E_FONTES_DIR=/caminho/para/seus/fontes

# Opcional: baseline DB para parity test
export PLUGADVPL_E2E_BASELINE_DB=/caminho/para/baseline.db

uv run pytest -m local
```

Se as variáveis não estiverem definidas, os testes locais são skipados gracefully.

## Estilo

- `ruff format` (linhas ≤100)
- `ruff check`
- `mypy --strict`
- Mensagens de commit: Conventional Commits (`feat:`, `fix:`, `refactor:`, ...)
