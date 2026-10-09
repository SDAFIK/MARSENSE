# UI contract and design brief

Engineering information architecture is defined here from the frozen product.
This is the Gate 0 brief, not an approved Figma design or completed UX audit.
Final design work follows Gate 12; final screenshot audit follows Gate 17.

## Product brief

Mission-control operator: inspect prior, route, new evidence, exact consequence
and decision. Astronaut: next target/distance, route/return/knowledge status,
relevant alert and WHY/COMPARE/verification. Future explorer: see inherited
verified discovery and its effect without repeating the previous EVA.

Primary hierarchy: mission → map → evidence difference → consequence → required
human action → detailed provenance. Default map is understandable without
twenty instrument overlays. Progressive detail exposes CTX/HiRISE and supported
ground footprints. MOLA/DEM/science layers appear only with real integrated data.

Six required screens: landing/introduction, Mission Control, Astronaut View,
Evidence Inspector, Exploration Memory, Before/After comparison. Landing states
the frozen identity/primary message and leads directly to Mission Control.
Every screen distinguishes real imagery, illustrative geometry, inference and
human verification. Never label an AI candidate "ground truth".

## Components and visual rules

Existing implementation uses a restrained dark scientific palette, Arial/system
sans body and Consolas/system monospace metadata; local fonts avoid network
dependency. Current CSS tokens: background #101513, panel #171d19, raised #1d2520,
border #303b32, text #e8ece6, muted #a7b3a9, verified accent #9bd9b4, provisional
accent #efb482. Current spacing is mostly 8/12/16/20/24/32; use explicit reusable
tokens in the selected final design, compact corners, no neon/glow/glass effects.

Components: mission switcher, mission summary, map/image layer selector, map
controls/legend/attribution, route summary with WHY, observation upload/selection,
expected/observed pair, alert, evidence-state badge, human review actions,
provenance disclosure, event timeline and inheritance notice. Color supplements
text/icon labels; it cannot be the only status signal.

Mission Control keeps the map dominant and evidence/action column concise.
Astronaut View must not simply repeat the full operator workspace: prioritize
next target, distance, route status, declared return assumption, knowledge,
relevant alert, WHY, COMPARE, and required confirmation. Hide raw NASA details
and costs until requested. Evidence Inspector must allow inspecting immutable
NASA priors as well as original observation, inference, interpretation and
decision; immutability must not disable viewing.

Before/after uses aligned extents and clearly labeled time/verification state.
Show Area 14 orbital-only/low obstruction/Alpha before, supported footprint
ground-observed/high rocks/challenged assumption/Beta after verification.
Pending evidence must not appear as learned verified terrain. Actual measured
route lengths/delta accompany WHY. Reduced motion uses an immediate accessible
state change; any slider must be keyboard operable with labels and readable
equivalent content.

## State matrix

| State | Required user behavior |
| --- | --- |
| Loading | Accessible status; prevent duplicate dependent mutations |
| Success | State only after saved response; refetch canonical mission snapshot |
| Empty | Explain next action; no invented counts/measurements |
| Offline / cached | Label local cache; cached assets need no external requests |
| Backend disconnected | Last loaded snapshot labeled; mutation disabled; retry available |
| Stale | Expired dynamic evidence visible in history, excluded from current overlays/alerts/costs |
| Partial | Missing slope/layer/model explicitly unavailable; preserve other evidence |
| Error | Explain affected operation and what remains usable; no filesystem/stack trace |
| Provisional safety warning | Named affected dependency and review action; no implied permanent map change |
| Rejected / conflicting | Auditable decision/conflict, prior retained, further evidence action |
| No route | Prior path remains for context; clear planning review required; no fabricated route |

Evidence states have labels for orbital-only, provisional, ground-observed,
multi-source confirmed, conflicting and superseded. Route UI covers nominal,
challenged, alternative, blocked and recalculating. Alert UI distinguishes
informational, mission relevant and provisional safety warning.

## Accessibility and responsive behavior

Desktop primary layout: map + action column; tablet collapses secondary panels;
mobile stacks content with map, consequence then action. Verify at 1440×1000,
834×1112 and 390×844 plus 200% zoom. No horizontal overflow or clipped action.
Visible focus, logical tab order, skip link, semantic headings, labeled inputs,
screen-reader status/alerts, minimum 4.5:1 normal text contrast and usable touch
targets. Current small 7–11 px metadata and 33 px map controls need review; no
contrast/touch compliance is claimed merely because overflow tests pass.

SVG/WebGL fallback must use the same current asset corners/selected layer,
route endpoints and expiry filtering. An incorrectly stretched basemap or stale
dynamic overlay is not an acceptable scientific fallback. Do not hide model or
cache limitations behind a permanently green connectivity indicator.

## Design workflow and acceptance

Product Design: validate this brief/flow after authority reconciliation.
MagicPath: explore two mission/astronaut structures without changing business
rules. Select and document the strongest hierarchy. Figma: build tokens,
components/states and all six final screen designs with responsive/accessibility
rules. Implement from that context. Product Design: capture and inspect final
desktop/tablet/mobile/error/offline/pending/conflict/no-route screens, report
findings and fix them. Tool capability availability is not proof of an artifact.
