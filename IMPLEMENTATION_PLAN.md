# Sequential engineering gates and tickets

Source authority: frozen request + preserved PROJECT_SPEC.md and the user-confirmed
MARSENSE_Final_Project_Notes.docx, extracted at docs/MAIN_PROJECT_NOTES.md.
Current implementation: docs/IMPLEMENTATION_STATUS.md. Owner: MARSENSE engineering.

Current execution scope: Gate 0 only, per the user's stop instruction. Gates
1-20 are a plan and historical observations, not authorization to resume
implementation in this chat.

Every gate follows: acceptance/spec → meaningful behavior test first → smallest
coherent implementation → checks → spec/code review → docs/status → coherent
commit. Existing implementation is assessed at each gate; do not rewrite passing
compatible code or label an inherited feature complete without its acceptance
evidence. Each gate blocks the next. Independent baseline audit/documentation
can continue alongside the user's other implementation chat. Application edits
remain with that chat to avoid overlapping writes. Gate 0 source is reconciled.

All tickets exclude unrelated features and optional instruments. Repository
tickets are the source of truth; Notion mirroring is conditional on actual access.

| Ticket / gate | Outcome and scope | Blocking edges | Acceptance tests / evidence |
| --- | --- | --- | --- |
| G00 Engineering specification | Frozen loop, requirements R01–R20, glossary, contracts, NASA/AI trust limits, decisions, ordered tickets | None; original notes reconciled | All required docs exist, links/requirements align, no replay/model or simulated/NASA ambiguity, authoritative DOCX cross-check recorded |
| G01 Foundation | Compatible monorepo, strict types, environment/ignore rules, Git, runnable documented commands, initial dependency locking | G00 | Clean install, lint/type checks and startup; no secrets/runtime/build artifacts tracked |
| G02 Domain and persistence | Complete typed entities, provenance/decision separation, Area 14/A17/three Alpha segments, schema versioning and history | G01 | Validation, prior immutability, restart, transactional/idempotent/concurrent confirmation, migration retention |
| G03 Mars geometry | One normalized local analysis CRS with source/render conversions, product alignment, finite valid footprints | G02 | Coordinate/distance/polyline/intersection/NoData/geotransform tests, manifest and backend agree |
| G04 NASA data | Bounded CTX/HiRISE/DTM/MOLA/CRISM/Navcam/Mastcam-Z/PLACES/AI4Mars ingestion, exact provenance and cached normalized package | G03; real selected products | Label/source verification, bounded downloads, hashes, coverage/projection, interrupted/corrupt cache tests; no fabricated missing datasets |
| G05 Core map | Real prior layers, Habitat/Delta/Area 14/position and supported footprints with accessible fallback | G04 | Render/corner alignment, layer switch, zoom, WebGL fallback, partial/offline state |
| G06 Routing | Deterministic normalized A* using distance/terrain/slope/uncertainty, mission-specific segments and dependencies | G05 | Known lengths, cost terms, obstacle edges, sub-grid patches, non-grid endpoints, blocked/no-path, source slope inputs |
| G07 Observation and inference | Validated uploads/raw assets, real local trained/validated inference, model metadata and unknown handling; labeled replay separate | G06; bounded labels/checkpoint | Real known-image + held-out inference, local model hash, mapping/metrics, failures retain evidence and manual review; no annotation substitution |
| G08 Discrepancy | Five explicit states and configurable project review thresholds, supported prior comparison | G07 | MATCH/minor/significant/conflict/insufficient cases, threshold boundaries, unknown/overlap handling |
| G09 Consequence | Exact assumption/segment/target/return relevance graph and provisional possible-safety warning | G08 | Off-route silent, relevant/safety weak warning, target-only impact, exact segment geometry, mission-specific identity |
| G10 Verification and knowledge | Confirm/reject/more-evidence lifecycle, immutable inference/decision history, bounded knowledge projection and expiry | G09 | No provisional permanent change, unknown guard, rejected audit, conflict handling, independent multi-source evidence, dynamic expiry |
| G11 Automatic reevaluation | Atomic cost/route/event update with preserved prior and future mission inheritance; stored WHY and actual tradeoff | G10 | Beta avoids footprint when preferable, no-route preserves previous context, transaction failure rollback, reload/restart/future EVA |
| G12 Final design system | Product Design brief/flow evaluation, MagicPath alternatives, selected direction, Figma tokens/components/states/six screens | G11; working design integrations | Accessible responsive hierarchy, final design artifacts and implementation references; no business-logic redesign |
| G13 Product UX | Faithful Mission Control, minimal Astronaut View, full evidence inspection, memory and before/after | G12 | Component state, keyboard, zoom/reduced motion, responsive/error/offline/stale/no-route verification |
| G14 Full integration | Real prior→image→AI→difference→consequence→human→map→route→future flow through documented contracts | G13 | API/DB/UI integration including failure and recovery; no duplicated frontend mission rules |
| G15 Playwright acceptance | Exact final Area 14/A17 loop using real inference, persistence and offline package | G14 | Browser acceptance reliable on cold isolated state; actual imagery/assumption/footprint/WHY verified; backend restart and future EVA |
| G16 Scientific-data audit | Provenance, reference-frame/registration, confidence, derived observations and claims checked | G15 | NASA_DATA.md citations, asset/metadata audit, source/calibration/measurement claims valid, no synthetic NASA data |
| G17 UX audit | Product Design captures evidence and audits all major flows and accessibility; fixes findings | G16 | Desktop/tablet/mobile, 200% zoom, contrast, touch/focus/readers, states, minimal astronaut cognitive load |
| G18 Reliability/security/performance | Bounded uploads/inference, raw provenance, no secrets/path leaks, atomic state, canonical saved status, cache readiness, backup | G17 | Injected failures, concurrency, protected full-stack flow, latency measurements, logs/request IDs, dependency audit, ALL blocker/high findings resolved |
| G19 Production configuration | Locked Docker/server env, private backend, authenticated frontend proxy, persistent volumes, HTTPS/restart/logs/health and fallback | G18 | Fresh deployment build/smoke, credential boundaries, backup/restore, local cold offline start; DigitalOcean only now if available |
| G20 Competition freeze | Exact versions/data/model hashes/final commit, README/submission checklist and demo recording | G19 | Complete mandatory suites, FINAL_AUDIT.md clear, deterministic rehearsal disconnected, recorded version/hash/assets; no new features |

