# FAQ — Perguntas frequentes sobre plugadvpl

## O plugadvpl é compatível com qual versão do Protheus?

Foi testado com Protheus **R12** (12.1.x e superior). O parser foca em ADVPL clássico
(`.prw/.prx`) e TLPP moderno (`.tlpp`) — ambos suportados desde a R11. Versões anteriores
(R10) não foram testadas; provavelmente funcionam para o subset ADVPL clássico.

## Funciona com qual banco de dados?

O índice é **SQLite** local — não toca no banco do Protheus (Oracle/SQL Server/Postgres/DB2).
A análise é estática sobre os fontes `.prw/.tlpp`, não requer conexão com o ambiente.

## Roda em Linux/macOS ou só Windows?

Roda nos três (Windows, macOS, Linux). CI testa as 9 combinações 3 OS × 3 Python. O caso
mais comum é Windows porque devs Protheus usam quase sempre, mas Linux é totalmente
suportado — útil em CI/CD ou em VMs de análise.

## Posso indexar fontes sem ter o ambiente Protheus instalado?

**Sim.** O plugadvpl é puramente análise estática. Você precisa apenas dos fontes
`.prw/.tlpp/.prx` em uma pasta. Não precisa de AppServer, DBAccess, Smartclient, RPO,
nem nada do TOTVS.

## Os fontes do meu cliente vão para algum servidor externo?

**Não.** O plugadvpl roda 100% localmente. O índice (`.plugadvpl/index.db`) fica na
pasta do projeto. Nada é enviado para a internet. Modelo opcional `--no-content`
e `--redact-secrets` na ingestão para projetos especialmente sensíveis (ver
[`docs/limitations.md`](limitations.md)).

## Por que SQLite + FTS5 e não embeddings/vector DB?

Para a maioria das queries de análise ADVPL (quem chama X, quem grava em SA1, qual MV
é usado em Y), busca **estrutural** (SQL) e **lexical** (FTS5 com BM25 + trigram) é
mais barata, mais rápida e mais determinística que busca semântica. Embeddings entram
no roadmap experimental v0.5+, mas como opcional — o core continua estrutural.

## Por que não tree-sitter?

Não existe gramática `tree-sitter-advpl` pública (linguagem proprietária da TOTVS,
comunidade pequena). Construir uma do zero é estimado em 3-6 semanas, e o parser regex
atual cobre os 25 padrões mais relevantes de produção. Tree-sitter pode entrar em v1.0+
se justificar pelo custo de manutenção.

## Funciona em projetos com fontes em sub-pastas?

**Sim.** O `ingest` faz scan recursivo via `os.walk`. Estrutura típica de cliente
(MGFCOM/, MGFFAT/, MGFFIN/, etc.) é detectada automaticamente.

## E se meu projeto está num share de rede (SMB/CIFS)?

WAL do SQLite **não funciona** em network share. O plugadvpl detecta UNC paths
(`\\server\share`) automaticamente e usa `journal_mode=DELETE` como fallback (mais lento
mas seguro). Mapped drives Windows (Z:\) **não são detectados** automaticamente — se
estiver lento ou der `SQLITE_CORRUPT`, mova o projeto para disco local.

## Qual a diferença entre o plugin Claude Code e a CLI Python?

- **CLI Python (`plugadvpl`)**: o motor — parser, banco, queries. Funciona standalone
  no terminal.
- **Plugin Claude Code**: camada fina sobre a CLI — slash commands `/plugadvpl:*`,
  16 knowledge skills, 4 agents, hook SessionStart. Faz Claude usar a CLI
  proativamente em vez de Read direto no `.prw`.

A CLI é o que faz o trabalho. O plugin é o que faz Claude saber usar.

## O lint dá muito falso-positivo. Posso desligar regras específicas?

No MVP atual (v0.2), não há config de regras silenciadas — todas as 13 regras single-file
ativas reportam. v0.3 deve incluir `.plugadvpl/lint.toml` com `disabled_rules = [...]`.
Por enquanto, filtre por `--severity critical` para ver só o que importa muito.

## Posso contribuir? Onde reporto bugs?

