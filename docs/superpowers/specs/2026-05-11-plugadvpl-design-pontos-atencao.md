# Plugadvpl — Pontos de Atenção da Design Spec

| Item | Valor |
|---|---|
| Data da revisão | 2026-05-11 |
| Arquivo revisado | `docs/superpowers/specs/2026-05-11-plugadvpl-design.md` |
| Escopo | Crítica arquitetural, produto, distribuição, DX e riscos de implementação |
| Observação | Este arquivo não altera a spec original; registra pontos para decidir antes de implementar |

## Resumo executivo

A ideia é forte: um índice local, offline, barato em tokens e específico para ADVPL/TLPP resolve uma dor real de análise em projetos Protheus. O design também acerta ao separar plugin Claude Code de CLI Python, manter ingestão manual e tratar o índice como artefato local do projeto cliente.

O principal risco não é a tese do produto, mas o excesso de superfície no MVP. A spec tenta entregar ao mesmo tempo parser, FTS, 39 tabelas, 13 slash commands, 10 skills, 4 agents, hook, release PyPI, marketplace, lint e benchmark de performance. Isso aumenta muito a chance de uma v0.1 grande, frágil e difícil de validar. Para ficar "top", eu reduziria o MVP para uma experiência impecável em 4 fluxos: `init`, `ingest`, `arch/find/grep`, `callers/tables/param`, com validação pesada em path, encoding, FTS e token budget.

## Pontos críticos

### P0 — Identidade de arquivo não pode ser `arquivo` simples

**Problema:** o schema usa `fontes.arquivo TEXT PRIMARY KEY` e vários relacionamentos por `arquivo`. Em projetos Protheus é comum haver nomes repetidos em pastas diferentes, cópias de rotinas, branches de cliente, backup limpo vs custom, ou separação por módulo. Isso cria colisão silenciosa e perda de linhas no índice.

**Impacto:** `arch MATA010.prw`, `callers`, `tables` e `reindex` podem apontar para o arquivo errado. Esse é o tipo de erro que destrói confiança no plugin.

**Recomendação:** trocar a chave lógica para `arquivo_id` ou `relpath_norm`:

- `arquivo_id`: hash estável de caminho relativo normalizado, por exemplo `sha1(relpath_lower)`.
- `relpath`: caminho relativo original para exibição.
- `nome_arquivo`: basename só para filtros e busca.
- `root_id` ou `project_root_hash`: evita colisão se um DB for movido ou mesclar múltiplas raízes no futuro.

Adicionar `UNIQUE(relpath_norm)` e índices por `nome_arquivo`, `modulo`, `source_type`.

### P0 — A spec promete leitura por linha, mas o schema não guarda range dos chunks

**Problema:** os fluxos canônicos dependem de `Read FATA050.prw#L234-280`, e `find function` promete retornar linhas. Porém `fonte_chunks` só tem `id`, `arquivo`, `funcao`, `content`, `modulo`. Falta `linha_inicio`, `linha_fim`, `assinatura`, `tipo_simbolo`, `classe`, `namespace`.

**Impacto:** o plugin não consegue cumprir sua promessa central: consultar o índice antes de ler apenas o trecho necessário. Sem ranges confiáveis, o Claude volta a ler arquivo inteiro ou chutes de linha.

**Recomendação:** tornar `fonte_chunks` a tabela central de símbolos:

- `chunk_id INTEGER PRIMARY KEY`.
- `arquivo_id`, `symbol_name`, `symbol_norm`.
- `symbol_kind`: `user_function`, `static_function`, `method`, `class`, `ws_method`, `mvc_hook`, `header`.
- `linha_inicio`, `linha_fim`, `assinatura`.
- `parent_symbol_id` para métodos/classes quando aplicável.

`funcao_docs`, `chamadas_funcao`, `lint_findings` e `sql_embedado` devem referenciar `chunk_id` quando possível.

### P0 — `uvx plugadvpl` sem versão fixa pode quebrar plugin e CLI

**Problema:** os wrappers chamam `uvx plugadvpl ...`. A documentação do `uv` indica que `uvx` executa ferramentas em ambiente isolado/cacheado e, sem versão explícita, usa a versão disponível/cacheada conforme resolução. Isso pode deixar o plugin markdown v0.1 chamando uma CLI v0.2 com flags ou schema incompatíveis.

