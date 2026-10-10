# MARSENSE AI4Mars prototype model card

Intended use: local research terrain evidence for human review. This model does
not measure mineral identity, soil strength or EVA safety.

Prototype anti-collapse check: FAIL. Requires nonzero
validation recall for every implemented class; this is MARSENSE configuration,
not a NASA performance or safety standard. A failed candidate must remain
unavailable for mission classification and S2 stays open.

Dataset: NASA-linked [AI4Mars merged-0.6](https://zenodo.org/records/15995036),
DOI 10.5281/zenodo.15995036, publisher license CC-BY-4.0. Bounded genuine subset,
not the complete archive. Counts: {'train': 48, 'validation': 16, 'test': 16, 'transfer': 8}. Source files/ranges and per-file hashes
are retained in data/nasa/ai4mars/source.json and the original release metadata.
Whole MSL site groups are disjoint across train/validation/test; all expert-test
sites are excluded from training/validation. Perseverance transfer is never trained.
Crowdsourced reference masks and expert reference masks are annotation evidence,
not physical terrain or safety truth. No benchmark fixture images are used here.

Classes: 0 soil, 1 bedrock, 2 sand, 3 big rock (application: large rocks), 255 ignored.
Train labeled pixels per class: [1019027, 508580, 149140, 4105].
Architecture: small four-layer dilated convolution segmentation baseline.
Configuration: seed 42, 3 epochs, deterministic CPU
PyTorch 2.14.1+cpu, Adam .001, batch 2. RGB bilinear 256x256,
float32 /255; mask nearest resize. Preprocessing: rgb-bilinear256-mask-nearest-v1.
Validation metrics remain separate in the checkpoint JSON. Held-out and transfer
sets are evaluated after training; no tuning is performed on their results.
Loss configuration: unweighted CrossEntropy baseline.

## Held-out MSL expert reference labels

Images: 16; labeled pixels: 632169.
Mean IoU over classes with nonzero union: 0.090728.

| Class | Precision | Recall | F1 | IoU |
| --- | --- | --- | --- | --- |
| soil | 0.362911 | 1.000000 | 0.532553 | 0.362911 |
| bedrock | undefined | 0.000000 | 0.000000 | 0.000000 |
| sand | undefined | 0.000000 | 0.000000 | 0.000000 |
| large rocks | undefined | 0.000000 | 0.000000 | 0.000000 |

Confusion matrix (rows reference, columns predicted; soil/bedrock/sand/large rocks):

```json
[[229421, 0, 0, 0], [183548, 0, 0, 0], [218385, 0, 0, 0], [815, 0, 0, 0]]
```

## Independent Perseverance transfer

Images: 8; labeled pixels: 280227.
Mean IoU over classes with nonzero union: 0.041542.

| Class | Precision | Recall | F1 | IoU |
| --- | --- | --- | --- | --- |
| soil | 0.166169 | 1.000000 | 0.284983 | 0.166169 |
| bedrock | undefined | 0.000000 | 0.000000 | 0.000000 |
| sand | undefined | 0.000000 | 0.000000 | 0.000000 |
| large rocks | undefined | 0.000000 | 0.000000 | 0.000000 |

Confusion matrix (rows reference, columns predicted; soil/bedrock/sand/large rocks):

```json
[[46565, 0, 0, 0], [159190, 0, 0, 0], [64937, 0, 0, 0], [9535, 0, 0, 0]]
```

## Limitations and failure modes

This is a tiny-subset baseline with uncalibrated scores, class imbalance,
crowdsourced-label noise and substantial viewpoint/lighting/rover/site domain shift.
Single-view classification cannot establish traversability. Transfer scores describe
only these selected images. Adjacent views may remain correlated within a partition.
Undefined metrics reflect missing prediction/reference support, not successful classification.
Poorly detected classes remain limitations, regardless of mean score. No operational
generalization or calibrated hazard probability is established.

Mean maximum softmax below .5 yields UNKNOWN; missing/failed/tampered checkpoint
yields unavailable evidence. Unsupported trained-class output yields UNKNOWN.
Human verification remains required. Deterministic replay is separately labeled DEMO.

## Version and artifacts

Checkpoint: ai/checkpoints/ai4mars-baseline-v1.pt, SHA-256 c55767b2886698a77645295e406ca652f987f6186995417fc6f46a9adcbf0a2e.
Dataset manifest SHA-256 f41b9cf9e6583ad422c95aca7609e497100e56380b16a47ae5cfccbf90fdf23c.
Exact training/evaluation/configuration metadata: adjacent checkpoint JSON.
Enable explicitly with MARSENSE_MODEL_PATH=ai/checkpoints/ai4mars-baseline-v1.pt.
Existing live services and saved observations are not silently changed.