## Test-first repair order within gates

With G00 source reconciliation complete, prioritize domain invariants and genuine demo
data/model blockers before UI refinements. Seed-specific names/IDs are migrated
without deleting evidence. Generate a failing regression for UNKNOWN high-score
confirmation, whitespace review identity, exact segment/target consequence,
unaligned CRS metadata and supported sub-grid terrain. Existing passing tests
must remain meaningful. Read docs/BASELINE_AUDIT.md for concrete reproductions.

## Non-goals and external blockers

No massive archives, unrequested model training claims, auto-confirming AI,
mission-resource simulator or safety certification. A missing selected product,
checkpoint, credential or tool access blocks only its dependent work, while
research/documentation/tests of existing components continue. It does not permit
inventing source products or bypassing sequential acceptance. Notion is currently
not exposed. Figma/MagicPath capabilities are available but not yet used for
Gate 12. No DigitalOcean infrastructure is provisioned at this checkpoint.

## Small tickets from the to-tickets workflow

Execution is stopped by the user's Gate 0-only instruction. All tickets are
TODO/on hold, including partially implemented behaviors awaiting final acceptance.
Owner of each: MARSENSE engineering, with QA review. Each row inherits these
non-goals: no frozen-product redesign, optional instruments, fabricated science,
automatic confirmation, unrelated platforms, destructive reset or early hosting.
Scope is limited to the named outcome. Dependencies include prior-gate acceptance
plus the listed edges. Completion requires a reviewed coherent commit, relevant
passing checks, STATUS/docs update and specified evidence. Assess existing code
first; do not rewrite accepted compatible behavior. Missing genuine inputs block
their dependent ticket rather than permitting synthetic substitutes.

