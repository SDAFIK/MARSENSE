> **Current prototype checkpoint — 2026-10-10:** S1–S10 workflow implementation,
> source matrix, claim audit and deployment preparation are recorded in
> [FINAL_AUDIT.md](FINAL_AUDIT.md). Validation: 70 backend tests, 3 component tests,
> 24 browser checks plus 1 authenticated browser flow; static checks and build pass.
> Source reliability remains partial: weak model classification is disabled,
> camera footprints are unknown, and CRISM coverage/registration limits remain.
> This is a research and mission-concept prototype, not full scientific validation.
> Nothing is publicly deployed. Earlier counts/gaps below are historical snapshots.

# MARSENSE gate status

> Current instruction: scientific completion resumed under SCIENTIFIC_COMPLETION_REQUEST.md. Start with S1 and pass each gate before continuing through S10. Preserve working behavior, services and mission history; no automatic public publication.

> Earlier scope instructions below are historical; the latest scientific completion request governs current execution.

Updated: 2026-10-10, Asia/Dhaka. This is an engineering specification/audit
checkpoint, **not** a completed product or competition freeze.

**Current scope: implementation explicitly resumed.** The latest user request
supersedes the earlier Gate 0-only pause. Ordered Toolkit revalidation is recorded
in docs/RESUMPTION_REVIEW.md. Existing services and saved missions are preserved.

Resumed work: persistent UNKNOWN overrides rejected; separate immutable human
review/interpretation records and typed provenance added; schema v2 migrates
legacy Alpha dependencies without losing decisions or historical references.
Importing the API no longer initializes/migrates the default runtime database;
initialization occurs only in the application's lifespan.

Geometry: finite input validation, independent PROJ transform checks, actual
pixel-rounded imagery bounds/resolution and source hashes verified. A new genuine
HiRISE DTM provides valid elevation at all 651 mission nodes, with label-verified
units/datum and bounded source ranges. It is not silently activated against saved
routes. Calibrated cameras, camera registration, CRISM and genuine model validation
still block scientific completion. NASA-linked AI4Mars ZIP index (146,179 entries) was obtained via ranges;
no model result is yet claimed. The next acquisition command was rejected by
automatic approval review because account usage prevented review completion.
This was a review failure, not a safety judgment; the blocked action was not run.

Measured resumed checks: 39 backend tests pass, plus 2 bounded-range reader tests;
3 component tests, 21 browser tests, Ruff, ESLint, TypeScript, mypy and
production frontend build pass. Browser acceptance remains labeled replay.
Tests use isolated databases. Docker remains unavailable; no deployment/freeze.

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
| 0 Specification | DONE; revalidated for resumption | Ordered five workflows, all 13 deliverables including .env.example, 45 small tickets, source reconciliation and contradiction fixes | docs/GATE_0_REVIEW.md and docs/GATE_0_CHECKS.json | Later scientific/model gaps are specified; next: sequential implementation under latest user request |
| 1 Foundation | REVIEW; acceptance pending | Existing compatible monorepo; Git initialized; strict TS; ignore/env setup; Docker files appear concurrently | Native lint/types/build passing snapshots | Windows dependency pins added; clean install/container validation; next G02 |
| 2 Domain/persistence | PARTIAL; acceptance pending | Typed entities; SQLite transactions; persisted evidence/history | Core restart/idempotency/concurrency tests | Guard/provenance/review records and legacy migration repaired; clean foundation acceptance and full lifecycle review pending; next G03 |
| 3 Mars geometry | PARTIAL; acceptance pending | Explicit Mars local transforms, validated footprint geometry | Roundtrip/known-distance/footprint tests | CRS/crop alignment and finite-input tests now pass; complete source-layer registration remains G04; next G04 |
| 4 NASA ingestion | INCOMPLETE | CTX/HiRISE/PIA26072 cache; new MOLA/PLACES subset; candidate DTM sampler | 10 initial cache SHA checks match; source docs verified | Covering DTM now sampled successfully; calibrated cameras/registration/CRISM/genuine AI4Mars incomplete; next G05 after source acceptance |
| 5 Core map | PARTIAL; acceptance pending | MapLibre local imagery/route/footprints plus SVG | Browser rendering/overflow screenshots | Area 14 labeling, astronaut position, fallback metadata/expiry; next G06 |
| 6 Routing | PARTIAL; acceptance pending | Deterministic A*, verified obstacle edges; optional slope adapter | Baseline path/footprint and synthetic slope/no-route tests | Valid source slope, exact segments, sub-grid cost/endpoints/config; next G07 |
| 7 Observation/AI | INCOMPLETE | Upload/CV/TorchScript adapter; new training/evaluation/export plumbing; labeled replay | Upload and synthetic model smoke tests | No genuine trained validated offline checkpoint or independent metrics; next G08 |
| 8 Discrepancy | PARTIAL; acceptance pending | Five states, footprint prior lookup | MATCH/minor/significant/conflict/weak core cases | Configurable backend policy/calibration/unknown rules; next G09 |
| 9 Consequence | PARTIAL; acceptance pending | Active-route relevance and provisional safety warning | On-route/weak/off-route branches | Exact segments improved; target-only dependencies/old-store migration; next G10 |
| 10 Verification/Living Map | PARTIAL; acceptance pending | Confirm/reject/more-evidence; local knowledge; dynamic expiry | Core/dynamic/rejection/conflict cases | UNKNOWN override repaired; independent multi-source/supersession pending; next G11 |
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

