---
description: Catálogo de Protheus.doc agregado por módulo/autor/deprecated + show formatado por função (Universo 3 Feature C, v0.4.2+)
disable-model-invocation: true
arguments: [modulo|filtros]
allowed-tools: [Bash]
---

# `/plugadvpl:docs`

**Killer feature do v0.4.2** (Universo 3 — Rastreabilidade Feature C, **fecha Universo 3**). Agrega blocos `/*/{Protheus.doc} ... /*/` indexados por módulo, autor, tipo, e estado de deprecação. Antes do v0.4.2 era impossível responder "lista funções documentadas do SIGAFAT", "quem é autor de X", "o que está deprecated" sem grep manual.

## Por quê

```
$ plugadvpl find MT460FIM
arquivo:    src/SIGAFAT/MT460FIM.tlpp
funcao:     MT460FIM
linha:      22
# ← sem documentação, sem author, sem since, sem @param.
#   Pra ver doc tinha que abrir o fonte e ler 30 linhas de header.
```

Agora:

```
$ plugadvpl docs --show MT460FIM
## MT460FIM (SIGAFAT) — `@type user function`

Ponto de Entrada apos faturamento. Envia ao Kafka.

**Author:** Fernando Vernier  **Since:** 18/10/2025  **Version:** 2.0

### Parâmetros
| name   | type      | optional | desc           |
| cNumNF | character | não      | Número da NF   |

### Retorno
- `logical` — `.T. se sucesso`
```

## Uso

```
/plugadvpl:docs [<modulo>] [--author <nome>] [--funcao <nome>]
                [--arquivo <basename>] [--deprecated|--no-deprecated]
                [--tipo <type>] [--show <funcao>] [--orphans]
```

## Modos de uso

| Modo | Comando | Saída |
|------|---------|-------|
| Lista por módulo | `plugadvpl docs SIGAFAT` | tabela: arquivo, funcao, modulo, tipo, author, since, deprecated, summary |
| Lista global | `plugadvpl docs` | tudo (limitar com `--limit`) |
| Show formatado | `plugadvpl docs --show MT460FIM` | bloco completo Markdown |
| Orphans (sem doc) | `plugadvpl docs --orphans` | cross-ref BP-007 do lint |

## Opções

- `[modulo]` — argumento positional opcional (`SIGAFAT`/`SIGACOM`/`SIGAFIN`/...)
- `--author` — LIKE `%valor%` case-insensitive (busca parcial no autor)
- `--funcao` / `-f` — exact match no nome de função
- `--arquivo` / `-a` — filtra por basename
- `--deprecated` / `--no-deprecated` — filtra @deprecated (ou exclui)
- `--tipo` / `-t` — filtra `@type`: `function`, `user function`, `static function`, `method`, `class`, `property`
- `--show <funcao>` — exibe doc completo Markdown (vs lista)
- `--orphans` — funções SEM header (cross-ref `lint --regra BP-007`)

## Execução

```bash
uvx plugadvpl@0.4.3 --format md docs $ARGUMENTS
```

> **Para agente IA:** prefira `--format md` (sem truncamento). Default `table` Rich trunca colunas em terminais estreitos.

## Exemplos

- `/plugadvpl:docs SIGAFAT` — catálogo do módulo Faturamento
- `/plugadvpl:docs --author "Fernando"` — todas as funções do autor X (LIKE parcial)
- `/plugadvpl:docs --deprecated` — o que está marcado pra remover
- `/plugadvpl:docs --tipo method` — só métodos de classe
- `/plugadvpl:docs --show MT460FIM` — doc completo formatado em Markdown
- `/plugadvpl:docs --orphans` — funções sem header (atalho pro lint BP-007)
- `/plugadvpl:docs --funcao MT460FIM --no-deprecated` — só se NÃO está deprecated

## Saída — modo lista

| Campo | Significado |
|-------|-------------|
| `arquivo`   | fonte que tem o bloco |
| `funcao`    | função resolvida (próxima decl após `/*/`) |
| `modulo`    | módulo inferido (path-based + routine-prefix) |
| `tipo`      | `@type` normalizado (lowercase) |
| `author`    | `@author` |
| `since`     | `@since` |
| `deprecated`| `sim` se `@deprecated` |
| `summary`   | texto antes da primeira `@tag` (truncado a 80 chars) |

Campos extras só visíveis em `--format json`:

