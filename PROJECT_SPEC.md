# MARSENSE Engineering Instructions

You are the senior software engineer responsible for implementing MARSENSE for the NASA Space Apps Challenge.

The approved product specification is frozen. Do not redesign the product, invent unrelated features, or replace core architectural decisions merely because another implementation seems easier.

Your responsibility is to implement the approved system with high engineering quality, strong UX, deterministic demo behavior, comprehensive tests, clear documentation, and graceful failure handling.

---

# 1. PRODUCT IDENTITY

Product name: MARSENSE

Product concept: The Living Mars Map

Core vision:

NASA tells us what we expect.
Astronauts show us what is actually there.
MARSENSE learns the difference.

Core loop:

NASA prior knowledge
→ mission assumptions
→ astronaut observation
→ AI perception
→ expected-vs-observed comparison
→ discrepancy classification
→ mission consequence analysis
→ human verification
→ persistent map update
→ route recalculation
→ future explorer inherits knowledge

This loop is the highest-priority product behavior.

---

# 2. CORE PRODUCT PRINCIPLES

1. NASA prior evidence must never be silently overwritten.

2. AI output is evidence, not truth.

3. Important observations begin as provisional.

4. Persistent map changes require verification.

5. Safety-relevant discrepancies may create immediate provisional alerts.

6. Every evidence item must preserve provenance.

7. Ground observations apply only to their supported spatial footprint.

8. Observation and interpretation must remain separate concepts.

9. Dynamic environmental observations must not become permanent terrain facts.

10. Astronauts retain final decision authority.

11. An LLM may explain structured results but must not invent mission measurements or safety values.

12. Every important system decision must be explainable from stored evidence.

13. Every verified observation must remain available for later missions.

14. The application must remain functional during the final demo even if external NASA services are temporarily unavailable.

15. Do not introduce new features unless they directly support the approved core loop.

---

# 3. PRIMARY MVP

The MVP must demonstrate one complete end-to-end scenario:

1. Display NASA-derived Jezero prior map.
2. Display Habitat, science target, and Route Alpha.
3. Select/upload a ground observation image.
4. Run Mars terrain perception.
5. Compare expected terrain with observed terrain.
6. Detect a significant discrepancy.
7. Determine that Route Alpha depends on the challenged terrain assumption.
8. Raise an understandable mission-relevant alert.
9. Allow human verification.
10. Persist the verified evidence.
11. Update local knowledge state.
12. Update terrain traversal cost.
13. Recalculate route.
14. Display Route Beta.
15. Show a clear explanation of why the route changed.
16. Reload/restart the application.
17. Show that the verified evidence remains.
18. Demonstrate a future astronaut benefiting from the previous EVA.

This workflow must work flawlessly before optional features are implemented.

---

# 4. FIXED TECHNICAL ARCHITECTURE

Use a monorepo.

Preferred structure:

marsense/
  AGENTS.md
  PROJECT_SPEC.md
  ARCHITECTURE.md
  NASA_DATA.md
  DATA_MODELS.md
  API_CONTRACT.md
  AI_PIPELINE.md
  ROUTING_LOGIC.md
  UI_SYSTEM.md
  DEMO_SCENARIO.md
  TEST_PLAN.md
  README.md

  frontend/
  backend/
  ai/
  data/
    nasa/
    processed/
    demo/
  scripts/
  tests/
  docs/

Frontend:
- Next.js
- React
- TypeScript strict mode
- Tailwind CSS
- MapLibre GL preferred; Leaflet acceptable only if justified
- accessible components
- responsive desktop-first mission-control experience

Backend:
- Python
- FastAPI
- Pydantic
- SQLAlchemy or equivalent typed ORM

Database:
- PostgreSQL + PostGIS when straightforward
- SQLite + GeoJSON is allowed for a deterministic hackathon fallback
- persistence is mandatory

AI:
- PyTorch
- OpenCV
- Mars terrain segmentation/classification
- AI4Mars-compatible data/model pipeline
- model inference exposed through a backend service interface