## Runtime/tool blocker

Automatic approval review rejected the next AI4Mars acquisition command because
the account usage limit prevented review completion (retry time reported 9:19 AM).
No full model/data acceptance or later-gate certification is claimed. The strict
range reader is implemented and its rejection/budget/cache tests pass locally.
Git gate commits also remain pending because .git writes require approval; no
permissions workaround is used. Existing services/history are preserved.

## Continuation

Continue the sequential tickets in IMPLEMENTATION_PLAN.md. Domain and geometry
repairs do not waive missing scientific inputs or real-inference acceptance.
Complete the bounded source package before certifying later gates. Root contracts
remain authoritative; historical baseline findings are retained for traceability.

## Scientific gate execution

S1: PASS for the research prototype (coarse 40 m slope); review in docs/science/S1_REVIEW.md. 45 backend, 3 component and 21 browser tests pass; Ruff/mypy/ESLint/TypeScript pass. Production frontend build passes. S2 active next; S3–S10 pending in order. See docs/SCIENTIFIC_COMPLETION_REQUEST.md for the exact current request.

S2 in progress: genuine AI4Mars merged-0.6 metadata and image/label pairs acquired via bounded ranges. Deterministic site-disjoint subset acquisition running; no checkpoint or real metrics accepted yet. Duplicate-byte/shared-group leakage guards, held-out/transfer evaluation reporting and checkpoint hash/preprocessing verification implemented; synthetic contract checks remain explicitly synthetic.

S2 acquisition checkpoint: 48 genuine training pairs and 16 validation pairs cached. Expert held-out pairs and reserved Perseverance transfer pairs still acquiring. Source archive responses are strictly checked; incomplete bytes are rejected and retries are capped. Latest code contracts: 50-test backend regression passed before the additional S1 tamper/direction tests; 7 S1-focused tests now pass. Model-card generation requires genuine artifact hashes and separate held-out/transfer outputs. No real model performance reported yet.

Current code verification: 52 backend tests pass; Ruff and mypy pass after latest hardening. Frontend alignment change remains covered by passing 3 component/21 browser tests, ESLint/TypeScript and production build. Genuine subset final transfer acquisition remains active; S2 acceptance still pending training/evaluation.

S2 genuine dataset acquired: 48 train/16 validation/16 expert held-out/8 Perseverance transfer pairs; 27/8/12/7 groups, all cross-partition intersections empty. All four NAV classes have real annotations in each partition. Successful range reads total 28,492,927 bytes; source files and hashes preserved. Earlier acquisition approval-limit blocker is resolved for these authorized reads. CPU training (three fixed epochs) is active; no metric or S2 pass claimed yet.

