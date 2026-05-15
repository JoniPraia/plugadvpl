# Auditoria técnica — 35 lint rules (v0.3.0 → v0.3.27)

**Data:** 2026-05-15
**Escopo:** robustez técnica dos detectores em `cli/plugadvpl/parsing/lint.py` + drift catálogo (`lookups/lint_rules.json`) × implementação. NÃO é reauditoria geral do plugin — só dos 35 lint rules.
**Metodologia:** revisão estática + reprodução isolada das regex em REPL Python (sem rodar contra cliente real). Comparação ponto-a-ponto JSON↔detector. Estimativa de big-O em projeto Protheus típico (~2k fontes, ~190k campos SX).

## Sumário executivo

O catálogo está **maduro nas regras single-file** (BP-001..BP-008, SEC-001..SEC-005, MOD-001/002/004, PERF-001/004/005). O motor de strip + escopo por função funciona; whitelists e dedup foram endereçados nos rounds anteriores. Tests cobrem positivo+negativo+edge bem.

Mas **três classes de problema** apareceram que não estavam nos QA reports anteriores:

1. **Persistência cross-file ficou inconsistente quando MOD-003 + PERF-006 entraram (v0.3.26/27).** A função que limpa antes de re-inserir só conhece `regra_id LIKE 'SX-%'`; MOD-003 e PERF-006 acumulam findings duplicados a cada `lint --cross-file`. Reedição do bug #9 do QA V1, agora em camada nova.

2. **Detectores de SQL (PERF-002 / PERF-003 / PERF-006) leem `sql_embedado.snippet` que é truncado a 300 caracteres pelo parser.** Queries Protheus reais com múltiplos JOIN ultrapassam isso fácil — `%notDel%` / `%xfilial%` / cláusula `WHERE` ficam fora da janela. Falso positivo massivo previsível em código legado de faturamento/financeiro.

3. **Várias heurísticas de regex têm edge cases reais:** SEC-002 aceita PT-BR comum (`FATURA`, `COMPRA`), PERF-004 dispara em variável `cnt` (não-hungarian), SX-009 nunca casa `.F.` (bug de boundary), BP-001 só pega tabela com 2-3 chars literais (perde físico `SA1010` e variável `cTab`).

**Top-3 (ver seção dedicada):** #1 (persist cross-file), #2 (snippet 300-char truncation), #5 (SX-009 `.F.` boundary).

---

## Achados

### #1 — `persist_cross_file_findings` apaga só `SX-%`, MOD-003 e PERF-006 acumulam *(severidade: crítica)*

**Categoria:** B (catálogo × impl drift) + E (cross-file)
**Regras afetadas:** MOD-003, PERF-006
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:2257`

```python
def persist_cross_file_findings(conn, findings) -> int:
    conn.execute("DELETE FROM lint_findings WHERE regra_id LIKE 'SX-%'")  # <-- só SX
    ...
    conn.executemany("INSERT INTO lint_findings (...)", rows)
```

A tupla `_CROSS_FILE_RULES` (linha 2198) inclui MOD-003 e PERF-006, ambos persistidos via mesma função. Sem `UNIQUE` em `lint_findings` (`migrations/001_initial.sql:214`).

**Cenário ADVPL:** dev roda `plugadvpl lint --cross-file` 3x para revalidar findings; toda execução adiciona N novos MOD-003 + PERF-006 sem apagar os anteriores. Após 5 execuções: 5× findings duplicados.

**Reprodução:**
```powershell
plugadvpl lint --cross-file
plugadvpl lint --cross-file
plugadvpl lint --regra MOD-003   # <-- 2x os findings esperados
```

**Recomendação:** `DELETE FROM lint_findings WHERE regra_id IN (?, ?, ...)` listando todas as cross-file IDs, ou `DELETE WHERE regra_id LIKE 'SX-%' OR regra_id IN ('MOD-003','PERF-006')`. Idealmente refatorar derivando a lista de `_CROSS_FILE_RULES`. Bonus: adicionar `UNIQUE(arquivo, linha, regra_id, snippet)` em `lint_findings` para defesa em profundidade (igual sugestão #9 do QA V1, ainda não aplicada).

---

### #2 — PERF-002/003/006 lêem snippet SQL truncado a 300 chars *(severidade: alta)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regras afetadas:** PERF-002, PERF-003, PERF-006
**Evidência:** `<projeto>/cli/plugadvpl/parsing/parser.py:1077,1125,1136,1147` define `_SQL_SNIPPET_MAX = 300` e trunca todo SQL em `sql[:_SQL_SNIPPET_MAX]`. Os detectores em `lint.py:918,947,983` consomem esse snippet:

```python
snippet = sql.get("snippet", "") or ""
if _NOTDEL_RE.search(snippet):  # 300 chars max
    continue
