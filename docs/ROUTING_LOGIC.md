# Routing logic

The route engine is deterministic eight-neighbor A* on a 40 m local Mars metric grid (31×21 nodes). The heuristic is straight-line metric distance; extra costs are nonnegative. Distance is computed from path geometry, not from Web Mercator rendering or Earth geographic libraries.

Each edge cost is distance + terrain penalty + slope penalty + uncertainty. Default orbital soil is an illustrative assumption with uncertainty 0.15×distance. Confirmed ground-supported nodes use uncertainty 0.02×distance; soil adds zero terrain cost, bedrock 0.1×distance, sand 0.5×distance, rough terrain 3×distance, large rocks 8×distance, unknown 1×distance. Obstacle-rich terrain blocks intersecting edges, including diagonal corner crossings. These weights express a demonstration policy, not NASA-approved physiological limits.

Only confirmed persistent ground evidence contributes permanent cost. Provisional, rejected, expired dynamic and orbital imagery alone do not create new obstacle footprints. The active route can be marked challenged while awaiting human review. Confirmation recomputes affected missions; routes that differ in geometry or cost are versioned and keep their predecessors. Future EVAs inherit verified footprint evidence.

Without a validated DEM, slope is explicitly unavailable and excluded. `python -m scripts.process_dem local_mars_dem.tif data/processed/slope.npz --product-id <id> --source-url <https-url>` aligns a single-band, meter-elevation Mars product to the grid and computes slope in degrees using metric gradients. It refuses Earth CRS, absent CRS and no coverage. Set `MARSENSE_SLOPE_PATH` before initializing a new mission database. Configured slopes add distance×degrees/10; slopes above 20° are excluded by the illustrative policy, and missing slope increases uncertainty. MOLA's coarse resolution cannot establish foot-scale hazards or justify such a threshold for actual operations.

The current candidate DTM cache has no valid data in this mission extent, so the demo excludes slope. No elevation is synthesized. Changing slope policy/data for an existing database requires explicit route recomputation and an auditable mission event; startup intentionally preserves existing routes.

No path returns NO_ROUTE and a stop/review explanation. The WHY text is assembled from evidence class, verified reviewer, footprint centroid, old/new distance and cost policy; it uses no generated safety claims.
