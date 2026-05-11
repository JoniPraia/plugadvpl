---
description: Dicionário SX do Protheus — SX1 (perguntas), SX2 (mapeamento de arquivos), SX3 (campos), SX5 (tabelas genéricas), SX6 (parâmetros MV_*), SX7 (gatilhos), SX8 (numeração), SX9 (relacionamentos), SXA (pastas), SXB (consultas F3), SIX (índices), SXE/SXF (sequência). Use ao customizar via dicionário, criar campo/parâmetro/gatilho/consulta, ou diagnosticar comportamento controlado pelo SX.
---

# advpl-dicionario-sx — Dicionário de dados Protheus

O **Dicionário SX** é o conjunto de tabelas de metadados que controlam estrutura, apresentação, validação e comportamento de tudo no Protheus. **Parte do código-fonte do Protheus está no dicionário** — alterar SX3, SX7, SXB muda comportamento sem recompilar.

## Quando usar

- Usuário pede para "criar campo", "adicionar parâmetro `MV_*`", "criar gatilho", "criar pergunta", "criar consulta F3".
- Investigar por que um campo aparece/desaparece (provavelmente `X3_USADO`/`X3_WHEN`).
- Customizar comportamento sem mexer em fonte (preferir SX a PE quando possível).
- Tabela do projeto: `dictionary_sx` no índice plugadvpl cataloga campos/parâmetros/gatilhos.

## Mapa das tabelas SX

| Tabela | Função                                     | Cardinalidade típica            |
|--------|---------------------------------------------|---------------------------------|
| SX1    | Perguntas (`Pergunte`/`ParamBox`)           | ~10k+ por instalação            |
| SX2    | Mapeamento físico de arquivos               | ~1500 tabelas oficiais          |
| SX3    | Campos de tabelas (estrutura + UI + regras) | ~80k campos                     |
| SX5    | Tabelas genéricas (códigos auxiliares)      | ~5k registros                   |
| SX6    | Parâmetros `MV_*` (configuração)            | ~3k parâmetros                  |
| SX7    | Gatilhos de campo                           | ~10k gatilhos                   |
| SX8    | Reserva de numeração sequencial             | runtime                         |
| SX9    | Relacionamentos entre entidades             | ~20k                            |
| SXA    | Pastas (folders) de cadastro                | ~500                            |
| SXB    | Consultas padrão F3                         | ~2k                             |
| SXE/SXF| Controle de sequência                       | runtime                         |
| SIX    | Índices físicos das tabelas                 | ~5k índices                     |

## SX3 — Campos (o mais importante)

```
X3_ARQUIVO  Tabela (ex: SA1)
X3_CAMPO    Nome (A1_COD)
X3_TIPO     C/N/D/M/L (character/numeric/date/memo/logical)
X3_TAMANHO  Tamanho
X3_DECIMAL  Casas decimais
X3_TITULO   Título da coluna (PT)
X3_DESCRIC  Descrição estendida
X3_PICTURE  Máscara (`@!`, `@E 999,999.99`)
X3_VALID    Expressão de validação (`U_XYZVAL()`)
X3_WHEN     Habilitação condicional
X3_USADO    Bitmap de uso por contexto
X3_BROWSE   Aparece em browse? (S/N)
X3_RELACAO  Default/fórmula
X3_F3       Consulta padrão (referência à SXB)
X3_TRIGGER  Disparar gatilho (S/N)
```

### Customizando campo sem mexer no fonte

- **Esconder**: `X3_BROWSE='N'`, `X3_NIVEL` baixo.
- **Tornar opcional**: `X3_OBRIGAT=''`.
- **Validação custom**: `X3_VALID := "U_XYZVAL()"`.
- **Default**: `X3_RELACAO := "U_XYZDEF()"`.

## SX7 — Gatilhos

Disparam ao terminar edição de um campo, modificando outro.

```
X7_CAMPO   Campo gatilho (A1_COD)
X7_SEQUENC Sequência (01, 02, ...)
X7_REGRA   Expressão que retorna valor
X7_CDOMIN  Campo destino (A1_NOME)
X7_TIPO    P (Primário) ou S (Secundário)
X7_SEEK    "S" — usa DbSeek + alias na regra
X7_ALIAS   Alias-fonte (se SEEK=S)
X7_ORDEM   Ordem do índice no seek
X7_CHAVE   Expressão da chave para o seek
```

Exemplo: ao digitar `A1_COD`, busca no SA1 e preenche `A1_NOME`:

```
X7_CAMPO   = A1_COD
X7_REGRA   = SA1->A1_NOME
X7_CDOMIN  = A1_NOME
X7_SEEK    = S
X7_ALIAS   = SA1
X7_ORDEM   = 1
X7_CHAVE   = xFilial("SA1") + M->A1_COD
```

