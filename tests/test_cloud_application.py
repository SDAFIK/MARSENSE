"""Real disposable Postgres, simulated Supabase HTTP services; no external project writes."""
import json
import os
from secrets import token_urlsafe
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.cloud_assets import CloudAssets
from backend.cloud_workspace import ACCESS, SupabaseIdentity
from backend.config import ROOT, Settings
from backend.main import create_app


class Provider:
    def __init__(self):
        self.users = {}
        self.access = {}
        self.refresh = {}
        self.objects = {}

    def session(self, email):
        token, refresh = token_urlsafe(24), token_urlsafe(24)
        self.access[token] = email
        self.refresh[refresh] = email
        return {"access_token": token, "refresh_token": refresh, "expires_in": 3600}

    def __call__(self, request):
        path = request.url.path
        method = request.method
        if path == "/auth/v1/signup":
            body = json.loads(request.content)
            email = body["email"]
            self.users[email] = {"id": str(uuid4()), "email": email, "user_metadata": body["data"]}
            return httpx.Response(200, json={"id": self.users[email]["id"]})
        if path == "/auth/v1/token":
            body = json.loads(request.content)
            if request.url.params["grant_type"] == "refresh_token":
                email = self.refresh.pop(body["refresh_token"], None)
            else:
                email = body["email"]
            if email not in self.users or not self.users[email].get("email_confirmed_at"):
                return httpx.Response(400, json={"error": "invalid"})
            return httpx.Response(200, json=self.session(email))
        if path == "/auth/v1/user":
            email = self.access.get(request.headers.get("authorization", "").removeprefix("Bearer "))
            if email is None:
                return httpx.Response(401, json={"error": "invalid"})
            return httpx.Response(200, json=self.users[email])
        if path == "/auth/v1/logout":
            self.access.pop(request.headers.get("authorization", "").removeprefix("Bearer "), None)
            return httpx.Response(204)
        if path == "/storage/v1/bucket/marsense-private":
            return httpx.Response(200, json={"public": False})
        if path == "/storage/v1/object/list/marsense-private":
            prefix = json.loads(request.content)["prefix"] + "/"
            return httpx.Response(200, json=[
                {"name": key.removeprefix(prefix), "metadata": {"size": len(value)}}
                for key, value in self.objects.items() if key.startswith(prefix)
            ])
        if path.startswith("/storage/v1/object/authenticated/marsense-private/"):
            key = path.removeprefix("/storage/v1/object/authenticated/marsense-private/")
            if key not in self.objects:
                return httpx.Response(404)
            return httpx.Response(200, content=self.objects[key])
        if path.startswith("/storage/v1/object/marsense-private/") and method == "POST":
            key = path.removeprefix("/storage/v1/object/marsense-private/")
            if key in self.objects:
                return httpx.Response(409)
            self.objects[key] = request.content
            return httpx.Response(200, json={"Key": key})
        if path == "/storage/v1/object/marsense-private" and method == "DELETE":
            for key in json.loads(request.content)["prefixes"]:
                self.objects.pop(key, None)
            return httpx.Response(200, json=[])
        raise AssertionError(f"Unexpected provider operation {method} {path}")


