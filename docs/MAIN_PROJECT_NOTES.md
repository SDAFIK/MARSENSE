# Main project reference

Source: MARSENSE_Final_Project_Notes.docx. Text extraction for implementation traceability; the original Word file remains authoritative.

MARSENSE

The Living Mars Map

Final Team Notes: Concept, Architecture, NASA Data, Cartography & Implementation



NASA Space Apps Challenge 2026

Locked Build Reference • Version 1.0

North-star statement

NASA tells us what we expect. Astronauts show us what is actually there. MARSENSE learns the difference.



This document consolidates the fixed project logic and the mapping/data principles discussed by the team.



1. Executive Summary

MARSENSE is a self-improving Mars exploration map for future astronauts. It begins with NASA-derived prior knowledge of terrain, elevation, science targets and environmental context. During a Marswalk, new astronaut camera or sensor evidence is compared against what the mission expected. If the difference is meaningful and affects a mission decision, MARSENSE raises an explainable alert, allows verification, updates local knowledge and recalculates relevant route information. Verified discoveries remain in the map so future explorers inherit better knowledge.

Public concept

A map that does not simply show Mars — a map that learns Mars.



Item

Frozen decision

Product name

MARSENSE

Product type

Evidence-aware Mars exploration decision-support system

Public concept

The Living Mars Map

Core AI idea

AI interprets astronaut observations as evidence; verified evidence improves map knowledge

Core logic

Expected → Observed → Difference → Significance → Mission Impact → Verify → Learn → Decide

Core user

Future Mars astronaut; secondary users are mission planners and planetary scientists

Prototype region

A small, real Mars exploration region, preferably Jezero Crater

Primary demo

Unexpected boulder-rich terrain challenges the route assumption; map learns and route changes



2. The Problem We Are Actually Solving

Future astronauts will already have sophisticated maps. The unresolved operational problem is that a Marswalk is planned from prior knowledge, while the astronaut will encounter human-scale details and current local conditions that prior orbital products may not fully capture. The system therefore must treat the map as a model of Mars, not as Mars itself.

Orbital data may not resolve small obstacles, trenches or local surface roughness.

Ground observations can confirm, refine or challenge prior interpretations.

Not every difference matters to the mission; unnecessary alerts create cognitive load.

New evidence should not blindly overwrite trusted NASA data.

Future explorers should inherit verified discoveries instead of rediscovering them.

Fundamental truth

The map is our current best understanding of Mars. Exploration changes that understanding.



3. First-Principles Logic

Why does a map exist? To support decisions.

Why can a decision become wrong? Because the information behind it may be incomplete, stale, uncertain, low-resolution or misinterpreted.

What changes when a human arrives? We gain immediate local evidence at human scale.

What should software do? Compare prior belief with new evidence, judge whether the difference matters, preserve provenance, and improve the next decision.

What is successful exploration? Gain useful new knowledge while remaining inside safety, time and resource constraints.

PRIOR KNOWLEDGE      ↓MISSION ASSUMPTIONS      ↓ASTRONAUT OBSERVATION      ↓EXPECTED ↔ OBSERVED      ↓DOES THE DIFFERENCE MATTER?      ↓VERIFY / UPDATE / REPLAN      ↓FUTURE EXPLORER



4. Core System Architecture

NASA DATA SOURCES  imagery • elevation • science • environment • rover observations                     ↓             PRIOR KNOWLEDGE MAP                     ↓            MISSION ASSUMPTION GRAPH                     ↓                PLANNED EVA                     ↓           CAMERA / SENSOR EVIDENCE                     ↓             AI PERCEPTION ENGINE                     ↓              DISCREPANCY ENGINE                     ↓         MISSION CONSEQUENCE GATE          /                     \    not relevant            mission relevant       ↓                         ↓     store                   alert + explain                                 ↓                         human verification                                 ↓                          living map update                                 ↓                          route recalculation                                 ↓                           future explorer



5. The Seven Core Engines

Engine

Purpose

Main output

1. Prior Knowledge

