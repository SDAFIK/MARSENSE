# Deterministic Jezero Marswalk

Frozen mandatory story: Habitat → Delta Outcrop, with Area 14 learned from
ground evidence. All EVA coordinates and habitat/target geometry are illustrative.
The visible orbital imagery and PIA26072 Navcam photo are real cached NASA assets.
The ground-photo footprint is simulated, not an actual registered astronaut pose.

## Initial fixture

Mars analysis extent: 1,200×800 m. Habitat=(120,400); Delta Outcrop=(1080,400).
Area 14 supported observation footprint=[520,320]..[680,480] m within corridor.
Orbital expected interpretation: low-obstacle soil. Alpha direct route length:
960 m on a 40 m grid. Assumption A17: low obstacle density supports Alpha segment
3, target access and the declared retraced return corridor.

Existing seed labels corridor as "Traverse corridor", uses assumption-corridor
and one alpha-corridor segment. Align these with Area 14/A17 and exact mission
segment geometries at Gates 2/6/9. This is a required terminology/dependency fix.

## Required final demonstration

1. Open Mission Control. Cached NASA prior, Habitat, Delta Outcrop, Alpha and
   orbital-only Area 14 are visible.
2. Select/upload the cached known ground image. Real validated local perception
   executes; model version/calibration limitations are inspectable.
3. Show expected low obstruction versus observed high rock abundance/rough
   terrain; classify significant discrepancy when evidence supports it.
4. Explain A17 and Alpha segment 3/target/return dependence. Issue a clearly
   provisional safety warning when a possible safety consequence exists. Keep
   evidence provisional and Alpha coordinates unchanged.
5. Astronaut reviews and confirms with named reviewer and rationale. Preserve
   raw observation/inference, NASA prior and all decisions.
6. Only the supported footprint becomes ground-observed. Revised costs trigger
   A*; Beta avoids verified obstacles when preferable. Show actual Alpha/Beta
   lengths and WHY traced to evidence, assumption and decision.
7. Before/after comparison visibly separates prior from verified map knowledge.
8. Reload; restart backend; confirmed discovery remains.
9. Switch to future EVA. The next astronaut inherits verified knowledge and route
   reevaluation. Do not reset saved evidence to create that transition.
10. Repeat with external internet/NASA/model downloads blocked.

## Existing replay fallback

Current "Boulder field" selection reads a curated replay annotation, deliberately
labeled in the UI. It proves branch logic, verification/persistence/routing and
inheritance, and currently passes browser acceptance. It does **not** execute AI
on the NASA image. Matching soil/minor/weak/failure/dynamic fixtures use the same
photo with different scenario annotations; they are regression fixtures, not six
scientific observations of that photo. Keep them separate from the final
known-image inference acceptance.

For testing use the isolated DB created by scripts/e2e_backend.py. For a separate
judge rehearsal set MARSENSE_DATABASE_URL to a new .tmp/rehearsal.db before
starting the backend. Existing runtime database is never deleted automatically.
Do not add a public reset endpoint that erases mission history.

## Demo package and freeze

Must include exact bounded real imagery/ground assets, normalized terrain/DEM
and selected science/pose products, provenance/checksum manifest, validated local
model/inference, mission fixture, pinned software, startup scripts and demo steps.
Record data/model hashes and final commit; verify a cold offline start. Current
cache covers imagery/public-release photo only; required scientific/model work
keeps the complete competition demo gate open.