## SX1 — Perguntas

```advpl
// Para criar pergunta:
PutSx1("XYZREL ", "01", "Empresa De?", "Empresa De?", "Empresa De?", "mv_ch1", "C", 2, 0, 0, "G", "", "mv_par01", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", {}, {}, {}, "")
// Em código, ler:
Pergunte("XYZREL", .T.)  // abre dialog
nValor := MV_PAR02
```

## SX6 — Parâmetros MV_*

```advpl
// Ler parâmetro
cValor := GetMV("MV_LOCPAD", .F., "01")  // default "01" se não existir
nValor := GetMV("MV_LIMCRD", .F., 0)

// Criar via PutMV (raro em runtime, mais em update sx)
PutMV("MV_XYZPAR", "valor")
```

Parâmetros são por empresa/filial. SE prefixo `MV_` é convenção. **Cliente** deve usar prefixo customizado (ex: `MV_XYZxxx`).

## SXB — Consultas F3

Tipo `1` (Consulta padrão) + tipo `2` (Filtros/colunas) + tipo `3` (Itens da consulta) + tipo `4` (Validações).

```
XB_ALIAS   Identificador (ex: SA1XYZ)
XB_TIPO    1/2/3/4
XB_SEQ     Sequência
XB_COLUNA  Coluna do filtro
XB_DESCR1  Descrição PT
XB_CONTEM  Conteúdo (campo, condição, etc.)
```

Atribui ao campo via `X3_F3 := "SA1XYZ"`.

## SIX — Índices

```
INDICE     Ordem (01, 02, ...)
CHAVE      Expressão da chave (FILIAL+COD)
DESCRICAO  Descrição
PROPRI     U (Único) ou S (Sistema)
F3         Aparece como consulta?
NICKNAME   Apelido para uso em ADVPL
SHOWPESQ   S/N — mostra no F4 (pesquisa)
```

Adicionar índice custom: `INDICE>=21` (TOTVS usa 01-20).

## SXA — Pastas (folders de cadastro)

Define abas e seu conteúdo no cadastro:

```
XA_ALIAS   Tabela (SA1)
XA_ORDEM   Sequência
XA_DESCRIC Descrição da aba (PT)
```

Campos pertencem à aba via `X3_FOLDER`.

## Funções utilitárias

| Função                       | Para que serve                          |
|------------------------------|-----------------------------------------|
| `GetSX3Cache(cCampo, cAtr)`  | Lê SX3 cacheado (rapido)                |
| `X3Descricao(cCampo)`        | Atalho para X3_DESCRIC                  |
| `X3Titulo(cCampo)`           | Atalho para X3_TITULO                   |
| `TamSX3(cCampo)`             | `{tamanho, decimal, tipo}`              |
| `Posicione(alias, ordem, key, cmpRet)` | Equivalente a DbSeek + retorno  |
| `GetMV(cParam, lOblig, xDef)`| Lê SX6                                  |
| `PutMV(cParam, xValor)`      | Grava SX6                               |
| `Pergunte(cGrp, lAsk)`       | Lê SX1, preenche `MV_PAR0X`             |
| `ExecAuto/MsExecAuto`        | Executa rotina padrão (usa SX3/SX7)     |
| `FwxFilial(alias)`           | Resolve filial                          |

## Anti-padrões

- Editar SX no banco direto (DBA) em vez de script via `PutSx3/PutSx7` → perde rastreio.
- Campo customer sem prefixo de cliente → colisão em upgrade.
- Gatilho com `X7_REGRA` complexa em vez de chamar `U_XYZxxx` → impossível debugar.
- Parâmetro `MV_` sem documentar (descrição vazia) → ninguém sabe o que faz.
- Esquecer `X3_NIVEL` ao criar campo confidencial → todos veem.
- Hardcode de campo `A1_XYZ` no fonte sem checar `FieldPos("A1_XYZ") > 0` → quebra se cliente não tiver campo.

## Referência profunda

Para detalhes completos (~1.6k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Esquema completo de **toda** SX (cada coluna documentada).
- Catálogo de `X3_PICTURE` (formatos `@!`, `@R`, `@E`, máscaras numéricas/data).
- Bitmap `X3_USADO` por contexto e como manipular.
- Fluxo de execução de gatilho (SX7) com encadeamento e short-circuit.
- Convenções para customização: campos reais × virtuais, contexto compartilhado × exclusivo.
- Procedimentos para upgrade-safe modifications.

## Comandos plugadvpl relacionados

- `/plugadvpl:tables <T>` — lista campos da tabela vinda do SX3 indexado.
- `/plugadvpl:param <MV_*>` — descobre uso de parâmetro no projeto.
- `/plugadvpl:find function PutSx3` — scripts de manipulação SX.
- A tabela `dictionary_sx` do índice cataloga campos do projeto.
