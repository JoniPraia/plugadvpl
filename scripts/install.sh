#!/usr/bin/env bash
# plugadvpl bootstrap installer for macOS / Linux
# Usage: curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh

set -e

echo ""
echo "  plugadvpl bootstrap installer (macOS/Linux)"
echo "  ============================================="
echo ""

# Step 1: Check/install uv
if ! command -v uv >/dev/null 2>&1; then
    echo "  [1/3] uv não encontrado, instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source env if available
    if [ -f "$HOME/.local/bin/env" ]; then
        . "$HOME/.local/bin/env"
    fi
    if [ -f "$HOME/.cargo/env" ]; then
        . "$HOME/.cargo/env"
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
else
    echo "  [1/3] uv já instalado: $(command -v uv)"
fi

# Verify
if ! command -v uv >/dev/null 2>&1; then
    echo ""
    echo "  ✗ uv ainda não está no PATH desta sessão."
    echo ""
    echo "  Solução:"
    echo "    1. Feche este terminal"
    echo "    2. Abra um novo terminal"
    echo "    3. Rode novamente: curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh"
    exit 1
fi
echo "  ✓ $(uv --version)"

# Step 2: Install plugadvpl
echo ""
echo "  [2/3] Instalando plugadvpl..."
uv tool install plugadvpl
export PATH="$HOME/.local/bin:$PATH"

if ! command -v plugadvpl >/dev/null 2>&1; then
    echo ""
    echo "  ⚠ plugadvpl instalado mas não está no PATH desta sessão."
    echo "    Feche este terminal e abra um novo."
    echo "    Depois rode:  plugadvpl version"
    exit 0
fi
echo "  ✓ $(plugadvpl version)"

# Step 3: Done
echo ""
echo "  [3/3] Pronto!"
echo ""
echo "  Próximos passos:"
echo "    cd <pasta-do-seu-projeto-Protheus>"
echo "    plugadvpl init"
echo "    plugadvpl ingest"
echo ""
echo "  Plugin Claude Code (opcional, para slash commands):"
echo "    /plugin marketplace add https://github.com/JoniPraia/plugadvpl.git"
echo "    /plugin install plugadvpl"
echo ""
echo "  Docs: https://github.com/JoniPraia/plugadvpl"
echo ""
