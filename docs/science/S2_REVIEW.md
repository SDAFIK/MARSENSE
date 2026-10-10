# S2 pipeline review — accepted with experimental-model limits

All required pipeline work is implemented: genuine NASA-linked AI4Mars 0.6 subset, original class/license metadata, reproducible range extraction, group/byte-hash split checks, deterministic training and export, immutable version artifacts, held-out metrics and separate Perseverance transfer, source/configuration hashes and inference integration. Source research is S2_RESEARCH.md; actual scores are in MODEL_CARD.md and checkpoint JSON.

Current checkpoint f9e09ba92d50265f2d61a8e02c3537ba5a26b15d3a2d170f39a874f9c9159c65. Train48/validation16/final-test16/transfer8. Prior failed baselines and their inspected groups remain history; final groups exclude all earlier diagnostics. Training/validation never include final held-out/transfer images. Final evaluation was performed once after twelve fixed epochs.

Prototype anti-collapse check passes for all four validation classes. It is a MARSENSE configuration check, not a NASA benchmark criterion or performance certification. Held-out mIoU .099405; separate transfer mIoU .132736. Performance is weak and mission terrain classification is explicitly DISABLED. The adapter retains genuine raw scores and class fractions, returns UNKNOWN, and requires human terrain identification. Failed candidates, invalid files and hash mismatches are unavailable, never forced terrain. No calibrated probability, reliable generalization or operational usability is claimed.

Review fixes: duplicate file/group leakage, preprocessing mismatch, model and metadata version provenance, checkpoint read/hash race, failed-candidate rejection, partial-range retry/cache checks. Synthetic fixtures remain separately labeled; their metrics are not benchmarks. 54 backend tests (including genuine checkpoint integration) pass; Ruff/mypy pass. Earlier frontend 3-component/21-browser/build/static checks pass; no additional UI change in S2.

S2 accepts the experimental training/evaluation/inference workflow. It does not validate model reliability; NASA source matrix must retain this limitation. S3 may proceed. Public deployment and full scientific completion remain unaccepted.
