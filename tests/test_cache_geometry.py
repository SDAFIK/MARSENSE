import hashlib
import json

import pytest
from PIL import Image
from pyproj import CRS

from backend.config import ROOT
from backend.spatial import ANALYSIS_CRS, to_local


def test_cached_imagery_uses_actual_pixel_bounds_and_mars_crs() -> None:
    manifest = json.loads((ROOT / "data/processed/manifest.json").read_text())
    for name in ("ctx", "hirise"):
        item = manifest[name]
        assert CRS(item["analysis_crs"]) == CRS(ANALYSIS_CRS)
        path = ROOT / f"data/nasa/jezero-{name}.png"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        with Image.open(path) as image:
            assert list(image.size) == item["pixel_size"]
        corners = [to_local(*corner) for corner in item["render_corners"]]
        x_size, y_size = item["effective_pixel_m"]
        assert corners[1][0] - corners[0][0] == pytest.approx(item["pixel_size"][0] * x_size)
        assert corners[0][1] - corners[3][1] == pytest.approx(item["pixel_size"][1] * y_size)
        # Requested bounds and actual pixel-rounded bounds can differ by at most half a pixel.
        assert abs(corners[0][0]) <= x_size / 2 + 1e-7
        assert abs(corners[0][1] - 800) <= y_size / 2 + 1e-7
