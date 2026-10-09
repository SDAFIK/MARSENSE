# MARSENSE gate status

Updated: 2026-10-10, Asia/Dhaka. This is an engineering specification/audit
checkpoint, **not** a completed product or competition freeze.

The user confirmed another chat is actively implementing in this shared workspace.
This chat owns the root specification/contract/audit checkpoint and avoids
application feature edits. Companion implementation notes are in
docs/IMPLEMENTATION_STATUS.md. Observed tests/source files changed during review;
no final gate pass is inferred from an earlier suite run.

## Current outcome

Completed Gate 0 source reconciliation and prepared all required documents, frozen requirements R01–R20, repository AGENTS,
architecture/domain/API/scientific/AI/routing/UI contracts, deterministic demo,
test plan, gates/tickets, README and deployment plan. Preserved the original
PROJECT_SPEC.md and added an engineering annex. Initialized Git and improved
ignore rules. Read/reconciled the new 28-section docs/MAIN_PROJECT_NOTES.md
extraction against all 458 paragraphs of the original Word file. Path/hash/text
fidelity is independently verified; the source-authority blocker is resolved.

Latest observed backend: **29 tests pass**. Component: **3 pass**. Browser:
**21 pass**, including replay→verify→Beta→reload→future EVA. Production frontend
build, ESLint, TypeScript, Ruff and mypy pass at their recorded snapshots.
Ten cached imagery/original photo hashes matched. Synthetic training/DEM tests
verify implementation plumbing, not scientific model/data validity.

Open release blockers/high findings are in docs/BASELINE_AUDIT.md. No design-tool
artifact, production deployment, video/submission freeze or final audit approval
has been created by this chat.

## Per-gate record

All downstream statuses mean **acceptance certification pending**, not absence
of existing code. Follow the dependency order in IMPLEMENTATION_PLAN.md.

| Gate | Status | Completed/observed work | Tests/evidence | Known issues / next step |
| --- | --- | --- | --- | --- |
| 0 Specification | PASS at document checkpoint | All root docs/decisions/tickets; frozen extraction reconciled | Manual requirements/contracts/source cross-check; doc completeness/link check | Original DOCX text/hash verified; next: G01 acceptance with the implementation owner |
| 1 Foundation | REVIEW; acceptance pending | Existing compatible monorepo; Git initialized; strict TS; ignore/env setup; Docker files appear concurrently | Native lint/types/build passing snapshots | Windows dependency pins added; clean install/container validation; next G02 |
| 2 Domain/persistence | PARTIAL; acceptance pending | Typed entities; SQLite transactions; persisted evidence/history | Core restart/idempotency/concurrency tests | UNKNOWN human override, typed provenance, old-store segment migration; next G03 |
| 3 Mars geometry | PARTIAL; acceptance pending | Explicit Mars local transforms, validated footprint geometry | Roundtrip/known-distance/footprint tests | HiRISE manifest CRS mismatch, source geotransform/crop validation; next G04 |
| 4 NASA ingestion | INCOMPLETE | CTX/HiRISE/PIA26072 cache; new MOLA/PLACES subset; candidate DTM sampler | 10 initial cache SHA checks match; source docs verified | DTM zero coverage, calibrated cameras/registration/CRISM/genuine AI4Mars incomplete; next G05 after source acceptance |
| 5 Core map | PARTIAL; acceptance pending | MapLibre local imagery/route/footprints plus SVG | Browser rendering/overflow screenshots | Area 14 labeling, astronaut position, fallback metadata/expiry; next G06 |
| 6 Routing | PARTIAL; acceptance pending | Deterministic A*, verified obstacle edges; optional slope adapter | Baseline path/footprint and synthetic slope/no-route tests | Valid source slope, exact segments, sub-grid cost/endpoints/config; next G07 |
| 7 Observation/AI | INCOMPLETE | Upload/CV/TorchScript adapter; new training/evaluation/export plumbing; labeled replay | Upload and synthetic model smoke tests | No genuine trained validated offline checkpoint or independent metrics; next G08 |
| 8 Discrepancy | PARTIAL; acceptance pending | Five states, footprint prior lookup | MATCH/minor/significant/conflict/weak core cases | Configurable backend policy/calibration/unknown rules; next G09 |
| 9 Consequence | PARTIAL; acceptance pending | Active-route relevance and provisional safety warning | On-route/weak/off-route branches | Exact segments improved; target-only dependencies/old-store migration; next G10 |
| 10 Verification/Living Map | PARTIAL; acceptance pending | Confirm/reject/more-evidence; local knowledge; dynamic expiry | Core/dynamic/rejection/conflict cases | UNKNOWN human override, independent multi-source/supersession; next G11 |
| 11 Reevaluation | PARTIAL; acceptance pending | Beta, route versions/events, future EVA evidence | Replay loop, restart/inheritance tests | Complete WHY dependency graph, failure rollback/no-route UI; next G12 |
| 12 Final design | NOT CERTIFIED | Frozen UI brief and existing screen implementation | Root UI_SYSTEM.md; Figma/MagicPath capabilities discovered | Product Design/MagicPath/Figma selected artifacts pending; next G13 |
| 13 Product UX | PARTIAL; acceptance pending | Six screens, improved astronaut layout from other chat | 3 component tests; responsive browser screens | Evidence freshness/prior inspection, minimal next-target/return UX, accessibility; next G14 |
| 14 Integration | PARTIAL | Replay complete loop; actual uploads/manual review path | Backend/API/persistence and browser tests | Mandatory real AI/scientific flow incomplete; next G15 |
| 15 Acceptance E2E | REPLAY PASS; full acceptance INCOMPLETE | Replay Alpha→provisional→verified→Beta→reload→future EVA | 21 Playwright tests passed | Real known-image inference, names now seeded; old-store migration/cold offline package; next G16 |
| 16 Scientific audit | OPEN | Sources/provenance claims inspected; no invented missing science | NASA_DATA.md and baseline findings | Covering DTM/camera/science/model validation and registration; next G17 |
| 17 UX audit | OPEN | Desktop/tablet/mobile screenshots generated | docs/screenshots; overflow/keyboard cases | Formal Product Design evidence audit/contrast/readers/zoom/states; next G18 |
| 18 Reliability/security/performance | OPEN | Upload caps, explicit CORS, API auth, serialized writes | Auth/upload/concurrency/recovery tests | HIGH findings, protected browser proxy, raw assets, valid JSON logs, readiness and failures; next G19 |
| 19 Production config | DRAFT; not deployed | DEPLOYMENT.md; concurrent loopback compose/Docker/start scripts | Native Next build passes; Docker unavailable on host | Locked clean deployment, auth/HTTPS/backup/smoke/health before DO; next G20 |
| 20 Competition freeze | NOT READY | Frozen story/required freeze checklist documented | No complete freeze evidence | Resolve prior gates and blocker/high findings; final audit, exact SHA/data/model/version, video/submission |

## Continuation

Do not race the other chat's application edits. Use docs/BASELINE_AUDIT.md for
concrete failing guard/dependency/provenance cases and TEST_PLAN.md for the final
missing behaviors. Source-authority provenance is resolved; product choices are already specified. No ordinary permission gate is
introduced. Never claim release readiness because transparent replay tests pass.
