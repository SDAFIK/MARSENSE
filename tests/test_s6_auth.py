import json
import time

from fastapi.testclient import TestClient

from backend.auth import AuthSession, password_hash
from backend.config import Settings
from backend.main import create_app
from backend.store import all_of, put


def test_authenticated_review_logout_expiry_roles_and_audit(tmp_path):
    users = tmp_path / "users.json"
    users.write_text(
        json.dumps(
            [
                {
                    "id": "control-1",
                    "username": "control",
                    "name": "Mission Reviewer",
                    "role": "MISSION_CONTROL",
                    "password_hash": password_hash("a-long-test-password"),
                },
                {
                    "id": "explorer-1",
                    "username": "explorer",
                    "name": "Explorer",
                    "role": "ASTRONAUT",
                    "password_hash": password_hash("another-test-password"),
                },
            ]
        )
    )
    config = Settings(
        database_url=f"sqlite:///{tmp_path / 'auth.db'}",
        auth_users_file=str(users),
        auth_required=True,
    )
    headers = {"Origin": "http://127.0.0.1:3000"}
    with TestClient(create_app(config)) as client:
        assert client.post("/api/observations/demo", json={}).status_code == 401
        login = client.post(
            "/api/auth/login",
            json={"username": "control", "password": "a-long-test-password"},
            headers=headers,
        )
        assert login.status_code == 200
        assert "httponly" in login.headers["set-cookie"].lower()
        evidence = client.post("/api/observations/demo", json={}, headers=headers).json()
        denied = client.post(
            f"/api/evidence/{evidence['id']}/verify",
            json={"decision": "CONFIRMED", "reviewer": "Imposter", "note": "Inspect image"},
        )
        assert denied.status_code == 403
        result = client.post(
            f"/api/evidence/{evidence['id']}/verify",
            json={"decision": "CONFIRMED", "reviewer": "Imposter", "note": "Inspect image"},
            headers=headers,
        )
        assert result.status_code == 200
        assert result.json()["verified_by"] == "Mission Reviewer"
        decision = client.get(f"/api/evidence/{evidence['id']}/history").json()["decisions"][0]
        assert decision["user_id"] == "control-1"
        assert decision["identity_basis"] == "authenticated session"
        assert client.post("/api/auth/logout", headers=headers).status_code == 200
        assert client.post("/api/observations/demo", json={}, headers=headers).status_code == 401
        client.post(
            "/api/auth/login",
            json={"username": "explorer", "password": "another-test-password"},
            headers=headers,
        )
        assert (
            client.post(
                f"/api/evidence/{evidence['id']}/verify",
                json={"decision": "REJECTED", "reviewer": "Imposter", "note": "Wrong role"},
                headers=headers,
            ).status_code
            == 403
        )
        with client.app.state.store.session(write=True) as session:
            for token in all_of(session, AuthSession):
                token.expires_at = time.time() - 1
                put(session, token)
        assert client.post("/api/observations/demo", json={}, headers=headers).status_code == 401


def test_read_only_demo_rejects_mutation(settings):
    settings.read_only = True
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/missions/eva-01").status_code == 200
        assert client.post("/api/observations/demo", json={}).status_code == 403


def test_production_cookie_and_login_throttling(tmp_path):
    users = tmp_path / "users.json"
    users.write_text(
        json.dumps(
            [
                {
                    "id": "operator",
                    "username": "operator",
                    "name": "Operator",
                    "role": "ADMIN",
                    "password_hash": password_hash("long-private-test-password"),
                }
            ]
        )
    )
    settings = Settings(
        environment="production",
        auth_users_file=str(users),
        database_url=f"sqlite:///{tmp_path / 'secure.db'}",
        cors_origins=["https://mission.example"],
    )
    with TestClient(create_app(settings), base_url="https://mission.example") as client:
        headers = {"Origin": "https://mission.example"}
        response = client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "long-private-test-password"},
            headers=headers,
        )
        assert response.status_code == 200
        assert "secure" in response.headers["set-cookie"].lower()
        assert "samesite=strict" in response.headers["set-cookie"].lower()
        for _ in range(5):
            assert (
                client.post(
                    "/api/auth/login",
                    json={"username": "operator", "password": "wrong"},
                    headers=headers,
                ).status_code
                == 401
            )
        assert (
            client.post(
                "/api/auth/login",
                json={"username": "operator", "password": "wrong"},
                headers=headers,
            ).status_code
            == 429
        )
