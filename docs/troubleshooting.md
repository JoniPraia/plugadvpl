# Troubleshooting — plugadvpl v0.1.0

Erros comuns e como resolvê-los. Cada entrada segue **Sintoma → Causa → Fix**.

## `uv: command not found`

- **Sintoma**: `uvx plugadvpl ...` falha porque `uv` não está no PATH.
- **Causa**: `uv` não instalado ou shell não recarregou o PATH.
- **Fix**:
  - Windows: `winget install astral-sh.uv`
  - Linux / macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Reabrir o terminal após a instalação.

## `UnicodeDecodeError` ao gravar `.prw`

- **Sintoma**: Erro de encoding ao salvar fonte ADVPL editado em UTF-8.
- **Causa**: Protheus exige cp1252 (Windows-1252). O editor está usando UTF-8.
- **Fix**: trocar o encoding para `cp1252`. No VSCode, usar o seletor de
  encoding no canto inferior direito da status bar (`Reopen with Encoding`
  → `Windows 1252`) e salvar novamente.

## `SQLITE_CORRUPT` em network share

- **Sintoma**: O DB `.plugadvpl/index.db` corrompe após ingest em share SMB.
- **Causa**: `.plugadvpl/` está em SMB/CIFS, onde o WAL do SQLite não é
  confiável.
- **Fix**: mover o projeto para disco local **ou** forçar
  `journal_mode=DELETE` (já automático para caminhos UNC `\\server\...`,
  manual para mapped drives).

## `Projeto ADVPL não detectado` no SessionStart

- **Sintoma**: O hook do plugin não roda na abertura da sessão.
- **Causa**: Não há `.prw`, `.tlpp` ou `.prx` em profundidade ≤2 a partir
  da raiz do projeto. Plugin desabilita silenciosamente.
- **Fix**: verificar a estrutura do diretório do projeto e confirmar que
  fontes ADVPL existem nas primeiras duas camadas.

## `ingest` leva muito tempo (>3min para 2k fontes)

- **Sintoma**: pipeline lento em projeto grande.
- **Causa**: paralelismo padrão pode não estar saturando CPU; overhead de
  `spawn` no Windows.
- **Fix**: usar `--workers 8`. Em Windows com spawn overhead, considere
  `uv tool install plugadvpl` em vez de `uvx` para reduzir cold start.

## `arch` retorna nada para fonte que existe

- **Sintoma**: `plugadvpl arch <arquivo>` retorna vazio mesmo com o `.prw`
  presente.
- **Causa**: arquivo não foi indexado (criado/modificado após o último
  `ingest`).
- **Fix**: `plugadvpl reindex <arq>` ou rodar `plugadvpl ingest` completo.

## `lint` reporta muitos falso-positivos

- **Sintoma**: regras como BP-005 e SEC-002 sinalizam código legítimo.
- **Causa**: as 13 regras single-file são heurísticas regex — alguns
  padrões enganam o detector (ver `docs/limitations.md`).
- **Fix**: ignorar ou validar manualmente. Silenciamento configurável via
  `.plugadvpl/lint.toml` está planejado para v0.2.

## `Pre-commit conventional-commits failing`

- **Sintoma**: commit local rejeitado pelo hook do `commitlint`.
- **Causa**: mensagem de commit não segue Conventional Commits.
- **Fix**: começar a mensagem com um dos prefixos:
  `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `perf:`,
  `ci:`, `build:`, `style:`, `revert:`.

## `FTS5 não encontra SA1->A1_COD` literal

- **Sintoma**: busca FTS5 não retorna match para `SA1->A1_COD`.
- **Causa**: o tokenizer FTS5 default quebra em `->` e `_`, ignorando o
  literal como pretendido.
- **Fix**: usar `plugadvpl grep --literal "SA1->A1_COD"` (modo trigram).
  O default `--fts` é apropriado para palavras inteiras.

## "/plugin isn't available in this environment"

**Sintoma:** Você digita `/plugin install plugadvpl` no chat do Claude Code e recebe a mensagem `"/plugin isn't available in this environment."`.

**Causa:** O slash command `/plugin install` **só existe no Claude Code CLI nativo** (terminal `claude`). Na extensão VSCode do Claude Code, esse comando não está disponível — é uma limitação oficial do Claude Code, não do plugadvpl.

**Solução:**

- **Se estiver no terminal `claude` (CLI nativo)**: o comando deveria funcionar. Verifique que você atualizou o Claude Code (`claude --update`).
- **Se estiver na extensão VSCode**:
  1. No chat, digite apenas `/plugin` (sem args) → abre a UI Manage Plugins
  2. Aba **Marketplaces** → Add → `https://github.com/JoniPraia/plugadvpl.git`
  3. Aba **Plugins** → `plugadvpl` → **Install for you (user scope)**

Veja `README.md` seção "Instalando o plugin Claude Code" para detalhes.
