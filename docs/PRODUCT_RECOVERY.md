# MARSENSE Product Recovery — competition release contract

Status: recovery baseline, not a completed release. Original submission: https://github.com/SDAFIK/MARSENSE. Default branch master remains unchanged pending acceptance. Baseline 48605ea; cloud PostgreSQL acceptance passed (43529086175), hosted smoke failed (43529086402: approved origin 403). Render health and 22 seeded records / 2 missions / 1 operator were verified before recovery. No prior private local data will be imported.

## Product outcome
For NASA Space Apps Interplanetary Survival Guide: Martian Map, a judge should understand in one guided three-minute journey how ground evidence corrects a bounded orbital assumption, changes a modeled traverse and informs the next EVA. No login or installation. MARSENSE is experimental decision support, not certified navigation.

## Requirements and evidence matrix
| ID | Requirement | Existing implementation | Recovery acceptance |
| --- | --- | --- | --- |
| P0-01 | Direct guest entry | /, /api/public-demo/start | Public URL, one click, 201, mission screen; no Vercel SSO or account |
| P0-02 | EXPECT | /mission, seed, NASA cache | Jezero map, A17, Alpha, source and illustrative labels; readable legend |
| P0-03 | OBSERVE | /astronaut, /api/public-demo/observations/demo | Area 14 curated replay, explicit simulation label, evidence created |
| P0-04 | COMPARE | /evidence, /comparison | Aligned source/ground evidence, uncertainty and actual mission consequence |
| P0-05 | VERIFY | evidence verify API | Confirm/reject/request evidence, identity/guest attribution, no automatic confirmation |
| P0-06 | LEARN | routing, knowledge, mission snapshot | Supported footprint only, Alpha retained, Beta changes, real persisted guest state |
| P0-07 | INHERIT | /memory, EVA-02 | Confirmed discovery visible in next mission; dynamic evidence expires |
| P0-08 | RESET | guest-only reset API | Repeatable story; no mutation to operator or another guest |
| P0-09 | Reliability | Render + Supabase + Vercel | Exact origin, same-origin API, cold-start/error/retry UX; no local PC |
| P0-10 | Responsive/accessibility | existing CSS and browser tests | 360/390/768/1440 widths; no horizontal overflow, keyboard controls, reduced motion |
| P1-01 | Optional private workspace | /signup, /workspace-login, workspaces API | Signup/login/logout/restart persistence, account isolation, real upload with size limits |
| P1-02 | Operator access | /login, /account, invite API | Separate admin login, invitations, permission checks; never required for demo |
| P1-03 | Science transparency | source matrix, scientific audit | Source IDs/links, genuine vs illustrative, classifier limitations, no invented telemetry |
| P1-04 | Release docs | README and guides | Same repository root, verified public URL, reproducible setup, 3-min walkthrough, limitations |

## Experience specification
Landing: real NASA imagery, concise problem/solution, primary Launch Mission; secondary Science and Workspace links. No fake telemetry. Mission Control: full dominant map, compact status and a single contextual action panel; six-step progress EXPECT → OBSERVE → COMPARE → VERIFY → LEARN → INHERIT. Map layer/route toggles, accessible legend, fit and zoom. Field mode: mobile-first capture/replay, location/footprint, route impact, return to mission. Evidence: side-by-side orbital/ground, source provenance, inference vs human interpretation, decision consequences. Living map: aligned before/after, Alpha and Beta legend, localized change, EVA-02 inheritance and timeline. Science: real products, processing limits, illustrative footprints and mission assumptions. Optional account flows remain behind secondary entry. Visual direction proposal: deep charcoal, rust/orange for uncertainty, mint for verified route, warm NASA imagery, legible type and calm restrained motion.

## Design and engineering stages
1. Recovery inventory (this document); separate source audit from visual/live acceptance.
2. Review current screenshots at 1440x900, 768x1024, 390x844, 360x800 and establish visual target before UI edits. Compare the six-step journey against existing code.
3. Stabilize public origin configuration, prove real guest start/mission/reset and full evidence loop, negative-origin and isolation tests. Prefer stable public origin; no wildcard or disabled CSRF.
4. Implement cohesive mission-first navigation and screen hierarchy; reuse real map, domain APIs, images. Include loading/retry/error/empty states and no dead buttons.
5. Run full browser journey with actual API responses; repeat as two independent guests. Verify cold start and reset, mobile touch/keyboard.
6. Test optional workspace and operator flows with disposable test data; never reset production. Verify upload/decision persistence and permissions.
7. Stage exact release commit on Vercel, inspect desktop/mobile screenshots and run hosted browser tests. Record HTTP status, expected and actual outcomes; do not use screenshots or health as a substitute for functional acceptance.
8. Merge reviewed changes into original master only after required CI and hosted gates pass. Update README with confirmed public URL and competition narrative. Promote tested release, check unauthenticated public access, retain previous rollback target.

## Release gates
- Every P0 requirement passes on exact deployed commit; P1 claims tested or explicitly labeled unavailable.
- No broken primary actions, inaccessible page, SSO wall, overflow or unhandled network error.
- Source provenance, scientific limits and simulation labels visible.
- Existing production data and local backups preserved. No paid service or unrelated project changes.
- Record build/deploy IDs, commit SHA, automated tests and live screenshots. Failure blocks promotion.
- Free Render may sleep; provide visible reconnect/loading and bounded retry, not a false always-on guarantee.

## Current blockers / decisions
Hosted smoke has confirmed 403 for intended origin; Blueprint configuration fix committed on cloud branch but application not verified. Browser page inspection from Chat is read-only, and authenticated full browser acceptance is still missing. This recovery branch is based on the cloud candidate, not master, to preserve pending work; do not merge stacked draft PRs blindly. No page redesign or functional release claimed by this document.