Build the starting view from NASA data and previous verified observations.

Expected terrain/science/environment + source metadata

2. Observation

Store geolocated astronaut camera/sensor evidence.

Evidence object with time, location, footprint and verification state

3. AI Perception

Interpret terrain features from astronaut imagery.

Segmentation/classes, rock abundance, roughness, confidence

4. Discrepancy

Compare current expectation with new evidence.

Match / minor / significant / conflicting / insufficient

5. Consequence Gate

Decide whether a discrepancy changes a route, target or safety assumption.

Store silently or create mission-relevant alert

6. Decision Support

Show affected assumptions and alternative actions.

Explainable options; astronaut retains authority

7. Living Memory

Preserve verified evidence for future missions.

Versioned map knowledge and exploration history



6. Most Important Logic

processObservation(observation):  region = locateObservation(observation)  prior = getCurrentKnowledge(region)  observed = runPerception(observation)  discrepancy = compare(prior, observed)  saveEvidence(observation, observed, discrepancy)  if discrepancy == NONE:      return RECORD_ONLY  dependencies = findMissionDependencies(region)  if dependencies is empty:      return RECORD_ONLY  impact = evaluateMissionImpact(discrepancy, dependencies)  if impact.safetyCritical:      createProvisionalSafetyAlert()  if not impact.isMissionRelevant:      return RECORD_ONLY  createMissionAlert()  generateDecisionOptions()  return WAIT_FOR_VERIFICATION



verifyEvidence(evidence):  evidence.state = GROUND_OBSERVED  updateRegionKnowledge(evidence)  affectedAssumptions = findAffectedAssumptions(evidence)  updateAssumptions(affectedAssumptions)  affectedRoutes = findAffectedRoutes(affectedAssumptions)  recalculate(affectedRoutes)  saveMissionEvent()  updateLivingMap()



7. Reliability and Evidence Rules

Rule

Implementation meaning

Never silently overwrite NASA evidence

Keep prior evidence and append/replace interpretation through versioned records.

Observation is not truth

AI output begins as provisional evidence.

Local evidence stays local

Every observation has a spatial footprint; do not generalize beyond it.

Safety and memory use different channels

Potential safety effects can warn provisionally; permanent map changes require verification.

Persistent vs dynamic

Terrain/geology can persist; dust/visibility/temperature can expire.

Human authority

Astronaut can confirm, reject or request more evidence.

Explainability

Every alert links back to source, observed change, affected assumption and consequence.

Fallback

If AI fails, retain last verified map and allow manual astronaut report.



Evidence state

Meaning

Orbital-only

No direct local observation available.

Provisional

New local evidence exists but is not yet operationally verified.

Ground-observed

Direct local evidence has been verified.

Multi-source confirmed

Independent sources agree.

Conflicting

Sources disagree and interpretation remains unresolved.

Superseded

A newer/better interpretation replaces an older one while preserving history.



8. NASA Data Stack — What We Actually Need

The project should not download “all Mars data.” Build a small, coherent Jezero package in which each source has one job. Raw PDS products should be preprocessed into tiles, GeoJSON, compact rasters or JSON before they reach the frontend.

NASA source

Role in MARSENSE

Priority

Mars Trek CTX / HiRISE mosaics

Regional and high-resolution basemap; zoom-dependent map context.

MUST

HiRISE DTM

Local elevation, slope and route terrain cost.

MUST

MOLA MEGDR

Global/regional elevation fallback.

MUST

Perseverance Navcam

Primary analog for astronaut terrain-camera observations.

MUST

Perseverance Mastcam-Z

Detailed ground imagery and visual/science context.

MUST

Mars 2020 PLACES

Ground-image localization, pose and real Mars position.

MUST

AI4Mars

Train/validate terrain segmentation and classification.

MUST

CRISM MTRDR/MRDR

Science/mineral context and science target layer.

MUST

MEDA

Optional local surface environmental observations.

SHOULD

Mars Climate Sounder

Optional regional atmospheric context.

SHOULD

MARCI

Optional dust/cloud regional imagery.

