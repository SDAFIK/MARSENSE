param(
    [Parameter(Mandatory=$true)][string]$ProductionOrigin,
    [Parameter(Mandatory=$true)][string]$ShowcaseOrigin
)
$ErrorActionPreference = 'Stop'
$prod = $ProductionOrigin.TrimEnd('/')
$show = $ShowcaseOrigin.TrimEnd('/')
foreach ($origin in @($prod,$show)) {
    $uri=[Uri]$origin
    if ($uri.Scheme -ne 'https' -or $uri.AbsolutePath -ne '/' -or $uri.Query -or $uri.Fragment -or $uri.UserInfo) { throw 'Use an HTTPS origin without path or credentials.' }
}
if ($prod -eq $show) { throw 'Production and showcase origins must differ.' }
function Check($condition,$message) { if(-not $condition){throw $message}; Write-Host "PASS: $message" }
function Login($url,$credential) {
    $session=New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $body=@{username=$credential.UserName;password=$credential.GetNetworkCredential().Password}|ConvertTo-Json -Compress
    $null=Invoke-RestMethod "$url/api/auth/login" -Method Post -Headers @{Origin=$url} -ContentType 'application/json' -Body $body -WebSession $session
    return $session
}
function Post($url,$path,$session,$body) {
    Invoke-RestMethod "$url/api/$path" -Method Post -Headers @{Origin=$url} -ContentType 'application/json' -Body ($body|ConvertTo-Json -Compress -Depth 10) -WebSession $session
}
function Denied($url,$path,$session,$code) {
    try { $null=Invoke-WebRequest "$url/api/$path" -UseBasicParsing -WebSession $session; throw "Unexpected success: $path" }
    catch { if (-not $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne $code) {throw}; Write-Host "PASS: $path rejected ($code)" }
}
function Snapshot($url,$session,$id) { Invoke-RestMethod "$url/api/missions/$id" -WebSession $session }
function ActiveRoute($snap) { @($snap.routes|Where-Object {$_.id -eq $snap.mission.active_route_id})[0].name }
$ph=Invoke-RestMethod "$prod/api/health"; $sh=Invoke-RestMethod "$show/api/health"
Check ($ph.environment -eq 'production' -and $sh.environment -eq 'showcase') 'Distinct public environments'
$ps=$null; $ss=$null
try {
    $pc=Get-Credential -Message 'Existing production account (mission read-only acceptance)'
    $ps=Login $prod $pc; $pc=$null
    $pstate=Invoke-RestMethod "$prod/api/auth/session" -WebSession $ps
    Check ($null -ne $pstate.user -and -not $pstate.replay_enabled) 'Production authenticated session'
    $before1=(Snapshot $prod $ps 'eva-01')|ConvertTo-Json -Depth 100 -Compress
    $before2=(Snapshot $prod $ps 'eva-02')|ConvertTo-Json -Depth 100 -Compress
    $sc=Get-Credential -UserName 'showcase-admin' -Message 'Separate showcase administrator'
    $ss=Login $show $sc; $sc=$null
    $sstate=Invoke-RestMethod "$show/api/auth/session" -WebSession $ss
    Check ($sstate.environment -eq 'showcase' -and $sstate.replay_enabled -and $sstate.user.role -eq 'ADMIN') 'Showcase administrator and replay'
    $start=Snapshot $show $ss 'eva-01'
    Check ((ActiveRoute $start) -eq 'Route Alpha') 'Showcase starts with Route Alpha'
    Check (@($start.evidence|Where-Object {$_.source_type -ne 'orbital'}).Count -eq 0) 'Clean showcase; no existing ground evidence'
    $e=Post $show 'observations/demo' $ss @{mission_id='eva-01';scenario='obstacles'}
    Check ($e.source_type -eq 'demo_replay' -and $e.verification_state -eq 'PROVISIONAL' -and $e.discrepancy -eq 'SIGNIFICANT_DIFFERENCE') 'Curated observation is provisional'
    $v=Post $show "evidence/$($e.id)/verify" $ss @{decision='CONFIRMED';reviewer='untrusted-client-name';note='Hosted isolated acceptance: curated evidence reviewed.'}
    Check ($v.verification_state -eq 'CONFIRMED' -and $v.verified_by -eq $sstate.user.name) 'Identity-bound human decision'
    Check ((ActiveRoute (Snapshot $show $ss 'eva-01')) -eq 'Route Beta') 'Route Beta activated'
    Check ((Snapshot $show $ss 'eva-02').mission.inherited_evidence -contains $e.id) 'Future EVA inherits evidence'
    if ((Read-Host 'Type RESET to clear ONLY the isolated showcase just tested') -ne 'RESET') { throw 'Reset not authorized' }
    $null=Post $show 'showcase/reset' $ss @{}
    Check ((ActiveRoute (Snapshot $show $ss 'eva-01')) -eq 'Route Alpha') 'Showcase reset restores Alpha'
    Check (@((Snapshot $show $ss 'eva-02').mission.inherited_evidence).Count -eq 0) 'Showcase inheritance cleared'
    Denied $show "evidence/$($e.id)" $ss 404
    $after1=(Snapshot $prod $ps 'eva-01')|ConvertTo-Json -Depth 100 -Compress
    $after2=(Snapshot $prod $ps 'eva-02')|ConvertTo-Json -Depth 100 -Compress
    Check ($before1 -eq $after1 -and $before2 -eq $after2) 'Production mission snapshots unchanged'
} finally {
    try { if($ss){$null=Post $show 'auth/logout' $ss @{}} } finally { if($ps){$null=Post $prod 'auth/logout' $ps @{}} }
}
Denied $prod 'missions/eva-01' $ps 401
Denied $show 'missions/eva-01' $ss 401
Write-Host 'HOSTED API ACCEPTANCE PASSED. Browser sign-in/navigation/logout still require inspection.'
