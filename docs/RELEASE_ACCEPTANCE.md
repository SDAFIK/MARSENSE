# MARSENSE release acceptance (2026-11-13)

Team Redscape. This is the engineering release record, not an operational EVA certification.

## Immutable baseline evidence

- Hosted baseline: `c9268192d00504f04cad539ae71026ee22d66bd9`.
- [Application release validation #28](https://github.com/SDAFIK/MARSENSE/actions/runs/43332517324): 71 backend, 12 component, 24 browser, 1 authentication, 1 real-upload production-mode browser, 1 showcase browser case; 110 passing total.
- [Production container smoke #22](https://github.com/SDAFIK/MARSENSE/actions/runs/43332517315): successful.
- Fresh loaded desktop/tablet/mobile screenshots inspected: homepage, login, mission, astronaut, evidence, comparison, memory. Mobile comparison terrain has letterboxing and long stacked panels; pixel equivalence and full accessibility certification not claimed.
- Existing host: https://desktop-sdfik.tailf13324.ts.net ; health 200; production session reports replay disabled.
- Vercel staging: https://redscape-nzyvxnmnx-sadib-dewans-projects.vercel.app ; READY, homepage, health, login, session and NASA HiRISE image 200.
- Host upgrade retained the named mission volume. Private backup and live SQLite integrity both ok. Original records 24, current 26, missing 0, changed non-session records 0, added 2. Record-level preservation verified; full restore rehearsal remains open.

## Master-instruction F1–F11 mapping

| Gate | Implemented baseline | Remaining release evidence / limits |
|---|---|---|
| F1 Secure application | Cookie sessions, authorization, upload checks, named SQLite store, private bootstrap identities | New candidate invite-only registration; test expiry, role denial, persistence and browser access; actual hosted login/logout |
| F2 Homepage | Real cached Navcam, cinematic visual language, product journey | New exact-head responsive screenshots and manual inspection |
| F3 Mission dashboard | Actual mission state, map, evidence, routes, activity | Six required viewport classes and hosted navigation |
| F4 Living Map | MapLibre, real cached CTX/HiRISE, local metric geometry, layers, focus and overlays | Map error/fallback and hosted browser; bounded illustrative geometry |
| F5 Observation | Validated JPEG/PNG, manual footprint, original and derivative hashes | New candidate actual preview and observation notes; new retry path |
| F6 AI | OpenCV actual features; optional TorchScript adapter; explicit abstention | New candidate null confidence for untrained heuristic, immutable original + inference retry; genuine private checkpoint scientific gate not in CI |
| F7 Evidence | Provenance, provisional and final decisions, authenticated reviewer, persistent history | New candidate exposes saved metadata and retry attempts; actual hosted UI |
| F8 Living update | Footprint-bounded cost changes, immutable prior, confirmed evidence, reload persistence | Hosted full journey; no scientific claim of actual surface discovery |
| F9 Route planning | Deterministic Mars metric A*, Alpha/Beta, no-route behavior | Scientific slope coverage/operational safety limits; no invented path |
| F10 Memory | Persistent events, versions and future EVA inheritance | Hosted journey and history navigation; additional search/filter enhancements may be evaluated separately |
| F11 Release | CI, Docker, live upgraded baseline, connected staging, verified preservation | New exact-head CI, backup restore rehearsal, hosted isolated showcase and authentication, final merge/promotion |

## New candidate changes

Invite-only registration uses existing private operator bootstrap accounts and transactionally stored registered accounts. Admin issues a random one-time 24-hour code; only its hash is stored. The role is fixed in the invitation, never ADMIN. Registration disabled in local demo, read-only and showcase. Registered accounts can be disabled without altering bootstrap identities. No production records changed by development or test runs.

OpenCV retains measured edge fraction and contrast, reports no numerical confidence, and requires human identification. Unexpected inference exceptions record unavailable provisional evidence, original bytes and a sanitized derivative. Retry validates both saved hashes, uses an idempotency request ID, appends a processing-attempt entity and updates only pending evidence; original observations remain immutable. No automatic trusted-map update.

## Release gates

1. Exact head: application, dependency and Docker CI successful; inspect actual responsive/browser artifacts. Record real checkpoint limitations, no claim of validated terrain classification.
2. Host: quiesce writes; backup and verify SQLite/assets/identity; restore into separate volume; retain rollback images and original mission volume. Fast-forward only to tested source, build before switching, compare records after upgrade.
3. Hosted browser: real authorized login, session reload, navigation, NASA images, logout. Use disposable showcase for mutating replay and reset.
4. Separate showcase: own identity, volume, port and cookie; actual Alpha → observation → human confirmation → Beta → EVA-02 → reset; production snapshots unchanged.
5. Production Vercel: exact tested source and server-only BACKEND_URL; exact permitted origins; verified health/authentication/mission workflow before promotion. Merge draft PR only when gates pass.

Scientific boundary: actual NASA pixels and computed prototype route geometry, manually placed observations and illustrative mission; experimental model held-out MSL mIoU 0.099405, Perseverance transfer mIoU 0.132736, classification disabled. No safety, NASA endorsement or scientific flight validation claim. Do not expose secrets, private observations or real tokens in artifacts.


## Operator handoff (Windows)
After the exact candidate passes CI, fetch and fast-forward to that commit. From the repository root, run `powershell -File scripts/hosted-showcase.ps1 -ExpectedCommit <full-tested-sha> -ProductionOrigin https://<existing-host>` and then `powershell -File scripts/hosted-acceptance.ps1 -ProductionOrigin https://<existing-host> -ShowcaseOrigin https://<existing-host>:8443`. These repository-tracked scripts provision separate showcase identity and storage, check both public environments, and verify a replay/confirmation/reset against an unchanged production snapshot. They do not upgrade production or erase production data. Credentials are entered privately on the host. Actual browser acceptance and restore rehearsal remain separate gates.
