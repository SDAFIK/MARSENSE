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
