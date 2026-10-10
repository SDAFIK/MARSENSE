$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$state = Join-Path $taskRoot 'data\runtime\local-processes.json'
if (-not (Test-Path -LiteralPath $state)) { Write-Output 'No launcher-managed processes recorded.'; exit }
foreach ($record in (Get-Content -LiteralPath $state -Raw | ConvertFrom-Json)) {
  $taskProcess = Get-Process -Id $record.id -ErrorAction SilentlyContinue
  if ($taskProcess -and $taskProcess.StartTime.Ticks -eq $record.startTicks) {
    # Next.js starts a child server; stop only this verified launcher's process tree.
    & taskkill.exe /PID $taskProcess.Id /T /F | Out-Null
  }
}
Remove-Item -LiteralPath $state
Write-Output 'Local MARSENSE processes stopped. Mission history is preserved.'
