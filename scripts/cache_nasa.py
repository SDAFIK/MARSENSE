"""Cache a bounded NASA WMTS crop, preserving exact source bytes, hashes, and metadata."""

import argparse
import hashlib
import io
import json
import math
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import ROOT
from backend.spatial import ANALYSIS_CRS, MARS_RADIUS_M, ORIGIN_LAT, to_mars

NS = {"w": "http://www.opengis.net/wmts/1.0", "o": "http://www.opengis.net/ows/1.1"}
GROUND_URL = "https://d2pn8kiwq2w21t.cloudfront.net/original_images/PIA26072.jpg"


def fetch(url: str, path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    request = urllib.request.Request(
        url, headers={"User-Agent": "MARSENSE educational data cache/1.0"}
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise ValueError("Refusing asset above 10 MB")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def cache(layer: str, name: str, zoom: int) -> dict[str, object]:
    endpoint = f"https://trek.nasa.gov/tiles/Mars/EQ/{layer}/1.0.0"
    xml_path = ROOT / f"data/nasa/{name}-capabilities.xml"
    xml = ET.fromstring(fetch(f"{endpoint}/WMTSCapabilities.xml", xml_path))
    matrix = next(
        m
        for m in xml.findall(".//w:TileMatrixSet/w:TileMatrix", NS)
        if m.findtext("o:Identifier", namespaces=NS) == str(zoom)
    )
    width = int(float(matrix.findtext("w:MatrixWidth", namespaces=NS) or "0"))
    height = int(float(matrix.findtext("w:MatrixHeight", namespaces=NS) or "0"))
    if width != 2 ** (zoom + 1) or height != 2**zoom:
        raise ValueError("Unsupported WMTS layout; inspect product metadata")
    west, south = to_mars(0, 0)
    east, north = to_mars(1200, 800)
    left, right = (west + 180) / 360 * width * 256, (east + 180) / 360 * width * 256
    top, bottom = (90 - north) / 180 * height * 256, (90 - south) / 180 * height * 256
    col0, col1, row0, row1 = (
        math.floor(left / 256),
        math.floor(right / 256),
        math.floor(top / 256),
        math.floor(bottom / 256),
    )
    tile_count = (col1 - col0 + 1) * (row1 - row0 + 1)
    if tile_count > 16:
        raise ValueError("Refusing more than 16 tiles; lower zoom")
    canvas = Image.new("RGBA", ((col1 - col0 + 1) * 256, (row1 - row0 + 1) * 256))
    tiles = []
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            url = f"{endpoint}/default/default028mm/{zoom}/{row}/{col}.png"
            path = ROOT / f"data/nasa/tiles/{name}-{zoom}-{row}-{col}.png"
            content = fetch(url, path)
            with Image.open(io.BytesIO(content)) as image:
                canvas.paste(image.convert("RGBA"), ((col - col0) * 256, (row - row0) * 256))
            tiles.append(
                {
                    "url": url,
                    "file": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    box = (
        round(left - col0 * 256),
        round(top - row0 * 256),
        round(right - col0 * 256),
        round(bottom - row0 * 256),
    )
    crop = canvas.crop(box)
    if crop.getchannel("A").getextrema()[1] == 0:
        raise ValueError("Product has no coverage of selected operational area")
    output = ROOT / f"data/nasa/jezero-{name}.png"
    crop.save(output)
    # Pixel rounding changes the geographic extent. Render those actual edges.
    actual_west = (col0 * 256 + box[0]) / (width * 256) * 360 - 180
    actual_east = (col0 * 256 + box[2]) / (width * 256) * 360 - 180
    actual_north = 90 - (row0 * 256 + box[1]) / (height * 256) * 180
    actual_south = 90 - (row0 * 256 + box[3]) / (height * 256) * 180
    longitude_pixel = math.radians(360 / (width * 256))
    latitude_pixel = math.radians(180 / (height * 256))
    return {
        "layer": layer,
        "requested_bounds_lon_lat": [west, south, east, north],
        "bounds_lon_lat": [actual_west, actual_south, actual_east, actual_north],
        "render_corners": [
            [actual_west, actual_north],
            [actual_east, actual_north],
            [actual_east, actual_south],
            [actual_west, actual_south],
        ],
        "effective_pixel_m": [
            MARS_RADIUS_M * longitude_pixel * math.cos(math.radians(ORIGIN_LAT)),
            MARS_RADIUS_M * latitude_pixel,
        ],
        "processing": "WMTS mosaic cropped to nearest pixel edges; "
        "native resolution retained in source layer ID",
        "analysis_crs": ANALYSIS_CRS,
        "local_origin_offset_m": [0, 3396190 * math.radians(18.44)],
        "source_crs": "IAU2000 Mars equirectangular / sphere 3396190 m",
        "capabilities": xml_path.relative_to(ROOT).as_posix(),
        "tiles": tiles,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "pixel_size": list(crop.size),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hirise-layer", default="")
    parser.add_argument("--hirise-zoom", type=int, default=15)
    args = parser.parse_args()
    path = ROOT / "data/processed/manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {}
    manifest["ctx"] = cache(
        "JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0", "ctx-controlled", 12
    )
    (ROOT / "data/nasa/jezero-ctx.png").write_bytes(
        (ROOT / "data/nasa/jezero-ctx-controlled.png").read_bytes()
    )
    if args.hirise_layer:
        manifest["hirise"] = cache(args.hirise_layer, "hirise", args.hirise_zoom)
    raw_ground = ROOT / "data/nasa/PIA26072.jpg"
    content = fetch(GROUND_URL, raw_ground)
    with Image.open(io.BytesIO(content)) as image:
        image.thumbnail((1600, 1000))
        image.convert("RGB").save(ROOT / "data/nasa/ground-navcam.jpg", quality=90)
    manifest["ground"] = {
        "source_url": GROUND_URL,
        "source_page": "https://www.jpl.nasa.gov/images/pia26072-perseverance-makes-tracks-in-boulder-field/",
        "product": "PIA26072",
        "instrument": "Perseverance Navcam",
        "sol": 866,
        "acquired": "2023-07-28",
        "credit": "NASA/JPL-Caltech",
        "sha256": hashlib.sha256(content).hexdigest(),
        "processing": "Public-release mosaic JPEG, resized only; not a calibrated PDS product",
        "registration": "Simulated local footprint; NOT the image's actual PLACES location",
    }
    manifest["cached_at"] = datetime.now(UTC).isoformat()
    manifest["mission_geometry"] = (
        "Illustrative habitat, target, soil assumptions and footprint; "
        "not NASA mission planning data"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))
    print(f"NASA cache ready: {path}")


if __name__ == "__main__":
    main()
