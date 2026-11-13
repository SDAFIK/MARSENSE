"""Tests use disposable local SQLite and a dedicated local PostgreSQL service only."""

import io
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from backend.auth import password_hash
from backend.config import Settings
from backend.main import create_app
from scripts.migrate_cloud import read_runtime, read_users, sync_snapshot

ORIGIN = "https://marsense.test"
HEADERS = {"Origin": ORIGIN}
OPERATOR = {"username": "controller", "password": "private-fixture-operator-password"}
EXPLORER = {"username": "explorer-one", "password": "private-fixture-explorer-password"}


def make_source(tmp_path: Path) -> tuple[Path, Path, dict, dict, bytes]:
    runtime = tmp_path / "runtime"
    users = tmp_path / "users.json"
    users.write_text(json.dumps([{
        "id": "operator", "username": OPERATOR["username"], "name": "Fixture operator",
        "role": "ADMIN", "password_hash": password_hash(OPERATOR["password"]),
    }]))
    cfg = Settings(
        environment="production", database_url=f"sqlite:///{runtime / 'marsense.db'}",
        runtime_dir=runtime, auth_users_file=str(users), cors_origins=[ORIGIN],
    )
    picture = io.BytesIO()
    Image.new("RGB", (64, 64), (180, 90, 40)).save(picture, format="JPEG")
    image = picture.getvalue()
    footprint = json.dumps({
        "type": "Polygon",
        "coordinates": [[[520, 320], [680, 320], [680, 480], [520, 480], [520, 320]]],
    })
    with TestClient(create_app(cfg), base_url=ORIGIN) as client:
        assert client.post("/api/auth/login", json=OPERATOR, headers=HEADERS).status_code == 200
        mission = client.get("/api/missions/eva-01").json()
        assert client.post("/api/auth/logout", headers=HEADERS).status_code == 200
        assert client.post("/api/workspaces/auth/signup", json={
            **EXPLORER, "name": "Fixture explorer",
        }, headers=HEADERS).status_code == 201
        upload = client.post("/api/workspaces/data/observations/upload", headers=HEADERS, files={
            "file": ("fixture.jpg", image, "image/jpeg"),
        }, data={"footprint": footprint, "mission_id": "eva-01"})
        assert upload.status_code == 200, upload.text
        evidence = upload.json()
        verified = client.post(
            f"/api/workspaces/data/evidence/{evidence['id']}/verify", headers=HEADERS,
            json={"decision": "CONFIRMED", "reviewer": "untrusted",
                  "human_terrain": "obstacle-rich terrain", "note": "Fixture field assessment"},
        )
        assert verified.status_code == 200, verified.text
        saved = client.get("/api/workspaces/data/missions/eva-01").json()
        assert saved["mission"]["active_route_id"] != mission["mission"]["active_route_id"]
        observation = client.get(
            f"/api/workspaces/data/observations/{evidence['observation_id']}"
        ).json()
        assert client.get(observation["original_asset_reference"]).content == image
    return runtime, users, saved, observation, image


def test_migration_source_checks(tmp_path: Path) -> None:
    runtime, users, _, _, _ = make_source(tmp_path)
    snapshots = read_runtime(runtime)
    assert len(snapshots) == 3
    assert len(snapshots[-1].assets) == 2
    assert len(read_users(users)) == 1
    asset = next((runtime / "personal_workspaces").glob("account-*/originals/*.bin"))
    asset.write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="hash mismatch"):
        read_runtime(runtime)


