# Relatório QA round 2 — plugadvpl v0.3.14 → v0.3.19

**Data:** 2026-05-14
**Escopo:** auditoria estática (codebase + testes + skills/docs) das 6 últimas releases
**Metodologia:** revisão de `CHANGELOG.md`, `cli/plugadvpl/parsing/{lint,parser}.py`, `cli/plugadvpl/{query,ingest,ingest_sx,cli}.py`, `cli/plugadvpl/lookups/lint_rules.json`, `cli/tests/{unit,integration}/*`, e cruzamento contra `skills/*/SKILL.md`. Sem execução contra cliente real.

## Sumário executivo

A maioria dos achados do `PLUGADVPL_QA_REPORT.md` (round 1) foi de fato endereçada — o RED→GREEN claim do CHANGELOG bate com o que o código entrega. As 5 fixes da v0.3.15 (callees quebrado, gatilho destino, project_root, --limit hint, CLAUDE.md), as 2 heurísticas de parser da v0.3.16 (WSRESTFUL + PARAMIXB), o boundary de impacto da v0.3.17 e o trio de polish da v0.3.18 (lint dups, execauto flag, self-call flag) estão implementados e cobertos por teste integration RED→GREEN com fixtures dedicadas. O guard de catálogo (`test_lint_catalog_consistency.py`) impede drift acidental — funcionou na v0.3.19 ao detectar gap em SEC-003/SEC-004.

O ponto fraco do ciclo está no **security pack v0.3.19**, especificamente SEC-003: a lista `_SEC003_LOG_FUNCS_RE` inclui `Help` — função canônica do framework Protheus para *exibir mensagem ao usuário em modal* (igual a `MsgInfo`, que o detector explicitamente pula). Em qualquer projeto MVC real, `Help(...,, 'Mensagem com cliente ' + SA1->A1_NOME, ...)` é o padrão; a regra vai disparar massa de false positives. O regex de variável PII também é amplo demais (`Pass`, `Pin`, `Card`, `Rg` casam dentro de palavras comuns como "PASSAGEM", "PINTAR", "DESCARDADO") — efetivamente case-insensitive substring matching dentro de identificadores. Ambos pre-shipping; nenhum teste cobre `Help` ou nomes-substring.

Drift documental também aparece: skills `help`, `advpl-code-review`, `arch`, `callers`, `status` ainda mostram contagens/comandos de versões anteriores (13 subcomandos, 18 single-file rules, sem mencionar `tabelas_via_execauto`/`is_self_call`). A flag `--version` foi documentada bem; o resto ficou pra trás.

---

## Achados

### #1 — SEC-003 inclui `Help` na lista de funções de log *(severidade: alta)*

**Categoria:** A (bug funcional) + B (gap de teste)
**Release relevante:** v0.3.19
**Evidência:** `cli/plugadvpl/parsing/lint.py:104-107`:

```python
_SEC003_LOG_FUNCS_RE = re.compile(
    r"\b(?:ConOut|FwLogMsg|MsgLog|LogMsg|UserException|Help)\s*\(",
    re.IGNORECASE,
)
```

`Help(...)` em ADVPL é a função canônica do framework para **exibir um diálogo de ajuda/erro ao usuário** — equivale a `MsgInfo` (que o detector explicitamente exclui per docstring). É o padrão usado em `X3_VALID`, `X3_VLDUSER`, `X7_REGRA`, validações MVC. As próprias skills do plugin documentam o uso:
- `skills/advpl-mvc/reference.md:784,888,1279,1308,...` — múltiplos `Help( ,, 'HELP',, 'Informe o CNPJ', 1, 0)`.
- `skills/advpl-pontos-entrada/SKILL.md:82` — `Help(, , "Validacao", , "NF " + cNumNF + " bloqueada por regra interna", 1, 0)`.
- `skills/advpl-dicionario-sx-validacoes/SKILL.md:42` — texto explicando que `Help()` mostra mensagem ao usuário.

A docstring da regra também afirma: *"NAO sinaliza: MsgInfo/MsgAlert/MsgBox/Aviso (UI modal pra usuario autenticado, nao log)"* — `Help` cai no mesmo balde mas não foi excluída. Pesquisa-first documentada na release notes não pegou esse padrão.

**Reprodução:** qualquer fonte MVC real com `Help( ,, 'Erro',, 'Cliente ' + SA1->A1_NOME + ' bloqueado', 1, 0)` dispara SEC-003 mesmo a chamada sendo UI (não vai pro `console.log` do servidor).

**Recomendação:** remover `Help` de `_SEC003_LOG_FUNCS_RE`. Adicionar teste negativo `test_negative_help_is_ui_not_log`. Considerar também: `UserException` é exceção runtime (não log estruturado per se) — em alguns contextos seu argumento aparece em log; vale revisitar se realmente pertence à lista.

---

### #2 — SEC-003 PII var regex casa palavras comuns como substring *(severidade: alta)*

**Categoria:** A (false positive)
**Release relevante:** v0.3.19
**Evidência:** `cli/plugadvpl/parsing/lint.py:109-113`:

