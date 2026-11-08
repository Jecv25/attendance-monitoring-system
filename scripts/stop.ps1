$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskRecordPath = Join-Path $taskRoot '.local\running.json'
if (-not (Test-Path -LiteralPath $taskRecordPath)) { Write-Output 'No owned server record exists.'; return }
$taskRecord = Get-Content -LiteralPath $taskRecordPath -Raw | ConvertFrom-Json
foreach ($taskProcessId in @($taskRecord.api,$taskRecord.worker)) {
    $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$taskProcessId"
    if ($null -ne $taskProcess -and $taskProcess.ExecutablePath -eq $taskRecord.executable -and $taskProcess.CommandLine -match '(scripts\.serve|backend\.app\.worker)') {
        Stop-Process -Id $taskProcessId
    }
}
Remove-Item -LiteralPath $taskRecordPath
Write-Output 'Stopped the recorded attendance processes.'
