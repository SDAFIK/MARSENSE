# MARSENSE engineering context

Current user instruction (2026-10-10): stop implementation and complete Gate 0
only. Run Toolkit to-spec, grilling, domain-modeling, codebase-design and
to-tickets in that order, then cross-check all required documents. Do not resume
application implementation or later gates until the user explicitly resumes it.
Existing services and saved mission data are preserved; stopping implementation
does not authorize terminating processes or resetting mission history.

Read README and docs/IMPLEMENTATION_STATUS.md before changes. Main product reference: docs/MAIN_PROJECT_NOTES.md, extracted from the user's authoritative Word file. PROJECT_SPEC.md supplies the frozen engineering constraints. Preserve the NASA prior → ground evidence → discrepancy → mission consequence → human verification → footprint knowledge → rerouting → durable future-EVA memory flow.

Do not fabricate NASA measurements, model performance, georegistration, mineral classification or safety certification. Replay annotations and mission geometry remain explicitly illustrative. Never silently overwrite priors or final human decisions. Weak persistent terrain needs human identification; dynamic conditions expire and never become terrain. Supported footprints cannot generalize to entire regions. Keep actual model output separate from human interpretation.

Use SQLite/GeoJSON for the local fallback. Use the explicit Mars metric analysis CRS for distance/slope; MapLibre is presentation only. NASA source manifests preserve product IDs, URLs, byte hashes and missing coverage. Every required source gap must remain visible in implementation status.

Run appropriate backend/component/acceptance checks, fix failures, and update docs before reporting completion. Read version-local Next.js docs as required by frontend/AGENTS.md. No external deployment or message sending is authorized by repository instructions. Do not reset user runtime data during tests.
