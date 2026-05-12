---
description: Top 30 erros comuns em ADVPL/TLPP em produção e métodos de debug. Tabela de sintoma → causa raiz → comando de diagnóstico → fix. Use quando o usuário cola um erro do AppServer.log, descreve "está dando erro" sem detalhe, ou pede ajuda pra investigar bug Protheus.
---

# advpl-debugging — Erros comuns e métodos de debug

Catálogo dos 30 erros mais frequentes em produção Protheus, organizados por **sintoma**
(o que aparece pro usuário ou no log) → **causa raiz** → **comando de diagnóstico** →
**fix típico**. Coberto em paralelo: ferramentas de debug do AppServer e métodos
manuais quando não dá pra anexar debugger.

## Como usar

1. Cole no chat o **traceback do AppServer.log** ou descreva o sintoma.
2. Procure pela seção que casa (Ctrl+F na tabela abaixo).
3. Para cada causa raiz há comando `plugadvpl` pra confirmar in-codebase.
4. Aplique o fix; valide com lint.

---

## Tabela rápida de sintomas → causa raiz

| Sintoma / Mensagem | Causa raiz | Diagnóstico |
|---|---|---|
| `Variable does not exist: NOME` | Local em escopo errado, ou Private declarada depois do uso | `plugadvpl arch <arq>` + lint BP-002 |
| `Type mismatch` em campo numérico após query | Falta `TCSetField` pós-BeginSql | `plugadvpl lint --regra PERF-003` |
| `RecLock failed` ou registro travado | RecLock anterior sem MsUnlock; outro processo travou | `plugadvpl lint --regra BP-001` |
| `Index out of range` em array | aSize/aDim divergente do esperado, ou índice 0 (ADVPL é 1-based) | Inspect via ConOut |
| Erro "Acesso à área inválida" | DbSelectArea sem fonte aberta, ou alias fechado antes do uso | `plugadvpl arch <arq>` |
| Pergunta SX1 não aparece | Grupo não cadastrado, ou idioma do MV_IDIOMA não tem entradas | `plugadvpl impacto <pergunta>` |
| Campo SX3 não aparece no cadastro | X3_USADO ausente, ordem incorreta, ou X3_RELACAO retornando vazio | `plugadvpl impacto <campo>` |
| Gatilho SX7 não dispara | X7_CONDIC = `.F.`; ou campo origem não está em SX3 | `plugadvpl gatilho <campo>` |
| `Browse vazio` mas dados existem em SQL | Filtro fixo, xFilial inválido, ou índice apontando errado | `plugadvpl grep "%xfilial%"` |
| MV_PAR retorna vazio em Pergunte | Variáveis Private MV_PAR* não inicializadas; nLin do Pergunte errado | inspect manual |
| Job não roda agendado | `RpcSetEnv` sem empresa/filial; `StartJob` falhando em deps | `plugadvpl callers <Job>` |
| REST endpoint retorna 500 | Self:GetContent vazio sem validação; ou WSRESTFUL Method não bate verbo HTTP | `plugadvpl grep "WSRESTFUL"` |
| MD-FE / NF-e rejeitada | Tag XML errada; lib desatualizada (cMV `MV_NFCSERV`) | `plugadvpl param MV_NFCSERV` |
| ConOut mostrando lixo / chars estranhos | Encoding errado (cp1252 vs utf-8); BOM em arquivo | `plugadvpl doctor` |
| Performance subitamente péssima | DbSeek em loop novo; falta TCSetField; índice estourado | `plugadvpl lint --regra PERF-002` |

---

## 1. `Variable does not exist: NOME`

**Sintoma típico no AppServer.log:**
```
Variable does not exist: CCLIENTE
Called from FOO.PRW(45)
```

**Causa raiz #1** — Variável **Local** declarada em outra função (escopos são por função
em ADVPL).

**Causa raiz #2** — Variável usada **antes** de `Private/Public` declarar.

**Causa raiz #3** — Typo no nome (raro mas acontece).

**Diagnóstico:**
```bash
plugadvpl arch FOO.prw                    # mostra ranges de função
plugadvpl grep "cCliente"                  # confirma onde aparece
plugadvpl lint FOO.prw --regra BP-002      # detecta Local fora do header
```

