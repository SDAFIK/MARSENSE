# Gate 0 workflow and consistency review

Scope: documentation and the required .env.example only. The user explicitly
stopped implementation on 2026-10-10. Gates 1–20 must not resume automatically.
Existing application code, running services and saved mission data are preserved.
This record does not certify later gates or scientific/model readiness.

## 1. To-spec

Applied the Software Engineering Toolkit to-spec workflow first. Inputs: the
complete master prompt, original project notes and existing repository context.
The original notes were previously independently verified: 458 paragraphs,
28 sections, no tracked insertions/deletions, exact paragraph-text agreement
with MAIN_PROJECT_NOTES.md after whitespace normalization. Source provenance:
MAIN_PROJECT_SOURCE.json. The original DOCX SHA-256 is
8ceaad7d579bfc79c16aa419d7db086fb21f2a15a6493463d6e07eec65c084a4.

The master prompt governs engineering sequence and constraints. The Word notes
govern frozen product intent. PROJECT_SPEC.md retains earlier engineering
instructions and specifies the observable R01–R20 contract. Neither current
code nor demonstration fixtures weaken the required product behavior.

| Required specification element | Output / review evidence |
| --- | --- |
| Context, problem, goals and non-goals | PROJECT_SPEC.md engineering annex and Gate 0 clarification |
| Domain terms | DATA_MODELS.md shared vocabulary and state definitions |
| User stories | PROJECT_SPEC.md operator, astronaut, scientist and future-EVA stories |
| Behavior and edge cases | Observation/verification contract; API_CONTRACT.md; TEST_PLAN.md |
| Constraints | Frozen stack, Mars geometry, footprint/provenance/human trust rules, offline package |
| Acceptance | R01–R20 plus DEMO_SCENARIO.md exact real-inference loop |
| Affected areas | ARCHITECTURE.md responsibility and trust boundaries |
| Test plan | TEST_PLAN.md required behavior matrix and historical results separated |
| Rollout | IMPLEMENTATION_PLAN.md sequential acceptance gates |
| Open decisions | docs/DECISIONS.md; product intent resolved, later scientific inputs explicitly open |

Contradictions to resolve in Gate 0: stale seed/segment claims in root documents;
original-upload retention described differently across root/companion contracts;
curated replay confused with full AI acceptance in summaries; environment example
omitted from the prior documentation commit; gate-sized rows insufficiently
split into small implementation tickets; no durable ordered workflow record.

The required scientific data/model integrations remain later acceptance blockers.
Gate 0 must specify them accurately; it must not implement or fabricate them.

## 2. Grilling

Applied grilling second, resolving each branch against the supplied sources before
asking anything. The master prompt forbids questions already answered by the
project notes. No new user question is needed because remaining uncertainty does
not change the frozen specification or Gate 0 delivery.

| Branch | Resolution and source | Decision |
| --- | --- | --- |
| Users and success | Notes §§1,14,24,28; master primary screens/demo | Mission Control operator, astronaut, scientist/reviewer, future explorer; full learning loop |
| Verification authority | Notes §7; master verification | Human confirm/reject/more-evidence; no automatic persistent AI update |
| Spatial scope | Notes §§7,12; master provenance/geometry | Supported local footprint; Mars metric analysis, separate map rendering |
| Dynamic versus persistent | Notes §7; master persistent/dynamic | Expiring operational conditions never become permanent terrain |
| Scientific inputs | Notes §§8–10,26,28 | All required sources remain required; no fake replacements |
| AI acceptance | Notes §17; master inference/offline/E2E | Genuine local trained/validated inference; replay is only a labeled fixture |
| Architecture | Notes §20; master compatible-stack exception | Retain Next/FastAPI, typed SQLAlchemy SQLite fallback; dedicated deterministic A* |
| Error paths | Master failure handling | Preserve observation, prior route context and saved state; distinguish unavailable/unsaved |
| Return/resource values | Master consequence/explanation | Use declared illustrative return assumption; unavailable resource/time models stay unavailable |
| Design/hosting | Master Gates 12,17,19 | Brief now; actual tools/audits/hosting later, after prerequisite acceptance |
| Rollout now | Latest user instruction | Gate 0 only; implementation remains stopped in this chat |

Decisions D02–D12 in DECISIONS.md document ordinary engineering choices. Exact
scientific product/model selection remains an evidence-dependent later task.
It is not an unanswered product question and does not prevent a complete Gate 0
contract. No credentials, deployment or destructive operation is needed here.

## 3. Domain-modeling

Applied domain-modeling third. DATA_MODELS.md defines terms, entities, states,
ownership, invariants and scenario checks. Compared those definitions with current
Pydantic entities, MissionService, seed/dependency logic and existing tests.
No application code or test implementation was changed.

