# Test plan and evidence

Implementation snapshot; required acceptance: [root TEST_PLAN.md](../TEST_PLAN.md).
The primary browser flow below executes curated replay annotations, not validated
terrain inference. It cannot certify Gates 7/14/15. Results are historical; no
application suites were run during the Gate 0-only review.

Latest completed verification: 29 pytest cases, 3 Vitest cases and 21 Playwright cases pass. Ruff/mypy/ESLint/TypeScript and the Next.js production build pass. Tests run against isolated mission databases; the native local preview also returns a healthy API and HTTP 200 mission page.

The primary acceptance scenario is exercised through the actual browser and API: orbital map + Alpha → analyze → significant discrepancy/alert → confirm → Ground Observed/Beta/WHY → reload → future EVA inheritance. Browser tests use an isolated SQLite database and block external requests in this flow.

Backend behavior tests cover matching/off-route silence, provisional safety relevance, human confirmation, weak evidence gating, rejection, conflict, immutable priors/final decisions, concurrent/idempotent verification, footprint locality, dynamic expiry, offline demo, actual upload validation, authentication, restart persistence and future-EVA inheritance. Spatial tests check Mars coordinate round-trips, a known geographic distance, deterministic path cost and no obstacle corner crossing. Pipeline tests check a known synthetic DEM plane gradient, Earth-CRS rejection, slope barriers/no route, training/evaluation/export contract, split isolation and model-failure fallback. Synthetic pipeline metrics are not scientific accuracy evidence.

Frontend component tests cover provisional/weak/final decision controls. Playwright checks all six views at 1440 px desktop, 834 px tablet and 390 px mobile, page runtime errors, horizontal overflow, connection failure/retry and keyboard navigation. Screenshots are saved under `docs/screenshots`; inspect their hierarchy, image/map visibility, forms and small-screen spacing. Browser tests use installed Edge or a configured Chromium channel.

Quality commands are in README: pytest, Ruff, mypy, ESLint, TypeScript, Vitest, Next production build and Playwright. No testing claim implies scientific validation of unprovided NASA assets/checkpoints. Docker startup is provided but requires a local Docker installation and is separate from the verified native run.

Current dependency warnings: PyTorch deprecates TorchScript in favor of newer export mechanisms; FastAPI/Starlette warn about HTTPX TestClient migration. These do not alter the tested contracts but should be tracked during dependency upgrades.

Resumed build: 39 backend and 3 component tests pass, with Ruff/mypy/ESLint/TypeScript and production Next build. Added UNKNOWN human override, separate decision/model immutability, legacy/future schema/rollback, finite geometry, independent projection and actual imagery bounds/hash tests. All 21 browser tests now pass. Two new strict range-reader tests pass locally; no network or real-model acceptance is inferred.


## Reference UI regression pass — 2026-10-10

- Backend: `.venv/Scripts/python.exe -m pytest -q --basetemp=.tmp/ui-reference-pytest-final --tb=short` — 70 passed, 8 existing deprecation warnings.
- Frontend: `npm run typecheck`, `npm run lint`, `npm run test` — pass; 3 component tests.
- Production: `npm run build` — pass, including standalone packaging.
- In-app browser on isolated SQLite/API 8001 and frontend 3001: actual observe,
  provisional alert, confirm, Beta, reload and future-EVA inheritance passed;
  map expansion/Escape, overlays and source layer selection passed. Loaded
  mission/astronaut/comparison/evidence/memory views checked at 390 x 844 and
  834 x 1112 with zero horizontal overflow. Desktop mission checked at
  1252 x 727 and 1440 x 1000. Intro desktop/mobile, source-image loading and
  browser console errors also checked. Captures: screenshots/ui-reference/.
- Visual QA: ../design-qa.md records comparisons, fixes and reference adaptations.
- Existing automated Playwright tests were not rerun in this UI pass.

Initial sandbox runs could not use default temp folders/local sockets and could
not finish standalone package writes. Resolved using an explicit workspace temp
directory and approved local execution. No user runtime database was reset.

## Full-site UI recovery checks (2026-10-10)

Backend suite: 70 passed; frontend: 9 passed (human verification guards, Alpha challenge footprint semantics, progressive Beta coordinates, aligned comparison slider). ESLint, TypeScript and isolated production Next build pass. Manual browser acceptance and screenshot evidence are documented in `../design-qa.md`. Preserve runtime data: isolated checks use a separate temporary demo database. Automated Playwright suites were not rerun for this visual pass.