**Fix:** mover declaração `Local cCliente` pro topo da função, ou usar `Private` se
precisa visibilidade entre funções (com cautela — `[[advpl-fundamentals]]`).

---

## 2. `Type mismatch` ou data/numérico bagunçado pós-query

**Sintoma:**
```
Type mismatch in operation: + (CHAR + NUMERIC)
```
Ou: campo `B1_PRV1` que deveria ser numérico vem como string `"00000001234.5600"`.

**Causa raiz:** após `BeginSql Alias "QRY"` ou `TCQuery`, o ADO retorna **tudo como
string** se você não declarar tipo. Falta `TCSetField`.

**Diagnóstico:**
```bash
plugadvpl lint --regra PERF-003 <arq>   # detecta query sem TCSetField
```

**Fix:**
```advpl
BeginSql Alias "QRY"
    SELECT B1_COD, B1_PRV1, B1_DTCAD FROM %table:SB1% ...
EndSql
TCSetField("QRY", "B1_PRV1",  "N", 14, 4)    // numérico
TCSetField("QRY", "B1_DTCAD", "D")             // data
```

---

## 3. `RecLock failed` / registro travado

**Sintoma:**
```
RecLock failed on SA1010 record 12345
```

**Causa raiz #1** — Outro usuário travou (uso legítimo).

**Causa raiz #2** — Seu próprio código deixou RecLock sem MsUnlock anterior. O Protheus
mantém lock até a session morrer.

**Causa raiz #3** — Erro no meio do `Begin Transaction` sem `DisarmTransaction()`.

**Diagnóstico:**
```bash
plugadvpl lint --regra BP-001 <arq>      # acha RecLock sem MsUnlock pareado
plugadvpl callers MsUnlock               # verifica se cobertura tá completa
```

**Fix manual no DBAccess:** se for trava órfã do seu próprio sistema, o admin pode matar
no `dbmonitor.bat` (Protheus tem ferramenta gráfica).

**Fix no código:** sempre usar pattern guard:

```advpl
RecLock("SA1", .F.)
Begin Sequence
    SA1->A1_NOME := cNovo
Recover Using oErr
    SA1->(MsUnlock())   // garante unlock mesmo em erro
    Break oErr
End Sequence
SA1->(MsUnlock())
```

Ou simplesmente usar `Begin Transaction` que faz unlock+rollback automático em erro.

---

## 4. `Index out of range` em array

**Sintoma:**
```
Index out of range: 4 not in [1, 3]
Called from FOO.PRW(89) in line:  aDados[4][2] := "X"
```

**Causa raiz #1** — ADVPL arrays são **1-based**. `aDados[0]` é erro.

**Causa raiz #2** — Loop até `Len(aDados)+1` ou cálculo errado de índice.

**Causa raiz #3** — Array foi `aDel`/`aSize` em outro lugar; não tem o tamanho que você
acha.

**Diagnóstico — ConOut + AScan:**
```advpl
ConOut("DEBUG aDados len=" + cValToChar(Len(aDados)))
ConOut("DEBUG aDados[1] = " + cValToChar(AScan(aDados, "buscado")))
```

**Fix:** sempre `If Len(aDados) >= nIdx` antes de acessar.

---

## 5. Pergunta SX1 não aparece em `Pergunte()`

**Sintoma:** janela do Pergunte aparece vazia, ou só com a primeira pergunta.

**Causa raiz #1** — Grupo não tem entrada na SX1 pra MV_IDIOMA atual (português/inglês/
espanhol). Cliente em pt-BR vai precisar `X1_IDIOMA = '01'`.

**Causa raiz #2** — `X1_GRUPO` na rotina não bate com o cadastrado (case-sensitive, padding).

**Causa raiz #3** — `Pergunte("GRUPO", .F.)` com `lAtual = .F.` significa "use defaults",
não exibe a janela.

**Diagnóstico:**
```bash
plugadvpl impacto MGFREL01                # vê onde a pergunta é usada
# No SQL direto:
SELECT * FROM SX1010 WHERE X1_GRUPO = 'MGFREL01' AND D_E_L_E_T_ = ' '
```

