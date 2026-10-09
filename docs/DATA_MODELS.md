# Data models

Canonical definitions are `backend/domain.py`; API schemas are generated at `/openapi.json`. All entities reject extra fields.

| Entity | Responsibility |
|---|---|
| Region | Original interpretation, current summary, geometry, knowledge state, complete evidence history |
| Observation | Original upload reference/hash, separate sanitized model-input hash, source note, timestamp, astronaut, mission, footprint, original model output |
| Evidence | Expected/observed values, quality, discrepancy, mission consequence, verification, reviewer/note, persistence/expiry, original observation link |
| MissionAssumption | Statement, route/target dependencies, supporting/challenging evidence, status |
| Route / RouteSegment | Versioned coordinates, distance, cost components, dependency/evidence links, factual explanation |
| MissionEvent | Durable observation/verification/rerouting/inheritance timeline |
| ScienceTarget | Objective, illustrative position and source note |
| Mission | Habitat, target, astronaut, active route and inherited evidence |
| AstronautState | Name, position, mission and human decision authority |

Knowledge states: ORBITAL_ONLY, PROVISIONAL, GROUND_OBSERVED, MULTI_SOURCE_CONFIRMED, CONFLICTING, SUPERSEDED. The last two confirmation/supersession distinctions are reserved in the schema; independent multi-source certification and explicit evidence supersession workflows are not yet implemented.

Verification states: PROVISIONAL, CONFIRMED, REJECTED, NEEDS_MORE_EVIDENCE. Final confirmed/rejected decisions are immutable and repeat requests are idempotent only for the same decision. Low-confidence terrain requires explicit human identification before confirmation. Footprints are validated closed, nonempty, non-self-intersecting single polygons inside the 1200×800 m mission extent, confined to one operational region.

Permanent knowledge is footprint-specific. Region-level “Ground Observed” is a summary, never authorization to treat the whole region as observed. Expected terrain uses confirmed ground interpretation only when its footprint covers the new observation footprint. Dynamic visibility records have expiry and never become permanent terrain.
