Continue MARSENSE from the current verified implementation state.

Do NOT redesign the product.
Do NOT add unrelated features.
Do NOT rewrite working core behavior.

The current application already has a functioning and tested vertical slice:

NASA-derived prior map
→ mission assumptions
→ astronaut observation
→ perception adapter
→ discrepancy classification
→ mission consequence
→ provisional alert
→ human confirmation/rejection/more-evidence
→ durable Living Map knowledge
→ route recalculation
→ factual WHY explanation
→ restart persistence
→ future EVA inheritance

Current verified quality state:

- 29 backend tests pass
- 3 component tests pass
- 21 browser tests pass
- Ruff passes
- mypy passes
- ESLint passes
- TypeScript passes
- production frontend build passes
- browser image-decode checks pass
- native launcher works at 127.0.0.1:3000 and 127.0.0.1:8000

Preserve all passing behavior.

The next goal is:

# SCIENTIFIC COMPLETION + NASA DATA HARDENING

The following six gaps are now the highest-priority blockers.

Work through them sequentially.

Do not mark MARSENSE scientifically complete until each required gate passes.

---

# GATE S1 — VALID JEZERO DTM + SLOPE PIPELINE

Current problem:

The currently attached HiRISE DTM candidate contains zero valid sampled coverage for the selected operational area.

Required work:

1. Identify an official HiRISE DTM product that actually covers the selected Jezero operational region.

2. Verify from official NASA/HiRISE/PDS metadata:
   - product identifier
   - bounds
   - projection
   - map scale
   - pixel size
   - no-data value
   - vertical reference
   - horizontal coordinate system

3. Implement reproducible ingestion.

4. Reproject/resample only when necessary.

5. Align DTM with:
   - operational map
   - mission regions
   - route grid
   - observation footprints

6. Derive slope.

7. Preserve raw elevation separately from derived slope.

8. Do not invent NASA EVA-safe slope thresholds.

Use project-defined prototype route-cost classes and clearly label them as MARSENSE configuration.

9. Add coverage validation.

The ingestion pipeline must fail loudly if:
- route region has no valid DTM data
- CRS mismatch occurs
- no-data values dominate required operational cells

10. Create visualization/debug outputs demonstrating alignment.

Tests required:

- valid DTM coverage exists for demo route
- no-data handling
- known elevation samples
- slope calculation sanity
- CRS round trip
- raster/route intersection
- routing cost changes with slope
- no silent fallback pretending missing DTM is valid

Update:

NASA_DATA.md
ROUTING_LOGIC.md
TEST_PLAN.md
STATUS.md

Do not continue to S2 until this gate passes.

---

# GATE S2 — REAL AI4MARS TRAINING + EVALUATION

The current perception adapter must be replaced or backed by a genuine validated AI4Mars pipeline.

Required work:

1. Obtain the genuine AI4Mars dataset or an official accessible subset sufficient for the implemented terrain classes.

2. Record:
   - exact dataset source
   - version/source metadata
   - class definitions
   - dataset size used
   - licensing/usage information where applicable

3. Build deterministic dataset preparation.

4. Split data without leakage.

At minimum:

train
validation
held-out test

5. Train or fine-tune the selected segmentation model.

Prefer a model appropriate for hackathon/local execution rather than unnecessary scale.

6. Save:
   - checkpoint
   - model metadata
   - training configuration
   - class mapping
   - normalization
   - preprocessing version

7. Evaluate on held-out data.

Report real metrics only.

Suggested metrics:

- per-class precision
- per-class recall
- F1
- IoU
- mean IoU
- confusion matrix

8. Perform a separate Perseverance transfer test where feasible.

Do NOT mix transfer images into training if they are being presented as independent evaluation.

9. Clearly distinguish:

AI4Mars held-out performance

from

Perseverance transfer/generalization performance.

10. Integrate the validated checkpoint into the existing inference adapter.

11. Low confidence / unsupported terrain must resolve to UNKNOWN or insufficient evidence, not forced classification.

12. Preserve deterministic fixture support for E2E reliability, but do not present fixture results as benchmark performance.

Create:

MODEL_CARD.md

Include:

- intended use
- training data
- evaluation data
- metrics
- limitations
- known domain shift
- failure modes
- version/hash

Tests required:

- model loads
- deterministic inference under fixed configuration
- output schema
- unknown handling
- confidence behavior
- invalid image handling
- checkpoint/version provenance