```python
_SEC003_PII_VAR_RE = re.compile(
    r"\b[a-z]?(?:Cpf|Cnpj|Senha|Pwd|Pass|Password|Token|Cartao|Card|Cvv|Pin|"
    r"ApiKey|Api_Key|Secret|Rg)\w*\b",
    re.IGNORECASE,
)
```

Problemas, por ordem de impacto:

1. **`Pass\w*`** com `IGNORECASE` casa: `PASSAGEM`, `PASSO`, `PASSAR`, `PASSADO`, `PASSADIA`, `PASSE`, `PASSARELA`, qualquer `Passage`. ADVPL usa termos PT-BR — variável `cPassagem` ou `nPasso` em rotina de TMS/turismo aparece o tempo todo.
2. **`Pin\w*`** casa `PINTAR`, `PINHEIRO`, `PINTOR`, `PINGADO`, `PINICAR`. Bem comum em base com municípios/nomes próprios.
3. **`Card\w*`** casa `CARDAPIO`, `CARDENAS`, `DESCARDADO`, `DECARDINAL`. Frequente em food-service e em integração com cardápio.
4. **`Rg\w*`** — apenas 2 letras. Combinado com `[a-z]?` opcional + `\w*` final, casa `cArgumento`, `nArgs`, `oArg`. (`\b` ajuda mas `cArg` casa `Arg` que não está no set; o problemático é `*Rg*` no meio: `\b[a-z]?Rg\w*\b` — na verdade `\b` requer boundary antes do `[a-z]?`, então `cArg` NÃO casa pois o `\b` está antes do `c`. Mas `cRg` ok, `cRgVal` ok, `MGFRG010` casa por iniciar com bondary M, depois G, então `\b` precisa de boundary entre não-word e word. Letras maiúsculas dentro de identificadores ADVPL não criam boundary. Concedo: o `\b` mitiga a `Rg` parcialmente. Permanece o problema de `Pass`, `Pin`, `Card`.)
5. **`Cvv`** — também 3 letras curtas; tipicamente OK (não há palavra PT comum com CVV), mas o pattern `[a-z]?(?:...)` com leading `[a-z]?` gera matches estranhos como o final de `aCvv` mas também `nCvvCount`. Aceitável.

Outro detalhe: `[a-z]?` no início é case-insensitive. Sem essa restrição (qualquer letra), o pattern só ganha 1 char no começo. Com `IGNORECASE` o intuito de "Hungarian opcional `c` ou nada" fica enganador: matchea qualquer `[A-Za-z]?` no começo, então `nPin` casa, `aPin` casa, etc.

**Reprodução:** rodar lint num fonte com `Local cPassagem := ...` + `ConOut("Bilhete: " + cPassagem)` → SEC-003 dispara achando que `Pass` em `cPassagem` é "senha".

**Recomendação:**
- Trocar variantes ambíguas curtas por matches exatos: `(?:Cpf|Cnpj|Senha|Pwd|Password|Token|Cartao|Cvv|Pin|ApiKey|Api_Key|Secret|Rg|Card|Pass)$` com `\b...\b` em vez de `\w*`. Exigir que o nome **termine** ou separar PT-BR (`Senha`) de EN curto.
- Para `Pass`/`Pin`/`Card`, exigir prefixo Hungarian estrito (`c` obrigatório, não `[a-z]?`) OU manter só formas longas (`Password`, `PinCode`, `CreditCard`).
- Adicionar teste `test_negative_word_passagem_is_not_password`, `test_negative_word_pintar_is_not_pin`, etc.

---

### #3 — SEC-004 `_SEC004_PREPARE_ENV_RE` rejeita `PASSWORD ""` mas o pattern `[^'"]+'` *(severidade: baixa)*

**Categoria:** A (correctness boundary)
**Release relevante:** v0.3.19
**Evidência:** `cli/plugadvpl/parsing/lint.py:83-86`:

```python
_SEC004_PREPARE_ENV_RE = re.compile(
    r"\bPREPARE\s+ENVIRONMENT\b[^\n]*?\bPASSWORD\s+['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
```

A intenção (per fix_guidance) é flagar literal não-vazio. O `[^'\"]+` (>=1 char) garante isso. Bom.

Porém: `[^\n]*?` (ungreedy ANY-NOT-NEWLINE) entre `PREPARE ENVIRONMENT` e `PASSWORD` requer que tudo esteja em **uma única linha**. UDC `tbiconn.ch` typically expande em múltiplas linhas via `;` continuation ADVPL. Exemplo real:

```advpl
PREPARE ENVIRONMENT EMPRESA cEmp FILIAL cFil ;
    USER cUser ;
    PASSWORD 'minhasenha' ;
    MODULO 'FAT'
```

O `;` é continuação ADVPL, mas o regex usa `[^\n]*?` que para no `\n` real. Logo, esse caso **comum** não é detectado. Falso negativo.

**Recomendação:** trocar `[^\n]*?` por `.*?` com flag `re.DOTALL`, OU remover qualquer regex de extensão e fazer match em duas etapas (achar `PREPARE ENVIRONMENT`, depois buscar `PASSWORD '<x>'` na mesma instrução até `;` ou newline lógico). Adicionar teste com continuação `;`.

---

### #4 — SEC-004 `RpcSetEnv` regex não suporta args com espaços/expressões *(severidade: média)*

