# Domain model and lifecycle

All coordinates below are local Mars meters; scientific CRS in ROUTING_LOGIC.md.
Entity definitions currently live in backend/domain.py. Proposed contract fields
are called out explicitly; they are requirements, not implemented capabilities.

## Shared vocabulary

| Concept | Meaning / ownership |
| --- | --- |
| Observation | What was captured, where, when, by whom, with original asset hash and supported footprint |
| Inference | Versioned model output from those bytes; uncalibrated until validated |
| Interpretation | Terrain hypothesis associated with a supported footprint; preserves expected prior and human identification |
| Discrepancy | Structured comparison of expected and observed interpretations |
| Consequence | Affected mission dependencies and provisional warning derived from geometry and assumptions |
| Decision | Human reviewer, action, rationale and time; authorizes a verified interpretation |
| Region | Spatial container with prior, current summary, knowledge state and evidence history |
| MissionAssumption | Statement supported by evidence with explicit dependent segment/target edges |
| Route / RouteSegment | Versioned path and exact segment geometries, assumed terrain, cost and supporting evidence |
| MissionEvent | Auditable recorded change linked to evidence and a mission |
| ScienceTarget | Source-linked objective and location; illustrative demo target clearly marked |
| Mission / AstronautState | EVA, human authority, habitat, active route, position and inherited evidence |

## States

Knowledge: ORBITAL_ONLY, PROVISIONAL, GROUND_OBSERVED,
MULTI_SOURCE_CONFIRMED, CONFLICTING, SUPERSEDED.

Verification: PROVISIONAL, CONFIRMED, REJECTED, NEEDS_MORE_EVIDENCE.

Discrepancy: MATCH, MINOR_DIFFERENCE, SIGNIFICANT_DIFFERENCE,
CONFLICTING_EVIDENCE, INSUFFICIENT_EVIDENCE.

Current route states: ACTIVE, CHALLENGED, SUPERSEDED, NO_ROUTE. UI labels ACTIVE
as nominal and a new route as alternative. A future recalculation state represents
work in progress; it must not be stored as a successful computed route.

Every ground evidence item begins provisional. Rejection remains auditable and
does not alter prior/current verified terrain. NEEDS_MORE_EVIDENCE remains pending.
Confirmed persistent evidence projects to GROUND_OBSERVED inside its footprint.
Two independent sources confirming the **same footprint and property** may project
MULTI_SOURCE_CONFIRMED; a second replay of the same image is not independent.
Conflicting verified/provisional interpretations do not silently supersede one
another. SUPERSEDED retains old interpretation/history and explicit replacement
references. The current code declares these states but does not implement all
transitions; independent multi-source/supersession needs acceptance tests.

## Evidence contract

Existing fields: identity; region/mission/observation references; source and source
type; timestamp; local location; spatial footprint; observation type; expected and
observed terrain; model output and score; verification state; persistence type;
valid_until; raw asset reference; discrepancy; consequence; reviewer/time/note;
derived stale flag. Observation additionally stores asset_sha256, metadata_note,
original_asset_reference and model_input_sha256. New uploads hash/store original
bytes separately from the sanitized display/model input. Older records may lack
the optional original reference; provenance absence must remain explicit.

Required additions before final audit: typed source mission/instrument/product,
archive URL/identifier, acquisition timestamp, source resolution/CRS, processing
history, observed/derived/simulated classification, model checksum/preprocessing,
calibration status and immutable human interpretation/decision records.
The global manifest alone is not enough to attach exact provenance to each upload
or interpretation. Preserve original uploaded bytes separately from a sanitized
display derivative, and record both hashes.

## Invariants and examples

- A 160 × 160 m camera footprint changes only supported local cells/edges, never
  the entire 320 × 800 m corridor summary area.
- A rough candidate with low confidence can warn if it intersects the active
  route, but confirmation needs explicit human terrain identification.
- A failed model or UNKNOWN terrain cannot become a verified terrain fact merely
  because a numeric score is high.
- Dust/visibility carries expiry; confirming it creates a temporary operational
  record, never permanent soil/boulder knowledge.
- Route versions reference exact segment and assumption identities for their
  mission; missions cannot share a segment whose route_id belongs to another EVA.
- Reviewer/note constraints apply after trimming. Geometry is finite, closed,
  valid, nonempty, within operational bounds and contained in a mapped region.
- Committed evidence survives a fresh process, not just a frontend reload.

## Persistence

Current EntityRow uses id/kind/validated JSON payload; SQLAlchemy typed accessors
reconstruct Pydantic entities. BEGIN IMMEDIATE serializes writes; rollback prevents
half-verified updates. Add payload/schema versioning and migration tests before
changing persisted fields. No migration may delete NASA priors or previous EVAs.

## Scenario checks and transition ownership

| Scenario | Stored state / allowed projection | Owner |
| --- | --- | --- |
| Orbital-only Area 14 before EVA | Immutable NASA source plus explicitly illustrative low-obstacle interpretation; no ground verification | Prior knowledge |
| Actual image/model result matches expectation | Provisional observation/inference retained, MATCH, no interrupt or terrain mutation | Perception then discrepancy |
| Minor difference away from mission dependencies | Retained provisional evidence, no mission alert | Consequence |
| Weak rough/unknown result intersects Alpha | INSUFFICIENT_EVIDENCE with possible provisional safety warning; no learned terrain | Consequence; human review required |
| Human confirms known persistent terrain | Append decision/interpretation, footprint-only GROUND_OBSERVED, assumption/event/route reevaluation atomically | Verification application service |
| Human supplies unknown even for strong model output | Reject persistent confirmation; preserve original provisional observation and inference | Verification |
| Human rejects or requests more evidence | Rejection retained without knowledge change; more-evidence remains pending | Verification |
| Dynamic dust is confirmed then expires | Temporary operational record; stale history remains, no permanent terrain or inherited condition | Freshness projection |
| Independent evidence agrees / disagrees | Agreement can support MULTI_SOURCE_CONFIRMED only for supported property/overlap; disagreement remains explicit CONFLICTING | Knowledge projection |
| Valid replacement interpretation supersedes old one | Retain source/old decision and explicit replacement reference; never edit final decision in place | Knowledge/version history |
| Routing or commit fails during confirmation | Roll back the combined mutation; prior saved state and route remain; report failure rather than confirmation success | Transaction boundary |
| Future EVA after restart | Queries committed persistent verified footprint knowledge; pending/rejected/stale dynamic evidence is not inherited as terrain | Mission memory |

Required event vocabulary covers mission plan, astronaut position/area entry,
image capture, inference completion/failure, discrepancy evaluation, assumption
challenge, review decision, knowledge update and route reevaluation/failure.
Events retain mission/evidence/decision/assumption/route references, timestamp and
saved outcome. Current coarser event strings are implementation observations,
not permission to omit the traceable final timeline.

The target Interpretation and Decision records are logically distinct even if
initial storage uses typed JSON aggregates. Observation.model_output is immutable;
human_terrain changes the reviewed interpretation, not the stored inference.
Region.knowledge_state is a coverage summary, not authority to reclassify every
point within the region. These distinctions resolve ambiguous uses of "truth",
"confirmed", "safe", "raw" and "known" in implementation descriptions.
