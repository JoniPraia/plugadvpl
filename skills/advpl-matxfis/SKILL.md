---
description: Família MATXFIS (Faturamento/Fiscal Protheus) — geração de NF-e, SPED, ECF, REINF, integração SF2/SD2/SF3, PEs do módulo fiscal. Use quando o tema for nota fiscal, livro fiscal ou obrigação acessória.
---

# advpl-matxfis — Família fiscal Protheus

`MATXFIS` é a família de rotinas/funções fiscais do Protheus. Domina geração de **NF-e** (Nota Fiscal Eletrônica), **NFC-e**, **CT-e**, e integração com obrigações fiscais brasileiras: **SPED Fiscal**, **SPED Contribuições**, **ECF**, **EFD-REINF**, **GIA**, **DAPI**.

> **Nota de escopo**: MATXFIS é um dos módulos mais densos do Protheus (milhares de regras tributárias por UF/operação). Esta skill dá panorama + entry-points. Para deep-dive em regras específicas (cálculo de ICMS-ST, partilha de DIFAL, ajuste fiscal SPED registro C100/E110), invoque o agent **`advpl-specialist`** ou consulte a documentação oficial TDN.

## Quando usar

- Usuário menciona "nota fiscal", "NF-e", "SPED", "ECF", "REINF", "tributação", "ICMS", "IPI", "PIS/COFINS", "fiscal", "obrigação acessória".
- Edit em fontes com prefixo `MATA9*`, `MTA710*`, `SPED*`, `MATFXX*`, `MATXFIS*`.
- Tabelas envolvidas: SF2 (NF de saída), SF1 (NF de entrada), SD1/SD2 (itens), SF3 (livro fiscal), SF6 (acumulado fiscal), SFB, CDA/CDF (apuração SPED).
- Workflow de "rejeição da SEFAZ", "carta de correção", "inutilização".

## Panorama

Diagrama de fluxo simplificado de uma nota de saída:

```
Pedido de Venda (SC5/SC6)
       ↓ MATA460 — Documento de Saída
Nota Fiscal de Saída (SF2/SD2)
       ↓ MATA951/MATA952 — Transmissão NF-e
SEFAZ ← XML assinado → resposta (autorizada/rejeitada)
       ↓ MATA920 — Encerramento
Livro Fiscal (SF3) + Acumulados (SF6/CDA/CDF)
       ↓ SPED* — Obrigações acessórias
Arquivos SPED Fiscal / Contribuições / ECF / REINF
```

## Tabelas-chave

| Tabela | Conteúdo                                    | Quando aparece           |
|--------|---------------------------------------------|--------------------------|
| SF1    | Cabeçalho NF entrada                        | Compras / Faturamento    |
| SD1    | Itens NF entrada                            | Compras / Faturamento    |
| SF2    | Cabeçalho NF saída                          | Faturamento              |
| SD2    | Itens NF saída                              | Faturamento              |
| SF3    | Livro Fiscal (linha por imposto)            | Apuração                 |
| SF6    | Resumo fiscal por período                   | Apuração / GIA           |
| SFB    | Tipos de operação / TES (Tipo Entrada Saída)| Cadastro                 |
| SFK    | Memo fiscal NF                              | Detalhes                 |
| SFT    | Saídas — apuração                           | Apuração                 |
| CDA    | Apuração SPED Fiscal — registros            | SPED Fiscal              |
| CDF    | Apuração ICMS-ST                            | SPED Fiscal              |
| CDY    | EFD REINF                                   | REINF                    |
| SFC    | Carta de Correção                           | Pós-emissão              |
| SF8    | Inutilização de NF                          | Gestão de numeração      |

## Pontos de Entrada (PE) comuns

### NF Saída

| PE             | Quando                                                |
|----------------|-------------------------------------------------------|
| `M460FIM`      | Final da geração de saída em `MATA460`                |
| `MT100LOK`     | Validação na inclusão de NF                           |
| `SF2100I`      | Pós-inclusão NF saída                                 |
| `MA440PGN`     | Antes de gerar item SD2                               |
| `MAFIS440`     | Hook fiscal genérico                                  |
| `MT103CAB`     | Cabeçalho NF entrada — customizar cálculo             |
| `MA103NF`      | Pós-gravação NF entrada                               |

### NF-e (transmissão)

| PE             | Quando                                                |
|----------------|-------------------------------------------------------|
| `NFEXMLAUT`    | Ajuste no XML antes de assinar/transmitir             |
| `NFSXMLGER`    | NFS-e — geração do XML                                |
| `NFEXMLENV`    | Antes do envio à SEFAZ                                |
| `NFEREJ`       | Tratamento de rejeição                                |

### SPED

| PE             | Quando                                                |
|----------------|-------------------------------------------------------|
| `SPEDFIS`      | Customização SPED Fiscal — registros adicionais       |
| `SPEDPISCOFINS`| SPED Contribuições — registros                        |
| `MFC100`       | Ajuste registro C100 (NF entrada/saída)               |
| `MFC170`       | Ajuste registro C170 (itens)                          |
| `MFC190`       | Ajuste registro C190 (totalização por CST/CFOP/aliq)  |

Use `/plugadvpl:find function <PE>` para localizar implementações no projeto. O lookup `pontos_entrada_padrao` cataloga os mais comuns.

