"""Integration checks require the actual bounded dataset and exported checkpoint."""

import hashlib
import json
from pathlib import Path

import pytest

from ai.perception import Perception
from backend.domain import Terrain


def test_genuine_checkpoint_provenance_and_separate_evaluations():
    root = Path(__file__).resolve().parents[1]
    model = root / "ai/checkpoints/ai4mars-prototype.pt"
    metadata = json.loads(model.with_suffix(".json").read_text())
    assert metadata["model_sha256"] == hashlib.sha256(model.read_bytes()).hexdigest()
    assert metadata["split_sizes"] == {"train": 48, "validation": 16, "test": 16, "transfer": 8}
    assert all(count > 0 for count in metadata["train_labeled_pixels_by_class"])
    # Prototype anti-collapse gate, not a NASA performance/safety standard.
    assert all(recall is not None and recall > 0 for recall in metadata["per_class_recall"])
    assert metadata["test_evaluation"]["labeled_pixels"] > 0
    assert metadata["transfer_evaluation"]["labeled_pixels"] > 0
    manifest_path = root / "data/nasa/ai4mars/subset.json"
    assert metadata["manifest_sha256"] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    manifest = json.loads(manifest_path.read_text())
    content = (manifest_path.parent / manifest["test"][0]["image"]).read_bytes()
    adapter = Perception(str(model))
    prediction = adapter.infer(content)
    assert prediction.engine == "torchscript-ai4mars"
    assert metadata["model_sha256"] in prediction.version
    assert sum(prediction.class_fractions.values()) == pytest.approx(1)
    assert adapter.infer(content) == prediction
    if not metadata.get("classification_enabled", True):
        assert prediction.terrain == Terrain.UNKNOWN
