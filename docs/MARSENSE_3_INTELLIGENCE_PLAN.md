# MARSENSE 3.0 intelligence upgrade — staged delivery

The existing cinematic competition release remains production. This branch extends it without altering production data or relaxing human verification.

## Phase 1 — research foundation (first implementation)
- Audit genuine AI4Mars splits, exact bytes, site isolation and class support.
- Baseline: existing small U-Net, held-out mean IoU 0.099405; Perseverance transfer 0.132736.
- Compare pretrained segmentation candidates (SegFormer / DeepLabV3+), use a larger genuine subset and freeze independent rover/site holdouts.
- Research screen: validation/test mIoU >= 0.40, transfer >= 0.35, all class recalls >= 0.20; these are engineering screening thresholds, not NASA standards. Passing does not enable mission classification. Calibration, error analysis and review required.
- Reproducible dataset/model hashes, per-class metrics, runtime and memory budgets; no checkpoint in production without review.

## Phase 2 — real-image inference
Versioned model adapter, bounded segmentation masks, uncertainty/abstention, original image and inference provenance, secure private upload. Human review mandatory; no guessed confidence. Demonstrate unseen images distinct from curated replay.

## Phase 3 — localization
Use calibrated camera metadata and PLACES pose, explicitly distinguish camera position from ground footprint. Add manual map placement, spatial uncertainty and validation against known products. Unknown location cannot update map.

## Phase 4 — mission planning
Expand current dependency and A* engine to multiple evidence geometries, alternative routes and explicit no-route outcomes. Preserve the original prior and explain changed costs. No safety guarantees.

## Phase 5 — memory
Extend existing versioned knowledge, conflicts, supersession and dynamic expiry across missions. Store reviewed labels separately for offline retraining, never automatic model updates.

## Phase 6 — product integration and release
Two clear entrances: guided no-account judge path and advanced private workspace. Design system retains cinematic dark aerospace palette, clear amber challenge/mint verified states, map-first layouts, accessible keyboard/mobile controls, reduced motion. Judge path emphasizes one next action at a time and before/after evidence. Advanced lab exposes masks, uncertainty, metadata and provenance on demand. Release gates: scientific validation, exact candidate CI, responsive real screenshots, guest/private isolation, upload and restart persistence, public production acceptance. No paid services or production database changes without explicit scope.

The first research candidate is implemented in `ai/train_candidate.py` (DeepLabV3 MobileNetV3, general-image pretrained; independent validation, test and transfer metrics; TorchScript output explicitly disabled for mission classification). The isolated research workflow can train it against the frozen genuine subset. This is not yet a trained improved model or a larger dataset. Subsequent phases remain open until implemented and validated.

## Current candidate record — 2026-11-14
- Real research training completed: [run 43575334860](https://github.com/SDAFIK/MARSENSE/actions/runs/43575334860), 88 genuine images, 55 site groups, 4 epochs. Validation mIoU 0.4431, held-out MSL 0.5296, Perseverance transfer 0.1306. Rock recall 0 on held-out MSL and 0.0181 on transfer. Research screen FAILED; never enable this model. See [research report](science/V3_RESEARCH_REPORT.md).
- Phase 2: bounded indexed-PNG model masks, per-pixel score withholding and explicit evidence display implemented. No mask for replay/fallback. Model classification remains disabled.
- Phase 3: local-map manual placement, explicit confirmation, optional observer-estimated uncertainty, retained provenance. Automatic calibrated photo geolocation remains open.
- Phase 4: bounded read-only A* candidate search, actual route segment geometry overlays, distance and modeled cost comparison. No active-route mutation on search.
- Phase 5: private confirmed-real-ground research manifest export with hashes and footprint; curated replay and superseded data excluded. Broader mission registry and actual training labels remain open.
- Phase 6: /guide, adaptive mission guidance, premium responsive styles and acceptance checks. Final exact-candidate CI, visual review and release remain gates. Production baseline unchanged.

### Follow-up: localization provenance and release engineering
- Corrected tensor typing and React render-time clock purity; new exact candidate requires full CI.
- The camera context independently checks the cached product clock/RMC association, PLACES site/drive position, and local coordinate transform. Relative easting/northing consistency is reported as arithmetic consistency, not absolute pose error. The UI locates the actual NASA drive anchor separately from evidence geometry; ground footprint and uncertainty stay unknown.
- Automatic image-to-ground localization remains blocked on registered stereo/XYZ range data, exact image pose transforms and independent error validation. No drive anchor is converted into a verified terrain footprint.

## Engineering release — November 14, 2026
- Exact tested candidate `60ff85475d7d54e4171f6c867012a37545cbede7`: [release validation](https://github.com/SDAFIK/MARSENSE/actions/runs/43577199146), 179 passed (84 backend, 26 component, 62 browser, 1 authenticated, 5 production-mode, 1 showcase); 2 skipped. PostgreSQL, cloud smoke and container smoke passed separately.
- Render deployment `dep-dbs2fi2fngtc73bhmiag` is live at the exact candidate; existing public proxy health returned 200. PR #7 merged as `8a4de164c4408bbfd5946f0395ff41f6f6632bd9`, source identical to tested candidate.
- Vercel production deployment `dpl_E2hTkFtWD8i7kcinfoQcGTTEVqsf` READY, original domain assigned to `8a4de16`. [Public V3 acceptance](https://github.com/SDAFIK/MARSENSE/actions/runs/43580317544) passed: guide, guided mission, seven screens, route alternatives, NASA drive anchors, replay export exclusion, human review, reroute, inheritance and exit. Live landing, guide and API health returned 200; no error/fatal Vercel runtime logs in the checked 15-minute window. Existing database unchanged; no trained classifier enabled.