```

**Cenário ADVPL:** query MVC clássica com 3 tabelas e 15 colunas no SELECT:
```sql
SELECT SA1.A1_COD, SA1.A1_NOME, SA1.A1_CGC, ..., SD2.D2_PRCVEN
  FROM SA1010 SA1
  INNER JOIN SC5010 SC5 ON SC5.C5_CLIENTE = SA1.A1_COD
  INNER JOIN SD2010 SD2 ON SD2.D2_CLIENTE = SC5.C5_CLIENTE
 WHERE SA1.%notDel% AND SC5.%notDel% AND SD2.%notDel%
```
String tem 528 chars; `%notDel%` começa em pos 486. **Detector vê apenas 300 → dispara PERF-002 (false positive)** mesmo com `%notDel%` correto presente.

**Reprodução (Python):**
```python
sql = "SELECT ..." + " " * 300 + " WHERE %notDel%"
# len(sql) > 300, %notDel% além da janela
# detector vai disparar PERF-002 falsamente
```

**Recomendação:** detectores SQL não devem ler `snippet` truncado. Opções:
1. Aumentar `_SQL_SNIPPET_MAX` para 4000 (trade-off: tamanho do DB cresce ~4-10x para sql_embedado, talvez aceitável).
2. Persistir `snippet_full` separado em coluna TEXT sem limite (preferido — mantém preview compacto + dado completo para análise).
3. Re-extrair SQL completo via offset original + tamanho real do bloco quando o detector roda (menos invasivo, mas requer refator).

A combinação dessa truncagem + falta de cobertura para `TCQuery(cVar, ...)` (regex `_TCQUERY_RE` só captura literal entre aspas) significa que o conjunto PERF-002/003/006 hoje **não cobre a maioria das queries reais Protheus em código de cliente**.

---

### #3 — SEC-002 aceita prefixos PT-BR comuns como "cliente" (`FAT|FIN|COM|EST|...`) *(severidade: alta)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regra afetada:** SEC-002
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:193`

```python
_CLIENT_PREFIX_RE = re.compile(
    r"^(MGF|MZF|ZZF|U_|ZF|CLI|XX|MT[A-Z]|MA\d|FAT|FIN|COM|EST|CTB|FIS|PCP|MNT)",
    re.IGNORECASE,
)
```

`FAT|FIN|COM|EST|CTB|FIS|PCP|MNT` são módulos Protheus (Faturamento, Financeiro, Compras, Estoque, Contabilidade, Fiscal, PCP, Manutenção) — não prefixos de cliente. Pior: casam **palavras inteiras em PT-BR**:

| Função | Match | Por quê |
|---|---|---|
| `User Function FATURA()` | passa | prefix `FAT` |
| `User Function COMPRA()` | passa | prefix `COM` |
| `User Function FINALIZA()` | passa | prefix `FIN` |
| `User Function ESTOQUE()` | passa | prefix `EST` |
| `User Function FISCALOK()` | passa | prefix `FIS` |

Resultado: **falso negativo massivo** — qualquer User Function nomeada em português que comece com FAT/FIN/COM/EST/CTB/FIS/PCP/MNT escapa a SEC-002. A regra perde justamente os casos canônicos que ela deveria flagar (User Functions sem prefixo cliente, escritas em PT-BR pelo dev).

