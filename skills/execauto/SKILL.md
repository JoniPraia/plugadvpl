---
description: Lista chamadas MsExecAuto resolvidas (rotina canônica + módulo + tabelas inferidas via catálogo TOTVS) — Universo 3 Feature B, v0.4.1+
disable-model-invocation: true
arguments: [filtros]
allowed-tools: [Bash]
---

# `/plugadvpl:execauto`

**Killer feature do v0.4.1** (Universo 3 — Rastreabilidade Feature B). Resolve a indireção do `MsExecAuto({|x,y,z| MATA410(x,y,z)}, ...)` e cruza com catálogo TOTVS pra **inferir tabelas tocadas indiretamente**.

## Por quê

Antes do v0.4.1, `arch MGFCOMBO.prw` mostrava `tabelas: []` mesmo o fonte chamando `MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCab, aIt, 3)` — que é **inclusão de Pedido de Venda** e portanto toca `SC5` + `SC6`. Agora:

```
$ plugadvpl arch MGFCOMBO.prw
tabelas: []
tabelas_via_execauto: true
tabelas_via_execauto_resolvidas: ["SC5", "SC6", "SF4", "SB1"]   ← novo
```

E o comando dedicado:

```
$ plugadvpl execauto --arquivo MGFCOMBO.prw
arquivo      funcao    linha  routine   module    op         tabelas
MGFCOMBO.prw  MGFCOMBO  621   MATA410   SIGAFAT   inclusao   SC5,SC6,SF4,SB1
```

## Uso

```
/plugadvpl:execauto [--routine <nome>] [--modulo <SIGAFAT>]
                    [--arquivo <basename>] [--op inc|alt|exc]
                    [--dynamic|--no-dynamic]
```

## Opções

- `--routine` / `-r` — filtra por rotina TOTVS (`MATA410`, `FINA050`, ...)
- `--modulo` / `-m` — filtra por módulo (`SIGAFAT`, `SIGACOM`, `SIGAFIN`, `SIGACTB`, `SIGAEEC`, `SIGAEST`, `SIGAPCP`, `SIGATMS`)
- `--arquivo` / `-a` — filtra por arquivo (basename, case-insensitive)
- `--op` / `-o` — filtra por operação: `inc` (3, inclusão), `alt` (4, alteração), `exc` (5, exclusão)
- `--dynamic` — só chamadas não-resolvíveis (`&(cVar)`, codeblock vazio, etc); `--no-dynamic` exclui

## Execução

```bash
uvx plugadvpl@0.4.2 --format md execauto $ARGUMENTS
```

> **Para agente IA:** prefira `--format md` (sem truncamento). Default `table` Rich trunca colunas. Flag global vem **antes** do subcomando.

## Exemplos

- `/plugadvpl:execauto` — lista todas as chamadas do projeto
- `/plugadvpl:execauto --routine MATA410 --op inc` — quem inclui Pedido de Venda
- `/plugadvpl:execauto --modulo SIGAFIN` — todas as integrações com financeiro
- `/plugadvpl:execauto --arquivo MGFCOM14.prw` — chamadas desse fonte
- `/plugadvpl:execauto --dynamic` — calls não-resolvíveis (precisam revisão manual)
- `/plugadvpl:execauto --op exc` — todas as exclusões automáticas (auditoria)

## Saída

| Campo | Significado |
|-------|-------------|
| `arquivo`     | fonte que tem a chamada |
| `funcao`      | função-pai onde foi detectada (resolved via chunks) |
| `linha`       | linha exata do `MsExecAuto(` |
| `routine`     | rotina TOTVS chamada (`MATA410`, etc) ou `(dynamic)` |
| `module`      | módulo TOTVS resolvido pelo catálogo (`SIGAFAT`, ...) |
| `op`          | `inclusao`/`alteracao`/`exclusao` ou número raw |
| `tabelas`     | tabelas resolvidas pelo catálogo (primary + secondary) |
| `snippet`     | linha do match (truncada a 80 chars no display; `--format json` mostra completa) |

Campos extras só visíveis em `--format json`:

| Campo | Significado |
|-------|-------------|
| `routine_type`     | `cadastro`/`movimento` |
| `op_code`          | inteiro raw (3/4/5/outros) |
| `tables_resolved`  | lista (vs string `tabelas` na tabela) |
| `dynamic_call`     | bool — `true` se rotina não-resolvível |
| `arg_count`        | num args do codeblock |

