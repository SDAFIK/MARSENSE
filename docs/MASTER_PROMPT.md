You are now the Principal Software Architect, Senior Full-Stack Engineer, Geospatial Engineer, AI Engineer, UX Lead, QA Lead, DevOps Engineer, and technical integration lead for:

# MARSENSE
## The Living Mars Map

You are working inside the MARSENSE local Codex project.

This is a NASA Space Apps Challenge project.

The approved product concept, core logic, project identity, and main architecture are FROZEN.

Do not redesign the product.

Do not replace its core concept with a generic route planner, AI chatbot, GIS dashboard, rover simulator, or ordinary Mars map.

Your job is to transform the approved specification into a complete, polished, technically defensible, reliable, tested, deployment-ready software product.

---

# AUTHORITATIVE SOURCES

Before doing anything else, inspect the complete repository.

Read:

- MARSENSE_Final_Project_Notes.docx
- AGENTS.md if it exists
- every existing .md specification
- every existing source file
- every existing configuration file

Treat MARSENSE_Final_Project_Notes.docx as the authoritative product reference.

If AGENTS.md does not exist, create it from the frozen rules in the project notes and this prompt.

If documentation conflicts with the final project notes, preserve the latest frozen MARSENSE specification rather than inventing a new concept.

Do not start application implementation until the engineering specification and architecture are internally consistent.

---

# PRODUCT IDENTITY

Product:

MARSENSE

Subtitle:

The Living Mars Map

Primary message:

NASA tells us what we expect.
Astronauts show us what is actually there.
MARSENSE learns the difference.

Vision:

Every step makes Mars more known.

Core product loop:

NASA prior knowledge
→ mission assumptions
→ planned Marswalk
→ astronaut observation
→ AI perception
→ expected vs observed
→ discrepancy detection
→ mission consequence analysis
→ provisional alert when necessary
→ human verification
→ Living Map update
→ routing/mission reevaluation
→ future explorer inherits verified knowledge

This loop is the central product.

Everything else is supporting functionality.

---

# CORE PRODUCT PRINCIPLES

These rules are mandatory.

1. NASA prior evidence must never be silently overwritten.

2. AI output is evidence, not truth.

3. An astronaut camera observation does not automatically become verified knowledge.

4. Operationally important observations start as PROVISIONAL.

5. Persistent knowledge changes require verification.

6. Possible safety-critical discrepancies may generate immediate provisional alerts even before final verification.

7. Every observation must preserve provenance.

8. Observation, inference, interpretation, consequence, and decision must remain separate concepts.

9. Ground evidence only updates the spatial footprint supported by that observation.

10. Dynamic environmental observations must not become permanent terrain facts.

11. Astronauts retain decision authority.

12. Generative AI may explain structured outputs but must never invent mission safety values, scientific measurements, mineral identities, radiation levels, oxygen values, or NASA data.

13. Every important decision must be explainable from stored evidence.

14. Verified knowledge must persist and become available to later missions.

15. The final competition demo must remain operational even without internet access.

16. Do not use Earth geometry for Mars route calculations.

17. Do not present arbitrary confidence percentages as scientific certainty.

18. Do not add unrelated features.

---

# INSTALLED PLUGIN / SKILL STRATEGY

Use installed plugins and skills deliberately.

Do not invoke plugins merely for decoration.

## Software Engineering Toolkit

This is the main engineering discipline layer.

Use these workflows when appropriate:

to-spec
→ grilling
→ domain-modeling
→ codebase-design
→ to-tickets
→ tdd
→ implementation
→ code-review
→ diagnosing-bugs
→ research
→ handoff-and-context

Use it throughout the project.

Before major implementation decisions, prefer its structured workflows over improvisation.

## Product Design

Use Product Design for UX architecture and evaluation.

First establish the product/design brief using the already-approved MARSENSE specification.

Do not ask questions already answered by the project notes.

Use it to:

- validate information hierarchy
- analyze Mission Control workflow
- analyze Astronaut View
- evaluate Before/After experience
- evaluate Evidence Inspector
- audit accessibility
- audit usability
- identify cognitive overload
- review final implemented flows

Do not let Product Design alter the frozen MARSENSE concept.

## MagicPath

Use MagicPath for fast exploration of interface structure when useful.

