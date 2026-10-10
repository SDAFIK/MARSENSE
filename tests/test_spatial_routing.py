from math import isclose, pi

import pytest
from pydantic import ValidationError
from shapely.geometry import Point, shape

from backend.comparison import expected_at
from backend.domain import Evidence, Footprint, Terrain, rectangle
from backend.routing import astar
from backend.spatial import MARS_RADIUS_M, to_local, to_mars


def test_mars_coordinates_roundtrip_and_known_distance() -> None:
    for point in [(0, 0), (1200, 800), (300, -50)]:
        transformed = to_local(*to_mars(*point))
        assert isclose(point[0], transformed[0], abs_tol=1e-7)
        assert isclose(point[1], transformed[1], abs_tol=1e-7)
    assert isclose(to_local(77.45, 19.44)[1], MARS_RADIUS_M * pi / 180, rel_tol=1e-10)
    assert 59000 < to_local(77.45, 19.44)[1] < 60000


def test_deterministic_shortest_route_cost() -> None:
    first = astar((120, 400), (1080, 400), [])
    assert first == astar((120, 400), (1080, 400), [])
    assert first.distance_m == 960
    assert first.breakdown == {"distance": 960, "terrain": 0, "slope": 0, "uncertainty": 144}
    assert first.cost == 1104


def test_invalid_footprints() -> None:
    with pytest.raises(ValidationError):
        rectangle(-10, 0, 30, 40)
    with pytest.raises(ValidationError):
        Footprint(coordinates=[[(0, 0), (10, 10), (0, 10), (10, 0), (0, 0)]])


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_footprints_are_rejected(invalid: float) -> None:
    with pytest.raises(ValidationError):
        rectangle(invalid, 0, 30, 40)


def test_mars_transform_matches_independent_proj_engine() -> None:
    from pyproj import CRS, Transformer

    from backend.spatial import ANALYSIS_CRS

    geographic = CRS.from_proj4("+proj=longlat +R=3396190 +no_defs")
    transform = Transformer.from_crs(geographic, ANALYSIS_CRS, always_xy=True)
    for lon, lat in [(77.45, 18.44), (77.47, 18.45), (77.43, 18.46)]:
        assert transform.transform(lon, lat) == pytest.approx(to_local(lon, lat), abs=1e-7)


def test_supported_footprint_does_not_generalize(client) -> None:
    e = client.post("/api/observations/demo", json={"scenario": "obstacles"}).json()
    client.post(
        f"/api/evidence/{e['id']}/verify",
        json={
            "decision": "CONFIRMED",
            "reviewer": "Astronaut",
            "note": "Confirmed within footprint",
        },
    )
    evidence = [
        Evidence.model_validate(item)
        for item in client.get("/api/missions/eva-01").json()["evidence"]
    ]
    assert expected_at(Terrain.SOIL, rectangle(450, 600, 500, 650), evidence)[0] == Terrain.SOIL
    assert (
        expected_at(Terrain.SOIL, rectangle(540, 340, 560, 360), evidence)[0] == Terrain.OBSTACLES
    )
    beta = client.get("/api/missions/eva-01").json()["routes"][-1]
    assert all(not shape(e["spatial_footprint"]).covers(Point(p)) for p in beta["coordinates"])