Adicionalmente: `U_` no prefix-list é dead code — `parser.py` extrai apenas o nome **após** `User Function`, sem o `U_` (que vive no chamador, não na declaração).

**Recomendação:** restringir prefix a iniciais que NÃO são palavras PT-BR comuns: `MGF|MZF|ZZF|ZF|XX|XYZ|<lista config por projeto>`. Considerar mover a lista para `lint_rules.json` por regra (`config: { client_prefixes: [...] }`) ou aceitar lista via `--config` no init. Remover `U_` (dead). Remover ou marcar como genérico `MT[A-Z]|MA\d` (são padrões de PE TOTVS, mas já cobertos por `_PE_NAME_RE`).

---

### #4 — PERF-004 dispara em variáveis `c<3-letras>` que não são hungarian (`cnt`, `csv`, `cmd`, `crm`) *(severidade: média)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regra afetada:** PERF-004
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:1170,1176`

```python
_PERF004_COMPOUND_RE = re.compile(r"\bc[A-Za-z_]\w*\s*\+=", re.IGNORECASE)
_PERF004_LONGFORM_RE = re.compile(r"\b(c[A-Za-z_]\w*)\s*:=\s*\1\s*\+", re.IGNORECASE)
```

Contrato declarado no docstring + JSON: "hungarian notation `c<NAME>` = string". Mas o regex `c[A-Za-z_]\w*` casa qualquer identificador iniciado em `c`, incluindo:

| Variável | Casa? | Realmente é string? |
|---|---|---|
| `cnt += 1` | sim | NÃO (counter, número) |
| `csv += linha` | sim | provavelmente sim |
| `cmd += ' --flag'` | sim | sim |
| `crm := crm + ...` | sim | depende do projeto |
| `cKey += nIndex` | sim | depende — código real pode estar concatenando número |

**Cenário real:** loop com contador `cnt` (abreviação `count`, idioma comum em ADVPL legado) é flagado como concat em loop, mas é só `cnt += 1` numérico.

**Recomendação:** ou exigir prefix `c` + **maiúscula** (`c[A-Z]\w*`) — convenção hungarian estrita: `cVar`, `cMsg` mas não `cnt`/`csv` —, ou adicionar lista de exceções comuns (`cnt`, `csv`, `cmd`, `crm`). Tradeoff: perde `chrCustom` etc. Trade vale a pena — código real raramente nomeia string com lower-case 2ª letra.

---

### #5 — SX-009 nunca dispara para `.F.` (regex `\b\.F\.\b` boundary impossível) *(severidade: média)*

**Categoria:** A (regex frágil) + B (catálogo × impl drift)
**Regra afetada:** SX-009
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:1575-1584`

```python
_INIT_RETURNS_EMPTY_RE = re.compile(
    r"""(['"])\s*\1
        | \bSpace\s*\(\s*\d+\s*\)
        | \bCToD\s*\(\s*['"]\s*['"]\s*\)
        | \bNil\b
        | \b\.F\.\b      # <-- nunca casa
        | \b0\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
```

Confirmado em REPL: `re.search(r'\b\.F\.\b', '.F.') is None`. Motivo: `\b` é transição word↔non-word; `.` é non-word, então `\b\.` exige um word-char à esquerda, e `.F.` isolado começa em BOF (não tem char à esquerda). Mesmo dentro de string como `init=.F.`, o `=` é non-word e `.` é non-word — não há boundary entre eles.

Catálogo (`lint_rules.json` regra SX-009) afirma cobrir `.F.`. Drift real entre intenção e comportamento.

**Cenário ADVPL:** `X3_INIT = ".F."` em campo obrigatório (`X3_OBRIGAT='X'`) — anti-pattern clássico, **silenciosamente não detectado**.

**Recomendação:** trocar `\b\.F\.\b` por `\.F\.` (sem boundaries) ou usar lookarounds `(?<![A-Za-z0-9_])\.F\.(?![A-Za-z0-9_])`. Mesmo problema potencial com `\bNil\b` está OK porque `Nil` é word.