**Fix:** cadastrar entrada em SX1 (Configurador) ou rodar update SX1 customizado.

---

## 6. Campo SX3 customizado não aparece no cadastro

**Sintoma:** adicionou `A1_XCAMPO` na SX3, mas no AxCadastro/MVC não aparece.

**Causa raiz #1** — `X3_USADO` vazio (precisa de valor binário válido tipo
`"þþ                  "`).

**Causa raiz #2** — `X3_ORDEM` igual a outro campo; conflito.

**Causa raiz #3** — Cadastro está em pasta SXA que não tem o campo (X3_FOLDER).

**Causa raiz #4** — Browse customizado tem lista fixa de campos.

**Diagnóstico:**
```bash
plugadvpl impacto A1_XCAMPO         # vê pasta, ordem, dependências
plugadvpl lint --cross-file --regra SX-001    # X3_VALID que chama U_xxx inexistente
```

**Fix:** preencher `X3_USADO` corretamente. Tem um helper `FwPutSX3()` que faz isso
automático no script de update.

---

## 7. Gatilho SX7 não dispara

**Sintoma:** mudou `A1_COD`, mas `A1_NREDUZ` não recalcula como esperado.

**Causa raiz #1** — `X7_CONDIC` retorna `.F.` (talvez quebra implícita).

**Causa raiz #2** — `X7_CDOMIN` aponta pra campo que não existe na SX3.

**Causa raiz #3** — Tipo do gatilho (`X7_TIPO`) é `S` (Secundário) sem SEEK obrigatório
e a chave não foi posicionada.

**Diagnóstico:**
```bash
plugadvpl gatilho A1_COD --depth 3       # cadeia completa
plugadvpl lint --cross-file --regra SX-002    # gatilhos com destino inexistente
plugadvpl lint --cross-file --regra SX-010    # Pesquisar sem SEEK
```

**Fix:** depende do caso. Para SX-002 (destino inexistente), criar o campo ou apagar o
gatilho. Para SX-010 (sem SEEK), marcar `X7_SEEK = 'S'`.

---

## 8. Browse mostra vazio mas SQL retorna linhas

**Sintoma:** `SELECT * FROM SA1010 WHERE A1_FILIAL='01'` no DBeaver retorna 500 linhas,
mas no Protheus browse aparece vazio.

**Causa raiz #1** — `xFilial("SA1")` está retornando algo diferente de `'01'` porque o
parâmetro `MV_LOCALIZA` está modo "Compartilhada", não exclusivo. Veja `[[advpl-fundamentals]]`.

**Causa raiz #2** — Filtro do browse (`oBrw:SetFilterDefault()`) está ativo.

**Causa raiz #3** — Índice atual aponta pra coluna sem dado; muda `DbSetOrder()`.

**Diagnóstico:**
```bash
plugadvpl param MV_LOCALIZA              # entende modo de compartilhamento
plugadvpl grep "SetFilterDefault\|SetFilter"   # filtros estáticos
```

**Fix:** revisar uso de `xFilial()` — em modo Compartilhado, retorna string vazia em
algumas tabelas. Em modo Exclusivo retorna `cFilAnt`.

---

## 9. `MV_PAR01` retorna vazio depois de Pergunte()

**Sintoma:** `Pergunte("GRUPO", .T.)` mostra a janela e o usuário responde, mas `MV_PAR01`
ainda vem vazio.

**Causa raiz #1** — As variáveis MV_PAR* são **Private** declaradas pelo Pergunte. Se
você está em função `Static` que chama outra função `Static`, a outra não vê (escopo
Private propaga para chamadas, mas... casos sutis).

**Causa raiz #2** — `Pergunte("GRUPO", .F.)` com `lAtual=.F.` carrega defaults da SX1
mas **NÃO** mostra janela. Defaults vazios → MV_PAR vazio.

**Diagnóstico:** manual; insira `ConOut` logo após Pergunte:
```advpl
Pergunte("MGFREL01", .T.)
ConOut("DEBUG MV_PAR01=" + cValToChar(MV_PAR01))
```

