param(
    [Parameter(Mandatory=$true)][string]$BackupDirectory
)
$ErrorActionPreference='Stop'
function NativeOK { if ($LASTEXITCODE -ne 0) { throw "Native command failed ($LASTEXITCODE). No live data was deleted." } }
$api='marsense-free-api-1'
$backup=(Resolve-Path -LiteralPath $BackupDirectory).Path
if (-not (Test-Path -LiteralPath "$backup\runtime\marsense.db" -PathType Leaf)) { throw 'Backup database not found' }
$info=(docker inspect $api | ConvertFrom-Json)[0]; NativeOK
if (-not $info.State.Running) { throw 'Production API is not running' }
if (@($info.Mounts | Where-Object {$_.Name -eq 'marsense-free_mission-data' -and $_.Destination -eq '/app/data/runtime'}).Count -ne 1) { throw 'Unexpected production volume' }
$stamp=[Guid]::NewGuid().ToString('N')
$work=Join-Path $env:TEMP "marsense-record-check-$stamp"
New-Item -ItemType Directory -Path "$work\before" -Force | Out-Null
$remote="/tmp/marsense-record-check-$stamp.db"
try {
    Copy-Item -Path "$backup\runtime\*" -Destination "$work\before" -Recurse -Force
    docker exec $api python -c "import sqlite3; a=sqlite3.connect('file:/app/data/runtime/marsense.db?mode=ro',uri=True); b=sqlite3.connect('$remote'); a.backup(b); b.close(); a.close()"; NativeOK
    docker cp "$($api):$remote" "$work\after.db"; NativeOK
    $compare=@'
import json, sqlite3
def rows(path):
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Integrity check failed'
        return {(kind, ident): json.loads(payload) for ident, kind, payload in db.execute('SELECT id,kind,payload FROM entities')}
old, new = rows('/check/before/marsense.db'), rows('/check/after.db')
missing = set(old) - set(new)
changed = [k for k in old if k in new and old[k] != new[k]]
missing_records = [k for k in missing if k[0] != 'AuthSession']
changed_records = [k for k in changed if k[0] != 'AuthSession']
print('Backup integrity: OK; live snapshot integrity: OK')
print('Original records:', len(old), 'Current records:', len(new), 'Added:', len(set(new)-set(old)))
print('Missing records:', len(missing), 'Changed non-session records:', len(changed_records))
print('Missing non-session records:', len(missing_records))
print('Missing session records:', len(missing)-len(missing_records), 'Changed session records:', len(changed)-len(changed_records))
assert len(old) == 28, 'Unexpected backup record count: expected 28'
assert not missing and not changed_records, 'Record preservation check failed'
print('POST-UPGRADE RECORD PRESERVATION PASSED')
'@
    $compare | docker run --rm -i --user 0 --network none --mount "type=bind,source=$work,target=/check" --entrypoint python $info.Image -; NativeOK
} finally {
    $previous=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        docker exec $api rm -f $remote 2>$null | Out-Null
        Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
    } finally { $ErrorActionPreference=$previous }
}
