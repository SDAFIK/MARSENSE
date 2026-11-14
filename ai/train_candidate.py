"""Research-only transfer learning candidate; no production enablement.

Run in an isolated CPU/GPU training environment with torchvision installed.
DeepLabV3 MobileNetV3 weights are general-image pretrained, not Mars validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader

from ai.research_gate import audit_manifest, evaluate_candidate
from ai.train import LabeledImages, evaluate


class Candidate(nn.Module):
    mean: torch.Tensor
    std: torch.Tensor

    def __init__(self, network: nn.Module):
        super().__init__()
        self.network = network
        self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.network((images - self.mean) / self.std)["out"]


def train_candidate(manifest: Path, output: Path, epochs: int = 8,
                    seed: int = 42) -> dict[str, Any]:
    if epochs < 1:
        raise ValueError("Positive epoch count required")
    audit = audit_manifest(manifest)
    data = json.loads(manifest.read_text())
    root = manifest.parent.parent if manifest.parent.name == "manifests" else manifest.parent
    # Optional research dependency; the production backend does not import it.
    from torchvision.models.segmentation import (
        DeepLabV3_MobileNet_V3_Large_Weights,
        deeplabv3_mobilenet_v3_large,
    )

    torch.manual_seed(seed)
    torch.set_num_threads(2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    weights = DeepLabV3_MobileNet_V3_Large_Weights.DEFAULT
    network = deeplabv3_mobilenet_v3_large(weights=weights)
    network.classifier[-1] = nn.Conv2d(network.classifier[-1].in_channels, 4, 1)
    network.aux_classifier = None
    model = Candidate(network).to(device)
    train = LabeledImages(data["train"], root)
    loaders = {s: DataLoader(LabeledImages(data[s], root), batch_size=2)
               for s in ("validation", "test", "transfer")}
    training = DataLoader(train, batch_size=2, shuffle=True, drop_last=True)
    if not len(training):
        raise ValueError("At least two training images required")
    counts = torch.tensor(audit["class_pixels"]["train"], dtype=torch.float32)
    # Square-root inverse-frequency weights reduce extreme rare-class amplification.
    class_weights = (counts.sum() / counts.clamp(min=1)).sqrt()
    class_weights = (class_weights / class_weights.mean()).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, ignore_index=255)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0001)
    steps = 0
    for epoch in range(epochs):
        model.train()
        for images, labels in training:
            if not (labels != 255).any():
                continue
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            steps += 1
        print(f"epoch {epoch + 1}/{epochs}; steps={steps}", flush=True)
    if not steps:
        raise ValueError("No training steps")
    model = model.cpu().eval()
    report: dict[str, Any] = {s + "_evaluation": evaluate(model, loader)
                              for s, loader in loaders.items()}
    report.update({
        "architecture": "DeepLabV3 MobileNetV3 Large, general-image pretrained",
        "pretrained_weights": str(weights),
        "seed": seed, "epochs": epochs, "training_steps": steps,
        "dataset_audit": audit, "preprocessing_version": "rgb-bilinear256-mask-nearest-v1",
        "trained_classes": ["soil", "bedrock", "sand", "large rocks"],
        "classification_enabled": False, "prototype_validation_passed": False,
        "limitations": "Research candidate only; not calibrated or approved "
                       "for mission classification.",
    })
    report["research_gate"] = evaluate_candidate(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    example = torch.zeros(1, 3, 256, 256)
    with torch.inference_mode():
        traced = torch.jit.trace(model, example)
        actual = traced(example)
        if actual.shape != (1, 4, 256, 256) or not torch.isfinite(actual).all():
            raise ValueError("Invalid exported segmentation output")
    traced.save(str(output))
    report["model_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args()
    print(json.dumps(train_candidate(args.manifest, args.output, args.epochs), indent=2))
