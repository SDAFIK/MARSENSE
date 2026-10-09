# AI pipeline

The replay and actual upload paths are deliberately explicit. Replay labels are reviewed demonstration annotations over the real Navcam PIA26072 mosaic. They are deterministic fixtures, not predictions. Uploads decode and re-encode a real image, then invoke the perception adapter.

Without a checkpoint, OpenCV computes edge density/contrast and returns a low-confidence roughness candidate or unknown. Lighting and viewpoint can mimic roughness; human terrain identification is mandatory before persistence. No soil strength, radiation, weather, mineral or safe-path conclusion is inferred from RGB.

With `MARSENSE_MODEL_PATH`, a local PyTorch TorchScript model receives RGB floats in [0,1], shape 1×3×256×256, and returns four-class pixel logits at the same resolution. Classes are soil, bedrock, sand and large rocks. The adapter calculates class fractions and mean maximum pixel probability. That score is uncalibrated. Model failure yields unavailable/unknown and preserves the image for review. Only load trusted local model files. TorchScript is deprecated in current PyTorch; a future model adapter should use torch.export after compatibility validation.

`python -m ai.train split.json ai/checkpoints/terrain.pt --epochs 10` trains a small dilated-convolution segmentation baseline and exports a model/report matching this contract. The manifest contains `train` and `validation` arrays, each with relative `image` and `mask` paths. Masks must be single-channel integer labels 0–3, with 255 ignored. Train and validation paths may not overlap. Use rover/site/sequence-disjoint splits; avoid near-duplicate frames crossing splits. The export records model/manifest hashes, seed, split sizes, confusion matrix, per-class IoU, present-class mean IoU and pixel accuracy.

No AI4Mars images or calibrated validated checkpoint are bundled. Acquire actual [AI4Mars](https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars) labels, preserve their release/license/source metadata, train on genuine labels and evaluate held-out rover/site data. The synthetic training smoke test verifies pipeline plumbing only and must never be presented as classifier performance. Before enabling operational inference, document class balance, failure cases, calibration, independent test performance and Perseverance domain transfer.

Semantic-mask visual overlays, calibrated Navcam/Mastcam-Z camera geometry and multisource model evaluation remain scientific completion items.