Update STATUS.md.

---

# GATE S3 — CALIBRATED PERSEVERANCE CAMERA + PLACES JOIN

Current visual demo assets are not enough for the final scientific data contract.

Implement calibrated Mars 2020 image ingestion.

Priority:

Navcam first.

Mastcam-Z second.

Requirements:

1. Use official calibrated PDS products.

2. Preserve:
   - product ID
   - camera/instrument
   - SCLK/time
   - sol
   - calibration state
   - image dimensions
   - camera metadata
   - source URL/archive identifier

3. Join images to Mars 2020 PLACES using proper time/pose identifiers.

Do not join based on approximate filenames unless officially justified.

4. Retrieve:
   - rover position
   - orientation
   - local site/drive labels
   - mechanism/camera pose information where necessary

5. Compute/derive the observation footprint only when camera geometry supports it.

If a reliable footprint cannot be derived:

represent location uncertainty honestly rather than inventing exact coverage.

6. Record spatial uncertainty.

7. Verify that the selected image location overlaps the corresponding orbital region.

8. Build a diagnostic view showing:

orbital location
rover pose
image
footprint/uncertainty

Tests required:

- metadata parsing
- SCLK/pose join
- missing pose behavior
- location conversion
- footprint generation
- uncertainty fallback
- invalid metadata handling

Do not overclaim centimeter-level image footprint accuracy.

Update:

NASA_DATA.md
DATA_MODELS.md
STATUS.md

---

# GATE S4 — CRISM SCIENCE CONTEXT

Implement the required CRISM science layer.

Use official processed CRISM products appropriate for mapping.

Prefer MTRDR/MRDR or another justified processed product.

Required:

1. Select CRISM product(s) covering or contextually supporting the chosen Jezero operational area.

2. Record:
   - product identifier
   - bounds
   - projection
   - resolution
   - processing level
   - source
   - relevant browse/summary parameters

3. Do NOT perform unsupported automatic mineral identification unless scientifically justified.

4. For the hackathon UI, derive only defensible science context.

Examples:

- mapped science-interest area
- CRISM observation coverage
- published/processed spectral parameter region

5. Clearly label:

Observed
Derived
Interpretive

states.

6. Add CRISM layer to Evidence Inspector and science target provenance.

7. Preserve the orbital-vs-ground distinction.

The system must never claim:

“helmet camera discovered mineral X”

unless actual appropriate instrument evidence supports it.

Tests:

- product loads
- geometry aligns
- layer provenance visible
- science target maps correctly
- missing CRISM does not break primary mission flow

Update STATUS.md.

---

# GATE S5 — MULTI-SOURCE CONFIRMATION + SUPERSESSION

The enum/state definitions already exist.

Now implement the operational workflow.

Required:

Evidence may originate from independent sources such as:

- orbital imagery
- astronaut camera
- second image/viewpoint
- another astronaut
- science instrument
- later mission observation

Implement explicit source independence metadata.

Avoid treating many correlated frames from the same observation burst as independent confirmations.

Required transitions should support:

ORBITAL_ONLY
→ PROVISIONAL
→ GROUND_OBSERVED
→ MULTI_SOURCE_CONFIRMED

and:

PROVISIONAL
→ REJECTED

and:

GROUND_OBSERVED
↔ CONFLICTING

and:

previous interpretation
→ SUPERSEDED

Rules:

1. Supersession never deletes history.

2. Current interpretation references supporting evidence.

3. Conflicting sources remain visible.

4. Independent confirmation requires a different qualifying evidence source/episode.

5. Correlated observations must not inflate confidence.

6. Users must be able to inspect evidence ancestry.

Add UI behavior to Evidence Inspector.

Do not clutter Astronaut View.

Tests:

- independent second source confirms
- repeated same-source frame does not falsely multi-confirm
- conflict transition
- supersession
- full historical trace remains
- current interpretation references correct evidence

Update STATUS.md.

---

# GATE S6 — AUTHENTICATION + IDENTITY-BOUND HUMAN REVIEW

Before any public deployment, human decisions must be attributable.

Implement lightweight but robust authentication appropriate for the prototype.

Required roles may include:

ASTRONAUT
MISSION_CONTROL
ADMIN

Do not build a giant enterprise IAM system.

Requirements:

1. authenticated user identity

2. verified actions record:

who
what
when
mission
observation
decision

3. confirmation/rejection/request-more-evidence actions must be identity-bound.