| Campo | Significado |
|-------|-------------|
| `funcao_id`         | `<id>` declarado no header (pode diferir de `funcao`) |
| `linha_bloco_inicio` / `linha_bloco_fim` | linhas do bloco |
| `linha_funcao`      | linha da decl (ou `null` se órfão) |
| `description`       | `@description` |
| `version`           | `@version` |
| `deprecated_reason` | valor de `@deprecated` (se houver) |
| `language`          | `@language` |
| `params[]`          | `[{name, type, desc, optional}]` |
| `returns[]`         | `[{type, desc}]` |
| `examples[]`        | código de `@example` |
| `history[]`         | `[{date, user, desc}]` |
| `see[]`             | `@see` referências cruzadas |
| `tables[]`          | `@table` (cross-ref com `tabelas`) |
| `todos[]`           | `@todo` |
| `obs[]`             | `@obs` |
| `links[]`           | `@link` URLs |
| `raw_tags{}`        | tags fora do whitelist (catch-all) |

## Tags canônicas suportadas (16)

Padrão oficial TOTVS: [tds-vscode/docs/protheus-doc.md](https://github.com/totvs/tds-vscode/blob/master/docs/protheus-doc.md)

| Single | Multi-valor | Flag |
|--------|-------------|------|
| `@type` | `@param` | `@deprecated` (também aceita reason) |
| `@author` | `@return` | |
| `@since` | `@example` / `@sample` | |
| `@version` | `@history` | |
| `@description` | `@see` | |
| `@language` | `@table` | |
| | `@todo` | |
| | `@obs` | |
| | `@link` | |

Tags fora dessa lista vão pro `raw_tags` — nada se perde.

## Inferência de módulo

Algoritmo (em ordem):

1. **Path**: regex `SIGA\w{3,4}` no path do fonte (ex.: `src/SIGAFAT/X.prw`)
2. **Routine prefix**: usa o catálogo já existente da Feature B (`execauto_routines.json`) — `MATA*` → SIGAFAT, `FINA*` → SIGAFIN, `CTBA*` → SIGACTB, etc. Match exato primeiro, depois prefixo de 4 chars
3. **Fallback**: `null` (parser não inventa)

Cobertura típica: ~70% via path, ~20% via prefix, ~10% null (UDC/util).

## Casos de uso

1. **Catálogo do módulo Faturamento** —
   `/plugadvpl:docs SIGAFAT`

2. **Onboarding: ver tudo do autor X** —
   `/plugadvpl:docs --author "Fernando"`

3. **Limpeza: o que está deprecated?** —
   `/plugadvpl:docs --deprecated`

4. **Documentação inline sem abrir o fonte** —
   `/plugadvpl:docs --show MT460FIM` (ideal pra agente IA copiar pro contexto)

5. **Cobertura de documentação do projeto** —
   `/plugadvpl:docs --orphans` (funções sem header, atalho BP-007)

6. **Migração: funções deprecated ainda sendo chamadas** —
   `/plugadvpl:docs --deprecated --format json | jq '.rows[].funcao'` →
   pra cada nome: `/plugadvpl:callers <nome>` (ver quem ainda chama)

## Cross-ref com outras features

- **`/plugadvpl:lint --regra BP-007`** — equivalente RAW do `--orphans` (mesmo dado, formato diferente).
- **`/plugadvpl:callers <funcao>`** — pra ver quem chama uma função documentada.
- **`/plugadvpl:arch <arquivo>`** — visão geral do fonte (capabilities + tabelas).
- **`/plugadvpl:execauto`** (Feature B) — usa o mesmo catálogo `execauto_routines.json` pra inferir módulo.
- **`/plugadvpl:workflow`** (Feature A) — workflows/jobs documentados aparecem em `docs` se tiverem header.

## Limitações conhecidas

- **Headers legados pré-Protheus.doc** (ASCII art `+--+` tabular) — não detectados. Heurística separada futura.
- **Inline `//{pdoc}`** (associado a próxima variável/property) — não no MVP. Raro.
- **Bloco sem `/*/` de fechamento** — ignorado (regex não casa). BP-007b candidato pra release dot.
- **Cross-validação `@param` vs assinatura real** — não no MVP. BP-009 candidato.
- **Geração de HTML/MD output style TDS** — fora de escopo. Plugin é índice, não doc-generator.

## Próximos passos sugeridos

- `/plugadvpl:docs --show <funcao>` — depois de localizar via lista
- `/plugadvpl:callers <funcao>` — quem chama essa função documentada
- `/plugadvpl:lint --regra BP-007 --format json` — findings raw cross-ref orphans
