import json

from fastapi.testclient import TestClient

from backend.auth import password_hash
from backend.config import Settings
from backend.main import create_app


def test_public_demo_isolated_from_other_guests_and_production(tmp_path):
    users = tmp_path / "users.json"
    users.write_text(json.dumps([{
        "id": "controller", "username": "controller", "name": "Mission Controller",
        "role": "ADMIN", "password_hash": password_hash("isolated-controller-password"),
    }]))
    origin = "https://marsense.example"
    app = create_app(Settings(
        environment="production", database_url=f"sqlite:///{tmp_path / 'production.db'}",
        auth_users_file=str(users), cors_origins=[origin],
    ))
    prefix = "/api/public-demo"
    headers = {"Origin": origin}
    with TestClient(app, base_url=origin) as client:
        assert client.get(f"{prefix}/missions/eva-01").status_code == 401
        denied = client.post(f"{prefix}/start", headers={"Origin": "https://wrong"})
        assert denied.status_code == 403
        assert client.get("/api/missions/eva-01").status_code == 401
        assert client.post("/api/auth/login", headers=headers, json={
            "username": "controller", "password": "isolated-controller-password",
        }).status_code == 200
        before = client.get("/api/missions/eva-01").json()
        assert client.post("/api/auth/logout", headers=headers).status_code == 200

        first = client.post(f"{prefix}/start", headers=headers)
        second = client.post(f"{prefix}/start", headers=headers)
        assert first.status_code == second.status_code == 201
        assert first.headers["cache-control"] == "no-store"
        a = {**headers, "X-Marsense-Demo": first.json()["token"]}
        b = {**headers, "X-Marsense-Demo": second.json()["token"]}
        assert a != b
        assert client.get(f"{prefix}/auth/session", headers=a).json()["public_demo"]
        assert client.get("/api/missions/eva-01", headers=a).status_code == 401
        assert client.post(f"{prefix}/observations/demo", headers={
            **a, "Origin": "https://wrong",
        }, json={}).status_code == 403
        response = client.post(f"{prefix}/observations/demo", headers=a, json={})
        assert response.status_code == 200
        evidence = response.json()
        assert evidence["source_type"] == "demo_replay"
        assert evidence["verification_state"] == "PROVISIONAL"
        evidence_id = evidence["id"]
        detail = f"{prefix}/evidence/{evidence_id}"
        assert client.get(detail, headers=b).status_code == 404
        confirmed = client.post(f"{detail}/verify", headers=a, json={
            "decision": "CONFIRMED", "reviewer": "Untrusted name",
            "note": "Guest simulated review",
        })
        assert confirmed.status_code == 200
        assert confirmed.json()["verified_by"] == "Guest reviewer (simulation)"
        snapshot = client.get(f"{prefix}/missions/eva-01", headers=a).json()
        assert any(r["name"] == "Route Beta" and r["id"] == snapshot["mission"]["active_route_id"]
                   for r in snapshot["routes"])
        future = client.get(f"{prefix}/missions/eva-02", headers=a).json()
        assert evidence_id in future["mission"]["inherited_evidence"]
        other = client.get(f"{prefix}/missions/eva-01", headers=b).json()
        assert other["mission"]["active_route_id"] == "eva-01-alpha"
        assert client.get(f"{detail}/history", headers=a).status_code == 200
        assert client.get(f"{detail}/ancestry", headers=a).status_code == 200
        assert client.get(f"{prefix}/observations/{evidence['observation_id']}",
                          headers=a).status_code == 200
        assert client.post(f"{prefix}/observations/upload", headers=a).status_code == 403
        assert client.post(f"{prefix}/showcase/reset", headers=a).status_code == 200
        assert client.get(detail, headers=a).status_code == 404
        assert client.post(f"{prefix}/auth/logout", headers=a).status_code == 200
        assert client.get(f"{prefix}/missions/eva-01", headers=a).status_code == 401
        assert client.get(f"{prefix}/missions/eva-01", headers=b).status_code == 200
        assert client.post("/api/auth/login", headers=headers, json={
            "username": "controller", "password": "isolated-controller-password",
        }).status_code == 200
        assert client.get("/api/missions/eva-01").json() == before
