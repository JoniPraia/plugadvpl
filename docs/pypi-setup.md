# PyPI Trusted Publisher — Setup

Guia passo-a-passo para configurar o Trusted Publisher do PyPI e disparar
o primeiro release de `plugadvpl`.

## Pré-requisito

Conta no PyPI com **2FA habilitado** (TOTP ou WebAuthn).

## Passo 1 — Criar / reservar o projeto

O nome `plugadvpl` ainda não existe no PyPI. Duas opções:

- **Implícita**: publicar o primeiro release reserva o nome automaticamente.
- **Explícita (recomendada)**: criar um *pending publisher* ANTES do primeiro
  release para garantir o nome — pypi.org → *Account settings* → *Publishing*
  → *Add a new pending publisher*.

## Passo 2 — Configurar Trusted Publisher

1. Logar em <https://pypi.org/>.
2. Ir em *Account settings* → *Publishing*.
3. Click em *Add a new pending publisher* (para 1º release) ou
   *Add a new publisher* (depois).
4. Preencher:
   - **PyPI Project Name**: `plugadvpl`
   - **Owner**: `JoniPraia`
   - **Repository name**: `plugadvpl`
   - **Workflow filename**: `release.yml`
   - **Environment name**: *(deixar vazio — não usamos GitHub Environments
     protegidos)*
5. Save.

## Passo 3 — Repetir para TestPyPI (release candidates)

Recomendado para validar a pipeline com tags `v*-rc*` antes do release real.

- Acessar <https://test.pypi.org/>.
- Repetir os mesmos passos com o mesmo nome `plugadvpl` (TestPyPI é
  namespace separado do PyPI).
- **Workflow filename**: `release-rc.yml` (definido em
  `.github/workflows/release-rc.yml`).

## Passo 4 — Validar config

- Workflow `release.yml` já tem `permissions: id-token: write` (OIDC
  habilitado).
- Wheel build via `uv build cli/` produz artefatos em `cli/dist/`.
- `pypa/gh-action-pypi-publish@release/v1` está configurado com
  `packages-dir: cli/dist/`.

## Passo 5 — Disparar o primeiro release

1. *Actions* → *Release Prepare* → *Run workflow* (workflow_dispatch).
2. Input version: `0.1.0`.
3. Workflow abre um PR com bump de `plugin.json` + `marketplace.json`.
4. Review + merge do PR.
5. Localmente:

   ```bash
   git fetch
   git tag v0.1.0
   git push origin v0.1.0
   ```

6. Workflow `release.yml` dispara automaticamente:
   - Build do wheel
   - Publish no PyPI (OIDC, sem token)
   - Criação da GitHub Release com `generate_release_notes: true`

## Troubleshooting

- **Erro 403 / "Trusted publisher not configured"** → conferir
  `Owner` / `Repository` / `Workflow filename` no PyPI batem 100% com o
  repositório.
- **Erro "Filename not unique"** → a versão já foi publicada (PyPI não
  permite reupload da mesma versão).
- **Wheel build falha** → checar `cli/pyproject.toml` (sintaxe) e
  `hatch-vcs raw-options.root = ".."` (precisa apontar para a raiz do
  repo para resolver as tags de versão).
