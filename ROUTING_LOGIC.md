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
