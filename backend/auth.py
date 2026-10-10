"""Small server-side session store. No passwords or session tokens are persisted in plaintext."""

import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.domain import Entity
from backend.store import get, put


class User(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    username: str
    name: str
    role: Literal["ASTRONAUT", "MISSION_CONTROL", "ADMIN"]
    password_hash: str


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


class AuthSession(Entity):
    user_id: str
    expires_at: float
    last_seen: float
    revoked: bool = False


class AuthAudit(Entity):
    user_id: str | None
    action: str
    timestamp: float = Field(default_factory=time.time)


def password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=131072, r=8, p=1, maxmem=256 * 1024 * 1024
    ).hex()
    return f"scrypt$131072$8$1${salt}${digest}"


class Auth:
    cookie = "marsense_session"

    def __init__(self, users_file: str):
        self.users = (
            [User.model_validate(u) for u in json.loads(Path(users_file).read_text())]
            if users_file
            else []
        )
        if len({u.username for u in self.users}) != len(self.users) or len(
            {u.id for u in self.users}
        ) != len(self.users):
            raise ValueError("Duplicate authentication identity")
        self.failures: dict[str, list[float]] = {}
        self.lock = Lock()
        self.dummy_hash = password_hash(secrets.token_urlsafe(32)) if self.users else ""

    def login(self, session: Session, request: Login, ip: str) -> tuple[User, str]:
        with self.lock:
            return self._login(session, request, ip)

    def _login(self, session: Session, request: Login, ip: str) -> tuple[User, str]:
        current = time.time()
        key = hashlib.sha256(ip.encode()).hexdigest()
        self.failures = {
            k: [t for t in values if current - t < 300]
            for k, values in self.failures.items()
            if values and current - values[-1] < 300
        }
        attempts = self.failures.setdefault(key, [])
        if len(attempts) >= 5 or len(self.failures) > 4096:
            raise HTTPException(429, "Too many sign-in attempts; retry after five minutes")
        user = next((u for u in self.users if u.username == request.username), None)
        encoded = user.password_hash if user else self.dummy_hash
        try:
            algorithm, n, r, p, salt, _ = encoded.split("$")
            if (algorithm, n, r, p) != ("scrypt", "131072", "8", "1"):
                raise ValueError("Unsupported password hash")
            matches = hmac.compare_digest(password_hash(request.password, salt), encoded)
        except ValueError:
            matches = False
        if not matches or user is None:
            attempts.append(current)
            raise HTTPException(401, "Invalid username or password")
        attempts.clear()
        token = secrets.token_urlsafe(32)
        put(
            session,
            AuthSession(
                id="session-" + hashlib.sha256(token.encode()).hexdigest(),
                user_id=user.id,
                expires_at=current + 8 * 3600,
                last_seen=current,
            ),
        )
        put(session, AuthAudit(id="auth-" + secrets.token_hex(16), user_id=user.id, action="LOGIN"))
        return user, token

    def resolve(self, session: Session, token: str | None) -> User | None:
        if not token:
            return None
        try:
            record = get(
                session, AuthSession, "session-" + hashlib.sha256(token.encode()).hexdigest()
            )
        except KeyError:
            return None
        if (
            record.revoked
            or record.expires_at <= time.time()
            or time.time() - record.last_seen > 1800
        ):
            return None
        record.last_seen = time.time()
        put(session, record)
        return next((u for u in self.users if u.id == record.user_id), None)

    def logout(self, session: Session, token: str | None) -> None:
        if not token:
            return
        try:
            record = get(
                session, AuthSession, "session-" + hashlib.sha256(token.encode()).hexdigest()
            )
        except KeyError:
            return
        record.revoked = True
        put(session, record)
        put(
            session,
            AuthAudit(id="auth-" + secrets.token_hex(16), user_id=record.user_id, action="LOGOUT"),
        )


def check_origin(request: Request, allowed: list[str]) -> None:
    if request.headers.get("origin") not in allowed:
        raise HTTPException(403, "Mutation requires an approved browser origin")
