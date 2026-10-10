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
Configuration: seed 42, 8 epochs, deterministic CPU
PyTorch 2.14.1+cpu, Adam .001, batch 2. RGB bilinear 256x256,
float32 /255; mask nearest resize. Preprocessing: rgb-bilinear256-mask-nearest-v1.
Validation metrics remain separate in the checkpoint JSON. Held-out and transfer
sets are evaluated after training; no tuning is performed on their results.
Loss configuration: CrossEntropy with inverse-frequency weights from training pixels only.

## Held-out MSL expert reference labels

Images: 16; labeled pixels: 654510.
Mean IoU over classes with nonzero union: 0.164389.

| Class | Precision | Recall | F1 | IoU |
| --- | --- | --- | --- | --- |
| soil | 0.554955 | 0.999090 | 0.713557 | 0.554675 |
| bedrock | undefined | 0.000000 | 0.000000 | 0.000000 |
| sand | 0.846445 | 0.104839 | 0.186570 | 0.102883 |
| large rocks | undefined | 0.000000 | 0.000000 | 0.000000 |

Confusion matrix (rows reference, columns predicted; soil/bedrock/sand/large rocks):

```json
[[354561, 0, 323, 0], [171367, 0, 2074, 0], [112818, 0, 13213, 0], [154, 0, 0, 0]]
```

## Independent Perseverance transfer

Images: 8; labeled pixels: 226296.
Mean IoU over classes with nonzero union: 0.075869.

| Class | Precision | Recall | F1 | IoU |
| --- | --- | --- | --- | --- |
| soil | 0.305583 | 0.977802 | 0.465643 | 0.303477 |
| bedrock | undefined | 0.000000 | 0.000000 | 0.000000 |
| sand | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| large rocks | undefined | 0.000000 | 0.000000 | 0.000000 |

Confusion matrix (rows reference, columns predicted; soil/bedrock/sand/large rocks):

```json
[[68673, 0, 1559, 0], [146385, 0, 9, 0], [6303, 0, 0, 0], [3367, 0, 0, 0]]
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

Checkpoint: ai/checkpoints/ai4mars-weighted-v2.pt, SHA-256 c0fd828a0164df5bb03a1292608db5dcb2342f6dfc5973a88fe6023e65766f68.
Dataset manifest SHA-256 6ec2a90869202f2719ce0fc33084ef094436371df271b163241251869ce8468e.
Exact training/evaluation/configuration metadata: adjacent checkpoint JSON.
Validation configuration: MARSENSE_MODEL_PATH=ai/checkpoints/ai4mars-weighted-v2.pt.
The adapter refuses a candidate flagged as failed; scientific gate status is in STATUS.md.
Existing live services and saved observations are not silently changed.
