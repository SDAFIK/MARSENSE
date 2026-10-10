# Scientific claim audit — S8

2026-10-10. Review scope: backend and frontend source at this checkpoint,
source manifests, MODEL_CARD.md and the eight-source matrix. Toolkit code-review
and research workflows applied. Search terms: safe, real-time, live, hazard
probability, radiation, weather, mineral identity, soil strength, oxygen,
guaranteed route, ground truth, NASA-approved and NASA-certified.

Fixed findings:
- Mission Control's "ground truth" heading implied more certainty than visual
  evidence supports. Changed to ground evidence and human-reviewed observation.
- Retired evidence could appear in current map/memory counts. Added explicit
  superseded references to snapshots and excluded them from current overlays and
  current-memory counts while preserving the archive and final decisions.
- Route support IDs could retain an old interpretation when cost/geometry stayed
  equal. Route revision now also compares evidence support.
- Dynamic fallback-map footprints lacked expiration filtering. Added an expiring
  render clock; the WebGL source also refreshes on that clock.
- CRISM label versus ENVI mapping disagreement retained explicitly; no automatic
  mineral output, and source pixel/coverage remain inspectable.
- Native DTM pixel-center correction is retained with archived prior artifacts;
  historical pre-correction review values must not be used as current measurements.

Claim classification:
OBSERVED: actual calibrated camera arrays and rover localization products.
DERIVED: orbital mosaics, DTM, resampled elevation/slope, CRISM browse and coverage.
MODELED: segmentation outputs and prototype weighted route costs.
SIMULATED/DEMO: replay annotation, illustrative mission target/habitat/footprint.
HUMAN INTERPRETATION: signed reviewer terrain decision, kept separate from model.

Retained with scope: PROVISIONAL SAFETY ALERT is a mission dependency warning,
not a predicted hazard probability or safety certification. The map is local
cached imagery, not a real-time planet-wide feed. No measured radiation/weather,
oxygen budget, bearing capacity, mineral identity or guaranteed safe route exists.
Static frozen specification language is a requirement/history, not an implemented
measurement; current status and source matrix qualify actual behavior.

Open scientific limits: low model quality (classification disabled), incomplete
camera/geometric registration, partial CRISM coverage and one-pixel origin
uncertainty, coarse DTM sampling, no operational slope policy validation.
No unresolved high-severity unsupported claim found within this review scope.
S8 claim-audit gate accepted; proceed to complete S9 regression.