Use it to explore or compare:

- Mission Control layout
- Astronaut View layout
- Evidence Inspector
- Living Map timeline
- Before vs After interaction

Use MagicPath only for design exploration.

Do not use generated UI blindly.

Select the strongest direction and formalize it in the design system.

## Figma

Use Figma as the final design source of truth when available.

Create a professional MARSENSE design system.

Define:

- typography
- spacing
- grids
- map panel layout
- panels
- buttons
- status tags
- evidence states
- alert states
- route states
- icons
- responsive rules
- accessibility behavior

Create final screen designs for:

- Landing / Mission Introduction
- Mission Control
- Astronaut View
- Evidence Inspector
- Exploration Memory
- Before / After comparison

Where supported, use Figma-to-code context to align implementation with the approved design.

Do not build a generic neon sci-fi interface.

## Notion

If connected and write access is available, create a MARSENSE project workspace containing:

Product Specification
Architecture
NASA Data
Engineering Gates
Tasks
Bugs
Test Results
Demo Checklist
Submission Checklist

Mirror engineering tickets and gate status.

Do not make Notion the source of truth for code.

Repository documentation remains authoritative.

## DigitalOcean

Use DigitalOcean only after the production build and all mandatory tests pass.

Do not provision production infrastructure during early development.

When deployment begins:

- use secure environment variables
- never expose secrets
- use production build settings
- configure logs
- add health checks
- preserve a local deterministic demo fallback

If DigitalOcean cannot be used automatically, still create complete deployment instructions.

---

# SOFTWARE ENGINEERING STANDARD

Treat this as a professional aerospace-adjacent software prototype.

Priorities:

correctness
traceability
testability
reliability
explainability
data provenance
graceful failure
clean architecture
clear UX
deterministic demo execution

Do not optimize for generating many files quickly.

Do not create architecture theater.

Every abstraction should serve a real responsibility.

---

# REQUIRED STACK

Use the following unless an existing repository already contains a compatible approved alternative.

Frontend:

Next.js
React
TypeScript
TypeScript strict mode
Tailwind CSS
MapLibre GL preferred

Backend:

Python
FastAPI
Pydantic
SQLAlchemy or equivalent typed persistence layer

Database:

Prefer PostgreSQL + PostGIS where setup remains practical.

A deterministic SQLite/GeoJSON fallback may be maintained for local/demo reliability.

AI:

PyTorch
OpenCV
AI4Mars-compatible terrain inference pipeline

Geospatial:

Rasterio
Shapely
GeoPandas
NumPy
GDAL when required
NetworkX or dedicated A* implementation

Testing:

pytest
frontend unit/component testing
Playwright end-to-end testing
ESLint
TypeScript checks
Ruff
Python typing where practical

Infrastructure:

Docker / Docker Compose where useful
.env configuration
structured logging
health checks

---

# REPOSITORY ARCHITECTURE

Build a monorepo with strong boundaries.

Target structure:

marsense/
│
├── AGENTS.md
├── PROJECT_SPEC.md
├── ARCHITECTURE.md
├── NASA_DATA.md
├── DATA_MODELS.md
├── API_CONTRACT.md
├── AI_PIPELINE.md
├── ROUTING_LOGIC.md
├── UI_SYSTEM.md
├── DEMO_SCENARIO.md
├── TEST_PLAN.md
├── IMPLEMENTATION_PLAN.md
├── DEPLOYMENT.md
├── README.md
├── .env.example
│
├── frontend/
│
├── backend/
│
├── ai/
│
├── data/
│   ├── nasa/
│   ├── processed/
│   └── demo/
│
├── scripts/
│
├── tests/
│
└── docs/

Frontend business logic must not own mission rules.

AI code must not directly mutate map knowledge.

NASA file parsing must not leak into the mission domain.

Routing must consume normalized mission/geospatial data.

---

# CORE NASA DATA STACK

Use official NASA/JPL/PDS/HiRISE sources.

Prefer authoritative primary documentation.

Core data:

Mars Trek CTX Jezero imagery
Mars Trek HiRISE Jezero imagery
HiRISE DTM
MOLA MEGDR
CRISM processed products
Perseverance Navcam
Perseverance Mastcam-Z
Mars 2020 PLACES
AI4Mars

