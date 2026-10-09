# Sequential engineering gates and tickets

Source authority: frozen request + preserved PROJECT_SPEC.md and the user-confirmed
MARSENSE_Final_Project_Notes.docx, extracted at docs/MAIN_PROJECT_NOTES.md.
Current implementation: docs/IMPLEMENTATION_STATUS.md. Owner: MARSENSE engineering.

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
