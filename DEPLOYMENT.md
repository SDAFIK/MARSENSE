# Deployment readiness — S10

MARSENSE is a research and mission-concept prototype for evidence-aware Mars
exploration decision support built from NASA-derived data and validated prototype
workflows. Public publication has not been authorized or performed. Source/model
limits in NASA_SOURCE_MATRIX.md remain; this is not operational EVA software.

## Local operation

Run scripts/start-local.ps1 after README dependency setup. It refuses occupied
ports, runs hidden loopback services on 3000/8000 and preserves SQLite mission
history. Frontend development edits reload automatically; backend code requires
a controlled process restart. Do not delete the database to repeat a demo.
Use a separate MARSENSE_DATABASE_URL for a fresh demonstration instead.

## Production preparation (operator steps, not executed)

1. Provision a Linux host with Docker Compose, a hostname and a valid TLS
   certificate. No infrastructure or billing action is automated here.
2. Provision identities using `python -m scripts.create_auth_user --file
   /private/marsense/users.json --username controller --name "Mission Controller"
   --role MISSION_CONTROL`. Use an installed project environment. Password is
   prompted, salted and hashed. Restrict file access to the API container account;
   never commit it. ADMIN also reviews; ASTRONAUT submits observations.
3. Set MARSENSE_USERS_FILE to that absolute private file, MARSENSE_DOMAIN to the
   certificate hostname, and MARSENSE_TLS_DIR to a directory containing
   fullchain.pem and privkey.pem. These are operator environment values, not
   secrets checked into the repository. The runtime account must be able to read
   its mounted users file; set ownership for the container UID or use a managed
   secrets mount with the same path. TLS key is readable only by the gateway.
4. Validate: `docker compose -f compose.production.yaml config --quiet`.
5. Build: `docker compose -f compose.production.yaml build`.
6. After separately authorizing publication, start with
   `docker compose -p marsense-production -f compose.production.yaml up -d`.
7. Check `docker compose -p marsense-production -f compose.production.yaml ps`,
   `/api/health`, browser sign-in, image decoding and an authorized test review
   against a disposable mission environment before accepting traffic.

The production file exposes only TLS port 443, routes through nginx to standalone
Next.js and private FastAPI, uses one API worker and persistent SQLite, and
restarts services unless stopped. API CORS is the exact HTTPS origin. Cookies
are Secure/HttpOnly/SameSite Strict; mutation Origin and roles are enforced.
Login rate limits exist at nginx and inside the single API process. The inner
limiter sees the direct proxy address and can throttle the small deployment
collectively; do not claim distributed abuse protection. Plan operational limits
and monitoring before scaling. API uploads are capped at 8 MiB with decoded
pixel limits; gateway body limit is 10 MiB for multipart overhead.

## Database and recovery

SQLite WAL and atomic schema-version migrations are the supported local/small
single-instance production database. Future schema versions are refused. Do not
configure PostgreSQL: the current store does not implement it. A named Docker
volume survives restarts/rebuilds. Never use `down -v` against mission data.

Back up the database with Python sqlite3's online backup API (not a live file
copy that omits WAL), and separately back up runtime/uploads and runtime/originals,
private identity configuration, and exact source manifests/cache. For a consistent
mission+upload snapshot, quiesce writes or stop only the API during backup.
Store backups encrypted with restrictive permissions outside the public web root.
Restore into a new volume/directory, run `PRAGMA integrity_check`, start the same
application version and inspect mission/evidence/history before changing traffic.
Keep the original volume intact for rollback. Sessions are in the database;
revoke them or rotate identities after a suspected compromise.

## Scientific/runtime configuration

The default local run keeps existing route cost facts and deterministic replay.
MARSENSE_SLOPE_PATH may explicitly select data/processed/hirise-covering-slope.npz
for a new isolated run. Configured invalid grids fail; unconfigured slope is
visibly excluded. MARSENSE_MODEL_PATH may select the experimental checkpoint,
whose classification remains disabled because measured quality is low. Mount
that checkpoint and adjacent metadata explicitly; checkpoints are excluded from
Docker builds by default. Genuine camera/CRISM context is bundled locally.
Production disables replay; local demo is a separate explicit mode. Optional
MARSENSE_READ_ONLY=true blocks mission mutation; never expose writable demo mode.

Health endpoint reports process/cache availability; it is not scientific source
certification. API errors use structured logging without passwords/session
secrets; container access logs require normal retention/privacy controls.

## Verification boundary

Native backend, Next production build, authenticated browser flow and offline
local acceptance are tested. Docker image builds, nginx TLS termination, DNS,
certificate renewal and external backup/restore operations have not been executed
in this workstation session. S10 delivers configuration and exact operator steps;
there is no externally deployed service or production security certification.