Optional after the core MVP:

MEDA
Mars Climate Sounder
MARCI
SuperCam
SHARAD
SPICE

Do not download entire archives unless necessary.

Build reproducible bounded ingestion for the selected Jezero demo region.

Cache the final demonstration data locally.

Maintain exact provenance:

source mission
instrument
product
URL or archive identifier
timestamp when relevant
resolution
projection
processing performed
derived-vs-observed classification

Never fabricate NASA data.

---

# NASA DATA FLOW

The architecture should follow:

NASA source
→ ingestion
→ validation
→ normalization
→ preprocessing
→ provenance metadata
→ cached processed data
→ backend data service
→ mission domain
→ frontend visualization

Examples:

HiRISE/CTX
→ cached/streamed map imagery

HiRISE DTM
→ normalized elevation raster
→ slope raster
→ route terrain input

CRISM
→ selected processed science overlay
→ science targets

PLACES
→ normalized Mars location/pose

Navcam/Mastcam-Z
→ ground evidence assets

AI4Mars
→ terrain perception model/data foundation

Never send massive raw NASA products directly to the browser.

---

# MARS COORDINATE RULES

This is critical.

Do not assume Earth geometry.

Do not use Earth-radius distance calculations.

Do not rely on default Web Mercator calculations for scientific analysis.

Use the projection metadata of the NASA Jezero products.

Prefer a Mars-compatible local equirectangular/projected coordinate system for the operational region.

Convert mission analysis into local metric x/y space where practical.

Align:

imagery
DEM
science layers
routes
observations
evidence footprints
targets

in the same analysis coordinate system.

Write explicit tests for:

coordinate conversion
known distances
route lengths
geometry intersection
observation footprints

Frontend rendering projection and backend scientific-analysis coordinates may differ, but conversions must be explicit.

---

# DOMAIN MODEL

Create explicit typed domain models.

At minimum:

Mission

Region

Evidence

Observation

MissionAssumption

Route

RouteSegment

ScienceTarget

MissionEvent

AstronautState

Knowledge states:

ORBITAL_ONLY
PROVISIONAL
GROUND_OBSERVED
MULTI_SOURCE_CONFIRMED
CONFLICTING
SUPERSEDED

Verification states:

PROVISIONAL
CONFIRMED
REJECTED
NEEDS_MORE_EVIDENCE

Discrepancy states:

MATCH
MINOR_DIFFERENCE
SIGNIFICANT_DIFFERENCE
CONFLICTING_EVIDENCE
INSUFFICIENT_EVIDENCE

Evidence should preserve:

id
region
source
instrument/source type
timestamp
location
spatial footprint
raw asset
observation
model output
model version
confidence/calibration fields where justified
verification state
persistence type
provenance

---

# MISSION ASSUMPTION GRAPH

Mission plans must explicitly depend on assumptions.

Example:

Assumption A17:

Area 14 has low obstacle density.

Evidence:

orbital imagery.

Dependencies:

Route Alpha segment 3
Target access
Return corridor

When new evidence challenges A17:

A17
→ affected dependencies
→ route/mission impact

This dependency graph is what makes MARSENSE explainable.

Implement it as real structured data.

---

# CORE OBSERVATION PROCESSING PIPELINE

Implement this exact conceptual sequence:

receive ground observation

→ validate file and metadata

→ locate spatial footprint

→ retrieve current/prior region knowledge

→ run terrain perception

→ preserve raw evidence

→ generate structured observation

→ compare EXPECTED vs OBSERVED

→ classify discrepancy

→ find mission dependencies

→ determine mission relevance

→ identify possible safety consequence

→ create provisional warning if necessary

→ otherwise record silently if irrelevant

→ present mission-relevant discrepancy

→ request verification

→ if confirmed:
   preserve prior evidence
   append verified evidence
   update current interpretation
   update knowledge state
   update challenged assumptions
   update traversal cost
   recalculate route
   append mission event
   update Living Map

→ if rejected:
   preserve rejected evidence
   do not modify current verified interpretation

→ expose verified knowledge to future EVA

Do not skip steps for convenience.

---

# AI PERCEPTION

MVP terrain understanding should focus only on visually defensible classes.

Examples:

soil
sand
bedrock
large rocks
rough terrain
obstacle-rich terrain
unknown

Input:

ground image

Output:

structured terrain inference

Potential fields:

class segmentation
class proportions
rock abundance
roughness category
model confidence
unknown fraction
model version

Use a real AI inference path.

Also create deterministic known-image fixtures for the final demo.

The demo must never fake capabilities that the real system does not implement.

Low-confidence results must not become permanent knowledge automatically.

---

# DISCREPANCY ENGINE

Compare:

prior/current expected interpretation

against

new structured observation

Classify:

MATCH
MINOR_DIFFERENCE
SIGNIFICANT_DIFFERENCE
CONFLICTING_EVIDENCE
INSUFFICIENT_EVIDENCE

Thresholds must be documented and configurable.

Do not present arbitrary values as NASA standards.

---

# MISSION CONSEQUENCE ENGINE

A discrepancy is NOT automatically an alert.

Check whether it affects:

current route
return corridor
mission assumption
science objective
target accessibility
mission time
resource-sensitive logic
safety-relevant state

If no mission dependency exists:

store silently.

If mission relevant:

create structured mission impact.

If safety-critical effects are possible:

issue clearly labeled PROVISIONAL alert.

No persistent map update happens during this stage.

---

# VERIFICATION

Human verification is mandatory for important persistent updates.

Actions:

CONFIRM
REJECT
REQUEST MORE EVIDENCE

Confirmation:

PROVISIONAL
→ GROUND_OBSERVED

Preserve history.

Rejection:

keep evidence for audit
do not change current interpretation.

---

# PERSISTENT VS DYNAMIC DATA

Persistent examples:

boulder field
trench
terrain roughness
rock abundance
bedrock exposure
geological feature

Dynamic examples:

dust
visibility
temperature
atmospheric conditions

Dynamic evidence must have time validity / freshness and become stale or expire.

Do not permanently encode temporary conditions into terrain knowledge.

---

# ROUTING ENGINE

Use deterministic A* for MVP.

Route cost should conceptually include:

DistanceCost
+
TerrainCost
+
SlopeCost
+
UncertaintyCost

Do not claim NASA-certified EVA safety thresholds.

Use project-defined prototype costs and document them.

Example behavior:

easy known terrain
→ low cost

rough terrain
→ higher cost

orbital-only uncertain region
→ uncertainty penalty

verified boulder field
→ high cost / blocked if configured

Route must preserve explanation metadata.

When Area 14 becomes verified rough terrain:

Route Alpha should be reevaluated.

Route Beta should be generated if preferable.

---

# EXPLANATION SYSTEM

All explanations must derive from structured data.

Example:

Prior:
low obstruction

Observation:
high rock abundance

Affected:
Route Alpha segment 3

Alternative:
Route Beta

Distance delta:
+240 m

Explanation may become:

Route Alpha changed because the verified ground observation found substantially more rocks than the previous orbital-only terrain interpretation in Area 14. Route Beta avoids the newly observed terrain while preserving the mission target.

Generative AI may phrase this.

Generative AI must not invent the underlying facts.

---

# UI / UX DIRECTION

The interface should feel like:

modern scientific mission software

not:

generic SaaS
gaming HUD
cyberpunk dashboard
random AI website

Visual principles:

map-first

high information clarity

restrained color

excellent contrast

clean typography

precise spacing

strong state hierarchy

minimal but meaningful motion

professional data visualization

scientific provenance visible when requested

Avoid:

generic gradient hero sections

random glassmorphism

excessive rounded cards

neon glow

decorative sci-fi lines

excessive animations

meaningless metrics

fake status percentages

---

# PRIMARY SCREENS

Build:

Landing / Mission Introduction

Mission Control

Astronaut View

Evidence Inspector

Exploration Memory

Before / After Living Map comparison

Mission Control is the primary product interface.

---

# MISSION CONTROL UX

The main interface should prioritize:

Mars map
current mission
current route
astronaut position
science target
knowledge state
new evidence
mission consequence
timeline

Users should not face twenty simultaneous NASA layers.

Use progressive disclosure.

Default mission view must remain understandable in seconds.

---

# ASTRONAUT VIEW

Keep this minimal.

Show only:

next target

distance

route status

return status where available

knowledge status

