# Registers a Windows Scheduled Task to run the health check daily
param(
    [string]$Time = "08:00"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $ScriptDir '.venv/Scripts/python.exe'
if (-Not (Test-Path $python)) { $python = 'python' }

$Action = New-ScheduledTaskAction -Execute $python -Argument "`"$ScriptDir\health_check_finanzas.py`""
$Trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date $Time)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

$TaskName = "HealthCheckFinanzasSupabase"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings
Write-Host "Tarea programada '$TaskName' creada para las $Time" -ForegroundColor Green
