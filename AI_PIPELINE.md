# Terrain perception and trust boundary

Input: validated ground JPEG/PNG plus independently provided footprint metadata.
Output: structured terrain inference; AI code cannot write region knowledge,
verification, assumptions or routes. MissionService owns consequences and humans
own verification. See R03–R05, R10–R12 and R19 in PROJECT_SPEC.md.

## Current execution paths

| Path | Execution | What can honestly be claimed |
| --- | --- | --- |
| Curated replay | MissionService.demo reads data/demo/scenarios.json | Deterministic branching fixture; no AI execution on the image |
| OpenCV fallback | Decode, resize 256 × 256, grayscale, Canny/contrast features | Conservative texture candidate; not trained AI4Mars segmentation |
| Optional TorchScript | Load configured local file; RGB float /255; 1×3×256×256 → 1×4×256×256 logits | Actual PyTorch execution if configured; compatibility adapter alone is not validated Mars perception |

Current class channel order: soil, bedrock, sand, large rocks. Other domain labels
rough terrain/obstacle-rich terrain require a documented derived-property rule
and validation rather than a fabricated extra classifier channel. UNKNOWN and
unknown fraction must be explicit for unsupported pixels/model failures.

OpenCV edge_fraction > 0.12 produces a rough candidate, otherwise unknown;
confidence 0.3 deliberately forces human review. This is a project heuristic,
not a scientific probability. Optional model mean softmax confidence uses 0.5
for review eligibility and 0.8 for the label high; neither is calibrated. Current
fixtures use 0.9 for replay annotations; that number is not a measured AI score.
Thresholds currently reside in source and must move to tested shared backend
configuration before final acceptance. Frontend must consume eligibility/state
from API rather than independently duplicate the 0.5 mission rule.

## Required trained/validated path

1. Select a bounded official AI4Mars subset with original IDs/labels/checksums.
2. Document camera/domain differences, label mapping, ignored/unknown pixels and
   train/validation/test split; avoid adjacent-frame or same-image leakage.
3. Train or acquire an appropriately licensed checkpoint with reproducible code,
   preprocessing and model metadata. Do not invent weights or calibrate on the
   final demo image and then call that held-out validation.
4. Report confusion matrix/per-class metrics and known failure modes on held-out
   images, including lighting/perspective and unfamiliar terrain.
5. Cache model/checksum locally; execute actual inference on a selected known NASA
   ground image in the final acceptance test with remote downloads blocked.
6. Persist class proportions, unknown coverage, model/version/hash, calibration
   status and limitations alongside untouched original observation.
7. A visually justified boulder-rich result challenges the low-obstruction
   assumption; human confirmation still controls persistence and routing.

No validated checkpoint is currently bundled. PyTorch dependencies are provided
in ai/requirements.txt; the local model execution path is selected by
MARSENSE_MODEL_PATH. Concurrent work added ai/train.py with split evaluation,
confusion/IoU reporting and TorchScript export. Its synthetic smoke test checks
plumbing only; genuine AI4Mars held-out performance is still absent.
Gate 7 and the real-inference part of Gate 15 remain open.
A recorded annotation may support a transparent demo fallback, but cannot be
presented as completion of R10.

## Failure behavior

Valid uploaded observation survives model load/inference failure. Store a
structured unavailable output with diagnostic reference; show manual review,
do not change permanent knowledge. Uncertain/unknown output can produce a
provisional warning if mission dependencies intersect. Human terrain
identification is required before terrain confirmation, and unknown cannot be
confirmed as a permanent traversability fact.

Reject undecodable/oversized assets before inference. Preserve original bytes
and metadata in audit storage; create a sanitized display derivative separately.
Run CPU inference outside the async event loop and cache an initialized model
per service, with bounded work/concurrency. Current upload inference runs inline
and _torch reloads the model per call; Gate 18 must correct these limits.

AI cannot infer mineral chemistry, radiation, toxicity, soil bearing strength,
oxygen, precise resource budgets, actual camera ground scale or certified risk.
