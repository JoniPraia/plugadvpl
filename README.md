# plugadvpl

[![PyPI version](https://img.shields.io/pypi/v/plugadvpl.svg?logo=pypi&logoColor=white)](https://pypi.org/project/plugadvpl/)
[![Python](https://img.shields.io/pypi/pyversions/plugadvpl.svg?logo=python&logoColor=white)](https://pypi.org/project/plugadvpl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/JoniPraia/plugadvpl/actions/workflows/ci.yml/badge.svg)](https://github.com/JoniPraia/plugadvpl/actions/workflows/ci.yml)
[![PyPI downloads](https://img.shields.io/pypi/dm/plugadvpl.svg?logo=pypi&logoColor=white)](https://pypi.org/project/plugadvpl/)
[![GitHub stars](https://img.shields.io/github/stars/JoniPraia/plugadvpl?logo=github)](https://github.com/JoniPraia/plugadvpl/stargazers)

> Plugin Claude Code + CLI Python que indexa fontes **ADVPL/TLPP** (TOTVS Protheus) em SQLite com FTS5 — para o Claude responder sobre o seu Protheus sem queimar contexto lendo `.prw` cru.

---

## Por que plugadvpl

- **Economia de tokens.** Um `.prw` médio tem 1.000 a 10.000 linhas. Abrir cru custa de 5k a 50k tokens. Com plugadvpl, a mesma pergunta é respondida via metadados estruturados — **~16× menos contexto** em projetos reais.
- **Parser provado em campo.** O extrator de funções, tabelas, SQL embarcado e call graph foi portado de um parser interno do autor, validado em aproximadamente **2.000 fontes ADVPL**. Não é um experimento de fim de semana.
- **MIT, sem telemetria, 100% local.** Índice SQLite mora em `.plugadvpl/index.db` dentro do seu repo. Nenhum dado sai da máquina. Funciona offline.

---

## Demonstração

**Cenário sem plugin** — pergunta: "explique a função `FATA050`":

```
Claude → Read FATA050.prw            # arquivo inteiro
       → ~12.000 tokens consumidos
       → resposta vaga, sem call graph, sem saber quem usa
```

**Cenário com plugadvpl**:

```
Claude → /plugadvpl:arch FATA050.prw   # capabilities, tabelas, funções, includes
       → /plugadvpl:callers FATA050    # quem chama
       → Read FATA050.prw offset=234 limit=46   # range exato, só se preciso
       → ~730 tokens consumidos       (≈ 16× menor)
       → resposta com contexto: módulo, MVC, tabelas SA1/SC5, PE relacionado
```

---

## Instalação rápida (one-liner)

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh
```

O script:
1. Instala `uv` (gerenciador de pacotes Python da Astral) se ainda não estiver presente
2. Instala `plugadvpl` globalmente via `uv tool install`
3. Imprime próximos passos

Depois é só:
```bash
cd <pasta-do-seu-projeto-Protheus>
plugadvpl init
plugadvpl ingest
plugadvpl status
```

> Se você prefere usar o plugin via Claude Code (slash commands), instale o marketplace
> e use `/plugadvpl:setup` que faz tudo automaticamente (ver "Plugin Claude Code" abaixo).

---

## Atualizando para uma versão nova

A forma simples — funciona em qualquer plataforma — é **rodar o one-liner de
instalação de novo**. Ele detecta `uv` ausente, instala se preciso, e
reinstala `plugadvpl` apontando para a versão atual do PyPI.

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh
```

Se já tem `uv` e quer só forçar pull da versão nova (uv às vezes segura cache):

```powershell
uv cache clean plugadvpl
uv tool install plugadvpl --reinstall --force
plugadvpl version
```

### O plugin Claude Code é separado da CLI

CLI (`plugadvpl`, Python) e plugin Claude Code (skills + agents + hook) são
**duas coisas que se atualizam separadamente**. Atualizar uma não toca na outra.

Pra atualizar o plugin:

```
/plugin marketplace update plugadvpl-marketplace
```

(no Claude Code CLI; na extensão VSCode use a UI `/plugin`).

Se algo travar (`uv` sumiu, plugin atualiza mas slash command parece velho,
cache de uvx segurando versão antiga), veja [Troubleshooting de atualização](docs/FAQ.md#troubleshooting-de-atualização) no FAQ.

---

## Quick start

```bash
# 1. Pré-requisito: uv (gerenciador Python rápido)
winget install astral-sh.uv                              # Windows
# OU: curl -LsSf https://astral.sh/uv/install.sh | sh    # Linux/macOS

# 2. Instale o plugin Claude Code — veja seção abaixo
#    (caminho varia entre CLI nativo e extensão VSCode)

# 3. Abra o seu projeto Protheus e rode:
/plugadvpl:init      # cria .plugadvpl/index.db, fragment CLAUDE.md, .gitignore
/plugadvpl:ingest    # parser paralelo, ~30–60s para 2.000 fontes
```

Pronto. A partir daqui o Claude já consulta o índice antes de abrir qualquer `.prw`. Para inspecionar você mesmo:

```bash
/plugadvpl:arch FATA050.prw         # visão arquitetural de um fonte
/plugadvpl:callers MaFisRef         # quem chama essa função
/plugadvpl:tables SA1               # quem lê/grava/reclock na SA1
/plugadvpl:param MV_LOCALIZA        # onde esse parâmetro é usado
/plugadvpl:lint --severity error    # encontrar problemas críticos
```

---

## Instalando o plugin Claude Code (opcional, para slash commands)

Além da CLI, o plugadvpl também é um **plugin Claude Code** que adiciona:
- Slash commands `/plugadvpl:arch`, `/plugadvpl:find`, `/plugadvpl:callers`, etc.
- 15 knowledge skills temáticas que Claude carrega automaticamente (advpl-mvc, advpl-tlpp, advpl-pontos-entrada, etc.)
- Hook `SessionStart` que detecta projetos ADVPL e sugere `/plugadvpl:init`
- 4 subagents especializados (analyzer, impact-analyzer, code-generator, reviewer-bot)

A forma de instalar depende de onde você usa o Claude Code:

### Opção A — Claude Code CLI (terminal `claude`)

No chat do CLI:

```
/plugin marketplace add https://github.com/JoniPraia/plugadvpl.git
/plugin install plugadvpl
```

Aceite o trust dialog. Pronto.

### Opção B — Extensão VSCode do Claude Code

A extensão **não suporta** `/plugin install` direto no chat (limitação oficial do Claude Code). Use a UI:

1. No chat, digite `/plugin` (sem args) — abre o painel **Manage Plugins**
   *Alternativa*: `Ctrl+Shift+P` → "Claude Code: Manage Plugins"
2. Aba **Marketplaces** → botão **Add** → cole `https://github.com/JoniPraia/plugadvpl.git`
3. Aba **Plugins** → encontre `plugadvpl` → clique **Install for you (user scope)**
4. Aceite o trust dialog

Reinicie o Claude Code para garantir que skills, hooks e slash commands carregam corretamente.

### Verificação

Em qualquer caminho, no chat:

```
/plugadvpl:status
```

Se aparecer output com counters do índice, o plugin está instalado e funcionando.

> **Importante:** O plugin precisa da CLI Python instalada também (`uv tool install plugadvpl` ou via [Instalação rápida (one-liner)](#instalação-rápida-one-liner)). O plugin é uma camada fina sobre a CLI — sem ela, os slash commands não funcionam.

---

## Comandos disponíveis

O CLI Python expõe **18 subcomandos** (a partir do v0.3.0), espelhados em slash commands do plugin Claude Code.

| Comando | Função |
|---|---|
| `/plugadvpl:init` | Cria `.plugadvpl/index.db`, fragment em `CLAUDE.md` e entrada no `.gitignore` |
| `/plugadvpl:ingest` | Escaneia e indexa todos os fontes (`--workers N`, `--incremental`, `--no-content`, `--redact-secrets`) |
| `/plugadvpl:reindex <arq>` | Re-ingest de um arquivo (após edição manual) |
| `/plugadvpl:status` | Versões, contadores, opcionalmente arquivos stale (`--check-stale`) |
| `/plugadvpl:find <termo>` | Busca composta: função → arquivo → conteúdo (FTS) |
| `/plugadvpl:callers <funcao>` | Quem chama a função (call graph reverso) |
| `/plugadvpl:callees <funcao>` | O que a função chama (call graph direto) |
| `/plugadvpl:tables <T>` | Quem usa a tabela `T` (`--mode read/write/reclock`) |
| `/plugadvpl:param <MV>` | Onde o parâmetro `MV_*` aparece |
| `/plugadvpl:arch <arq>` | **Visão arquitetural** — use SEMPRE antes de `Read` |
| `/plugadvpl:lint [arq]` | Lint findings (`--severity`, `--regra`, `--cross-file`) |
| `/plugadvpl:doctor` | Diagnósticos (encoding, órfãos, FTS sync, lookups) |
| `/plugadvpl:grep <pattern>` | Busca textual nos chunks (`--mode fts/literal/identifier`) |
| `/plugadvpl:help` | Lista comandos (atalho do CLI `--help`) |
| **`/plugadvpl:ingest-sx <pasta-csv>`** | **(v0.3.0)** Ingere dicionário SX exportado em CSV (sx1..sxg) |
| **`/plugadvpl:impacto <campo>`** | **(v0.3.0)** **Killer feature** — cruza referências a um campo em fontes ↔ SX3 ↔ SX7 ↔ SX1 (com `--depth 1..3`) |
| **`/plugadvpl:gatilho <campo>`** | **(v0.3.0)** Cadeia de gatilhos SX7 origem → destino (com `--depth 1..3`) |
| **`/plugadvpl:sx-status`** | **(v0.3.0)** Counts por tabela do dicionário SX |

Reference completa: [docs/cli-reference.md](docs/cli-reference.md).

---

## Skills incluídas

Além dos 18 command wrappers (1 por subcomando do CLI, mais o helper `setup`), o plugin traz **16 knowledge skills** carregadas pelo Claude conforme contexto:

| Skill | Quando carrega |
|---|---|
| `plugadvpl-index-usage` | Skill-chefe — força consulta ao índice antes de qualquer `Read` em fonte ADVPL |
| `advpl-fundamentals` | Notação húngara, naming, prefixos de módulo, 195 funções restritas |
| `advpl-encoding` | cp1252 (.prw) vs utf-8 (.tlpp) — preserve-by-default |
| `advpl-mvc` | MenuDef/ModelDef/ViewDef, hooks bCommit/bTudoOk, FWFormStruct |
| `advpl-mvc-avancado` | Eventos MVC, validações cruzadas, FWMVCRotAuto |
| `advpl-tlpp` | TLPP moderno — OO, namespaces, annotations |
| `advpl-embedded-sql` | BeginSql/EndSql, TCQuery, `%xfilial%`, `%notDel%`, `%table%` |
| `advpl-pontos-entrada` | User Function NOME(PARAMIXB), retorno via PARAMIXB[última] |
| `advpl-webservice` | REST (`WSRESTFUL`, `@Get/@Post`) e SOAP (`WSSERVICE`/`WSMETHOD`) |
| `advpl-web` | Interfaces web — Webex / HTML / WebExpress |
| `advpl-jobs-rpc` | `RpcSetEnv`, `StartJob`, `MsRunInThread`, funções proibidas em job |
| `advpl-matxfis` | Família fiscal (NF-e, SPED, ECF, REINF, integração SF2/SD2/SF3) |
| `advpl-advanced` | Threads, IPC, debug, OO em profundidade |
| `advpl-dicionario-sx` | Estrutura SX1/SX2/SX3/SX5/SX6/SX7/SIX/SXA/SXB (v0.2.0) |
| `advpl-dicionario-sx-validacoes` | Expressões ADVPL embutidas em X3_VALID/INIT/WHEN/VLDUSER, X7_REGRA, X1_VALID, X6_VALID/INIT — guia pra análise de impacto (v0.3.0) |
| `advpl-code-review` | 24 regras BP/SEC/PERF/MOD — 13 single-file (v0.1) + 11 cross-file `SX-001..SX-011` (v0.3.0) |

Também incluídos: **4 agents** especializados (`advpl-analyzer`, `advpl-impact-analyzer`, `advpl-code-generator`, `advpl-reviewer-bot`) e **1 SessionStart hook** Node.js que faz onboarding cross-platform do `.plugadvpl/`.

---

## Como funciona

```
.prw / .tlpp           parser strip-first         SQLite + FTS5         slash command
(seu projeto)   ───▶   (regex sobre conteúdo  ─▶  22 tabelas físicas  ─▶ /plugadvpl:*
                       sem comentário/string)     + 2 FTS5 virtuais     (Claude consulta)
                       paralelo adaptive          + 6 lookups TOTVS
```

O `plugadvpl ingest` escaneia o projeto, parseia cada fonte em paralelo (`ProcessPoolExecutor` com fallback single-thread para projetos < 200 arquivos), persiste metadados (funções, chamadas, tabelas, MV_*, SQL embarcado, PEs, REST endpoints, jobs, etc.) em SQLite, e rebuilda dois índices FTS5 — um `unicode61` com `tokenchars '_-'` (mantém `A1_COD` e `FW-Browse` como um token) e um trigram para busca substring exata (`SA1->A1_COD`, `%xfilial%`).

Quando você pergunta algo ao Claude sobre o projeto, o slash command roda uma query barata no SQLite e devolve só o que importa — função, range de linhas, callers, tabelas — em ~700 tokens. Detalhes em [docs/architecture.md](docs/architecture.md).

---

## Requisitos

- **Claude Code** (CLI ou IDE extension) com suporte a plugins
- **Python 3.11+** instalado via `uvx`/`uv` (não precisa criar venv manualmente)
- **Projeto Protheus** com fontes `.prw`, `.prx`, `.tlpp` ou `.apw`
- SO: Windows, Linux ou macOS (CI rodando matrix 3 OS × 3 Python)

---

## Status

**v0.3.0 — Universo 2: Dicionário SX (killer feature `impacto`).**

- 18 subcomandos, 35 skills (16 knowledge + 18 CLI wrappers + 1 setup helper), 4 agents, 1 hook
- 33 tabelas físicas (22 fontes + 11 SX) + 2 FTS5 + 6 lookups
- 250+ testes (unit + integration + bench + e2e_local)
- Bench em ~2.000 fontes: ingest <60s com `--workers 8`; ingest-sx
  do dicionário completo (~420k rows) <30s
- Schema + parser SX baseado em projeto interno anterior do autor

**Roadmap.**

- **v0.1** *(shipped)* — Universo 1: parser de fontes, FTS5, 13 regras lint single-file, 14 subcomandos CLI.
- **v0.2** *(shipped)* — 21k linhas de referência ADVPL/TLPP embutidas em 5 skills novas + 6 reforçadas.
- **v0.3** *(shipped)* — Universo 2 (Dicionário SX): ingest SX1..SXG, comandos `impacto`/`gatilho`/`sx-status`, 11 regras cross-file SX-001..SX-011.
- **v0.4** *(próximo)* — Universo 3 (Rastreabilidade): grafo PE × ponto de origem, MVC × tabela × campo, detecção de código morto, cross-cliente diff.

Detalhes em [docs/ROADMAP.md](docs/ROADMAP.md) e no spec `docs/superpowers/specs/2026-05-11-plugadvpl-design.md` (§15).

---

## Documentação

- [docs/cli-reference.md](docs/cli-reference.md) — reference completa dos 18 subcomandos com sintaxe, opções e exemplos
- [docs/schema.md](docs/schema.md) — schema SQLite (22 tabelas + 2 FTS5 + diagrama Mermaid + queries úteis)
- [docs/architecture.md](docs/architecture.md) — fluxo, componentes, decisões-chave e guia para contribuir com novas extrações
- [CONTRIBUTING.md](CONTRIBUTING.md) — setup local, fixtures, estilo, commits
- [CHANGELOG.md](CHANGELOG.md) — histórico de releases
- [SECURITY.md](SECURITY.md) — política de vulnerabilidades

---

## Créditos

- **Parser de fontes** portado de projeto interno anterior do autor (~750 linhas, validado em aproximadamente 2.000 fontes ADVPL).
- **Lookup catalogs** (funções nativas, restritas, lint rules, SQL macros, módulos ERP, PEs) extraídos de [advpl-specialist](https://github.com/thalysjuvenal/advpl-specialist) por **Thalys Augusto** (MIT) — crédito em [NOTICE](NOTICE).
- Construído pela e para a comunidade **Protheus/ADVPL brasileira**. PRs são muito bem-vindos.

---

## Comunidade

- **Bugs e sugestões**: [GitHub Issues](https://github.com/JoniPraia/plugadvpl/issues/new/choose)
- **Dúvidas, discussões, showcase**: [GitHub Discussions](https://github.com/JoniPraia/plugadvpl/discussions)
- **Roadmap público**: [docs/ROADMAP.md](docs/ROADMAP.md)
- **FAQ**: [docs/FAQ.md](docs/FAQ.md)

Pull requests muito bem-vindas — especialmente para parser, lint rules,
skills temáticas e exemplos `.prw/.tlpp` de produção (sanitizados).

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para setup de dev.

---

## Disclaimer / Marcas registradas

**Protheus**, **ADVPL**, **TLPP** e **TOTVS** são produtos e marcas registradas
de propriedade da **TOTVS S.A.** Este plugin é um projeto independente e
**não possui vínculo** com a TOTVS, suas franquias ou representantes.

### Sobre o uso e desenvolvimento

- Este plugin **não utiliza, redistribui ou expõe nenhum código-fonte do
  produto padrão Protheus** (rotinas TOTVS internas, RPO, fontes oficiais).
- A ferramenta foi desenvolvida e validada **exclusivamente sobre fontes
  customizados** (User Functions, customizações MVC, pontos de entrada,
  WebServices, jobs e demais arquivos `.prw`/`.tlpp`/`.prx` escritos pelos
  próprios clientes em seus ambientes).
- Os catálogos embarcados (funções nativas, funções restritas, módulos ERP,
  pontos de entrada padrão) contêm apenas **nomes e metadados publicamente
  documentados** na [TDN — TOTVS Developers Network](https://tdn.totvs.com/).
  Não há código-fonte proprietário embutido.
- Os exemplos `.prw`/`.tlpp` distribuídos em `skills/<x>/exemplos/` são
  **código original do autor**, escritos para ilustrar padrões de
  customização (não derivados de fontes padrão TOTVS).
- Cabe a cada usuário garantir que possui direito de acesso e análise sobre
  os fontes que indexar com este plugin (tipicamente customizações da própria
  empresa ou de cliente sob contrato).

---

## Licença

[MIT](LICENSE) © 2026 JoniPraia.
