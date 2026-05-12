---
description: Política de encoding em fontes ADVPL/TLPP — cp1252 (Windows-1252) padrão para .prw/.prx clássico, utf-8 para .tlpp moderno, preserve-by-default. Funções ADVPL EncodeUTF8/DecodeUTF8/STRICONV pra conversão runtime. Use antes de Edit/Write em .prw/.prx/.tlpp, ou quando ver mojibake ("Ã§", "Ã£") em qualquer output.
---

# advpl-encoding — cp1252 / utf-8 preserve-by-default

Fontes ADVPL/TLPP em projetos Protheus reais misturam dois encodings:

- **`.prw` / `.prx` clássicos** → **cp1252 (Windows-1252)** — padrão histórico, herdado do Clipper.
- **`.tlpp` moderno** → **UTF-8** é suportado e recomendado pela TOTVS para código novo.

Em clientes grandes essas duas extensões coexistem no mesmo repositório. Algumas codebases legadas chegam a ter `.prw` em UTF-8 (raro, mas existe). **A regra é: preserve o encoding detectado, nunca normalize por conta própria.**

## Quando usar

- Antes de qualquer `Edit` ou `Write` em `.prw`, `.prx`, `.tlpp`.
- Quando o usuário menciona "acento errado", "ç", "ã", "caractere quebrado", "mojibake", "encoding".
- Quando ler um arquivo via `Read` e ver `Ã§` ou `Ã£` no output (sinal de cp1252 lido como utf-8).
- Antes de rodar `/plugadvpl:ingest` em base nova (verifique a política).
- Em REST/WebService onde XML/JSON entra UTF-8 e o fonte é cp1252.
- Em scripts auxiliares (instalador `.ps1`, `.sh`) que vão ser lidos por terminal cp1252.

## Caracteres que tipicamente quebram (mojibake)

Ao salvar cp1252 como UTF-8 (ou vice-versa) sem decodificar corretamente, estes caracteres viram lixo:

| Char cp1252 | Byte cp1252 | Lido como UTF-8 (mojibake)   |
|-------------|-------------|------------------------------|
| `ç`         | `0xE7`      | `Ã§`                         |
| `ã`         | `0xE3`      | `Ã£`                         |
| `á`         | `0xE1`      | `Ã¡`                         |
| `é`         | `0xE9`      | `Ã©`                         |
| `ó`         | `0xF3`      | `Ã³`                         |
| `Á`         | `0xC1`      | `Ã`                          |
| `°`         | `0xB0`      | `Â°`                         |
| `—` (em-dash) | `0x97`    | `â`                          |
| `↔` (arrow) | (não existe cp1252) | crash UnicodeEncodeError |

Comentários `// Atualizacao` viram `// AtualizaÃ§Ã£o` quando lidos errado. **Pior**: o compilador AppServer rejeita o arquivo, ou compila e quebra strings em runtime.

> **Char fora do cp1252 = crash**: `↔` (U+2194), `→` (U+2192), box-drawing (`─`, `│`), emojis. Não existem em cp1252 → quando Python/AppServer tenta encodar `cp1252`, dá `UnicodeEncodeError: 'charmap' codec can't encode character`. Foi exatamente o bug da v0.3.0 do plugadvpl no `--help` em Windows PS 5.1.

## Como o parser plugadvpl detecta

Algoritmo real (parser.py, validado em ampla base de fontes ADVPL):

1. **ASCII-only** → reporta `"cp1252"` (default Protheus; ASCII é subset).
2. **UTF-8 strict válido** (tem multi-byte chars que decodam como UTF-8) → `"utf-8"`.
3. **cp1252 fast-path** (99% dos fontes Protheus com chars latinos) → `"cp1252"`.
4. **`chardet[:4096]`** (sample do início do arquivo) → heurística, último fallback.
5. **`latin-1`** se chardet falhar.

> Detalhe técnico: a ordem **UTF-8 strict antes de cp1252** é proposital. cp1252 só tem 5 bytes indefinidos (0x81/8D/8F/90/9D); todos os outros valores 0x00-0xFF são "válidos" em cp1252. Então tentar cp1252 primeiro misdecodaria silenciosamente bytes UTF-8 multi-byte como sequência de chars latinos. UTF-8 strict rejeita bytes cp1252 típicos (`ã` = 0xE3 sozinho não forma sequência UTF-8 válida).

> A extensão **não** influencia a ordem — `.tlpp` segue o mesmo algoritmo. Mas como `.tlpp` na prática tem mais chars multi-byte, o passo 2 acerta primeiro.

A coluna `encoding` da tabela **`fontes`** (não "sources") registra o resultado. Consulte antes de editar:

```sql
SELECT arquivo, encoding FROM fontes WHERE arquivo = 'XXX.prw';
```

Ou via CLI: `/plugadvpl:doctor` mostra distribuição de encoding na base.

## Política `--encoding-policy` no `ingest`

`/plugadvpl:ingest` aceita uma das três políticas:

- **`preserve`** (default) — armazena o encoding detectado por fonte, não impõe regra global. **Recomendado.**
- **`cp1252`** — assume cp1252 para `.prw/.prx`; emite warning para `.tlpp` UTF-8 detectado.
- **`utf8-warn`** — emite warning para qualquer fonte que NÃO seja UTF-8 (útil em migração ativa).

Para edição feita por Claude, **preserve sempre**.

## Funções ADVPL de conversão runtime

Quando o código precisa misturar encodings em runtime (ex: REST que recebe JSON UTF-8 num fonte cp1252):

| Função                        | Direção            | Quando usar                                     |
|-------------------------------|--------------------|--------------------------------------------------|
| `EncodeUTF8(cStr)`            | cp1252 → UTF-8     | Antes de enviar string ADVPL pra REST/JSON      |
| `DecodeUTF8(cStr)`            | UTF-8 → cp1252     | Após receber body UTF-8 de REST/JSON            |
| `STRICONV(cStr, nCodepage)`   | cp1252 ↔ outras     | Conversões cross-codepage (sistemas externos)   |

```advpl
// Recebendo body REST UTF-8 e gravando em fonte cp1252
WSMETHOD POST cadastraCliente WSRECEIVE cBody WSSERVICE zClientes
    Local oJson := Nil
    Local cBody := DecodeUTF8(Self:GetContent())   // converte UTF-8 → cp1252

    FwJsonDeserialize(cBody, @oJson)
    RecLock("SA1", .T.)
    SA1->A1_NOME := AllTrim(oJson:nome)   // string cp1252, OK pra gravar
    MsUnlock()
Return .T.

// Enviando resposta JSON UTF-8 a partir de dados cp1252
WSMETHOD GET listaClientes WSSERVICE zClientes
    Local cResp := '{"nome":"' + AllTrim(SA1->A1_NOME) + '"}'
    Self:SetResponse(EncodeUTF8(cResp))           // converte cp1252 → UTF-8
Return .T.
```

> **Quirk:** `EncodeUTF8()` com char inválido **retorna NIL** e loga warning no `console.log` do AppServer. Sempre verifique retorno em rotinas críticas.

XML é exceção: o parser XML do ADVPL **internamente** já faz UTF-8 ↔ cp1252 — você lê chars como `á`, `ç` direto no `XmlElem:Text` sem conversão manual.

## Display correto no console do AppServer (Windows)

`ConOut`/`FwLogMsg` no console.log aparece com mojibake se o terminal estiver em codepage diferente:

```bat
:: appserver.bat — antes de subir
chcp 1252
TotvsAppServer.exe -console
```

Pra Linux/WSL: locale `pt_BR.iso-8859-1` ou converter o log com `iconv` na hora de ler.

## Workflow correto antes de Edit

1. **Consulte o encoding indexado**: `/plugadvpl:doctor` ou `SELECT encoding FROM fontes WHERE arquivo='X.prw'`.
2. **Se Claude vê mojibake no `Read`**, **não é o arquivo que está corrompido** — é a tool/IDE lendo errado. Confirme com `/plugadvpl:doctor`.
3. **Ao editar**, mantenha bytes literais: não cole texto de outra fonte UTF-8 num arquivo cp1252 sem converter.
4. **Para arquivos novos**: siga a extensão. `.prw` novo → cp1252; `.tlpp` novo → UTF-8.
5. **Scripts auxiliares** (`.ps1`, `.sh`, `.bat`) que rodam em terminal cp1252 → **ASCII-only é mais portável**. UTF-8 BOM nesses scripts atrapalha mais que ajuda (causa parse errors em PS 5.1).

## Exemplo — comentário com acento

`.prw` (cp1252, byte `0xE7` para `ç`):

```advpl
// Funcao de validacao do codigo do cliente
User Function ValCli()
    Local cMsg := "Operacao concluida com sucesso"
Return .T.
```

> Como exibição em markdown, vou usar comentário sem acentos pra clareza. No fonte real, `ç`, `ã`, `é` estão lá literalmente como bytes cp1252 — Claude/IDE precisa decodar como cp1252 pra ler corretamente.

Os bytes do source: `// Fun\xe7\xe3o de valida\xe7\xe3o`. Se Claude leu como UTF-8, vai ver `// FunÃ§Ã£o`. **Não "conserte" isso editando** — o arquivo está correto, o problema é o decoder.