## Catálogo de rotinas

25 rotinas indexadas no MVP em `cli/plugadvpl/lookups/execauto_routines.json`:

| Módulo | Rotinas |
|--------|---------|
| SIGAFAT | MATA050, MATA410, MATA460, MATA461 |
| SIGACOM | MATA103, MATA110, MATA120, MATA125, MATA150 |
| SIGAFIN | MATA030, FINA040, FINA050, FINA070, FINA080 |
| SIGAEST | MATA010, MATA075, MATA180, MATA220, MATA261, MATA310, MATA311 |
| SIGAPCP | MATA242 |
| SIGACTB | CTBA102 |
| SIGAEEC | EECAP100 |
| SIGATMS | TMSA500 |

**Rotina não no catálogo?** Ainda é detectada (`routine` populado) mas com `module=null` e `tabelas=[]`. PRs adicionando rotinas novas são bem-vindos — só editar `execauto_routines.json`, sem mudar código.

## Casos de uso

1. **Auditoria de exclusões automáticas**
   `/plugadvpl:execauto --op exc` — lista TODAS as `MsExecAuto({...}, ..., 5)` do projeto. Útil pra rever se há exclusão sem confirmação/log.

2. **Mapeamento de integrações por módulo**
   `/plugadvpl:execauto --modulo SIGAFIN` — quais fontes geram títulos no Contas a Pagar/Receber automaticamente?

3. **Cobertura real de tabelas** (cross-ref com `arch`)
   `arch X.prw` mostra `tabelas: []`? Cheque `tabelas_via_execauto_resolvidas` no mesmo output ou rode `execauto --arquivo X.prw` pra ver detalhe por chamada.

4. **Revisão de chamadas dinâmicas**
   `/plugadvpl:execauto --dynamic` — calls que o parser não conseguiu resolver (rotina via `&(cVar)` ou variável armazenada). Esses casos ficam fora da inferência de tabelas — vale revisar manualmente.

5. **Migração de rotina TOTVS** (deprecation)
   TOTVS depreciou `MATA410` → migrar pra `MATA468`? `/plugadvpl:execauto --routine MATA410` lista tudo que precisa atualizar.

## Cross-ref com outras features

- **`/plugadvpl:arch`** — agora expõe `tabelas_via_execauto_resolvidas: list[str]` agregando tabelas inferidas. O campo bool `tabelas_via_execauto` continua (não-breaking).
- **`/plugadvpl:tables`** — para ver tabelas escritas/lidas DIRETAMENTE pelo fonte. ExecAuto fica fora porque é indireção — use `execauto` específico.
- **`/plugadvpl:workflow`** (Feature A) — workflows + schedules + jobs + mail. Rotinas via ExecAuto frequentemente são chamadas dentro de jobs (`/plugadvpl:workflow --kind job_standalone`).
- **`/plugadvpl:lint`** — algumas chamadas ExecAuto erradas (parametros faltando) podem disparar lint. Cruzar quando relevante.
- **`/plugadvpl:callers`** — pra ver QUEM chama o fonte que tem ExecAuto (chain reversa: caller → este_fonte → MsExecAuto → MATA410 → SC5/SC6).

## Limitações conhecidas

- **Resolução via variável** — `bExec := {|x,y| MATA410(x,y)}; MsExecAuto(bExec, ...)`. Marca como `dynamic_call=true, routine=null`. Resolução exigiria data-flow analysis (fora do escopo MVP).
- **Macro-substituição** — `MsExecAuto({|x,y,z| &(cRot).(x,y,z)}, ...)`. Mesma flag `dynamic_call=true`. Raro nos customizados que vimos.
- **Rotinas fora do catálogo** — `routine` é populado mas `module=null` e `tabelas=[]`. Solução: adicionar entry em `execauto_routines.json`.
- **`op_code` por convenção** — extraído do último arg numérico literal. Se a rotina recebe nOpc via variável (`nOpc := 3; MsExecAuto(..., nOpc)`), fica `null`.

## Próximos passos sugeridos

- `/plugadvpl:arch <arquivo>` — visão geral incluindo `tabelas_via_execauto_resolvidas`
- `/plugadvpl:find <routine>` — abre a rotina TOTVS (se for User Function customizada)
- `/plugadvpl:tables` — tabelas tocadas diretamente (complementa o que `execauto` mostra como indireto)
