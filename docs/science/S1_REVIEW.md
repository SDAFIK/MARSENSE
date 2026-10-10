# S1 review

Reviewed scope: coverage ingestion, Mars CRS, elevation/slope separation, routing loader, raster display coordinates and alignment diagnostic. Fixed findings: partial coverage accepted by loader/processor; CRS metadata not validated by loader; HiRISE displaying with CTX crop corners.

Official source: https://hirise.lpl.arizona.edu/dtm/ESP_045994_1985 . Native metadata comes from the attached PDS label, not rounded catalog display values. Exact raw ranges and source hashes remain in the manifest. Operational grid coverage is 100%; sampled elevations -2598.258 to -2562.159 m, derived slopes 0.037 to 13.364 degrees. These are sampled planning values, not foot-scale validation.

Checks: 45 backend tests, 3 component tests, 21 browser tests pass; Ruff, mypy, ESLint and TypeScript pass. Diagnostic PNG visually inspected: route aligns with identical node centers in elevation/slope panels. Production build result recorded in STATUS.md. Tests use temporary databases; no live services were restarted.

Review boundary: slope must be explicitly configured for a new run. Legacy saved routes retain their original cost facts. Missing/invalid configured DEM fails; an intentionally unconfigured DEM stays visibly unavailable. Prototype slope routing weights are documented MARSENSE configuration. S1 accepted for the research prototype, with coarse sampling limitations. This does not certify later scientific gates.

Additional hardening after review: NPZ content hash and 40 m cell-size metadata checked at load. Six S1-focused tests pass, including offline byte-identical reproduction and altered-cache detection; the original 45-test regression remains a timestamped checkpoint.

Correction notice (2026-10-10): the numerical range in the initial review above
is historical and predates the independent GDAL pixel-center correction. Current
processed source is data/processed/hirise-covering-slope.json; slope spans
0.0371615 to 13.3302622 degrees. Original outputs are archived under
 data/processed/history/s1-grid-v1. Nine current S1 tests pass.
