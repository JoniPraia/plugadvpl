# Universo 3 — Feature C: Protheus.doc agregada

> **Status:** spec — aguardando aprovação
> **Versão alvo:** v0.4.2 (incremento sobre v0.4.1)
> **Schema bump:** v6 → v7
> **Pré-requisito:** v0.4.1 (Feature B) já entregue
> **Fechamento Universo 3:** A (workflow) + B (execauto) + C (docs) ✅

## 1. Problema

Hoje (v0.4.1) o plugin tem **lint BP-007** que detecta funções SEM header
`Protheus.doc` — mas só conta a presença/ausência. **Não extrai o conteúdo.**
Resultado prático:

```bash
$ plugadvpl find MT460FIM
arquivo:    src/SIGAFAT/MT460FIM.tlpp
funcao:     MT460FIM
linha:      22
# ← sem documentação, sem author, sem since, sem @param. Eu tenho que
#   abrir o fonte e ler 30 linhas de header pra saber o que ele faz.
```

E pior: **não há agregação por módulo**. Se o usuário quer "todas as funções
documentadas do SIGAFAT deste projeto, com summary e author", precisa fazer
`grep` manual.

**Pergunta que o plugin deve responder após v0.4.2:**
> "Liste todas as funções documentadas do SIGAFAT com summary"
> "Quais funções foram escritas pelo autor X?"
> "Quais funções estão `@deprecated` e ainda são chamadas?"
> "Liste @param/@return de `MT460FIM` sem abrir o fonte"
> "Há funções com header Protheus.doc mal-formado (sem fechar `/*/`)?"

## 2. Escopo MVP (v0.4.2)

### Inclui

1. **Parser `parsing/protheus_doc.py`** — `extract_protheus_docs(content) ->
   list[dict]`. Captura blocos `/*/{Protheus.doc} <id> ... /*/` e extrai
   estruturadamente as 16 tags canônicas TOTVS.
2. **Tabela `protheus_docs`** — schema v6→v7 com colunas para os 6 campos
   quentes (module, author, type, since, deprecated, funcao) + `raw_tags_json`
   catch-all + arrays JSON pra `params`, `returns`, `examples`, `history`.
3. **Inferência de módulo** — `module_inferido` por dois caminhos:
   - **Path-based**: `re.search(r"SIGA\w{3,4}", arquivo)` (ex.: `src/SIGAFAT/X.prw`)
   - **Routine-prefix**: usa o catálogo já existente `execauto_routines.json`
     (Feature B) — `MATA*` → SIGAFAT, `FINA*` → SIGAFIN, etc — pra resolver
     pelo nome da função quando o path não revelar
   - Fallback: `null` (parser não inventa)
4. **Comando `plugadvpl docs`** com argumento positional `[modulo]` + filtros
   `--author`, `--funcao`, `--arquivo`, `--deprecated`, `--tipo`. Skill
   `/plugadvpl:docs`.
5. **Modo `--show <funcao>`** — exibe o bloco completo formatado de uma função
   específica (vs. lista resumida).
6. **Cross-ref com BP-007** — comando `docs --orphans` lista funções
   mencionadas pelo BP-007 (sem header) — atalho pra ver "o que falta documentar".

### Não inclui (defer pra v0.5.x)

- **Headers legados pré-Protheus.doc** (`+--+` ASCII art tabular). Heurística
  separada, fora do MVP.
- **Inline `//{pdoc}`** (associado a próxima variável/property). Raro, defer.
- **Geração de HTML/MD** (output style do TDS Eclipse). Plugin é índice, não
  doc-generator.
- **Validação de cross-ref `@param` vs assinatura real** (lint candidato BP-009
  futuro).
- **Detecção de `/*/` não-fechado até EOF** como erro de lint (BP-007b
  candidato — pode entrar em release dot).

## 3. Padrão Protheus.doc (oficial TOTVS)

### 3.1 Estrutura do bloco

```advpl
/*/{Protheus.doc} MinhaFn
Resumo livre na primeira linha (vira summary).
Pode ter múltiplas linhas até a primeira @tag.
@type function
@author Joao Silva
@since 18/10/2025
@version 1.0
@param cArg1, character, "Descrição do primeiro parâmetro"
@param [nArg2], numeric, "Opcional (colchetes em [nArg2])"
@return logical, ".T. se sucesso"
@example
   Local lOk := MinhaFn("X", 1)
@see OutraFn
@deprecated
/*/
User Function MinhaFn(cArg1, nArg2)
   ...
Return .T.
```

