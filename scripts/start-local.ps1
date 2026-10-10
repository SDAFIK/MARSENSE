$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime = Join-Path $taskRoot 'data\runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$python = Join-Path $taskRoot '.venv\Scripts\python.exe'
$node = (Get-Command node -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath $python)) { throw 'Run the README setup commands first.' }
foreach ($port in @(8000, 3000)) {
  if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    throw "Port $port is already occupied. Keep the existing service or stop it explicitly."
  }
}
$api = Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'api.log') -RedirectStandardError (Join-Path $runtime 'api-error.log')
$taskPreviousDist = [Environment]::GetEnvironmentVariable('NEXT_DIST_DIR', 'Process')
try {
  $env:NEXT_DIST_DIR = '.next-local'
  $web = Start-Process -FilePath $node -ArgumentList @('node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1','--port','3000') -WorkingDirectory (Join-Path $taskRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'web.log') -RedirectStandardError (Join-Path $runtime 'web-error.log')
} finally {
  [Environment]::SetEnvironmentVariable('NEXT_DIST_DIR', $taskPreviousDist, 'Process')
}
@(@{id=$api.Id;startTicks=$api.StartTime.Ticks},@{id=$web.Id;startTicks=$web.StartTime.Ticks}) | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'local-processes.json')
Write-Output 'MARSENSE starting: http://127.0.0.1:3000/mission | API http://127.0.0.1:8000/docs'