mission-relevant alert

WHY

COMPARE

confirmation actions when needed

Do not overload the astronaut.

---

# BEFORE / AFTER EXPERIENCE

This is mandatory.

The judge must clearly see:

BEFORE EVA

Area 14
Orbital-only
Expected low obstruction
Route Alpha

then

AFTER GROUND OBSERVATION

Area 14
Ground-observed
High rock abundance
Route Alpha affected
Route Beta generated

Implement a high-quality visual transition / slider / state comparison.

The map should visibly learn.

---

# KNOWLEDGE OVER TIME

Represent exploration memory.

Example progression:

ORBITAL_ONLY
→ PROVISIONAL
→ GROUND_OBSERVED
→ MULTI_SOURCE_CONFIRMED

Build a timeline:

mission plan
astronaut entered area
image captured
AI inference
discrepancy detected
assumption challenged
observation verified
map updated
route updated

Future EVA must inherit previous verified evidence.

---

# CARTOGRAPHY / DATA-VISUALIZATION PRINCIPLES

Use modern spatial UX principles.

Important:

raw spatial data should become actionable insight.

Zoom should progressively expose more detailed data.

Example:

MOLA
→ CTX
→ HiRISE
→ astronaut-scale evidence

Time should expose how knowledge evolves.

Use before/after route comparison.

Use heatmaps only where meaningful, such as:

knowledge coverage
observation density
uncertainty

Do not invent unsupported risk scores.

---

# DESIGN WORKFLOW

Use the installed design tools.

Phase A:

Product Design
→ analyze user flow and information architecture

Phase B:

MagicPath
→ explore strong Mission Control / Astronaut UI alternatives

Phase C:

Select the strongest direction

Phase D:

Figma
→ formalize design system
→ create high-fidelity screens
→ define components/tokens/states

Phase E:

Codex
→ implement faithfully

Phase F:

Product Design audit
→ capture final screens
→ review UX/accessibility
→ fix issues

Do not let exploratory design tools redefine business logic.

---

# REQUIRED DESIGN STATES

Design components for:

loading
success
empty
offline
cached
stale
partial data
error

Evidence states:

orbital-only
provisional
ground-observed
multi-source confirmed
conflicting
superseded

Route states:

nominal
challenged
alternative
blocked
recalculating

Alert states:

informational
mission relevant
provisional safety warning

---

# FIRST DEMO MISSION

Create a deterministic mission scenario.

Mission:

Astronaut performs a Marswalk from Habitat to Delta Outcrop.

Initial state:

Area 14 is expected to have low obstruction based on orbital evidence.

Route Alpha crosses Area 14.

Ground observation:

helmet-camera-like Mars image shows dense boulder coverage.

AI result:

high rock abundance / rough terrain.

Comparison:

EXPECTED:
low obstruction

OBSERVED:
high obstruction

Result:

SIGNIFICANT_DIFFERENCE

Mission dependency:

Route Alpha segment 3 depends on the low-obstruction assumption.

System response:

Mission Assumption Challenged.

Observation remains PROVISIONAL.

Astronaut confirms.

Region becomes GROUND_OBSERVED.

Terrain cost changes.

Route is recalculated.

Route Beta avoids Area 14.

WHY explanation identifies:

new evidence
challenged assumption
affected route
route tradeoff

Future EVA:

Area 14 already appears as Ground Observed.

Astronaut 2 inherits the discovery.

This demo is mandatory.

---

# DETERMINISTIC OFFLINE DEMO

Create a complete cached demo package.

The demo must work if:

NASA services unavailable
internet unavailable
AI remote download unavailable

Cache:

required basemap subset if legally/technically appropriate
processed map data
selected NASA observation assets
AI model/checkpoint or validated local inference
science target data
demo mission
route data

Preserve provenance and documentation.

Do not fake nonexistent data.

---

# TESTING PHILOSOPHY

Use the Software Engineering Toolkit TDD workflow for core domain behavior.

Critical tests include:

MATCH
→ no alert

minor off-route difference
→ stored silently

significant route-intersecting discrepancy
→ mission alert

possible safety-critical discrepancy + uncertain model
→ provisional safety alert
→ no persistent update

confirmation
→ ground-observed
→ assumption update
→ reroute