**Fonte oficial:** [tds-vscode/docs/protheus-doc.md](https://github.com/totvs/tds-vscode/blob/master/docs/protheus-doc.md)

### 3.2 Tags canônicas (16 oficiais)

| Tag | Multiplicidade | Tipo | Notas |
|-----|----------------|------|-------|
| `@type`        | 1 (obrigatória) | enum | function, user function, static function, class, method, property |
| `@author`      | 1 | string | autor |
| `@since`       | 1 | date string | data criação |
| `@version`     | 1 | string | versão |
| `@description` | 1 | string | descrição (vs. summary livre) |
| `@deprecated`  | 1 | flag/string | sem valor = flag; com valor = motivo |
| `@language`    | 1 | string | pt-br/en/es |
| `@param`       | N | structured | `<name>, <type>, <desc>` (colchetes em name = optional) |
| `@return`      | N | structured | `<type>, <desc>` (geralmente 1) |
| `@example`     | N | code block | aceita `@sample` como alias |
| `@see`         | N | string | referência cruzada |
| `@history`     | N | structured | `<date>, <user>, <desc>` |
| `@table`       | N | string | tabela tocada (cross-ref com `tabelas`!) |
| `@todo`        | N | string | item pendente |
| `@obs`         | N | string | observação |
| `@link`        | N | string | URL externa |

### 3.3 Identificação `<id>`

- User/Static Function: `<NomeFn>` simples
- Method: `Classe::Metodo` (ex.: `TQuad::new`)
- Class: `<NomeClasse>`
- Sem `<id>`: bloco "soltinho" (raro, marca como `funcao_id=null`)

### 3.4 Algoritmo de extração

```
1. strip_advpl(content) → remove comentários e strings (já existe no plugin).
   Mas ATENÇÃO: o bloco Protheus.doc É um comentário /* */!
   → usar versão do stripper que preserva comentários TOTVS-doc, OU
   → pré-extrair os blocos antes do strip e re-injetar.
   Decisão: extrair Protheus.doc do CONTEÚDO ORIGINAL (não-stripado),
   já que comments-internos-de-comments são raros em ADVPL.
2. Match `/\*/\{Protheus\.doc\}\s*(?P<id>[\w:]+)?(?P<body>.*?)/\*/` (DOTALL).
3. Body = summary (linhas até primeiro @) + tags.
4. Tags split por `^\s*@(?P<tag>\w+)\b[ \t]*(?P<value>.*)$` com MULTILINE.
   Cada tag continua até a próxima @tag ou EOF do body.
5. Pra `@param`: parsear `<name>, <type>, <desc>` (vírgulas top-level).
   Detectar optional via colchetes em name.
6. Pra `@return`: parsear `<type>, <desc>` (vírgulas top-level).
7. Pra `@history`: parsear `<date>, <user>, <desc>`.
8. Casar bloco → função pela linha do `/*/` final + 1 (próxima decl).
9. `module_inferido`: tentar path → routine-prefix → null.
```

## 4. Schema (migration `007_universo3_protheus_docs.sql`)

```sql
CREATE TABLE protheus_docs (
  id INTEGER PRIMARY KEY,
  arquivo TEXT NOT NULL,
  funcao TEXT,                   -- nome resolvido (User Function/Method/etc)
  funcao_id TEXT,                -- <id> declarado no header (pode diferir!)
  tipo TEXT,                     -- @type normalizado: function/user_function/method/...
  module_inferido TEXT,          -- SIGAFAT, SIGAFIN, NULL
  linha_bloco_inicio INTEGER NOT NULL,
  linha_bloco_fim INTEGER NOT NULL,
  linha_funcao INTEGER,          -- linha da decl (próxima após /*/), NULL se órfão
  summary TEXT,                  -- texto livre antes da primeira @tag
  description TEXT,              -- @description
  author TEXT,                   -- @author
  since TEXT,                    -- @since
  version TEXT,                  -- @version
  deprecated INTEGER NOT NULL DEFAULT 0,  -- 0/1 (bool flag)
  deprecated_reason TEXT,        -- valor de @deprecated (se houver)
  language TEXT,                 -- @language
  params_json TEXT,              -- JSON: [{"name","type","desc","optional"}]
  returns_json TEXT,             -- JSON: [{"type","desc"}]
  examples_json TEXT,            -- JSON: [str]
  history_json TEXT,             -- JSON: [{"date","user","desc"}]
  see_json TEXT,                 -- JSON: [str]
  tables_json TEXT,              -- JSON: [str] (cross-ref com `tabelas`!)
  todos_json TEXT,               -- JSON: [str]
  obs_json TEXT,                 -- JSON: [str]
  links_json TEXT,               -- JSON: [str]
  raw_tags_json TEXT             -- JSON catch-all pra tags fora do whitelist
);

