# Security Policy

## Reportando uma vulnerabilidade

Email: jonipraiaoficial@gmail.com

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