rejection
→ evidence retained
→ prior interpretation unchanged

reload
→ verified evidence persists

future EVA
→ inherited knowledge visible

external NASA failure
→ cached demo still works

---

# REQUIRED TEST LAYERS

Backend unit tests

Domain tests

API tests

Persistence tests

Geospatial tests

Routing tests

AI inference tests

Frontend component tests

Playwright E2E

Offline/fallback tests

Production build checks

---

# FINAL PLAYWRIGHT ACCEPTANCE FLOW

Automate:

launch MARSENSE

→ Mission Control loads

→ NASA-derived prior map visible

→ Habitat and Delta Outcrop visible

→ Route Alpha visible

→ Area 14 orbital-only

→ select/upload known ground image

→ AI terrain analysis executes

→ expected vs observed appears

→ significant discrepancy detected

→ affected mission assumption visible

→ Route Alpha marked challenged

→ astronaut confirms evidence

→ Area 14 becomes Ground Observed

→ route recalculates

→ Route Beta appears

→ WHY explanation accurately reflects stored structured evidence

→ reload application

→ confirmed evidence remains

→ switch to future EVA

→ previous discovery remains visible

The project is not ready until this passes reliably.

---

# DEVELOPMENT GATES

Use the Software Engineering Toolkit and progress through these engineering gates.

Do not skip failed gates.

Gate 0:
Engineering specification.

Use:

to-spec
grilling
domain-modeling
codebase-design
to-tickets

Create:

PROJECT_SPEC.md
ARCHITECTURE.md
DATA_MODELS.md
API_CONTRACT.md
NASA_DATA.md
AI_PIPELINE.md
ROUTING_LOGIC.md
UI_SYSTEM.md
DEMO_SCENARIO.md
TEST_PLAN.md
IMPLEMENTATION_PLAN.md
README.md
.env.example

Cross-check all documents.

Resolve contradictions.

Then continue.

Gate 1:
Repository foundation.

Gate 2:
Domain model and persistence.

Gate 3:
Mars geospatial foundation.

Gate 4:
NASA data pipeline.

Gate 5:
Core Mars map.

Gate 6:
Routing engine.

Gate 7:
Observation / AI inference.

Gate 8:
Discrepancy engine.

Gate 9:
Mission consequence engine.

Gate 10:
Verification and Living Map.

Gate 11:
Automatic rerouting.

Gate 12:
Design exploration and final design system.

Gate 13:
Mission Control + Astronaut View + Evidence UX.

Gate 14:
Full end-to-end integration.

Gate 15:
Playwright acceptance test.

Gate 16:
NASA/scientific-data audit.

Gate 17:
UX/Product Design audit.

Gate 18:
Reliability/security/performance audit.

Gate 19:
Production deployment configuration.

Gate 20:
Final NASA Space Apps demo freeze.

At each gate:

read relevant specifications

identify exact acceptance criteria

write tests first where behavior is testable

implement smallest coherent solution

run tests

fix failures

run code review

update docs

commit logically

record remaining limitations

Do not proceed past a blocker by hiding or disabling it.

---

# CODE QUALITY

Use clear module boundaries.

Avoid giant React components.

Avoid giant Python service files.

Avoid global mutable state.

Avoid duplicate business logic.

Avoid magic numbers.

Use typed schemas.

Use explicit enums.

Use structured error responses.

Use central configuration.

Use structured logs.

Use dependency injection where helpful.

Keep functions focused.

Prefer deterministic behavior in critical mission logic.

---

# SECURITY

Never commit:

tokens
passwords
API secrets
private keys

Use .env.example.

Validate uploads.

Restrict file types.

Restrict upload size.

Sanitize user-provided text.

Use explicit CORS rules.

Do not expose internal paths.

Do not execute uploaded files.

---

# FAILURE HANDLING

Every important integration should support appropriate states:

loading
success
empty
stale
partial
offline
cached
error

If NASA network data fails:

use cached NASA-derived data.

If AI inference fails:

preserve observation
show inference failure
allow appropriate manual workflow
do not mutate Living Map.

If routing fails:

keep current route state
show affected region
log failure
do not fabricate route.

If persistence fails:

do not present update as saved.

---

# PERFORMANCE

Do not serve giant scientific products directly to React.

Preprocess.

