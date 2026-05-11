#!/usr/bin/env pwsh
# plugadvpl bootstrap installer for Windows
# Usage: irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex

$ErrorActionPreference = 'Stop'

Write-Host ""
Write-Host "  plugadvpl bootstrap installer (Windows)" -ForegroundColor Cyan
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check/install uv
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    Write-Host "  [1/3] uv não encontrado, instalando..." -ForegroundColor Yellow

    # Try winget first
    $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetAvailable) {
        winget install --id=astral-sh.uv --silent --accept-source-agreements --accept-package-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  winget falhou, usando installer oficial..." -ForegroundColor Yellow
            iex (irm https://astral.sh/uv/install.ps1)
        }
    } else {
        Write-Host "  winget não disponível, usando installer oficial..." -ForegroundColor Yellow
        iex (irm https://astral.sh/uv/install.ps1)
    }

    # Refresh PATH for current session
    $machinePath = [System.Environment]::GetEnvironmentVariable('Path','Machine')
    $userPath = [System.Environment]::GetEnvironmentVariable('Path','User')
    $env:PATH = "$machinePath;$userPath"
    # Add common uv install locations explicitly
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:PATH"
} else {
    Write-Host "  [1/3] uv já instalado: $($uvCmd.Source)" -ForegroundColor Green
}

# Verify uv works now
$uvVersion = & uv --version 2>$null
if (-not $uvVersion) {
    Write-Host ""
    Write-Host "  ✗ uv ainda não está no PATH desta sessão." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Solução:" -ForegroundColor Yellow
    Write-Host "    1. Feche este terminal"
    Write-Host "    2. Abra um novo terminal"
    Write-Host "    3. Rode este script de novo:"
    Write-Host "       irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex"
    exit 1
}
Write-Host "  ✓ $uvVersion" -ForegroundColor Green

# Step 2: Install plugadvpl globally via uv tool install
Write-Host ""
Write-Host "  [2/3] Instalando plugadvpl..." -ForegroundColor Yellow
& uv tool install plugadvpl 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ uv tool install falhou" -ForegroundColor Red
    exit 1
}

# Refresh PATH again (uv tool install adds to ~/.local/bin)
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"

# Verify plugadvpl works
$plugVersion = & plugadvpl version 2>$null
if (-not $plugVersion) {
    Write-Host ""
    Write-Host "  ⚠ plugadvpl instalado mas não está no PATH desta sessão." -ForegroundColor Yellow
    Write-Host "    Feche este terminal e abra um novo." -ForegroundColor Yellow
    Write-Host "    Depois rode:  plugadvpl version"
    exit 0
}
Write-Host "  ✓ $plugVersion" -ForegroundColor Green

# Step 3: Done
Write-Host ""
Write-Host "  [3/3] Pronto!" -ForegroundColor Green
Write-Host ""
Write-Host "  Próximos passos:" -ForegroundColor Cyan
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
