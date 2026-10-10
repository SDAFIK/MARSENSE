"""Sample a bounded genuine HiRISE DTM using its PDS3 label and exact byte ranges."""

import json
import math
import re

import numpy as np
from rasterio.transform import from_origin

from backend.config import ROOT
from backend.spatial import ANALYSIS_CRS, to_mars
from scripts.cache_context import range_bytes, write_raster
from scripts.process_dem import process

PRODUCT = "DTEEC_045994_1985_046060_1985_U01"
URL = (
    "https://hirise.lpl.arizona.edu/PDS/DTM/ESP/ORB_045900_045999/"
    f"ESP_045994_1985_ESP_046060_1985/{PRODUCT}.IMG"
)


def number(label: str, key: str) -> float:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*([-+\d.eE]+)", label, re.MULTILINE)
    if not match:
        raise ValueError(f"Missing PDS numeric field {key}")
    return float(match.group(1))


def cache() -> dict[str, object]:
    raw, header = range_bytes(URL, 0, 30000, PRODUCT + "-label")
    label = raw.decode("ascii", errors="ignore").replace("\r", "\n")
    for expected in (PRODUCT, "PC_REAL", "EQUIRECTANGULAR", "PLANETOCENTRIC", "METERS/PIXEL"):
        if expected not in label:
            raise ValueError("Unsupported PDS projection/sample format")
    if "meters above the martian equipotential surface" not in label:
        raise ValueError("Elevation units/datum were not verified")
    for key, expected in {
        "TARGET_NAME": "MARS",
        "COORDINATE_SYSTEM_NAME": "PLANETOCENTRIC",
        "POSITIVE_LONGITUDE_DIRECTION": "EAST",
        "MISSING_CONSTANT": "16#FF7FFFFB#",
    }.items():
        if not re.search(rf'^\s*{key}\s*=\s*"?{re.escape(expected)}"?\s*$', label, re.MULTILINE):
            raise ValueError(f"Unsupported PDS coordinate or missing-pixel field {key}")
    if number(label, "SAMPLE_BITS") != 32 or number(label, "MAP_PROJECTION_ROTATION") != 0:
        raise ValueError("Unsupported sample width or map rotation")
    radius = number(label, "A_AXIS_RADIUS") * 1000
    if any(number(label, key) * 1000 != radius for key in ("B_AXIS_RADIUS", "C_AXIS_RADIUS")):
        raise ValueError("Source is not the supported spherical Mars projection")
    scale = number(label, "MAP_SCALE")
    center = number(label, "CENTER_LONGITUDE")
    true_latitude = number(label, "CENTER_LATITUDE")
    columns, rows = int(number(label, "LINE_SAMPLES")), int(number(label, "LINES"))
    record = int(number(label, "RECORD_BYTES"))
    offset = record * (int(number(label, "^IMAGE")) - 1)
    if record != columns * 4:
        raise ValueError("Unsupported row padding; inspect product label")
    minimum, maximum = number(label, "VALID_MINIMUM"), number(label, "VALID_MAXIMUM")
    source_crs = f"+proj=eqc +lat_ts={true_latitude} +lon_0={center} +R={radius} +units=m"
    grid = np.full((21, 31), np.nan, dtype="float32")
    ranges = [header]
    for i, y in enumerate(range(800, -1, -40)):
        positions = []
        for j, x in enumerate(range(0, 1201, 40)):
            lon, lat = to_mars(x, y)
            px = radius * math.cos(math.radians(true_latitude)) * math.radians(lon - center)
            py = radius * math.radians(lat)
            # PDS projection offsets locate pixel centers. GDAL's corner transform
            # already accounts for half a pixel; do not subtract it a second time.
            col = round(px / scale + number(label, "SAMPLE_PROJECTION_OFFSET"))
            row = round(number(label, "LINE_PROJECTION_OFFSET") - py / scale)
            if 0 <= col < columns and 0 <= row < rows:
                positions.append((j, col, row))
        if not positions:
            continue
        source_row = positions[0][2]
        if any(p[2] != source_row for p in positions):
            raise ValueError("Source row variation requires a different sampling adapter")
        left, right = min(p[1] for p in positions), max(p[1] for p in positions)
        content, metadata = range_bytes(
            URL, offset + source_row * record + left * 4, (right - left + 1) * 4, PRODUCT
        )
        ranges.append(metadata)
        values = np.frombuffer(content, dtype="<f4")
        for j, col, _ in positions:
            value = float(values[col - left])
            if minimum <= value <= maximum:
                grid[i, j] = value * number(label, "SCALING_FACTOR") + number(label, "OFFSET")
    if not np.isfinite(grid).any():
        raise ValueError("No valid mission coverage; refusing active DEM")
    source = ROOT / "data/processed/hirise-covering-elevation40m.tif"
    write_raster(source, grid, ANALYSIS_CRS, from_origin(-20, 820, 40, 40))
    metadata = process(source, ROOT / "data/processed/hirise-covering-slope.npz", PRODUCT, URL)
    metadata.update(
        {
            "native_source_crs": source_crs,
            "native_resolution_m": scale,
            "native_bounds_lonlat": [
                number(label, "WESTERNMOST_LONGITUDE"),
                number(label, "MINIMUM_LATITUDE"),
                number(label, "EASTERNMOST_LONGITUDE"),
                number(label, "MAXIMUM_LATITUDE"),
            ],
            "native_missing_constant": "16#FF7FFFFB# (IEEE float32 PDS special pixel)",
            "vertical_datum": "Mars 2000 equipotential surface; PDS IMAGE NOTE",
            "elevation_units": "meters, verified in PDS label",
            "classification": "DERIVED: official stereo DTM, sampled mission grid and slope",
            "ranges": ranges,
            "source_dimensions": [columns, rows],
            "processing": "Nearest native samples at 40 m mission nodes; metric gradient at 40 m",
            "pixel_convention": "PDS pixel centers, independently checked with GDAL PDS driver",
            "limitations": "Coarse planning slope; not foot-scale obstacle "
            "or EVA safety certification",
        }
    )
    output = ROOT / "data/processed/hirise-covering-slope.json"
    output.write_text(json.dumps(metadata, indent=2))
    manifest_path = ROOT / "data/processed/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["dtm_covering"] = metadata
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return metadata


if __name__ == "__main__":
    result = cache()
    print(
        json.dumps({k: result[k] for k in ("product_id", "coverage_fraction", "elevation_units")})
    )