OPTIONAL

SuperCam / SHERLOC / PIXL

Optional ground science evidence.

OPTIONAL

SHARAD

Optional subsurface evidence.

OPTIONAL

SPICE kernels

Advanced coordinate/time/instrument geometry.

OPTIONAL



9. Dataset Relationship That Powers the Core Demo

HiRISE / CTX“What did we expect from orbit?”        +PLACES“Exactly where are we?”        +Navcam / Mastcam-Z“What did we actually see?”        +AI4Mars model“What terrain does the image contain?”        ↓EXPECTED ↔ OBSERVED        +HiRISE DTM“Does this matter to the route?”        +CRISM“Why is this location scientifically interesting?”



Dataset freeze for the winning MVP

Mars Trek CTX + HiRISE, HiRISE DTM, MOLA, CRISM, Perseverance Navcam/Mastcam-Z, PLACES, and AI4Mars. Add MEDA/MCS only after the core loop is working.



10. Data Preparation Strategy

Raw source

Processed product consumed by app

CTX / HiRISE imagery

Web map tiles / cached demo tiles

HiRISE DTM

Elevation raster + derived slope raster

MOLA

Low-resolution elevation raster

CRISM

Small science GeoJSON polygons or GeoTIFF layer

Navcam / Mastcam-Z

Evidence image files with metadata

PLACES

Compact coordinates/pose records

AI4Mars

Model weights + class definitions

MEDA / MCS

Time-series JSON / compact regional layer



data/├── nasa/│   ├── mars_trek/{ctx,hirise}│   ├── dem/{hirise,mola}│   ├── crism/│   ├── perseverance/{navcam,mastcamz,places,meda}│   └── ai4mars/├── processed/│   ├── terrain/│   ├── elevation/│   ├── slope/│   ├── science/│   ├── evidence/│   └── routes/└── demo/    ├── mission.json    ├── route_alpha.geojson    ├── route_beta.geojson    ├── observations.json    └── events.json



11. Cartography & Spatial-Visualization Principles

The CARTO examples are design references, not scientific datasets. Their strongest lesson is that modern spatial systems should convert large, changing geospatial data into understandable decisions. For MARSENSE, this means dynamic layers, user-controlled filters, route comparison, before/after views, time-aware evidence and concise AI explanations rather than overwhelming the astronaut with raw GIS.

Spatial-analytics pattern

MARSENSE use

Dynamic map tiles

CTX at regional zoom, HiRISE at local zoom, astronaut evidence at human scale.

Real-time/dynamic updates

New ground observations and mission events appear without reloading the full map.

User-controlled filters

Toggle terrain, route, science, evidence state, elevation, knowledge gaps.

Heatmaps / hotspots

Optional knowledge-coverage or observation-density view.

Route optimization

Compare original route vs updated route after evidence changes.

Time filtering

Pre-EVA → EVA 01 → EVA 02 → Current knowledge.

GenAI explanation

WHY button translates structured mission changes into plain language.

Raw data → insight

Do not show sensor values without explaining what they change operationally.



UX rule

Do not show data when you can show meaning; do not show meaning when you can support a decision.



12. Map Projection & Coordinate-System Decision

Map projections always trade off area, shape, distance, direction or appearance. Therefore MARSENSE must choose a projection for the mission task, not because it is familiar from Earth web maps. The operational Jezero map should use a Mars-appropriate local/equirectangular projected coordinate system consistent with the NASA source products. Earth Web Mercator can be a rendering convenience, but Earth distance formulas must not be used for scientific route calculations.

View

Recommended representation

Purpose

Global Mars / landing page

3D globe or global Mars overview

Storytelling and navigation to Jezero; no critical route math.

Operational Jezero map

Mars equirectangular / local projected x-y meters

Distance, route, evidence footprint, DEM, slope and layer alignment.

Backend analysis

Projected x-y in meters wherever possible

Clean geometry, routing and overlap calculations.



NASA lat/lon or source projection        ↓Mars coordinate transform        ↓Local Jezero x/y meters        ↓HiRISE + CTX + DEM + CRISM + routes + evidence footprints        ↓One shared analysis coordinate system



