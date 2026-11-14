"""Self-service personal workspaces, separate from operator mission and guest data."""

import hashlib
import re
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from secrets import token_urlsafe
from threading import Lock
from time import monotonic, time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.auth import (
    Auth,
    AuthAudit,
    AuthSession,
    Login,
    RegisteredAccount,
    User,
    check_origin,
    password_hash,
)
from backend.config import Settings
from backend.seed import seed
from backend.service import MissionService, identifier
from backend.store import Store, all_of, put

WORKSPACE_COOKIE = "marsense_workspace_session"
WORKSPACE_PREFIX = "/api/workspaces"
DATA_PREFIX = WORKSPACE_PREFIX + "/data"
MAX_ACCOUNTS = 64
MAX_UPLOADS = 16
MAX_ASSET_BYTES = 64 * 1024 * 1024
_ID = r"[A-Za-z0-9_-]{1,100}"
_GET_DATA = re.compile(
    rf"/(?:missions/{_ID}(?:/alternatives)?|evidence/{_ID}(?:/(?:ancestry|history))?"
    rf"|observations/{_ID}(?:/original)?|assets/upload-[a-f0-9]{{32}}\.jpg)"
)
_POST_DATA = re.compile(rf"/(?:observations/upload|evidence/{_ID}/(?:verify|source|retry))")


class WorkspaceRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]{2,39}$")
    name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=15, max_length=256)

    @field_validator("name", mode="before")
    @classmethod
    def plain_name(cls, value: Any) -> str:
        if not isinstance(value, str) or any(ord(c) < 32 or c in "<>" for c in value):
            raise ValueError("Use a plain-text display name")
        return value.strip()


@dataclass
class Workspace:
    store: Store
    directory: Path


@dataclass
class WorkspaceContext:
    user: User
    workspace: Workspace


workspace_context: ContextVar[WorkspaceContext | None] = ContextVar(
    "marsense_personal_workspace", default=None
)


class WorkspaceManager:
    def __init__(self, settings: Settings, service: MissionService):
        self.enabled = settings.environment != "showcase" and not settings.read_only
        self.secure = settings.environment != "demo"
        self.origins = settings.cors_origins
        self.root = settings.runtime_dir / "personal_workspaces"
        self.service = service
        self.database_url = settings.database_url
        self.postgres = self.database_url.startswith(("postgresql://", "postgresql+psycopg://"))
        self.lock = Lock()
        self.signup_lock = Lock()
        self.accounts: Store | None = None
        self.auth: Auth | None = None
        self.workspaces: dict[str, Workspace] = {}
        self.signup_attempts: list[float] = []

    def require_enabled(self) -> None:
        if not self.enabled:
            raise HTTPException(404, "Personal workspaces are unavailable in this environment")

    def _accounts(self) -> tuple[Store, Auth]:
        self.require_enabled()
        with self.lock:
            if self.accounts is None or self.auth is None:
                self.root.mkdir(parents=True, exist_ok=True)
                auth = Auth("")
                # Nonexistent users run the same password verification as real accounts.
                auth.dummy_hash = password_hash(token_urlsafe(32))
                self.accounts = (
                    Store(self.database_url, "marsense_accounts") if self.postgres
                    else Store(f"sqlite:///{self.root / 'accounts.db'}")
                )
                self.auth = auth
            return self.accounts, self.auth

    def register(self, request: WorkspaceRegistration) -> tuple[User, str]:
        accounts, _ = self._accounts()
        with self.signup_lock:
            current = monotonic()
            self.signup_attempts = [t for t in self.signup_attempts if current - t < 300]
            if len(self.signup_attempts) >= 20:
                raise HTTPException(429, "Signup limit reached. Retry in a few minutes.")
            self.signup_attempts.append(current)
            with accounts.session(write=True) as session:
                existing = all_of(session, RegisteredAccount)
                if len(existing) >= MAX_ACCOUNTS:
                    raise HTTPException(429, "Personal workspace capacity reached.")
                if any(a.username.casefold() == request.username.casefold() for a in existing):
                    raise HTTPException(409, "Choose another username")
                account = RegisteredAccount(
                    id=identifier("account"),
                    username=request.username,
                    name=request.name,
                    role="MISSION_CONTROL",
                    password_hash=password_hash(request.password),
                )
                put(session, account)
                token = token_urlsafe(32)
                current_time = time()
                put(session, AuthSession(
                    id="session-" + hashlib.sha256(token.encode()).hexdigest(),
                    user_id=account.id,
                    expires_at=current_time + 8 * 3600,
                    last_seen=current_time,
                ))
                put(session, AuthAudit(
                    id=identifier("auth"), user_id=account.id, action="PERSONAL_WORKSPACE_CREATED",
                ))
                return account.as_user(), token

    def login(self, body: Login, ip: str) -> tuple[User, str]:
        accounts, auth = self._accounts()
        with accounts.session(write=True) as session:
            return auth.login(session, body, ip)

    def user(self, request: Request) -> User | None:
        self.require_enabled()
        token = request.cookies.get(WORKSPACE_COOKIE)
        if not token:
            return None
        accounts, auth = self._accounts()
        with accounts.session(write=True) as session:
            return auth.resolve(session, token)

    def logout(self, request: Request) -> None:
        self.require_enabled()
        token = request.cookies.get(WORKSPACE_COOKIE)
        if token:
            accounts, auth = self._accounts()
            with accounts.session(write=True) as session:
                auth.logout(session, token)

    def context(self, request: Request) -> WorkspaceContext:
        user = self.user(request)
        if user is None:
            raise HTTPException(401, "Authentication required")
        if not re.fullmatch(r"account-[a-f0-9]{32}", user.id):
            raise HTTPException(403, "Invalid personal workspace identity")
        with self.lock:
            workspace = self.workspaces.get(user.id)
            if workspace is None:
                directory = self.root / user.id
                directory.mkdir(parents=True, exist_ok=True)
                store = (
                    Store(self.database_url, "marsense_ws_" + user.id.removeprefix("account-"))
                    if self.postgres else Store(f"sqlite:///{directory / 'mission.db'}")
                )
                try:
                    with store.session(write=True) as session:
                        seed(session, self.service.slope_grid)
                except Exception:
                    store.engine.dispose()
                    raise
                workspace = Workspace(store, directory)
                self.workspaces[user.id] = workspace
        return WorkspaceContext(user, workspace)

    def close(self) -> None:
        with self.lock:
            for workspace in self.workspaces.values():
                workspace.store.engine.dispose()
            self.workspaces.clear()
            if self.accounts is not None:
                self.accounts.engine.dispose()
            self.accounts = None
            self.auth = None


