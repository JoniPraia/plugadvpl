---
description: Mostra status do indice plugadvpl (contagem de fontes, simbolos, tamanho do DB, ultima ingest)
disable-model-invocation: true
allowed-tools: [Bash]
---

# `/plugadvpl:status`

Mostra status do indice plugadvpl no projeto atual.

## Uso

```
/plugadvpl:status [--check-stale]
```

## Opcoes

- `--check-stale` — verifica fontes cujo hash/mtime divergem do indice (detecta defasagem)

## Execucao

```bash
uvx plugadvpl@0.3.14 --format md status $ARGUMENTS
```

## Saida

Linhas relevantes (todas como dict de 1 row):

| Campo                | Significado                                                              |
|----------------------|--------------------------------------------------------------------------|
| `runtime_version`    | **versao do binario rodando AGORA** (`plugadvpl.__version__`) — v0.3.12+ |
| `plugadvpl_version`  | versao do binario que **gravou o indice** (frozen no init/ingest)        |
| `cli_version`        | versao do binario que rodou o **ultimo ingest** (idem)                   |
| `parser_version`     | versao do parser usado na ingest                                         |
| `schema_version`     | versao do schema SQLite (das migrations aplicadas)                       |
| `indexed_at`         | timestamp ISO da ultima ingest                                           |
| `total_arquivos`     | numero de fontes indexados                                               |
| `total_chunks`       | total de funcoes/chunks                                                  |
| `total_chamadas`     | total de calls indexadas (call graph)                                    |
| `total_lint_findings`| total de achados do lint (somente em `lint_findings`)                    |
| `lookup_bundle_hash` | hash dos lookups (funcoes_restritas, lint_rules, etc.)                   |

> **v0.3.12 — divergencia runtime vs indice:** se `runtime_version != plugadvpl_version`, o `status` imprime aviso amarelo em **stderr** orientando `plugadvpl ingest --incremental` para ganhar regras/parsers da versao nova. Use `--quiet` se quiser suprimir o aviso.

Quando `--check-stale`: lista adicional de arquivos com `mtime` defasado.

## Exemplos

- `/plugadvpl:status` — visao geral rapida
- `/plugadvpl:status --check-stale` — detecta arquivos defasados para reindex
- `plugadvpl --version` — apenas a versao do binario (sem precisar do `status` inteiro)

## Para descobrir "qual versao do plugadvpl esta instalada?"

Tres caminhos validos, cada um responde uma pergunta diferente:

| Comando                        | Responde                                                  |
|--------------------------------|-----------------------------------------------------------|
| `plugadvpl --version` (ou `-V`) | "qual binario esta rodando AGORA?" — eager flag, v0.3.12+ |
| `plugadvpl version`            | mesma resposta, via subcomando antigo                     |
| `plugadvpl status`             | "binario AGORA + binario que gravou indice + sao iguais?" |
| `uv tool list`                 | "qual versao o `uv` instalou no PATH?"                    |

> **Pegadinha:** `plugadvpl status` historicamente mostrava SO a versao gravada no indice (frozen no ingest). Apos `uv tool upgrade` o binario mudava mas o status continuava mostrando a antiga, confundindo agentes IA. Em **v0.3.12** o status mostra as duas (`runtime_version` + `plugadvpl_version`) e avisa quando divergem.

## Proximos passos sugeridos

- Se houver arquivos stale, rode `/plugadvpl:ingest` (incremental) ou `/plugadvpl:reindex <arquivo>`
- Se `runtime_version != plugadvpl_version`, rode `/plugadvpl:ingest --incremental` para refletir o binario novo
- `/plugadvpl:doctor` — diagnostico do ambiente