Geospatial:
- Rasterio
- GDAL where required
- GeoPandas
- Shapely
- NumPy
- NetworkX or dedicated A* implementation

Testing:
- pytest
- frontend unit/component tests
- Playwright end-to-end tests
- linting
- type checking

Deployment:
- Dockerized where practical
- deterministic local/demo deployment
- production-ready environment variables
- no secrets committed

---

# 5. NASA DATA STACK

Core:

1. Mars Trek CTX controlled Jezero mosaic
   - regional map/context

2. Mars Trek HiRISE controlled Jezero mosaic
   - high-resolution local imagery

3. HiRISE DTM
   - elevation
   - slope
   - routing cost

4. MOLA MEGDR
   - global/regional elevation fallback

5. Perseverance Navcam calibrated imagery
   - simulated astronaut ground observation

6. Perseverance Mastcam-Z calibrated imagery
   - detailed ground/science imagery

7. Mars 2020 PLACES
   - rover observation location/orientation

8. AI4Mars
   - Mars terrain AI training/validation

9. CRISM processed products
   - science/mineral context

Secondary only after MVP:
- MEDA
- Mars Climate Sounder
- MARCI
- SuperCam
- SHARAD
- SPICE

Do not download giant archives unnecessarily.
Create small reproducible data-ingestion scripts and cached processed demo datasets.

---

# 6. MAP / COORDINATE RULES

Do not treat Mars as Earth.

Do not use Earth-radius distance calculations.

Do not silently rely on Web Mercator for scientific route computations.

Frontend map projection may be chosen for rendering convenience, but backend spatial analysis must use Mars-appropriate coordinates.

For the Jezero operational area:

- use the projection metadata of the selected NASA products;
- prefer compatible Mars equirectangular/local projected coordinates;
- perform route/distance calculations in local metric x/y space where possible.

Keep imagery, DEM, science regions, routes, observations, and evidence footprints aligned in the same analysis CRS.

Add tests for coordinate transforms and known distances.

---

# 7. KNOWLEDGE MODEL

Every region must support:

- prior interpretation
- current interpretation
- knowledge/evidence state
- evidence history
- update timestamp
- geometry/spatial footprint

Recommended knowledge states:

ORBITAL_ONLY
PROVISIONAL
GROUND_OBSERVED
MULTI_SOURCE_CONFIRMED
CONFLICTING
SUPERSEDED

Never delete historical evidence because a newer interpretation exists.

---

# 8. REQUIRED DOMAIN ENTITIES

Implement typed domain entities for at least:

Region
Evidence
Observation
MissionAssumption
Route
RouteSegment
MissionEvent
ScienceTarget
Mission
AstronautState

Evidence should include:

id
region_id
source
source_type
timestamp
geometry/location
spatial_footprint
observation_type
observed_value
model_output
model_confidence
verification_state
persistence_type
raw_asset_reference

MissionAssumption should include:

id
statement
status
supporting_evidence
dependent_route_segments
dependent_targets
created_at
updated_at

---

# 9. OBSERVATION PROCESSING LOGIC

The authoritative logical sequence is:

receive observation
→ validate metadata
→ locate spatial region
→ retrieve prior/current knowledge
→ run AI perception
→ store observation and model output
→ compare observed vs expected
→ classify discrepancy
→ discover mission dependencies
→ calculate mission consequence
→ trigger provisional safety alert when appropriate
→ otherwise store silently when irrelevant
→ present mission-relevant discrepancy
→ await confirmation/verification
→ persist verified interpretation
→ challenge affected assumptions
→ update traversal costs
→ reroute affected routes
→ append mission event
→ update Living Map
→ make knowledge available to future missions

Do not bypass steps for convenience.

---

# 10. DISCREPANCY STATES

Use understandable categories:

MATCH
MINOR_DIFFERENCE
SIGNIFICANT_DIFFERENCE
CONFLICTING_EVIDENCE
INSUFFICIENT_EVIDENCE

Avoid fake scientific precision.

