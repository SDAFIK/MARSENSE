"""Train/evaluate a small four-class segmentation baseline on local AI4Mars labels.

Input JSON: {"train": [{"image": "...", "mask": "..."}], "validation": [...]}
Paths relative to manifest. Labels 0 soil, 1 bedrock, 2 sand, 3 large rocks, 255 ignore.
Use disjoint rover/site/sequence splits; this baseline is not a certified flight model.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset


class TerrainNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder1 = self.block(3, 16)
        self.encoder2 = self.block(16, 32)
        self.bottleneck = self.block(32, 64)
        self.decoder2 = self.block(96, 32)
        self.decoder1 = self.block(48, 16)
        self.head = nn.Conv2d(16, 4, 1)

    @staticmethod
    def block(inputs: int, outputs: int) -> nn.Sequential:
        return nn.Sequential(
            nn.Conv2d(inputs, outputs, 3, padding=1),
            nn.BatchNorm2d(outputs),
            nn.ReLU(),
            nn.Conv2d(outputs, outputs, 3, padding=1),
            nn.BatchNorm2d(outputs),
            nn.ReLU(),
        )

    def forward(self, pixels: torch.Tensor) -> torch.Tensor:
        first = self.encoder1(pixels)
        second = self.encoder2(torch.nn.functional.max_pool2d(first, 2))
        middle = self.bottleneck(torch.nn.functional.max_pool2d(second, 2))
        up = torch.nn.functional.interpolate(
            middle, size=second.shape[-2:], mode="bilinear", align_corners=False
        )
        decoded = self.decoder2(torch.cat([up, second], dim=1))
        up = torch.nn.functional.interpolate(
            decoded, size=first.shape[-2:], mode="bilinear", align_corners=False
        )
        return self.head(self.decoder1(torch.cat([up, first], dim=1)))


class LabeledImages(Dataset):
    def __init__(self, rows: list[dict[str, str]], base: Path) -> None:
        self.rows, self.base = rows, base

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.rows[index]
        with Image.open(self.base / row["image"]) as image:
            rgb = (
                np.array(
                    image.convert("RGB").resize((256, 256), Image.Resampling.BILINEAR),
                    dtype="float32",
                )
                / 255
            )
        with Image.open(self.base / row["mask"]) as image:
            mask = np.array(image.resize((256, 256), Image.Resampling.NEAREST), dtype="int64")
        if mask.ndim != 2 or not np.isin(mask, [0, 1, 2, 3, 255]).all():
            raise ValueError("Expected AI4Mars single-channel integer labels 0..3 or 255")
        return torch.from_numpy(rgb.transpose(2, 0, 1).copy()), torch.from_numpy(mask.copy())


def evaluate(model: nn.Module, loader: DataLoader) -> dict[str, object]:
    confusion = torch.zeros((4, 4), dtype=torch.int64)
    model.eval()
    with torch.inference_mode():
        for images, labels in loader:
            predicted = model(images).argmax(dim=1)
            valid = labels != 255
            counts = torch.bincount(4 * labels[valid] + predicted[valid], minlength=16)
            confusion += counts.reshape(4, 4)
    total = int(confusion.sum())
    if not total:
        raise ValueError("Validation set has no labeled pixels")
    diagonal = confusion.diag().float()
    union = confusion.sum(0) + confusion.sum(1) - diagonal
    iou = [float(diagonal[i] / union[i]) if union[i] else None for i in range(4)]
    observed = [v for v in iou if v is not None]
    precision = [
        float(diagonal[i] / confusion.sum(0)[i]) if confusion.sum(0)[i] else None for i in range(4)
    ]
    recall = [
        float(diagonal[i] / confusion.sum(1)[i]) if confusion.sum(1)[i] else None for i in range(4)
    ]
    f1 = [
        float(2 * diagonal[i] / (confusion.sum(0)[i] + confusion.sum(1)[i]))
        if confusion.sum(0)[i] + confusion.sum(1)[i]
        else None
        for i in range(4)
    ]
    return {
        "confusion_matrix": confusion.tolist(),
        "pixel_accuracy": float(diagonal.sum() / total),
        "class_iou": dict(zip(["soil", "bedrock", "sand", "large rocks"], iou)),
        "mean_iou_present_classes": sum(observed) / len(observed),
        "labeled_pixels": total,
        "per_class_precision": precision,
        "per_class_recall": recall,
        "per_class_f1": f1,
    }


def train(manifest: Path, output: Path, epochs: int, seed: int = 42) -> dict[str, object]:
    if epochs < 1:
        raise ValueError("At least one training epoch required")
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(2)
    content = manifest.read_bytes()
    data = json.loads(content)
    if not data.get("train") or not data.get("validation"):
        raise ValueError("Nonempty train and validation splits required")
    splits = [key for key in ("train", "validation", "test", "transfer") if data.get(key)]
    for i, first in enumerate(splits):
        for second in splits[i + 1 :]:
            groups_a = {r["group"] for r in data[first] if r.get("group")}
            groups_b = {r["group"] for r in data[second] if r.get("group")}
            if groups_a & groups_b:
                raise ValueError("Dataset group overlap across splits")
    hashes: dict[str, set[str]] = {}
    for split in splits:
        for row in data[split]:
            for key in ("image", "mask"):
                expected_hash = row.get(key + "_sha256")
                if (
                    expected_hash
                    and expected_hash
                    != hashlib.sha256((manifest.parent / row[key]).read_bytes()).hexdigest()
                ):
                    raise ValueError("Dataset file hash differs from source manifest")
        hashes[split] = {
            hashlib.sha256((manifest.parent / r["image"]).read_bytes()).hexdigest()
            for r in data[split]
        }
        for previous in hashes:
            if previous != split and hashes[previous] & hashes[split]:
                raise ValueError("Dataset image byte hashes overlap across splits")
    training_paths = {str((manifest.parent / r["image"]).resolve()) for r in data["train"]}
    validation_paths = {str((manifest.parent / r["image"]).resolve()) for r in data["validation"]}
    if training_paths & validation_paths:
        raise ValueError("Training and validation image paths overlap")
    model = TerrainNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    training = DataLoader(LabeledImages(data["train"], manifest.parent), batch_size=2, shuffle=True)
    validation = DataLoader(LabeledImages(data["validation"], manifest.parent), batch_size=2)
    class_counts = torch.zeros(4, dtype=torch.int64)
    labeled_training = LabeledImages(data["train"], manifest.parent)
    for index in range(len(labeled_training)):
        _, labels = labeled_training[index]
        class_counts += torch.bincount(labels[labels != 255], minlength=4)
    weights = class_counts.sum().float() / (4 * class_counts.clamp(min=1).float())
    criterion = nn.CrossEntropyLoss(ignore_index=255, weight=weights, reduction="none")
    training_steps = 0
    for epoch in range(epochs):
        model.train()
        for pixels, labels in training:
            if not (labels != 255).any():
                continue
            optimizer.zero_grad()
            loss = criterion(model(pixels), labels).sum() / (labels != 255).sum()
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            training_steps += 1
        print(f"epoch {epoch + 1}/{epochs}: {training_steps} cumulative training steps", flush=True)
    if training_steps == 0:
        raise ValueError("Training split contains no labeled pixels; refusing untrained export")
    report = evaluate(model, validation)
    report["prototype_validation_passed"] = (
        all(
            value is not None and value > 0
            for value in cast(list[float | None], report["per_class_recall"])
        )
        if data.get("source_metadata")
        else None
    )
    for split in ("test", "transfer"):
        if data.get(split):
            report[split + "_evaluation"] = evaluate(
                model, DataLoader(LabeledImages(data[split], manifest.parent), batch_size=2)
            )
    report.update(
        {
            "seed": seed,
            "epochs": epochs,
            "manifest_sha256": hashlib.sha256(content).hexdigest(),
            "train_images": len(data["train"]),
            "validation_images": len(data["validation"]),
            "limitations": "Baseline; uncalibrated; rover/site domain transfer unvalidated.",
            "preprocessing_version": "rgb-bilinear256-mask-nearest-v1",
            "normalization": "RGB float32 divided by 255; no channel standardization",
            "class_mapping": {"0": "soil", "1": "bedrock", "2": "sand", "3": "large rocks"},
            "optimizer": {"name": "Adam", "learning_rate": 0.001, "batch_size": 2},
            "loss": "CrossEntropy with inverse-frequency weights from training pixels only",
            "loss_reduction": "Weighted valid pixel sum / valid pixel count "
            "(no per-batch weight renormalization)",
            "architecture": "Small U-Net; Conv/BatchNorm/ReLU, 16/32/64 channels, "
            "bilinear skip decoder",
            "loss_class_weights": weights.tolist(),
            "split_sizes": {split: len(data[split]) for split in splits},
            "dataset_source": data.get("source_metadata", "synthetic/local operator manifest"),
            "classification_enabled": not bool(data.get("source_metadata")),
            "classification_policy": "Genuine experimental checkpoints retain raw scores; "
            "mission terrain identification requires human review until independent calibration",
            "torch_version": str(torch.__version__),
            "training_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "train_labeled_pixels_by_class": class_counts.tolist(),
            "trained_classes": [
                name
                for name, count in zip(
                    ["soil", "bedrock", "sand", "large rocks"], class_counts.tolist()
                )
                if count
            ],
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.jit.script(model.eval()).save(str(output))
    report["model_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epochs", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(train(args.manifest, args.output, args.epochs), indent=2))
