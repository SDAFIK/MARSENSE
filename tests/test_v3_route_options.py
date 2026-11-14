from fastapi.testclient import TestClient
from shapely.geometry import LineString, shape


def test_options_are_distinct_read_only_and_avoid_confirmed_obstacle(client: TestClient) -> None:
    evidence = client.post("/api/observations/demo", json={"scenario": "obstacles"}).json()
    result = client.post(f"/api/evidence/{evidence['id']}/verify", json={
        "decision": "CONFIRMED", "reviewer": "Research reviewer",
        "note": "Verified supported obstacle footprint.",
    })
    assert result.status_code == 200
    before = client.get("/api/missions/eva-01").json()
    response = client.get("/api/missions/eva-01/alternatives")
    assert response.status_code == 200
    options = response.json()["options"]
    assert 2 <= len(options) <= 3
    assert len({tuple(map(tuple, p["coordinates"])) for p in options}) == len(options)
    for option in options:
        assert not shape(evidence["spatial_footprint"]).intersects(
            LineString(option["coordinates"])
        )
    assert client.get("/api/missions/eva-01").json() == before
    assert before["route_segments"]
