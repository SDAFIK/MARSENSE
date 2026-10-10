# MARSENSE AI4Mars prototype model card

Intended use: local research terrain evidence for human review. This model does
not measure mineral identity, soil strength or EVA safety.

Prototype anti-collapse check: PASS. Requires nonzero
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
Architecture: Small U-Net; Conv/BatchNorm/ReLU, 16/32/64 channels, bilinear skip decoder.
Configuration: seed 42, 12 epochs, deterministic CPU
PyTorch 2.14.1+cpu, Adam .001, batch 2. RGB bilinear 256x256,
float32 /255; mask nearest resize. Preprocessing: rgb-bilinear256-mask-nearest-v1.
Validation metrics remain separate in the checkpoint JSON. Held-out and transfer
sets are evaluated after training; no tuning is performed on their results.
Loss configuration: CrossEntropy with inverse-frequency weights from training pixels only.
Loss reduction: Weighted valid pixel sum / valid pixel count (no per-batch weight renormalization).

## Held-out MSL expert reference labels

Images: 16; labeled pixels: 599311.
Mean IoU over classes with nonzero union: 0.099405.

| Class | Precision | Recall | F1 | IoU |
| --- | --- | --- | --- | --- |
| soil | 0.518592 | 0.081641 | 0.141074 | 0.075890 |
| bedrock | 0.239361 | 0.484935 | 0.320517 | 0.190843 |
| sand | 0.093493 | 0.326020 | 0.145314 | 0.078350 |
| large rocks | 0.054442 | 0.600406 | 0.099831 | 0.052538 |

Confusion matrix (rows reference, columns predicted; soil/bedrock/sand/large rocks):

```json
[[31129, 227637, 111641, 10883], [19050, 79509, 51465, 13934], [9834, 24054, 16822, 888], [13, 972, 0, 1480]]
```

## Independent Perseverance transfer

Images: 8; labeled pixels: 278918.
Mean IoU over classes with nonzero union: 0.132736.

| Class | Precision | Recall | F1 | IoU |
| --- | --- | --- | --- | --- |
| soil | 0.182544 | 0.006890 | 0.013279 | 0.006684 |
| bedrock | 0.322146 | 0.847381 | 0.466822 | 0.304480 |
| sand | 0.559653 | 0.260836 | 0.355830 | 0.216419 |
| large rocks | 0.003423 | 0.155131 | 0.006698 | 0.003360 |

Confusion matrix (rows reference, columns predicted; soil/bedrock/sand/large rocks):

```json
[[1006, 140153, 2437, 2416], [2260, 75433, 6482, 4844], [2245, 18220, 11338, 11665], [0, 352, 2, 65]]
```

## Limitations and failure modes

This is a tiny-subset baseline with uncalibrated scores, class imbalance,
crowdsourced-label noise and substantial viewpoint/lighting/rover/site domain shift.
Single-view classification cannot establish traversability. Transfer scores describe
only these selected images. Adjacent views may remain correlated within a partition.
Undefined metrics reflect missing prediction/reference support, not successful classification.
Poorly detected classes remain limitations, regardless of mean score. No operational
generalization or calibrated hazard probability is established.
Mission terrain classification enabled: False.
For this experimental checkpoint, weak held-out performance requires explicit
human terrain identification; raw segmentation fractions and scores are retained.

Mean maximum softmax below .5 yields UNKNOWN; missing/failed/tampered checkpoint
yields unavailable evidence. Unsupported trained-class output yields UNKNOWN.
Human verification remains required. Deterministic replay is separately labeled DEMO.

## Version and artifacts

Checkpoint: ai/checkpoints/ai4mars-prototype.pt, SHA-256 f9e09ba92d50265f2d61a8e02c3537ba5a26b15d3a2d170f39a874f9c9159c65.
Dataset manifest SHA-256 9316a7cb03d33acc9af92639f29bdcf383be519d34c2035d7d3806f1e9fdaa75.
Exact training/evaluation/configuration metadata: adjacent checkpoint JSON.
Validation configuration: MARSENSE_MODEL_PATH=ai/checkpoints/ai4mars-prototype.pt.
The adapter refuses a candidate flagged as failed; scientific gate status is in STATUS.md.
Existing live services and saved observations are not silently changed.
