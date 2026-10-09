# Deterministic demonstration

Start an empty local database. Open `/mission`. Route Alpha connects the illustrative habitat (120,400 m) with the delta target (1080,400 m), using a low-obstacle soil assumption. CTX/HiRISE imagery is real; mission geometry is simulated.

1. Select “Boulder field · on Route Alpha” and click Analyze terrain.
2. Read expected soil versus observed obstacle-rich terrain, Significant Difference, the challenged low-obstacle corridor assumption and affected traverse/return corridor.
3. Observe the provisional safety alert and amber footprint. NASA prior remains intact; terrain cost has not yet changed.
4. Confirm with a human verification note. Evidence becomes confirmed and Ground Observed is limited to the supported 160×160 m footprint centered at (600,400 m).
5. A* computes Route Beta around the obstacle footprint. Alpha 960 m → Beta 1059.41 m; cost changes from 1104 to 1218.32 model units. The explanation attributes the change to the reviewer, evidence class and footprint.
6. Reload; the decision remains. Switch to EVA 02 or open Exploration Memory and start the future EVA. The next explorer inherits the evidence and rerouted plan.

Alternative fixtures in `data/demo/scenarios.json`: matching soil (silent), minor off-route terrain (silent), weak relevant roughness (provisional safety alert and explicit human class required), model unavailable (unknown, no automatic update), dynamic visibility (30-minute expiry, reviewable but no persistent terrain change). Rejection preserves the prior and audit trail.

All fixtures use the same public Navcam mosaic to demonstrate the decision lifecycle. Their curated classes and footprints are intentionally simulated; they are not six independently acquired/geolocated images. Actual upload accepts JPEG/PNG up to 8 MB with manually declared local bounds. Without a trained checkpoint it produces conservative texture evidence for human review.

Demo operation makes no external requests. The browser acceptance test blocks external network resources during the primary flow. For repeat performances use a separate database via `MARSENSE_DATABASE_URL`; do not erase existing mission history.
