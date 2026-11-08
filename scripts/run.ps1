param([switch]$Https, [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
$taskPython = Join-Path $taskRoot '.tools\python\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run scripts/setup.ps1 first.' }
New-Item -ItemType Directory -Path .local -Force | Out-Null
if (Test-Path -LiteralPath '.local\running.json') { throw 'A run record exists. Run scripts/stop.ps1 before starting another instance.' }
if (-not $SkipBuild) {
    Push-Location -LiteralPath frontend
    try { flutter build web --no-web-resources-cdn; if ($LASTEXITCODE -ne 0) { throw 'Flutter build failed' } } finally { Pop-Location }
}
$taskArguments = @('-m','scripts.serve')
if ($Https) { & $taskPython -m scripts.tls; $taskArguments += @('--https','--port','8443') }
$taskWorker = Start-Process -FilePath $taskPython -ArgumentList @('-m','backend.app.worker') -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput '.local\worker-output.log' -RedirectStandardError '.local\worker-error.log'
$taskApi = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput '.local\api-output.log' -RedirectStandardError '.local\api-error.log'
@{ worker = $taskWorker.Id; api = $taskApi.Id; executable = $taskPython } | ConvertTo-Json | Set-Content -LiteralPath '.local\running.json' -Encoding utf8
if ($Https) { Write-Output 'Open https://localhost:8443 after explicitly trusting the local CA, or use a trusted deployment certificate. Certificate validation must remain enabled.' }
else { Write-Output 'Open http://127.0.0.1:8000. This is the loopback development profile.' }
