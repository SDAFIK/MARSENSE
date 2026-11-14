# Zero-cost MARSENSE hosting (operator setup)

Use an existing computer with Docker Compose and Tailscale Personal, keeping all
mission data in a dedicated persistent Docker volume. No paid cloud VM, domain,
database or AI service is needed. This is a personal/hackathon prototype, not a
high-availability or operational EVA service. The computer must stay on and
connected; electricity/internet, tunnel bandwidth and account eligibility are
real constraints. Funnel is public HTTPS, not private access control.

## 1. Prepare an isolated host

Use the validated release branch and an existing Docker Compose installation.
Do not use the local writable demo service as a public backend. Do not copy
existing private mission data into this public-facing deployment.

On Windows, in PowerShell from the repository root (with the existing Python
environment installed), create an identity outside the checkout:

```powershell
$private = Join-Path $HOME "marsense-host-private"
New-Item -ItemType Directory -Force $private | Out-Null
$env:MARSENSE_USERS_FILE = Join-Path $private "users.json"
.\.venv\Scripts\python.exe -m scripts.create_auth_user --file $env:MARSENSE_USERS_FILE --username controller --name "Mission Controller" --role MISSION_CONTROL
```

Enter a strong unique password at the prompt; never paste it into chat or GitHub.
Restrict the private file to the operator and the API container's runtime account.
Use a separate reviewer account for any intended tester. The production API
requires identity-bound sessions, explicit mutation origins and secure cookies.

## 2. Set the public origin and start the isolated stack

Install/sign in to Tailscale Personal on the host and enable MagicDNS and HTTPS
in the admin console. Get the node's DNS name from `tailscale status --json`
(Self.DNSName, remove the trailing dot). Replace the example below with the actual
host name. The tunnel hostname is not a purchased domain.

```powershell
$publicOrigin = "https://YOUR-NODE.YOUR-TAILNET.ts.net"
$env:MARSENSE_CORS_ORIGINS = ConvertTo-Json -InputObject @($publicOrigin) -Compress
docker compose -p marsense-free -f compose.funnel.yaml config --quiet
docker compose -p marsense-free -f compose.funnel.yaml up -d --build --wait
curl.exe --fail http://127.0.0.1:8080/api/health
```

The API and Next server have no published ports. Only the nginx gateway binds
host loopback port 8080. The new named volume is separate from local and other
production stores. If port 8080 is occupied, stop and resolve the conflict rather
than replacing unrelated services. This configuration expects HTTPS termination
by Funnel; do not change the binding to 0.0.0.0 or expose plain HTTP publicly.

In an Administrator PowerShell window, start the tunnel:

```powershell
tailscale funnel --bg 8080
tailscale funnel status
```

Follow the official approval prompt if needed. Confirm the actual generated
HTTPS origin matches the configured origin. Visit it from a second network and
check the public landing image, unauthenticated mission 401, sign-in,
authorized upload/review, sign-out and persistence across an API restart.
Replay is intentionally disabled in production; use a disposable, authorized
observation fixture for mutation checks, never private user evidence.
Never share test credentials publicly. Do not publish if checks fail.

## 3. Optional Vercel Hobby frontend (after the backend is verified)

Import the public repository with root directory `frontend` on the free Hobby
plan, for personal/noncommercial use within current plan limits. Configure
`BACKEND_URL` to the exact Funnel HTTPS origin (no trailing slash), then build
and deploy. Add the actual Vercel HTTPS origin to the JSON list in
`MARSENSE_CORS_ORIGINS` alongside the Funnel origin, then recreate the API
container using the same named volume. Do not use a wildcard origin.

Verify Vercel's same-origin /api proxy, secure session cookie, login/logout,
NASA assets, uploads and authenticated review through the deployed frontend.
A passing local tunnel does not establish that Vercel works. Do not expose
preview deployments as trusted mutation origins without explicit review.
No frontend deployment should be promoted before the backend is reachable.

## 4. Shutdown and recovery

`tailscale funnel reset` removes Funnel configuration on the host (check other
existing Funnel routes first; do not reset unrelated routes). To stop only this
stack, use `docker compose -p marsense-free -f compose.funnel.yaml stop` with
the same environment. Never use `down -v` on an actual mission volume.
Follow DEPLOYMENT.md for consistent SQLite/uploads/originals backup and restore.
Keep backup and identity files outside the checkout. If the host is offline,
the public app is unavailable; no high-availability guarantee is implied.

Official documentation: https://tailscale.com/kb/1223/funnel and
https://tailscale.com/pricing. This path is prepared, not externally deployed
or verified. A free cloud host is a separate alternative if one is available.
