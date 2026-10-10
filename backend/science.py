"""Optional orbital science provenance; never terrain or human verification."""

import hashlib
import json
from pathlib import Path
from typing import Any

import rasterio
from pyproj import Transformer

from backend.config import ROOT
from backend.spatial import to_mars


def crism_context(
    location: tuple[float, float], metadata_path: Path | None = None,
) -> dict[str, Any] | None:
    path = metadata_path or ROOT / 'data/processed/crism.json'
    if not path.exists():
        return None
    metadata = json.loads(path.read_text())
    raster = ROOT / metadata['processed_file']
    if not raster.is_file():
        return None
    if hashlib.sha256(raster.read_bytes()).hexdigest() != metadata['processed_sha256']:
        raise ValueError('CRISM processed cache hash mismatch')
    lon, lat = to_mars(*location)
    with rasterio.open(raster) as source:
        converter = Transformer.from_crs(source.crs.geodetic_crs, source.crs, always_xy=True)
        row, col = source.index(*converter.transform(lon, lat))
        inside = 0 <= row < source.height and 0 <= col < source.width
        values = source.read(window=((row, row+1), (col, col+1)))[:, 0, 0] if inside else None
    valid = bool(values is not None and values[3] > 0)
    metadata['target'] = {
        'local_m': list(location), 'longitude': lon, 'planetocentric_latitude': lat,
        'source_pixel': [col, row], 'valid_pixel': valid,
        'display_rgb': values[:3].tolist() if valid and values is not None else None,
        'classification': 'INTERPRETIVE / illustrative mission waypoint',
        'mineral_identity': None,
    }
    return metadata
