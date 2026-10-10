# Demonstrating MARSENSE

Open http://127.0.0.1:3000/mission. Existing saved history remains intact; if
Route Beta is already present, inspect Before & After and Exploration Memory.
Never reset the user's database to repeat a demonstration. For a clean Alpha
scenario, use a different MARSENSE_DATABASE_URL and separate local service ports.

1. Explore the mission map; Open full map expands it, Escape closes it. Toggle
   routes/evidence and CTX/HiRISE. The source crop is approximately 1.2 × 0.8 km.
2. Analyze Boulder field on Route Alpha. The labeled replay annotation and
   simulated footprint challenge the low-obstacle assumption provisionally.
3. Inspect expected versus observed terrain and the mission consequence. Confirm
   only after human review; weak/UNKNOWN persistent terrain needs manual identity.
4. Route Beta reflects footprint-supported terrain cost; original NASA prior,
   raw observation and Route Alpha remain in history. No route is safety-certified.
5. Reload and switch to Future EVA: inherited knowledge persists.
6. Evidence Inspector shows calibrated camera context/unknown footprints, CRISM
   target coverage/no mineral identity, source declarations and evidence ancestry.
   Duplicate bytes/same acquisition episode cannot establish independent support.
7. For contradictory later evidence, explicitly name the confirmed IDs to supersede
   and explain the reassessment. Full retired-footprint coverage is required; old
   decisions stay immutable. Source declarations are permanent human assertions.
8. In authenticated configuration, sign in as a provisioned Mission Control/Admin
   reviewer. Confirmation records the server session identity, not the submitted
   display name. Sign out revokes the session. Writable demo is loopback-only.

This demonstrates validated prototype workflows, not scientific model accuracy.
The experimental model's low measured quality keeps automatic classification
disabled; see MODEL_CARD.md and NASA_SOURCE_MATRIX.md.
