---
description: Como usar o indice plugadvpl para consultar metadados ADVPL antes de ler fontes inteiros. Ative SEMPRE antes de Read em .prw/.prx/.tlpp/.apw, find por funcao, callers/callees, uso de tabela ou MV_, impacto de campo SX3, cadeia de gatilhos SX7, ou lint. Ganho tipico 10-50x em tokens.
---

# plugadvpl-index-usage — Skill-chefe

Quando o projeto tem `.plugadvpl/index.db`, **Claude DEVE consultar o indice antes de qualquer `Read` em fonte ADVPL**. Fontes Protheus tem tipicamente 1.000-10.000 linhas — abrir cru queima contexto, escala mal e produz respostas vagas.

> **Token math:** 20 results do indice ≈ 1.000 tokens. 1 fonte `.prw` cru ≈ 5.000-50.000 tokens. **10-50× menos contexto** por pergunta, sem perder precisao.

## Quando usar

Esta skill ativa sempre que:

- O projeto atual contem `.plugadvpl/` (detectado pelo fragment `<!-- BEGIN plugadvpl -->` em `CLAUDE.md`).
- O usuario pergunta sobre arquivos `.prw`, `.prx`, `.tlpp`, `.apw` (ou pede analise/edicao).
- **Antes de qualquer chamada `Read` em fonte ADVPL** — sem excecao.
- Para localizar funcoes, callers/callees, uso de tabelas, parametros MV_, SQL embarcado, cadeias SX7, impacto de campos SX3.

## Regra de decisao — qual ferramenta usar

| Pergunta do usuario                                | Comando primeiro                              |
|----------------------------------------------------|-----------------------------------------------|
| "O que faz o fonte X?"                             | `/plugadvpl:arch X` (veja workflow abaixo)    |
| "Onde esta a funcao Y?"                            | `/plugadvpl:find function Y`                  |
| "Quem chama Y?"                                    | `/plugadvpl:callers Y`                        |
| "O que Y chama por dentro?"                        | `/plugadvpl:callees Y`                        |
| "Quem le/grava na tabela SA1?"                     | `/plugadvpl:tables SA1` (`--mode read/write/reclock`) |
| "Onde MV_LOCALIZA e usado?"                        | `/plugadvpl:param MV_LOCALIZA`                |
| "Onde SC5 e gravada/atualizada?"                   | `/plugadvpl:tables SC5 --mode write`          |
| "Procura texto/regex no projeto"                   | `/plugadvpl:grep "<padrao>"`                  |
| "Tem erro de boas praticas em X?"                  | `/plugadvpl:lint X`                           |
| "Roda lint cross-file (regras SX-001..SX-011)"     | `/plugadvpl:lint --cross-file`                |
| "Achar funcao que faz <descricao>"                 | `/plugadvpl:grep "<termo>"`                   |
| "Essa funcao e nativa do TOTVS?"                   | `/plugadvpl:find function <nome>` (vs `funcoes_nativas`) |
| "Posso usar `StaticCall`?"                         | `/plugadvpl:find function StaticCall` (tabela `funcoes_restritas` lista as 195 proibidas) |
| **Universo 2 — Dicionario SX (v0.3.0):**          |                                               |
| "Importa o dicionario SX (CSVs)"                   | `/plugadvpl:ingest-sx <pasta-csv>`            |
| "Cruza referencias de campo A1_COD"                | `/plugadvpl:impacto A1_COD` (killer feature)  |
| "Cadeia de gatilhos SX7 de A1_COD"                 | `/plugadvpl:gatilho A1_COD --depth 3`         |
| "Status do dicionario SX (counts por tabela)"      | `/plugadvpl:sx-status`                        |

> Para refactor/bug/debug, veja tambem `[[advpl-code-review]]`, `[[advpl-refactoring]]`,
> `[[advpl-debugging]]`. Para validacoes embutidas em X3_VALID/X7_REGRA, veja
> `[[advpl-dicionario-sx-validacoes]]`.

## Quando E permitido `Read` no `.prw` cru

So **depois** de localizar a linha exata via indice. Exemplos validos:

- `Read FATA050.prw` com `offset=234, limit=46` (intervalo 234-280 identificado em `sql_embedado`).
- `Read MATA461.prw` com `limit=50` (apenas header/cabecalho).

**NUNCA** abra o arquivo inteiro sem range. Exemplo concreto:

| Acao                                       | Tokens consumidos |
|--------------------------------------------|-------------------|
| `Read MATA461.prw` (4.500 linhas, cru)     | ~12.000 tokens    |
| `/plugadvpl:arch MATA461.prw`              | ~600 tokens       |
| `/plugadvpl:lint MATA461.prw`              | ~400 tokens       |

Diferenca: **20x** menos contexto, com a mesma resposta (e mais estruturada).

## Workflow recomendado — "Explique o que faz o programa X"

A pergunta mais comum do usuario merece um caminho explicito:

1. **`/plugadvpl:arch X`** — visao arquitetural: tipo de fonte, capabilities, funcoes, tabelas usadas, includes. Sempre comecar aqui.
2. **`/plugadvpl:lint X --severity critical,error`** — health check, ja revela bugs estruturais.
3. Se a saida do `arch` citou uma funcao chave:
   - **`/plugadvpl:callers <funcao>`** — entende quem usa (o "porque")
   - **`/plugadvpl:callees <funcao>`** — entende o que ela faz (o "como")
4. Se citou tabelas relevantes:
   - **`/plugadvpl:tables <T> --mode write`** — quem grava, transacoes criticas
5. Se for fonte de cadastro/customizacao SX:
   - **`/plugadvpl:impacto <campo-chave>`** — cadeia completa de impacto cross-camadas
6. **So entao**, se algo especifico ainda faltou: `Read X` com `offset+limit` apontando para a linha retornada nos passos 1-5.

## Workflow generico

1. Receba a pergunta do usuario.
2. Mapeie para um comando da tabela acima.
3. Rode o slash command (resultado limitado a 20 entradas por default).
4. Refine com `--module/--table/--path` se vier "... e mais N resultados".
5. Use `--format json` se for parsear programaticamente, ou `--compact` para uma-linha-por-registro.
6. So entao, se ainda precisar do codigo exato, faca `Read` com `offset+limit` apontando para a linha retornada.

## Output budget

Todo comando retorna no maximo 20 resultados (`--limit 20`). Se a saida indicar  
"... e mais N resultados; refine com --table/--module/--path", **refine com filtros**, nao peca mais resultados sem criterio. Comandos suportam `--compact` para uma-linha-por-registro.

## Saude do indice

Antes de confiar em consultas, em sessao nova rode `/plugadvpl:status` para conferir contagens e ultima ingestao. Se arquivos foram editados fora do Claude (IDE, git pull), execute `/plugadvpl:reindex <arquivo>` ou `/plugadvpl:ingest --incremental`.

Para checar integridade do indice (encoding, orfaos, FTS dessincronizado): `/plugadvpl:doctor`.

## Anti-padroes

- **Ler `.prw` cru "para entender o contexto"** — proibido. Exemplo concreto: `Read MATA461.prw` (12k tokens) versus `/plugadvpl:arch MATA461.prw` (600 tokens). 20x mais barato, resposta mais estruturada.
- **Pedir ao usuario para colar trechos do fonte** — o indice ja tem os metadados. Pergunte qual fonte/funcao e use o comando.
- **Usar `Grep` direto no diretorio com regex generica** em vez de `find/grep` do plugadvpl (que retorna chunks/funcoes, nao linhas soltas).
- **Ignorar `--limit`**: pedir todos os resultados em base com 2.000+ fontes e estouro de contexto garantido.
- **Iniciar lint cross-file sem ter rodado `ingest-sx`**: regras SX-001..SX-011 dependem do dicionario SX ingerido.

## Referencia rapida — tabelas do indice (Universo 1: fontes)

