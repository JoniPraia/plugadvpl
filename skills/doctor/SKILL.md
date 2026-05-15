---
description: Diagnostica ambiente plugadvpl (uv, sqlite, FTS5, schema, lookups, permissoes)
disable-model-invocation: true
allowed-tools: [Bash]
---

# `/plugadvpl:doctor`

Diagnostica ambiente e indice plugadvpl. Util para troubleshooting.

## Uso

```
/plugadvpl:doctor [--env] [--quiet]
```

## Opcoes

- `--env` — imprime apenas info de ambiente (uv, python, sqlite, plataforma)
- `--quiet` — saida compacta (apenas falhas)

## Execucao

```bash
uvx plugadvpl@0.3.24 doctor $ARGUMENTS
```

## Checks

- `uvx` disponivel e versao do plugadvpl
- Python embarcado / venv
- SQLite com suporte FTS5
- `.plugadvpl/index.db` existe e e acessivel
- Schema na versao esperada (migrations aplicadas)
- 6 lookups carregadas (hash bate)
- Permissoes de escrita em `.plugadvpl/`
- Encoding/locale (CP1252 vs UTF-8)
- Espaco em disco

## Exemplos

- `/plugadvpl:doctor` — bateria completa
- `/plugadvpl:doctor --env` — so ambiente
- `/plugadvpl:doctor --quiet` — so o que esta falhando

## Saida

Para cada check:
- OK / WARN / FAIL
- detalhe quando aplicavel
- sugestao de correcao em caso de FAIL

## Proximos passos sugeridos

- Se schema desatualizado: `/plugadvpl:init` novamente
- Se lookups stale: reingest (a init carrega lookups)
- Se DB ausente/corrompido: remover `.plugadvpl/` e `/plugadvpl:init`
