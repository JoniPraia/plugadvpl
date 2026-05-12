#!/usr/bin/env pwsh
# plugadvpl bootstrap installer for Windows
# Usage: irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex
#
# This file is intentionally ASCII-only (no accents, no BOM) so it parses
# correctly under both `.\install.ps1` (local PS 5.1) and `irm ... | iex`
# (network pipe). A UTF-8 BOM here would survive Invoke-RestMethod and turn
# the shebang into an unrecognized command in PowerShell's parser.

$ErrorActionPreference = 'Stop'

# PS 5.1 compat: force TLS 1.2 (legacy .NET Framework default is TLS 1.0/1.1
# and fails against modern hosts like astral.sh). PS 7+ already negotiates 1.2/1.3.
try {
    [Net.ServicePointManager]::SecurityProtocol =
        [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {
    # Silently ignore - TLS already set or already on PS 7+.
}

Write-Host ""
Write-Host "  plugadvpl bootstrap installer (Windows)" -ForegroundColor Cyan
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check/install uv
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    Write-Host "  [1/3] uv nao encontrado, instalando..." -ForegroundColor Yellow

    # Try winget first
    $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetAvailable) {
        # PS 5.1: 2>&1 em exe nativo embrulha stderr como NativeCommandError; usa *>$null.
        winget install --id=astral-sh.uv --silent --accept-source-agreements --accept-package-agreements *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  winget falhou, usando installer oficial..." -ForegroundColor Yellow
            iex (irm https://astral.sh/uv/install.ps1)
        }
    } else {
        Write-Host "  winget nao disponivel, usando installer oficial..." -ForegroundColor Yellow
        iex (irm https://astral.sh/uv/install.ps1)
    }

    # Refresh PATH for current session
    $machinePath = [System.Environment]::GetEnvironmentVariable('Path','Machine')
    $userPath = [System.Environment]::GetEnvironmentVariable('Path','User')
    $env:PATH = "$machinePath;$userPath"
    # Add common uv install locations explicitly
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:PATH"
} else {
    Write-Host "  [1/3] uv ja instalado: $($uvCmd.Source)" -ForegroundColor Green
}

# Verify uv works now (sem 2>$null pra evitar NativeCommandError em PS 5.1)
$uvVersion = $null
try { $uvVersion = & uv --version } catch { $uvVersion = $null }
if (-not $uvVersion) {
    Write-Host ""
    Write-Host "  [X] uv ainda nao esta no PATH desta sessao." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Solucao:" -ForegroundColor Yellow
    Write-Host "    1. Feche este terminal"
    Write-Host "    2. Abra um novo terminal"
    Write-Host "    3. Rode este script de novo:"
    Write-Host "       irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex"
    exit 1
}
Write-Host "  [OK] $uvVersion" -ForegroundColor Green

# Step 2: Install plugadvpl globally via uv tool install
Write-Host ""
Write-Host "  [2/3] Instalando plugadvpl..." -ForegroundColor Yellow
Write-Host "        (na primeira instalacao pode levar 1-3 min: uv baixa Python managed +" -ForegroundColor DarkGray
Write-Host "         deps. Sem barra de progresso ate terminar - paciencia.)" -ForegroundColor DarkGray
& uv tool install plugadvpl
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [X] uv tool install falhou" -ForegroundColor Red
    exit 1
}

# Refresh PATH again (uv tool install adds to ~/.local/bin)
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"

# Verify plugadvpl works
$plugVersion = $null
try { $plugVersion = & plugadvpl version } catch { $plugVersion = $null }
if (-not $plugVersion) {
    Write-Host ""
    Write-Host "  [!] plugadvpl instalado mas nao esta no PATH desta sessao." -ForegroundColor Yellow
    Write-Host "      Feche este terminal e abra um novo." -ForegroundColor Yellow
    Write-Host "      Depois rode:  plugadvpl version"
    exit 0
}
Write-Host "  [OK] $plugVersion" -ForegroundColor Green

# Step 3: Done
Write-Host ""
Write-Host "  [3/3] Pronto!" -ForegroundColor Green
Write-Host ""
Write-Host "  Proximos passos:" -ForegroundColor Cyan
Write-Host "    cd <pasta-do-seu-projeto-Protheus>"
Write-Host "    plugadvpl init"
Write-Host "    plugadvpl ingest"
Write-Host ""
Write-Host "  Plugin Claude Code (opcional, para slash commands):"
Write-Host "    /plugin marketplace add https://github.com/JoniPraia/plugadvpl.git"
Write-Host "    /plugin install plugadvpl"
Write-Host ""
Write-Host "  Docs: https://github.com/JoniPraia/plugadvpl"
Write-Host ""