Critical developer warning

Leaflet/MapLibre may assume Earth geometry. Use them for rendering if convenient, but perform distance, area and route calculations with Mars-specific/local projected coordinates.



13. Zoom and Time as Two Dimensions of Knowledge

ZOOM / SPATIAL DETAILMOLA → CTX → HiRISE → ASTRONAUT OBSERVATIONTIME / KNOWLEDGE EVOLUTIONORBITAL-ONLY → PROVISIONAL → GROUND-OBSERVED → MULTI-SOURCE CONFIRMED



This gives the interface two complementary dimensions: spatial resolution and knowledge maturity. As the user zooms closer, the map can reveal higher-resolution sources; as exploration progresses, the same location can move from orbital-only to verified ground-observed knowledge.

14. Final Website Information Architecture

Screen

Purpose

Essential content

1. Landing / Mission Intro

Explain the concept immediately.

Hero: “A Mars map that learns from every astronaut.” Start Mission button.

2. Mission Control

Main operational interface.

Mars map, route, astronaut, targets, evidence status, mission panel, event timeline.

3. Astronaut View

Minimal decision interface.

Next target, route status, knowledge status, critical evidence alert, WHY/COMPARE.

4. Evidence Inspector

Trace what the system believes and why.

Current interpretation + all supporting/conflicting evidence and verification state.

5. Exploration Memory

Show how the map learned over time.

Chronological events and previous astronaut discoveries.

6. Before / After control

Core demo visual.

Compare prior map and updated post-EVA knowledge.



15. Mission Control Layout Notes

┌──────────────────────────────────────────────┐│ MARSENSE       MISSION 01       EVA ACTIVE   │├──────────────────────────────┬───────────────┤│                              │ MISSION STATUS││          MARS MAP            │ target        ││                              │ distance      ││  route • astronaut • POIs    │ route state   ││  evidence overlays           │ knowledge     ││                              │ evidence      │├──────────────────────────────┴───────────────┤│ TIMELINE / EVIDENCE EVENTS                  │└──────────────────────────────────────────────┘



Default astronaut view stays sparse; Mission Control can expose richer layers.

Use color plus icon/text so evidence states remain accessible.

Avoid a single mysterious “risk score.” Show terrain condition, evidence state and mission consequence separately.

Before/after visual comparison is more persuasive than simply replacing Route Alpha with Route Beta.

Use the WHY button to explain structured backend results; the LLM explains, it does not decide.

16. Routing Logic

The MVP does not need advanced rover navigation. Convert the local map into a cost grid and run A* or Dijkstra. The key is that verified evidence can change a region’s traversal and uncertainty costs, causing the route to update.

Cell condition

Illustrative prototype cost

Easy / well-known terrain

1

Moderate terrain

3

Rough terrain

6

High hazard / newly challenged area

20

Blocked

∞



A simple knowledge-aware route objective is:RouteCost = DistanceCost + TerrainCost + UncertaintyCost

Orbital-only terrain can carry an uncertainty penalty.

Ground-observed safe terrain can carry a smaller uncertainty penalty.

Confirmed obstacle-rich terrain receives high terrain cost.

Prototype thresholds are configuration values, not NASA-certified EVA safety limits.

17. AI Pipeline

Astronaut / rover ground image        ↓Image preprocessing        ↓Terrain segmentation model        ↓class proportions + segmentation mask        ↓terrain interpretation (rock abundance / roughness)        ↓compare with prior expectation        ↓provisional evidence object



AI4Mars is the training/validation foundation for terrain perception.

MVP classes: soil, sand, bedrock, large rock, rough terrain, obstacle-rich terrain.

Camera imagery cannot legitimately infer exact mineral chemistry, radiation, soil toxicity or subsurface ice.

Model confidence does not equal mission truth; operationally important results remain provisional until verification.

Future sensors can plug into the same evidence system without changing the architecture.

18. Core Data Model

