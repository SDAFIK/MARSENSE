"""Small server-side session store. No passwords or session tokens are persisted in plaintext."""

import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Any, Literal

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from backend.domain import Entity
from backend.store import all_of, get, put


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


class RegisteredAccount(Entity):
    username: str
    name: str
    role: Literal["ASTRONAUT", "MISSION_CONTROL"]
    password_hash: str
    created_at: float = Field(default_factory=time.time)
    disabled: bool = False

    def as_user(self) -> User:
        return User(
            id=self.id, username=self.username, name=self.name,
            role=self.role, password_hash=self.password_hash,
        )


class RegistrationInvite(Entity):
    role: Literal["ASTRONAUT", "MISSION_CONTROL"]
    created_by: str
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    used_by: str | None = None
    revoked: bool = False


class InviteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["ASTRONAUT", "MISSION_CONTROL"] = "ASTRONAUT"


class Registration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]{2,39}$")
    name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=15, max_length=256)

    @field_validator("name", mode="before")
    @classmethod
    def plain_name(cls, value: Any) -> str:
        if not isinstance(value, str) or any(ord(c) < 32 or c in "<>" for c in value):
            raise ValueError("Use a plain-text display name")
        return value.strip()


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
        self.dummy_hash = password_hash(secrets.token_urlsafe(32)) if users_file else ""
        self.registration_failures: dict[str, list[float]] = {}

    def available_users(self, session: Session) -> list[User]:
        return self.users + [
            account.as_user()
            for account in all_of(session, RegisteredAccount) if not account.disabled
        ]

    def admin_snapshot(self, session: Session) -> dict[str, Any]:
        return {
            "accounts": [
                account.model_dump(exclude={"password_hash"})
                for account in all_of(session, RegisteredAccount)
            ],
            "invitations": [
                invite.model_dump() for invite in all_of(session, RegistrationInvite)
            ],
        }

    def issue_invite(
        self, session: Session, admin: User, request: InviteRequest
    ) -> dict[str, Any]:
        current = time.time()
        recent = [
            invite for invite in all_of(session, RegistrationInvite)
            if invite.created_at > current - 3600
        ]
        if len(recent) >= 20:
            raise HTTPException(429, "Invitation limit reached; retry later")
        token = secrets.token_urlsafe(32)
        invite = RegistrationInvite(
            id="invite-" + hashlib.sha256(token.encode()).hexdigest(),
            role=request.role, created_by=admin.id, expires_at=current + 24 * 3600,
        )
        put(session, invite)
        put(session, AuthAudit(
            id="auth-" + secrets.token_hex(16), user_id=admin.id, action="INVITE_ISSUED"
        ))
        return {"token": token, "role": invite.role, "expires_at": invite.expires_at}

    def register(self, session: Session, request: Registration, ip: str) -> User:
        with self.lock:
            current = time.time()
            key = hashlib.sha256(ip.encode()).hexdigest()
            self.registration_failures = {
                k: [t for t in values if current - t < 300]
                for k, values in self.registration_failures.items()
                if values and current - values[-1] < 300
            }
            failures = self.registration_failures.setdefault(key, [])
            if len(failures) >= 5 or len(self.registration_failures) > 4096:
                raise HTTPException(429, "Too many registration attempts; retry later")
            invite_id = "invite-" + hashlib.sha256(request.token.encode()).hexdigest()
            invite: RegistrationInvite | None
            try:
                invite = get(session, RegistrationInvite, invite_id)
            except KeyError:
                invite = None
            if not invite or invite.revoked or invite.used_by or invite.expires_at <= current:
                failures.append(current)
                raise HTTPException(400, "Invitation is invalid, expired or already used")
            reserved = {u.username.casefold() for u in self.users}
            reserved.update(a.username.casefold() for a in all_of(session, RegisteredAccount))
            if request.username.casefold() in reserved:
                failures.append(current)
                raise HTTPException(409, "Choose another username")
            account = RegisteredAccount(
                id="account-" + secrets.token_hex(16), username=request.username,
                name=request.name, role=invite.role, password_hash=password_hash(request.password),
            )
            put(session, account)
            invite.used_by = account.id
            put(session, invite)
            put(session, AuthAudit(
                id="auth-" + secrets.token_hex(16), user_id=account.id,
                action="INVITE_REGISTERED",
            ))
            failures.clear()
            return account.as_user()

    def revoke_invite(self, session: Session, admin: User, invite_id: str) -> None:
        invite = get(session, RegistrationInvite, invite_id)
        if invite.used_by:
            raise HTTPException(409, "Invitation already redeemed; disable its account instead")
        if not invite.revoked:
            invite.revoked = True
            put(session, invite)
            put(session, AuthAudit(
                id="auth-" + secrets.token_hex(16), user_id=admin.id,
                action="INVITE_REVOKED",
            ))

    def disable_account(self, session: Session, admin: User, account_id: str) -> None:
        account = get(session, RegisteredAccount, account_id)
        if not account.disabled:
            account.disabled = True
            put(session, account)
            put(session, AuthAudit(
                id="auth-" + secrets.token_hex(16), user_id=admin.id,
                action="REGISTERED_ACCOUNT_DISABLED:" + account.id,
            ))

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
        user = next(
            (u for u in self.available_users(session) if u.username == request.username), None
        )
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
        user = next((u for u in self.available_users(session) if u.id == record.user_id), None)
        if user is None:
            return None
        record.last_seen = time.time()
        put(session, record)
        return user

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
