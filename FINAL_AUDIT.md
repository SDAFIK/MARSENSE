# Final prototype audit — 2026-10-10

MARSENSE is a research and mission-concept prototype for evidence-aware Mars
exploration decision support built from NASA-derived data and validated prototype
workflows. The requested S1–S10 implementation sequence is complete at the
prototype-workflow level. This is not full scientific validation or certification.

| Gate | Outcome | Evidence / limits |
|---|---|---|
| S1 | Accepted | Genuine covering DTM, 651 finite samples, independent pixel-center check, coarse slope/route tests; source and correction history retained |
| S2 | Accepted workflow; source partially validated | Genuine training and held-out/transfer evaluation; poor classifier disabled, UNKNOWN/manual review retained; MODEL_CARD.md |
| S3 | Accepted ingestion/uncertainty workflow | Calibrated Navcam/Mastcam products; exact interval joins; missing pointing/footprints explicit; S3_REVIEW.md |
| S4 | Accepted context workflow | Genuine CRISM processed browse, coverage/target provenance; no mineral claim; one-pixel mapping discrepancy retained |
| S5 | Accepted | Immutable declarations and supersession, overlap-only independent support, conflicts/ancestry UI, current planning excludes retired evidence |
| S6 | Accepted prototype authentication | Signed-in reviewer identity, roles, cookie sessions, origin validation, expiry/logout, read-only mode and rate limits tested |
| S7 | Accepted inventory | NASA_SOURCE_MATRIX.md includes all eight genuine source streams with actual usage and partial statuses |
| S8 | Accepted claim audit | SCIENTIFIC_AUDIT.md; no automatic ground-truth or operational safety claim |
| S9 | Passed | 70 backend, 3 component, 24 browser plus 1 auth browser; static checks and production frontend build |
| S10 | Configuration and instructions delivered | compose.production.yaml, nginx TLS configuration, DEPLOYMENT.md; containers/TLS/external host not executed |

Additional verification: 23 frozen camera/CRISM files hash verified; source
coverage, AI inference, no-data behavior, restart persistence, isolated migration,
offline NASA-cache replay and full Alpha→evidence→verification→Beta→future-EVA
acceptance included in the tests. Regression tests use temporary stores and
services; existing saved missions are not reset. Deprecation warnings from
Starlette/PyTorch/raster affine multiplication remain, with no test failures.

Targeted UI improvements: full-width mission map, expanded map view with Escape,
route/evidence controls, source layer selection, direct map navigation from other
screens and a visible observation→review→route→memory workflow. The cached map
covers the local mission area, not all of Mars. No unsupported pixels were filled.

Limits requiring future scientific work: reliable terrain classifier, validated
camera footprints/mechanism pose, CRISM map-origin reconciliation/full spectral
analysis, denser terrain modeling and operational policy validation. Account
provisioning, TLS certificates, hosting and backup operational rehearsal require
operator-owned infrastructure. No real credentials are checked in or seeded.

This audit applies to the source hashes in docs/science/final-source-hashes.json.
The source snapshot and test results are implementation evidence, not an external
scientific or security assessment. Earlier numbered gates/status counts are
historical snapshots superseded by this report and NASA_SOURCE_MATRIX.md.
