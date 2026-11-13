param(
    [Parameter(Mandatory=$true)][string]$ExpectedCommit,
    [Parameter(Mandatory=$true)][string]$ProductionOrigin
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$prod = $ProductionOrigin.TrimEnd('/')
$uri = [Uri]$prod
if ($uri.Scheme -ne 'https' -or $uri.AbsolutePath -ne '/' -or $uri.Query -or $uri.Fragment -or $uri.UserInfo -or $uri.Port -ne 443) { throw 'Use the existing HTTPS production origin with no path or credentials.' }
$show = "$($uri.Scheme)://$($uri.Host):8443"
function NativeOK { if ($LASTEXITCODE -ne 0) { throw "Native command failed ($LASTEXITCODE). No volume removal is authorized." } }
function Check($condition, $message) { if (-not $condition) { throw $message }; Write-Host "PASS: $message" }
$head = (git rev-parse HEAD).Trim(); NativeOK
Check ($ExpectedCommit -match '^[a-f0-9]{40}$' -and $head -eq $ExpectedCommit) 'Exact approved source commit'
$dirty = git status --porcelain; NativeOK
Check (-not $dirty) 'Clean source tree'
$health = Invoke-RestMethod "$prod/api/health"
Check ($health.status -eq 'ok' -and $health.environment -eq 'production') 'Production health'
$info = (docker inspect marsense-free-api-1 | ConvertFrom-Json)[0]; NativeOK
Check (@($info.Mounts | Where-Object { $_.Name -eq 'marsense-free_mission-data' -and $_.Destination -eq '/app/data/runtime' }).Count -eq 1) 'Original production volume'
$private = Join-Path $env:USERPROFILE 'MARSENSE-Showcase-Private'
New-Item -ItemType Directory -Force $private | Out-Null
$env:MARSENSE_SHOWCASE_USERS_FILE = Join-Path $private 'users.json'
$env:MARSENSE_SHOWCASE_ORIGINS = ConvertTo-Json -InputObject @($show) -Compress
if (-not (Test-Path $env:MARSENSE_SHOWCASE_USERS_FILE)) {
    $script = @'
import getpass, json, pathlib, uuid, sys
sys.path.insert(0, "/app")
from backend.auth import password_hash
p = pathlib.Path('/private/users.json')
if p.exists(): raise SystemExit('Refusing to overwrite existing identity')
a = getpass.getpass('New showcase password (15+ characters): ')
if len(a) < 15 or a != getpass.getpass('Repeat password: '): raise SystemExit('Invalid password or mismatch')
p.write_text(json.dumps([dict(id=str(uuid.uuid4()), username='showcase-admin', name='Showcase Administrator', role='ADMIN', password_hash=password_hash(a))]))
print('Showcase identity created')
'@
    $scriptPath = Join-Path $private ('provision-' + [Guid]::NewGuid().ToString('N') + '.py')
    [IO.File]::WriteAllText($scriptPath, $script, [Text.UTF8Encoding]::new($false))
    try {
        $file = Split-Path -Leaf $scriptPath
        docker run --rm -it --user 0 --network none --mount "type=bind,source=$private,target=/private" --entrypoint python marsense-free-api "/private/$file"
        NativeOK
    } finally { Remove-Item -LiteralPath $scriptPath -ErrorAction SilentlyContinue }
}
docker compose -p marsense-showcase -f compose.showcase.yaml config --quiet; NativeOK
docker compose -p marsense-showcase -f compose.showcase.yaml up -d --build --wait; NativeOK
$si = (docker inspect marsense-showcase-api-1 | ConvertFrom-Json)[0]; NativeOK
Check (@($si.Mounts | Where-Object { $_.Name -eq 'marsense-showcase_showcase-data' -and $_.Destination -eq '/app/data/runtime' }).Count -eq 1) 'Separate showcase volume'
Check (@($si.Mounts | Where-Object { $_.Name -eq 'marsense-free_mission-data' }).Count -eq 0) 'No production volume in showcase'
$sh = Invoke-RestMethod 'http://127.0.0.1:8081/api/health'
Check ($sh.environment -eq 'showcase' -and $sh.status -eq 'ok') 'Local showcase healthy'
tailscale funnel status; NativeOK
if ((Read-Host 'Confirm HTTPS 8443 is unused or already points to 8081; type YES to enable showcase') -ne 'YES') { throw 'Funnel unchanged' }
tailscale funnel --bg --https=8443 8081; NativeOK
$sh = Invoke-RestMethod "$show/api/health"
Check ($sh.environment -eq 'showcase' -and $sh.status -eq 'ok') 'Public HTTPS showcase healthy'
$state = Invoke-RestMethod "$show/api/auth/session"
Check ($state.environment -eq 'showcase' -and $state.replay_enabled -and $state.required) 'Showcase authenticated replay enabled'
$state = Invoke-RestMethod "$prod/api/auth/session"
Check ($state.environment -eq 'production' -and -not $state.replay_enabled -and $state.required) 'Production replay remains disabled'
Write-Host "SHOWCASE_URL=$show"