def test_postgres_migration_restart_upload_and_isolation(tmp_path: Path) -> None:
    url = os.environ.get("MARSENSE_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Disposable PostgreSQL service is not configured")
    parsed = make_url(url)
    assert parsed.host in {"127.0.0.1", "localhost"} and parsed.database == "marsense_test", (
        "Cloud integration tests must never connect to a real production database"
    )
    engine = create_engine(url)
    with engine.begin() as connection:
        for role in ("anon", "authenticated", "service_role"):
            connection.execute(text(f"CREATE ROLE {role} NOLOGIN"))
    engine.dispose()

    runtime, users, saved, observation, image = make_source(tmp_path)
    snapshots = read_runtime(runtime)
    identities = read_users(users)
    for item in snapshots:
        sync_snapshot(url, item, identities if item.schema == "marsense" else None)
    for item in snapshots:
        sync_snapshot(
            url, item, identities if item.schema == "marsense" else None, verify_only=True
        )
    # Exact reruns are safe; conflicting changes must not overwrite existing rows.
    sync_snapshot(url, snapshots[0], identities)
    modified = snapshots[0]
    first = next(iter(modified.rows))
    kind, payload = modified.rows[first]
    modified.rows[first] = (kind, {**payload, "migration_test_conflict": True})
    with pytest.raises(ValueError, match="refusing overwrite"):
        sync_snapshot(url, modified, identities)

    cfg = Settings(
        environment="production", database_url=url, runtime_dir=tmp_path / "cloud-empty",
        cors_origins=[ORIGIN],
    )
    data = "/api/workspaces/data"
    with TestClient(create_app(cfg), base_url=ORIGIN) as client:
        assert client.post("/api/auth/login", json=OPERATOR, headers=HEADERS).status_code == 200
        assert client.get("/api/auth/session").json()["registration_enabled"]
        assert client.get("/api/missions/eva-01").status_code == 200
        assert client.post("/api/auth/logout", headers=HEADERS).status_code == 200
        assert client.post("/api/workspaces/auth/login", json=EXPLORER,
                           headers=HEADERS).status_code == 200
        assert client.get(f"{data}/missions/eva-01").json() == saved
        assert client.get(observation["original_asset_reference"]).content == image
        assert client.post("/api/workspaces/auth/logout", headers=HEADERS).status_code == 200
        assert client.post("/api/workspaces/auth/signup", json={
            "username": "explorer-two", "name": "Another explorer",
            "password": "another-private-fixture-password",
        }, headers=HEADERS).status_code == 201
        assert client.get(f"{data}/missions/eva-01").json()["mission"][
            "active_route_id"] == "eva-01-alpha"
        assert client.get(observation["original_asset_reference"]).status_code == 404
        assert client.get(observation["raw_asset_reference"]).status_code == 404
        upload = client.post(f"{data}/observations/upload", headers=HEADERS, files={
            "file": ("another.jpg", image, "image/jpeg"),
        }, data={"footprint": json.dumps({
            "type": "Polygon",
            "coordinates": [[[520, 320], [680, 320], [680, 480], [520, 480], [520, 320]]],
        })})
        assert upload.status_code == 200, upload.text
        new = client.get(f"{data}/observations/{upload.json()['observation_id']}").json()
        assert client.get(new["original_asset_reference"]).content == image
        assert not (cfg.runtime_dir / "personal_workspaces" / "accounts.db").exists()
    with TestClient(create_app(cfg), base_url=ORIGIN) as client:
        assert client.post("/api/workspaces/auth/login", json={
            "username": "explorer-two", "password": "another-private-fixture-password",
        }, headers=HEADERS).status_code == 200
        assert client.get(new["original_asset_reference"]).content == image
        assert client.get(observation["original_asset_reference"]).status_code == 404


def test_fresh_cloud_bootstrap_and_restart(tmp_path: Path) -> None:
    url = os.environ.get("MARSENSE_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Disposable PostgreSQL service is not configured")
    parsed = make_url(url)
    assert parsed.host in {"127.0.0.1", "localhost"} and parsed.database == "marsense_test"
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text("CREATE DATABASE marsense_fresh_test"))
        for role in ("anon", "authenticated", "service_role"):
            connection.execute(text(
                f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{role}') "
                f"THEN CREATE ROLE {role} NOLOGIN; END IF; END $$"
            ))
    engine.dispose()
    fresh_url = parsed.set(database="marsense_fresh_test").render_as_string(hide_password=False)
    from pydantic import SecretStr

    password = "fresh-test-operator-password"
    config = Settings(
        environment="production", database_url=fresh_url,
        runtime_dir=tmp_path / "fresh", cors_origins=[ORIGIN],
        cloud_fresh_start=True, cloud_admin_password=SecretStr(password),
    )
    login = {"username": "marsense-admin", "password": password}
    with TestClient(create_app(config), base_url=ORIGIN) as client:
        assert client.post("/api/auth/login", headers=HEADERS, json=login).status_code == 200
        mission = client.get("/api/missions/eva-01").json()
        assert mission["mission"]["active_route_id"] == "eva-01-alpha"
        assert client.get("/api/health").status_code == 200
    config.cloud_fresh_start = False
    config.cloud_admin_password = SecretStr("")
    with TestClient(create_app(config), base_url=ORIGIN) as client:
        assert client.post("/api/auth/login", headers=HEADERS, json=login).status_code == 200
        assert client.get("/api/missions/eva-01").json() == mission
