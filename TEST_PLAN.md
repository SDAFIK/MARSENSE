# Validation plan and baseline results

Date: 2026-10-10. Historical results below validate the existing implementation
and precede the user's Gate 0-only stop. No application test, feature repair,
training, ingestion or server launch is part of this Gate 0 review. A passing
suite does not waive missing trained AI, required datasets or audit
findings. No tests are disabled or changed to conceal these gaps.

## Current local commands

From D:\MARSENSE:

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp/test-run
.venv\Scripts\python.exe -m ruff check backend ai scripts tests
.venv\Scripts\python.exe -m mypy backend ai
```

From D:\MARSENSE\frontend:

```powershell
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

Playwright starts isolated FastAPI (8001) and Next dev (3001), using one worker
and Edge by default; PLAYWRIGHT_CHANNEL overrides browser selection. It does not
reset data/runtime/marsense.db. Each run uses a temporary E2E DB. Browser fixtures
currently depend on the serial first flow's verification; failure should not be
hidden by changing tests to accept arbitrary prior state.

On this host sandbox restrictions prevented pytest temporary-directory access
and Vitest compiler subprocess launch. Authorized elevated reruns succeeded;
these were tooling failures, not application test failures. Use a fresh test
directory; do not recursively delete unchecked computed Windows paths.

## Measured baseline

| Check | Result / scope |
| --- | --- |
| pytest | Initial 21 passed; after pipeline/expiry 26; latest guard/segment regressions 29 passed; TestClient and TorchScript deprecation warnings |
| Vitest | 3 component tests passed; weak/strong/final EvidenceReview states |
| ESLint | Passed |
| TypeScript | Passed |
| mypy backend/ai | Latest pass, 13 source files |
| Next.js production build | Passed; six requested screens generated |
| Playwright | 21 passed, including replay loop, six screens × three sizes, service recovery and basic keyboard navigation |
| Ruff | Initial line-length failures corrected by concurrent implementation; latest rerun passed |
| Cached manifest hash audit | All 10 listed tile/crop/original-photo SHA-256 comparisons matched |

Playwright screenshots are in docs/screenshots. External requests are blocked in
the primary browser flow; it exercises curated replay, not local trained-model
inference. Backend offline test forces urllib failure but cannot establish the
missing data/model pipeline. Existing screenshot generation is not a completed
Product Design/accessibility audit.

## Required TDD additions by boundary

| Boundary | Required behaviors and acceptance evidence |
| --- | --- |
| Domain/verification | R02–R07/R13: immutable priors/inference, trimmed reviewer/note, UNKNOWN guards, rejection, more-evidence, independent confirmation, conflict resolution |
| Geometry | R06/R08: finite/empty/malformed polygons, metadata projection agreement, image geotransform alignment, known longitude/latitude distances, supported edge intersections |
| Routing | R14/R15: blocked/no-path, non-grid endpoint accounting, small rough footprints, slope/NoData, actual distance delta and affected segment graph |
| Consequence | R11/R12: MATCH no alert, off-route minor silent, route significance warning, weak unknown possible safety warning, target-only dependency, exact segment mapping, other-EVA identities |
| Persistence | R13/R16/R19: restart, concurrent/idempotent confirmation, injected commit failure rollback, retained route after failure, schema migration without history loss |
| AI | R03/R10/R19: real model output on held-out known images, class mapping, unknown fraction, checksum/preprocessing, absent/failed/nonfinite model; original upload vs sanitized derivative |
| API/security | R19/R20: upload MIME/size/pixels/geometry, no leaked paths or request bodies/secrets, auth through frontend server boundary, idempotent transport retry |
| NASA | R09/R17: bounded real product ingestion, projection/NoData/units, corruption/missing partial cache, deterministic ingestion, atomic interrupted update |
| Components | R04/R05/R18/R19: canonical eligibility, stale/conflict/unknown/unsaved state, offline disabling, actual upload preview and NASA prior inspection |
| E2E | R01/R10/R15–R18: exact Area 14/A17 flow with real inference, Beta explanation facts, backend restart, future EVA, cold offline start and isolated fixture independence |
| UX | R18: captured evidence first, contrast, 200% zoom, all controls by keyboard, reduced motion, screen reader, 44 px target review, no overflow, minimal astronaut flow |
| Deployment | R20: pinned clean install, container health/readiness, backup/restore, production proxy/auth, logs, cold local fallback |

Use toolkit TDD at core behavior seams: reproduce failure with a meaningful test,
implement the smallest fix, review and run the relevant suite. Expand testing
only for changed behavior or unresolved risks. Final freeze requires all mandatory
checks passing and BLOCKER/HIGH findings resolved; never treat a baseline replay
pass as Gate 15 completion.
