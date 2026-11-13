param([Parameter(Mandatory=$true)][string]$Origin)
$ErrorActionPreference = 'Stop'
$base = $Origin.TrimEnd('/')
$uri = [Uri]$base
if ($uri.Scheme -ne 'https' -or $uri.AbsolutePath -ne '/' -or $uri.Query -or $uri.Fragment -or $uri.UserInfo) {
    throw 'Use the exact public HTTPS origin without a path or credentials.'
}
function Check($condition, $message) {
    if (-not $condition) { throw $message }
    Write-Host "PASS: $message"
}
function Get-Guest($path, $token) {
    Invoke-RestMethod "$base/api/public-demo/$path" -Headers @{'X-Marsense-Demo'=$token}
}
function Post-Guest($path, $token, $body) {
    $headers = @{Origin=$base}
    if ($token) { $headers['X-Marsense-Demo'] = $token }
    Invoke-RestMethod "$base/api/public-demo/$path" -Method Post -Headers $headers -ContentType 'application/json' -Body ($body | ConvertTo-Json -Depth 10 -Compress)
}
function Denied($path, $token, $code) {
    $headers = @{Origin=$base}
    if ($token) { $headers['X-Marsense-Demo'] = $token }
    try {
        $null = Invoke-WebRequest "$base/api/$path" -Headers $headers -UseBasicParsing
        throw "Unexpected success: $path"
    } catch {
        if (-not $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne $code) { throw }
        Write-Host "PASS: $path rejected ($code)"
    }
}
function ActiveRoute($snapshot) {
    @($snapshot.routes | Where-Object {$_.id -eq $snapshot.mission.active_route_id})[0].name
}
$health = Invoke-RestMethod "$base/api/health"
$state = Invoke-RestMethod "$base/api/auth/session"
Check ($health.status -eq 'ok' -and $health.cache_available -and $state.environment -eq 'production' -and $state.required -and -not $state.replay_enabled) 'Production health, NASA cache and authentication boundaries'
Denied 'missions/eva-01' '' 401
$a = $null
$b = $null
try {
    $a = (Post-Guest 'start' '' @{}).token
    $b = (Post-Guest 'start' '' @{}).token
    Check ($a -and $b -and $a -ne $b) 'Two distinct anonymous sessions, no credentials'
    Check ((Get-Guest 'auth/session' $a).public_demo) 'Guest identity is simulated'
    Denied 'missions/eva-01' $a 401
    $initial = Get-Guest 'missions/eva-01' $a
    Check ((ActiveRoute $initial) -eq 'Route Alpha') 'Guest starts with Route Alpha'
    $e = Post-Guest 'observations/demo' $a @{mission_id='eva-01';scenario='obstacles'}
    Check ($e.source_type -eq 'demo_replay' -and $e.verification_state -eq 'PROVISIONAL' -and $e.discrepancy -eq 'SIGNIFICANT_DIFFERENCE') 'Curated provisional observation and discrepancy'
    Denied "public-demo/evidence/$($e.id)" $b 404
    $decision = Post-Guest "evidence/$($e.id)/verify" $a @{decision='CONFIRMED';reviewer='untrusted-client-label';note='Isolated public demo acceptance; simulated review.'}
    Check ($decision.verification_state -eq 'CONFIRMED' -and $decision.verified_by -eq 'Guest reviewer (simulation)') 'Guest-bound simulated human decision'
    Check ((ActiveRoute (Get-Guest 'missions/eva-01' $a)) -eq 'Route Beta') 'Computed Route Beta'
    Check ((Get-Guest 'missions/eva-02' $a).mission.inherited_evidence -contains $e.id) 'Future EVA inherits confirmed evidence'
    Check ((ActiveRoute (Get-Guest 'missions/eva-01' $b)) -eq 'Route Alpha') 'Other guest remains at Route Alpha'
    $null = Get-Guest "evidence/$($e.id)/history" $a
    $null = Post-Guest 'showcase/reset' $a @{}
    Check ((ActiveRoute (Get-Guest 'missions/eva-01' $a)) -eq 'Route Alpha') 'Reset affects only current disposable guest'
    Check (@((Get-Guest 'missions/eva-02' $a).mission.inherited_evidence).Count -eq 0) 'Reset clears guest inheritance'
    Denied "public-demo/evidence/$($e.id)" $a 404
    Check ((ActiveRoute (Get-Guest 'missions/eva-01' $b)) -eq 'Route Alpha') 'Second guest still isolated after reset'
    $null = Post-Guest 'auth/logout' $a @{}
    Denied 'public-demo/missions/eva-01' $a 401
    $a = $null
    $null = Post-Guest 'auth/logout' $b @{}
    Denied 'public-demo/missions/eva-01' $b 401
    $b = $null
    Denied 'missions/eva-01' '' 401
    Write-Host 'HOSTED PUBLIC DEMO ACCEPTANCE PASSED. Browser inspection is a separate gate.'
} finally {
    foreach ($token in @($a,$b)) {
        if ($token) {
            try { $null = Post-Guest 'auth/logout' $token @{} }
            catch { Write-Warning 'Temporary guest cleanup failed; it will expire automatically.' }
        }
    }
}