## Anti-padrões

- **"Vou normalizar tudo pra UTF-8 para evitar problemas"** → **NÃO**. Quebra compilação no AppServer clássico, desalinha includes `#include "TOTVS.CH"`, dispara `EncodeUTF8()` falhas em runtime.
- **Salvar `.prw` com BOM UTF-8** (`EF BB BF`) → AppServer rejeita.
- **Salvar `.ps1`/`.sh`/`.bat` com BOM UTF-8** → terminal PS 5.1 não reconhece, parser quebra (bug real do install.ps1 v0.3.1).
- **Editar `.tlpp` em cp1252** só porque o resto do projeto é cp1252 → perde recurso natural do TLPP (chars Unicode, emoji em strings, etc.).
- **Confiar em "abrir e olhar"** — use `file -i` (Linux/WSL) ou `/plugadvpl:doctor` para encoding real.
- **Concatenar string cp1252 com retorno de REST sem `DecodeUTF8`** → byte sequences inválidos no SQL.
- **Acento em identificador** (`cNomeCliênte`) — compilador aceita mas quebra deserialização cross-encoding (CSV, REST). Veja `[[advpl-fundamentals]]`.
- **Char fora de cp1252** (setas `↔`/`→`, emojis, box-drawing) em string de fonte `.prw` → `UnicodeEncodeError` em runtime quando AppServer tenta exibir.

## Referência rápida

| Extensão  | Encoding esperado | Alternativa aceita | Política Claude            |
|-----------|-------------------|--------------------|----------------------------|
| `.prw`    | cp1252            | (raro) utf-8       | preserve                   |
| `.prx`    | cp1252            | —                  | preserve                   |
| `.tlpp`   | utf-8             | cp1252 (legado)    | preserve                   |
| `.ch`     | cp1252            | utf-8              | preserve                   |
| `.th`     | utf-8             | —                  | preserve                   |
| `.ps1`/`.sh` (instaladores) | ASCII-only OU UTF-8 sem BOM | — | preserve, ASCII se possível |
| Body REST/JSON | utf-8         | —                  | `EncodeUTF8`/`DecodeUTF8`  |

## Cross-references com outras skills

- `[[advpl-fundamentals]]` — char ASCII-only em identificadores; `.prw` (cp1252, 10 chars) vs `.tlpp` (utf-8, 250 chars).
- `[[advpl-webservice]]` — REST/JSON precisa `EncodeUTF8`/`DecodeUTF8` ao entrar/sair do fonte cp1252.
- `[[advpl-web]]` — Webex/HTML serve em UTF-8; conversão é obrigatória.
- `[[advpl-debugging]]` — mojibake é sintoma frequente; primeiro passo é `/plugadvpl:doctor`.
- `[[advpl-code-review]]` — não há regra de lint específica de encoding ainda (gap conhecido).
- `[[plugadvpl-index-usage]]` — `/plugadvpl:doctor` checa encoding real de cada fonte ingesto.

## Comandos plugadvpl relacionados

- `/plugadvpl:doctor` — checa encoding real de cada fonte ingesto.
- `/plugadvpl:ingest --encoding-policy {cp1252|preserve|utf8-warn}` — controla detecção.
- `/plugadvpl:status` — mostra distribuição de encodings na base.
- Query direta: `SELECT encoding, COUNT(*) FROM fontes GROUP BY encoding`.

## Sources

- [O que é CODEPAGE e ENCODING - Tudo em AdvPL](https://siga0984.wordpress.com/2019/07/21/o-que-e-codepage-e-encoding-parte-02/)
- [EncodeUTF8 - TDN](https://tdn.totvs.com/display/tec/EncodeUTF8)
- [Aplicando codificação UTF-8 com DecodeUTF8 e EncodeUTF8 - Maratona AdvPL TL++ 138](https://terminaldeinformacao.com/2023/12/24/aplicando-a-codificacao-utf-8-com-decodeutf8-e-encodeutf8-maratona-advpl-e-tl-138/)
- [Acentuação FWRest AdvPL - DevForum TOTVS](https://devforum.totvs.com.br/527-acentuacao-fwrest-advpl)
- [Como mudar codificação padrão no VSCode - Terminal de Informação](https://terminaldeinformacao.com/2020/12/03/como-mudar-a-codificacao-padrao-no-vscode/)
- [Tag CP-1252 - Tudo em AdvPL](https://siga0984.wordpress.com/tag/cp-1252/)
- [Tag UTF-8 - Tudo em AdvPL](https://siga0984.wordpress.com/tag/utf-8/)