@pytest.mark.skipif(not os.getenv("MARSENSE_TEST_POSTGRES_URL"), reason="Disposable Postgres required")
def test_cloud_email_missions_private_assets_restart_and_guest_isolation(monkeypatch, tmp_path):
    provider = Provider()
    monkeypatch.setattr("backend.cloud_workspace.SupabaseIdentity",
                        lambda settings: SupabaseIdentity(settings, httpx.MockTransport(provider)))
    monkeypatch.setattr("backend.main.CloudAssets",
                        lambda settings: CloudAssets(settings, httpx.MockTransport(provider)))
    origin = "https://marsense.example"
    settings = Settings(
        environment="production", runtime_dir=tmp_path,
        cloud_database_url=SecretStr(os.environ["MARSENSE_TEST_POSTGRES_URL"]),
        cloud_supabase_url="https://fixture.supabase.co",
        cloud_publishable_key=SecretStr("fixture-publishable"),
        cloud_storage_key=SecretStr("fixture-service"),
        cloud_public_origin=origin, cors_origins=[origin],
    )
    headers = {"Origin": origin}
    auth = "/api/workspaces/auth"
    data = "/api/workspaces/data"
    email = f"one-{uuid4().hex}@example.com"
    email2 = f"two-{uuid4().hex}@example.com"
    password = "fixture-only-password"
    image = (ROOT / "data/nasa/ground-navcam.jpg").read_bytes()
    footprint = {"type": "Polygon", "coordinates": [
        [[520, 320], [680, 320], [680, 480], [520, 480], [520, 320]]
    ]}

    def register(client, address, name):
        result = client.post(f"{auth}/signup", headers=headers, json={
            "email": address, "password": password, "name": name,
        })
        assert result.status_code == 201, result.text
        assert result.json()["confirmation_required"]
        assert client.get(f"{data}/missions/eva-01").status_code == 401
        provider.users[address]["email_confirmed_at"] = "2026-11-13T00:00:00Z"
        result = client.post(f"{auth}/login", headers=headers, json={
            "email": address, "password": password,
        })
        assert result.status_code == 200, result.text
        assert result.json()["user"]["role"] == "MISSION_CONTROL"
        assert "password_hash" not in result.text
        assert "HttpOnly" in result.headers["set-cookie"]

    with TestClient(create_app(settings), base_url=origin) as client:
        assert client.get("/api/missions/eva-01").status_code == 401
        assert client.get(f"{auth}/session").json()["cloud_auth"]
        assert client.post(f"{auth}/signup", headers={"Origin": "https://wrong.example"}, json={
            "email": email, "password": password, "name": "Explorer One",
        }).status_code == 403
        register(client, email, "Explorer One")
        # The identity provider, not editable user metadata, controls the owner namespace.
        provider.users[email]["user_metadata"]["role"] = "ADMIN"
        assert client.get(f"{auth}/session").json()["user"]["role"] == "MISSION_CONTROL"
        initial = client.get(f"{data}/missions/eva-01").json()
        assert initial["mission"]["active_route_id"] == "eva-01-alpha"
        assert client.get("/api/missions/eva-01").status_code == 401
        uploaded = client.post(f"{data}/observations/upload", headers=headers,
                               files={"file": ("fixture.jpg", image, "image/jpeg")},
                               data={"footprint": json.dumps(footprint), "mission_id": "eva-01"})
        assert uploaded.status_code == 200, uploaded.text
        evidence = uploaded.json()
        original = client.get(f"{data}/observations/{evidence['observation_id']}").json()[
            "original_asset_reference"]
        assert client.get(original).content == image
        assert client.get(evidence["raw_asset_reference"]).status_code == 200
        detail = f"{data}/evidence/{evidence['id']}"
        verified = client.post(f"{detail}/verify", headers=headers, json={
            "decision": "CONFIRMED", "reviewer": "untrusted", "human_terrain": "obstacle-rich terrain",
            "note": "Cloud fixture review",
        })
        assert verified.status_code == 200, verified.text
        assert verified.json()["verified_by"] == "Explorer One"
        saved = client.get(f"{data}/missions/eva-01").json()
        active = next(r for r in saved["routes"] if r["id"] == saved["mission"]["active_route_id"])
        assert active["name"] == "Route Beta"
        assert evidence["id"] in client.get(f"{data}/missions/eva-02").json()["mission"]["inherited_evidence"]
        # Expire access server-side; refresh through the protected auth endpoint.
        provider.access.pop(client.cookies.get(ACCESS), None)
        assert client.get(f"{data}/missions/eva-01").status_code == 401
        assert client.get(f"{auth}/session").json()["user"]["name"] == "Explorer One"
        assert client.get(f"{data}/missions/eva-01").status_code == 200
        assert client.post(f"{auth}/logout", headers=headers).status_code == 200
        assert client.get(f"{data}/missions/eva-01").status_code == 401
        register(client, email2, "Explorer Two")
        assert client.get(f"{data}/missions/eva-01").json()["mission"]["active_route_id"] == "eva-01-alpha"
        assert client.get(detail).status_code == 404
        assert client.get(original).status_code == 404
        assert client.get(evidence["raw_asset_reference"]).status_code == 404
        assert client.post(f"{data}/showcase/reset", headers=headers).status_code == 404
        assert client.post(f"{auth}/logout", headers=headers).status_code == 200
        guest = client.post("/api/public-demo/start", headers=headers).json()["token"]
        assert client.get("/api/public-demo/missions/eva-01", headers={"X-Marsense-Demo": guest}).json()[
            "mission"]["active_route_id"] == "eva-01-alpha"
        assert client.get(f"{data}/missions/eva-01").status_code == 401

    with TestClient(create_app(settings), base_url=origin) as client:
        assert client.post(f"{auth}/login", headers=headers, json={
            "email": email, "password": password,
        }).status_code == 200
        assert client.get(f"{data}/missions/eva-01").json() == saved
        assert client.get(original).content == image
        assert not (tmp_path / "cloud").exists()
