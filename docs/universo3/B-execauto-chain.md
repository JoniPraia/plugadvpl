# Universo 3 — Feature B: ExecAuto Chain Expansion

> **Status:** spec — aguardando aprovação
> **Versão alvo:** v0.4.1 (incremento sobre v0.4.0)
> **Schema bump:** v5 → v6
> **Pré-requisito:** v0.4.0 (Feature A) já entregue

## 1. Problema

Hoje (v0.4.0) o plugin sabe que `MsExecAuto` foi usado em um fonte (capability
`EXEC_AUTO_CALLER`, flag `tabelas_via_execauto: bool` em `arch`), mas **não
resolve a indireção**. Resultado prático:

```bash
$ plugadvpl arch MGFCOMBO.prw
arquivo:    MGFCOMBO.prw
capabilities: ["EXEC_AUTO_CALLER", ...]
tabelas:    []                          # ← vazio!
tabelas_via_execauto: true              # ← indica "alguma coisa", mas não diz O QUÊ
```

O fonte `MGFCOMBO.prw:621` chama `MsExecAuto({|x,y,z| MATA410(x,y,z)}, aCab, aIt, 3)`
— que é **inclusão de Pedido de Venda** e portanto **toca `SC5` + `SC6`**. O
plugin tem essa informação latente (regex captura `MATA410`), mas não cruza com
o catálogo TOTVS pra dizer "tabelas reais via ExecAuto: SC5, SC6".

**Pergunta que o plugin deve responder após v0.4.1:**
> "Quais tabelas o fonte X realmente toca, contando as via ExecAuto?"
> "Quais fontes deste projeto incluem Pedido de Venda automaticamente (`MATA410` op=3)?"
> "Tem chamada ExecAuto não-resolvível (dynamic) que precisa de revisão manual?"

## 2. Escopo MVP (v0.4.1)

### Inclui
1. **Lookup `execauto_routines.json`** — catálogo de ~25 rotinas canônicas TOTVS
   com `routine`, `module`, `type`, `tables_primary[]`, `tables_secondary[]`,
   `source_url`, `verified` (vide §4).
2. **Detector `parsing/execauto.py`** — extrai chamadas `MsExecAuto`/`ExecAuto`,
   resolve rotina pelo codeblock (`{|x,y,z| MATA410(x,y,z)}` → `MATA410`),
   detecta `op_code` (3/4/5), flag `dynamic_call` se rotina não-resolvível.
3. **Tabela `execauto_calls`** — nova tabela com 1 row por chamada detectada
   (não 1 por fonte). Schema em §5.
4. **Comando `plugadvpl execauto`** com filtros `--routine`, `--modulo`,
   `--arquivo`, `--op` (inc/alt/exc), `--dynamic`. Skill correspondente.
5. **Enrichment do `arch`** — campo novo `tabelas_via_execauto_resolvidas:
   list[str]` (era só `bool`). Não quebra clientes existentes (campo bool
   continua).
6. **Cross-ref `tables`** — quando o usuário roda `plugadvpl tables --include-execauto`,
   tabelas inferidas via ExecAuto entram na lista (com flag `via_execauto: true`).

### Não inclui (defer pra v0.4.2+)
- **Resolução por data-flow** de variável armazenada (`bExec := {|x,y| ...}`
  depois `MsExecAuto(bExec, ...)`) — fora do escopo, exige análise de fluxo.
  Marca como `dynamic_call: true, reason: "indirect-block-var"`.
- **Catálogo > 50 rotinas** — começamos com 25 mais comuns; expansão
  incremental conforme uso.
- **Detecção de `aLog`/`MostraErro`** padrão pós-ExecAuto (já é parcialmente
  capturado pelo lint, redundante).
- **Resolução de `&(cFunc)` macro-substituição** — flag `dynamic` (raro,
  zero ocorrências no customizado local).

## 3. Padrões TOTVS para detecção

### 3.1 Sintaxe canônica
```advpl
MsExecAuto( {|args| RotinaCanonica(args)}, <param1>, <param2>, ..., <opCode> )
```

Variantes confirmadas em produção (vide research):