**Fix:** garantir `lAtual=.T.` e que SX1 tem defaults sensatos.

---

## 10. Job não roda no agendado

**Sintoma:** schedule registrado em `appserver.ini`, hora certa, mas Job não executa
(ou executa e nada acontece).

**Causa raiz #1** — Falta `RpcSetEnv("99", "01", , , , "FAT")` antes do código real
(Job começa sem empresa/filial).

**Causa raiz #2** — Função do Job precisa começar com `User Function` (não Static).

**Causa raiz #3** — Há trava `OpenSx*` que bloqueia abrir as tabelas.

**Diagnóstico:**
```bash
plugadvpl callers JOB_NOME               # quem chama / qual a entrada
plugadvpl arch <arquivo-do-job>
```

**Fix esqueleto correto:**

```advpl
User Function JOB_REL01()
    Local lOk := .F.
    RpcSetEnv("99", "01", , , , "FAT")
    Begin Sequence
        // ... lógica real
        lOk := .T.
    Recover Using oErr
        ConOut("Job falhou: " + oErr:Description)
    End Sequence
    RpcClearEnv()
Return lOk
```

Ver `[[advpl-jobs-rpc]]` para detalhes.

---

## 11. REST endpoint retorna 500

**Sintoma:** chamar `POST /rest/api/zclientes` retorna `500 Internal Server Error`.

**Causa raiz #1** — `Self:GetContent()` retorna vazio (Content-Type não é
`application/json` ou body vazio).

**Causa raiz #2** — Method ADVPL declarado para `GET` mas request é `POST` (anotação
`@Post` ausente).

**Causa raiz #3** — Conversão de JSON com `FwJsonDeserialize` recebe string que não é
JSON válido; lança exceção.

**Diagnóstico:**
```bash
plugadvpl grep "WSRESTFUL\|WSMETHOD"
plugadvpl arch <arquivo-rest>            # vê endpoints
```

**Fix:**
```advpl
WSMETHOD POST cadastraCliente WSRECEIVE cBody WSSERVICE zClientes
    Local oJson := Nil
    Local cBody := Self:GetContent()

    If Empty(cBody)
        Self:SetResponse('{"error":"empty body"}')
        Self:SetReturnCode(400)
        Return .F.
    EndIf

    Begin Sequence
        FwJsonDeserialize(cBody, @oJson)
    Recover Using oErr
        Self:SetResponse('{"error":"invalid JSON: ' + oErr:Description + '"}')
        Self:SetReturnCode(400)
        Return .F.
    End Sequence
    // ... lógica
Return .T.
```

Ver `[[advpl-webservice]]`.

---

## 12. Encoding bagunçado / chars estranhos em ConOut ou arquivo

**Sintoma:** ConOut mostra `Não há` em vez de `Não há`. Ou arquivo CSV exportado com
acentos virou lixo.

**Causa raiz #1** — Fonte `.prw` salvo em UTF-8 quando o Protheus espera cp1252 (R10/R11).

**Causa raiz #2** — Fonte `.tlpp` em cp1252 quando o compilador espera UTF-8.

**Causa raiz #3** — BOM (Byte Order Mark) no início do arquivo confunde o parser.

**Diagnóstico:**
```bash
plugadvpl doctor                         # checa encoding de fontes
plugadvpl arch <arquivo>                 # mostra encoding detectado
```

**Fix:** padronize `[[advpl-encoding]]`. Regra geral: `.prw` em cp1252, `.tlpp` em UTF-8.

---

## 13. Performance subitamente péssima

**Sintoma:** rotina que rodava em 30s passou a demorar 5 minutos.

**Causa raiz #1** — Alguém adicionou `DbSeek` em loop (anti-N+1 violado).

**Causa raiz #2** — Falta `TCSetField` em query nova → string-to-number em cada linha.

**Causa raiz #3** — Índice novo não foi rebuildado; otimizador escolheu plano ruim.

**Causa raiz #4** — Tabela cresceu (10× linhas) mas `WHERE` não usa índice.

