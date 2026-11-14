import hashlib
import json

import pytest
from PIL import Image

from ai.research_gate import audit_manifest, evaluate_candidate


def test_research_gate_never_enables_classification():
    metrics = {"mean_iou_present_classes": 0.65, "per_class_recall": [0.6] * 4,
               "labeled_pixels": 10000}
    report = {s + "_evaluation": metrics for s in ("validation", "test", "transfer")}
    result = evaluate_candidate(report)
    assert result["research_screen_passed"]
    assert result["classification_enabled"] is False
    assert not evaluate_candidate({})["research_screen_passed"]
    report["transfer_evaluation"] = {**metrics, "mean_iou_present_classes": 0.13}
    assert not evaluate_candidate(report)["research_screen_passed"]


def test_dataset_audit_rejects_leakage_and_checks_bytes(tmp_path):
    data = {}
    for index, split in enumerate(("train", "validation", "test", "transfer")):
        image, mask = tmp_path / f"{split}.png", tmp_path / f"{split}-mask.png"
        Image.new("RGB", (4, 4), (index, 50, 80)).save(image)
        labels = Image.new("L", (2, 2))
        labels.putdata([0, 1, 2, 3])
        labels.save(mask)
        data[split] = [{"image": image.name, "mask": mask.name, "group": split,
                        "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                        "mask_sha256": hashlib.sha256(mask.read_bytes()).hexdigest()}]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(data))
    audit = audit_manifest(manifest)
    assert audit["unique_images"] == 4
    assert audit["resampled_pairs"] == dict.fromkeys(data, 1)
    data["transfer"][0]["group"] = "train"
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="group"):
        audit_manifest(manifest)
    data["transfer"][0]["group"] = "transfer"
    data["test"][0]["image_sha256"] = "invalid"
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="hash"):
        audit_manifest(manifest)


def test_unexplained_aspect_ratio_is_rejected(tmp_path):
    image = tmp_path / "image.png"
    mask = tmp_path / "mask.png"
    Image.new("RGB", (4, 2)).save(image)
    Image.new("L", (2, 2)).save(mask)
    row = {"image": image.name, "mask": mask.name, "group": "train",
           "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
           "mask_sha256": hashlib.sha256(mask.read_bytes()).hexdigest()}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"train": [row]}))
    with pytest.raises(ValueError, match="aspect mismatch"):
        audit_manifest(manifest)