Numeric probabilities may exist internally where justified, but the UI must not present arbitrary values as scientific certainty.

---

# 11. CONSEQUENCE GATE

A discrepancy does not automatically interrupt the astronaut.

Check whether it affects:

- current route
- return corridor
- safety assumption
- science objective
- target accessibility
- mission time estimate
- resource-dependent logic

If no mission dependency exists:
store the evidence silently.

If a safety-critical dependency may be affected:
issue a clearly labeled PROVISIONAL safety alert.

If mission relevant but not safety critical:
present the discrepancy and decision options.

---

# 12. ROUTING

MVP routing should remain understandable and deterministic.

Use a raster/grid or graph representation.

Each traversable region/cell receives costs such as:

distance cost
terrain cost
slope cost
knowledge/uncertainty cost

Baseline conceptual equation:

RouteCost =
DistanceCost
+ TerrainCost
+ SlopeCost
+ UncertaintyCost

Use A* unless a better justified deterministic algorithm is needed.

Confirmed obstacles may be assigned a very high cost or blocked.

Ground-observed safe terrain may receive less uncertainty penalty than orbital-only terrain.

Never claim the resulting route is NASA-certified or physically guaranteed safe.

---

# 13. AI PERCEPTION

MVP AI focuses on visually defensible terrain properties.

Suggested classes:

soil
sand
bedrock
large rocks
rough terrain
obstacle-rich terrain
unknown

Do not use ordinary camera images to claim:

- exact mineral composition
- radiation
- toxicity
- subsurface ice
- mechanical soil strength

Those require separate sensors.

Model output format must be structured and testable.

Model failure must degrade gracefully.

Low-confidence predictions must not automatically become persistent map knowledge.

---

# 14. HUMAN VERIFICATION

Operationally important updates require verification.

MVP verification:
manual astronaut confirmation.

Support states such as:

PROVISIONAL
CONFIRMED
REJECTED
NEEDS_MORE_EVIDENCE

Future confirmation methods may include:

second image
different viewpoint
stereo
scientific instrument
second astronaut

---

# 15. PERSISTENT VS DYNAMIC EVIDENCE

Persistent examples:
boulder field
trench
terrain roughness
bedrock exposure
geological feature

Dynamic examples:
dust
visibility
temperature
weather/environment

Dynamic observations require timestamps/validity windows and must expire or become stale.

---

# 16. UI DESIGN SYSTEM

Visual direction:

- scientific
- modern
- mission-control inspired
- restrained
- highly readable
- map-first
- professional
- not game-like
- not generic AI dashboard

Avoid:

- excessive glassmorphism
- random gradients
- oversized glowing cards
- excessive rounded corners
- neon cyberpunk style
- decorative animations
- unnecessary 3D
- meaningless sci-fi terminology

Information hierarchy:

1. current mission state
2. map
3. important new evidence
4. consequence
5. required action
6. detailed provenance on demand

Animations should communicate state transitions, especially:

ORBITAL_ONLY
→ PROVISIONAL
→ GROUND_OBSERVED

and

Route Alpha
→ challenged
→ Route Beta

No animation purely for decoration.

---

# 17. REQUIRED SCREENS

1. Landing / Mission Introduction
2. Mission Control
3. Astronaut View
4. Evidence Inspector
5. Exploration Memory / Timeline
6. Before vs After knowledge comparison

Primary hero message:

A Mars map that learns from every astronaut.

Mission Control must remain the main product surface.

---

# 18. BEFORE / AFTER EXPERIENCE

This is a mandatory competition feature.

Show clearly:

BEFORE EVA:
expected terrain
orbital-only evidence
Route Alpha

AFTER OBSERVATION:
ground evidence
updated knowledge state
affected route
Route Beta

The judge must understand the system without reading documentation.

---

# 19. DEMO RELIABILITY

The final demo must not depend entirely on:

- live NASA servers
- live third-party APIs
- live AI downloads
- external network connectivity

Cache the exact demonstration data locally.

Preserve scripts that prove where the cached NASA data originated.