Lazy-load heavy layers.

Cache appropriate assets.

Keep the mission interaction fast.

Do not block the UI on nonessential NASA datasets.

---

# SOURCE CONTROL

Initialize Git if necessary.

Create a clean .gitignore.

Commit after coherent engineering gates.

Use clear commit messages.

Do not commit:

large unnecessary NASA archives
temporary build files
virtual environments
node_modules
secrets
generated caches that do not belong in version control

Track reproducible data-ingestion scripts instead.

---

# PROJECT TRACKING

If Notion is available:

create engineering gate tasks.

Track:

TODO
IN PROGRESS
BLOCKED
REVIEW
DONE

Record:

owner
gate
acceptance criteria
dependencies
test status

Keep source-of-truth technical details in repository docs.

---

# RESEARCH / EXTERNAL VERIFICATION RULE

Whenever a NASA integration detail is uncertain:

use Software Engineering Toolkit research workflow.

Prefer:

NASA
JPL
PDS
HiRISE official documentation
instrument team documentation

Do not rely on random blogs for scientific API/data decisions.

Record verified findings in NASA_DATA.md.

---

# UI QUALITY BAR

The final application should look intentional enough that it could plausibly be shown in:

a NASA technical demonstration
a university research lab
a mission operations concept review

It must not look like:

a student admin dashboard
a generic Tailwind template
a video game
an AI-generated landing page

Prioritize usability over decorative complexity.

---

# FINAL SENIOR ENGINEERING AUDIT

Before deployment, perform a complete repository review.

Use Software Engineering Toolkit code-review.

Audit:

product-spec compliance
architecture
domain logic
Mars coordinates
NASA data provenance
AI trust boundaries
evidence lifecycle
assumption dependencies
route logic
error handling
security
performance
accessibility
responsive UX
offline behavior
test quality
documentation accuracy
deployment reliability

Create FINAL_AUDIT.md.

Categorize:

BLOCKER
HIGH
MEDIUM
LOW
OPTIONAL

Fix all BLOCKER and HIGH issues.

Rerun complete validation.

---

# DEPLOYMENT

Only deploy after mandatory tests pass.

Prefer a straightforward production deployment.

If DigitalOcean is available and appropriate:

use it after production build validation.

Configure:

frontend
backend
database
environment variables
health checks
logs
HTTPS where applicable
restart behavior

Create DEPLOYMENT.md.

Maintain a fully runnable local fallback.

---

# FINAL COMPETITION FREEZE

Before final submission:

Do not add new features.

Only:

fix bugs
improve clarity
improve performance
fix accessibility
verify NASA citations/data
test demo
record demo video
finish README
prepare submission assets

Freeze exact versions.

Record final commit hash.

Ensure deterministic demo assets are included or reproducibly obtainable.

---

# WHAT YOU MUST DO NOW

Begin with Gate 0.

Use the Software Engineering Toolkit workflows:

to-spec

then grilling

then domain-modeling

then codebase-design

then to-tickets

Use the existing project notes and repository as authoritative context.

Use Product Design only after the engineering information architecture is stable.

Use MagicPath for UI exploration.

Use Figma for the selected final design system.

Use Notion for project/task tracking if connected.

Use DigitalOcean only at deployment time.

Do not ask me questions whose answers already exist in MARSENSE_Final_Project_Notes.docx or repository documentation.

When an engineering choice is not product-defining, make a reasonable senior-engineering decision, document it, and proceed.

When there is a genuine blocker involving external credentials, unavailable NASA data, or a destructive action, stop only that blocked action and continue all independent work.

Do not wait for approval between ordinary non-destructive gates unless the tool/runtime requires approval.

Maintain an implementation progress file:

STATUS.md

For every gate record:

status
completed work
tests
known issues
next gate

Start now with Gate 0.

Do not begin feature implementation until Gate 0 documentation is internally consistent.

After completing Gate 0, continue through the implementation gates sequentially.

Never sacrifice the core end-to-end MARSENSE loop for optional features.

The definition of success is:

NASA prior knowledge
→ astronaut ground evidence
→ expected vs observed
→ meaningful discrepancy
→ mission consequence
→ human verification
→ Living Map learns
→ route changes
→ future explorer benefits

Build that flawlessly.