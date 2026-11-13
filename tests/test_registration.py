import json
import time

from fastapi.testclient import TestClient

from backend.auth import RegistrationInvite, password_hash
from backend.config import Settings
from backend.main import create_app
from backend.store import all_of, put


def test_invitation_registration_single_use_roles_and_persistence(tmp_path):
    users = tmp_path / "users.json"
    users.write_text(json.dumps([{
        "id": "operator", "username": "operator", "name": "Operator", "role": "ADMIN",
        "password_hash": password_hash("private-admin-test-password"),
    }]))
    origin = "https://mission.example"
    headers = {"Origin": origin}
    config = Settings(
        environment="production", database_url=f"sqlite:///{tmp_path / 'mission.db'}",
        runtime_dir=tmp_path / "runtime", auth_users_file=str(users), cors_origins=[origin],
    )
    app = create_app(config)
    with TestClient(app, base_url=origin) as admin:
        assert admin.get("/api/auth/session").json()["registration_enabled"]
        assert admin.post("/api/auth/invitations", json={}, headers=headers).status_code == 401
        assert admin.post("/api/auth/login", json={
            "username": "operator", "password": "private-admin-test-password"
        }, headers=headers).status_code == 200
        assert admin.post("/api/auth/invitations", json={"role": "ADMIN"},
                          headers=headers).status_code == 422
        invite = admin.post("/api/auth/invitations", json={}, headers=headers)
        assert invite.status_code == 201
        token = invite.json()["token"]
        assert token not in admin.get("/api/auth/admin").text
        account = {"token": token, "username": "explorer", "name": "New Explorer",
                   "password": "private-explorer-test-password"}
        with TestClient(create_app(config), base_url=origin) as explorer:
            assert explorer.post("/api/auth/register", json=account).status_code == 403
            assert explorer.post("/api/auth/register", json={**account, "role": "ADMIN"},
                                 headers=headers).status_code == 422
            invalid = explorer.post("/api/auth/register", json={**account, "password": "secret"},
                                    headers=headers)
            assert invalid.status_code == 422
            assert "secret" not in invalid.text and token not in invalid.text
            registered = explorer.post("/api/auth/register", json=account, headers=headers)
            assert registered.status_code == 201
            user = registered.json()["user"]
            assert user["role"] == "ASTRONAUT" and "password_hash" not in user
            assert explorer.post("/api/auth/register", json={**account, "username": "second"},
                                 headers=headers).status_code == 400
            assert explorer.post("/api/auth/login", json={
                "username": "explorer", "password": account["password"]
            }, headers=headers).status_code == 200
            assert explorer.get("/api/missions/eva-01").status_code == 200
            assert explorer.get("/api/auth/admin").status_code == 403
            assert explorer.post(
                "/api/auth/invitations", json={}, headers=headers
            ).status_code == 403
            cookie = explorer.cookies.get("marsense_session")
            assert cookie
        snapshot = admin.get("/api/auth/admin").json()
        assert snapshot["accounts"][0]["id"] == user["id"]
        assert "password_hash" not in snapshot["accounts"][0]
        assert snapshot["invitations"][0]["used_by"] == user["id"]
        expired = admin.post("/api/auth/invitations", json={}, headers=headers).json()["token"]
        with app.state.store.session(write=True) as session:
            for row in all_of(session, RegistrationInvite):
                if not row.used_by:
                    row.expires_at = time.time() - 1
                    put(session, row)
        assert admin.post("/api/auth/register", json={**account, "token": expired,
                          "username": "expired-user"}, headers=headers).status_code == 400
    # Both the new account and its session survive a backend restart.
    with TestClient(create_app(config), base_url=origin) as restarted:
        restarted.cookies.set("marsense_session", cookie)
        assert restarted.get("/api/auth/session").json()["user"]["id"] == user["id"]
        assert restarted.post("/api/auth/logout", headers=headers).status_code == 200
        assert restarted.post("/api/auth/login", json={
            "username": "operator", "password": "private-admin-test-password"
        }, headers=headers).status_code == 200
        assert restarted.post(f"/api/auth/accounts/{user['id']}/disable", json={},
                              headers=headers).status_code == 200
        assert restarted.post("/api/auth/login", json={
            "username": "explorer", "password": account["password"]
        }, headers=headers).status_code == 401
    assert json.loads(users.read_text())[0]["id"] == "operator"


def test_registration_disabled_in_local_demo(client):
    assert not client.get("/api/auth/session").json()["registration_enabled"]
    response = client.post("/api/auth/register", json={
        "token": "a" * 43, "username": "test", "name": "Test User",
        "password": "private-local-test-password",
    }, headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 404