---

### #6 — Mensagem de SX-009 referencia campo errado (`X3_RELACAO` em vez de `X3_INIT`) *(severidade: baixa)*

**Categoria:** B (catálogo × impl drift) + F (sugestão de fix)
**Regra afetada:** SX-009
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:1917`

```python
"sugestao_fix": (
    f"Campo {tabela}.{campo} é obrigatório mas X3_RELACAO inicializa "  # <-- errado
    "com vazio/zero ..."
),
```

JSON descreve a regra usando `X3_INIT` (correto) e o detector lê `inicializador` da tabela `campos`, mas a mensagem de fix menciona `X3_RELACAO` — **outro campo** do SX3 (regra de cálculo, não inicializador). Confunde quem vai fazer o fix.

**Recomendação:** trocar `X3_RELACAO` por `X3_INIT` no texto.

---

### #7 — BP-001 só detecta RecLock com tabela 2-3 chars *literal*, perde físico e variável *(severidade: média)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regra afetada:** BP-001
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:29-30`

```python
_RECLOCK_OPEN_RE = re.compile(r'\bRecLock\s*\(\s*["\'](\w{2,3})["\']', re.IGNORECASE)
_RECLOCK_VIA_ALIAS_RE = re.compile(r"\b(\w{2,3})\s*->\s*\(\s*RecLock\b", re.IGNORECASE)
```

Casos perdidos:

| Padrão real | Detectado? |
|---|---|
| `RecLock("SA1", .F.)` (alias) | sim |
| `RecLock("SA1010", .F.)` (físico) | NÃO (`\w{2,3}` máx 3) |
| `RecLock(cTab, .F.)` (variável) | NÃO (sem aspas) |
| `RecLock(cAlias, .F.)` (variável) | NÃO |
| `(cAlias)->(RecLock("...",.F.))` (alias dinâmico) | NÃO |

Código real Protheus mistura nome físico em scripts de migração e variáveis em rotinas reutilizáveis. Falso negativo silencioso na regra **crítica** de unlock pareado.

**Recomendação:** mudar para `\w{2,7}` (cobre alias 2-3 + físico 6-7); adicionar variante para variáveis: `\bRecLock\s*\(\s*\w+` (qualquer arg primário) e cruzar com presença/ausência de `MsUnlock` no escopo. Trade: aumenta recall, pode adicionar 2-3% FP, mas a função é critical e MsUnlock pareado é praticamente sempre desejado.

---

### #8 — PERF-006 tem lógica de cross-table-match frágil; pode marcar coluna como não-indexada quando indexada em outra tabela *(severidade: média)*

**Categoria:** A (regex frágil) + E (cross-file)
**Regra afetada:** PERF-006
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:2080-2089`

```python
matched_table = None
for tbl, cols in indices_cache.items():
    if any(c.startswith(prefix + "_") for c in cols):
        matched_table = tbl
        if full in cols:
            matched_table = "INDEXED"
            break
```

Iteração depende da ordem de `indices_cache.items()` (não determinística pré-Python 3.7, depois preserva inserção que vem do `SELECT` SQL — também não-determinística sem `ORDER BY`). Se duas tabelas tiverem o mesmo prefixo de coluna (caso real: prefixo `R8` aparece em SR8 *e* SR8XYZ extension), e a coluna está indexada em apenas uma, dá pra reportar falso positivo dependendo de qual veio primeiro.

Caso menor mas pior: `*_FILIAL` é silenciado por nome — mas há tabelas com filial em sufixo diferente (raro, mas sistemas custom têm). Nesses, `xxx_FILIAL2` etc. não é skipado.

**Recomendação:** depois de coletar todas as `matched_table` candidatas, decidir como "INDEXED" se **qualquer** uma tem `full in cols`. Iterar todas antes de gravar finding.

---

### #9 — SEC-005 detecta chamadas a função que coincide com nome custom do projeto *(severidade: baixa)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regra afetada:** SEC-005
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:1396-1400`

