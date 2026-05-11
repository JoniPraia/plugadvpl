---
description: Bootstrap completo do plugadvpl. Detecta uv, instala se faltar, faz init + ingest no projeto atual. Use no primeiro uso ou quando quiser reconfigurar.
disable-model-invocation: true
allowed-tools: [Bash]
---

# /plugadvpl:setup

Setup automático: detecta uv, instala se necessário, e roda init + ingest no projeto atual.

## Execução

Você (Claude) deve rodar os passos abaixo via Bash, sequencialmente, NA PASTA ATUAL do projeto (cwd do usuário):

### Passo 1: Verificar uv

```bash
if ! command -v uv >/dev/null 2>&1 && ! command -v uvx >/dev/null 2>&1; then
  echo "uv não instalado. Para instalar:"
  case "$(uname -s 2>/dev/null || echo Windows)" in
    Linux*|Darwin*)
      echo "  curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh"
      ;;
    *)
      echo "  irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex"
      ;;
  esac
  echo ""
  echo "Após instalar, feche e abra um terminal novo, então rode /plugadvpl:setup de novo."
  exit 0
fi
```

### Passo 2: Garantir plugadvpl instalado

```bash
if ! command -v plugadvpl >/dev/null 2>&1; then
  uv tool install plugadvpl
fi
plugadvpl version
```

### Passo 3: Init + Ingest no diretório atual

```bash
plugadvpl init
plugadvpl ingest
plugadvpl status
```

## Resultado esperado

Ao final, o diretório atual terá:
- `.plugadvpl/index.db` (SQLite com índice dos fontes)
- `CLAUDE.md` com fragmento orientando Claude a consultar o índice antes de ler `.prw` cru
- `.plugadvpl/` adicionado ao `.gitignore`

Depois disso, comandos como `/plugadvpl:arch`, `/plugadvpl:tables`, `/plugadvpl:callers` ficam disponíveis.

## Próximos passos sugeridos

- `/plugadvpl:status` — ver contagens do índice
- `/plugadvpl:arch <arquivo.prw>` — visão arquitetural de um fonte
- `/plugadvpl:tables SA1` — quem usa a tabela SA1
- `/plugadvpl:param MV_LOCALIZA` — quem usa esse parâmetro
- `/plugadvpl:lint` — findings de qualidade
