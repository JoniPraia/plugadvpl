---
description: Re-indexa um arquivo especifico no indice plugadvpl
disable-model-invocation: true
arguments: [arquivo]
allowed-tools: [Bash]
---

# `/plugadvpl:reindex`

Re-indexa um arquivo especifico (forca atualizacao mesmo se hash/mtime nao mudou).

## Uso

```
/plugadvpl:reindex <arquivo>
```

## Execucao

```bash
uvx plugadvpl@0.3.17 reindex $arquivo
```

## Exemplos

- `/plugadvpl:reindex src/matxxx.prw` — reindex de um arquivo apos edicao
- `/plugadvpl:reindex include/totvs.ch` — reindex de um include

## Quando usar

- Apos editar um fonte e querer atualizar o indice imediatamente
- Quando suspeita-se que o indice esta defasado para um arquivo
- Para validar que parser/lint produzem saida esperada para um fonte

## Proximos passos sugeridos

- `/plugadvpl:arch <arquivo>` — confirma visao arquitetural atualizada
- `/plugadvpl:lint <arquivo>` — roda lint apos reindex