**Impacto:** usuários atualizam a CLI sem atualizar plugin, ou o inverso. O resultado é erro em slash command, migração surpresa ou comportamento diferente entre máquinas.

**Recomendação:** pin explícito nos commands:

```bash
uvx --from plugadvpl==0.1.0 plugadvpl status
```

Para desenvolvimento local:

```bash
uvx --from ./cli plugadvpl status
```

Além disso, o `plugadvpl status` deve validar compatibilidade entre `plugin_version`, `cli_version` e `schema_version`, retornando orientação clara de upgrade.

### P0 — O FTS precisa ser desenhado para busca de código, não só texto natural

**Problema:** `unicode61 remove_diacritics 2` é bom para palavras, mas código ADVPL contém padrões como `SA1->A1_COD`, `FWFormStruct`, `U_FOO`, `%xfilial%`, `::`, `->`, `&macro`, nomes com underscore e trechos SQL. A query FTS também pode falhar ou retornar pouco se o termo tiver pontuação não escapada.

**Impacto:** `grep "SA1->A1_COD"` ou `grep "%notDel%"` pode não achar o que o usuário espera. Se o grep parecer aleatório, o valor do índice cai muito.

**Recomendação:** separar modos de busca:

- `grep --fts <query>`: busca FTS com parser/escape seguro.
- `grep --literal <texto>`: busca literal por `LIKE`/scan limitado ou índice trigram.
- `grep --identifier <nome>`: normaliza identificadores ADVPL.

Testar explicitamente `RecLock`, `SA1->A1_COD`, `%xfilial%`, `FWExecView`, `U_ABC`, `StaticCall`, `::New`, `PARAMIXB[1]` e `BeginSQL`.

### P0 — Política de encoding está absoluta demais

**Problema:** a spec diz que todos os `.prw`, `.tlpp`, `.prx` são cp1252 e nunca UTF-8. Ao mesmo tempo, o schema tem campo `encoding` e os fixtures incluem `encoding_utf8.prw`. Essa contradição precisa virar política operacional.

**Impacto:** um editor ou comando pode corromper fonte real se gravar com encoding errado, especialmente em clientes com mistura histórica de CP1252, UTF-8 sem BOM, arquivos gerados e TLPP moderno.

**Recomendação:** usar política `preserve-by-default`:

- Detectar e armazenar encoding por arquivo.
- Em edição, preservar o encoding detectado.
- Se detection for incerta, bloquear escrita e pedir escolha explícita.
- `doctor` lista arquivos suspeitos e sugere normalização.
- `init` permite `--encoding-policy cp1252|preserve|utf8-warn`, com default conservador para CP1252 em projetos legado.

## Pontos altos

### P1 — MVP está grande demais para v0.1

**Problema:** 39 tabelas, 22 populadas, 17 vazias, 13 comandos listados, 10 skills, 4 agents, hook, release PyPI, marketplace e lint de 13 regras é uma v0.1 ambiciosa demais.

**Impacto:** o projeto pode gastar tempo em aparência de completude enquanto os fluxos principais ainda não estão sólidos.

**Recomendação:** redefinir o MVP como "índice confiável + consultas que economizam tokens":

1. `init`, `ingest`, `status`, `doctor`.
2. `arch`, `find`, `grep`, `callers`, `callees`, `tables`, `param`.
3. Uma skill principal `plugadvpl-index-usage`.
4. Um agent `advpl-analyzer`.
5. Sem tabelas vazias no DB público, ou tabelas vazias marcadas como `experimental` e sem promessa de contrato.

Deixar REST, HTTP outbound, 10 skills, 4 agents e lint avançado para versões menores incrementais.

### P1 — Há inconsistência de contagem nos comandos

**Problema:** o layout fala em 12 slash commands, os critérios de aceitação falam em 12 commands, mas a seção 6 lista 13 (`help` incluso).

**Impacto:** validação e documentação podem divergir logo no primeiro release.

**Recomendação:** decidir se `help` é skill/comando real ou apenas seção de README. Atualizar critério de aceitação para o número exato e gerar esse número automaticamente no `validate_plugin.py`.

### P1 — Claude Code mudou a ênfase de commands para skills

