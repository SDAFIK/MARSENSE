"""Bounded, reproducible NASA PDS elevation and localization samples for Jezero.

Range requests must be honored: never silently download a 411 MB DTM.
The sampled DTM covers only part of the extent. No missing ground is invented.
"""

import csv
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from backend.config import ROOT
from backend.spatial import ANALYSIS_CRS, to_local, to_mars
from scripts.cache_nasa import fetch
from scripts.process_dem import process

DTM = (
    "https://hirise.lpl.arizona.edu/PDS/DTM/ESP/ORB_048800_048899/"
    "ESP_048842_1985_ESP_048908_1985/DTEEC_048842_1985_048908_1985_U01.IMG"
)
MOLA = (
    "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/"
    "mgsl_300x/meg128/megt44n000hb.img"
)
PLACES = (
    "https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-"
    "mars2020_rover_places/data_localizations/best_tactical.csv"
)


def range_bytes(url: str, start: int, length: int, name: str) -> tuple[bytes, dict[str, object]]:
    path = ROOT / "data/nasa/ranges" / f"{name}-{start}-{length}.bin"
    if path.exists():
        content = path.read_bytes()
    else:
        request = urllib.request.Request(
            url, headers={"Range": f"bytes={start}-{start + length - 1}"}
        )
        with urllib.request.urlopen(request, timeout=40) as response:
            if response.status != 206 or not response.headers.get("Content-Range", "").startswith(
                f"bytes {start}-{start + length - 1}/"
            ):
                raise ValueError("Server refused precise range; refusing large archive download")
            content = response.read(length + 1)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    if len(content) != length:
        raise ValueError("Truncated or oversized PDS range")
    return content, {
        "url": url,
        "offset": start,
        "length": length,
        "file": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def write_raster(path: Path, grid: np.ndarray, crs: str, transform: object) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=grid.shape[0],
        width=grid.shape[1],
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=np.nan,
    ) as dst:
        dst.write(grid.astype("float32"), 1)


def cache_dtm() -> dict[str, object]:
    label, header = range_bytes(DTM, 0, 27820, "hirise-dtm")
    # Constants verified against the attached PDS label; fail if product changes.
    text = label.decode("ascii", errors="ignore")
    for token in ["DTEEC_048842_1985_048908_1985_U01", "PC_REAL", "14775", "6955"]:
        if token not in text:
            raise ValueError("Unexpected DTM label; inspect metadata before processing")
    radius, scale = 3394839.8133163, 1.0096633268711
    grid = np.full((21, 31), np.nan, dtype="float32")
    ranges = [header]
    for local_row, y in enumerate(range(800, -1, -40)):
        positions = []
        for local_col, x in enumerate(range(0, 1201, 40)):
            lon, lat = to_mars(x, y)
            projected_x = radius * math.cos(math.radians(15)) * math.radians(lon - 77.52)
            projected_y = radius * math.radians(lat)
            col = round(projected_x / scale + 3318.5000000001 - 0.5)
            row = round(1090855.5 - 0.5 - projected_y / scale)
            if 0 <= col < 6955 and 0 <= row < 14775:
                positions.append((local_col, col, row))
        if not positions:
            continue
        source_row = positions[0][2]
        if any(p[2] != source_row for p in positions):
            raise ValueError("Unexpected row variation")
        left, right = min(p[1] for p in positions), max(p[1] for p in positions)
        content, metadata = range_bytes(
            DTM, 27820 * (source_row + 1) + left * 4, (right - left + 1) * 4, "hirise-dtm"
        )
        ranges.append(metadata)
        values = np.frombuffer(content, dtype="<f4")
        for local_col, col, _ in positions:
            value = float(values[col - left])
            if -2655 <= value <= -2468.73:
                grid[local_row, local_col] = value
    source = ROOT / "data/processed/hirise-elevation-sampled40m.tif"
    write_raster(source, grid, ANALYSIS_CRS, from_origin(-20, 820, 40, 40))
    metadata = {
        "product_id": "DTEEC_048842_1985_048908_1985_U01",
        "source_url": DTM,
        "coverage_fraction": float(np.isfinite(grid).mean()),
    }
    if np.isfinite(grid).any():
        metadata.update(
            process(
                source,
                ROOT / "data/processed/hirise-slope.npz",
                "DTEEC_048842_1985_048908_1985_U01",
                DTM,
            )
        )
    metadata.update(
        {
            "ranges": ranges,
            "native_scale_m": scale,
            "processing": "Nearest native elevation samples every 40 m, slope at 40 m",
            "file": source.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "limitations": "No valid sampled coverage; no slope enabled."
            if not np.isfinite(grid).any()
            else "Partial coverage; holes retained. Not foot-scale hazards.",
        }
    )
    return metadata


