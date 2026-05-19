# Bogamatic SAC installer for Windows
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1 <SAC_USERNAME> <SAC_PASSWORD>

param(
    [Parameter(Mandatory = $true)][string]$SacUsername,
    [Parameter(Mandatory = $true)][string]$SacPassword
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=== Bogamatic SAC - Instalador ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install uv if needed
Write-Host "[1/3] Verificando uv..." -ForegroundColor White

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

if (-not (Get-Command "uvx" -ErrorAction SilentlyContinue)) {
    Write-Host "  Instalando uv..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    if (-not (Get-Command "uvx" -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: No se pudo instalar uv." -ForegroundColor Red
        Write-Host "  Instalalo manualmente: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "  OK: uv instalado" -ForegroundColor Green

# Step 2: Detect Claude Desktop config path
Write-Host "[2/3] Buscando Claude Desktop..." -ForegroundColor White

$ConfigDir = $null

# Microsoft Store version
$StorePackage = Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA "Packages") -Filter "Claude_*" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if ($StorePackage) {
    $candidate = Join-Path $StorePackage.FullName "LocalCache\Roaming\Claude"
    if (Test-Path $candidate) {
        $ConfigDir = $candidate
        Write-Host "  Detectada instalacion Microsoft Store" -ForegroundColor Green
    }
}

# Standard install
if (-not $ConfigDir) {
    $candidate = Join-Path $env:APPDATA "Claude"
    if (Test-Path $candidate) {
        $ConfigDir = $candidate
        Write-Host "  Detectada instalacion estandar" -ForegroundColor Green
    }
}

if (-not $ConfigDir) {
    Write-Host ""
    Write-Host "ERROR: No se encontro Claude Desktop instalado." -ForegroundColor Red
    Write-Host "  Instala Claude Desktop, abrilo una vez, y volve a ejecutar este script." -ForegroundColor Yellow
    exit 1
}

$ConfigFile = Join-Path $ConfigDir "claude_desktop_config.json"
Write-Host "  Config: $ConfigFile" -ForegroundColor Gray

# Step 3: Write config
Write-Host "[3/3] Configurando Claude Desktop..." -ForegroundColor White

if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}

$newServer = @{
    command = "uvx"
    args = @("--python", "3.13", "bogamatic-sac-mcp")
    env = @{
        SAC_USERNAME = $SacUsername
        SAC_PASSWORD = $SacPassword
    }
}

# Try to preserve existing config
$existingJson = $null
if (Test-Path $ConfigFile) {
    $raw = Get-Content $ConfigFile -Raw -ErrorAction SilentlyContinue
    if ($raw -and $raw.Trim().Length -gt 2) {
        try {
            $existingJson = $raw | ConvertFrom-Json
        } catch {
            $existingJson = $null
        }
    }
}

if ($existingJson -and $existingJson.mcpServers) {
    # Add or overwrite only the bogamatic-sac key
    $existingJson.mcpServers | Add-Member -NotePropertyName "bogamatic-sac" -NotePropertyValue ([PSCustomObject]$newServer) -Force
} elseif ($existingJson) {
    $existingJson | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{ "bogamatic-sac" = [PSCustomObject]$newServer }) -Force
} else {
    $existingJson = [PSCustomObject]@{ mcpServers = [PSCustomObject]@{ "bogamatic-sac" = [PSCustomObject]$newServer } }
}

$jsonOut = $existingJson | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($ConfigFile, $jsonOut, [System.Text.UTF8Encoding]::new($false))

Write-Host "  OK: Config escrito en $ConfigFile" -ForegroundColor Green

Write-Host ""
Write-Host "=== Instalacion completa ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Reinicia Claude Desktop para activar Bogamatic SAC." -ForegroundColor Yellow
Write-Host ""
