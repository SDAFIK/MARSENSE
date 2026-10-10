import io
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
import torch
from PIL import Image
from rasterio.transform import from_origin

from ai.perception import Perception
from ai.train import train
from backend.domain import Terrain
from backend.routing import COLS, ROWS, astar, load_slope
from backend.spatial import ANALYSIS_CRS
from scripts.process_dem import process


def test_dem_plane_gradient_and_routing_barrier(tmp_path: Path) -> None:
    elevation = np.broadcast_to(np.arange(COLS) * 4.0, (ROWS, COLS)).astype("float32")
    source = tmp_path / "plane.tif"
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        height=ROWS,
        width=COLS,
        count=1,
        dtype="float32",
        crs=ANALYSIS_CRS,
        transform=from_origin(-20, 820, 40, 40),
    ) as dataset:
        dataset.write(elevation, 1)
    output = tmp_path / "plane.npz"
    metadata = process(source, output, "synthetic-test-plane", "https://example.test/plane")
    assert metadata["coverage_fraction"] == 1
    slopes = load_slope(str(output))
    assert np.allclose(slopes, np.degrees(np.arctan(0.1)), atol=1e-5)
    flat = astar((120, 400), (1080, 400), [])
    sloped = astar((120, 400), (1080, 400), [], slopes)
    assert sloped.breakdown["slope"] > 500
    assert sloped.cost > flat.cost
    barrier = np.zeros((ROWS, COLS))
    barrier[:, 15] = 25
    assert astar((120, 400), (1080, 400), [], barrier).coordinates == []


def test_dem_refuses_earth_coordinates(tmp_path: Path) -> None:
    source = tmp_path / "earth.tif"
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        crs="EPSG:3857",
        transform=from_origin(0, 80, 40, 40),
    ) as dataset:
        dataset.write(np.ones((2, 2), dtype="float32"), 1)
    with pytest.raises(ValueError, match="refusing Earth"):
        process(source, tmp_path / "bad.npz", "earth", "https://example.test")


def test_training_export_inference_and_split_isolation(tmp_path: Path) -> None:
    # Synthetic pipeline test only: these metrics are NOT Mars classification performance.
    for name in ["train", "validation"]:
        Image.new("RGB", (16, 16), "tan" if name == "train" else "brown").save(
            tmp_path / f"{name}.png"
        )
        Image.new("L", (16, 16), 0).save(tmp_path / f"{name}-mask.png")
    manifest = tmp_path / "split.json"
    data = {
        name: [{"image": f"{name}.png", "mask": f"{name}-mask.png"}]
        for name in ["train", "validation"]
    }
    manifest.write_text(json.dumps(data))
    model = tmp_path / "terrain.pt"
    report = train(manifest, model, epochs=1)
    assert report["labeled_pixels"] == 256 * 256
    assert len(report["model_sha256"]) == 64
    output = io.BytesIO()
    Image.new("RGB", (32, 32), "tan").save(output, "PNG")
    prediction = Perception(str(model)).infer(output.getvalue())
    assert prediction == Perception(str(model)).infer(output.getvalue())
    assert report["model_sha256"] in prediction.version
    assert prediction.engine == "torchscript-ai4mars"
    assert sum(prediction.class_fractions.values()) == pytest.approx(1)
    assert torch.jit.load(str(model))(torch.zeros(1, 3, 256, 256)).shape == (1, 4, 256, 256)
    data["validation"] = data["train"]
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="overlap"):
        train(manifest, tmp_path / "leaked.pt", 1)
    model.write_bytes(model.read_bytes() + b"tampered")
    assert Perception(str(model)).infer(output.getvalue()).terrain == Terrain.UNKNOWN


def test_model_failure_remains_reviewable() -> None:
    output = io.BytesIO()
    Image.new("RGB", (16, 16)).save(output, "PNG")
    prediction = Perception("missing-checkpoint.pt").infer(output.getvalue())
    assert prediction.terrain == Terrain.UNKNOWN
    assert prediction.confidence == 0
