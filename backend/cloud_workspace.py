"""Supabase email identities and persistent, server-only personal mission schemas."""
import logging
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text

from backend.auth import User, check_origin
from backend.cloud_store import CloudStore, create_cloud_engine
from backend.config import Settings
from backend.seed import seed
from backend.service import MissionService
from backend.workspaces import MAX_ACCOUNTS, WORKSPACE_PREFIX, Workspace, WorkspaceContext

logger = logging.getLogger(__name__)
ACCESS = "marsense_cloud_access"
REFRESH = "marsense_cloud_refresh"
AUTH_PATH = WORKSPACE_PREFIX + "/auth"


class CloudLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=1, max_length=1024)


class CloudSignup(CloudLogin):
    password: str = Field(min_length=15, max_length=256)
    name: str = Field(min_length=2, max_length=80)

    @field_validator("name", mode="before")
    @classmethod
    def plain_name(cls, value: Any) -> str:
        if not isinstance(value, str) or any(ord(c) < 32 or c in "<>" for c in value):
            raise ValueError("Use a plain-text display name")
        return value.strip()


class SupabaseIdentity:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(
            base_url=settings.cloud_supabase_url.rstrip("/") + "/auth/v1/",
            headers={"apikey": settings.cloud_publishable_key.get_secret_value()},
            timeout=20, follow_redirects=False, transport=transport,
        )
        self.redirect = settings.cloud_public_origin.rstrip("/") + "/workspace-login"

    def close(self) -> None:
        self.client.close()

    def request(self, method: str, path: str, token: str = "", **kwargs: Any) -> httpx.Response:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            return self.client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Cloud identity service is unavailable") from exc

    @staticmethod
    def checked(response: httpx.Response, message: str, invalid: int = 400) -> dict[str, Any]:
        if response.status_code == 429:
            raise HTTPException(429, "Account request limit reached. Try again later.")
        if response.status_code >= 500:
            raise HTTPException(503, "Cloud identity service is unavailable")
        if not response.is_success:
            raise HTTPException(invalid, message)
        value = response.json()
        if not isinstance(value, dict):
            raise HTTPException(503, "Unexpected identity service response")
        return value

    def signup(self, body: CloudSignup) -> dict[str, Any]:
        return self.checked(self.request("POST", "signup", params={"redirect_to": self.redirect},
                            json={"email": body.email.strip().lower(), "password": body.password,
                                  "data": {"name": body.name}}), "Unable to create account")

    def login(self, body: CloudLogin) -> dict[str, Any]:
        return self.checked(self.request("POST", "token", params={"grant_type": "password"},
                            json={"email": body.email.strip().lower(), "password": body.password}),
                            "Sign-in failed. Confirm your email and check your credentials.", 401)

    def refresh(self, token: str) -> dict[str, Any] | None:
        response = self.request("POST", "token", params={"grant_type": "refresh_token"},
                                json={"refresh_token": token})
        if response.status_code in (400, 401, 403):
            return None
        return self.checked(response, "Session refresh failed", 401)

    def user(self, token: str | None) -> User | None:
        if not token or len(token) > 4096:
            return None
        response = self.request("GET", "user", token=token)
        if response.status_code in (400, 401, 403):
            return None
        data = self.checked(response, "Session is invalid", 401)
        try:
            ident = UUID(str(data["id"])).hex
            email = data["email"]
            if not isinstance(email, str) or not data.get("email_confirmed_at"):
                return None
            metadata = data.get("user_metadata") or {}
            name = metadata.get("name", "Explorer")
            if not isinstance(name, str) or not 2 <= len(name) <= 80 or any(
                ord(c) < 32 or c in "<>" for c in name
            ):
                name = "Explorer"
            # Role and namespace are server-derived, never taken from editable metadata.
            return User(id=f"account-{ident}", username=email, name=name,
                        role="MISSION_CONTROL", password_hash="")
        except (KeyError, ValueError, TypeError, AttributeError):
            return None

    def revoke(self, token: str) -> None:
        response = self.request("POST", "logout", token=token, params={"scope": "local"})
        if not response.is_success and response.status_code not in (400, 401, 403):
            raise HTTPException(503, "Provider logout could not be verified")


