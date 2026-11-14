"""Research-only AI4Mars candidate audit and release gate; never enables a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image
import numpy as np

CLASSES = ("soil", "bedrock", "sand", "large rocks")
SPLITS = ("train", "validation", "test", "transfer")


def audit_manifest(manifest: Path) -> dict[str, Any]:
    """Verify disjoint site groups and image bytes, label validity and source hashes."""
    data = json.loads(manifest.read_text())
    root = manifest.parent
    # Frozen genuine manifests are stored in manifests/, with assets relative to
    # their parent dataset directory. Other manifests resolve beside themselves.
    if root.name == "manifests":
        root = root.parent
    groups: dict[str, str] = {}
    images: dict[str, str] = {}
    counts: dict[str, list[int]] = {}
    for split in SPLITS:
        rows = data.get(split, [])
        if not rows:
            raise ValueError(f"Missing nonempty {split} split")
        totals = np.zeros(4, dtype=np.int64)
        for row in rows:
            group = row.get("group")
            if not group:
                raise ValueError("Every image needs a rover/site group")
            if group in groups and groups[group] != split:
                raise ValueError("Site group crosses splits")
            groups[group] = split
            files = {}
            for kind in ("image", "mask"):
                path = (root / row[kind]).resolve()
                if not path.is_relative_to(root.resolve()):
                    raise ValueError("Dataset path escapes root")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest != row.get(kind + "_sha256"):
                    raise ValueError(f"{kind} hash missing or mismatched")
                files[kind] = path
                if kind == "image":
                    if digest in images:
                        raise ValueError("Duplicate image bytes")
                    images[digest] = split
            with Image.open(files["image"]) as img, Image.open(files["mask"]) as mask:
                if img.size != mask.size:
                    raise ValueError("Image/mask geometry differs")
                labels = np.asarray(mask)
                if labels.ndim != 2 or not np.isin(labels, [0, 1, 2, 3, 255]).all():
                    raise ValueError("Invalid AI4Mars label values")
                totals += np.bincount(labels[labels != 255].astype(int), minlength=4)
        counts[split] = totals.tolist()
    if any(min(counts[split]) == 0 for split in ("train", "validation", "test", "transfer")):
        raise ValueError("All four classes need labeled support in every split")
    return {"manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "split_sizes": {s: len(data[s]) for s in SPLITS},
            "class_pixels": counts, "site_groups": len(groups), "unique_images": len(images)}


def evaluate_candidate(report: dict[str, Any]) -> dict[str, Any]:
    """Conservative research screening, not calibration or safety certification."""
    issues: list[str] = []
    thresholds = {"validation": 0.40, "test": 0.40, "transfer": 0.35}
    for split, minimum in thresholds.items():
        metrics = report.get(split + "_evaluation", {})
        iou = metrics.get("mean_iou_present_classes")
        if not isinstance(iou, (int, float)) or isinstance(iou, bool) or not math.isfinite(iou) or not minimum <= iou <= 1:
            issues.append(f"{split}: mean IoU must be at least {minimum}")
        recall = metrics.get("per_class_recall", [])
        if len(recall) != 4 or any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or not 0.20 <= x <= 1 for x in recall):
            issues.append(f"{split}: every class needs recall >= 0.20")
        pixels = metrics.get("labeled_pixels", 0)
        if not isinstance(pixels, int) or pixels < 1:
            issues.append(f"{split}: missing labeled support")
    return {"research_screen_passed": not issues, "issues": issues,
            "classification_enabled": False,
            "note": "Screening thresholds are project-defined. Independent calibration, localization and human review remain required."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit_manifest(args.manifest)
    if args.report:
        result["candidate_gate"] = evaluate_candidate(json.loads(args.report.read_text()))
    print(json.dumps(result, indent=2))
