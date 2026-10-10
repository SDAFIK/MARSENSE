# Engineering decisions and source reconciliation

## Current source reconciliation — 2026-10-10

The user supplied `C:\Users\ACER\Downloads\MARSENSE_Final_Project_Notes.docx`
and confirmed it is the main project document, to use as both reference and
implementation specification. It has been read and extracted into
docs/MAIN_PROJECT_NOTES.md. This audit independently read all 458 paragraphs
and verified that the complete extraction matches after whitespace normalization.
Original SHA-256: 8ceaad7d579bfc79c16aa419d7db086fb21f2a15a6493463d6e07eec65c084a4.
The missing-document blocker recorded below is resolved;
the following table is preserved as a historical planning snapshot. The core
human-verification loop and stack agree with the pasted instructions. The notes
drive the sparse astronaut view and Area 14 / A17 wording. Required scientific
gaps remain open at IMPLEMENTATION_STATUS.md; source availability does not
certify those gates.

## Earlier planning snapshot

Date: 2026-10-10 (Asia/Dhaka). These decisions implement the frozen request;
they do not replace the missing final project notes.

| ID | Question | Decision | Consequence / validation |
| --- | --- | --- | --- |
| D01 | Authoritative DOCX missing | Prepare complete engineering documentation from the pasted request and existing PROJECT_SPEC.md; keep Gate 0 pending source reconciliation | No invented DOCX contents; no feature implementation or deployment while that check is unresolved |
| D02 | Existing app or fresh scaffold? | Preserve the existing compatible Next.js/FastAPI monorepo | Audit before extending; no needless rewrite |
| D03 | Practical persistence | SQLAlchemy typed JSON entities in SQLite/WAL for the bounded single-server demo | Transactional writes, restart and concurrency tests; PostGIS is a later deployment option, not a claim about current support |
| D04 | Analysis geometry | Local Mars equirectangular meters, origin 77.45 E / 18.44 N, sphere radius 3,396,190 m as used by the cached Mars Trek service | Align and test against product metadata; no Earth distances |
| D05 | Real image vs actual EVA location | Public-release PIA26072 illustrates a fictional EVA; footprint and mission geometry are explicitly simulated | Never claim PLACES registration or calibrated PDS imagery for this JPEG |
| D06 | Replay vs inference | Keep replay only as a labeled branch/regression fixture; mandatory final acceptance must execute real local validated inference | Current replay acceptance is insufficient for Gate 7 and Gate 15 |
| D07 | Missing elevation | Display slope unavailable; exclude it from current cost; require bounded DEM ingestion and tested slope before the full required data gate passes | A numeric zero cost must not be described as measured zero slope |
| D08 | Confidence | Scores are uncalibrated model evidence; prototype review thresholds configurable and documented, never NASA standards | Unknown/failed inference cannot confirm terrain without explicit human identification |
| D09 | Return corridor | The current outbound route may be treated as the illustrative retraced corridor only with an explicit assumption | No independently validated return/safety/resource guarantee |
| D10 | Design tools | Product Design brief after engineering IA stabilizes; MagicPath alternatives; selected Figma tokens and screens; final screenshot audit | Figma and MagicPath tool capabilities are exposed; no design artifact has been created in this checkpoint |
| D11 | Notion | Use repository tickets and status; mirror only if a connected writable Notion capability becomes available | No Notion tools are currently exposed; do not install or pretend a workspace exists |
| D12 | Hosting | Do not provision or publish until required gates pass | DEPLOYMENT.md contains a plan and current local commands, not a deployment claim |
| D13 | Original instructions | Preserve pre-existing PROJECT_SPEC.md verbatim and add a precise engineering annex | Both sources remain reviewable |
| D14 | New notes extraction | Read and reconcile docs/MAIN_PROJECT_NOTES.md when it appeared during concurrent work | Its product content agrees with the frozen request; original path/hash/text fidelity independently verified |
| D15 | Concurrent workspace | User confirmed another chat is implementing; this chat finishes contracts and evidence audit without feature edits | Do not commit or overwrite the other chat's application changes; no final fixed-release claim |

| D16 | Gate 0-only stop | Run the five Toolkit workflows in order; documentation/configuration only | No automatic Gates 1-20 resumption, application edits, training, ingestion, service launches or deployment |
| D17 | Contract versus implementation | Root files are required contracts; companion docs are implementation snapshots | Existing replay/tests never weaken required real-inference/data acceptance |
| D18 | Original versus derivative | New uploads retain original bytes/hash separately from display/model input | Correct stale documentation; older records may lack originals and must disclose absence |

The grilling workflow was resolved against the supplied material: users are
mission-control operators, astronauts, and future explorers; verification is
manual; the first scenario and stack are already specified. The source question initially received "okay", without a path. Later the
concurrent chat recorded the user-supplied path and authority confirmation; this
audit verified the original file directly. No unresolved source question or
repeated product questions remain. Remaining choices above are ordinary engineering choices.

D19 — Latest user request explicitly resumes implementation. The earlier pause and concurrent-chat ownership notes are historical; follow sequential gate acceptance while preserving live services/history. See RESUMPTION_REVIEW.md.

D20 — Latest supplied AGENTS instruction restores Gate 0-only scope. “finish it” completes that scope; it does not explicitly resume later gates. Existing implementation checkpoints are retained as history.