4. preserve audit history.

5. prevent anonymous mutation of mission-critical state in public deployment.

6. read-only demo mode may be supported separately.

7. secure session/token handling.

8. credentials never stored in repository.

Tests:

- unauthenticated mutation rejected
- authenticated confirmation succeeds
- role checks
- audit identity recorded
- logout/session expiry
- read-only demo behavior

Perform security review after implementation.

Update STATUS.md.

---

# GATE S7 — EIGHT-SOURCE STACK VERIFICATION

The eight-source NASA stack is mandatory.

Create a final matrix covering:

1. CTX
2. HiRISE imagery
3. HiRISE DTM
4. MOLA
5. Navcam/Mastcam-Z
6. PLACES
7. AI4Mars
8. CRISM

For every source document:

- official product/source
- exact role
- raw format
- processed format
- current status
- actual demo usage
- provenance
- projection/coordinate handling
- observed vs derived classification
- fallback behavior
- test coverage

No source may be marked complete because only a placeholder adapter exists.

Create:

NASA_SOURCE_MATRIX.md

Statuses:

VALIDATED
PARTIALLY_VALIDATED
NOT_VALIDATED
BLOCKED

No exaggeration.

---

# GATE S8 — FULL SCIENTIFIC AUDIT

After S1–S7:

Use Software Engineering Toolkit code-review + research workflows.

Audit every visible scientific claim.

Search for unsupported claims including:

safe
real-time
live
hazard probability
radiation
weather
mineral identity
soil strength
oxygen
guaranteed route
ground truth
NASA-approved
NASA-certified

Anything unsupported must be:

removed

or

reworded accurately.

Preferred terminology:

ground evidence

rather than automatic ground truth.

Mark data clearly as:

OBSERVED
DERIVED
MODELED
SIMULATED
DEMO

Create:

SCIENTIFIC_AUDIT.md

Fix all high-severity findings.

---

# GATE S9 — COMPLETE REGRESSION

Run the complete suite after scientific integration.

Must include:

backend tests

frontend component tests

Playwright browser tests

Ruff

mypy

ESLint

TypeScript

production frontend build

database restart/persistence test

offline demo test

NASA cache test

AI inference test

DTM/slope test

CRISM test

authentication tests

multi-source evidence tests

full competition E2E

Ensure existing behavior has not regressed.

The primary scenario remains:

prior map
→ Route Alpha
→ ground observation
→ perception
→ discrepancy
→ mission impact
→ verification
→ Living Map update
→ reroute
→ Route Beta
→ persistence
→ future EVA

---

# GATE S10 — PUBLIC DEPLOYMENT READINESS

Only after S9 passes.

Prepare deployment configuration.

Requirements:

- production frontend
- production FastAPI
- production database
- migrations
- environment validation
- HTTPS-ready configuration
- health endpoints
- structured logs
- secure authentication
- CORS
- upload limits
- backup/recovery notes
- startup/restart behavior
- deterministic demo seed
- offline/local fallback

Use DigitalOcean only now if connected and appropriate.

Do not publish automatically unless deployment credentials and explicit authorization are available.

If publication cannot be completed automatically:

create exact DEPLOYMENT.md instructions.

---

# FINAL DELIVERABLES

Before declaring completion create/update:

STATUS.md

NASA_SOURCE_MATRIX.md

MODEL_CARD.md

SCIENTIFIC_AUDIT.md

FINAL_AUDIT.md

DEPLOYMENT.md

README.md

NASA_DATA.md

TEST_PLAN.md

DEMO_SCENARIO.md

---

# FINAL COMPLETION LANGUAGE

Do not say:

“fully scientifically validated”

unless every mandatory source/pipeline is genuinely validated.

Do not say:

“NASA-certified”

or:

“operational EVA safety system”.

Correct final description:

MARSENSE is a research and mission-concept prototype for evidence-aware Mars exploration decision support built from NASA-derived data and validated prototype workflows.

---

# EXECUTION RULE

Start with S1.

Work sequentially.

Preserve all currently passing functionality.

Do not spend time redesigning already-good UI.

Do not add features unrelated to these completion gates.

Use Software Engineering Toolkit:
- research for NASA-source questions
- TDD for new domain behavior
- implementation for each gate
- code-review after each major gate
- diagnosing-bugs for regressions

Use Product Design only for targeted UX review if new evidence/auth workflows create usability problems.

Maintain STATUS.md continuously.

Begin now.