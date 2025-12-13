# One-click bulk sync for finanzas -> Supabase
# Usage: double-click or run in PowerShell

function Load-DotEnv {
    param([string]$Path)
    if (-Not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^[#;]') { return }
        if ($_ -notmatch '=') { return }
        $parts = $_ -split '=',2
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if ($name) { Set-Item -Path "env:$name" -Value $value }
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Load .env if present
$envPath = Join-Path $ScriptDir '.env'
Load-DotEnv -Path $envPath

# Fallback defaults
if (-not $env:POS_DB_PATH) { $env:POS_DB_PATH = 'pos_cremeria.db' }

if (-not $env:SUPABASE_URL -or -not $env:SUPABASE_SERVICE_ROLE_KEY) {
    Write-Host "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el entorno o .env" -ForegroundColor Red
    Write-Host "Define en .env, por ejemplo:" -ForegroundColor Yellow
    Write-Host "SUPABASE_URL=https://TU_PROYECTO.supabase.co" -ForegroundColor Yellow
    Write-Host "SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key" -ForegroundColor Yellow
    exit 1
}

Write-Host "Usando DB local: $env:POS_DB_PATH" -ForegroundColor Cyan
Write-Host "Sincronizando a Supabase: $env:SUPABASE_URL" -ForegroundColor Cyan

# Prefer local venv python if available
$python = Join-Path $ScriptDir '.venv/Scripts/python.exe'
if (-Not (Test-Path $python)) { $python = 'python' }

$cmd = "$python sync_finanzas_bulk.py"
Write-Host "Ejecutando: $cmd" -ForegroundColor Green

& $python sync_finanzas_bulk.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Sync falló" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Sync completada" -ForegroundColor Green
