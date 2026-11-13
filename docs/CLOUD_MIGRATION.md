# MARSENSE cloud migration — staged engineering release

Goal: GitHub + Vercel + dedicated Supabase PostgreSQL/Auth/Storage + cloud scientific API, independent of the Windows/Tailscale host. No paid resources, no edits to TeamFlow Guard, no production data deletion.

## Implemented in this branch
- Postgres entity-store adapter with isolated private schemas, schema version gate and transaction-scoped write serialization. Preserves existing domain records and scientific logic.
- SQLite mission import utility: dry-run by default; validates source integrity/schema, refuses nonempty target, compares all written mission records before committing. Session/account secrets are excluded and must be provisioned separately. Image assets are a separate migration.
- Dedicated PostgreSQL integration test, including isolation and restart persistence. It uses disposable CI infrastructure only.
- Mobile layout correction for the guest Astronaut View acceptance failure; browser regression remains the release gate.

## Deployment sequence (do not skip)
1. Create a new free MARSENSE Supabase project in the explicitly selected organization; never reuse TeamFlow Guard tables or credentials.
2. Provision private database namespaces and Supabase Auth identities, enforce per-user workspace ownership and server-only service credentials. Keep private images in a private Storage bucket, verify original/derivative hashes and authorization.
3. Integrate the new Store into the application and replace filesystem-dependent persistent workspace/account/asset handling. Guest sessions must remain isolated and bounded; guest state can be explicitly ephemeral on restart. Do not enable public signup or upload until storage and authorization are tested.
4. Package a lean CPU OpenCV runtime; do not load unvalidated TorchScript or train on the free service. Measure memory, cold-start latency and real routing/analysis. Render Free has ephemeral files and 512 MB RAM: not an availability guarantee.
5. Export a consistent copy of the existing operator database and assets, dry-run import, compare records and hashes, then test cloud-only staging. Do not copy old sessions or bootstrap password files into source control.
6. Connect Vercel server-only BACKEND_URL to the validated cloud origin; validate exact origins, signed-out guest flow, two-user separation, upload/restart persistence and full mobile UI. Publish only after CI and real deployed acceptance.
7. Keep the old host untouched as rollback until the cloud copy is validated. Then merge the tested default branch and update the competition README.

## Adapter integration test
Run `MARSENSE_TEST_POSTGRES_URL=postgresql://... python -m pytest tests/test_cloud_store.py -q` against a disposable PostgreSQL database only. The CI job creates disposable schemas in a short-lived PostgreSQL service.

## Import usage
`python -m scripts.cloud_import_mission --source <consistent-backup.db> --schema marsense_operator` performs a dry run. After a reviewed backup and explicit target verification, pass `--apply` with `MARSENSE_CLOUD_DATABASE_URL` in the private environment. This does not migrate uploads, identities, or sessions and is not by itself a complete cutover.

**Current boundary:** this branch prepares and tests persistence; the existing API still uses SQLite. No new Supabase project or hosted backend has been provisioned yet.

## Cloud API candidate integration
The cloud-enabled application now selects PostgreSQL for operator and personal workspace data, verifies Supabase email identities server-side, uses HTTP-only access/refresh cookies, and sends uploads to a verified private bucket. Local mode still uses its existing authentication and SQLite. The cloud operator workspace is inaccessible unless a private bootstrap identity is supplied; do not publish the original operator credentials. The no-login guest demonstration remains disposable and bounded, separate from persistent user data. The Render Blueprint is a **candidate**, not an active deployment. Its lean Dockerfile omits PyTorch training and enforces CPU CV mode. Provider confirmation delivery, refresh, storage policy, actual cloud memory/cold start, asset migration, and hosted browser acceptance must all be validated before release.
