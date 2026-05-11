---
description: 24 regras de code review ADVPL (BP/SEC/PERF/MOD). No MVP plugadvpl v0.1, 13 são detectadas via regex single-file; 11 deferidas para v0.2 (semantic/cross-file). Use após gerar/editar código ADVPL.
---

# advpl-code-review — As 24 regras de code review

`plugadvpl` cataloga **24 regras de code review** para ADVPL/TLPP, agrupadas em 4 categorias:

- **BP-xxx** — Best-Practice (8 regras).
- **SEC-xxx** — Segurança (5 regras).
- **PERF-xxx** — Performance (6 regras).
- **MOD-xxx** — Modernização (4 regras).

No **MVP v0.1**, 13 regras são detectáveis com **regex single-file** (rápido, alto recall). As outras 11 ficam catalogadas em `lint_rules` mas só serão detectadas no **v0.2** (análise semantic / cross-file).

## Quando usar

- Logo após gerar/editar qualquer fonte ADVPL.
- Antes de marcar tarefa como "concluída".
- Quando usuário pede "revise este código" / "tem boa prática aqui?".
- Antes de propor PR / commit.

Rode `/plugadvpl:lint <arq>` para resultado de fato — esta skill é o **guia mental** das regras.

## As 24 regras — quick reference

### Best Practice (BP)

| ID         | Sev      | Título                                                          | v0.1 |
|------------|----------|-----------------------------------------------------------------|------|
| `BP-001`   | critical | `RecLock` sem `MsUnlock` correspondente                         | ✅   |
| `BP-002`   | error    | `Local` declarado fora do header da função                      | ✅   |
| `BP-002b`  | warning  | Variável como `Private`/`Public` em vez de `Local`              | ✅   |
| `BP-003`   | warning  | Falta `GetArea/RestArea` em função que usa `DbSelectArea/DbSeek`| ⏸ (v0.2) |
| `BP-004`   | warning  | `#Include "Protheus.ch"` em vez de `"TOTVS.CH"`                 | ✅   |
| `BP-005`   | warning  | Falta `Begin Sequence/Recover/End` em operação crítica          | ⏸ (v0.2) |
| `BP-006`   | info     | Variável sem notação húngara                                    | ✅   |
| `BP-007`   | info     | Função sem header Protheus.doc                                  | ✅   |
| `BP-008`   | critical | Shadowing de variável reservada (cFilAnt, cEmpAnt, etc.)        | ✅   |

### Security (SEC)

| ID         | Sev      | Título                                                          | v0.1 |
|------------|----------|-----------------------------------------------------------------|------|
| `SEC-001`  | critical | SQL com concatenação `+` (SQL injection)                        | ✅   |
| `SEC-002`  | critical | `SELF:GetContent()` / `oRest:GetBody` sem validação             | ⏸ (v0.2) |
| `SEC-003`  | warning  | PII/credenciais em `ConOut`/`FWLogMsg`                          | ⏸ (v0.2) |
| `SEC-004`  | warning  | Credenciais hardcoded                                           | ✅   |
| `SEC-005`  | critical | Uso de função TOTVS restrita/interna                            | ✅ (via lookup) |

### Performance (PERF)

| ID         | Sev      | Título                                                          | v0.1 |
|------------|----------|-----------------------------------------------------------------|------|
| `PERF-001` | critical | `SELECT *` em BeginSql/TCQuery                                  | ✅   |
| `PERF-002` | warning  | `DbSeek` dentro de loop                                         | ⏸ (v0.2) |
| `PERF-003` | warning  | Falta `TCSetField` para data/numérico pós-query                 | ⏸ (v0.2) |
| `PERF-004` | warning  | Concatenação de string com `+`/`+=` em loop                     | ⏸ (v0.2) |
| `PERF-005` | warning  | `RecCount()` para checar existência                             | ✅   |
| `PERF-006` | info     | `WHERE`/`ORDER BY` em coluna sem índice                         | ⏸ (v0.2 — cross-file SIX) |

### Modernization (MOD)

| ID         | Sev   | Título                                                              | v0.1 |
|------------|-------|---------------------------------------------------------------------|------|
| `MOD-001`  | info  | `.prw` com `CLASS` que poderia migrar para `.tlpp`                  | ✅   |
| `MOD-002`  | info  | `using namespace` em `.tlpp` em vez de `.th` include                | ✅   |
| `MOD-003`  | info  | Funções com prefixo comum candidatas a virar classe                 | ⏸ (v0.2 — cross-function) |
| `MOD-004`  | info  | Uso de `AxCadastro`/`Modelo2`/`Modelo3` em vez de MVC               | ✅   |

**Total v0.1 ativas: 13** (8 BP-detectáveis + 3 SEC + 1 PERF + 3 MOD — contabilizando aliás `SEC-005` que é via lookup).

## Severidades — política de bloqueio

| Severidade | Significado                              | Bloqueia merge?              |
|------------|------------------------------------------|------------------------------|
| `critical` | Bug grave / falha de segurança garantida | **SIM** (corrigir antes)     |
| `error`    | Erro de compilação ou runtime provável   | **SIM**                      |
| `warning`  | Funciona, mas má prática                 | Corrigir; pode flagged em PR |
| `info`     | Estilo / sugestão                        | Não bloqueia                 |