| Ticket / gate | Outcome and limited scope | Extra dependency | Acceptance tests and required evidence |
| --- | --- | --- | --- |
| T01 / G01 | Reproducible compatible foundation | G00 | Clean install/start on isolated state, lint/types/build, locks/ignore and no secrets |
| T02 / G02 | Typed raw/inference/interpretation/decision provenance | T01 | Separate references/hashes, immutable prior/model/decisions and schema examples |
| T03 / G02 | Footprint/state/human review invariants | T02 | Strong/weak/failed/unknown overrides, trimmed identity, reject/more-evidence regressions |
| T04 / G02 | Versioned non-destructive migration | T03 | Restart plus old mission/segment migration preserving evidence/priors |
| T05 / G03 | Mars transforms and product alignment | G02 | CRS/geotransform/known-distance/NoData and retained frame metadata |
| T06 / G03 | Supported polygon/segment geometry | T05 | Empty/nonfinite/invalid/cross-region and exact intersection cases |
| T07 / G04 | Bounded CTX prior/cache provenance | G03 | Product/hash/corners/resolution and interrupted/corrupt cache checks |
| T08 / G04 | Aligned bounded HiRISE imagery | T07 | Source/analysis CRS, actual crop bounds/hash and corner fixture |
| T09 / G04 | Covering HiRISE DTM and real slope | T08; covering product | Label/units/datum/coverage/NoData/gradient; zero-coverage cannot pass |
| T10 / G04 | Coarse MOLA regional fallback | T07; selected product | Topography/areoid meaning, native resolution/hash and regional-only caveats |
| T11 / G04 | Calibrated Navcam asset/metadata | T08; selected product | Source ID/time/calibration/camera metadata, original/derivative hashes |
| T12 / G04 | Calibrated Mastcam-Z context | T11; selected product | Calibration/provenance contract, no RGB mineral claims |
| T13 / G04 | PLACES image/pose/frame registration | T11,T12; matching pose | SCLK/site/drive/mechanism joins, validated footprint; simulated path separate |
| T14 / G04 | CRISM science/target context | T08; selected product | Mapped product/band/label provenance, registration and target linkage |
| T15 / G04 | Genuine bounded AI4Mars split manifest | T11; genuine dataset | IDs/labels/license/hashes and disjoint rover/site/sequence splits |
| T16 / G04 | Complete normalized offline package | T09–T15 | Atomic/checksum schema, missing/corrupt/network cases; all required sources |
| T17 / G05 | Prior map with mission/position/target | G04 | Area 14/Habitat/Delta/astronaut, aligned detail and partial-state rendering |
| T18 / G05 | Cached/WebGL fallback consistency | T17 | Equal corners/routes/expiry across renderers, external requests blocked |
| T19 / G06 | Deterministic edge-aware A* costs | G05 | Non-grid endpoints, sub-grid roughness, diagonal blocks, slope/NoData and cost breakdown |
| T20 / G06 | Exact segments and no-path context | T19 | Mission-specific geometries, prior route retained, no false zero-distance success |
| T21 / G07 | Original/derivative upload contract | G06 | MIME/size/pixel/geometry bounds, both hashes, protected original access/cleanup |
| T22 / G07 | Genuine validated local inference | T21,T15 | Reproducible checkpoint/classes/preprocessing, held-out metrics, domain limits, known image |
| T23 / G07 | Failed inference/manual-review boundary | T22 | Unknown/unavailable/nonfinite retains observation; no mutation; offline model hash |
| T24 / G08 | Configured five-state discrepancy | G07 | MATCH/minor/significant/conflict/insufficient, boundaries, backend eligibility |
| T25 / G09 | Exact mission dependency consequence | G08,T20 | Route/off-route/target-only/return cases and actual dependency IDs |
| T26 / G09 | Relevant/provisional safety alerts | T25 | Strong/uncertain possible-safety, irrelevant silence, no terrain update |
| T27 / G10 | Atomic human verification lifecycle | G09 | Confirm/reject/more-evidence, immutable decisions, idempotency/concurrency/rollback |
| T28 / G10 | Local knowledge and independent evidence | T27 | Outside-footprint unchanged, multi-source independence, conflict/supersession |
| T29 / G10 | Dynamic expiry and stale history | T28 | Restart/expiry, no permanent terrain/inherited condition, consistent filtering |
| T30 / G11 | Verified reroute with stored WHY | G10 | Preferable Beta, source/decision/dependency references and actual distance tradeoff |
| T31 / G11 | Durable future-EVA reevaluation | T30 | Reload/restart/inheritance, route/commit failure preserving saved context |
| T32 / G12 | Product Design/MagicPath selection | G11; tools | Brief/flow review, alternatives and selection preserving business rules |
| T33 / G12 | Figma system and six final screens | T32 | Artifact links, tokens/components/states, responsive/accessibility/code references |
| T34 / G13 | Mission Control and sparse astronaut UX | G12 | Target/distance/return/knowledge, alert, WHY/COMPARE/review and map hierarchy |
| T35 / G13 | Evidence/memory/before-after UX | T34 | Prior inspection, raw/model/decision provenance, timeline, pending versus learned |
| T36 / G13 | Accessible canonical state/failure UX | T35 | Keyboard/zoom/reduced motion, offline/stale/partial/unsaved/conflict/no-route |
| T37 / G14 | Real complete integrated learning loop | G13 | Genuine image/model through consequence, human review, map/route/future memory |
| T38 / G15 | Known-image cold offline Playwright | G14 | Area 14/A17/Alpha segment 3, real inference, Beta/WHY, restart/future EVA |
| T39 / G16 | Scientific claims/provenance audit | G15 | Source/model/frame/coverage assertions, limitations and resolved findings |
| T40 / G17 | Captured UX/accessibility audit/fixes | G16 | Six screens, responsive/zoom/state captures, contrast/readers/focus/touch |
| T41 / G18 | Protected browser/identity reviews | G17 | Server proxy/private backend, no client secret, protected full-loop checks |
| T42 / G18 | Bounded inference/readiness/recovery | T41 | Worker/model lifecycle, valid JSON, DB/cache/model readiness, failures/performance |
| T43 / G18 | Fixed-commit blocker/high closure | T42 | FINAL_AUDIT.md, meaningful regressions and complete required validation |
| T44 / G19 | Locked production/local deployment | G18 | Container/start/smoke, HTTPS/auth/volumes/restart/backup/restore/fallback; DO only now |
| T45 / G20 | Competition freeze and rehearsal | G19 | Versions/SHA/data/model hashes, offline demo, final README/video/submission |

Gate 0 defines these tickets. It does not execute them, produce later design
artifacts, deploy an application or freeze a competition build.
