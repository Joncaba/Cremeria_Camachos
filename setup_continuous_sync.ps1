# Registers a Windows Scheduled Task to run sync_all_continuous.py every 5 minutes
param(
    [string]$Workspace = "C:\Users\jo_na\Documents\Cre",
    [string]$PythonExe = "$Workspace\.venv\Scripts\python.exe",
    [string]$TaskName = "Cremeria-ContinuousSync",
    [int]$IntervalMinutes = 5
)

$scriptPath = Join-Path $Workspace "sync_all_continuous.py"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Python not found at $PythonExe" -ForegroundColor Yellow
}

if (-not (Test-Path $scriptPath)) {
    Write-Error "Missing sync script at $scriptPath"
    exit 1
}

# Build action command
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument $scriptPath -WorkingDirectory $Workspace

# Run indefinitely every N minutes (duration: 365 days)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365)

# Use current user
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Environment vars from .env are loaded by the script via python-dotenv
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal

# Replace existing
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
} catch {}

Register-ScheduledTask -TaskName $TaskName -InputObject $task | Out-Null
Write-Host "Scheduled task '$TaskName' registered to run every $IntervalMinutes minutes." -ForegroundColor Green