**Problema:** a documentação atual do Claude Code diz que custom commands foram mesclados ao modelo de skills; arquivos em `commands/` continuam funcionando, mas `skills/` é o caminho com recursos mais ricos para novos plugins. A spec ainda trata `commands/` como centro dos slash wrappers.

**Impacto:** o plugin pode nascer com uma organização compatível, mas menos alinhada à plataforma atual.

**Recomendação:** usar `skills/` para as experiências invocáveis principais e manter `commands/` apenas onde for realmente um wrapper fino. Validar localmente com:

```bash
claude --plugin-dir .
/reload-plugins
/plugadvpl:status
```

Também documentar o namespace esperado: o `name` do `plugin.json` precisa ser `plugadvpl` se a UX desejada é `/plugadvpl:arch`.

### P1 — Hooks precisam de contrato exato no `hooks.json`

**Problema:** a spec descreve `hooks/session-start`, mas não mostra o `hooks/hooks.json`. Na plataforma atual, o evento é `SessionStart` e hooks de plugin ficam em `hooks/hooks.json` ou inline no `plugin.json`.

**Impacto:** se o JSON usar nome errado, o hook simplesmente não roda. Se imprimir muito output, polui contexto ou passa do limite.

**Recomendação:** incluir o exemplo real:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start"
          }
        ]
      }
    ]
  }
}
```

O script deve retornar JSON com `hookSpecificOutput.additionalContext` apenas quando houver algo útil. Para "sem índice e sem fonte", saída vazia.

### P1 — Incremental precisa invalidar por versão de parser e lookups

**Problema:** a spec considera incremental por `mtime_ns`, mas o resultado do parser muda quando mudam regexes, lookups, schema, versão da CLI ou regras lint.

**Impacto:** usuário atualiza o plugin e continua com índice antigo, aparentemente válido, mas semanticamente defasado.

**Recomendação:** armazenar em `manifest.json` e `meta`:

- `parser_version`.
- `lookup_bundle_hash`.
- `schema_version`.
- `cli_version`.
- `ingest_config_hash`.
- `source_root`.

Se qualquer item mudar, `status --check-stale` deve marcar `needs_full_reingest: true`.

### P1 — Case-insensitive e normalização ADVPL precisam estar no schema

**Problema:** ADVPL costuma ser tratado de forma case-insensitive em nomes de funções, aliases, campos e parâmetros. O schema guarda nomes como texto livre e os índices não especificam collation/normalização.

**Impacto:** `callers FATA050`, `callers fata050` e `callers Fata050` podem divergir. Busca por tabela/campo também pode falhar.

**Recomendação:** para toda entidade consultável, manter duas colunas:

- `nome_display`: original.
- `nome_norm`: normalizado, por exemplo uppercase trim.

Indexar `nome_norm` e usar sempre nas consultas. Para SQLite, considerar `COLLATE NOCASE` onde fizer sentido, mas preferir normalização explícita para nomes técnicos.

### P1 — `INSERT OR REPLACE` é perigoso com FKs e FTS

**Problema:** a spec usa `INSERT OR REPLACE` como mecanismo geral de idempotência. Em SQLite, `REPLACE` pode apagar e recriar linhas, afetando FKs, rowids e sincronização com FTS.

**Impacto:** reindex de arquivo pode gerar órfãos, perder relações ou deixar FTS inconsistente se a ordem de operações falhar.

**Recomendação:** preferir transação por arquivo:

1. Resolver `arquivo_id`.
2. Deletar dependentes do arquivo.
3. Upsert controlado em `fontes` com `ON CONFLICT DO UPDATE`.
4. Inserir dependentes.
5. Reconstruir FTS daquele arquivo.

Adicionar teste que reindexa o mesmo arquivo 3 vezes e confirma contagens estáveis.

### P1 — FTS duplica conteúdo e pode crescer rápido

**Problema:** `fonte_chunks.content` armazena o texto e a FTS padrão também mantém cópia interna do conteúdo. A documentação do SQLite permite FTS external-content/contentless para reduzir espaço, mas exige sincronização cuidadosa.

**Impacto:** em 24k fontes, o DB pode ficar muito maior do que o necessário. Isso pesa em backup local, antivírus, sync corporativo e `doctor`.

**Recomendação:** avaliar:

- FTS external-content apontando para `fonte_chunks`.
- `contentless_delete=1` se o alvo for só busca e snippet próprio.
- `detail=column` ou `detail=none` apenas se não quebrar `snippet()` e ranking desejado.

Decidir com benchmark de tamanho e tempo em fixture real.

### P1 — Output para LLM precisa ter contrato de orçamento

**Problema:** `arch`, `grep`, `tables` e `callers` podem retornar listas enormes. A spec fala em economia de tokens, mas não define limite de linhas, truncamento, ordenação, score ou sugestão de refinamento.

**Impacto:** um único comando pode despejar milhares de linhas no contexto e anular a economia prometida.

**Recomendação:** definir contrato de saída:

- Todo comando tem `--limit`, `--offset`, `--compact`, `--json`.
- Default para Claude: máximo ~2000 caracteres ou N resultados.
- Mensagem padrão: "mais 132 resultados; refine com --table, --function, --path".
- `arch` mostra resumo, top símbolos, ranges e alertas, nunca corpo inteiro.
- `grep` ordena por `bm25`, arquivo e linha, com snippet curto.

## Pontos médios

### P2 — `status --check-stale` está ambíguo

**Problema:** em uma seção ele compara `mtime > indexed_at`; em outra, consulta `arquivo, mtime_ns` e compara com `os.stat`. A comparação correta deve ser por `mtime_ns` e `size_bytes`, com hash opcional para casos suspeitos.

**Recomendação:** definir:

- stale se arquivo não existe mais, é novo, `mtime_ns` difere ou `size_bytes` difere.
- `--deep` calcula hash.
- arquivos deletados removem índice no próximo `ingest --incremental`.

### P2 — WAL precisa de regra de checkpoint e versionamento

**Problema:** a spec permite versionar `.plugadvpl/index.db` opcionalmente. Em WAL, existem arquivos `index.db-wal` e `index.db-shm`, e separar esses arquivos pode causar perda de transações recentes ou inconsistência.

**Recomendação:** default `.gitignore` deve cobrir `.plugadvpl/`. Se houver modo versionável, oferecer:

```bash
plugadvpl export-index --checkpoint --vacuum
```

Ou converter temporariamente para journal mode adequado antes de empacotar. Também testar `locking_mode=EXCLUSIVE` em Windows, porque lock e antivírus costumam ser fontes reais de falha.

### P2 — Release workflow tem risco de commit em checkout de tag

**Problema:** o job de release propõe `git commit -am "release $tag" && git push` dentro de workflow disparado por tag `v*`. Em checkout de tag, o repositório geralmente está detached, e esse commit pode falhar ou ir para lugar inesperado.

**Recomendação:** fazer bump de marketplace e changelog antes de criar a tag, ou ter workflow separado que abre PR de release. O job de tag deve publicar artefatos, não modificar fonte.

### P2 — Dependência de caminhos locais reduz reprodutibilidade

**Problema:** a spec cita `D:/IA/Projetos/advpl-specialist-main`, caminhos locais de fixtures e parser de projeto privado. Isso é útil para o autor, mas não é reprodutível para contributors.

**Recomendação:** manter esses caminhos apenas como nota interna. Para o repo público, incluir fixtures sintéticas, snapshot de subset autorizado e script de geração. No `NOTICE`, creditar origem e licença sem depender de path local.

### P2 — Tabelas vazias criam contrato antes da hora

**Problema:** criar 17 tabelas vazias no MVP "para evitar migração" parece barato, mas transforma nomes e colunas em API pública. Se v0.2 precisar mudar o desenho, a compatibilidade já está comprometida.

**Recomendação:** ou criar essas tabelas só quando a feature entrar, ou marcá-las em `schema_experimental` e permitir migração breaking em `0.x`. O benefício de evitar migração é menor do que o custo de congelar design cedo.

### P2 — Falta história de erro para ambientes corporativos

**Problema:** o fluxo assume `uv` disponível, PyPI acessível e execução de hooks permitida. Muitos ambientes Protheus são Windows corporativo com proxy, antivírus, restrição de PowerShell/Bash e sem internet.

**Recomendação:** adicionar seção "Ambientes restritos":

- `plugadvpl doctor --env`.
- Mensagem clara para `uv não encontrado`.
- Instalação alternativa com wheel local.
- Cache/prewarm: `uv tool install plugadvpl==X`.
- Modo offline documentado.

### P2 — Segurança e privacidade precisam ser parte do produto

**Problema:** o índice local contém nomes de tabelas, regras de negócio, endpoints, SQL, parâmetros e possivelmente segredos literais. A spec foca em performance, mas não explicita proteção desse artefato.

**Recomendação:** incluir:

- `.plugadvpl/` no `.gitignore` por padrão.
- `doctor` alerta se `.plugadvpl/index.db` está versionado.
- Redação de snippets sensíveis opcional para URLs/tokens.
- `SECURITY.md` com política de disclosure.
- Opção `--no-content` para indexar metadados sem corpo de chunk em ambientes sensíveis.

## Melhorias para deixar a UX excelente

### 1. Uma primeira experiência muito curta

O primeiro uso deveria caber em 3 comandos:

```bash
/plugadvpl:init
/plugadvpl:ingest
/plugadvpl:arch FATA050.prw
```

Se algo falhar, a mensagem deve dizer exatamente o que fazer: instalar `uv`, rodar com versão fixa, liberar proxy, escolher encoding ou reindexar.

### 2. `arch` precisa ser o produto principal

`arch` deve ser tratado como tela inicial do fonte:

- Tipo e capabilities.
- Ranges por função/método.
- Tabelas lidas/escritas.
- Chamadas recebidas/enviadas.
- Parâmetros MV/SX1.
- SQL embutido.
- Alertas de lint críticos.
- Próximas consultas sugeridas.

Se `arch` for excelente, o Claude naturalmente evita `Read` inteiro.

### 3. Comandos devem retornar "próxima ação"

Exemplo:

```text
FATA050.prw
  Função principal: FATA050 L120-L310
  Writes: SC5, SC6
  Chamado por: MENU FAT, U_XYZ

