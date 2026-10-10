# S3 review — prototype ingestion accepted with explicit uncertainty

Reviewed parser, exact-clock resolver, bounded cache, numeric decoder, API source
context and Evidence Inspector against the S3 request and official PLACES SIS.
This passes the ingestion/uncertainty workflow, not exact image georegistration.
Both products/labels are genuine cached calibrated PDS collection inputs.

Review fixes: scope mission clocks separately from mini-header clocks; preserve
Mastcam discrepancy; reject negative RMC/wildcards and ambiguous intervals;
verify frozen source hashes before numeric processing; validate array axis order;
require partition 1 for these PLACES tables; wrap long provenance in the inspector.
No mission observations or verification decisions are created by ingestion.

Verification: 60 backend tests pass, including six camera tests; three component
and 21 browser tests pass; Ruff, mypy (explicit package bases), ESLint and
TypeScript pass; production build passes. Cached-source reproduction verifies
15 frozen files. Numeric tests compare calibrated pixels to original array bytes.
Diagnostic was visually inspected; anchor labels were separated after overlap.

Required limitations remain visible: Mastcam observation clock has no exact
match, exact mechanism validity is unavailable, best tactical orientation is a
drive anchor with wildcard pose, and reliable camera footprints are unavailable.
Uncertainty is unknown, not zero. These source/registration aspects remain
PARTIALLY_VALIDATED in the final matrix. No centimeter coverage or fully
scientifically validated system claim is justified. Continue to S4.
