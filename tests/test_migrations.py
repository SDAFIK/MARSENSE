import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.domain import Evidence, MissionAssumption, Route, RouteSegment
from backend.main import create_app
from backend.store import Store, all_of, get, put


def test_legacy_shared_segments_migrate_without_losing_decisions(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    settings = Settings(database_url=f"sqlite:///{path}")
    with TestClient(create_app(settings)) as client:
        evidence = client.post("/api/observations/demo", json={"scenario": "obstacles"}).json()
        client.post(
            f"/api/evidence/{evidence['id']}/verify",
            json={"decision": "REJECTED", "reviewer": "Astronaut", "note": "Keep this history"},
        ).raise_for_status()
        with client.app.state.store.session(write=True) as session:
            original_evidence = [e.model_dump(mode="json") for e in all_of(session, Evidence)]
            for route in all_of(session, Route):
                route.segment_ids = ["alpha-segment-3"]
                put(session, route)
            put(
                session,
                RouteSegment(
                    id="alpha-segment-3",
                    route_id="eva-01-alpha",
                    coordinates=[(440, 400), (760, 400)],
                    assumption_ids=["assumption-corridor"],
                ),
            )
            assumption = get(session, MissionAssumption, "assumption-corridor")
            assumption.dependent_route_segments = ["alpha-segment-3"]
            put(session, assumption)
    # Old databases had only the entities table, with no schema-version metadata.
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE IF EXISTS schema_version")
    for _ in range(2):
        with TestClient(create_app(settings)) as client:
            with client.app.state.store.session() as session:
                assert [
                    e.model_dump(mode="json") for e in all_of(session, Evidence)
                ] == original_evidence
                segments = {s.id: s for s in all_of(session, RouteSegment)}
                for route in all_of(session, Route):
                    assert all(segments[s].route_id == route.id for s in route.segment_ids)
                    assert route.segment_ids == [f"{route.id}-segment-{i}" for i in (1, 3, 4)]
                assert "alpha-segment-3" in segments  # historical reference is retained
                assumption = get(session, MissionAssumption, "assumption-corridor")
                assert {"eva-01-alpha-segment-3", "eva-02-alpha-segment-3"} <= set(
                    assumption.dependent_route_segments
                )
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone() == (2,)


def test_newer_database_schema_is_refused_without_mutation(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)")
        connection.execute("INSERT INTO schema_version VALUES (1, 999)")
    with pytest.raises(ValueError, match="newer"):
        Store(f"sqlite:///{path}")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone() == (999,)


def test_migration_failure_rolls_back_payload_and_version(tmp_path: Path, monkeypatch) -> None:
    from backend import migrations

    path = tmp_path / "rollback.db"
    with TestClient(create_app(Settings(database_url=f"sqlite:///{path}"))):
        pass
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE schema_version")
        original = connection.execute(
            "SELECT id, kind, payload FROM entities ORDER BY id"
        ).fetchall()

    def fail(session):
        route = all_of(session, Route)[0]
        route.name = "must roll back"
        put(session, route)
        raise RuntimeError("injected migration failure")

    monkeypatch.setattr(migrations, "migrate_legacy_segments", fail)
    with pytest.raises(RuntimeError, match="injected"):
        Store(f"sqlite:///{path}")
    with sqlite3.connect(path) as connection:
        assert (
            connection.execute("SELECT id, kind, payload FROM entities ORDER BY id").fetchall()
            == original
        )
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name='schema_version'"
        ).fetchall()
