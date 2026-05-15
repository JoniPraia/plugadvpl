# build-pdf.ps1 — gera linkedin-v04-carousel.pdf a partir do HTML
# Usa Microsoft Edge (ou Chrome) em modo headless. Funciona offline.

$ErrorActionPreference = "Continue"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$htmlPath = Join-Path $here "linkedin-v04-carousel.html"
$pdfPath  = Join-Path $here "linkedin-v04-carousel.pdf"

if (-not (Test-Path $htmlPath)) {
    Write-Error "HTML nao encontrado: $htmlPath"
    exit 1
}

# Tenta Edge primeiro, depois Chrome
$candidates = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

$browser = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) {
    Write-Error "Nem Edge nem Chrome encontrado."
    exit 1
}

Write-Output "Browser: $browser"
Write-Output "HTML:    $htmlPath"
Write-Output "PDF:     $pdfPath"

$uri = "file:///" + ($htmlPath -replace '\\', '/')

# --headless=new respeita CSS @page size (1080x1350)
# --no-pdf-header-footer remove cabecalho/rodape padrao
$browserArgs = @(
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--no-margins",
    "--print-to-pdf=$pdfPath",
    $uri
)

# stderr fica visivel mas nao quebra o script (Edge faz log ruidoso normal)
& $browser @browserArgs | Out-Null
Start-Sleep -Milliseconds 500

if (Test-Path $pdfPath) {
    $size = (Get-Item $pdfPath).Length
    Write-Output ""
    Write-Output "OK. PDF gerado ($([math]::Round($size/1KB, 1)) KB)"
    Write-Output "   $pdfPath"
} else {
    Write-Error "Falha ao gerar PDF."
    exit 1
}