def cache_mola() -> dict[str, object]:
    label = fetch(MOLA.replace(".img", ".lbl"), ROOT / "data/nasa/mola.lbl")
    if b"MSB_INTEGER" not in label or b"11520" not in label:
        raise ValueError("Unexpected MOLA label")
    # A small regional neighborhood (about 4 km), preserving native 1/128-degree pixels.
    col0, row0 = int(77.45 * 128) - 3, int((44 - 18.46) * 128) - 3
    grid = np.empty((9, 9), dtype="float32")
    ranges = []
    for i in range(9):
        content, metadata = range_bytes(MOLA, ((row0 + i) * 11520 + col0) * 2, 18, "mola")
        grid[i] = np.frombuffer(content, dtype=">i2")
        ranges.append(metadata)
    radius = 3396000.0
    pixel = radius * math.radians(1 / 128)
    transform = from_origin(
        radius * math.radians(col0 / 128 - 180),
        radius * math.radians(44 - row0 / 128),
        pixel,
        pixel,
    )
    source = ROOT / "data/processed/mola-context.tif"
    crs = "+proj=eqc +lat_ts=0 +lon_0=180 +R=3396000 +units=m +no_defs"
    write_raster(source, grid, crs, transform)
    return {
        "product_id": "MEGT44N000HB.IMG",
        "source_url": MOLA,
        "source_crs": crs,
        "native_pixel_m": pixel,
        "ranges": ranges,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "file": source.relative_to(ROOT).as_posix(),
        "limitations": "Regional median topography; interpolated bins; no local hazard claim.",
    }


def cache_places() -> dict[str, object]:
    content = fetch(PLACES, ROOT / "data/nasa/places-best-tactical.csv")
    fetch(PLACES + ".xml", ROOT / "data/nasa/places-best-tactical.csv.xml")
    features = []
    for row in csv.DictReader(io.StringIO(content.decode())):
        lon, lat = float(row["longitude"]), float(row["planetocentric_latitude"])
        x, y = to_local(lon, lat)
        if row["frame"] == "ROVER" and 0 <= x <= 1200 and 0 <= y <= 800:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [x, y]},
                    "properties": {
                        "sol": int(row["sol"]),
                        "site": row["site"],
                        "drive": row["drive"],
                        "sclk": row["sclk"],
                    },
                }
            )
    output = ROOT / "data/processed/places-rover-local.geojson"
    output.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return {
        "source_url": PLACES,
        "sha256": hashlib.sha256(content).hexdigest(),
        "selected_poses": len(features),
        "file": output.relative_to(ROOT).as_posix(),
        "coordinate_note": "Planetocentric lat / east lon converted to local Mars meters",
        "limitations": "Rover poses alone do not establish image footprint or instrument pointing.",
    }


if __name__ == "__main__":
    path = ROOT / "data/processed/manifest.json"
    manifest = json.loads(path.read_text())
    for key, cache in [("dtm", cache_dtm), ("mola", cache_mola), ("places", cache_places)]:
        manifest[key] = cache()
        path.write_text(json.dumps(manifest, indent=2))
        print(f"Cached {key}")
