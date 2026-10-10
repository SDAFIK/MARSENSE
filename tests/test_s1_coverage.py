from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from backend.routing import astar, load_slope
from backend.spatial import ANALYSIS_CRS
from scripts.process_dem import process


def test_configured_slope_refuses_partial_required_grid(tmp_path):
    grid = np.zeros((21, 31), dtype="float32")
    grid[10, 15] = np.nan
    path = tmp_path / "partial.npz"
    np.savez(path, slope_deg=grid)
    with pytest.raises(ValueError, match="coverage"):
        load_slope(str(path))


def test_direct_routing_refuses_missing_slope_cells():
    grid = np.zeros((21, 31))
    grid[10, 15] = np.nan
    with pytest.raises(ValueError, match="coverage"):
        astar((120, 400), (1080, 400), [], grid)


def test_ingestion_refuses_partial_nodata(tmp_path):
    grid = np.ones((21, 31), dtype="float32")
    grid[10, 15] = np.nan
    source = tmp_path / "partial.tif"
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        height=21,
        width=31,
        count=1,
        dtype="float32",
        crs=ANALYSIS_CRS,
        transform=from_origin(-20, 820, 40, 40),
        nodata=np.nan,
    ) as dst:
        dst.write(grid, 1)
    with pytest.raises(ValueError, match="coverage"):
        process(source, tmp_path / "bad.npz", "test", "https://example.test")
    assert not (tmp_path / "bad.npz").exists()


def test_genuine_covering_grid_aligns_with_route_and_changes_cost():
    root = Path(__file__).resolve().parents[1]
    path = root / "data/processed/hirise-covering-elevation40m.tif"
    with rasterio.open(path) as src:
        elevation = src.read(1)
        assert np.isfinite(elevation).all()
        assert elevation.min() >= -2679.20
        assert elevation.max() <= -2388.31
        assert elevation[0, 0] == pytest.approx(-2567.874267578125)
        assert elevation[10, 15] == pytest.approx(-2571.6513671875)
        assert elevation[20, 30] == pytest.approx(-2598.330078125)
        assert src.xy(10, 3) == pytest.approx((120, 400))
        assert src.xy(10, 27) == pytest.approx((1080, 400))
    slopes = load_slope(str(root / "data/processed/hirise-covering-slope.npz"))
    flat = astar((120, 400), (1080, 400), [])
    derived = astar((120, 400), (1080, 400), [], slopes)
    assert derived.coordinates
    assert derived.breakdown["slope"] > 0
    assert derived.cost > flat.cost


def test_native_sample_indices_match_independent_gdal_pds_pixel_centers():
    import json

    from pyproj import Transformer
    from rasterio.io import MemoryFile

    from backend.spatial import to_mars

    root = Path(__file__).resolve().parents[1]
    header = next((root / 'data/nasa/ranges').glob('DTEEC_045994*0-30000.bin'))
    metadata = json.loads((root / 'data/processed/hirise-covering-slope.json').read_text())
    with MemoryFile(header.read_bytes()) as memory:
        with memory.open() as source:
            projector = Transformer.from_crs(source.crs.geodetic_crs, source.crs, always_xy=True)
            px, py = projector.transform(*to_mars(0, 800))
            col, row = (~source.transform) * (px, py)
            expected = round(col-.5), round(row-.5)
            record_bytes = source.width * 4
            offset = metadata['ranges'][1]['offset'] - record_bytes
            actual_row, column_bytes = divmod(offset, record_bytes)
            assert (column_bytes//4, actual_row) == expected


def test_configured_grid_rejects_crs_mismatch(tmp_path):
    import json

    path = tmp_path / "wrong.npz"
    np.savez(path, slope_deg=np.zeros((21, 31)))
    path.with_suffix(".json").write_text(json.dumps({"analysis_crs": "EPSG:3857"}))
    with pytest.raises(ValueError, match="CRS"):
        load_slope(str(path))


def test_covering_ingestion_reproduces_offline_without_touching_live_data(tmp_path, monkeypatch):
    from scripts import cache_hirise_dtm

    def refuse_network(*args, **kwargs):
        raise AssertionError("Cached DTM regeneration must not need network")

    monkeypatch.setattr("urllib.request.urlopen", refuse_network)
    monkeypatch.setattr(cache_hirise_dtm, "ROOT", tmp_path)
    processed = tmp_path / "data/processed"
    processed.mkdir(parents=True)
    (processed / "manifest.json").write_text("{}")
    result = cache_hirise_dtm.cache()
    assert result["coverage_fraction"] == 1
    assert result["native_bounds_lonlat"] == pytest.approx(
        [77.3833804, 18.305293550569, 77.50109494, 18.548391096554]
    )
    with np.load(processed / "hirise-covering-slope.npz") as actual:
        root = Path(__file__).resolve().parents[1]
        with np.load(root / "data/processed/hirise-covering-slope.npz") as expected:
            assert np.array_equal(actual["elevation_m"], expected["elevation_m"])
            assert np.array_equal(actual["slope_deg"], expected["slope_deg"])


def test_configured_grid_detects_tampered_processed_bytes(tmp_path):
    import shutil

    root = Path(__file__).resolve().parents[1]
    source = root / "data/processed/hirise-covering-slope.npz"
    path = tmp_path / "tampered.npz"
    shutil.copyfile(source.with_suffix(".json"), path.with_suffix(".json"))
    with np.load(source) as cached:
        np.savez(path, elevation_m=cached["elevation_m"], slope_deg=cached["slope_deg"] + 0.01)
    with pytest.raises(ValueError, match="hash"):
        load_slope(str(path))


def test_ingestion_rejects_unexpected_longitude_direction(monkeypatch):
    from scripts import cache_hirise_dtm

    root = Path(__file__).resolve().parents[1]
    label = (
        root / "data/nasa/ranges" / "DTEEC_045994_1985_046060_1985_U01-label-0-30000.bin"
    ).read_bytes()
    import re

    modified = re.sub(rb"(POSITIVE_LONGITUDE_DIRECTION\s*=\s*)EAST", rb"\1WEST", label)
    monkeypatch.setattr(cache_hirise_dtm, "range_bytes", lambda *a: (modified, {}))
    with pytest.raises(ValueError, match="POSITIVE_LONGITUDE_DIRECTION"):
        cache_hirise_dtm.cache()
