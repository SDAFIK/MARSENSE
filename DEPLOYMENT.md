# Local operation and production deployment plan

Status: documentation only. No deployment/provisioning has occurred. Gate 19
cannot pass until Gates 0–18, real inference/data acceptance, all required checks
and BLOCKER/HIGH audit fixes pass. README.md contains current runnable dev commands.

## Existing local production frontend check

From frontend, npm run build produces the Next.js application successfully;
npm run start serves it on port 3000. Backend remains a local FastAPI process
with persisted SQLite/runtime uploads. NEXT_DIST_DIR separates development/E2E
builds. BACKEND_URL is server configuration; never put secrets in public env.
Use MARSENSE_ENVIRONMENT=demo on loopback for the existing demonstration.

## Configuration contract

| Variable | Meaning |
| --- | --- |
| MARSENSE_ENVIRONMENT | demo or production; production disables curated replay |
| MARSENSE_DATABASE_URL | SQLite absolute/working-directory-consistent persistent file; current application does not support PostgreSQL |
| MARSENSE_CORS_ORIGINS | Explicit JSON list of allowed origins; no wildcard |
| MARSENSE_API_TOKEN | Production backend bearer secret, >=32 characters; never exposed to browser |
| MARSENSE_MODEL_PATH | Absolute path to verified locally cached TorchScript checkpoint |
| MARSENSE_SLOPE_PATH | Optional validated Mars DEM-derived slope-grid path; no covering grid is active in the current demo |
| MARSENSE_MAX_UPLOAD_BYTES | Upload byte cap, default 8 MiB |
| BACKEND_URL | Next server backend origin; private service address in production |
| NEXT_DIST_DIR | Optional distinct Next build directory |
| PLAYWRIGHT_CHANNEL | Browser installed for local E2E; default msedge |

Current .env.example demonstrates local settings. Production auth exists on the
backend, but the current Next rewrite/browser client does not authenticate.
Production would therefore return 401 for mission data/assets and 404 for replay.
Fix the full-stack authenticated session/server proxy and validated model path
before using production mode. Do not weaken backend authorization to make the UI
appear deployed.

## Production topology to implement at Gate 19

HTTPS reverse proxy → Next standalone server → private FastAPI. Bind backend
privately; authenticate operators at the frontend server boundary and use its
server-side backend credential. Single backend writer with SQLite persistent
volume is sufficient for this bounded prototype. PostGIS migration may be chosen
later, but is not current configuration support and needs migrations/tests.

Build pinned frontend lockfile and pinned Python/AI environment into versioned
containers with non-root processes. Include only bounded cached NASA assets,
manifest and verified local model. Keep user evidence/database/uploads on a
separate persistent volume; preserve ownership/permissions and disk capacity.
Read secrets through runtime environment/secret manager. Serve assets with
appropriate private caching for user evidence. Apply request body/time/rate bounds.

Configure process restart, health and **readiness** checks, structured valid JSON
logs/request IDs without credentials, backup and restore. Current /api/health
checks process and CTX existence only; it is insufficient as readiness. Readiness
must verify DB connectivity, asset/checksum completeness and configured model.
Measure inference/mission interaction latency and bound CPU work before sizing a
host. Cache the model per service and avoid inline blocking async inference.

## Reproducible release / rollback procedure

1. Pin exact dependency versions and record build, data/model hashes and Git SHA.
2. Run every mandatory command in TEST_PLAN.md from a clean environment.
3. Complete FINAL_AUDIT.md with no open BLOCKER/HIGH findings.
4. Validate image builds, health/readiness and production browser authentication
   locally on isolated data, including upload → verification → reroute → restart.
5. Back up the live SQLite file using a consistent database backup and preserve
   uploads/provenance together; verify restore in an isolated instance.
6. Deploy that exact release behind HTTPS, observe health/logs, run protected
   smoke tests without deleting existing evidence. Keep previous release/data
   migration rollback strategy available.
7. Cold-start the full local deterministic demo with external internet blocked.

If DigitalOcean access is available at this point, use the installed provisioning
workflow then; do not create a remote box during early gates. If credentials or
provisioning are unavailable, complete the tested container/reverse-proxy/runbook
configuration and clearly report the external deployment blocker. This file is
not a claim that HTTPS, validated container deployment or backup automation exist.
Concurrent implementation added Dockerfiles, a loopback demo compose.yaml and
native PowerShell startup/shutdown scripts. Docker is not installed/exposed on
this host, so no container build/start validation is recorded. The compose
configuration is local demo mode, not protected public production.

## Competition fallback

Keep the offline demo laptop/environment, pinned dependencies, verified cache,
local model, fresh separate rehearsal DB and printed/demo steps. Record a demo
video and submission references after freeze. Remote-host failure must not force
switching to fabricated images, replay presented as AI, or deleting history.