| Tabela do indice               | Para que serve                                       |
|--------------------------------|------------------------------------------------------|
| `fontes`                       | Lista de fontes ingestos, encoding, mtime, sha       |
| `fonte_chunks`                 | Funcoes/main funcs com ranges, conteudo, FTS5        |
| `funcao_docs`                  | Doc-comments extraidos das funcoes                   |
| `chamadas_funcao`              | Call graph: quem chama quem (caller × callee)        |
| `fonte_tabela`                 | Uso de tabelas ERP (SA1, SC5, etc.) — read/write/reclock |
| `parametros_uso`               | Uso de parametros `MV_*` / `AcessaCpo`               |
| `perguntas_uso`                | `Pergunte()` calls — grupo SX1 + linha               |
| `operacoes_escrita`            | `RecLock`+`Replace`+`MsUnlock` — operacoes de escrita |
| `sql_embedado`                 | SQL embarcado (`BeginSql`/`TCQuery`/`MPSysOpenQuery`) |
| `rest_endpoints`               | `WSRESTFUL`/`WSMETHOD` endpoints                     |
| `http_calls`                   | Clientes HTTP — `HttpPost`, `RestRun`, etc.          |
| `env_openers`                  | `RpcSetEnv`/`PrepareEnv` calls                       |
| `log_calls`                    | `ConOut`/`FwLogMsg` calls                            |
| `defines`                      | `#define` constants extraidos                        |
| `lint_findings`                | Achados do lint (35 regras: 24 single-file + 11 cross-file SX-*) |

**Lookups (catalogos pre-populados):**

| Tabela           | O que cataloga                                              |
|------------------|-------------------------------------------------------------|
| `funcoes_nativas`| ~280 funcoes built-in TOTVS (saber o que e nativo vs custom) |
| `funcoes_restritas` | 195 funcoes proibidas/internas (`SEC-005` lint)          |
| `lint_rules`     | 24 regras single-file + 11 cross-file SX-001..SX-011        |
| `sql_macros`     | 6 macros do `BeginSql` (`%xfilial%`, `%notDel%`, etc.)      |
| `modulos_erp`    | 8 modulos Protheus (FAT/COM/EST/FIN/CTB/RH/MAT/PCO)         |
| `pontos_entrada_padrao` | 15 PEs padrao (MA040ALT/MT100GRV/etc.)               |

## Referencia rapida — tabelas Universo 2 (Dicionario SX, v0.3.0)

Disponiveis apos `/plugadvpl:ingest-sx <pasta-csv>`. Veja `[[advpl-dicionario-sx]]`.

| Tabela              | Origem CSV | Para que serve                                |
|---------------------|------------|-----------------------------------------------|
| `tabelas`           | SX2        | Tabelas dicionarizadas (X2_CHAVE, modo C/E/U) |
| `campos`            | SX3        | Campos: tipo, tamanho, X3_VALID, X3_INIT, etc.|
| `indices`           | SIX        | Indices de tabela                             |
| `gatilhos`          | SX7        | Gatilhos: campo origem -> destino, regra      |
| `parametros`        | SX6        | Parametros MV_* — definicao + default         |
| `perguntas`         | SX1        | Perguntas de relatorios — grupo + defs        |
| `tabelas_genericas` | SX5        | Tabelas genericas (codigo-descricao)          |
| `relacionamentos`   | SX9        | Relacionamentos entre tabelas                 |
| `pastas`            | SXA        | Pastas das telas de cadastro                  |
| `consultas`         | SXB        | Consultas (F3 lookup)                         |
| `grupos_campo`      | SXG        | Grupos de tamanho/template de campo           |

## Comandos plugadvpl relacionados (todos os 18)

**Universo 1 (fontes):** `/plugadvpl:init`, `/plugadvpl:ingest`, `/plugadvpl:reindex`,
`/plugadvpl:status`, `/plugadvpl:find`, `/plugadvpl:callers`, `/plugadvpl:callees`,
`/plugadvpl:tables`, `/plugadvpl:param`, `/plugadvpl:arch`, `/plugadvpl:lint`,
`/plugadvpl:grep`, `/plugadvpl:doctor`, `/plugadvpl:help`.

**Universo 2 (dicionario SX):** `/plugadvpl:ingest-sx`, `/plugadvpl:impacto`,
`/plugadvpl:gatilho`, `/plugadvpl:sx-status`.

Detalhes em `/plugadvpl:help` ou `docs/cli-reference.md`.
