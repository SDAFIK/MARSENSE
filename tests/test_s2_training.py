import json

import pytest
from PIL import Image

from ai.perception import Perception
from ai.train import train
from backend.domain import Terrain


def test_training_refuses_same_pixels_under_different_names(tmp_path):
    for name in ("train", "validation"):
        Image.new("RGB", (16, 16), "tan").save(tmp_path / f"{name}.png")
        Image.new("L", (16, 16), 0).save(tmp_path / f"{name}-mask.png")
    manifest = tmp_path / "split.json"
    manifest.write_text(
        json.dumps(
            {
                name: [{"image": f"{name}.png", "mask": f"{name}-mask.png"}]
                for name in ("train", "validation")
            }
        )
    )
    with pytest.raises(ValueError, match="overlap"):
        train(manifest, tmp_path / "bad.pt", 1)


def test_training_refuses_same_site_across_splits(tmp_path):
    manifest = tmp_path / "split.json"
    manifest.write_text(
        json.dumps(
            {
                name: [{"image": f"{name}.png", "mask": "mask.png", "group": "msl-site-001"}]
                for name in ("train", "validation")
            }
        )
    )
    with pytest.raises(ValueError, match="group"):
        train(manifest, tmp_path / "bad.pt", 1)


def test_low_confidence_and_invalid_image_remain_explicit(tmp_path):
    import hashlib
    import io

    import torch

    class Uniform(torch.nn.Module):
        def forward(self, pixels):
            return pixels[:, :1].repeat(1, 4, 1, 1) * 0

    path = tmp_path / "fixture-uniform.pt"
    torch.jit.trace(Uniform(), torch.zeros(1, 3, 256, 256)).save(str(path))
    path.with_suffix(".json").write_text(
        json.dumps(
            {
                "model_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "preprocessing_version": "rgb-bilinear256-mask-nearest-v1",
            }
        )
    )
    content = io.BytesIO()
    Image.new("RGB", (20, 20), "tan").save(content, "PNG")
    result = Perception(str(path)).infer(content.getvalue())
    assert result.terrain == Terrain.UNKNOWN
    assert result.confidence == pytest.approx(0.25)
    assert result.confidence_label == "low"
    with pytest.raises(ValueError, match="decoded"):
        Perception(str(path)).infer(b"not an image")
    metadata_path = path.with_suffix(".json")
    metadata = json.loads(metadata_path.read_text())
    metadata["prototype_validation_passed"] = False
    metadata_path.write_text(json.dumps(metadata))
    rejected = Perception(str(path)).infer(content.getvalue())
    assert rejected.terrain == Terrain.UNKNOWN
    assert rejected.engine == "unavailable"
    assert metadata["model_sha256"] in rejected.version
