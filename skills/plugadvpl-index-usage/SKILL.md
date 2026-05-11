---
description: Como usar o índice plugadvpl para consultar metadados ADVPL antes de ler fontes inteiros. Use SEMPRE que analisar projeto com .plugadvpl/.
---

# plugadvpl-index-usage — Skill-chefe

Quando o projeto tem `.plugadvpl/index.db`, **Claude DEVE consultar o índice antes de qualquer `Read` em fonte ADVPL**. Fontes Protheus têm tipicamente 1.000–10.000 linhas — abrir cru queima contexto, escala mal e produz respostas vagas.

## Quando usar

Esta skill ativa sempre que:

- O projeto atual contém `.plugadvpl/` (detectado pelo fragment `<!-- BEGIN plugadvpl -->` em `CLAUDE.md`).
- O usuário pergunta sobre arquivos `.prw`, `.prx`, `.tlpp` (ou pede análise/edição).
- Antes de qualquer chamada `Read` em fonte ADVPL — **sem exceção**.
- Para localizar funções, callers/callees, uso de tabelas, parâmetros MV_, SQL embarcado.

## Regra de decisão — qual ferramenta usar

| Pergunta do usuário                               | Comando primeiro                          |
|---------------------------------------------------|-------------------------------------------|
| "O que faz o fonte X?"                            | `/plugadvpl:arch X`                       |
| "Onde está a função Y?"                           | `/plugadvpl:find function Y`              |
| "Quem chama Y?"                                   | `/plugadvpl:callers Y`                    |
| "O que Y chama por dentro?"                       | `/plugadvpl:callees Y`                    |
| "Quem lê/grava na tabela SA1?"                    | `/plugadvpl:tables SA1`                   |
| "Onde MV_LOCALIZA é usado?"                       | `/plugadvpl:param MV_LOCALIZA`            |
| "Mostre SQL de update em SC5"                     | `/plugadvpl:sql --op update --table SC5`  |
| "Tem erro de boas práticas em X?"                 | `/plugadvpl:lint X`                       |
| "Achar função que faz <descrição>"                | `/plugadvpl:grep "<termo>"`               |
| "Essa função é nativa do TOTVS?"                  | `/plugadvpl:find function <nome>`         |
| "Posso usar `StaticCall`?"                        | Consulte `funcoes_restritas` (catalogada) |

## Quando É permitido `Read` no `.prw` cru

Só **depois** de localizar a linha exata via índice. Exemplos válidos:

- `Read FATA050.prw` com `offset=234, limit=46` (intervalo 234–280 identificado em `sql_refs`).
- `Read MATA461.prw` com `limit=50` (apenas header/cabeçalho).

**NUNCA** abra o arquivo inteiro sem range — isso queima ~50k tokens por fonte médio e desperdiça contexto que poderia caber 10 arquivos analisados via índice.

## Workflow recomendado

1. Receba a pergunta do usuário.
2. Mapeie para um comando da tabela acima.
3. Rode o slash command (resultado limitado a 20 entradas por default).
4. Refine com `--module/--table/--path` se vier "... e mais N resultados".
5. Só então, se ainda precisar do código exato, faça `Read` com `offset+limit` apontando para a linha retornada.

## Output budget

Todo comando retorna no máximo 20 resultados (`--limit 20`). Se a saída indicar  
"... e mais N resultados; refine com --table/--module/--path", **refine com filtros**, não peça mais resultados sem critério. Comandos suportam `--compact` para uma-linha-por-registro.

## Saúde do índice

Antes de confiar em consultas, em sessão nova rode `/plugadvpl:status` para conferir contagens e última ingestão. Se arquivos foram editados fora do Claude (IDE, git pull), execute `/plugadvpl:reindex <arquivo>` ou `/plugadvpl:ingest --incremental`.

## Anti-padrões

- Ler `.prw` cru "para entender o contexto" — **proibido**. Use `arch` primeiro.
- Pedir ao usuário para colar trechos do fonte — o índice já tem os metadados.
- Usar `Grep` direto no diretório com regex genérica em vez de `find/grep` do plugadvpl (que retorna chunks/funções, não linhas soltas).
- Ignorar `--limit`: pedir todos os resultados em base com 24k fontes é estouro de contexto garantido.

## Referência rápida

| Tabela do índice           | Para que serve                           |
|----------------------------|------------------------------------------|
| `sources`                  | Lista de fontes ingestos, encoding, mtime |
| `simbolos`                 | Funções, classes, métodos, includes      |
| `calls`                    | Quem chama quem (caller × callee)        |
| `tabelas`                  | Uso de tabelas ERP (SA1, SC5, etc.)      |
| `params`                   | Uso de parâmetros MV_/AcessaCpo          |
| `sql_refs`                 | SQL embarcado (BeginSQL/TCQuery)         |
| `ws_services` + `ws_structures` | WSRESTFUL/WSSERVICE                |
| `mvc_hooks`                | Hooks MVC (bCommit, bTudoOk, etc.)       |
| `lint_findings`            | Achados do lint (24 regras catalogadas)  |

## Comandos plugadvpl relacionados

`/plugadvpl:arch`, `/plugadvpl:find`, `/plugadvpl:callers`, `/plugadvpl:callees`,
`/plugadvpl:tables`, `/plugadvpl:param`, `/plugadvpl:lint`, `/plugadvpl:status`,
`/plugadvpl:ingest`, `/plugadvpl:reindex`, `/plugadvpl:grep`, `/plugadvpl:doctor`,
`/plugadvpl:help`.