Resolved ambiguities: source evidence is not its interpretation; inference is
not a human decision; a region summary is not full-region coverage; uncalibrated
score is not truth; ground-observed is not a safe-route certification; repeated
image evidence is not independent confirmation; expired visibility is not terrain;
the original asset and model-input/display derivative have separate references.

Walked through MATCH, irrelevant minor, relevant strong/weak, failed/unknown,
confirmation, rejection, more-evidence, conflict, multi-source, supersession,
expiry, failed transaction and restart/future-EVA cases. Requirements agree with
R02–R07/R11–R16/R19. Known incomplete transitions remain later tickets instead
of being described as implemented. No frozen product concept was changed.

## 4. Codebase-design

Applied codebase-design fourth. ARCHITECTURE.md defines stable input/output seams,
ownership and tests for the seven core engines plus their transport/transaction
boundaries. Retained the compatible existing monorepo and dedicated A*; no scaffold,
new service, framework or application refactor was performed.

Review decisions: scientific ingestion returns normalized products and provenance;
AI returns immutable typed evidence and has no persistence authority; mission rules
stay behind backend interfaces; verification/knowledge/routing/events share a clear
atomic boundary; source parsing and Earth display math cannot leak into analysis;
UI consumes canonical status and structured WHY facts. Existing broad service and
frontend threshold duplication are explicit later repairs, not the intended design.

SQLite versus PostGIS, worker execution, model lifecycle and generated API types
are documented tradeoffs. Failure injection and historical schema migration are
required at stable seams. The design has enough responsibility separation to test
the frozen loop without introducing many shallow wrappers or microservices.

## 5. To-tickets

Applied to-tickets fifth, after the specification, decision review, domain model
and module boundaries. IMPLEMENTATION_PLAN.md retains exact G00–G20 order and
adds T01–T45 as independently reviewable acceptance slices. Every ticket has an
outcome/limited scope, non-goals, blocking edges, acceptance tests, completion
evidence, owner and TODO/on-hold status. Prior-gate acceptance is inherited, so
the small tickets cannot bypass a failed NASA, AI or other gate.

The tickets connect real products and behavior vertically: source/footprint and
model evidence, exact dependency/warning, human decision, local knowledge, route
tradeoff and future inheritance. Genuine missing data/weights remain explicit
inputs. Later design, scientific/UX/security audits, deployment and freeze are
planned without being executed. No Notion workspace or external messaging is
needed for Gate 0; repository tickets remain authoritative.

## Cross-document reconciliation and acceptance

| Issue found | Resolution |
| --- | --- |
| Required .env.example omitted from prior checkpoint | Included local defaults, empty credential/model/slope settings, explicit upload cap and server-only backend origin; include in Gate 0 commit |
| Root seed/segment descriptions stale | Corrected to current fresh Area 14/A17 and EVA-specific segment IDs; old-store migration remains a later requirement |
| Original upload retention differed across documents | API/data contracts now distinguish original bytes/hash from model/display derivative and unavailable older originals |
| Replay summaries could imply actual model acceptance | Required real-inference flow remains separate; companion test summary explicitly labels curated replay and historical results |
| Failure transaction wording allowed ambiguous partial success | Domain/routing contract now distinguishes atomic rollback on execution failure from a valid, explicit no-path planning result |
| Gate rows lacked small testable slices | Added T01–T45 with inherited non-goals/dependencies, acceptance and completion evidence |
| Master engineering prompt not retained verbatim in repository | Added MASTER_PROMPT.md; its bytes match the pasted attachment |
| Automatic continuation conflicted with latest instruction | AGENTS/README/STATUS/plan record Gate 0-only stop; no later gate resumes automatically |

All 13 exact master-prompt Gate 0 deliverables are present: PROJECT_SPEC.md,
ARCHITECTURE.md, DATA_MODELS.md, API_CONTRACT.md, NASA_DATA.md, AI_PIPELINE.md,
ROUTING_LOGIC.md, UI_SYSTEM.md, DEMO_SCENARIO.md, TEST_PLAN.md,
IMPLEMENTATION_PLAN.md, README.md and .env.example. Supplemental AGENTS/STATUS,
decisions, source metadata and this review make their authority and scope explicit.

Static review passed: required files, R01–R20, G00–G20, T01–T45, all gate status
records, ordered workflow sections, root/companion Markdown links, UTF-8 text,
environment syntax/defaults/no credentials, exact master archive and original
DOCX paragraph fidelity. GATE_0_CHECKS.json stores hashes and machine-readable
results. All 67 application/configuration/data files compared with the prior
audit snapshot remain unchanged. No application suites or source fixes were run.

Gate 0 is complete as an internally consistent engineering specification.
Required covering science products, camera registration, genuine model validation,
remaining domain/reliability fixes and later design/audits/deployment remain planned
acceptance work. They are not hidden, waived or claimed complete by this result.
Stop here until the user explicitly resumes implementation.