Region {  id, geometry, expected_terrain, current_terrain, knowledge_state, updated_at}Evidence {  id, region_id, source, source_type, timestamp, location, footprint,  observation_type, observed_value, model_confidence, verification_state, persistence}MissionAssumption {  id, statement, evidence_ids[], status, affected_route_segments[], affected_targets[]}Route {  id, name, geometry, distance, cost, status}MissionEvent {  id, timestamp, type, description, related_evidence, related_assumption}



19. Recommended Backend Endpoints

GET  /api/map/regionsGET  /api/regions/{id}GET  /api/regions/{id}/evidenceGET  /api/routesPOST /api/routes/planPOST /api/routes/recalculatePOST /api/observationsPOST /api/observations/{id}/verifyGET  /api/assumptionsGET  /api/observations/{id}/impactGET  /api/events



20. Recommended Tech Stack

Layer

Recommendation

Frontend

Next.js + React + TypeScript + Tailwind CSS

Map

MapLibre GL or Leaflet; MapLibre preferred if team is comfortable

Backend

Python + FastAPI

Database

PostgreSQL/PostGIS if familiar; otherwise SQLite + GeoJSON for hackathon simplicity

AI

PyTorch + OpenCV; DeepLabV3-style segmentation is a practical starting point

Geospatial

GeoPandas, Shapely, Rasterio, GDAL, NumPy, NetworkX



21. Repository Structure

marsense/├── frontend/│   ├── app/│   ├── components/{Map,MissionPanel,EvidencePanel,AstronautHUD,Timeline}│   ├── services/│   ├── hooks/│   └── types/├── backend/app/│   ├── api/│   ├── models/│   ├── schemas/│   ├── services/{evidence,discrepancy,assumptions,routing,mission}.py│   └── db/├── ai/{models,inference,preprocessing,training}/├── data/{nasa,processed,demo}/├── notebooks/├── docs/└── README.md



22. Fixed Build Order

Render one Jezero Mars map.

Load one NASA-derived image layer.

Display habitat and at least one science target.

Generate Route Alpha.

Create region/evidence storage.

Upload/select a ground image.

Run terrain AI and return structured observation.

Compare expected vs observed.

Create discrepancy and mission-dependency result.

Show mission-relevant alert.

Verify observation.

Update knowledge state.

Recalculate route.

Build before/after comparison.

Persist evidence and demonstrate a future explorer inheriting it.

Only then add optional environment/LLM/3D features.

Scope rule

A complete 5-feature loop beats an unfinished 25-feature platform. Do not add optional features until the full expected→observed→impact→verify→learn→reroute loop works.



23. Feature Priority

Priority

Features

MUST HAVE

Mars map; NASA-derived layer; planned route; ground image; AI terrain analysis; expected-vs-observed comparison; mission relevance check; verification; living map update; route recalculation; before/after view; future-explorer memory.

SHOULD HAVE

Evidence inspector; event timeline; science targets; route comparison; knowledge-status overlays.

NICE TO HAVE

Environmental layer; natural-language explanation; voice; 3D terrain; knowledge-gap heatmap.

DO NOT PRIORITIZE

Whole-Mars 3D globe; AR hardware; medical AI; exact radiation forecasting; generic chatbot; automatic life detection.



24. Locked Demo Story

Scene

What judge sees

1. Pre-EVA

Area 14 appears low-obstruction; evidence is orbital-only; Route Alpha is planned.

2. Observation

Helmet/ground image arrives; AI detects high rock abundance.

3. Comparison

Expected: low obstruction. Observed: dense boulders.

4. Consequence

Mission assumption challenged; Route Alpha segment is affected.

5. Verification

Astronaut confirms the evidence.

6. Learning

Area 14 becomes ground-observed; the old NASA evidence is preserved in history.

7. Replan

Route Beta appears and the WHY explanation shows exactly why.

8. Future explorer

Next EVA starts with the verified boulder-field knowledge already visible.



Demo “wow” moment

Do not make the rotating Mars globe the wow moment. Make the map-belief change the wow moment: BEFORE EVA → new ground evidence → ASSUMPTION CHALLENGED → AFTER EVA → route moves.



