param([switch]$BrowserTests)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
$taskPython = Join-Path $taskRoot '.tools\python\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    New-Item -ItemType Directory -Path '.tools\python' -Force | Out-Null
    Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-embed-amd64.zip' -OutFile '.tools\python-runtime.zip' -UseBasicParsing
    Expand-Archive -LiteralPath '.tools\python-runtime.zip' -DestinationPath '.tools\python' -Force
    Set-Content -LiteralPath '.tools\python\python313._pth' -Value "python313.zip`n.`n..\..`nimport site" -Encoding ascii
    Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '.tools\get-pip.py' -UseBasicParsing
    & $taskPython '.tools\get-pip.py' --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw 'Python bootstrap failed' }
}
& $taskPython -m pip install -r backend/requirements.lock.txt --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $taskPython -m scripts.manage configure
& $taskPython -m scripts.manage seed
Push-Location -LiteralPath frontend
try { flutter pub get; if ($LASTEXITCODE -ne 0) { throw 'Flutter dependency installation failed' } } finally { Pop-Location }
if ($BrowserTests) { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Browser tooling installation failed' } }
Write-Output 'Setup complete. Usernames: admin, teacher, supervisor. Read the generated passwords locally in .env.'
