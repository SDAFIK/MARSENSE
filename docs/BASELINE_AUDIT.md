# Baseline engineering audit — not a release approval

Reviewed 2026-10-10, against the pasted frozen request, preserved PROJECT_SPEC.md
and newly available docs/MAIN_PROJECT_NOTES.md extraction. Another chat is actively
changing application code (confirmed by the user). Findings refer to the observed
source snapshot and isolated reproductions, not a frozen final release. See
docs/BASELINE_SOURCE_MANIFEST.json for audited source hashes. A final fixed-commit
diff review, scientific audit and FINAL_AUDIT.md are still required.

This chat changed root engineering documents/ignore rules and initialized Git;
it did not implement or overwrite application features owned by the other chat.
No production infrastructure was provisioned and user mission data was not reset.

## BLOCKER

**B01 — RESOLVED: original source reconciled.** The concurrent chat's decision
log identified C:\Users\ACER\Downloads\MARSENSE_Final_Project_Notes.docx.
This audit independently read all 458 paragraphs (28 sections), found no tracked
insertions/deletions, and verified the complete extraction matches the original
after whitespace normalization. SHA-256:
8ceaad7d579bfc79c16aa419d7db086fb21f2a15a6493463d6e07eec65c084a4.
The user supplied that path and confirmed it is the main project document in
the concurrent chat. The frozen loop, stack, NASA sources, sparse astronaut UX
and demo agree with the request. No source-authority blocker remains.

**B02 — The main acceptance path bypasses image inference.**
backend/service.py MissionService.demo reads curated model_output from
data/demo/scenarios.json. frontend/e2e/acceptance.spec.ts selects that path.
The UI labels replay, which is appropriate, but that pass is not R10/G07/G15.
Actual uploads run a conservative texture heuristic unless a local checkpoint
is supplied. ai/train.py and a synthetic training test now exist, but no genuine
AI4Mars dataset, trained validated checkpoint, calibration or independent
Perseverance-domain evaluation is bundled. Cache and validate genuine inference
then add final known-image E2E with remote model downloads blocked.

**B03 — The mandatory scientific stack is incomplete.** Current candidate HiRISE
DTM manifest reports coverage_fraction=0.0. MOLA regional data and 42 PLACES rover
poses are cached but do not establish local slope or ground-image footprint.
Calibrated Navcam/Mastcam-Z and CRISM science ingestion/registration remain open.
Do not call a source URL, training script or zero-coverage TIFF a completed
integration. Acquire bounded valid products and verify their labels/frames/units.

## HIGH

**H01 — PARTIAL FIX: UNKNOWN can still become permanent ground knowledge.**
The original high-score UNKNOWN model case now returns 422 without explicit
known human identification, and its new regression passes. However a strong
SOIL model result (confidence 0.9) confirmed with human_terrain="unknown" still
returns 200, CONFIRMED/unknown and GROUND_OBSERVED in an isolated probe. The
service checks the original class before accepting the optional human override.
Require every persistent final interpretation to be known, including explicit
human overrides, and add this second regression. No user mission data was changed.

**H02 — RESOLVED: whitespace reviewer/rationale rejected.** Concurrent code now
normalizes text before minimum-length validation. The isolated whitespace probe
raises ValidationError, and the new API regression passes. Binding identity to
an authenticated operator remains part of H04's production work.

**H03 — PARTIAL FIX: mission dependency propagation remains incomplete.**
Concurrent code now intersects actual RouteSegment geometries and uses distinct
EVA-specific segment IDs; the new off-corridor segment regression passes. Area 14
and A17/segment 3 wording are present in the seed. Target-only/access assumptions
are still not independently resolved: consequence requires intersection with an
active route. Existing persisted mission databases also skip the seed update and
retain the old shared IDs; migration is required without deleting evidence.
Test target-only dependencies, future EVA and old-store migration separately.

**H04 — Protected backend cannot be used through the production browser.**
backend/main.py requires a bearer token in production; frontend/src/lib/api.ts
sends no token and next.config.ts is a plain rewrite. Protected mission/asset
requests return 401, and the default replay endpoint is disabled. Add an
authenticated server-side frontend/session proxy and real validated inference;
keep the backend private and never put its secret in client variables.
Current compose.yaml uses loopback demo mode and is not a public deployment.