## Workflow de revisão

1. Termine de editar o arquivo.
2. `/plugadvpl:lint <arq>` — roda regex single-file, lista findings.
3. Para cada `critical`/`error`: corrija **antes** de prosseguir.
4. Para `warning`: corrija; justifique se não der (PR-only).
5. Para `info`: trate como TODO de longo prazo.
6. Para v0.2 (regras deferidas), faça revisão manual usando esta skill como checklist.

## Checklist mental por severidade (ao gerar código)

**Antes de devolver código para o usuário, mentalmente percorra:**

### Critical (não passar com isso)

- [ ] Todo `RecLock` tem `MsUnlock` pareado, inclusive em branch de erro (`BP-001`).
- [ ] Nenhuma variável reservada (`cFilAnt`, `cEmpAnt`, `nUsado`) declarada como `Local` (`BP-008`).
- [ ] Nenhum SQL concatenado com `+ cVar +` (`SEC-001`) — use `%exp:`.
- [ ] Nenhuma função restrita TOTVS usada (`SEC-005`) — checou `funcoes_restritas`?
- [ ] `SELECT *` removido (`PERF-001`).

### Error/Warning

- [ ] `Local` no topo da função, antes de qualquer statement (`BP-002`).
- [ ] `Local` em vez de `Private`/`Public` quando possível (`BP-002b`).
- [ ] `GetArea/RestArea` em funções que mudam WorkArea (`BP-003`).
- [ ] `#include "TOTVS.CH"` (não `Protheus.ch`) (`BP-004`).
- [ ] `Begin Sequence/Recover/End Sequence` em operações críticas (`BP-005`).
- [ ] Credenciais via SuperGet/SX6, não hardcoded (`SEC-004`).
- [ ] Logs de `ConOut` sem PII/senha (`SEC-003`).
- [ ] Validação de input REST antes de usar (`SEC-002`).
- [ ] `DbSeek` em loop substituído por JOIN/IN quando possível (`PERF-002`).
- [ ] `TCSetField` após query pra colunas D/N (`PERF-003`).
- [ ] Concatenação em loop usa array + `Array2String` (`PERF-004`).
- [ ] Existência testada com `!Eof()`, não `RecCount() > 0` (`PERF-005`).

### Info (sugestões)

- [ ] Notação húngara em todas as variáveis (`BP-006`).
- [ ] Header Protheus.doc em todas as funções (`BP-007`).
- [ ] Cobertura de índice consultada (`PERF-006`).
- [ ] Classes em `.prw` candidatas a `.tlpp` (`MOD-001`).
- [ ] `.tlpp` usa `.th` em vez de `using namespace` (`MOD-002`).
- [ ] Grupos de funções com prefixo comum → considerar classe (`MOD-003`).
- [ ] Sem `AxCadastro`/`Modelo2`/`Modelo3` — usar MVC (`MOD-004`).

## Exemplos de fix por regra

### BP-001 — RecLock sem MsUnlock

```advpl
// ERRADO
RecLock("SA1", .F.)
SA1->A1_NOME := "novo"
// faltou MsUnlock

// CORRETO
RecLock("SA1", .F.)
SA1->A1_NOME := "novo"
SA1->(MsUnlock())
```

### BP-002 — Local no meio do código

```advpl
// ERRADO
Function Foo()
    DbSelectArea("SA1")
    Local cCod := "001"  // declarado depois de statement

// CORRETO
Function Foo()
    Local cCod := "001"  // todos no topo
    DbSelectArea("SA1")
```

### SEC-001 — SQL injection

```advpl
// ERRADO
cSql := "SELECT * FROM SA1010 WHERE A1_COD = '" + cCod + "'"

// CORRETO
BeginSql Alias "QRY"
    SELECT A1_COD, A1_NOME
      FROM %table:SA1% SA1
     WHERE SA1.A1_FILIAL = %xfilial:SA1%
       AND SA1.A1_COD    = %exp:cCod%
       AND SA1.%notDel%
EndSql
```

### PERF-005 — RecCount para existência

```advpl
// ERRADO
TCQuery cSql NEW ALIAS "QRY"
If QRY->(RecCount()) > 0
    // ...

// CORRETO
TCQuery cSql NEW ALIAS "QRY"
If !QRY->(Eof())
    // ...
```

## Anti-padrões gerais

- Aplicar fix automático cego sem entender a regra → pode quebrar lógica.
- Suprimir warning sem comentário justificativo → conhecimento perdido.
- Tratar `info` como ruído → no agregado, é o que diferencia código mantível.
- Não rodar lint antes de PR → ciclo de review fica longo desnecessariamente.

## Comandos plugadvpl relacionados

- `/plugadvpl:lint <arq>` — roda as 13 regras ativas do MVP.
- `/plugadvpl:lint` (sem arg) — roda no projeto inteiro.
- `/plugadvpl:find function <restrita>` — descobre funções proibidas (SEC-005).
- A tabela `lint_findings` no índice armazena o histórico; útil pra dashboard.