```python
_SEC005_CALL_RE = re.compile(
    r"(?<![:.])"                    # not after : or .
    r"\b([A-Za-z_][A-Za-z0-9_]*)"   # identifier
    r"\s*\(",                       # opening paren
)
```

Lista `funcoes_restritas.json` tem ~194 nomes. Se um projeto cliente tem função custom com nome igual (caso real: `MA410IMPOS` está no JSON, mas se cliente criou função própria homônima — improvável mas possível em PEs canônicos como `MT100LOK`), a regra não distingue.

Mitigação parcial: o cliente provavelmente teria criado como User Function `U_MT100LOK` que vira `MT100LOK` chamável internamente. Hoje o detector skipa só se a linha começa com `User|Static|Function|Method|Class|Procedure` antes do nome.

**Recomendação:** baixa prioridade. Logging seria útil — em projeto grande, contar quantos findings vêm de função homônima ao próprio projeto e oferecer flag `--exclude-defined-locally` que cruza com `fonte_chunks`.

---

### #10 — `_CROSS_FILE_RULES` requires_sx flag não cobre PERF-006 graciosamente quando `indices` vazia *(severidade: baixa)*

**Categoria:** E (cross-file)
**Regra afetada:** PERF-006
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:2030-2054`

PERF-006 está marcado `requires_sx=True` (linha 2211), então só roda se migration 002 está aplicada. Mas o detector dentro também guard-clauses: `if not indices_cache: return findings`. Isso é correto.

Porém: `sql_embedado` é tabela do core (não SX). Detector roda `SELECT FROM sql_embedado` mesmo se `indices` estiver vazia — só desperdiça uma query e a iteração de rows. Não é bug, é overhead pequeno (provavelmente <1s em projetos grandes).

Mais relevante: documentação JSON menciona "SX so cobre custom" — mas indices SX em projeto Protheus padrão (sem ingest-sx custom completo) cobre poucas tabelas standard. Detector vai marcar muito coluna como "skip — sem tabela mapeada". UX: usuário roda PERF-006 e recebe vazio, sem entender que era falta de dado SX-001..SIX, não falta de problema. Considerar emitir 1 finding sintético "PERF-006: SX-SIX vazio, regra não consegue avaliar" quando aplicável.

**Recomendação:** baixa. Adicionar log/aviso "indices SIX vazias para tabelas X/Y/Z — cobertura PERF-006 limitada".

---

### #11 — BP-007 skipa `kind="mvc_hook"` mas esse kind não existe no parser *(severidade: baixa)*

**Categoria:** B (catálogo × impl drift)
**Regra afetada:** BP-007
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:633` faz `if f.get("kind") in {"mvc_hook"}: continue`. O parser (`parser.py:271-323`) emite kinds: `user_function|static_function|main_function|function|ws_method|method`. Nenhum `mvc_hook`. Branch é dead code.

**Cenário ADVPL:** hooks MVC reais (`bCommit`, `bTudoOk`, `bLineOk`) são funções anônimas/lambdas, não declaradas como Function. Não geram entry em `funcoes` mesmo. O skip é defensivo mas inútil.

**Recomendação:** remover o branch ou implementar de fato (parser teria que expor codeblocks anônimos). Hoje é só ruído + comentário enganoso.

---

### #12 — SEC-003 forma curta `c<Pwd|Rg|Pin|Card|Pass>\b` ignora variantes legítimas (`cPwdHash`, `cRgEmissor`) *(severidade: baixa)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regra afetada:** SEC-003
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:131` regex `\bc(?:Pwd|Rg|Pin|Card|Pass)\b` exige boundary depois — só nomes EXATOS.

Casos não detectados:
- `cPwdHash` — hash de senha, ainda é PII (deveria flagar)
- `cRgEmissor` — info do RG, PII
- `cCardNumber` — number do cartão
- `cPinAtual` — PIN ativo

Já o oposto: `cPwd` exato dispara, mas variantes não. A escolha foi explícita (comment line 119-122) para evitar PT-BR FP — válida — mas restringe demais o positivo.

**Recomendação:** liberar sufixo opcional para alguns ambíguos: `\bc(?:Pwd|Pin)\w*` (`cPwd`, `cPwdHash`, `cPinAtual` mas não `cPiscina`). Fica como tradeoff: `Pin` ainda casa palavras tipo `cPinta` — mas elas são raras vs PII real. Talvez aceitar o overlap. Decisão de produto.

---

### #13 — BP-005 conta vírgula naive, falha em params com default `aArr := {1,2}` *(severidade: baixa)*

**Categoria:** A (regex frágil) + C (edge case ADVPL)
**Regra afetada:** BP-005
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:491` faz `n_params = params_text.count(",") + 1`. Não trata vírgulas dentro de literais ou expressões.

