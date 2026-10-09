# MARSENSE — The Living Mars Map

NASA tells us what we expect. Astronauts show us what is actually there.
MARSENSE learns the difference. Every step makes Mars more known.

**Current task scope: Gate 0 only; implementation stopped by the user.**
[Ordered workflow review](docs/GATE_0_REVIEW.md) records to-spec, grilling,
domain-modeling, codebase-design and to-tickets, followed by consistency checks.
[Master prompt](docs/MASTER_PROMPT.md) is retained verbatim. Root contract files
define required acceptance; companion implementation summaries describe snapshots.
The existing runnable app below is preserved, not certification of later gates.

This NASA Space Apps prototype preserves orbital evidence, compares ground
observations with mission assumptions, requests human verification, updates only
the supported map footprint, reevaluates routes and passes verified discoveries
to the next EVA. Mission Control is the primary surface.

**Current readiness:** the user confirmed MARSENSE_Final_Project_Notes.docx as
the main project reference. It has been read and extracted in
[MAIN_PROJECT_NOTES.md](docs/MAIN_PROJECT_NOTES.md). The local acceptance flow
works; the full scientific data/model stack and authenticated browser access
remain incomplete. See [current implementation status](docs/IMPLEMENTATION_STATUS.md)
and [baseline audit](docs/BASELINE_AUDIT.md). This is not a deployment/freeze claim.

## Run the existing local demo

Requires Python 3.12+, Node compatible with the installed Next.js version, npm
and a browser. Dependencies/assets are already present on this workstation.
For a fresh checkout install from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item -LiteralPath .env.example -Destination .env
```

Then, from frontend:

```powershell
npm ci
```

Use .env for private local settings; never commit it. Start backend in one
terminal from the repository root:

```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal, from frontend:

```powershell
npm run dev
```

Open [Mission Control](http://127.0.0.1:3000/mission).
[API health](http://127.0.0.1:8000/api/health) and
[API docs](http://127.0.0.1:8000/docs) are local diagnostics.
The backend seeds a new SQLite database once and preserves existing evidence.
Demo runtime uses bundled/cache assets and makes no NASA service requests.
Internet is needed for a fresh dependency install or missing source assets.

## Demonstrate the current replay

Choose Boulder field, Analyze terrain, inspect expected/observed and provisional
consequence, confirm, see Route Beta and ground-observed footprint, reload, then
switch to future EVA. [DEMO_SCENARIO.md](DEMO_SCENARIO.md) describes the exact final
required flow and why replay is not completion of real AI acceptance.

Do not delete data/runtime to reset a judge demonstration. For a clean rehearsal
set a different MARSENSE_DATABASE_URL (for example sqlite:///.tmp/rehearsal.db)
in the backend terminal. Playwright already uses an isolated database.

## Data and inference claims

Cached imagery: controlled Jezero CTX/HiRISE crops and NASA/JPL-Caltech PIA26072
Navcam public-release mosaic. Habitat, science target, soil interpretation and
camera footprint are illustrative. No actual helmet camera, PLACES registration,
calibrated PDS imagery or measured soil strength is claimed. The map uses local
Mars metric coordinates for analysis; rendering is separate.

Curated replay fixtures do not run AI. Actual uploads run conservative OpenCV
texture analysis; optional MARSENSE_MODEL_PATH selects a local TorchScript
AI4Mars-class adapter after installing ai/requirements.txt. No validated trained
checkpoint is bundled. Human confirmation remains mandatory. Missing elevation
means slope is unavailable/excluded. [NASA_DATA.md](NASA_DATA.md),
[AI_PIPELINE.md](AI_PIPELINE.md) and [ROUTING_LOGIC.md](ROUTING_LOGIC.md) record
provenance, limitations and required remaining work.

## Validation and engineering reference

Commands and measured results: [TEST_PLAN.md](TEST_PLAN.md). The existing backend,
component and browser suites pass; the latest Ruff and Python typing checks pass.
The production frontend build passes, but the protected production workflow is
not yet integrated. [DEPLOYMENT.md](DEPLOYMENT.md) states release prerequisites.

- [Frozen specification and requirements](PROJECT_SPEC.md)
- [Architecture](ARCHITECTURE.md), [domain model](DATA_MODELS.md), [API contract](API_CONTRACT.md)
- [UI/design brief](UI_SYSTEM.md), [engineering decisions](docs/DECISIONS.md)
- [Ordered gates/tickets](IMPLEMENTATION_PLAN.md), [progress](STATUS.md)
- [Repository rules](AGENTS.md)

Secrets, dependencies, builds, test reports, temporary databases and user uploads
are ignored by Git. Required small cached NASA assets and their provenance are
retained; unnecessary archives are not downloaded. Production/competition freeze
requires all mandatory gates and blocker/high audit findings resolved.

## Current local delivery

[Launcher and locked setup](docs/LOCAL_RUN.md), [current NASA source status](docs/NASA_DATA.md), and [current implementation and remaining gates](docs/IMPLEMENTATION_STATUS.md) describe the latest executable code. The root contracts define the required final behavior; no later gate resumes
automatically after this Gate 0-only review. The launcher publishes no external deployment.
