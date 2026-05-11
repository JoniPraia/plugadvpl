---
description: Política de encoding em fontes ADVPL/TLPP — cp1252 para .prw clássico, utf-8 para .tlpp moderno, preserve-by-default. Use antes de Edit/Write em .prw/.prx/.tlpp.
---

# advpl-encoding — cp1252 / utf-8 preserve-by-default

Fontes ADVPL/TLPP em projetos Protheus reais misturam dois encodings:

- **`.prw` / `.prx` clássicos** → **cp1252 (Windows-1252)**.
- **`.tlpp` moderno** → **UTF-8** é suportado e usado em código novo (TOTVS recomenda).

Em clientes grandes essas duas extensões coexistem no mesmo repositório. Algumas codebases legadas chegam a ter `.prw` em UTF-8 (raro, mas existe). **A regra é: preserve o encoding detectado, nunca normalize por conta própria.**

## Quando usar

- Antes de qualquer `Edit` ou `Write` em `.prw`, `.prx`, `.tlpp`.
- Quando o usuário menciona "acento errado", "ç", "ã", "caractere quebrado", "mojibake", "encoding".
- Quando ler um arquivo via `Read` e ver `Ã§` ou `Ã£` no output (sinal de cp1252 lido como utf-8).
- Antes de rodar `/plugadvpl:ingest` em base nova (verifique a política).

## Caracteres que tipicamente quebram

Ao salvar cp1252 como UTF-8 (ou vice-versa) sem decodificar corretamente, estes caracteres viram lixo:

| Char cp1252 | Byte cp1252 | Lido como UTF-8 (mojibake)   |
|-------------|-------------|------------------------------|
| `ç`         | `0xE7`      | `Ã§`                         |
| `ã`         | `0xE3`      | `Ã£`                         |
| `á`         | `0xE1`      | `Ã¡`                         |
| `é`         | `0xE9`      | `Ã©`                         |
| `ó`         | `0xF3`      | `Ã³`                         |
| `Á`         | `0xC1`      | `Ã`                          |
| `'` (curly) | `0x92`      | `’` virou byte inválido      |
| `°`         | `0xB0`      | `Â°`                         |

Comentários `// Atualizacao` viram `// AtualizaÃ§Ã£o` quando lidos errado. **Pior**: o compilador AppServer rejeita o arquivo, ou compila e quebra strings em runtime.

## Como o parser plugadvpl detecta

Algoritmo (rápido, validado em ampla base de fontes ADVPL):

1. **Fast-path**: tenta decodificar como cp1252 → sucesso? grava `encoding='cp1252'` em `sources.encoding`.
2. **Fallback**: se cp1252 falhar (caracteres não-mapeáveis no header), tenta UTF-8.
3. **Última cartada**: `chardet[:4096]` (sample do início do arquivo) para detecção heurística.
4. **`.tlpp`** começa direto pela tentativa UTF-8 (extensão sugere TLPP moderno), depois cai para cp1252.

A coluna `encoding` da tabela `sources` registra o resultado. **Consulte ela antes de editar.**

## Política `--encoding-policy`

`/plugadvpl:ingest` aceita uma das três políticas:

- **`preserve`** (default) — armazena o encoding detectado por fonte, não impõe regra global. **Recomendado.**
- **`cp1252`** — assume cp1252 para `.prw/.prx`; emite warning para `.tlpp` UTF-8 detectado.
- **`utf8-warn`** — emite warning para qualquer fonte que NÃO seja UTF-8 (útil em migração ativa).

Para edição feita por Claude, **preserve sempre**.

## Workflow correto antes de Edit

1. Consulte `/plugadvpl:status` ou rode `SELECT encoding FROM sources WHERE arquivo='X.prw'`.
2. Se Claude vê mojibake no `Read`, **não é o arquivo que está corrompido** — é a IDE/tool lendo errado. Confirme com `/plugadvpl:doctor`.
3. Ao editar, mantenha bytes literais: não cole texto de outra fonte UTF-8 num arquivo cp1252 sem converter.
4. Para arquivos novos: siga a extensão. `.prw` novo → cp1252; `.tlpp` novo → UTF-8.

## Exemplo — comentário com acento

`.prw` (cp1252, byte `E7` para `ç`):

```advpl
// Função de validação do código do cliente
User Function ValCli()
    Local cMsg := "Operação concluída com sucesso"
Return .T.
```

Os bytes do source: `// Fun\xe7\xe3o de valida\xe7\xe3o`. Se Claude leu como UTF-8, vai ver `// FunÃ§Ã£o`. **Não “conserte” isso editando** — o arquivo está correto, o problema é o decoder.

## Anti-padrões

- "Vou normalizar tudo pra UTF-8 para evitar problemas" → **NÃO**. Quebra compilação no AppServer clássico e desalinha includes `#include "TOTVS.CH"`.
- Salvar `.prw` com BOM UTF-8 (`EF BB BF`) → AppServer rejeita.
- Editar `.tlpp` em cp1252 só porque o resto do projeto é cp1252 → perde recurso natural do TLPP.
- Confiar em "abrir e olhar" — use `file -i` (Linux/WSL) ou `/plugadvpl:doctor` para encoding real.

## Referência rápida

| Extensão  | Encoding esperado | Alternativa aceita | Política Claude            |
|-----------|-------------------|--------------------|----------------------------|
| `.prw`    | cp1252            | (raro) utf-8       | preserve                   |
| `.prx`    | cp1252            | —                  | preserve                   |
| `.tlpp`   | utf-8             | cp1252 (legado)    | preserve                   |
| `.ch`     | cp1252            | utf-8              | preserve                   |
| `.th`     | utf-8             | —                  | preserve                   |

## Comandos plugadvpl relacionados

- `/plugadvpl:doctor` — checa encoding real de cada fonte ingesto.
- `/plugadvpl:ingest --encoding-policy {cp1252|preserve|utf8-warn}` — controla detecção.
- `/plugadvpl:status` — mostra distribuição de encodings na base.