## TES — Tipo de Entrada/Saída

A **TES** (cadastrada em `SF4`) é o coração do cálculo tributário. Define:

- Se gera duplicata (`F4_DUPLIC`).
- Se atualiza estoque (`F4_ESTOQUE`).
- CFOP padrão.
- Bases e alíquotas de IPI, ICMS, PIS, COFINS.
- Tratamento de Substituição Tributária.

Funções utilitárias:

- `MaFisRef("operacao_fiscal", "tag", aDados)` — leitura/gravação de campos fiscais.
- `MaFisGet("tag")` — lê valor fiscal corrente do contexto.
- `MaFisEnd()` — encerra contexto fiscal.
- `MaFisIni()` — inicia contexto.

## Cálculo de impostos — quem é responsável

| Imposto      | Onde calcula                | Tabela campo            |
|--------------|------------------------------|-------------------------|
| ICMS         | `MaFisCalc`                  | SD2: D2_ICMSRET, D2_VALICM |
| ICMS-ST      | `MaFisCalc` + regras CDA     | D2_VALICM, D2_BRICMS    |
| IPI          | `MaFisCalc`                  | D2_VALIPI, D2_BASEIPI   |
| PIS/COFINS   | `MaFisCalc`                  | D2_VALIMP4, D2_VALIMP6  |
| DIFAL        | Regras partilha por UF       | CDA/CDF                 |
| FCP          | Vinculado a DIFAL e ST       | —                       |

Para customizar cálculo: **PE M460FIM**, **PE MA440PGN**, ou *override* via `MaFisRef`. Mexer direto em SD2 sem `MaFisRef` quebra a integridade fiscal.

## Anti-padrões

- Atualizar `SF2`/`SD2` direto com `RecLock` sem chamar `MaFisRef` → bases ficam zeradas, gera multa.
- Customizar SPED via `WriteFile` fora da rotina `SPEDFIS` → registros fora de ordem.
- Mudar CFOP na PE pós-gravação → não recalcula impostos.
- Ler `SF3` direto para apuração → use `MaFisCalc`/`MaFisRef` para garantir consistência.
- Hardcode de alíquota ICMS → use SF7 (alíquotas por UF) ou SFB (TES) — alíquotas mudam por legislação.
- Não tratar carta de correção (`SFC`) ao recalcular nota — pode revogar correção sem querer.

## Referência rápida

| Funcionalidade           | Função/rotina principal       |
|--------------------------|-------------------------------|
| Gerar NF saída           | `MATA460`                     |
| Cabeçalho NF entrada     | `MATA103`                     |
| Transmissão NF-e         | `MATA951`/`MATA952`           |
| Carta de correção        | `MATA935`                     |
| Inutilização             | `MATA938`                     |
| Apuração ICMS            | `MATA950`                     |
| SPED Fiscal              | `SPEDFISCAL` / `MATA951`      |
| SPED Contribuições       | `SPEDPISCOFINS`               |
| ECF                      | `CTBA901`/`CTBA902`           |
| REINF                    | `CTBR100` família             |
| Cálculo fiscal de item   | `MaFisCalc`/`MaFisRef`        |

## Quando escalar para `advpl-specialist`

Esta skill cobre o panorama. Acione o agente especialista quando o usuário pedir:

- Regra detalhada de DIFAL/FCP por par origem-destino.
- Diferenças entre regimes (Lucro Real × Presumido × Simples) em rotinas fiscais.
- Reconciliação fina SPED Fiscal × ECF × SF3.
- Diagnóstico de rejeição NF-e por código (rejeição 539, 627, etc.).
- Histórico de uma legislação específica (NT 2024.xxx).

## Comandos plugadvpl relacionados

- `/plugadvpl:tables SF2` (e SD2, SF3, SF6, CDA, CDF) — quem usa o quê.
- `/plugadvpl:find function MaFisCalc` — usos no projeto.
- `/plugadvpl:arch <fonte>` antes de tocar em qualquer rotina fiscal.
- `/plugadvpl:callers <PE_fiscal>` — onde a PE está implementada.

## Referência profunda

Para detalhes completos (~1.3k linhas), consulte [`reference.md`](reference.md) ao lado deste arquivo:

- Estrutura completa do contexto fiscal (`MaFisIni`/`MaFisEnd`/`MaFisRef`/`MaFisGet`/`MaFisCalc`).
- Tabela exaustiva de tags fiscais (`IT_VALMERC`, `IT_VALICM`, `IT_BASEIPI`, etc.) e quando atualizar cada uma.
- Regras de DIFAL/FCP/Partilha por UF e ajustes para emendas constitucionais (EC 87/2015).
- Mapeamento dos registros SPED Fiscal (C100/C170/C190/E110) ↔ tabelas Protheus (SF2/SD2/SF3/CDA).
- Cenários de NF complementar, NF de ajuste, denegação, inutilização, carta de correção.

## Exemplos práticos

Veja a pasta [`exemplos/`](exemplos/) ao lado deste SKILL.md para fonte real ADVPL de produção:

- `DAMDFE.prw` — impressão do Documento Auxiliar do Manifesto Eletrônico (MDF-e) com tratamento de contingência, layout estruturado em `oDamdfe:SetPaperSize`/`SetMargin` e parsing do XML MDF-e via `XMLXFUN.CH`.
