"""Offline alignment diagnostic; coordinates are Mars metric mission nodes."""

import json

import numpy as np
from PIL import Image, ImageDraw

from backend.config import ROOT
from backend.routing import CELL_M, astar, load_slope
from backend.spatial import to_mars


def main() -> None:
    path = ROOT / "data/processed/hirise-covering-slope.npz"
    slope = load_slope(str(path))
    assert slope is not None
    with np.load(path, allow_pickle=False) as data:
        elevation = data["elevation_m"]
    route = astar((120, 400), (1080, 400), [], slope)
    canvas = Image.new("RGB", (1000, 430), "#111827")
    draw = ImageDraw.Draw(canvas)
    for panel, (grid, label) in enumerate(
        [(elevation, "NASA stereo DTM samples (DERIVED, m)"), (slope, "Derived slope (degrees)")]
    ):
        low, high = float(grid.min()), float(grid.max())
        scaled = (grid - low) / max(high - low, 1e-9)
        rgb = np.stack(
            [scaled * 220 + 20, (1 - scaled) * 150 + 30, np.full_like(grid, 100)], axis=-1
        ).astype("uint8")
        canvas.paste(
            Image.fromarray(rgb).resize((465, 315), Image.Resampling.NEAREST),
            (20 + panel * 500, 60),
        )
        draw.text((20 + panel * 500, 15), label, fill="white")
        draw.text(
            (20 + panel * 500, 35), f"Range {low:.3f} to {high:.3f}; 40 m nodes", fill="white"
        )
        points = [
            (20 + panel * 500 + (x / CELL_M + 0.5) * 15, 60 + (20 - y / CELL_M + 0.5) * 15)
            for x, y in route.coordinates
        ]
        draw.line(points, fill="white", width=3)
    draw.text(
        (20, 395),
        "White: prototype route. Coarse slope; no EVA safety certification.",
        fill="white",
    )
    output = ROOT / "docs/science"
    output.mkdir(parents=True, exist_ok=True)
    canvas.save(output / "s1-dtm-alignment.png")
    (output / "s1-route.geojson").write_text(
        json.dumps(
            {
                "type": "Feature",
                "properties": {
                    "classification": "MODELED",
                    "analysis_coordinates_m": route.coordinates,
                    "cost": route.breakdown,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [to_mars(x, y) for x, y in route.coordinates],
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