class WorkspaceDataMiddleware:
    """Dispatch only an allowlisted set of mission endpoints to the owner's store."""

    def __init__(self, app: ASGIApp, manager: WorkspaceManager):
        self.app = app
        self.manager = manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(DATA_PREFIX + "/"):
            await self.app(scope, receive, send)
            return
        path = scope["path"].removeprefix(DATA_PREFIX)
        method = scope["method"]
        allowed = (
            method == "GET" and _GET_DATA.fullmatch(path)
            or method == "POST" and _POST_DATA.fullmatch(path)
        )
        if not allowed:
            await JSONResponse({"detail": "Personal workspace endpoint unavailable"}, 404)(
                scope, receive, send
            )
            return
        request = Request(scope)
        try:
            if method == "POST":
                check_origin(request, self.manager.origins)
            context = await run_in_threadpool(self.manager.context, request)
        except HTTPException as exc:
            await JSONResponse({"detail": exc.detail}, exc.status_code)(scope, receive, send)
            return
        inner = dict(scope)
        inner["path"] = "/api" + path
        inner["raw_path"] = inner["path"].encode("ascii")
        token = workspace_context.set(context)

        async def private_send(message: Message) -> None:
            if message['type'] == 'http.response.start':
                headers = MutableHeaders(scope=message)
                headers['Cache-Control'] = 'private, no-store'
                headers.add_vary_header('Cookie')
            await send(message)

        try:
            await self.app(inner, receive, private_send)
        finally:
            workspace_context.reset(token)


def create_workspace_router(manager: WorkspaceManager) -> APIRouter:
    router = APIRouter(prefix=WORKSPACE_PREFIX)

    def set_session(response: Response, token: str) -> None:
        response.set_cookie(
            WORKSPACE_COOKIE, token, httponly=True, secure=manager.secure,
            samesite="strict", max_age=8 * 3600, path=WORKSPACE_PREFIX,
        )
        response.headers["Cache-Control"] = "no-store"

    @router.post("/auth/signup", status_code=201)
    def signup(body: WorkspaceRegistration, request: Request, response: Response) -> dict[str, Any]:
        check_origin(request, manager.origins)
        user, token = manager.register(body)
        set_session(response, token)
        return {"user": user.model_dump(exclude={"password_hash"})}

    @router.post("/auth/login")
    def login(body: Login, request: Request, response: Response) -> dict[str, Any]:
        check_origin(request, manager.origins)
        user, token = manager.login(body, request.client.host if request.client else "unknown")
        set_session(response, token)
        return {"user": user.model_dump(exclude={"password_hash"})}

    @router.get("/auth/session")
    def session(request: Request, response: Response) -> dict[str, Any]:
        user = manager.user(request) if manager.enabled else None
        response.headers["Cache-Control"] = "no-store"
        return {
            "user": user.model_dump(exclude={"password_hash"}) if user else None,
            "required": True,
            "read_only": False,
            "environment": "production",
            "registration_enabled": False,
            "replay_enabled": False,
            "personal_workspace": True,
            "signup_enabled": manager.enabled,
        }

    @router.post("/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, bool]:
        check_origin(request, manager.origins)
        manager.logout(request)
        response.delete_cookie(
            WORKSPACE_COOKIE, path=WORKSPACE_PREFIX, secure=manager.secure,
            httponly=True, samesite="strict",
        )
        response.headers["Cache-Control"] = "no-store"
        return {"ok": True}

    return router


def enforce_asset_quota(directory: Path, incoming_bytes: int) -> None:
    originals = list((directory / "originals").glob("*.bin"))
    derivatives = list((directory / "uploads").glob("*.jpg"))
    stored_bytes = sum(p.stat().st_size for p in originals + derivatives)
    if len(originals) >= MAX_UPLOADS or stored_bytes + incoming_bytes > MAX_ASSET_BYTES:
        raise HTTPException(413, "Personal workspace storage limit reached (16 images / 64 MB)")