**H05 — Uploaded original evidence bytes/metadata are discarded.**
backend/main.py sanitizes the image into JPEG before storing asset/hash and
inference. That is a safe display derivative but not the original received
observation. Preserve original bytes/hash and useful provenance metadata in audit
storage, sanitize a separate derivative and explicitly identify model input.
Restrict original access; never execute or serve unsafe arbitrary content.

## MEDIUM

**M01 — Scientific metadata alignment needs a regression.** Initial CTX/HiRISE
analysis_crs omitted local y_0. CTX was fixed concurrently; HiRISE still failed
string equality with backend/spatial.py ANALYSIS_CRS in the probe. Validate
equivalent CRS/geotransforms, actual pixel-rounded crop bounds and source units,
not only a roundtrip of the same formula. The small-image SVG fallback stretches
imagery across the local extent without consuming actual manifest corners.

**M02 — Routing undersamples supported terrain.** Full-edge intersections block
obstacle-rich footprints, but other penalties apply only at destination nodes.
A rough footprint between nodes can be missed. Non-grid endpoints are silently
rounded. Compute supported edge cost/connecting geometry or explicitly restrict
input to grid nodes with clear validation. Tests must verify tiny footprints and
actual route lengths, not just deterministic output.

**M03 — Current UI can misstate provenance/freshness.** EXPECTED / ORBITAL appears
even when expected_at used verified ground evidence. The SVG fallback omits
dynamic expiry filtering while the WebGL data path filters expiry. NASA prior
archive rows are disabled, preventing inspection rather than just editing.
Mission selection is written to sessionStorage but not restored by the workspace.
Small text/map touch targets and reduced-motion behavior require captured audit.

**M04 — Async work and logging need hardening.** CPU inference runs inline in an
async upload endpoint; TorchScript loads every request. The log format manually
wraps messages as JSON without escaping embedded quotes (isolated HTTP log was
invalid JSON). Use a bounded worker/model lifecycle and a real JSON formatter;
readiness should verify DB/cache/model, not just CTX file existence.

**M05 — Failure acceptance is incomplete.** Add injected commit/routing/model
failures, original-asset retention, no-route UI, canonical saved-status recovery
and schema migration coverage. No-path currently activates an empty zero-distance
route while preserving old route rows; make the affected prior route visible and
avoid any nominal/successful traverse interpretation.

## LOW / OPTIONAL

Track TestClient/HTTPX and TorchScript deprecation warnings during pinned dependency
updates. A new model exporter must preserve the proven preprocessing/class contract.
Root contract docs describe required final acceptance; docs/* companion files from
the other chat describe its implementation. Keep both synchronized and avoid
two independent sources of product decisions. No optional NASA layer/LLM/globe
feature should displace blocker/high repairs.

## Validation observed

- Initial backend 21 tests passed; after pipeline/expiry: 26; latest with
  verification/segment regressions: 29 passed.
- Vitest: 3 passed. Playwright: 21 passed, replay/reload/future EVA, responsive
  six screens, recovery and basic keyboard navigation. Next production build passed.
- ESLint and TypeScript passed. Latest Ruff and mypy backend/ai passed (13 modules).
- Original tile/crop/photo cache SHA checks: 10/10 matched.
- Initial probes reproduced H01/H02. Latest probes confirm the first UNKNOWN
  case and whitespace fixes, reproduce H01's explicit-UNKNOWN override hole and
  the remaining HiRISE CRS mismatch.
- Candidate DTM has no valid mission samples; model smoke test is synthetic.
- Original DOCX paragraph text matches the extraction; its hash is recorded
  in BASELINE_SOURCE_MANIFEST.json.

These passes were measured at different points during concurrent edits. They are
not a fixed final release validation. The next feature owner should first read
H01–H05, implement meaningful regressions/fixes, reconcile source metadata and
complete data/model gates, then run final required suites at one fixed commit.
