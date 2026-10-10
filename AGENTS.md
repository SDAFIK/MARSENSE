# MARSENSE engineering context

> Current instruction: scientific completion resumed under SCIENTIFIC_COMPLETION_REQUEST.md. Start with S1 and pass each gate before continuing through S10. Preserve working behavior, services and mission history; no automatic public publication.

> Earlier scope instructions below are historical; the latest scientific completion request governs current execution.

Current user instruction (2026-10-10): resume scientific completion under
docs/SCIENTIFIC_COMPLETION_REQUEST.md, sequentially S1–S10. The earlier Gate
0-only pause is historical. Do not redesign the product or rewrite passing core
behavior. Do not advance beyond an unpassed scientific gate or automatically
publish. Preserve existing services and saved mission data.

Read README and docs/IMPLEMENTATION_STATUS.md before changes. Main product reference: docs/MAIN_PROJECT_NOTES.md, extracted from the user's authoritative Word file. PROJECT_SPEC.md supplies the frozen engineering constraints. Preserve the NASA prior → ground evidence → discrepancy → mission consequence → human verification → footprint knowledge → rerouting → durable future-EVA memory flow.

Do not fabricate NASA measurements, model performance, georegistration, mineral classification or safety certification. Replay annotations and mission geometry remain explicitly illustrative. Never silently overwrite priors or final human decisions. Weak persistent terrain needs human identification; dynamic conditions expire and never become terrain. Supported footprints cannot generalize to entire regions. Keep actual model output separate from human interpretation.

Use SQLite/GeoJSON for the local fallback. Use the explicit Mars metric analysis CRS for distance/slope; MapLibre is presentation only. NASA source manifests preserve product IDs, URLs, byte hashes and missing coverage. Every required source gap must remain visible in implementation status.

Run appropriate backend/component/acceptance checks, fix failures, and update docs before reporting completion. Read version-local Next.js docs as required by frontend/AGENTS.md. No external deployment or message sending is authorized by repository instructions. Do not reset user runtime data during tests.