| # | Forma | Exemplo |
|---|-------|---------|
| 1 | 3 args (cab+itens+opc) | `MsExecAuto({\|x,y,z\| MATA410(x,y,z)}, aCab, aIt, 3)` |
| 2 | 2 args (sem itens) | `MsExecAuto({\|x,y\| FINA040(x,y)}, aArr, 3)` |
| 3 | 4 args nomeados | `MsExecAuto({\|a,b,c,d\| MATA410(a,b,c,d)}, aCab, aIt, 3, .F.)` |
| 4 | nTipo prefixo (Mata120) | `MsExecAuto({\|v,x,y,z,w,a\| Mata120(v,x,y,z,w,a)}, 2, aCab, aIt, 3)` |
| 5 | Skip args (vírgulas vazias) | `MSExecAuto({\|x,y,z,k,a,b\| MATA103(x,y,z,,,,k,a,,,b)}, ...)` |
| 6 | Sem args `{\|\|}` | `MsExecAuto({\|\| CN121Encerr(.T.)})` |
| 7 | Aninhado em MsAguarde | `MsAguarde({\|\| MsExecAuto({\|a,b,c,d\| EECAF200(a,b,c,d)}, ...)}, "msg")` |
| 8 | `&(cFunc)` dynamic (raro) | `MsExecAuto({\|x,y,z\| &(cRot).(x,y,z)}, ...)` |

### 3.2 Regra de extração (algoritmo)