ADVPL permite default args com array literal: `Function Foo(a, b, c := {1,2,3}, d)` — splitting por vírgula dá 6, não 4. **Falso positivo BP-005** (acima do threshold 6).

Caso adicional: `Function Foo(a, b, c, d, e)` com 5 params reais é OK; mas `Function Foo(a, b, c := MyFunc(1, 2, 3))` conta 5 (3 args internos contam como params).

**Recomendação:** parser de paren-balance simples no `params_text`, ignorando vírgulas dentro de `()`/`{}`. Implementação trivial (~10 linhas). Já existe pattern parecido em `_check_sec003_pii_in_logs` (depth-counted parens).

---

### #14 — SX-005 carrega corpus inteiro de fontes em memória — possível OOM em monorepo grande *(severidade: baixa)*

**Categoria:** D (performance)
**Regra afetada:** SX-005
**Evidência:** `<projeto>/cli/plugadvpl/parsing/lint.py:1768-1771`

```python
fonte_corpus = "\n".join(
    (r[0] or "").upper()
    for r in conn.execute("SELECT content FROM fonte_chunks")
)
```

Em projeto Protheus típico (~2k fontes, ~25 KB médio = 50MB de fonte). Em PowerShell/Windows o overhead Python é ~3-4x → ~200MB residente para a string única. Dá pra rodar, mas em monorepo (10k fontes, 250MB → ~1GB) começa a doer.

Soma com o fato que isso roda **toda** vez que SX-005 é chamado (sem cache entre chamadas), e que `lint --cross-file` chama 13 detectores, alguns dos quais re-leem fonte_chunks — multiplicando IO sobre dado idêntico.

**Recomendação:** baixa. Considerar SQLite FTS5 sobre `fonte_chunks.content` para substring lookup sem materializar corpus. Comment do código já diz "100-1000× mais rápido" vs versão N+1 antiga, então atual é aceitável; não otimizar prematuramente.

---

### #15 — Catálogo descreve "BP-002 ... NUNCA misture funções de manutenção AdvPL básicas com Framework dentro do mesmo bloco" — texto pertence a BP-006, não BP-002 *(severidade: baixa)*

**Categoria:** B (catálogo × impl drift) + F (fix guidance)
**Regra afetada:** BP-002
**Evidência:** `<projeto>/cli/plugadvpl/lookups/lint_rules.json:19` (campo `fix_guidance`):

```json
"fix_guidance": "Pareie `Begin Transaction` com `End Transaction`. Use `DisarmTransaction()` antes do `Break` em `Recover`. NUNCA misture funções de manutenção AdvPL básicas com Framework dentro do mesmo bloco."
```

A última frase é regra do BP-006 (`mistura RecLock + dbAppend()`). BP-002 é só sobre transação não pareada. Pequeno copy-paste cruzado.

**Recomendação:** remover a frase final ou mover para BP-006.

---

## Resumo executivo (tabela)