S2 baseline v1 FAILED: validation predicts only soil (validation mIoU .152066); zero recall for bedrock/sand/large rocks. Original checkpoint, metrics, dataset manifest and model card are preserved as baseline-v1 artifacts. Anti-collapse check intentionally fails; adapter refuses failed candidates and returns UNKNOWN/unavailable with checkpoint hash. Repair uses inverse-frequency loss weights from training counts only and validation feedback. Fresh expert-test sites and Perseverance sols are being reserved before evaluating the repaired model. S3–S10 remain gated.

S2 repair run: training/validation manifests unchanged byte-for-byte; final expert sites and Perseverance sols are disjoint from the earlier diagnostic sets. Eight fixed epochs with inverse-frequency training-only loss weights are running. Failed baseline remains preserved; genuine acceptance test intentionally fails for that candidate. Eight S1-focused tests pass, including direct-router no-data rejection.

S2 weighted v2 FAILED: validation mIoU .159434; bedrock and large-rock recall remain zero. Training diagnostic also has zero recall for those classes, so this is underfitting rather than only transfer failure. V2 checkpoint/metrics/model card and exact split manifest are preserved. Compact U-Net plus weighted valid-pixel loss normalization prepared; source-independent tests/export pass. Fresh reserved evaluation acquisition is active. No S2 acceptance or advancement.

S2 compact encoder-decoder run: twelve fixed epochs, training-only inverse-frequency weights, weighted loss sum / valid pixel count, BatchNorm and 16/32/64 channels. Export/inference synthetic contract passes. Final reserved reference masks contain every class; group disjointness from all prior diagnostics verified. Evaluation has not yet been accepted; S3 stays pending.

S2 pipeline PASS with explicit experimental-model limitation: 54 backend tests/Ruff/mypy pass; review in docs/science/S2_REVIEW.md. Held-out mIoU .099405, Perseverance transfer .132736; terrain classification disabled, raw scores retained and human identification required. This does not validate model reliability or full scientific completion. S3 next; S4–S10 pending.
## Latest checkpoint — S3

Calibrated Navcam/Mastcam-Z ingestion and conservative PLACES context pass the
prototype workflow. 60 backend, 3 component and 21 browser tests pass; Ruff,
mypy, ESLint, TypeScript and production build pass. Review:
docs/science/S3_REVIEW.md. Genuine calibrated arrays, masks, previews and source
hashes are separate; the Evidence Inspector exposes limits. Mastcam observation
clock and exact image footprints remain unvalidated/unknown. S4–S10 remain open;
no full scientific completion or publication is claimed.


## Latest checkpoint — 2026-10-10
S4 processed CRISM context workflow accepted with explicit source limits;
see docs/science/S4_REVIEW.md. S5–S10 remain pending. Map workspace expanded
without resetting mission history. This is not a scientific completion claim.

S5 prototype ancestry/supersession workflow accepted (docs/science/S5_REVIEW.md).
67 backend tests and two new browser checks pass. Identity-bound review is S6,
currently pending; source assertions in local mode remain self-asserted.

S6 accepted: three security tests pass (including Secure/SameSite cookies and
login throttling), 25 auth/core regression tests pass, browser authentication
flow passes, Ruff and mypy pass. S7 source verification is next.

S7 matrix complete: NASA_SOURCE_MATRIX.md records all eight genuine sources,
actual use, provenance, coordinate handling and remaining partial validation.
Proceed to S8 claim audit; no full scientific validation claim is justified.

S8 scientific claim audit completed: SCIENTIFIC_AUDIT.md records fixed claims,
classification and unresolved source reliability limits. S9 regression underway.

S9 passed: 70 backend tests, 3 component tests, 24 main browser tests plus the
separate authenticated browser flow. Ruff (backend/ai/scripts/tests), mypy
(18 source files), ESLint, TypeScript and production frontend build pass.
Camera/CRISM caches verify 23 frozen files. S10 deployment preparation follows.
