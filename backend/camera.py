"""PDS camera provenance and exact PLACES validity, without invented footprints."""

import hashlib
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from itertools import combinations
from math import hypot, isfinite
from pathlib import Path
from typing import Any

from backend.spatial import to_local


def _tag(element: ET.Element) -> str:
    return element.tag.split('}')[-1]


def _one(element: ET.Element, name: str) -> str:
    values = {e.text.strip() for e in element.iter() if _tag(e) == name and e.text}
    if len(values) != 1:
        raise ValueError(f'Missing or conflicting PDS {name}')
    return values.pop()


def parse_label(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:
        raise ValueError('External XML entities are unsupported')
    try:
        root = ET.fromstring(raw)
        lid = _one(root, 'logical_identifier')
        if '_calibrated:' not in lid:
            raise ValueError('Expected official calibrated collection identifier')
        mission = next(e for e in root.iter() if _tag(e) == 'Mission_Information')
        start = Decimal(_one(mission, 'spacecraft_clock_start'))
        stop = Decimal(_one(mission, 'spacecraft_clock_stop'))
        mini_headers = [e for e in root.iter() if _tag(e) == 'MSSS_Camera_Mini_Header']
        mini_clock = _one(mini_headers[0], 'spacecraft_clock_start') if mini_headers else None
        if not start.is_finite() or not stop.is_finite() or start < 0 or stop < start:
            raise ValueError('Invalid clock interval')
        counters = [e for e in root.iter() if _tag(e) == 'Motion_Counter']
        mappings = [
            {_one(e, 'index_id'): int(_one(e, 'index_value_number'))
             for e in counter if _tag(e) == 'Motion_Counter_Index'}
            for counter in counters
        ]
        if not mappings or any(m != mappings[0] for m in mappings):
            raise ValueError('Missing or conflicting RMC')
        if not {'SITE', 'DRIVE', 'POSE', 'RSM'} <= mappings[0].keys():
            raise ValueError('Incomplete rover motion counter')
        if min(mappings[0].values()) < 0:
            raise ValueError('Image RMC cannot contain PLACES wildcards')
        arrays = [e for e in root.iter() if _tag(e) in ('Array_3D_Image', 'Array_2D_Image')]
        if len(arrays) != 1:
            raise ValueError('Expected one science image array')
        array = arrays[0]
        dimensions = {_one(e, 'axis_name'): int(_one(e, 'elements'))
                      for e in array if _tag(e) == 'Axis_Array'}
        axes = sorted([e for e in array if _tag(e) == 'Axis_Array'],
                      key=lambda e: int(_one(e, 'sequence_number')))
        if not {'Line', 'Sample'} <= dimensions.keys() or min(dimensions.values()) <= 0:
            raise ValueError('Invalid image dimensions')
        camera = next(e for e in root.iter() if _tag(e) == 'Camera_Model_Parameters')
        components = [e for e in root.iter() if _tag(e) == 'Observing_System_Component'
                      and any(_tag(c) == 'type' and c.text == 'Instrument' for c in e)]
        instrument = [_one(e, 'name') for e in components]
        return {
            'product_id': lid, 'version_id': _one(root, 'version_id'),
            'instrument': instrument, 'sclk': str(start), 'sclk_stop': str(stop),
            'clock_partition': int(_one(root, 'spacecraft_clock_partition')),
            'mini_header_sclk': mini_clock,
            'places_observation_sclk': mini_clock or str(start),
            'utc_start': _one(root, 'start_date_time'),
            'sol': int(_one(root, 'start_sol_number')), 'rmc': mappings[0],
            'processing_level': _one(root, 'processing_level'),
            'dimensions': dimensions, 'file_name': _one(root, 'file_name'),
            'axis_order': [_one(e, 'axis_name') for e in axes],
            'array_offset': int(_one(array, 'offset')),
            'array_type': _one(array, 'data_type'),
            'scaling_factor': next((e.text for e in array.iter()
                                    if _tag(e) == 'scaling_factor'), '1'),
            'value_offset': next((e.text for e in array.iter()
                                  if _tag(e) == 'value_offset'), '0'),
            'axis_index_order': _one(array, 'axis_index_order'),
            'camera_model': {'model_type': _one(camera, 'model_type'),
                             'xml': ET.tostring(camera, encoding='unicode')},
            'label_sha256': hashlib.sha256(raw).hexdigest(),
            'classification': 'DERIVED', 'footprint': None, 'spatial_uncertainty_m': None,
            'limitations': ['Camera distortion, depth and pose uncertainty are not validated; '
                            'rover location is not an image footprint.'],
        }
    except (ET.ParseError, InvalidOperation, StopIteration, KeyError) as exc:
        raise ValueError('Invalid calibrated PDS camera metadata') from exc


def exact_clock_join(
    rmc: dict[str, int], start: Decimal, stop: Decimal, rows: list[dict[str, str]],
) -> dict[str, str] | None:
    """Require full exposure inside one exact interval with matching known RMC.

    Approximate intervals and overlapping candidates never authorize a pose join.
    Wildcards remain unknown; they cannot validate a requested component.
    """
    if not start.is_finite() or not stop.is_finite() or stop < start:
        raise ValueError('Invalid image clock')
    if any(value < 0 for value in rmc.values()):
        return None
    matches = []
    for row in rows:
        if row.get('frame') != 'ROVER':
            continue
        if any(row.get(key.lower()) != str(value) for key, value in rmc.items()):
            continue
        try:
            lo, hi = Decimal(row['min_sclk']), Decimal(row['max_sclk'])
        except (InvalidOperation, KeyError):
            continue
        if lo.is_finite() and hi.is_finite() and lo <= start <= stop <= hi:
            matches.append(row)
    return matches[0] if len(matches) == 1 else None


def drive_anchor_context(product: dict[str, Any]) -> dict[str, Any]:
    """Validate a cached PLACES drive anchor, never infer a camera ground footprint."""
    unavailable: dict[str, Any] = {
        "status": "UNAVAILABLE", "anchor_local_m": None,
        "ground_footprint_available": False, "spatial_uncertainty_m": None,
        "reason": "No consistent PLACES drive anchor for the calibrated product.",
    }
    try:
        anchor = product["drive_anchor"]
        interval = product["places_exact_interval"]
        rmc = product["rmc"]
        if not anchor or not interval or product["clock_partition"] != 1:
            return unavailable
        if exact_clock_join(
            rmc, Decimal(product["sclk"]), Decimal(product["sclk_stop"]), [interval]
        ) is None:
            return unavailable
        if anchor["frame"] != "ROVER" or any(
            anchor[key.lower()] != str(rmc[key]) for key in ("SITE", "DRIVE")
        ):
            return unavailable
        lon, lat = float(anchor["longitude"]), float(anchor["planetocentric_latitude"])
        if not (isfinite(lon) and isfinite(lat) and 0 <= lon <= 360 and -90 <= lat <= 90):
            return unavailable
        x, y = to_local(lon, lat)
        cached_x, cached_y = product["rover_local_m"]
        if not all(isfinite(v) for v in (cached_x, cached_y, x, y)):
            return unavailable
        if hypot(x - cached_x, y - cached_y) > 0.05:
            return unavailable
        return {
            "status": "DRIVE_ANCHOR_ONLY", "anchor_local_m": [x, y],
            "ground_footprint_available": False, "spatial_uncertainty_m": None,
            "reason": "Best-tactical site/drive position; exact image pose and depth unvalidated.",
        }
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return unavailable


def camera_anchor_consistency(products: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare relative local offsets to archived easting/northing differences.

    This checks coordinate arithmetic only, not absolute geolocation accuracy.
    """
    anchors = []
    for product in products:
        context = drive_anchor_context(product)
        if context["status"] != "DRIVE_ANCHOR_ONLY":
            continue
        try:
            record = product["drive_anchor"]
            east, north = float(record["easting"]), float(record["northing"])
            if isfinite(east) and isfinite(north):
                anchors.append((context["anchor_local_m"], east, north))
        except (KeyError, ValueError, TypeError):
            continue
    residuals = [
        hypot((b[0][0] - a[0][0]) - (b[1] - a[1]),
              (b[0][1] - a[0][1]) - (b[2] - a[2]))
        for a, b in combinations(anchors, 2)
    ]
    return {"anchor_count": len(anchors),
            "max_relative_residual_m": max(residuals) if residuals else None}
