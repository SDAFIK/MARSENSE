# MARSENSE cloud migration — gated deployment

Target: dedicated Supabase project knfvcyujieelulhswkxg. Never use TeamFlow Guard's database. The private schemas are server-only; the browser never receives a database credential. No live cutover has been made.

## Private source and verification

Use a consistent backup of the existing Windows Docker deployment's runtime and its operator identity JSON. Existing scripts/hosted-upgrade.ps1 documents the volume and identity mount. Stop/quiesce writes for a final snapshot; preserve the source volume and rollback image. Store the backup outside Git and never paste credentials into chat or logs.

From the cloud branch, install backend dependencies in a private local environment. First run:
```
python -m scripts.migrate_cloud --runtime PATH_TO_PRIVATE_RUNTIME --users PATH_TO_PRIVATE_USERS_JSON
```
This is a source-only dry run. Set MARSENSE_DATABASE_URL privately using the Supabase direct or session pooler connection (port 5432, TLS), then run the same command with --apply. The importer refuses a different destination project or conflicting destination records. It verifies exact JSON and uploaded bytes including identity records. Re-run with --verify to independently compare the target. Do not start the cloud application until import verification succeeds.

## Staging backend

The optional render.yaml specifies a free Singapore Docker web service and a lean Dockerfile that omits optional Torch dependencies; the OpenCV fallback remains. The host must be separately authorized, and actual build, memory use, cold starts and request limits must be tested. Supply the PostgreSQL connection and exact HTTPS frontend CORS origins as private environment settings. No public database password or service-role key belongs in the frontend. Use one backend instance because temporary guest demos are process-local.

## Acceptance and release

1. Require successful exact-commit SQLite/browser and PostgreSQL CI, plus a cloud container smoke test.
2. Verify health, authentication, original/derivative evidence, mission snapshots, workspace isolation, restart persistence and guest reset through staging.
3. Preserve final source backup and prevent writes to the old instance during cutover. Reconcile any changes after an earlier snapshot before switching; the importer deliberately refuses conflicting records.
4. Set the existing Vercel frontend backend origin to the validated HTTPS cloud backend, and test the preview before promoting.
5. Keep the Windows deployment and its volume intact for rollback. Do not resume writes on both versions or claim automatic reverse synchronization.

Free hosting can sleep and has resource limits; this is not an SLA or an always-on guarantee. Do not enable paid services without authorization.
