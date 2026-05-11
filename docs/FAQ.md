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
  15 knowledge skills, 4 agents, hook SessionStart. Faz Claude usar a CLI
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