**Categoria:** A (false negative)
**Release relevante:** v0.3.19
**Evidência:** `cli/plugadvpl/parsing/lint.py:73-80`:

```python
_SEC004_RPCSETENV_LITERAL_RE = re.compile(
    r"\bRpcSetEnv\s*\("
    r"\s*['\"][^'\"]*['\"]\s*,"        # emp
    r"\s*['\"][^'\"]*['\"]\s*,"        # fil
    r"\s*['\"]([^'\"]+)['\"]\s*,"      # user (NAO vazio)
    r"\s*['\"]([^'\"]+)['\"]",         # pwd (NAO vazio)
    re.IGNORECASE,
)
```

Cobre `RpcSetEnv("01","01","admin","totvs",...)`. Mas o detector **não dispara** quando os primeiros args são variáveis e só user/pwd são literais — caso real e comum:

```advpl
RpcSetEnv(cEmp, cFil, "admin", "totvs", "FAT")
```

O regex exige string literal nos slots 1 e 2. Falso negativo.

Outro caso: line continuation `;` espalhando args em múltiplas linhas — o regex usa `\s*` que casa newlines (sim), então isso provavelmente OK. Não testado.

**Recomendação:** afrouxar slots 1+2 para aceitar variável OU literal — pattern para slot ergônomico é `(?:\w+|['"][^'"]*['"])\s*,`. Ou: separar os checks e procurar **par `user_literal, pwd_literal`** em qualquer posição `≥ 3`. Adicionar teste positivo com `RpcSetEnv(cEmp, cFil, "admin", "totvs", ...)`.

---

### #5 — SEC-003 cobre apenas A1_*/RA_* — falta SF1/SE2/SC5 etc. *(severidade: baixa)*

**Categoria:** B (gap de teste/cobertura)
**Release relevante:** v0.3.19
**Evidência:** `cli/plugadvpl/parsing/lint.py:117-121`:

```python
_SEC003_PII_FIELDS_RE = re.compile(
    r"\b(?:A1_CGC|A1_CPF|A1_NOME|A1_NREDUZ|A1_EMAIL|A1_TEL|A1_END|A1_DDD|"
    r"RA_CIC|RA_RG|RA_NOMECMP|RA_EMAIL|RA_NUMCP|RA_TELEFON)\b",
    re.IGNORECASE,
)
```

Lista é "conservadora" mas perde campos PII frequentes:
- `A2_*` (fornecedores) — `A2_CGC`, `A2_NOME`, `A2_EMAIL`, `A2_TEL` são equivalentes A1_*.
- `B1_PRODUTO/B1_DESC` não é PII, OK.
- `RH_*` (folha) — vários campos PII (`RH_*` pra dependentes).
- `RD_NUMCP` (folha-cabeçalho).
- Fornecedor pessoa-física (`A2_CPFRG`).

A própria descrição do catálogo (`lint_rules.json`:126) cita "A2_*" indiretamente ("clientes/funcionarios"). Decisão de escopo aceitável, mas vale documentar como limitação conhecida no fix_guidance ou ampliar.

**Recomendação:** estender para `A2_CGC|A2_NOME|A2_EMAIL|A2_TEL|A2_END` e equivalentes folha. Sem urgência; documentar como "lista conservadora — adicione sua tabela custom via lookup" no skill.

---

### #6 — `gatilho_query` segue só descendentes mesmo após v0.3.15 fix *(severidade: média)*