```
1. Match `\bMs?ExecAuto\s*\(` (case-insensitive, não em comentário/string).
2. Localiza primeiro arg = codeblock `\{\s*\|[^|]*\|\s*(.+?)\s*\}` (não-greedy, multi-line).
3. Dentro do corpo do codeblock:
   a) Se primeira ocorrência é `\w+\s*\(` → routine = grupo 1.
   b) Se é `&\(` ou `&[a-zA-Z_]` → dynamic_call = true, routine = null.
   c) Se é `\w+\.\w+\(` → routine_obj = obj.method (raro, marca).
4. op_code: último arg literal numérico (3/4/5) antes do `)` final.
5. arg_count: número de pipes args na assinatura `|x,y,z|` (informativo).
```

### 3.3 op_code mapping

| valor | semântica | metadata.op |
|-------|-----------|-------------|
| 3     | Inclusão  | `"inclusao"` |
| 4     | Alteração | `"alteracao"` |
| 5     | Exclusão  | `"exclusao"` |
| outro | Não-padrão | `null` (raro) |

## 4. Catálogo `execauto_routines.json`

Schema:
```json
{
  "schema_version": 1,
  "routines": [
    {
      "routine": "MATA410",
      "module": "SIGAFAT",
      "type": "movimento",
      "label": "Pedido de Venda",
      "tables_primary": ["SC5", "SC6"],
      "tables_secondary": ["SF4", "SB1"],
      "source_url": "https://tdn.totvs.com/pages/releaseview.action?pageId=6784012",
      "verified": true
    },
    ...
  ]
}
```

### Catálogo inicial (25 rotinas)

| Rotina | Módulo | Tipo | Tabelas primárias | Verified |
|--------|--------|------|-------------------|----------|
| MATA010 | SIGAEST | cadastro | SB1 | ✅ |
| MATA030 | SIGAFIN | cadastro | SA1 | ✅ |
| MATA050 | SIGAFAT | cadastro | SA4 | ✅ |
| MATA075 | SIGAEST | movimento | SB8 | ⚠️ |
| MATA103 | SIGACOM | movimento | SF1, SD1 | ✅ |
| MATA110 | SIGACOM | movimento | SC1 | ✅ |
| MATA120 | SIGACOM | movimento | SC7 | ✅ |
| MATA125 | SIGACOM | movimento | SCA, SCB | ⚠️ |
| MATA150 | SIGACOM | movimento | SC8 | ✅ |
| MATA180 | SIGAEST | cadastro | SB5 | ✅ |
| MATA220 | SIGAEST | cadastro | SG1 | ⚠️ |
| MATA242 | SIGAPCP | movimento | SD3 | ✅ |
| MATA261 | SIGAEST | movimento | SD3 | ✅ |
| MATA310 | SIGAEST | movimento | SD3 | ✅ |
| MATA311 | SIGAEST | movimento | SD3 | ✅ |
| MATA410 | SIGAFAT | movimento | SC5, SC6 | ✅ |
| MATA460 | SIGAFAT | movimento | SF2, SD2 | ✅ |
| MATA461 | SIGAFAT | movimento | SF2, SD2 | ✅ |
| FINA040 | SIGAFIN | movimento | SE1 | ✅ |
| FINA050 | SIGAFIN | movimento | SE2 | ✅ |
| FINA070 | SIGAFIN | movimento | SE1, SE5 | ✅ |
| FINA080 | SIGAFIN | movimento | SE2, SE5 | ✅ |
| CTBA102 | SIGACTB | movimento | CT2 | ✅ |
| EECAP100 | SIGAEEC | movimento | EEC, EE7 | ⚠️ |
| TMSA500 | SIGATMS | movimento | DT6 | ⚠️ |

`verified: false (⚠️)` — fonte secundária; usuário pode corrigir via PR.

## 5. Schema (migration `006_universo3_execauto_calls.sql`)

```sql
CREATE TABLE execauto_calls (
  id INTEGER PRIMARY KEY,
  arquivo TEXT NOT NULL,
  funcao TEXT,
  linha INTEGER NOT NULL,
  routine TEXT,                  -- MATA410, FINA050, NULL se dynamic
  module TEXT,                   -- SIGAFAT, NULL se rotina não no catálogo
  routine_type TEXT,             -- cadastro/movimento, NULL se desconhecido
  op_code INTEGER,               -- 3/4/5 ou NULL
  op_label TEXT,                 -- "inclusao"/"alteracao"/"exclusao"
  tables_resolved_json TEXT,     -- JSON array ["SC5","SC6"] (primary+secondary)
  dynamic_call INTEGER NOT NULL DEFAULT 0,  -- 0 ou 1 (bool)
  arg_count INTEGER,             -- número de args do codeblock
  snippet TEXT NOT NULL          -- linha do match
);
CREATE INDEX idx_execauto_arquivo ON execauto_calls(arquivo);
CREATE INDEX idx_execauto_routine ON execauto_calls(routine);
CREATE INDEX idx_execauto_module ON execauto_calls(module);
```

**Por que tabela própria** (e não estender `execution_triggers`):
- Volume diferente: 1 fonte = N execauto calls (vs ~1 execution_trigger);
- Query patterns diferentes (agregar por rotina/módulo, cross-ref tabelas);
- Metadata estruturada — não cabe em JSON-blob;
- Cross-ref com tabela `tabelas` é mais limpa via JOIN.

## 6. Comando `plugadvpl execauto`

```
plugadvpl execauto [--routine <nome>] [--modulo <SIGAFAT>]
                   [--arquivo <basename>] [--op inc|alt|exc]
                   [--dynamic]
```

### Saída padrão (table)
| arquivo | funcao | linha | routine | op | tables | snippet |

### Casos de uso
1. *"Quem inclui pedido de venda?"* →
   `plugadvpl execauto --routine MATA410 --op inc`
2. *"Quais fontes integram com SIGAFIN via ExecAuto?"* →
   `plugadvpl execauto --modulo SIGAFIN`
3. *"Tem chamada não-resolvível (dynamic) que merece revisão?"* →
   `plugadvpl execauto --dynamic`
4. *"Esse fonte chama o quê?"* →
   `plugadvpl execauto --arquivo MGFCOMBO.prw`

## 7. Enrichment de comandos existentes

### 7.1 `arch <arquivo>`
Adiciona campo `tabelas_via_execauto_resolvidas: list[str]`:
```json
{
  "arquivo": "MGFCOMBO.prw",
  "tabelas": [],
  "tabelas_via_execauto": true,
  "tabelas_via_execauto_resolvidas": ["SC5", "SC6", "SF4", "SB1"]
}
```
Campo bool `tabelas_via_execauto` continua (não-breaking).

### 7.2 `tables --include-execauto` (flag opt-in)
Quando flag, agrega tabelas resolvidas em `execauto_calls.tables_resolved_json`
na lista. Cada entry recebe `via_execauto: bool`.

## 8. Edge cases

| # | Caso | Comportamento esperado |
|---|------|------------------------|
| 1 | `MsExecAuto` em comentário `// ...` | NÃO detectar |
| 2 | `"MsExecAuto"` em string literal | NÃO detectar |
| 3 | `MSEXECAUTO` (maiúsculo total) | DETECTAR (case-insensitive) |
| 4 | `ExecAuto` sem `Ms` (legacy raro) | DETECTAR (mesmo regex `Ms?`) |
| 5 | Codeblock multi-line | DETECTAR (regex multi-line dotall) |
| 6 | Aninhado em `MsAguarde({\|\| MsExecAuto(...)})` | DETECTAR (regex não se importa com nesting) |
| 7 | `MsExecAuto({\|x,y,z\| &(cVar).(x,y,z)}, ...)` | flag `dynamic_call: true, reason: "macro-substitution"` |
| 8 | `bExec := {\|...\| ...}; MsExecAuto(bExec, ...)` | flag `dynamic_call: true, reason: "indirect-block-var"` |
| 9 | Rotina não no catálogo (`MATAXYZ`) | `routine="MATAXYZ", module=null, tables_resolved=[]` |
| 10 | op_code não-padrão (ex: `9`) | `op_code=9, op_label=null` |
| 11 | Codeblock sem call (`{\|\| Nil}`) | `routine=null, dynamic_call=true, reason: "no-routine-in-block"` |

## 9. Plano de implementação (TDD)

### Fase 1 — Catálogo (~30 min)
- Criar `cli/plugadvpl/lookups/execauto_routines.json` com 25 rotinas iniciais.
- Helper `_load_execauto_catalog()` em `parsing/execauto.py`.

### Fase 2 — Detector + tests RED (~90 min)
- `cli/tests/unit/test_execauto.py` — 12-15 tests cobrindo §3 e §8.
- `cli/plugadvpl/parsing/execauto.py` — `extract_execauto_calls(content) -> list[dict]`.
- Migration `006_universo3_execauto_calls.sql`.
- Bump `SCHEMA_VERSION` 5 → 6.

### Fase 3 — Ingest wire (~30 min)
- `ingest.py` — após `execution_triggers`, chamar `extract_execauto_calls`,
  INSERT em `execauto_calls`. Idempotência: DELETE+INSERT por `arquivo`.
- Counter `execauto_calls` + meta `total_execauto_calls`.

### Fase 4 — Query + CLI (~60 min)
- `query.py` — `execauto_calls_query(conn, *, routine, modulo, arquivo, op, dynamic)`.
- `cli.py` — `@app.command() def execauto(...)`.
- Skill `skills/execauto/SKILL.md`.

### Fase 5 — Enrichment `arch` (~30 min)
- `query.py::arch_query` — adiciona `tabelas_via_execauto_resolvidas` via JOIN
  com `execauto_calls`.
- 1 test integration regredindo o cenário existente + novo cenário com tabelas resolvidas.

### Fase 6 — Release v0.4.1 (~30 min)
- Bump 19 skills (`@0.4.0` → `@0.4.1`), `plugin.json`, `marketplace.json`.
- CHANGELOG entry.
- Final test sweep.
- Commit + tag + push.

**Total estimado:** ~4h.

## 10. Trade-offs e decisões a aprovar

### 10.1 Tabela própria vs. estender `execution_triggers`
**Recomendação:** tabela própria (`execauto_calls`).
- ✅ Volume e query patterns diferentes
- ✅ Metadata estruturada (não JSON-blob)
- ✅ JOIN limpo com `tabelas` pra cross-ref
- ❌ Mais 1 tabela no schema (mas tradeoff vale)

### 10.2 Comando próprio `execauto` vs. integrar em `arch`/`tables`
**Recomendação:** comando próprio + enrichment em `arch` e `tables` (ambos).
- Comando próprio responde "quem chama X?" / "agregar por módulo"
- Enrichment em `arch` mantém o usuário no fluxo "quero entender este fonte"
- Enrichment em `tables` (opt-in flag) responde "quais tabelas este projeto realmente toca?"

### 10.3 Versão
**Recomendação:** v0.4.1 (incremento sobre v0.4.0).
- Universo 3 tem 3 features (A, B, C) — cada feature ganha sua minor incremento (.0/.1/.2)
- v0.4.0 entregou A; v0.4.1 entrega B; v0.4.2 entrega C; v0.4.3+ enriquecimento
- Schema bump (5→6) é incremento normal, não justifica major
- Migração não-destrutiva (só adiciona tabela)

### 10.4 Catálogo: 25 rotinas iniciais é suficiente?
**Recomendação:** sim para MVP. Pode expandir depois via PR/release dot.
- Cobertura cobre os casos mais comuns (fat/com/fin/est/ctb)
- Rotinas faltantes ainda são detectadas (`routine` populado, `module=null`,
  `tables_resolved=[]`) — usuário vê que existe mas falta enriquecimento
- Linha de PR clara: "adicionar X ao catálogo" sem mudar código

### 10.5 Resolução de variável indireta (data-flow)
**Recomendação:** fora do escopo MVP (flag `dynamic_call: true, reason: "indirect-block-var"`).
- Exige análise de fluxo (caro)
- Caso raro no customizado local
- Pode ser feature dot futura

## 11. Comparação com Feature A

| Aspecto | Feature A (workflow) | Feature B (execauto) |
|---------|---------------------|----------------------|
| Tabela | `execution_triggers` (genérica) | `execauto_calls` (específica) |
| Detector | `parsing/triggers.py` (4 kinds) | `parsing/execauto.py` (1 kind, N rotinas) |
| Catálogo externo | não | `execauto_routines.json` (25 rotinas) |
| Comando | `workflow` (filtros gerais) | `execauto` + enrichment `arch`/`tables` |
| Volume típico | 1-3 triggers/projeto | 10-100 calls/projeto |
| Schema bump | 4 → 5 | 5 → 6 |

## 12. Fontes (research)

### Oficial TOTVS
- [TDN MATA410](https://tdn.totvs.com/pages/releaseview.action?pageId=6784012)
- [TDN MATA110](https://tdn.totvs.com/pages/viewpage.action?pageId=318605213)
- [Central TOTVS MATA050](https://centraldeatendimento.totvs.com/hc/pt-br/articles/8058455139479)
- [TDN PEST01014 (MATA180)](https://tdn.totvs.com/pages/releaseview.action?pageId=358453385)
- [TDN PEST06508 (MATA242)](https://tdn.totvs.com/pages/viewpage.action?pageId=393362555)
- [TDN MATA261](https://tdn.totvs.com/pages/viewpage.action?pageId=379292916)
- [TDN EECAP100](https://tdn.totvs.com/pages/releaseview.action?pageId=394219396)
- [TDN TMSA500](https://tdn.totvs.com/display/public/PROT/TUMGXW_DT_MsExecAuto_Manutencao_de_Documentos_de_Transporte_TMSA500)

### Comunidade
- [ProtheusAdvpl FINA050](https://protheusadvpl.com.br/execauto-fina050/)
- [Mastersiga MATA103](https://mastersiga.tomticket.com/kb/compras/sigacom-documento-de-entrada-rotina-automatica-mata103-execauto)
- [advpl-protheus.blogspot rotinas-automaticas](http://advpl-protheus.blogspot.com/2011/03/rotinas-automaticas.html)

### Customizado local (D:\Clientes\Customizados)
- MGFCOMBO.prw:621 (MATA410), MGFCOMBM.PRW:165 (MATA103 11-arg),
  MGFCOM35.tlpp:1178 (MATA120 com nTipo prefixo), MGFEEC83.PRW:940
  (aninhado MsAguarde), MGFCOM14.prw:1493 (sem args), MGFCRM57.PRW:1370
  (FINA040)

---

## Perguntas pra aprovar antes de codar

1. **Tabela própria ok** (vs. estender `execution_triggers`)? *(rec: própria)*
2. **Comando próprio `execauto` + enrichment `arch`/`tables`** (vs. só enrichment ou só comando)? *(rec: próprio + enrichment)*
3. **Catálogo 25 rotinas iniciais** suficiente pro MVP? *(rec: sim, expandir via PR)*
4. **Versão v0.4.1** (vs. v0.5.0)? *(rec: v0.4.1, schema bump não é breaking)*
5. **Resolução indireta (data-flow) fora do MVP** ok? *(rec: sim, flag dynamic)*
