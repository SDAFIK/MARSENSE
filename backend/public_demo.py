"""Bounded, disposable guest workspaces. Never use the production Store."""

from _thread import LockType
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Lock
from time import monotonic
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.auth import check_origin
from backend.domain import (
    Evidence,
    EvidenceHistory,
    HumanDecision,
    InferenceAttempt,
    Interpretation,
    Observation,
    ObserveRequest,
    Snapshot,
    VerifyRequest,
    now,
)
from backend.knowledge import SourceDeclaration, declare_source, synthesis
from backend.seed import seed
from backend.service import MissionService
from backend.store import EntityRow, Store, all_of, get

DEMO_HEADER = "X-Marsense-Demo"
DEMO_REVIEWER = "Guest reviewer (simulation)"
MAX_SESSIONS = 32
SESSION_SECONDS = 3600
MAX_ACTIONS = 60


@dataclass
class Guest:
    store: Store
    directory: TemporaryDirectory[str]
    expires: float
    actions: int = 0
    active: int = 0
    lock: LockType = field(default_factory=Lock)

    def close(self) -> None:
        self.store.engine.dispose()
        self.directory.cleanup()


class GuestPool:
    def __init__(self, service: MissionService):
        self.service = service
        self.guests: dict[str, Guest] = {}
        self.lock = Lock()

    def _prune(self) -> None:
        for key, guest in list(self.guests.items()):
            if guest.expires <= monotonic() and guest.active == 0:
                guest.close()
                del self.guests[key]

    def start(self) -> str:
        with self.lock:
            self._prune()
            if len(self.guests) >= MAX_SESSIONS:
                raise HTTPException(429, "Demo capacity reached. Please try again later.")
            directory = TemporaryDirectory(prefix="marsense-guest-")
            store: Store | None = None
            try:
                store = Store(f"sqlite:///{Path(directory.name) / 'guest.db'}")
                with store.session(write=True) as session:
                    seed(session, self.service.slope_grid)
                token = token_urlsafe(32)
                self.guests[token] = Guest(store, directory, monotonic() + SESSION_SECONDS)
                return token
            except Exception:
                if store is not None:
                    store.engine.dispose()
                directory.cleanup()
                raise

    @contextmanager
    def lease(self, token: str, mutation: bool = False) -> Iterator[Guest]:
        with self.lock:
            self._prune()
            guest = self.guests.get(token)
            if guest is None or guest.expires <= monotonic():
                raise HTTPException(401, "Demo expired. Return home and launch a new demo.")
            guest.active += 1
        try:
            with guest.lock:
                if guest.expires <= monotonic():
                    raise HTTPException(401, "Demo expired. Return home and launch a new demo.")
                if mutation:
                    if guest.actions >= MAX_ACTIONS:
                        raise HTTPException(429, "Demo action limit reached. Exit and relaunch.")
                    guest.actions += 1
                yield guest
        finally:
            with self.lock:
                guest.active -= 1
                self._prune()

    def close(self) -> None:
        with self.lock:
            for guest in self.guests.values():
                guest.close()
            self.guests.clear()