Support a deterministic demo mission.

Real pipeline and deterministic demo may coexist, but the demo must never fake capabilities that do not exist in the code.

---

# 20. TEST REQUIREMENTS

No feature is complete without tests.

Required core cases:

A.
Expected smooth terrain
Observed smooth terrain
→ MATCH
→ no alert

B.
Minor difference outside mission route
→ store silently

C.
Significant obstacle discrepancy intersecting Route Alpha
→ mission alert

D.
Potential safety consequence with weak model confidence
→ provisional safety alert
→ no permanent update

E.
Confirmed observation
→ knowledge becomes ground-observed
→ assumption changes
→ route recalculates

F.
Application restart/reload
→ verified knowledge persists

G.
Rejected observation
→ prior interpretation remains current
→ rejected evidence remains auditable

H.
NASA external service unavailable
→ cached demo still works

Add API, unit, integration, geospatial, and end-to-end tests.

---

# 21. CODE QUALITY

Use:

- TypeScript strict mode
- typed Python
- clear module boundaries
- small functions
- domain-driven names
- dependency injection where useful
- structured logging
- central error handling
- consistent configuration
- environment validation
- explicit API schemas

Avoid:

- giant components
- giant service files
- hidden global state
- duplicated business logic
- magic constants
- arbitrary delays
- mock values escaping into production code
- TODO-driven incomplete critical paths

---

# 22. ERROR HANDLING

Every critical integration must have:

loading
success
empty
stale
partial
error
offline/cached

states where relevant.

User-facing failures must explain what remains usable.

Never show stack traces to normal users.

Log internal details for debugging.

---

# 23. SECURITY

Never commit credentials.

Use `.env.example`.

Validate uploaded files.

Limit upload size/type.

Sanitize all user-supplied strings.

Do not execute user-uploaded content.

Configure CORS explicitly.

Do not expose filesystem paths.

Protect production endpoints appropriately.

---

# 24. PERFORMANCE

Do not send raw multi-hundred-megabyte NASA datasets to the browser.

Preprocess:

GeoTIFF → web-friendly tile/raster representation
CRISM → selected GeoJSON/science overlay
PLACES → normalized JSON/DB rows
DEM → server-side/local derived slope and routing data

Lazy-load heavy map layers.

Cache static NASA-derived data.

Keep mission interactions responsive.

---

# 25. DOCUMENTATION

Maintain:

README.md
PROJECT_SPEC.md
ARCHITECTURE.md
NASA_DATA.md
DATA_MODELS.md
API_CONTRACT.md
AI_PIPELINE.md
ROUTING_LOGIC.md
UI_SYSTEM.md
DEMO_SCENARIO.md
TEST_PLAN.md

Document:

how to install
how to run
how to test
how to seed demo data
how NASA data was processed
how AI inference works
how routing works
known limitations
deployment instructions

---

# 26. DEVELOPMENT BEHAVIOR

Before implementing a phase:

1. inspect existing code;
2. read relevant project documentation;
3. propose the smallest coherent implementation;
4. identify tests;
5. implement;
6. run tests;
7. fix failures;
8. inspect code for regressions;
9. update docs;
10. summarize what changed.

Do not proceed after failing tests unless the failure is explicitly documented and unavoidable.

Prefer fixing root causes over suppressing tests.

Do not change tests merely to make incorrect behavior pass.

---

# 27. UI QUALITY GATE

For every major page:

- inspect it at desktop width;
- inspect at tablet width;
- inspect at mobile width where relevant;
- check overflow;
- check loading/error states;
- check keyboard accessibility;
- check map controls;
- check text hierarchy;
- check contrast;
- check empty states.

The application must look intentionally designed rather than AI-generated.

---

# 28. FINAL ACCEPTANCE TEST

MARSENSE is not finished until this exact sequence works:

open Mission Control
→ NASA prior map visible
→ Route Alpha visible
→ select/upload ground image
→ terrain analysis completes
→ expected vs observed comparison appears
→ significant discrepancy identified
→ affected mission assumption shown
→ Route Alpha impact shown
→ human confirms observation
→ region becomes Ground Observed
→ traversal cost updates
→ Route Beta generated
→ WHY explanation accurately describes structured evidence
→ page reload
→ verified evidence remains
→ switch to future EVA
→ future astronaut sees inherited observation

This is the primary acceptance criterion.

Do not sacrifice this flow for optional features.

---

# Engineering annex — Gate 0, 2026-10-10

Update: the user has now supplied and confirmed the main Word document at
`C:\Users\ACER\Downloads\MARSENSE_Final_Project_Notes.docx`. Its text is
extracted in `docs/MAIN_PROJECT_NOTES.md`; source reconciliation is complete.
The original text and hash were independently verified in this audit. Current
code and scientific gaps are in `docs/IMPLEMENTATION_STATUS.md`.

The preceding frozen engineering instructions are preserved. This annex makes
their acceptance criteria and implementation gaps explicit; it does not change
the approved product. Final source reconciliation is complete. See STATUS.md
and docs/DECISIONS.md; no later gate is certified complete.

## Context, users and non-goals

MARSENSE is a NASA Space Apps scientific mission-support prototype, **The Living
Mars Map**. NASA tells us what we expect. Astronauts show us what is actually
there. MARSENSE learns the difference. Vision: every step makes Mars more known.

Mission Control plans/reviews; astronauts capture observations and retain decision
authority; later explorers inherit verified knowledge. The scenario is a
fictional Marswalk from Habitat to Delta Outcrop in a bounded Jezero area.
Its purpose is to demonstrate traceable learning from ground evidence, not
certify EVA safety or simulate resources. No generic chatbot, rover simulation,
unsupported mineral/radiation/oxygen inference, unrelated dashboard or extra
instruments before the required loop works.

## Observable requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| R01 | Preserve frozen identity and full prior-to-future-EVA loop | Six screens and mandatory DEMO_SCENARIO.md flow |
| R02 | NASA prior/source evidence cannot be silently overwritten | Byte hashes and immutable-prior tests before/after verification |
| R03 | Ground observation, AI inference, human interpretation, consequence and decision remain separate | Stored raw/derived assets, model metadata, decision history inspected through API |
| R04 | Ground evidence begins PROVISIONAL and AI cannot mutate verified knowledge | No terrain/cost change before verification, including failed/weak model cases |
| R05 | Human confirmation is required for important persistent updates | Confirm/reject/more-evidence tests; named reviewer, timestamp and rationale |
| R06 | Supported spatial footprint bounds every terrain update | Outside-footprint expectations/costs remain unchanged; edge intersection tests |
| R07 | Dynamic observations expire and never become terrain/inherited facts | Expiry, stale-display and post-restart exclusion tests |
| R08 | Distances, intersections and costs use explicit Mars metric geometry | Roundtrip, product CRS alignment, known-distance and route-length tests |
| R09 | Bounded reproducible NASA ingestion preserves full provenance | Source/product/CRS/resolution/time/processing manifest; cache integrity validation |
| R10 | Real terrain inference executes for known image and upload | Pinned local model or validated inference, genuine output, reproducible held-out validation; no annotation replay substitution |
| R11 | Discrepancy has MATCH, MINOR, SIGNIFICANT, CONFLICTING and INSUFFICIENT states | Configurable project thresholds, branch tests and no fabricated calibration |
| R12 | Consequences resolve real assumption/segment/target dependencies | Exact affected geometry IDs, off-route silent case, provisional safety-warning case |
| R13 | Verification atomically appends knowledge, events, assumptions and route versions | Rollback, idempotency and concurrent-confirmation tests |
| R14 | Deterministic A* consumes normalized prior and verified evidence | Cost breakdown and evidence references; blocked/no-route/corner-cutting tests |
| R15 | WHY derives entirely from stored facts and measured route tradeoffs | Expected/observed/affected assumption/segment/evidence and actual distance delta traceable |
| R16 | Verified evidence persists and reaches future EVA | Fresh backend process and browser reload; future mission route/evidence inheritance |
| R17 | Demo works disconnected from external services | Block external requests and downloads; cached real imagery and local inference remain usable |
| R18 | Six screens are clear, restrained, responsive and accessible | Desktop/tablet/mobile screenshots; keyboard, contrast, error and state audits |
| R19 | Failures preserve evidence and avoid false success | Model-failure retention, route-failure retention, unsaved persistence state, bounded sanitized errors |
| R20 | Deploy only after required gates/tests/audits pass | Locked dependencies, health/readiness, server-side auth, container validation, local fallback, freeze hash |