**Categoria:** A (correctness parcial) + C (doc engana)
**Release relevante:** v0.3.15 (#4)
**Evidência:** `cli/plugadvpl/query.py:761-770`:

```python
rows = conn.execute(
    """
    SELECT campo_origem, sequencia, campo_destino, regra, condicao,
           tipo, alias, seek
    FROM gatilhos
    WHERE upper(campo_origem) = ? OR upper(campo_destino) = ?
    ORDER BY sequencia
    """,
    (origem, origem),
).fetchall()
for co, seq, cd, regra, cond, tp, alias, seek in rows:
    ...
    if cd and cd.upper() not in visited:
        visited.add(cd.upper())
        next_frontier.append((cd.upper(), f"{co}#{seq}"))
```

A v0.3.15 corretamente expandiu o `WHERE` para `origem OR destino` — campo só recebedor agora aparece. Bom. Porém, ao expandir o `next_frontier`, o código adiciona apenas `cd` (destino), nunca `co` (origem) das rows que casaram via `campo_destino = ?`. Significa: a cadeia caminha forward (level N+1 = destinos do level N), mas, ao consultar pelo destino, os origins inversos NÃO se tornam frontier do próximo nível.

Concretamente: `gatilho A1_COD --depth 3`:
- level 1: pega rows onde `co=A1_COD` E rows onde `cd=A1_COD`.
- level 2: para cada row do nível 1, frontier = destinos. Se row é `co=Y, cd=A1_COD`, frontier não recebe Y (fica `cd=A1_COD` que está em visited).
- Portanto a cadeia inversa morre no nível 1.

Help da CLI diz "*cadeia* de gatilhos *originados/destinados* ao campo". Para seguir a cadeia em ambas direções, precisaria adicionar `co` ao frontier também (com flag pra distinguir direção). É uma escolha de design defensável — full bidirectional BFS pode explodir o output —, mas o "depth=3" não significa o mesmo nas duas direções e o usuário não tem como saber.

**Reprodução:** banco com gatilhos `Y -> A1_COD` (level 1, ok) + `Z -> Y` (level 2, NÃO retornado por `gatilho A1_COD`). Gatilho de Y não aparece como upstream cadeia.

**Recomendação:** ou (a) adicionar opção `--direction up|down|both` (default `down` retro-compat) e seguir pra cima quando solicitado; ou (b) clarificar no help/skill "cadeia downstream a partir de origens diretas + indiretas (via destino)". Tests não cobrem o caso 2-níveis upstream.

---

### #7 — Word boundary não aplicado em `_impacto_fontes` (limitação assumida, mas não documentada na saída) *(severidade: baixa)*

**Categoria:** C (UX/docs)
**Release relevante:** v0.3.17
**Evidência:** `cli/plugadvpl/query.py:507-533`:

```python
def _impacto_fontes(conn, campo_up, max_rows):
    rows = conn.execute(
        """
        SELECT arquivo, funcao, linha_inicio,
               substr(content, max(1, instr(upper(content), ?) - 30), 160) AS snippet
        FROM fonte_chunks
        WHERE upper(content) LIKE '%' || ? || '%'
        LIMIT ?
        """,
```

Per CHANGELOG da v0.3.17: *"Impacto em fontes (`fonte_chunks.content`) NAO foi alterado"*. Ok, essa decisão é justificada (fonte pode citar o campo dentro de string maior). Porém o output do `impacto` não distingue: o usuário roda `impacto A1_COD` esperando precisão e ainda recebe rows do tipo `fonte` que casam `BA1_CODEMP`. A SX3/SX7/SX1 vem limpa; fonte não. Ninguém documenta a inconsistência.

**Reprodução:** fonte contendo `cExpr := "BA1_CODEMP"` num string. `impacto A1_COD` retorna esse fonte com snippet contendo "BA1_CODEMP". Usuário não-iniciado interpreta como uso real.

**Recomendação:** ou (a) documentar no help do `impacto` que tipo=`fonte` é substring (justificadamente menos preciso), ou (b) adicionar coluna `match_kind: exact|substring` no row, ou (c) opcionalmente filtrar fonte com `\bX\b` quando boundary é viável (excluir só matches DENTRO de identificadores).

---

### #8 — `_PARAMIXB_USAGE_RE` checa o body raw (sem strip) *(severidade: baixa)*

**Categoria:** A (false positive teórico)
**Release relevante:** v0.3.16 (#6/#10)
**Evidência:** `cli/plugadvpl/parsing/parser.py:1186-1191`:

```python
ini = int(f.get("linha_inicio", 0))
fim = int(f.get("linha_fim", ini))
if ini <= 0 or fim < ini:
    continue
body = "\n".join(content_lines[ini - 1 : fim])
if _PARAMIXB_USAGE_RE.search(body):
    result.add(nome)
```

`content_lines` é construído via `content.splitlines()` em `parse_source` linha 1513 — i.e., conteúdo **raw**, não stripped. Comentário `// PARAMIXB[1] vai aqui` ou string literal `cMsg := "Use PARAMIXB[1] na implementacao"` dentro de uma User Function comum disparam classificação como PE.

Probabilidade prática: baixa (mas não-zero — fontes copy-pasted de tutoriais TDN às vezes contêm strings explicativas com PARAMIXB).

**Recomendação:** mudar `content_lines` para vir do `stripped_strict` (`strip_advpl(content, strip_strings=True)`) que já é calculado em `parse_source`. Custo zero, correctness ganhada.

---

### #9 — Catálogo: descrição da skill `advpl-code-review` divergiu da impl pós-v0.3.19 *(severidade: média)*

**Categoria:** C (doc obsoleta) + D (catálogo × skill)
**Release relevante:** v0.3.19 (release notes mencionam atualização das tabelas, mas alguns números não bateram)
**Evidência:** `skills/advpl-code-review/SKILL.md:2,7,25,52,73,95`:

- Frontmatter: *"24 regras... (13 single-file via regex + 11 cross-file SX)"*. Realidade pós-v0.3.19: 31 regras ativas (20 single-file + 11 cross-file).
- Linha 7: *"29 são efetivamente detectadas (v0.3.9+)..."*. Realidade: 31 ativas (catálogo `lookups/lint_rules.json`: 35 total − 4 planned = 31 ativas).
- Linha 27: cabeçalho *"Single-file (18)"* com tabela de **20 linhas** (BP-001..MOD-004). Off-by-2 — não atualizado quando SEC-003 e SEC-004 saíram de planned para active.
- Linha 73: *"As 4 regras catalogadas mas não detectadas (v0.3.19)"* — corretamente diz 4. Mas a tabela acima fala "29".
- Linha 95: *"`/plugadvpl:lint <arquivo>` — roda as 13 regras single-file"*. Conta antiga.
- Linha 459-470: bloco "Info / Checklist mental (não detectadas automaticamente)" lista SEC-003 e SEC-004 como "não detectadas". Mas elas SÃO detectadas em v0.3.19.

A skill foi parcialmente atualizada (linhas SEC-003/SEC-004 ganharam entrada na tabela), mas os totais agregados e o checklist final ficaram pra trás.

**Recomendação:** atualizar contagens (`24 → 31`, `13 → 20`, `18 → 20`, `29 → 31`); remover SEC-003/SEC-004 da seção "não detectadas"; sincronizar contagens do bloco workflow (linha 95) e da tabela de "planned" (4 itens, já correto).

---

### #10 — Skill `help` desatualizada: 13 subcomandos (sao 19), falta `impacto`/`gatilho`/`sx-status`/`ingest-sx` *(severidade: média)*

**Categoria:** C (doc obsoleta)
**Release relevante:** acumulado v0.3.0..v0.3.19 (não-fix de release específica)
**Evidência:** `skills/help/SKILL.md:25-38`:

```
Lista os 13 subcomandos com descricao curta:
- `init` ... `grep`
```

Lista apenas 13 subcomandos; o CLI atual define 19 (`@app.command()` em `cli.py`: 17 ocorrências + 2 `@app.command(name=...)` para `ingest-sx` e `sx-status`). Ausentes do skill:
- `version` (subcomando antigo)
- `impacto` (Universo 2)
- `gatilho` (Universo 2)
- `ingest-sx` (Universo 2)
- `sx-status` (Universo 2)
- (`init` aparece como literal na linha "Primeira vez? `/plugadvpl:init`" — está OK na lista; somando bem, listou 13 mas faltam 6.)

Versionado `@0.3.19` no `uvx plugadvpl@0.3.19 --help` — execução correta. Só o resumo textual ficou pra trás.

**Recomendação:** atualizar lista. Idealmente, gerar via `plugadvpl --help` no momento do build do skill (out of scope para este relatório).

---

### #11 — Skills `arch` e `callers` não mencionam novas flags v0.3.18 *(severidade: baixa)*

**Categoria:** C (doc obsoleta)
**Release relevante:** v0.3.18 (#11 e #12 do QA original)
**Evidência:**
- `skills/arch/SKILL.md` lista o output esperado (linhas 14-27) — não menciona `tabelas_via_execauto`. Usuário/IA não sabem que a flag existe nem o que significa.
- `skills/callers/SKILL.md:33-37` descreve "Para cada caller: nome da funcao chamadora, arquivo:linha do call site, contexto da chamada". Não menciona `is_self_call`. A linha "Resultado vazio nao eh bug — pode ser endpoint exposto..." é boa, mas o oposto (resultado cheio de self-calls) não é abordado.

CHANGELOG v0.3.18 explicitamente cita esses flags como features novas; bumpou as 18 skills `@0.3.17 → @0.3.18` por consistência de versão, mas o conteúdo não foi tocado.

**Recomendação:** adicionar 1-2 linhas em cada skill descrevendo a flag nova, exemplo de uso (`jq '.rows[] | select(.is_self_call==false)'` para listar só externos), e quando filtrar.

---

### #12 — Skill `status` recomenda `ingest --incremental` pós-upgrade — conflita com aviso v0.3.13 *(severidade: média)*

**Categoria:** C (UX/doc inconsistente)
**Release relevante:** v0.3.13 + v0.3.15
**Evidência:** `skills/status/SKILL.md:71`:

> Se `runtime_version != plugadvpl_version`, rode `/plugadvpl:ingest --incremental` para refletir o binario novo

Mas a v0.3.13 introduziu o aviso explicando que **`--incremental` pula arquivos cujo mtime não mudou** e portanto NÃO re-aplica regras novas. A skill `ingest/SKILL.md` (linha 41-61) descreve corretamente a "Pegadinha do `--incremental` apos upgrade" e recomenda `--no-incremental`. Os dois skills se contradizem.

**Reprodução:** usuário segue skill `status`, roda `--incremental`, vê warning amarelo, fica confuso pq dois skills dizem coisas diferentes.

**Recomendação:** alinhar `status/SKILL.md:71` para `plugadvpl ingest --no-incremental` (consistente com a skill `ingest`) ou ao menos referenciar `ingest/SKILL.md` "Pegadinha do --incremental apos upgrade".

---

### #13 — `_resolve_funcao_origem` não cobre métodos de classe *(severidade: média)*

**Categoria:** A (correctness parcial)
**Release relevante:** v0.3.15 (#8 fix)
**Evidência:** `cli/plugadvpl/ingest.py:335-355`:

```python
chunk_ranges: list[tuple[int, int, str]] = sorted(
    (
        int(f.get("linha_inicio", 1)),
        int(f.get("linha_fim", int(f.get("linha_inicio", 1)))),
        f.get("nome", ""),
    )
    for f in funcoes_list
    if f.get("kind", "function") not in _NON_CHUNK_KINDS
)
```

`_NON_CHUNK_KINDS = frozenset({"mvc_hook"})`. Tudo o que não é mvc_hook entra. Bom. Mas:

- `kind="method"` (extraído por `_METHOD_RE` em parser.py:32) entra com `nome=<method_name>` (sem classe). Funciona pra resolver o método pai.
- `kind="ws_method"` (extraído por `_WSMETHOD_RE`) entra com `nome=group(2)` — segundo grupo do regex `WSMETHOD (verb)? (\w+) WS(SERVICE|SEND|RECEIVE)`. Para `WSMETHOD GET clientes WSSERVICE Vendas`, group(2) = "clientes". Para `WSMETHOD POST WSSERVICE PortaldeViagem` (verb-only WSRESTFUL — formato novo da v0.3.16), o regex `_WSMETHOD_RE` **não casa** (vide #14 abaixo); essas funções **não entram** em `chunk_ranges`. Logo, qualquer `chamada_funcao` originada nelas não tem `funcao_origem` resolvido, regredindo parcialmente o fix v0.3.15 para REST endpoints novos.

**Recomendação:** ou (a) adicionar `_WSMETHOD_REST_BARE_RE` ao extractor de funções pra incluir esses métodos como `kind="ws_method"`, ou (b) usar `rest_endpoints` como fonte alternativa de ranges para `_resolve_funcao_origem`.

---

### #14 — `WSRESTFUL` REST endpoints não viram `funcoes` (efeito cascata) *(severidade: baixa)*

**Categoria:** A (limitação conhecida não-mencionada na release)
**Release relevante:** v0.3.16 (#5/#7)
**Evidência:**
- `_WSMETHOD_RE` em `parser.py:28-31` casa `WSMETHOD (verb)? <name> WS(RECEIVE|SEND|SERVICE)` — exige um `<name>` antes de `WS...`.
- O fixture `cli/tests/fixtures/synthetic/ws_restful_classic.prw:12,18` tem `WSMETHOD GET WSSERVICE PortaldeViagem` (verb-only, sem `<name>`).
- O regex tenta: verb=`GET`, name=`WSSERVICE` (consome a palavra), depois precisa de `WS(RECEIVE|SEND|SERVICE)` — `PortaldeViagem` falha. Não match.

Resultado: `funcoes` para fixtures WSRESTFUL não inclui os endpoints. `source_type` correto via `ws_restfuls`, capability `WS-REST` correta — mas:
- `find function GET` não encontra nada.
- `callees GET` retorna vazio.
- `callers SetResponse` (chamada interna do método REST) tem `funcao_origem=""` porque o range cobrindo a linha 14 não está em `chunk_ranges`.

A release v0.3.16 corrige a classificação do **arquivo**, mas o **call graph** das funções dentro fica incompleto. Não há teste que verifique `funcoes` do fixture WSRESTFUL — só `source_type` e `capabilities`.

**Recomendação:** adicionar regex paralelo ao `_WSMETHOD_RE` para o formato verb-only e popular `funcoes` com `kind="ws_method"`, `nome=verb` (ou melhor, `nome=f"{Class}.{verb}"`). Adicionar teste `test_wsrestful_methods_appear_in_funcoes`.

---

### #15 — `ingest-sx` reporta `inserted = len(rows)` mesmo após dedup PK *(severidade: média)*

**Categoria:** A + C (bug + UX)
**Release relevante:** v0.3.14 (acompanhado pelo aviso de dedup, mas o counter ainda mente)
**Evidência:** `cli/plugadvpl/ingest_sx.py:256-273`:

```python
inserted = _bulk_insert(conn, table, columns, rows)
conn.commit()
counters["per_table"][table] = inserted
counters["total_rows"] += inserted
...
lost = inserted - distinct
if lost > 0:
    print(
        f"WARN: tabela '{table}': {inserted} linhas CSV "
        f"→ {distinct} distintas após PK dedup "
        f"({lost} duplicada(s) na PK {pk_cols} foram sobrescrita(s)).",
        file=sys.stderr,
    )
```

`_bulk_insert` retorna `len(batch)` somado — sempre `len(rows)`, independente de quantos colidiram em `INSERT OR REPLACE`. Logo `counters["per_table"][table] = inserted = len(rows)`, mesmo que SQLite agora tenha apenas `distinct` rows. O CLI `ingest-sx` mostra `summary.per_table.gatilhos = 26.251` enquanto `sx-status` (que faz `COUNT(*)` real) mostra `25.930`. Justamente a discrepância apontada no #15 do round 1.

A v0.3.14 adicionou WARN em stderr — bom — mas o número exibido no resumo continua inflado. Quem só lê o summary tira número errado.

**Recomendação:** trocar `counters["per_table"][table] = inserted` por `counters["per_table"][table] = distinct` (e renomear `inserted` para `csv_rows` se quiser preservar o número original na warning). Atualizar `total_rows` análogo.

---

### #16 — `sx_status` retorna keys instáveis (depende de `_sx_tables_present`) *(severidade: baixa)*

**Categoria:** F (UX defensivo) + B
**Release relevante:** N/A (pré-existente, mas relevante após v0.3.14 que reforçou checks SX)
**Evidência:** `cli/plugadvpl/query.py:799-815`:

```python
def sx_status(conn):
    if not _sx_tables_present(conn):
        return [{"sx_ingerido": False, "msg": "Rode 'plugadvpl ingest-sx <dir>' primeiro."}]
    out = {"sx_ingerido": True, "last_sx_ingest_at": ..., "sx_csv_dir": ...}
    for table in (...):
        out[table] = ...
```

Estrutura do row varia drasticamente: 2 keys quando ausente, 14 quando presente. Quem parsea programaticamente (`--format json`) precisa branchear. Não é bug em si, mas adicionar campos consistentes (zero quando ausente) facilita.

**Recomendação:** retornar sempre o mesmo schema; `sx_ingerido=False` + tabelas com `0`. Issue baixa prioridade.

---

### #17 — Catálogo SEC-003/SEC-004 fix_guidance é claro mas longo *(severidade: baixa)*

**Categoria:** C (UX)
**Release relevante:** v0.3.19
**Evidência:** `lookups/lint_rules.json:127, 138`. Os `fix_guidance` ocupam ~3-5 linhas longas com vírgulas, citando MV_RELAUSR/MV_RELAPSW etc. Em terminal estreito (Rich `--format table`), esses textos quebram em cell wrapping pesado e ofuscam a estrutura. Não é bug; só polish.

**Recomendação:** considerar `fix_guidance_short` (uma linha) + `fix_guidance_long` (parágrafo) — diferentes formatos consomem o que faz sentido. Out-of-scope pra agora.

---

### #18 — `_GLOBAL_FLAGS` set não inclui `--workers`, `--no-content`, `--redact-secrets` *(severidade: baixa)*

**Categoria:** A (false negative no hint)
**Release relevante:** v0.3.15 (#2)
**Evidência:** `cli/plugadvpl/cli.py:1040-1043`:

```python
_GLOBAL_FLAGS = {
    "--root", "-r", "--db", "--format", "-f", "--limit", "--offset",
    "--compact", "--quiet", "-q", "--no-next-steps", "--version", "-V",
}
```

Flags como `--workers`, `--no-content`, `--redact-secrets`, `--no-incremental`, `--check-stale`, `--cross-file` são **subcommand-scoped**, não globais. Boa demarcação. Porém, o usuário inexperiente pode rodar `plugadvpl --workers 8 ingest` (esperando que seja global) e tomar `No such option: --workers`. O hint atual só dispara para flags em `_GLOBAL_FLAGS`. Quem usar uma flag de subcomando antes do subcomando não recebe hint algum (continua com erro Click cru). Inverso do bug original mas mesmo problema de UX.

**Recomendação:** adicionar 2ª heurística: se Click reporta "No such option: X" e X é uma flag conhecida de algum subcomando, sugerir `plugadvpl <subcmd> X` em vez de `plugadvpl X <subcmd>`. Out-of-scope pra v0.3.x; documentar como follow-up.

---

### #19 — Test `test_callees_by_function_name_works` fixture é minimalista *(severidade: baixa)*

**Categoria:** B (test too-shallow)
**Release relevante:** v0.3.15 (#8)
**Evidência:** `cli/tests/unit/test_query.py:120` — teste valida que `callees("Outer")` retorna chamada para "Inner". Cobre o caso happy-path. **Não cobre**:
- `funcao_origem` resolvido para método dentro de Class (chunk mais interno).
- Static Function aninhada / overloads.
- Caso onde `linha_origem == 0` (chamada fora de função, e.g., a nível de arquivo).
- Caso WSRESTFUL com método verb-only (vide #14 — provavelmente broken).

A docstring da v0.3.15 fala de "chunk MAIS INTERNO em caso de nesting (Class > Method > Static)" — mas o teste não exercita nesting.

**Recomendação:** adicionar fixture com `Class A` contendo `Method M1 Class A` e `Static Function helper` na mesma `.prw`, validar que call dentro de `M1` resolve `funcao_origem="M1"` (não "helper" nem "A").

---

### #20 — Encoding dos arquivos de skill misto (alguns sem acento, outros com) *(severidade: baixa)*

**Categoria:** C (consistência)
**Release relevante:** —
**Evidência:** `skills/help/SKILL.md`, `skills/status/SKILL.md`, `skills/ingest-sx/SKILL.md` — usam "execucao", "saida", "configuracao" sem acento. Outras skills (`advpl-code-review`) usam acentos completos. Provavelmente legado de geração via terminal Windows cp1252. Nada quebrado, mas polish.

**Recomendação:** padronizar; baixa prioridade.

---

## Resumo executivo (tabela)

| # | Achado | Severidade | Categoria | Release |
|---:|---|---|---|---|
| 1 | SEC-003 inclui `Help` (UI, não log) → false positives massivos | **alta** | A+B | v0.3.19 |
| 2 | SEC-003 var regex (`Pass`/`Pin`/`Card`) casa palavras comuns PT-BR | **alta** | A | v0.3.19 |
| 3 | SEC-004 `PREPARE ENV ... PASSWORD` regex não suporta `;` continuação | baixa | A | v0.3.19 |
| 4 | SEC-004 `RpcSetEnv` regex exige literal nos slots 1+2 (caso real usa var) | média | A | v0.3.19 |
| 5 | SEC-003 cobre só A1_*/RA_* — falta A2_*, RH_*, etc. | baixa | B | v0.3.19 |
| 6 | `gatilho` only-downstream mesmo após v0.3.15 OR-fix | média | A+C | v0.3.15 |
| 7 | `impacto fonte` não usa boundary — usuário não sabe (sem flag) | baixa | C | v0.3.17 |
| 8 | `_PARAMIXB_USAGE_RE` busca em raw (sem strip) | baixa | A | v0.3.16 |
| 9 | Skill `advpl-code-review` com contagens divergidas (24/13/29 → 31/20/31) | média | C+D | v0.3.19 |
| 10 | Skill `help` lista 13 subcomandos (são 19) | média | C | acumulado |
| 11 | Skills `arch`/`callers` não mencionam `tabelas_via_execauto`/`is_self_call` | baixa | C | v0.3.18 |
| 12 | Skill `status` recomenda `--incremental` (conflita com `ingest` skill) | média | C | v0.3.13/v0.3.15 |
| 13 | `_resolve_funcao_origem` quebra para WSRESTFUL verb-only (cascata #14) | média | A | v0.3.15+v0.3.16 |
| 14 | `funcoes` não popula REST verb-only — `find/callees/callers` cegos | baixa | A+B | v0.3.16 |
| 15 | `ingest-sx per_table` mostra inserted, não distinct — número infla | média | A+C | v0.3.14 |
| 16 | `sx_status` retorna schema instável (2 vs 14 keys) | baixa | F+B | — |
| 17 | `fix_guidance` SEC-003/SEC-004 longo, quebra em terminal estreito | baixa | C | v0.3.19 |
| 18 | `_GLOBAL_FLAGS` hint só cobre globais, não flags subcomando misplaced | baixa | A | v0.3.15 |
| 19 | Teste callees nesting test-shallow (sem Class+Method) | baixa | B | v0.3.15 |
| 20 | Skills mistura "execucao"/"execução" — encoding inconsistente | baixa | C | — |

## Top-3 a priorizar

1. **#1 — Remover `Help` de SEC-003.** Single-line fix em `_SEC003_LOG_FUNCS_RE` + 1 teste negativo. Sem isso, o detector vai disparar em qualquer fonte MVC real (Help é universal em validação/erro UI). É uma regressão de UX sobre uma regra que estréia bandeira de "LGPD".
2. **#2 — Restringir `_SEC003_PII_VAR_RE`.** Trocar `Pass|Pin|Card|Rg` curtos por matches mais estritos (exigir prefixo Hungarian `c` literal, OU usar formas longas), adicionar testes negativos com `cPassagem`/`cPintar`/`cCardapio`. Sem isso, projetos PT-BR (especialmente turismo, varejo, food) vão receber centenas de falsos positivos.
3. **#9 + #10 + #12 — Sincronizar skills.** Atualizar contagens da `advpl-code-review` (`24→31`, `13→20`), expandir lista de subcomandos do `help`, alinhar `status` com a recomendação `--no-incremental` da `ingest`. Custo total: ~30 minutos. Impacto: agentes IA upstream passam a ver realidade da v0.3.19 em vez de v0.3.4.

## O que funcionou bem

- **`test_lint_catalog_consistency.py`**: o guard de drift fez exatamente o trabalho — durante v0.3.19 detectou que SEC-003/SEC-004 viraram `active` no JSON sem `_check_*` correspondente em `lint.py`. Esse teste é dinheiro investido bem.
- **Pesquisa-first metodologia**: SEC-004 `RpcSetEnv` slot 3+4 padrão TDN, PARAMIXB[N] heurística pro PE — release notes mencionam consulta a TDN/comunidade antes do detector. Mostra rigor técnico.
- **Word boundary ADVPL-aware** (`_word_boundary_re` em query.py): a documentação inline explicando "`_` é `\\w` no Python, então `\\bA1_COD\\b` NÃO casa em `BA1_COD`" é exemplar — facilita manutenção e evita reintrodução do bug.
- **Fixtures dedicadas** (`pe_paramixb.prw`, `ws_restful_classic.prw`, `reclock_alias_dup_trigger.prw`): cada fix v0.3.16-v0.3.18 ganhou fixture mínimo para o caso, sem inflar test data. Boa disciplina.
- **`--version` / `-V` global** + `_detect_misplaced_global_flag`: UX de transparency runtime vs index version está sólida; o hint friendly é exatamente o tipo de polish que IAs externas pegam (e foi feedback de IA externa que motivou).
- **CHANGELOG.md detalhado**: cada release nomeia o `#N do QA report` que está fechando, preservando rastreabilidade entre relatório original e fix. Útil pra round 2 (este relatório).
- **v0.3.18 closeout**: o backlog do round 1 chegou a zero — todos os 13 achados endereçados em 4 releases consecutivas. Disciplina rara.

## Notas finais

- Severidade "alta" foi reservada pra detectores SEC-003 que **vão disparar em massa** assim que usuários rodarem `ingest --no-incremental` na v0.3.19. Os outros achados são polish ou edge case — nenhum compromete dados ou bloqueia uso normal.
- Não foi possível executar contra cliente real, então as taxas exatas de false positive são inferidas da leitura dos regex × conhecimento ADVPL. Se conseguirem rodar v0.3.19 contra o mesmo projeto Marfrig do round 1 com `lint --severity warning --regra SEC-003`, o número total vs filtrar `Help`-related deve confirmar.
- O catálogo `lint_rules.json` está com 35 regras (31 active + 4 planned) — a categoria SEC fechou conforme prometido. Próximo grande tema natural (v0.4.0?) seria fechar BP-007 (Protheus.doc) ou começar Universo 3 (rastreabilidade).