def create_demo_router(service: MissionService, origins: list[str]) -> tuple[APIRouter, GuestPool]:
    pool = GuestPool(service)

    def no_store(response: Response) -> None:
        response.headers["Cache-Control"] = "no-store"

    router = APIRouter(prefix="/api/public-demo", dependencies=[Depends(no_store)])

    def token_for(request: Request) -> str:
        token = request.headers.get(DEMO_HEADER, "")
        if len(token) != 43:
            raise HTTPException(401, "Launch a private guest demo first.")
        return token

    @contextmanager
    def access(request: Request, write: bool = False) -> Iterator[Session]:
        if write:
            check_origin(request, origins)
        with pool.lease(token_for(request), mutation=write) as guest:
            with guest.store.session(write=write) as session:
                yield session

    @router.post("/start", status_code=201)
    def start(request: Request) -> dict[str, str | int]:
        check_origin(request, origins)
        return {"token": pool.start(), "expires_in": SESSION_SECONDS}

    @router.get("/auth/session")
    def guest_session(request: Request) -> dict[str, Any]:
        with access(request):
            return {
                "user": {"name": DEMO_REVIEWER, "role": "MISSION_CONTROL"},
                "required": False,
                "read_only": False,
                "registration_enabled": False,
                "environment": "showcase",
                "replay_enabled": True,
                "public_demo": True,
            }

    @router.post("/auth/logout")
    def guest_logout(request: Request) -> dict[str, bool]:
        check_origin(request, origins)
        with pool.lease(token_for(request)) as guest:
            guest.expires = 0
        return {"ok": True}

    @router.get("/missions/{mission_id}", response_model=Snapshot)
    def snapshot(mission_id: str, request: Request) -> Snapshot:
        with access(request) as session:
            return service.snapshot(session, mission_id)

    @router.get("/missions/{mission_id}/alternatives")
    def alternatives(mission_id: str, request: Request) -> dict[str, Any]:
        with access(request) as session:
            return service.alternatives(session, mission_id)

    @router.post("/observations/demo", response_model=Evidence)
    def observe(body: ObserveRequest, request: Request) -> Evidence:
        with access(request, write=True) as session:
            return service.demo(session, body)

    @router.post("/observations/upload")
    def no_upload(request: Request) -> None:
        with access(request):
            raise HTTPException(403, "Guest demos use curated observations. Sign in to upload.")

    @router.get("/evidence/{evidence_id}", response_model=Evidence)
    def evidence_detail(evidence_id: str, request: Request) -> Evidence:
        with access(request) as session:
            return get(session, Evidence, evidence_id)

    @router.get("/evidence/{evidence_id}/ancestry")
    def ancestry(evidence_id: str, request: Request) -> dict[str, Any]:
        with access(request) as session:
            return synthesis(session, evidence_id)

    @router.get("/evidence/{evidence_id}/history", response_model=EvidenceHistory)
    def history(evidence_id: str, request: Request) -> EvidenceHistory:
        with access(request) as session:
            evidence = get(session, Evidence, evidence_id)
            decisions = sorted(
                [d for d in all_of(session, HumanDecision) if d.evidence_id == evidence_id],
                key=lambda d: d.timestamp,
            )
            return EvidenceHistory(
                decisions=decisions,
                interpretations=sorted(
                    [i for i in all_of(session, Interpretation) if i.evidence_id == evidence_id],
                    key=lambda i: i.timestamp,
                ),
                legacy_decision=not decisions and evidence.verification_note is not None,
                inference_attempts=sorted(
                    [a for a in all_of(session, InferenceAttempt) if a.evidence_id == evidence_id],
                    key=lambda a: a.timestamp,
                ),
            )

    @router.get("/observations/{observation_id}", response_model=Observation)
    def observation_detail(observation_id: str, request: Request) -> Observation:
        with access(request) as session:
            return get(session, Observation, observation_id)

    @router.post("/evidence/{evidence_id}/source")
    def source(
        evidence_id: str, body: SourceDeclaration, request: Request,
    ) -> SourceDeclaration:
        with access(request, write=True) as session:
            return declare_source(session, body.model_copy(update={
                "id": "source-" + evidence_id,
                "evidence_id": evidence_id,
                "reviewer": DEMO_REVIEWER,
                "timestamp": now(),
            }))

    @router.post("/evidence/{evidence_id}/verify", response_model=Evidence)
    def verify(evidence_id: str, body: VerifyRequest, request: Request) -> Evidence:
        with access(request, write=True) as session:
            return service.verify(
                session, evidence_id, body.model_copy(update={"reviewer": DEMO_REVIEWER}),
            )

    @router.post("/showcase/reset")
    def reset(request: Request) -> dict[str, bool]:
        with access(request, write=True) as session:
            session.execute(delete(EntityRow))
            seed(session, service.slope_grid)
        return {"ok": True}

    return router, pool