**Diagnóstico:**
```bash
plugadvpl lint --regra PERF-002 <arq>    # DbSeek em loop
plugadvpl lint --regra PERF-003 <arq>    # TCSetField faltando
plugadvpl lint --regra PERF-001 <arq>    # SELECT *
```

**Fix:** veja `[[advpl-refactoring]]` padrão 1 (DbSeek loop → SQL embarcado).

---

## Métodos de debug quando não dá pra anexar debugger

ADVPL tem debugger gráfico no TDS/SmartIDE, mas em produção (Linux server, sem GUI)
geralmente não. Métodos manuais:

### `ConOut()` — log no console do AppServer

```advpl
ConOut("DEBUG cValor=" + cValToChar(cValor) + " nLen=" + cValToChar(Len(aVar)))
```

Saída cai no `console.log` do AppServer. Use `tail -f console.log` no Linux.

### `MemoWrite("trace.txt", cStr)` — escreve em arquivo

```advpl
MemoWrite("\system\debug\rel01.txt", FwTimeStamp() + " - " + cValToChar(MV_PAR01) + Chr(13)+Chr(10), .T.)
```

Útil quando precisa de log persistente que sobreviva ao restart do AppServer.

### `FwLogMsg()` — log estruturado

```advpl
FwLogMsg("INFO", , "MGFFAT", "RELATORIO_VENDAS", , "Iniciado para filial " + cFilial)
```

Versões R26+ têm tabela `FWN` pra log estruturado consultável.

### `varInfo()` — inspect de qualquer variável

```advpl
ConOut(varInfo("aDados", aDados))
```

Mostra estrutura completa do array/objeto.

### `aClone()` + inspect antes/depois

```advpl
Local aAntes := aClone(aDados)
// ... modifica aDados
ConOut("DIFF " + cValToChar(Len(aAntes)) + " -> " + cValToChar(Len(aDados)))
```

### Conta de chamadas com `nCount`

```advpl
Local nCount := 0
Public nGlobalCount := 0
// dentro da função
nCount++
nGlobalCount++
ConOut("ENTROU pela " + cValToChar(nCount) + "x  (global=" + cValToChar(nGlobalCount) + ")")
```

---

## Workflow de debug

1. **Reproduza o erro consistentemente** — sem repro, qualquer fix é chute.
2. **Cole o traceback completo do AppServer.log** — não só "deu erro".
3. **Use a tabela rápida acima** pra mapear sintoma → causa raiz candidata.
4. **Rode o comando `plugadvpl` correspondente** pra confirmar in-codebase.
5. **ConOut/MemoWrite em pontos-chave** se ainda não está claro.
6. **Aplique fix mínimo** (um por vez).
7. **Valide com lint** que não introduziu novos findings.

## Anti-padrões de debug

- **"Vou debugar com print()" sem ConOut estruturado:** depois esquece de remover e enche
  o `console.log`.
- **Print sem timestamp e sem identificador da função:** quando o log tem 10k linhas,
  print solto sem contexto é inútil.
- **Modificar código pra forçar fluxo só pra debugar:** muda comportamento, esconde bug.
  Use ConOut sem alterar lógica.
- **Aplicar fix sem entender por que funciona:** acumula tech debt + risco de regredir
  em refactor futuro.

## Comandos plugadvpl relacionados

- `/plugadvpl:arch <arquivo>` — entender escopo antes de investigar.
- `/plugadvpl:callers <funcao>` — quem chama, ajuda achar bug upstream.
- `/plugadvpl:callees <funcao>` — o que essa função chama, ajuda achar bug downstream.
- `/plugadvpl:grep "<padrao>"` — busca textual no projeto.
- `/plugadvpl:lint <arq>` — todos os findings, foco em critical/error.
- `/plugadvpl:impacto <campo>` — pra bugs envolvendo SX3/SX7/SX1.
- `/plugadvpl:gatilho <campo>` — debug de cascata SX7.
- `/plugadvpl:doctor` — checa integridade do índice.
- `[[advpl-fundamentals]]` — variáveis Private/Public/Local, escopos.
- `[[advpl-encoding]]` — bugs de encoding.
- `[[advpl-refactoring]]` — quando o "bug" é só performance ruim.
