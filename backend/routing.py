import hashlib
import heapq
import json
from dataclasses import dataclass
from math import hypot, inf
from pathlib import Path

import numpy as np
from pyproj import CRS
from shapely.geometry import LineString, Point, shape

from backend.domain import Evidence, Terrain, Verification
from backend.spatial import ANALYSIS_CRS

CELL_M = 40
COLS, ROWS = 31, 21
TERRAIN_PENALTY = {
    Terrain.SOIL: 0.0,
    Terrain.SAND: 0.5,
    Terrain.BEDROCK: 0.1,
    Terrain.LARGE_ROCKS: 8.0,
    Terrain.ROUGH: 3.0,
    Terrain.OBSTACLES: inf,
    Terrain.UNKNOWN: 1.0,
}


@dataclass
class PathResult:
    coordinates: list[tuple[float, float]]
    distance_m: float
    cost: float
    breakdown: dict[str, float]


def astar(
    start: tuple[float, float],
    goal: tuple[float, float],
    evidence: list[Evidence],
    slope_grid: np.ndarray | None = None,
) -> PathResult:
    if slope_grid is not None and slope_grid.shape != (ROWS, COLS):
        raise ValueError("Slope grid does not match the mission grid")
    if slope_grid is not None and not np.isfinite(slope_grid).all():
        raise ValueError("Slope coverage is incomplete for required operational cells")
    if slope_grid is not None and ((slope_grid < 0).any() or (slope_grid > 90).any()):
        raise ValueError("Slope grid must contain physical slopes in degrees")
    confirmed = [
        (shape(e.spatial_footprint.model_dump()), e.observed_value)
        for e in evidence
        if e.verification_state == Verification.CONFIRMED
        and e.persistence_type == "persistent"
        and e.source_type != "orbital"
    ]

    def terms(a: tuple[int, int], b: tuple[int, int]) -> dict[str, float]:
        x, y = b[0] * CELL_M, b[1] * CELL_M
        step = LineString([(a[0] * CELL_M, a[1] * CELL_M), (x, y)])
        distance = step.length
        terrain, known = Terrain.SOIL, False
        for geom, value in confirmed:
            # Test the entire edge: no corner cutting across supported obstacle footprints.
            if value == Terrain.OBSTACLES and geom.intersects(step):
                return {"distance": inf, "terrain": 0, "slope": 0, "uncertainty": 0}
            if geom.covers(Point(x, y)):
                terrain, known = value, True
        slope = float(slope_grid[ROWS - 1 - b[1], b[0]]) if slope_grid is not None else 0.0
        # These are illustrative planning weights, never physiological safety thresholds.
        missing_slope = slope_grid is not None and not np.isfinite(slope)
        if not missing_slope and slope > 20:
            return {"distance": inf, "terrain": 0, "slope": 0, "uncertainty": 0}
        return {
            "distance": distance,
            "terrain": distance * TERRAIN_PENALTY[terrain],
            "slope": distance * slope / 10 if not missing_slope else 0.0,
            "uncertainty": distance * ((0.02 if known else 0.15) + (0.5 if missing_slope else 0)),
        }

    source = (round(start[0] / CELL_M), round(start[1] / CELL_M))
    target = (round(goal[0] / CELL_M), round(goal[1] / CELL_M))
    frontier = [(0.0, source)]
    costs = {source: 0.0}
    previous: dict[tuple[int, int], tuple[int, int]] = {}
    moves = [(1, 0), (0, 1), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    visited = set()
    while frontier:
        _, cell = heapq.heappop(frontier)
        if cell in visited:
            continue
        visited.add(cell)
        if cell == target:
            chain = [cell]
            while chain[-1] != source:
                chain.append(previous[chain[-1]])
            chain.reverse()
            breakdown = dict.fromkeys(["distance", "terrain", "slope", "uncertainty"], 0.0)
            for a, b in zip(chain, chain[1:]):
                for key, value in terms(a, b).items():
                    breakdown[key] += value
            return PathResult(
                [(x * CELL_M, y * CELL_M) for x, y in chain],
                round(breakdown["distance"], 2),
                round(costs[cell], 2),
                {k: round(v, 2) for k, v in breakdown.items()},
            )
        for dx, dy in moves:
            neighbor = (cell[0] + dx, cell[1] + dy)
            if not (0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS):
                continue
            candidate = costs[cell] + sum(terms(cell, neighbor).values())
            if candidate < costs.get(neighbor, inf):
                costs[neighbor] = candidate
                previous[neighbor] = cell
                heuristic = CELL_M * hypot(neighbor[0] - target[0], neighbor[1] - target[1])
                heapq.heappush(frontier, (candidate + heuristic, neighbor))
    return PathResult([], 0.0, 0.0, {})


def load_slope(path: str) -> np.ndarray | None:
    if not path:
        return None
    with np.load(Path(path), allow_pickle=False) as source:
        grid = source["slope_deg"].copy()
    if grid.shape != (ROWS, COLS):
        raise ValueError("Configured elevation grid has incompatible dimensions")
    if not np.isfinite(grid).all():
        raise ValueError("Configured slope coverage is incomplete for required operational cells")
    metadata_path = Path(path).with_suffix(".json")
    if not metadata_path.is_file():
        raise ValueError("Configured slope CRS provenance metadata is missing")
    metadata = json.loads(metadata_path.read_text())
    if not CRS(metadata.get("analysis_crs", "")).equals(CRS(ANALYSIS_CRS)):
        raise ValueError("Configured slope CRS does not match Mars mission analysis")
    if metadata.get("analysis_cell_m") != CELL_M:
        raise ValueError("Configured slope pixel size does not match the mission grid")
    if metadata.get("processed_sha256") != hashlib.sha256(Path(path).read_bytes()).hexdigest():
        raise ValueError("Configured slope bytes do not match provenance hash")
    finite = grid[np.isfinite(grid)]
    if len(finite) == 0 or (finite < 0).any() or (finite > 90).any():
        raise ValueError("Slope grid must contain physical slopes in degrees")
    return grid