Próximo passo recomendado:
  plugadvpl callers FATA050
  ou Read FATA050.prw#L120-180 se precisar do fluxo principal
```

Isso melhora a ergonomia tanto para humano quanto para agente.

### 4. Métrica de sucesso deve virar teste operacional

Além do token-budget manual, criar fixture de conversa com comandos esperados:

- Pergunta: "explique FATA050".
- Deve chamar `arch`, `callers`/`callees` e no máximo 1 `Read` com range.
- Falha se tentar ler `.prw` inteiro.

Mesmo que o teste seja semi-manual, ele protege a promessa central do produto.

## Ajustes recomendados na spec original

1. Trocar PKs baseadas em `arquivo` por `arquivo_id`/`relpath_norm`.
2. Adicionar ranges de linha e tipos de símbolo em `fonte_chunks`.
3. Pinning de CLI nos slash commands: `uvx --from plugadvpl==<versao> plugadvpl`.
4. Definir contrato de compatibilidade `plugin_version` x `cli_version` x `schema_version`.
5. Revisar `commands/` vs `skills/` com base no modelo atual do Claude Code.
6. Incluir `hooks/hooks.json` real com evento `SessionStart`.
7. Reduzir MVP ou separar "MVP obrigatório" de "MVP stretch".
8. Corrigir contagem de 12 vs 13 commands.
9. Definir política de encoding como preservação detectada, não absoluta.
10. Adicionar modo de busca literal/identificador além de FTS.
11. Definir limites de output por comando.
12. Adicionar estratégia para WAL/checkpoint/export.
13. Adicionar invalidação incremental por versão de parser/lookups.
14. Adicionar seção de segurança/privacy do índice.
15. Remover caminhos locais da especificação pública ou movê-los para nota interna.

## Fontes consultadas

- Claude Code — Create plugins: https://code.claude.com/docs/en/plugins
- Claude Code — Plugins reference: https://code.claude.com/docs/en/plugins-reference
- Claude Code — Skills: https://code.claude.com/docs/en/skills
- Claude Code — Hooks: https://code.claude.com/docs/en/hooks
- Claude Code — Plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- uv — Using tools / `uvx`: https://docs.astral.sh/uv/guides/tools/
- uv — Tool concepts and version behavior: https://docs.astral.sh/uv/concepts/tools/
- SQLite — FTS5: https://www.sqlite.org/fts5.html
- SQLite — WAL: https://www.sqlite.org/wal.html