## Exact observation/verification behavior

Receive → validate bytes and metadata → locate footprint → retrieve prior/current
knowledge → execute perception → retain raw evidence → structure observation →
compare expected/observed → classify discrepancy → resolve dependencies → assess
relevance/possible safety consequence → warn provisionally or store silently →
show relevant discrepancy → request verification. No persistent terrain change
occurs at this point.

CONFIRM preserves prior, appends verified evidence and human interpretation,
updates knowledge state and challenged assumptions, changes supported traversal
costs, reevaluates routing, appends events, updates the Living Map and future EVA.
REJECT keeps the evidence and prior/current verified interpretation.
NEEDS_MORE_EVIDENCE remains pending. Conflicting evidence requires explicit
resolution; unknown or failed inference cannot confirm a terrain fact without
human identification. Expired dynamic evidence cannot become a fresh observation.

## Before/after contract

Before: **Area 14**, ORBITAL_ONLY, expected low obstruction, Route Alpha segment 3
depends on that assumption. After ground observation: high rock abundance / rough
candidate, significant discrepancy when sufficiently supported, assumption
challenged, provisional consequence. After human verification: GROUND_OBSERVED
inside footprint, revised costs, Route Beta if preferable, WHY and actual distance
tradeoff. Future EVA inherits discovery. Existing names "Traverse corridor" and
"assumption-corridor" are implementation gaps against Area 14 / A17 terminology,
not a new approved scenario.

## Current implementation versus required scope

The existing compatible stack is retained. SQLite is an allowed fallback.
Real CTX/HiRISE crops and PIA26072 are cached. Habitat, target, soil expectation
and observation registration are illustrative. The mandatory current E2E test
uses curated replay; uploads execute conservative untrained OpenCV or an optional
TorchScript adapter. No validated local checkpoint or training/validation report
is bundled. During concurrent work a training/export pipeline, DEM adapter,
candidate DTM sampler, MOLA context crop and PLACES pose subset appeared.
The candidate DTM has zero valid coverage; genuine model validation, calibrated
Navcam/Mastcam-Z registration and CRISM science ingestion remain incomplete.
These are incomplete gates, never synthetic NASA replacements or implied
completed scientific capabilities. docs/MAIN_PROJECT_NOTES.md now contains a
repository text extraction of the named final notes. Its product content was
cross-checked against all 458 paragraphs of the original DOCX at
C:\Users\ACER\Downloads\MARSENSE_Final_Project_Notes.docx. The extraction matches
after whitespace normalization. Hash/provenance: docs/BASELINE_SOURCE_MANIFEST.json.

## Rollout and traceability

Contracts: ARCHITECTURE.md, DATA_MODELS.md, API_CONTRACT.md, NASA_DATA.md,
AI_PIPELINE.md, ROUTING_LOGIC.md and UI_SYSTEM.md. Validation: TEST_PLAN.md.
Scenario: DEMO_SCENARIO.md. Ordered tickets/gates: IMPLEMENTATION_PLAN.md.
Current outcomes and blockers: STATUS.md. Existing-code audit:
docs/BASELINE_AUDIT.md. Production plan: DEPLOYMENT.md.

Gate 0 passes only when these documents are internally consistent **and** checked
against the authoritative project notes. New feature work follows gates 1–20 in
order; a baseline test pass does not waive missing source/data/model requirements.
