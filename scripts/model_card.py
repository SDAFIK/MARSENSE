"""Generate a model card only from completed genuine run artifacts."""

import hashlib
import json

from backend.config import ROOT


def main() -> None:
    model = ROOT / "ai/checkpoints/ai4mars-prototype.pt"
    report = json.loads(model.with_suffix(".json").read_text())
    manifest_path = ROOT / "data/nasa/ai4mars/subset.json"
    manifest = json.loads(manifest_path.read_text())
    if hashlib.sha256(model.read_bytes()).hexdigest() != report["model_sha256"]:
        raise ValueError("Model checksum mismatch")
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != report["manifest_sha256"]:
        raise ValueError("Dataset manifest checksum mismatch")
    sections = []
    names = ["soil", "bedrock", "sand", "large rocks"]
    for split in ("test", "transfer"):
        metrics = report[split + "_evaluation"]
        title = (
            "Held-out MSL expert reference labels"
            if split == "test"
            else "Independent Perseverance transfer"
        )
        sections.extend(
            [
                f"## {title}",
                "",
                f"Images: {len(manifest[split])}; labeled pixels: {metrics['labeled_pixels']}.",
                "Mean IoU over classes with nonzero union: "
                f"{metrics['mean_iou_present_classes']:.6f}.",
                "",
                "| Class | Precision | Recall | F1 | IoU |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for i, name in enumerate(names):
            values = [
                metrics["per_class_precision"][i],
                metrics["per_class_recall"][i],
                metrics["per_class_f1"][i],
                metrics["class_iou"][name],
            ]
            cells = ["undefined" if v is None else f"{v:.6f}" for v in values]
            sections.append("| " + " | ".join([name] + cells) + " |")
        sections.extend(
            [
                "",
                "Confusion matrix (rows reference, columns predicted; "
                "soil/bedrock/sand/large rocks):",
                "",
                "```json",
                json.dumps(metrics["confusion_matrix"]),
                "```",
                "",
            ]
        )
    sizes = {key: len(manifest[key]) for key in ("train", "validation", "test", "transfer")}
    accepted = all(value is not None and value > 0 for value in report["per_class_recall"])
    text = f"""# MARSENSE AI4Mars prototype model card

Intended use: local research terrain evidence for human review. This model does
not measure mineral identity, soil strength or EVA safety.

Prototype anti-collapse check: {"PASS" if accepted else "FAIL"}. Requires nonzero
validation recall for every implemented class; this is MARSENSE configuration,
not a NASA performance or safety standard. A failed candidate must remain
unavailable for mission classification and S2 stays open.

Dataset: NASA-linked [AI4Mars merged-0.6](https://zenodo.org/records/15995036),
DOI 10.5281/zenodo.15995036, publisher license CC-BY-4.0. Bounded genuine subset,
not the complete archive. Counts: {sizes}. Source files/ranges and per-file hashes
are retained in data/nasa/ai4mars/source.json and the original release metadata.
Whole MSL site groups are disjoint across train/validation/test; all expert-test
sites are excluded from training/validation. Perseverance transfer is never trained.
Crowdsourced reference masks and expert reference masks are annotation evidence,
not physical terrain or safety truth. No benchmark fixture images are used here.

Classes: 0 soil, 1 bedrock, 2 sand, 3 big rock (application: large rocks), 255 ignored.
Train labeled pixels per class: {report["train_labeled_pixels_by_class"]}.
Architecture: {report.get("architecture", "small four-layer dilated convolution baseline")}.
Configuration: seed {report["seed"]}, {report["epochs"]} epochs, deterministic CPU
PyTorch {report["torch_version"]}, Adam .001, batch 2. RGB bilinear 256x256,
float32 /255; mask nearest resize. Preprocessing: {report["preprocessing_version"]}.
Validation metrics remain separate in the checkpoint JSON. Held-out and transfer
sets are evaluated after training; no tuning is performed on their results.
Loss configuration: {report.get("loss", "unweighted CrossEntropy baseline")}.
Loss reduction: {report.get("loss_reduction", "standard CrossEntropy reduction")}.

{chr(10).join(sections)}
## Limitations and failure modes

This is a tiny-subset baseline with uncalibrated scores, class imbalance,
crowdsourced-label noise and substantial viewpoint/lighting/rover/site domain shift.
Single-view classification cannot establish traversability. Transfer scores describe
only these selected images. Adjacent views may remain correlated within a partition.
Undefined metrics reflect missing prediction/reference support, not successful classification.
Poorly detected classes remain limitations, regardless of mean score. No operational
generalization or calibrated hazard probability is established.
Mission terrain classification enabled: {report.get("classification_enabled", True)}.
For this experimental checkpoint, weak held-out performance requires explicit
human terrain identification; raw segmentation fractions and scores are retained.

Mean maximum softmax below .5 yields UNKNOWN; missing/failed/tampered checkpoint
yields unavailable evidence. Unsupported trained-class output yields UNKNOWN.
Human verification remains required. Deterministic replay is separately labeled DEMO.

## Version and artifacts

Checkpoint: ai/checkpoints/ai4mars-prototype.pt, SHA-256 {report["model_sha256"]}.
Dataset manifest SHA-256 {report["manifest_sha256"]}.
Exact training/evaluation/configuration metadata: adjacent checkpoint JSON.
Validation configuration: MARSENSE_MODEL_PATH=ai/checkpoints/ai4mars-prototype.pt.
The adapter refuses a candidate flagged as failed; scientific gate status is in STATUS.md.
Existing live services and saved observations are not silently changed.
"""
    (ROOT / "MODEL_CARD.md").write_text(text, encoding="utf-8")
    print("MODEL_CARD.md generated from genuine held-out and transfer results")


if __name__ == "__main__":
    main()
