param(
    [Parameter(Mandatory=$true)][string]$ExpectedCommit,
    [Parameter(Mandatory=$true)][string]$StagingOrigin,
    [string]$ProductionOrigin = 'https://desktop-sdfik.tailf13324.ts.net',
    [string]$FinalOrigin = 'https://redscape-eight.vercel.app'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function NativeOK { if ($LASTEXITCODE -ne 0) { throw "Native command failed ($LASTEXITCODE). Stop; no data deletion authorized." } }
function Check($ok,$msg) { if (-not $ok) { throw $msg }; Write-Host "PASS: $msg" }
foreach ($origin in @($StagingOrigin,$ProductionOrigin,$FinalOrigin)) {
    $u=[Uri]$origin
    Check ($u.Scheme -eq 'https' -and $u.AbsolutePath -eq '/' -and -not $u.Query -and -not $u.Fragment -and -not $u.UserInfo) 'HTTPS origin'
}
Check ($ExpectedCommit -match '^[a-f0-9]{40}$') 'Full tested commit required'
$head=(git rev-parse HEAD).Trim(); NativeOK
Check ($head -eq $ExpectedCommit) 'Exact tested checkout'
$dirty=git status --porcelain; NativeOK
Check (-not $dirty) 'Clean checkout'
$api='marsense-free-api-1'
$info=(docker inspect $api | ConvertFrom-Json)[0]; NativeOK
Check (@($info.Mounts | Where-Object {$_.Name -eq 'marsense-free_mission-data' -and $_.Destination -eq '/app/data/runtime'}).Count -eq 1) 'Existing mission volume'
$identity=@($info.Mounts | Where-Object {$_.Destination -eq '/run/secrets/marsense-users.json'})
Check ($identity.Count -eq 1) 'Existing private identity mount'
$env:MARSENSE_USERS_FILE=$identity[0].Source
if ($env:MARSENSE_USERS_FILE -match '^/run/desktop/mnt/host/([a-zA-Z])/(.*)$') {
    $env:MARSENSE_USERS_FILE="$($Matches[1]):\$($Matches[2] -replace '/', '\')"
}
Check (Test-Path -LiteralPath $env:MARSENSE_USERS_FILE -PathType Leaf) 'Private identity file accessible'
$entry=$info.Config.Env | Where-Object {$_ -like 'MARSENSE_CORS_ORIGINS=*'} | Select-Object -First 1
$origins=@()
if ($entry) { $origins=@($entry.Substring('MARSENSE_CORS_ORIGINS='.Length) | ConvertFrom-Json) }
$origins=@($origins + @($ProductionOrigin.TrimEnd('/'),$StagingOrigin.TrimEnd('/'),$FinalOrigin.TrimEnd('/')) | Sort-Object -Unique)
$env:MARSENSE_CORS_ORIGINS=ConvertTo-Json -InputObject $origins -Compress
docker compose -p marsense-free -f compose.funnel.yaml config --quiet; NativeOK
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$backup=Join-Path $env:USERPROFILE "MARSENSE-Backups\release-$stamp"
New-Item -ItemType Directory -Force "$backup\runtime" | Out-Null
$oldApi=(docker inspect $api --format '{{.Image}}').Trim(); NativeOK
$oldWeb=(docker inspect marsense-free-web-1 --format '{{.Image}}').Trim(); NativeOK
docker tag $oldApi "marsense-api:rollback-$stamp"; NativeOK
docker tag $oldWeb "marsense-web:rollback-$stamp"; NativeOK
Write-Host "Building candidate before interruption; rollback images tagged $stamp"
docker compose -p marsense-free -f compose.funnel.yaml build api web; NativeOK
if ((Read-Host 'Close other mission sessions. Type UPGRADE to back up and switch the existing host') -ne 'UPGRADE') { throw 'Upgrade not authorized' }
docker stop $api; NativeOK
try {
    docker cp "$($api):/app/data/runtime/." "$backup\runtime"; NativeOK
    Copy-Item -LiteralPath $env:MARSENSE_USERS_FILE -Destination "$backup\users.json"
} catch { docker start $api | Out-Null; throw }
# The old API remains stopped until switch; failures in the rehearsal restart it.
try {
Check (Test-Path "$backup\runtime\marsense.db") 'Backup database exists'
$restore="marsense-restore-$stamp"
docker volume create $restore | Out-Null; NativeOK
$copy=@'
import shutil,sqlite3,pathlib
shutil.copytree('/backup/runtime','/restore',dirs_exist_ok=True)
p=pathlib.Path('/restore/marsense.db')
assert p.is_file()
with sqlite3.connect(p) as db:
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    print('RESTORE INTEGRITY OK',db.execute('SELECT COUNT(*) FROM entities').fetchone()[0])
'@
$copy | docker run --rm -i --user 0 --network none --mount "type=bind,source=$backup,target=/backup,readonly" --mount "type=volume,source=$restore,target=/restore" --entrypoint python $oldApi -; NativeOK
$restoreName="marsense-restore-check-$stamp"
$restoreEnv=Join-Path $backup 'restore.env'
@('MARSENSE_ENVIRONMENT=production','MARSENSE_AUTH_USERS_FILE=/run/secrets/marsense-users.json','MARSENSE_CORS_ORIGINS=["https://restore.invalid"]','MARSENSE_DATABASE_URL=sqlite:////app/data/runtime/marsense.db') | Set-Content -LiteralPath $restoreEnv -Encoding ascii
try {
    docker run -d --name $restoreName --network none --user 0 --mount "type=volume,source=$restore,target=/app/data/runtime" --mount "type=bind,source=$backup\users.json,target=/run/secrets/marsense-users.json,readonly" --env-file "$restoreEnv" $oldApi | Out-Null; NativeOK
    $healthy=$false
    for($i=0;$i -lt 30;$i++){
        docker exec $restoreName python -c "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200" 2>$null
        if($LASTEXITCODE -eq 0){$healthy=$true;break}
        Start-Sleep -Seconds 2
    }
    Check $healthy 'Restored copy boots original application in isolated container'
} finally { docker rm -f $restoreName 2>$null | Out-Null }
} catch {
    docker start $api | Out-Null
    throw
}
# Do not delete the rehearsal volume or backup. Quiesce writes during switch.
try {
    docker compose -p marsense-free -f compose.funnel.yaml up -d --no-build --force-recreate --wait; NativeOK
} catch {
    Write-Warning "Activation failed. Backup: $backup. Rollback tags: marsense-api:rollback-$stamp and marsense-web:rollback-$stamp. Do not restore or delete the live volume automatically."
    throw
}
$live=(docker inspect $api | ConvertFrom-Json)[0]; NativeOK
Check (@($live.Mounts | Where-Object {$_.Name -eq 'marsense-free_mission-data' -and $_.Destination -eq '/app/data/runtime'}).Count -eq 1) 'Original live volume retained'
$state=Invoke-RestMethod "$ProductionOrigin/api/auth/session"
Check ($state.environment -eq 'production' -and $state.required -and -not $state.replay_enabled -and $state.registration_enabled) 'Updated production authentication'
$compare=@'
import sqlite3,json
a=sqlite3.connect('file:/backup/runtime/marsense.db?mode=ro',uri=True)
b=sqlite3.connect('file:/app/data/runtime/marsense.db?mode=ro',uri=True)
def rows(c):
    return {(k,i):json.loads(p) for i,k,p in c.execute('SELECT id,kind,payload FROM entities')}
old,new=rows(a),rows(b)
assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
missing=set(old)-set(new)
changed=[k for k in old if k in new and k[0]!='AuthSession' and old[k]!=new[k]]
print('Original',len(old),'Current',len(new),'Missing',len(missing),'Changed non-session',len(changed))
assert not missing and not changed
'@
# Compare a disposable online snapshot, never a read-only WAL mount.
$tmp="/tmp/marsense-release-$stamp.db"
docker exec $api python -c "import sqlite3; a=sqlite3.connect('file:/app/data/runtime/marsense.db?mode=ro',uri=True); b=sqlite3.connect('$tmp'); a.backup(b); b.close(); a.close()"; NativeOK
docker cp "$($api):$tmp" "$backup\after.db"; NativeOK
docker exec $api rm $tmp; NativeOK
$compare=$compare.Replace('file:/app/data/runtime/marsense.db?mode=ro','file:/backup/after.db?mode=rw').Replace('file:/backup/runtime/marsense.db?mode=ro','file:/backup/runtime/marsense.db?mode=rw')
# Compare copies so WAL bookkeeping cannot modify the retained backup.
New-Item -ItemType Directory -Force "$backup\verify\runtime" | Out-Null
Copy-Item "$backup\runtime\*" "$backup\verify\runtime" -Recurse -Force
Copy-Item "$backup\after.db" "$backup\verify\after.db"
$compare | docker run --rm -i --user 0 --network none --mount "type=bind,source=$backup\verify,target=/backup" --entrypoint python marsense-free-api -; NativeOK
Write-Host "HOST UPGRADE AND RESTORE REHEARSAL PASSED. Backup: $backup; rollback images: $stamp; isolated restore volume: $restore"
