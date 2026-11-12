import json

from fastapi.testclient import TestClient

from backend.auth import password_hash
from backend.config import Settings
from backend.main import create_app


def test_showcase_replay_reset_and_production_isolation(tmp_path):
    users = tmp_path / "users.json"
    users.write_text(json.dumps([{
        "id": "demo-admin", "username": "demo-admin", "name": "Demo Reviewer",
        "role": "ADMIN", "password_hash": password_hash("isolated-showcase-password"),
    }]))
    origin = "https://showcase.example"
    headers = {"Origin": origin}
    common = {"auth_users_file": str(users), "cors_origins": [origin]}
    production = Settings(
        environment="production", database_url=f"sqlite:///{tmp_path / 'production.db'}", **common
    )
    showcase = Settings(
        environment="showcase", database_url=f"sqlite:///{tmp_path / 'showcase.db'}", **common
    )
    with TestClient(create_app(production), base_url=origin) as prod:
        with TestClient(create_app(showcase), base_url=origin) as demo:
            assert demo.post("/api/observations/demo", json={}, headers=headers).status_code == 401
            for client in (prod, demo):
                response = client.post("/api/auth/login", json={
                    "username": "demo-admin", "password": "isolated-showcase-password",
                }, headers=headers)
                assert response.status_code == 200
                assert "secure" in response.headers["set-cookie"].lower()
            assert "marsense_showcase_session" in demo.cookies
            assert "marsense_session" not in demo.cookies
            assert prod.post("/api/observations/demo", json={}, headers=headers).status_code == 404
            assert prod.post("/api/showcase/reset", headers=headers).status_code == 404
            original = prod.get("/api/missions/eva-01").json()
            response = demo.post("/api/observations/demo", json={}, headers=headers)
            assert response.status_code == 200
            evidence = response.json()
            assert evidence["source_type"] == "demo_replay"
            assert evidence["verification_state"] == "PROVISIONAL"
            response = demo.post(f"/api/evidence/{evidence['id']}/verify", json={
                "decision": "CONFIRMED", "reviewer": "Untrusted", "note": "Curated replay reviewed",
            }, headers=headers)
            assert response.status_code == 200
            assert response.json()["verified_by"] == "Demo Reviewer"
            future = demo.get("/api/missions/eva-02").json()
            assert evidence["id"] in future["mission"]["inherited_evidence"]
            assert demo.post(
                "/api/showcase/reset", headers={"Origin": "https://wrong.example"}
            ).status_code == 403
            assert demo.post("/api/showcase/reset", headers=headers).status_code == 200
            assert not demo.get("/api/missions/eva-02").json()["mission"]["inherited_evidence"]
            assert demo.get(f"/api/evidence/{evidence['id']}").status_code == 404
            assert demo.post("/api/observations/demo", json={}, headers=headers).status_code == 200
            assert prod.get("/api/missions/eva-01").json() == original
