---
name: Parser/lint false-positive ou false-negative
about: Parser não detecta algo que deveria, ou detecta errado
title: '[parser] '
labels: bug, parser
assignees: ''
---

## Tipo

- [ ] Parser **não detectou** algo que deveria (false-negative)
- [ ] Parser **detectou errado** (false-positive)
- [ ] Lint regra X **não disparou** quando devia
- [ ] Lint regra X **disparou** quando não devia

## Fonte mínimo de reprodução

**Cole aqui um `.prw/.tlpp` mínimo** (10-30 linhas) que reproduz o problema.
Sem fonte minimal, parser issues são quase impossíveis de corrigir.

```advpl
// fonte aqui
```

## O que o parser/lint devolveu

```
<saída de plugadvpl arch <fonte>, plugadvpl callers <funcao>, plugadvpl lint <fonte>, etc>
```

## O que deveria ter devolvido

<descreva: "deveria ter detectado a tabela SA1 em DbSelectArea(\"SA1\")", etc.>

## Versão

- **plugadvpl**: `<plugadvpl version>`
- **OS**: <Windows / Linux / macOS>
