# Publicação LinkedIn — plugadvpl v0.2 → v0.4

> Carrossel + copy prontos pra colar. Slides em ordem.
> Formato sugerido: 1080×1350 (vertical LinkedIn). 10 slides.

---

## Copy do post (texto que vai acima do carrossel)

```
plugadvpl saiu da v0.2 (biblioteca de referência embarcada) e chegou
agora na v0.4 (rastreabilidade de execução). De um indexador de
fontes ADVPL pra responder o Claude com ~16× menos token, virou um
mapa do Protheus customizado: dicionário SX, lint cross-file 100%
ativo, e agora workflows/schedules/jobs/mail indexados.

Linha do tempo no carrossel — mais o roadmap do Universo 3 e uma
prévia do que vem por aí com a entrada do Tiago Barbieri no projeto
(integração com TDS-LS/TDS-CLI da TOTVS).

MIT, 100% local, sem telemetria. Comunidade ADVPL define o que vem.

→ pypi.org/project/plugadvpl
→ github.com/JoniPraia/plugadvpl

#ADVPL #TLPP #Protheus #TOTVS #ClaudeCode
```

---

## Slide 1 — Capa / hook

**plugadvpl**

de **v0.2** a **v0.4** — virou outro plugin.

*Indexador ADVPL que economiza ~16× tokens do Claude. O que mudou em ~30 releases.*

> Visual: logo + badge "v0.4.0" grande. Subtítulo pequeno.

---

## Slide 2 — Recap do problema

**Antes:** Claude lê `FATA050.prw` cru → ~12.000 tokens, resposta vaga, sem call graph.

**Com plugadvpl:** consulta o índice SQLite → ~730 tokens, resposta com módulo, MVC, SA1/SC5, PE relacionado.

**~16× menos contexto.** Parser validado em ~2.000 fontes reais.

---

## Slide 3 — v0.2: Biblioteca de referência embarcada

**Universo 1 turbinado.**

- ~23k linhas de docs ADVPL/TLPP embutidas em 6 skills
- 5 skills novas: `advpl-advanced`, `advpl-tlpp`, `advpl-web`, `advpl-dicionario-sx`, `advpl-mvc-avancado`
- 7 exemplos `.prw/.tlpp` de produção embarcados
- CLAUDE.md com tabela de decisão + workflow numerado

*Claude deixou de "achar" — passou a citar.*

---

## Slide 4 — v0.3: Universo 2 — Dicionário SX

**Killer feature: `impacto`.**

Ingest do dicionário SX exportado do Configurador Protheus (CSV) — só customização, padrão TOTVS é ignorado por design.

- 11 tabelas SX populadas (SX1, SX2, SX3, SX5, SX6, SX7, SXA, SXB, SX9, SIX, SXG)
- 3 comandos novos: `ingest-sx`, `impacto <campo>`, `gatilho <campo>`
- **~420k rows ingeridos em <30s**

---

## Slide 5 — v0.3.x: Lint cross-file 100%

**35/35 regras detectáveis automaticamente.**

- 13 single-file (v0.1) + 11 cross-file SX-001..SX-011 + 11 robustness fixes
- Valida que `X3_VALID`/`X7_REGRA`/`X1_VALID` referenciam funções, campos e consultas **que realmente existem**
- PERF-006: detecta `WHERE`/`ORDER BY` em coluna **sem índice SIX**

408 testes verde. Backlog técnico zerado.

---

## Slide 6 — v0.4.0: Universo 3 — Feature A (entregue)

**Indexar o invisível.**

Mecanismos canônicos TOTVS de **execução não-direta**:

- 🔄 **Workflow** (`TWFProcess`, `MsWorkflow`, `WFPrepEnv`)
- ⏰ **Schedule** (`Static Function SchedDef()`)
- ⚙️ **Job standalone** (`Main Function` + `RpcSetEnv` + `Sleep` loop)
- 📧 **Mail send** (`MailAuto`, `SEND MAIL`, `TMailManager`)

1 comando responde tudo: **`/plugadvpl:workflow`**

---

## Slide 7 — Caso de uso real (v0.4.0)

*"Essa User Function `XYZAprov` é alvo de workflow ou só helper?"*

Antes da v0.4: impossível responder via índice.

Agora:

```
/plugadvpl:workflow --target XYZAprov
```

Se aparecer com `kind=workflow` → é callback de `TWFProcess`. Mudar sem cuidado **quebra o workflow em produção**.

---

## Slide 8 — Roadmap v0.4.x

**Universo 3 tem 3 features.**

✅ **v0.4.0 — Feature A** — workflow / schedule / job / mail *(entregue)*

🟡 **v0.4.1 — Feature B — ExecAuto chain expansion** *(spec aprovada)*
`MsExecAuto({|x,y,z| MATA410(x,y,z)}, …)` → resolve pra **SC5, SC6** automaticamente. Catálogo inicial de 25 rotinas canônicas (MATA410, FINA040, CTBA102…).

🟡 **v0.4.2 — Feature C** — Protheus.doc agregada por módulo

Backlog: `appserver.ini` parser, `record_counts` via DBAccess, embeddings via `sqlite-vec`.

---

## Slide 9 — No horizonte: TDS-LS / TDS-CLI

**plugadvpl + ferramental oficial TOTVS.**

Próximo passo: integrar com **TDS-CLI** (github.com/totvs/tds-ls) — o language server oficial da TOTVS pra ADVPL.

Combinação: índice SQLite + análise estática + LSP oficial.

🤝 **Quem entra como colaborador:** **Tiago Barbieri.**
Esse pedaço é dele.

> Visual: logos TOTVS + plugadvpl + avatar do Tiago. Marcar o @ dele no copy do post.

---

## Slide 10 — CTA

**MIT. 100% local. Sem telemetria.**

Instalação em 1 linha:

```powershell
irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex
```

📦 **PyPI** — `pypi.org/project/plugadvpl`
💾 **GitHub** — `github.com/JoniPraia/plugadvpl`
🗣️ **Discussions** — pra showcase, dúvidas, sugestões

*Comunidade ADVPL/TLPP brasileira define o que vem primeiro.*

---

## Notas práticas pra montar no Canva / Figma

- **Paleta sugerida:** azul-escuro fundo + verde Protheus (#2D8B3A) pra destaques + branco/cinza pro corpo. Consistente do slide 1 ao 10.
- **Tipografia:** monospace pra blocos de código (snippets dos comandos), sans-serif pesada pros títulos.
- **Cada slide com 1 ideia.** Não emende v0.3 + v0.4 no mesmo slide (perde no feed).
- **Slide 1 e 9 são os "stoppers"** — caprichar no visual. O slide 9 (entrada do Tiago) vai gerar engagement porque humaniza.
- **Tamanho:** 1080×1350 (formato vertical do LinkedIn carousel, melhor que quadrado em 2026).

## Antes de publicar

- **Marcar o Tiago** no copy ("com @Tiago Barbieri entrando como colaborador") — aumenta alcance e dá crédito visível.
- **Link sem `https://`** no copy (LinkedIn não encurta, fica feio).
- **Hashtags no fim do copy** (não nos slides). Máx 5.