CREATE INDEX IF NOT EXISTS idx_pdoc_arquivo ON protheus_docs(arquivo);
CREATE INDEX IF NOT EXISTS idx_pdoc_funcao  ON protheus_docs(funcao);
CREATE INDEX IF NOT EXISTS idx_pdoc_module  ON protheus_docs(module_inferido);
CREATE INDEX IF NOT EXISTS idx_pdoc_author  ON protheus_docs(author);
CREATE INDEX IF NOT EXISTS idx_pdoc_dep     ON protheus_docs(deprecated);
```

**Por que tabela própria** (e não estender `chunks` ou outra existente):
- Volume diferente: 1 fonte = N docs (1 por função documentada)
- Query patterns específicos (filtrar por author/module/deprecated)
- Multi-valor (params/returns/examples) tem sintaxe estruturada — não cabe em coluna única
- JSON catch-all `raw_tags_json` permite expansão sem migração

## 5. Comando `plugadvpl docs`

```
plugadvpl docs [<modulo>] [--author <nome>] [--funcao <nome>]
               [--arquivo <basename>] [--deprecated] [--tipo <type>]
               [--show <funcao>] [--orphans]
```

### Modos de uso

| Modo | Comando | Saída |
|------|---------|-------|
| Lista | `plugadvpl docs SIGAFAT` | tabela: arquivo, funcao, summary, author, since |
| Show | `plugadvpl docs --show MT460FIM` | bloco completo formatado (markdown) |
| Orphans | `plugadvpl docs --orphans` | funções sem Protheus.doc (cross-ref BP-007) |
| Filtro | `plugadvpl docs --author "Fernando" --deprecated` | só deprecated do autor X |

### Casos de uso

1. *"Catálogo de funções documentadas do módulo SIGAFAT"* →
   `/plugadvpl:docs SIGAFAT`
2. *"Quem escreveu o quê?"* →
   `/plugadvpl:docs --author "Joao"` (case-insensitive contains)
3. *"O que está deprecated e pode ser removido?"* →
   `/plugadvpl:docs --deprecated`
4. *"Ver doc completa de uma função sem abrir o fonte"* →
   `/plugadvpl:docs --show MT460FIM`
5. *"Cobertura de documentação do projeto"* →
   `/plugadvpl:docs --orphans` (lista funções sem header)

## 6. Inferência de módulo (algoritmo)

```python
def infer_module(arquivo: str, funcao: str | None) -> str | None:
    # 1. Path-based.
    m = re.search(r"\b(SIGA\w{3,4})\b", arquivo, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # 2. Routine-prefix (reaproveita execauto_routines.json).
    if funcao:
        catalog = load_execauto_catalog()  # já existe (v0.4.1)
        for entry in catalog["routines"]:
            if funcao.upper().startswith(entry["routine"][:4]):
                return entry["module"]
    # 3. Fallback.
    return None
```

Cobertura esperada nos customizados típicos: ~70% via path (clientes
organizam por módulo), ~20% via prefixo, ~10% null (UDC/util/U_*).

## 7. Edge cases

| # | Caso | Comportamento |
|---|------|---------------|
| 1 | Bloco sem fechar (`/*/` ausente até EOF) | `extract_protheus_docs` ignora (não consegue casar regex). Lint BP-007b candidato pra próxima release |
| 2 | Bloco em string literal | Impossível em ADVPL real (strings são single-line). Não tratar |
| 3 | `@param` multi-linha | Greedy até próxima `@tag` em start-of-line. Junta com `\n` |
| 4 | `@example` com código `@param` dentro | Whitelist de tags — `@param` no MEIO da linha não conta como nova tag |
| 5 | `@param` sem 3 partes (só `@param cArg`) | `name=cArg, type=null, desc=null` |
| 6 | Acentos/encoding | Reaproveitar `file_reader.py` que já decoda UTF-8/cp1252 |
| 7 | Bloco "soltinho" sem função associada | `funcao=null, funcao_id=<id ou null>, linha_funcao=null` |
| 8 | 2+ blocos para mesma função (raro) | Persistir ambos, ordenados por linha |
| 9 | Bloco com `<id>` que não bate com função real | `funcao_id` preserva o declarado, `funcao` resolve via `_resolve_funcao_origem` (próxima decl) |
| 10 | `@deprecated` sem valor | `deprecated=1, deprecated_reason=null` |
| 11 | `@deprecated Use OutraFn` | `deprecated=1, deprecated_reason="Use OutraFn"` |
| 12 | Tag desconhecida (`@meuTag`) | Vai pro `raw_tags_json` catch-all |

## 8. Plano de implementação (TDD)

### Fase 1 — Tests RED (~60 min)
- `cli/tests/unit/test_protheus_doc.py` — 25-30 tests cobrindo §3 + §7.
- 4 classes: TestBlockParsing, TestTagExtraction, TestModuleInference, TestEdgeCases.

### Fase 2 — Detector + migration (~90 min)
- `cli/plugadvpl/parsing/protheus_doc.py` — `extract_protheus_docs(content) -> list[dict]`.
- `cli/plugadvpl/migrations/007_universo3_protheus_docs.sql`.
- Bump `SCHEMA_VERSION` 6 → 7.

### Fase 3 — Ingest wire (~30 min)
- `ingest.py` — após `execauto_calls`, chamar `extract_protheus_docs`,
  INSERT em `protheus_docs`. Idempotência: DELETE+INSERT por `arquivo`.
- Counter + meta `total_protheus_docs`.

### Fase 4 — Query + CLI (~75 min)
- `query.py` — `protheus_docs_query(conn, *, modulo, author, funcao, arquivo, deprecated, tipo)`.
- `query.py` — `protheus_docs_orphans(conn)` — funções sem doc (cross-ref com tabela `simbolos`/`chunks`).
- `cli.py` — `@app.command() def docs(...)` com `--show` e `--orphans`.
- Skill `skills/docs/SKILL.md`.

### Fase 5 — Integration tests (~30 min)
- `cli/tests/integration/test_cli.py::TestDocs` — fixture com 3 fontes
  (1 documentado completo, 1 deprecated, 1 órfão).

### Fase 6 — Release v0.4.2 (~30 min)
- Bump 20 skills (`@0.4.1` → `@0.4.2`), `plugin.json`, `marketplace.json`.
- CHANGELOG entry com **fechamento Universo 3** (A+B+C entregues).
- Final test sweep (~470+ verde esperado).
- Commit + tag + push.

**Total estimado:** ~5h.

## 9. Trade-offs e decisões a aprovar

### 9.1 Tabela própria vs. JSON-blob em `chunks`
**Recomendação:** tabela própria.
- ✅ Query patterns específicos (filtros estruturados)
- ✅ Multi-valor estruturado (params/returns)
- ✅ Catch-all JSON pra tags raras (sem migração)
- ❌ +1 tabela no schema (vale tradeoff)

### 9.2 Comando `docs` com argumento positional vs `--modulo`
**Recomendação:** positional `[modulo]` opcional.
- `plugadvpl docs SIGAFAT` é mais natural que `plugadvpl docs --modulo SIGAFAT`
- Sem arg: lista TODOS os docs (limitar a head_limit do framework)
- Mantém `--show` e `--orphans` como flags

### 9.3 Versão
**Recomendação:** v0.4.2 (incremento sobre v0.4.1).
- Universo 3 fecha aqui — natural ser dot release dentro de 0.4.x
- Schema bump 6→7 não-breaking
- Próxima major bump (0.5.0) reservada pra Universo 4 ou refactor grande

### 9.4 Inferência de módulo: path vs prefix vs ambos
**Recomendação:** ambos com fallback null.
- Path cobre cliente organizado por módulo
- Prefix cobre fonte solto fora de pasta organizada
- Null sincero quando não dá pra inferir (não inventar)

### 9.5 Modo `--show <funcao>` formato
**Recomendação:** markdown estruturado (cabeçalho + tabela params + sections).
- Fácil de copiar/colar pra issue/wiki
- Renderiza bem no `--format md` que o agente IA usa
- Exemplo:
  ```markdown
  ## MT460FIM (SIGAFAT) — `@type user function`
  Ponto de Entrada após faturamento.
  **Author:** Fernando Vernier  **Since:** 18/10/2025  **Version:** 2.0
  ### Parâmetros
  | name | type | optional | desc |
  | cNumNF | character | no | Número da NF |
  ### Retorno
  - `logical` — `.T.` se sucesso
  ```

## 10. Comparação com Features A e B

| Aspecto | A (workflow) | B (execauto) | C (docs) |
|---------|--------------|--------------|----------|
| Tabela | `execution_triggers` | `execauto_calls` | `protheus_docs` |
| Detector | `parsing/triggers.py` | `parsing/execauto.py` | `parsing/protheus_doc.py` |
| Catálogo externo | não | `execauto_routines.json` | reaproveita execauto_routines (pra módulo) |
| Comando | `workflow` | `execauto` | `docs` (com `--show`/`--orphans`) |
| Volume típico | 1-3/projeto | 10-100/projeto | 50-500/projeto (1 por função doc) |
| Schema bump | 4→5 | 5→6 | 6→7 |
| Linhas estimadas | ~280 | ~200 | ~350 (parser de tags estruturadas é mais complexo) |

## 11. Universo 3 — fechamento

Após v0.4.2, **todos os 3 mecanismos canônicos TOTVS de "rastreabilidade
não-óbvia" estarão indexados**:

- ✅ **A (v0.4.0)** — execução não-direta (workflow/schedule/job/mail)
- ✅ **B (v0.4.1)** — chamada indireta (ExecAuto chain)
- ✅ **C (v0.4.2)** — documentação inline (Protheus.doc)

Próximo passo natural pós-Universo 3: **Universo 4** (a definir — talvez
"qualidade & métricas": complexidade ciclomática, hot-paths, ownership
analytics).

## 12. Fontes (research)

### Oficial TOTVS
- [tds-vscode/docs/protheus-doc.md](https://github.com/totvs/tds-vscode/blob/master/docs/protheus-doc.md)
- [tds-vscode/docs/pdoc.md](https://github.com/totvs/tds-vscode/blob/master/docs/pdoc.md)
- [Central Atendimento — Como utilizar ProtheusDoc](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360017976051)
- [TDN — ProtheusDOC](https://tdn.totvs.com/display/tec/ProtheusDOC)

### Comunidade
- [ProtheusDoc-VSCode (Alencar Gabriel)](https://marketplace.visualstudio.com/items?itemName=AlencarGabriel.protheusdoc-vscode)
- [Mundo ADVPL — Documentando Fontes](http://mundoadvpl.blogspot.com/2014/07/documentando-fontes-advpl-com-o.html)
- [Terminal de Informação — Gerando ProtheusDoc](https://terminaldeinformacao.com/2015/08/20/gerando-e-personalizando-protheusdoc/)

### Exemplos GitHub
- [dan-atilio/AdvPL/zQuinto.prw](https://github.com/dan-atilio/AdvPL/blob/main/Fontes/zQuinto.prw) — User Function completa
- [ftvernier/erp-solutions/MT460FIM.tlpp](https://github.com/ftvernier/erp-solutions/blob/main/kafka/MT460FIM.tlpp) — Ponto de Entrada
- [GillesK/Protheus-Advpl-OO-Framework/TSUtils.prw](https://github.com/GillesK/Protheus-Advpl-OO-Framework/blob/master/Utils/TSUtils.prw) — Class + Methods
- [danielAlbuquerque/tlpp-rest-api-boilerplate/AuthFilter.tlpp](https://github.com/danielAlbuquerque/tlpp-rest-api-boilerplate/blob/main/src/Filter/AuthFilter.tlpp) — TLPP/WSRESTFUL

---

## Perguntas pra aprovar antes de codar

1. **Tabela própria `protheus_docs`** vs JSON-blob em `chunks`? *(rec: própria)*
2. **Comando `docs` positional `[modulo]`** vs `--modulo`? *(rec: positional opcional)*
3. **Modo `--show` em markdown estruturado**? *(rec: sim)*
4. **Modo `--orphans`** (cross-ref BP-007 — funções sem header)? *(rec: sim, atalho útil)*
5. **Inferência de módulo: path + prefix + fallback null**? *(rec: ambos)*
6. **Versão v0.4.2** (vs v0.5.0)? *(rec: v0.4.2, fecha Universo 3 dentro do 0.4.x)*
7. **16 tags canônicas no MVP**? *(rec: sim, raw_tags_json catch-all pra resto)*