| # | Achado | Severidade | Categoria | Regra |
|---:|---|---|---|---|
| 1 | persist cross-file deleta só `SX-%`, MOD-003/PERF-006 acumulam | crítica | B+E | MOD-003, PERF-006 |
| 2 | snippet SQL truncado a 300 chars → FP em PERF-002/003/006 | alta | A+C | PERF-002, PERF-003, PERF-006 |
| 3 | SEC-002 prefix list aceita PT-BR (`FAT`, `FIN`, `COM`...) | alta | A+C | SEC-002 |
| 4 | PERF-004 dispara em `cnt` (counter, não string) | média | A+C | PERF-004 |
| 5 | SX-009 regex `\b\.F\.\b` nunca casa `.F.` | média | A+B | SX-009 |
| 6 | SX-009 mensagem cita `X3_RELACAO` em vez de `X3_INIT` | baixa | B+F | SX-009 |
| 7 | BP-001 perde RecLock com físico/variável | média | A+C | BP-001 |
| 8 | PERF-006 cross-table match não-determinístico | média | A+E | PERF-006 |
| 9 | SEC-005 não distingue função homônima custom local | baixa | A+C | SEC-005 |
| 10 | PERF-006 sem fallback gracioso quando `indices` vazia | baixa | E | PERF-006 |
| 11 | BP-007 skipa `kind="mvc_hook"` que não existe | baixa | B | BP-007 |
| 12 | SEC-003 forma curta `\b...\b` ignora `cPwdHash` etc. | baixa | A+C | SEC-003 |
| 13 | BP-005 conta vírgula naive, falha em default `{1,2}` | baixa | A+C | BP-005 |
| 14 | SX-005 carrega 50-250MB corpus em memória | baixa | D | SX-005 |
| 15 | BP-002 fix_guidance tem frase de BP-006 | baixa | B+F | BP-002 |

## Top-3 a priorizar

1. **#1 (persist cross-file)** — fix de 1 linha (`DELETE WHERE regra_id IN (...)` ou `LIKE 'SX-%' OR regra_id IN ('MOD-003','PERF-006')`). Sem isso, `lint --cross-file` chamado 2x = findings duplicados; usuário perde confiança no output. Bug recorrente do plugin (já apareceu como #9 no QA V1 com lint single-file).

2. **#2 (snippet truncado a 300)** — afeta 3 das regras de SQL (PERF-002/003/006), gera **falso positivo previsível em qualquer query MVC com 2+ JOINs**. Em código real Protheus de cliente, isso significa lint relatando "sem %notDel%" para queries que TÊM. Quebra a credibilidade do detector quando aplicado a fonte legado de faturamento.

3. **#5 (SX-009 .F. boundary)** — fix trivial (remover `\b...\b` ou trocar por lookarounds). Hoje regra promete cobrir `.F.` mas silenciosamente perde — drift crítico catálogo×impl que vai levar dev a confiar em lint que não está olhando.

## O que funcionou bem

- **Strip de comentários/strings** (`stripper.py`): preserva offsets/length, evita FP em código comentado. Padrão sólido reutilizado por todos os detectores.
- **Escopo por função** (`_funcs_with_offsets` + `_scope_for_match`): BP-001/002/006 contam pares no escopo certo, não no arquivo todo. Heurística difícil de acertar bem, e está correta.
- **Whitelists semânticas** em BP-008/BP-002b/SEC-003/SEC-004 (PT-BR, MV_PAR*, lMsErroAuto, framework reservadas) endereçaram FPs documentados nos rounds 1-3.
- **Dedup por (linha, regra_id)** dentro dos detectores PERF-004 e MOD-004 evita duplo finding em mesmo callsite.
- **Lookbehind anti-method-call** `(?<![:.])` em SEC-005/MOD-004 e anti-definition em SEC-005 cobrem bem as armadilhas óbvias.
- **Tests unit cobrem positivo + negativo + casos PT-BR explicitamente** (`cPassagem`, `cPintar`, `cCardapio`) — boa cultura defensiva.
- **Cross-file rules separadas em `_CROSS_FILE_RULES`** com flag `requires_sx`: design correto para skipar gracioso quando dicionário ausente. (O bug está no persist, não na orquestração.)
- **`_perf004_loop_ranges`** com stack para loop aninhado: implementação simples e correta, suporta `For/Next` + `While/EndDo` mistos.
