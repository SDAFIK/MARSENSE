import json

from fastapi.testclient import TestClient

from backend.auth import password_hash
from backend.config import ROOT, Settings
from backend.main import create_app
from backend.workspaces import WORKSPACE_COOKIE


def test_self_service_workspace_upload_review_persistence_and_isolation(tmp_path):
    users = tmp_path / "operator.json"
    users.write_text(json.dumps([{
        "id": "controller", "username": "controller", "name": "Operator",
        "role": "ADMIN", "password_hash": password_hash("isolated-controller-password"),
    }]))
    origin = "https://marsense.example"
    settings = Settings(
        environment="production", database_url=f"sqlite:///{tmp_path / 'production.db'}",
        runtime_dir=tmp_path / "runtime", auth_users_file=str(users), cors_origins=[origin],
    )
    auth = "/api/workspaces/auth"
    data = "/api/workspaces/data"
    headers = {"Origin": origin}
    first = {"username": "explorer-one", "password": "first-explorer-password"}
    second = {"username": "explorer-two", "password": "second-explorer-password"}
    image = (ROOT / "data/nasa/ground-navcam.jpg").read_bytes()
    footprint = {
        "type": "Polygon",
        "coordinates": [[[520, 320], [680, 320], [680, 480], [520, 480], [520, 320]]],
    }
    with TestClient(create_app(settings), base_url=origin) as client:
        assert client.get(f"{data}/missions/eva-01").status_code == 401
        assert client.post("/api/auth/login", headers=headers, json={
            "username": "controller", "password": "isolated-controller-password",
        }).status_code == 200
        original = client.get("/api/missions/eva-01").json()
        assert client.post("/api/auth/logout", headers=headers).status_code == 200
        assert client.post(f"{auth}/signup", headers={"Origin": "https://wrong"}, json={
            **first, "name": "Explorer One",
        }).status_code == 403
        invalid = client.post(f"{auth}/signup", headers=headers, json={
            **first, "name": "Explorer One", "password": "secret",
        })
        assert invalid.status_code == 422
        assert "secret" not in invalid.text
        signup = client.post(f"{auth}/signup", headers=headers, json={
            **first, "name": "Explorer One",
        })
        assert signup.status_code == 201
        assert signup.json()["user"]["role"] == "MISSION_CONTROL"
        assert "password_hash" not in signup.json()["user"]
        assert "httponly" in signup.headers["set-cookie"].lower()
        assert "secure" in signup.headers["set-cookie"].lower()
        assert WORKSPACE_COOKIE in client.cookies
        assert client.get("/api/missions/eva-01").status_code == 401
        assert client.get(f"{data}/auth/admin").status_code == 404
        assert client.post(f"{data}/showcase/reset", headers=headers).status_code == 404
        assert client.post(f"{auth}/signup", headers=headers, json={
            **first, "name": "Duplicate",
        }).status_code == 409
        prior = client.get(f"{data}/missions/eva-01")
        assert prior.status_code == 200
        assert prior.headers["cache-control"] == "private, no-store"
        assert prior.json()["mission"]["active_route_id"] == "eva-01-alpha"

        upload = client.post(
            f"{data}/observations/upload", headers=headers,
            files={"file": ("fixture.jpg", image, "image/jpeg")},
            data={"footprint": json.dumps(footprint), "mission_id": "eva-01"},
        )
        assert upload.status_code == 200, upload.text
        evidence = upload.json()
        assert evidence["source_type"] == "ground"
        assert evidence["verification_state"] == "PROVISIONAL"
        assert evidence["raw_asset_reference"].startswith(data + "/assets/")
        observation = client.get(f"{data}/observations/{evidence['observation_id']}").json()
        assert observation["original_asset_reference"].startswith(data + "/observations/")
        assert client.get(observation["original_asset_reference"]).content == image
        detail = f"{data}/evidence/{evidence['id']}"
        denied = client.post(f"{detail}/verify", headers={"Origin": "https://wrong"}, json={
            "decision": "CONFIRMED", "reviewer": "Untrusted",
            "human_terrain": "obstacle-rich terrain", "note": "Personal review",
        })
        assert denied.status_code == 403
        verified = client.post(f"{detail}/verify", headers=headers, json={
            "decision": "CONFIRMED", "reviewer": "Untrusted",
            "human_terrain": "obstacle-rich terrain", "note": "Personal review",
        })
        assert verified.status_code == 200, verified.text
        assert verified.json()["verified_by"] == "Explorer One"
        saved = client.get(f"{data}/missions/eva-01").json()
        active = next(r for r in saved["routes"] if r["id"] == saved["mission"]["active_route_id"])
        assert active["name"] == "Route Beta"
        future = client.get(f"{data}/missions/eva-02").json()
        assert evidence["id"] in future["mission"]["inherited_evidence"]
        assert client.post(f"{auth}/logout", headers=headers).status_code == 200
        assert client.get(f"{data}/missions/eva-01").status_code == 401

        assert client.post(f"{auth}/signup", headers=headers, json={
            **second, "name": "Explorer Two",
        }).status_code == 201
        assert client.get(f"{data}/missions/eva-01").json()["mission"][
            "active_route_id"] == "eva-01-alpha"
        assert client.get(detail).status_code == 404
        assert client.get(evidence["raw_asset_reference"]).status_code == 404
        assert client.get(observation["original_asset_reference"]).status_code == 404
        assert client.post(f"{auth}/logout", headers=headers).status_code == 200
        assert client.post("/api/auth/login", headers=headers, json={
            "username": "controller", "password": "isolated-controller-password",
        }).status_code == 200
        assert client.get("/api/missions/eva-01").json() == original
        assert client.get(f"{data}/missions/eva-01").status_code == 401

    # Account, source image, decision, map and route survive a complete API restart.
    with TestClient(create_app(settings), base_url=origin) as client:
        assert client.post(f"{auth}/login", headers=headers, json=first).status_code == 200
        assert client.get(f"{data}/missions/eva-01").json() == saved
        assert client.get(observation["original_asset_reference"]).content == image
