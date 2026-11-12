# MARSENSE engineering context

## Current working agreement — 2026-10-21

Read and follow [the full user-supplied product engineering workflow](docs/PRODUCT_ENGINEERING_WORKFLOW.md).
It governs how requested work is inspected, previewed, implemented and verified.
Default to **PREVIEW-FIRST**. For major UI changes, new pages, features or
redesigns: inspect the current implementation, explain the expected result,
show an inspectable preview (desktop/mobile when relevant), give a compact
change and verification plan, then wait for the user's approval before major
implementation. AUTOPILOT applies only when the user explicitly selects it.
Minor implementation details already covered by an approved plan do not need
repeated approval.

Preserve the existing stack, approved design system, working functionality,
user modifications, services and saved mission history. Implement requested
features in small verified vertical slices. Trace UI actions through API,
validation, business logic and persistence; distinguish mocks from real
integrations. Do not introduce unrelated features or architectural rewrites.

Use CURRENT MILESTONE / COMPLETED / NEXT / ISSUES for substantial progress
updates. Report applicable checks as PASS, FAIL or NOT RUN; preserve the date
and scope of older test evidence rather than presenting it as a fresh run.
Inspect actual browser behavior, responsive layouts, motion and errors when
relevant. Never invent screenshots, scientific claims or performance results.
Keep existing status documents current and report external blockers precisely.

The workflow adoption itself does not authorize a new redesign, hosting
purchase, database migration or resumption of deferred backend deployment.
The GitHub repository was made public at the user's explicit request; source
publication is distinct from a verified live application deployment.

## Scientific and product constraints

When scientific completion resumes, use docs/SCIENTIFIC_COMPLETION_REQUEST.md
and the recorded S1–S10 gate evidence. Do not restart passed gates without cause
or advance beyond an unpassed gate. Earlier Gate 0-only pauses are historical.
Preserve passing core behavior and keep unresolved scientific reliability
limits visible even where prototype workflow checks pass.

Read README and docs/IMPLEMENTATION_STATUS.md before changes. Main product reference: docs/MAIN_PROJECT_NOTES.md, extracted from the user's authoritative Word file. PROJECT_SPEC.md supplies the frozen engineering constraints. Preserve the NASA prior → ground evidence → discrepancy → mission consequence → human verification → footprint knowledge → rerouting → durable future-EVA memory flow.

Do not fabricate NASA measurements, model performance, georegistration, mineral classification or safety certification. Replay annotations and mission geometry remain explicitly illustrative. Never silently overwrite priors or final human decisions. Weak persistent terrain needs human identification; dynamic conditions expire and never become terrain. Supported footprints cannot generalize to entire regions. Keep actual model output separate from human interpretation.

Use SQLite/GeoJSON for the local fallback. Use the explicit Mars metric analysis CRS for distance/slope; MapLibre is presentation only. NASA source manifests preserve product IDs, URLs, byte hashes and missing coverage. Every required source gap must remain visible in implementation status.

Run appropriate backend/component/acceptance checks, fix failures, and update docs before reporting completion. Read version-local Next.js docs as required by frontend/AGENTS.md. No external deployment or message sending is authorized by repository instructions. Do not reset user runtime data during tests.
