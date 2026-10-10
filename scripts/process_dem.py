"""Align a LOCAL Mars elevation product to the mission grid. Never download whole archives."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject

from backend.routing import CELL_M, COLS, ROWS
from backend.spatial import ANALYSIS_CRS


def process(source: Path, output: Path, product_id: str, source_url: str) -> dict[str, object]:
    if not product_id or not source_url.startswith("https://"):
        raise ValueError("A product identifier and HTTPS provenance URL are required")
    elevation = np.full((ROWS, COLS), np.nan, dtype="float32")
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    # Grid row zero is north; each pixel center coincides with an A* node.
    transform = from_origin(-CELL_M / 2, 800 + CELL_M / 2, CELL_M, CELL_M)
    with rasterio.open(source) as dataset:
        if dataset.crs is None:
            raise ValueError("Missing Mars CRS; inspect the PDS label before assigning it")
        radius = CRS(dataset.crs).ellipsoid.semi_major_metre
        if not 3_300_000 < radius < 3_500_000:
            raise ValueError("Expected Mars coordinates, refusing Earth or unknown body")
        if dataset.count != 1:
            raise ValueError("Use a single-band elevation raster in meters, not a browse image")
        reproject(
            source=rasterio.band(dataset, 1),
            destination=elevation,
            src_transform=dataset.transform,
            src_crs=dataset.crs,
            src_nodata=dataset.nodata,
            dst_transform=transform,
            dst_crs=ANALYSIS_CRS,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        metadata = {
            "product_id": product_id,
            "source_url": source_url,
            "source_crs": dataset.crs.to_wkt(),
            "analysis_crs": ANALYSIS_CRS,
            "source_resolution": list(dataset.res),
            "analysis_cell_m": CELL_M,
            "elevation_units": "m (operator must verify PDS units before import)",
            "coverage_fraction": float(np.isfinite(elevation).mean()),
            "sha256": digest,
            "limitations": "Resampling cannot improve source resolution. MOLA is regional context.",
        }
    if metadata["coverage_fraction"] == 0:
        raise ValueError("Product has no valid elevation in the mission area")
    if metadata["coverage_fraction"] != 1:
        raise ValueError("Incomplete elevation coverage in required operational cells")
    dy, dx = np.gradient(elevation, CELL_M)
    slope = np.degrees(np.arctan(np.hypot(dx, dy))).astype("float32")
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, elevation_m=elevation, slope_deg=slope)
    metadata["processed_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()
    print(json.dumps(process(args.source, args.output, args.product_id, args.source_url), indent=2))


if __name__ == "__main__":
    main()