25. Scientific & Communication Boundaries

Do not claim NASA lacks Mars maps or autonomous navigation.

Do not claim one camera image is automatically ground truth.

Do not label regional orbital atmospheric products as street-level live weather.

Do not create exact radiation, oxygen or metabolic numbers without a valid source/model.

Do not say AI discovers minerals from RGB images; use CRISM or appropriate instruments for mineral evidence.

Do not claim “nobody has ever done this.” Position MARSENSE around the integration of prior assumptions, new evidence, decision relevance and persistent exploration memory.

Do not replace source provenance with an unexplained single risk score.

26. Final Frozen Decisions

Decision

Final choice

Core identity

MARSENSE — The Living Mars Map

Core product behavior

Self-improving map that learns from verified astronaut evidence

Core engineering idea

Mission-assumption validation and consequence propagation

Core UX rule

Interrupt the astronaut only when new evidence changes a decision or potentially affects safety

Primary data region

Jezero Crater / small real Mars corridor

Primary camera analog

Perseverance Navcam; Mastcam-Z for detail/science visuals

AI dataset

AI4Mars

Position link

Mars 2020 PLACES

Basemap

NASA Mars Trek CTX + HiRISE

Terrain

HiRISE DTM + MOLA fallback

Science layer

CRISM processed products

Projection

Mars-appropriate local/equirectangular analysis projection

Route algorithm

A* / Dijkstra on knowledge-aware terrain cost grid

Optional environment

MEDA + Mars Climate Sounder after core MVP

Final demo

Unexpected boulder field → assumption challenged → verify → map learns → reroute → next astronaut benefits



27. Source & Reference Library

These references support the project’s NASA-data stack, mapping approach and spatial-visualization notes. They are not all equal in scientific authority: NASA/PDS sources are primary data references; CARTO/Future Maps are design/cartography references.

[1] NASA Mars Trek WMTS / map layershttps://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars

[2] NASA Mars Trekhttps://trek.nasa.gov/

[3] HiRISE DTM archive / Jezero exampleshttps://hirise.lpl.arizona.edu/dtm/

[4] MOLA MEGDR archivehttps://pds-geosciences.wustl.edu/missions/mgs/megdr.html

[5] NASA AI4Mars datasethttps://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars

[6] Mars 2020 PLACEShttps://pds-geosciences.wustl.edu/missions/mars2020/places.htm

[7] CRISM archivehttps://pds-geosciences.wustl.edu/missions/mro/crism.htm

[8] Perseverance Navcam calibrated productshttps://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn:nasa:pds:mars2020_navcam_ops_calibrated

[9] Mastcam-Z calibrated productshttps://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn:nasa:pds:mars2020_mastcamz_sci_calibrated

[10] MEDA archivehttps://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/PERSEVERANCE/meda.html

[11] Mars Climate Sounder informationhttps://science.nasa.gov/mission/mars-reconnaissance-orbiter/science-instruments/

[12] CARTO: 24 of the best maps, visualizations & analysis from 2024https://carto.com/blog/2024-best-maps-dataviz/

[13] Future Mapping Company: Top 10 World Map Projectionshttps://futuremaps.com/blogs/newstop-10-world-map-projections

28. Final One-Page Team Reminder

What are we building?

A Mars exploration map that begins with NASA prior knowledge, learns from verified astronaut-scale evidence, and changes only when new evidence matters to a mission decision.



What is the most important loop?

EXPECTED → OBSERVED → DIFFERENCE → MISSION IMPACT → VERIFY → LEARN → REROUTE



What are the minimum NASA sources?

Mars Trek CTX/HiRISE + HiRISE DTM + MOLA + CRISM + Perseverance Navcam/Mastcam-Z + PLACES + AI4Mars.



What must the judge remember?

Astronaut 2 should not need to rediscover what Astronaut 1 already learned.



What should we never forget?

The map is not Mars. It is our current knowledge of Mars — and exploration should make that knowledge better.

