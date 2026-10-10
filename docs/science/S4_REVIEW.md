# S4 review — CRISM processed context

2026-10-10: prototype workflow accepted. Official MTRDR product
FRT000047A3_07_BRTANJ_MTR3 is a derived TAN browse (R2529/R1330/R770),
not a mineral identification. Eight frozen source files are hash verified.
The source PNG RGB values match the PDS IMG; its alpha mask defines coverage.
The target falls at valid PDS pixel (298,795); the southern mission edge has
missing coverage. The PDS and ENVI origins disagree by one 18 m pixel; the
pipeline retains this discrepancy and uses the PDS mapping explicitly.
The full hyperspectral cube is not downloaded or represented as processed.

Four CRISM tests pass: actual source product/target, geometry/provenance,
missing context, and API continuity. Together with the independently corrected
DTM regression, 13 targeted tests pass; Ruff passes. Evidence Inspector browser
provenance and narrow-screen checks passed in the prior S4 implementation run.
Source registration remains PARTIALLY_VALIDATED. No mineral identity is inferred.

S1 correction: native sample selection now matches GDAL PDS pixel centers.
Prior derived artifacts are archived under data/processed/history/s1-grid-v1.
Existing mission routes and decisions were not recomputed or overwritten.
Proceed to S5, retaining these limitations.
