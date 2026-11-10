param([switch]$Https, [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
$taskPython = Join-Path $taskRoot '.tools\python\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run scripts/setup.ps1 first.' }
New-Item -ItemType Directory -Path .local -Force | Out-Null
$taskRecordPath = Join-Path $taskRoot '.local\running.json'
if (Test-Path -LiteralPath $taskRecordPath) {
    $taskPreviousRun = Get-Content -LiteralPath $taskRecordPath -Raw | ConvertFrom-Json
    $taskActiveProcesses = 0
    foreach ($taskRole in @('api', 'worker')) {
        $taskRecordedId = [int]$taskPreviousRun.$taskRole
        if ($taskRecordedId -le 0) { continue }
        $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$taskRecordedId" -ErrorAction Stop
        $taskModule = if ($taskRole -eq 'api') { 'scripts.serve' } else { 'backend.app.worker' }
        if ($null -ne $taskProcess -and $taskProcess.ExecutablePath -eq $taskPython -and $taskProcess.CommandLine -match ('-m\s+' + [regex]::Escape($taskModule) + '(\s|$)')) {
            $taskActiveProcesses++
        }
    }
    if ($taskActiveProcesses -eq 2) {
        $taskExistingUrl = $taskPreviousRun.url
        if (-not $taskExistingUrl) {
            $taskApiProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$taskPreviousRun.api)" -ErrorAction Stop
            $taskExistingUrl = if ($taskApiProcess.CommandLine -match '--https') { 'https://localhost:8443' } else { 'http://127.0.0.1:8000' }
        }
        Write-Output "Attendance is already running. Open $taskExistingUrl"
        Write-Output 'To restart or rebuild it, run scripts/stop.ps1 first.'
        return
    }
    if ($taskActiveProcesses -gt 0) {
        throw 'Only part of the previous attendance run is active. Run scripts/stop.ps1, then run this command again.'
    }
    Remove-Item -LiteralPath $taskRecordPath
    Write-Output 'Removed a stale run record; starting attendance.'
}
if (-not $SkipBuild) {
    Push-Location -LiteralPath frontend
    try { flutter build web --no-web-resources-cdn; if ($LASTEXITCODE -ne 0) { throw 'Flutter build failed' } } finally { Pop-Location }
}
$taskArguments = @('-m','scripts.serve')
if ($Https) { & $taskPython -m scripts.tls; $taskArguments += @('--https','--port','8443') }
$taskWorker = Start-Process -FilePath $taskPython -ArgumentList @('-m','backend.app.worker') -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput '.local\worker-output.log' -RedirectStandardError '.local\worker-error.log'
$taskApi = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput '.local\api-output.log' -RedirectStandardError '.local\api-error.log'
$taskUrl = if ($Https) { 'https://localhost:8443' } else { 'http://127.0.0.1:8000' }
@{ worker = $taskWorker.Id; api = $taskApi.Id; executable = $taskPython; url = $taskUrl } | ConvertTo-Json | Set-Content -LiteralPath $taskRecordPath -Encoding utf8
if ($Https) { Write-Output 'Open https://localhost:8443 after explicitly trusting the local CA, or use a trusted deployment certificate. Certificate validation must remain enabled.' }
else { Write-Output 'Open http://127.0.0.1:8000. This is the loopback development profile.' }