- **Bugs/sugestões**: [GitHub Issues](https://github.com/JoniPraia/plugadvpl/issues)
- **Discussão geral / dúvidas / showcase**: [GitHub Discussions](https://github.com/JoniPraia/plugadvpl/discussions)
- **PRs**: muito bem-vindas. Veja [CONTRIBUTING.md](../CONTRIBUTING.md).

## Quem mantém o projeto?

[JoniPraia](https://github.com/JoniPraia) — desenvolvedor com background em Protheus
e ferramentas internas de análise. Open-source MIT, comunidade ADVPL é o público alvo.

---

## Troubleshooting de atualização

### `uv` não é reconhecido / sumiu do PATH

**Sintoma:** ao rodar `uv cache clean plugadvpl` ou `uv tool upgrade plugadvpl`
você recebe `O termo 'uv' não é reconhecido como nome de cmdlet` (PowerShell)
ou `bash: uv: command not found` (Linux/macOS).

**Causa:** o `uv` foi instalado em sessão anterior e o PATH desta sessão
não pegou; ou o `uv` foi removido. Comum depois de reinstalar o Windows,
trocar de máquina, ou usar o Python da Microsoft Store (que isola o PATH).

**Solução** — rodar o one-liner do plugadvpl de novo. Ele detecta `uv`
ausente, instala via `winget` (Windows) ou o installer oficial da Astral
(Linux/macOS) e refresca o PATH na sessão:

```powershell
# Windows
irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex
```

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh
```

Se mesmo assim o `uv` não aparecer no PATH desta sessão, **feche o terminal**,
abra outro novo, e rode o one-liner de novo. O Windows às vezes só propaga
PATH novo pra processos novos.

### `uv tool upgrade plugadvpl` diz "Nothing to do" mas PyPI tem versão nova

**Sintoma:** `https://pypi.org/project/plugadvpl/` mostra (por exemplo) `0.3.1`,
mas `uv tool upgrade plugadvpl` não faz nada — `plugadvpl version` continua
mostrando a versão antiga.

**Causa:** o `uv` tem cache agressivo de releases. `upgrade` não re-resolve
contra PyPI quando o cache já tem uma versão satisfazendo o specifier.

**Solução** — limpar cache da package + reinstalar forçado:

```powershell
uv cache clean plugadvpl
uv tool install plugadvpl --reinstall --force
plugadvpl version   # confere
```

### Atualizei o plugin mas slash command roda CLI antiga

**Sintoma:** depois de `/plugin marketplace update plugadvpl-marketplace`
o `plugin.json` mostra versão nova, mas algum bug que foi corrigido na CLI
nova continua acontecendo via slash command (`/plugadvpl:lint`, etc.).

**Causa:** cada SKILL.md do plugin invoca a CLI com versão pinada
(`uvx plugadvpl@X.Y.Z`). Se houver dessincronia entre o `plugin.json` e
o pin nos SKILL.md (release management), o plugin metadata avança mas o
slash command continua puxando CLI antiga.

**Solução imediata** — atualizar a CLI fora do uvx, instalando via
`uv tool` (que cria binário direto, sem o pin do uvx):

```powershell
uv cache clean plugadvpl
uv tool install plugadvpl --reinstall --force
```

Como o `plugadvpl.exe` no PATH é o que conta para usuários que rodam
direto, isso garante que pelo menos a invocação direta pega a versão
nova. Para corrigir o slash command também: aguardar a próxima release
do plugin (que re-sincroniza os pins) ou reportar o issue.

### `plugadvpl version` mostra `0.0.0+dev`

**Sintoma:** depois de instalar via `pip install -e .` ou `uv pip install -e .`
local, `plugadvpl version` retorna `0.0.0+dev`.

**Causa:** o pacote usa `hatch-vcs` — a versão real vem da tag git. Em checkout
sem tag aplicada (ex.: branch de feature, shallow clone), o fallback é `0.0.0+dev`.
Não é bug; só não é uma instalação "release". Para versão real, instale do PyPI:

```bash
uv tool install plugadvpl --force
```
