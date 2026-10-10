# Mars geometry and deterministic routing

R08/R14: scientific analysis is local metric Mars geometry; MapLibre's rendering
projection is only presentation. No browser/Earth/Web Mercator distances feed
the mission domain.

## Coordinate contract

Origin: longitude 77.45 E, latitude 18.44 N. Radius R = 3,396,190 m, matching the
selected Mars Trek IAU2000 spherical service convention. For bounded Jezero use:

```
x = R × radians(lon − 77.45) × cos(radians(18.44))
y = R × radians(lat − 18.44)
lon = 77.45 + degrees(x / (R × cos(radians(18.44))))
lat = 18.44 + degrees(y / R)
```

Authoritative code: backend/spatial.py ANALYSIS_CRS including negative y_0 origin
offset. Mission footprint/route coordinates use x∈[0,1200], y∈[0,800] meters.
Convert all source rasters/overlays using their actual label CRS/datums, retaining
source transformation metadata. Spherical analysis is a declared local prototype
approximation, not a universal Mars reference frame. Verify against product
geotransforms and known distances. Test origin/roundtrip, longitude scale,
latitude scale, route polyline lengths and footprint/segment intersections.

## Grid and cost

Current A*: 40 m spacing, 31×21 nodes, eight neighbors, Euclidean heuristic in
meters and deterministic heap tie breaking. Habitat (120,400), target (1080,400)
are grid nodes, so Alpha is 960 m. General non-grid endpoints must not be silently
rounded without storing actual connecting edges and testing their distance.

Each edge cost is distance + terrain + slope + uncertainty. Current terrain
multiplier per meter: soil 0, sand 0.5, bedrock 0.1, large rocks 8, rough 3,
unknown 1, confirmed obstacle-rich blocked. Uncertainty multiplier: 0.15
orbital-only, 0.02 ground-observed. All are **project-defined prototype costs**,
not NASA standards, mechanical resistance, time or safety probabilities.

Current demo slope term is excluded because there is no covering valid DEM.
Concurrent work added an optional MARSENSE_SLOPE_PATH and tested DEM adapter:
slope adds distance×degrees/10; >20° blocks by prototype policy and NoData adds
0.5×distance uncertainty. These source constants still need central configuration.
A displayed zero slope cost means unavailable/excluded, never measured flat
surface. Gate 4/6 requires
real slope input with NoData handling, units, configurable prototype multiplier
and tested derivation. Add sensitivity tests to show how a weight changes the
chosen path without claiming physical validation.

Only confirmed **persistent** non-orbital terrain updates costs. No provisional,
rejected, expired dynamic or failed inference may change permanent terrain costs.
Confirmed blocked footprints test the full edge, preventing diagonal corner
cutting. Other terrain costs currently sample the destination node; improve
to account for supported edge intersection lengths, especially sub-grid rough
patches. Outside the footprint retain prior/uncertainty. Never globally assign
the region summary's newest terrain to every cell.

## Dependencies and route revisions

The low-obstruction Area 14 assumption must name supporting prior evidence and
exact dependent Alpha segment 3, target access and illustrative retraced return
corridor. Geometry intersection resolves affected segments before consequence.
Current consequence intersects actual segment geometries and fresh seeds use
EVA-specific IDs. Target-only/access dependencies and old-store migration remain
incomplete. Revisions must carry stable mission-scoped segment identities.

Before verification Alpha is challenged, coordinates/cost unchanged. After
confirmation reevaluate all relevant missions against verified evidence. Preserve
Alpha as superseded, create Beta only if path/cost changed, record evidence and
cost breakdown and compute actual distance delta; do not hardcode +240 m from
the illustrative prompt. Future EVA inherits the same verified footprint.

WHY references prior expectation, observed/human interpretation, evidence ID,
assumption/segment, verification reviewer, changed costs and real distance tradeoff.
No generative model is required to phrase these stored facts.

If no path exists: retain the previous path for context, clearly mark it affected,
record NO_ROUTE / failed reevaluation and require planning review. Do not replace
the visible route with a fake path or show zero meters as a successful traverse.
An algorithm error during verification must roll back the combined transaction
and report failure with prior saved state retained. A valid no-path result is
distinct from an execution failure and must be stored with explicit planning status.

## Scientific completion S1 — current checkpoint

Official covering product: DTEEC_045994_1985_046060_1985_U01, selected from
https://hirise.lpl.arizona.edu/dtm/ESP_045994_1985 . Attached PDS metadata
and source byte hashes are retained in data/processed/hirise-covering-slope.json.
Native coverage bounds, equirectangular planetocentric source CRS, 1.0096633268711 m
pixel size, IEEE missing constant and Mars 2000 equipotential vertical datum
are recorded. Native source radius differs from the mission analysis radius;
sampling explicitly converts through planetocentric longitude/latitude.

Reproduce with `.venv\Scripts\python.exe -m scripts.cache_hirise_dtm`; cached
exact PDS ranges enable offline reuse. Raw range bytes, sampled elevation TIFF
and derived slope NPZ remain separate. All 651 operational cells have valid
elevation. Ingestion and configured slope loading now reject incomplete
operational coverage; loader requires matching Mars analysis CRS metadata.
Missing configured files are errors. Empty slope configuration remains visibly
unavailable rather than measured zero slope.

Enable explicitly for a new/local validation run using
`MARSENSE_SLOPE_PATH=data/processed/hirise-covering-slope.npz`. Existing services
and saved routes were not silently restarted or rewritten. MARSENSE prototype
route weights: slope cost = edge length * slope degrees / 10; slopes above
20 degrees excluded. These are configuration choices, not NASA EVA-safe limits.

Diagnostic: docs/science/s1-dtm-alignment.png and s1-route.geojson, generated
by `python -m scripts.debug_dtm`. White route overlays the identical 40 m
node grid on elevation and slope. GeoJSON rendering longitude/latitude is
presentation only; metric coordinates remain in feature properties. HiRISE
rendering now uses its own actual crop bounds; CTX/HiRISE switching updates
the image coordinates together with the URL. No product redesign.

Checks cover real cached coverage and known samples, grid/route intersection,
partial no-data refusal, CRS mismatch, independent PROJ round trip, synthetic
plane gradient sanity and cost changes. The coarse 40 m slope cannot validate
foot-scale obstacles or operational EVA safety. Complete regression results
are recorded in STATUS.md after execution. S2 remains pending until S1 review passes.
