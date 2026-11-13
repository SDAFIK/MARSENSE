param(
    [Parameter(Mandatory=$true)][string]$BackupDirectory,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function NativeOK { if ($LASTEXITCODE -ne 0) { throw "Migration command failed ($LASTEXITCODE). Source remains unchanged." } }
$backup = (Resolve-Path -LiteralPath $BackupDirectory).Path
if (-not (Test-Path -LiteralPath "$backup\runtime\marsense.db" -PathType Leaf)) { throw 'Missing runtime database' }
if (-not (Test-Path -LiteralPath "$backup\users.json" -PathType Leaf)) { throw 'Missing private operator identity backup' }
# Use a disposable container, not the production service. The source is mounted read-only.
$image = 'marsense-cloud-migration:local'
docker build -f backend/Dockerfile.cloud -t $image .; NativeOK
$mount = "type=bind,source=$backup,target=/backup,readonly"
$code = "type=bind,source=$(Join-Path (Get-Location) 'scripts'),target=/app/scripts,readonly"
$common = @('run','--rm','--mount',$mount,'--mount',$code,'--entrypoint','python',$image,'-m','scripts.migrate_cloud','--runtime','/backup/runtime','--users','/backup/users.json')
docker @common; NativeOK
if (-not $Apply) { Write-Host 'Dry run completed; no database changes.'; exit 0 }
$secret = Read-Host 'Paste the MARSENSE PostgreSQL session-pooler URI (not the API URL)' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $env:MARSENSE_DATABASE_URL = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    docker run --rm --mount $mount --mount $code -e MARSENSE_DATABASE_URL --entrypoint python $image -m scripts.migrate_cloud --runtime /backup/runtime --users /backup/users.json --apply
    NativeOK
    docker run --rm --mount $mount --mount $code -e MARSENSE_DATABASE_URL --entrypoint python $image -m scripts.migrate_cloud --runtime /backup/runtime --users /backup/users.json --verify
    NativeOK
} finally {
    Remove-Item Env:MARSENSE_DATABASE_URL -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}
Write-Host 'Snapshot imported and independently verified. The live website was not switched.'
