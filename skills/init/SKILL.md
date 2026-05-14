---
description: Inicializa plugadvpl no projeto atual (cria .plugadvpl/index.db, fragment CLAUDE.md, atualiza .gitignore)
disable-model-invocation: true
allowed-tools: [Bash]
---

# `/plugadvpl:init`

Inicializa o indice plugadvpl no projeto atual.

## Uso

```
/plugadvpl:init
```

## Execucao

```bash
uvx plugadvpl@0.3.14 init
```

## O que faz

1. Cria `.plugadvpl/index.db` (SQLite + FTS5)
2. Aplica migrations (schema completo: sources, simbolos, calls, tabelas, params, includes, includes_resolved, sql_refs, ws_structures, ws_services, mvc_hooks, defines, lint_findings + lookups)
3. Carrega lookups (6 catalogos: funcoes_nativas, funcoes_restritas, lint_rules, sql_macros, modulos_erp, pontos_entrada_padrao)
4. Escreve fragment delimitado em `CLAUDE.md` instruindo Claude a consultar o indice antes de Read
5. Adiciona `.plugadvpl/` ao `.gitignore`

## Exemplos

- `/plugadvpl:init` — inicializa no projeto atual

## Proximos passos sugeridos

- Apos init, execute `/plugadvpl:ingest` para indexar os fontes
- Verifique a saude do indice com `/plugadvpl:status`
- Use `/plugadvpl:doctor` para diagnosticar problemas de ambiente