class CloudWorkspaceManager:
    def __init__(self, settings: Settings, service: MissionService):
        self.url = settings.cloud_database_url.get_secret_value()
        self.engine = create_cloud_engine(self.url)
        self.identity = SupabaseIdentity(settings)
        self.origins = settings.cors_origins
        self.service = service
        self.root = settings.runtime_dir
        self.lock = Lock()
        self.workspaces: dict[str, Workspace] = {}

    def context(self, request: Request) -> WorkspaceContext:
        user = self.identity.user(request.cookies.get(ACCESS))
        if not user:
            raise HTTPException(401, "Authentication required")
        ident = user.id.removeprefix("account-")
        schema = f"marsense_user_{ident}"
        with self.lock:
            workspace = self.workspaces.get(user.id)
            if workspace is None:
                with self.engine.begin() as connection:
                    connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('marsense_provision',0))"))
                    existing = connection.scalar(
                        text("SELECT 1 FROM pg_namespace WHERE nspname=:schema"), {"schema": schema}
                    )
                    count = connection.scalar(text(
                        "SELECT count(*) FROM pg_namespace WHERE nspname ~ '^marsense_user_[0-9a-f]{32}$'"
                    ))
                    if not existing and (count or 0) >= MAX_ACCOUNTS:
                        raise HTTPException(429, "Personal workspace capacity reached")
                    store = CloudStore(self.url, schema, shared_engine=self.engine)
                    with store.session(write=True) as session:
                        seed(session, self.service.slope_grid)
                workspace = Workspace(store, Path(self.root) / "cloud" / user.id)
                self.workspaces[user.id] = workspace
        return WorkspaceContext(user, workspace)

    def close(self) -> None:
        self.workspaces.clear()
        self.identity.close()
        self.engine.dispose()


def create_cloud_workspace_router(manager: CloudWorkspaceManager) -> APIRouter:
    router = APIRouter(prefix=AUTH_PATH)
    identity = manager.identity

    def clear(response: Response) -> None:
        for name, path in ((ACCESS, WORKSPACE_PREFIX), (REFRESH, AUTH_PATH)):
            response.delete_cookie(name, path=path, secure=True, httponly=True, samesite="strict")
        response.headers["Cache-Control"] = "no-store"

    def adopt(response: Response, result: dict[str, Any]) -> User | None:
        token, refresh = result.get("access_token"), result.get("refresh_token")
        if not isinstance(token, str) or not isinstance(refresh, str):
            return None
        user = identity.user(token)
        if not user:
            return None
        expires = result.get("expires_in", 3600)
        age = max(60, min(3600, expires)) if isinstance(expires, int) else 3600
        response.set_cookie(ACCESS, token, path=WORKSPACE_PREFIX, max_age=age,
                            httponly=True, secure=True, samesite="strict")
        response.set_cookie(REFRESH, refresh, path=AUTH_PATH, max_age=7 * 86400,
                            httponly=True, secure=True, samesite="strict")
        response.headers["Cache-Control"] = "no-store"
        return user

    @router.post("/signup", status_code=201)
    def signup(body: CloudSignup, request: Request, response: Response) -> dict[str, Any]:
        check_origin(request, manager.origins)
        result = identity.signup(body)
        response.headers["Cache-Control"] = "no-store"
        user = adopt(response, result)
        return {"confirmation_required": user is None,
                "user": user.model_dump(exclude={"password_hash"}) if user else None}

    @router.post("/login")
    def login(body: CloudLogin, request: Request, response: Response) -> dict[str, Any]:
        check_origin(request, manager.origins)
        user = adopt(response, identity.login(body))
        if not user:
            raise HTTPException(401, "Confirm your email before signing in")
        return {"user": user.model_dump(exclude={"password_hash"})}

    @router.get("/session")
    def session(request: Request, response: Response) -> dict[str, Any]:
        user = identity.user(request.cookies.get(ACCESS))
        if not user and (refresh := request.cookies.get(REFRESH)):
            result = identity.refresh(refresh)
            user = adopt(response, result) if result else None
            if not user:
                clear(response)
        response.headers["Cache-Control"] = "no-store"
        return {
            "user": user.model_dump(exclude={"password_hash"}) if user else None,
            "required": True, "read_only": False, "environment": "production",
            "registration_enabled": False, "replay_enabled": False,
            "personal_workspace": True, "signup_enabled": True, "cloud_auth": True,
        }

    @router.post("/logout")
    def logout(request: Request, response: Response) -> dict[str, bool]:
        check_origin(request, manager.origins)
        try:
            token = request.cookies.get(ACCESS)
            if not token and (refresh := request.cookies.get(REFRESH)):
                result = identity.refresh(refresh)
                token = result.get("access_token") if result else None
            if isinstance(token, str):
                identity.revoke(token)
        except HTTPException:
            logger.warning("cloud_provider_logout_unverified")
        finally:
            clear(response)
        return {"ok": True}

    return router
