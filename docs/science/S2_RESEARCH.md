# S2 source and split research

NASA catalog links the exact Zenodo release, not an arbitrary mirror:
https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars
https://zenodo.org/records/15995036
DOI 10.5281/zenodo.15995036, merged-0.6. Publisher API metadata retained
in data/nasa/ai4mars/release-record.json declares CC-BY-4.0. Catalog-level
license is unspecified; these are distinct metadata levels.

The extracted original info.md and label_keys.json define NAV labels 0 soil,
1 bedrock, 2 sand, 3 big rock, 255 unlabeled. Crowdsourced train labels require
three labelers and two-thirds agreement; expert test min1 requires 100% agreement
of contributing expert annotations. This is reference annotation, not physical
terrain truth or safety certification. M2020 geology labels use a different
taxonomy and are excluded.

Dataset documentation explicitly describes image-name to label-name pairing,
including the merged suffix. MSL camera SIS describes site/drive filename fields:
https://planetarydata.jpl.nasa.gov/img/data/msl/MSLMOS_1XXX/DOCUMENT/MSL_CAMERA_SIS.PDF
(searchable official example NRA_013760215EDR_F0930008NCAM22103M1: site093, drive0008).
The direct PDF endpoint was unavailable to the browser tool; official indexed
text supported the field interpretation. Acquisition partitions whole MSL site
identifiers, rather than random adjacent frames. All expert-test sites are
excluded from train and validation; selected Perseverance images are transfer only.
This reduces local sequence leakage but does not prove planet-wide generalization.

Selection is deterministic SHA-256 ordering, with per-site caps and fixed counts.
The entire 16.23 GB ZIP is not downloaded. Exact ranges, extracted byte hashes,
ZIP header/name/length/CRC checks and bounded retries are used. Archive index is
retained for reproducibility; --index can rebuild it with a separate 40 MB cap.
No model metric may be accepted until the real manifests and held-out evaluations
are complete. Tiny-subset performance must be reported with its sample limits.
