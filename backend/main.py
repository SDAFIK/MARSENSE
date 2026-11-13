import hashlib
import hmac
import io
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Response, UploadFile
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy import delete, text
from sqlalchemy.orm import Session
from starlette.requests import Request

from ai.perception import Perception
from backend.auth import Auth, AuthAudit, InviteRequest, Login, Registration, User, check_origin
from backend.cloud_assets import enforce_cloud_quota, put_asset, read_asset
from backend.config import ROOT, Settings
from backend.domain import (
    Evidence,
    Mission,
    EvidenceHistory,
    Footprint,
    HumanDecision,
    InferenceAttempt,
    Interpretation,
    ModelOutput,
    Observation,
    ObserveRequest,
    RetryRequest,
    Snapshot,
    VerifyRequest,
)
from backend.knowledge import SourceDeclaration, declare_source, synthesis
from backend.public_demo import create_demo_router
from backend.routing import load_slope
from backend.seed import seed
from backend.service import MissionService, identifier
from backend.store import EntityRow, Store, all_of, get, put
from backend.workspaces import (
    DATA_PREFIX,
    WorkspaceDataMiddleware,
    WorkspaceManager,
    create_workspace_router,
    enforce_asset_quota,
    workspace_context,
)

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","event":"%(message)s"}')
logger = logging.getLogger(__name__)
Image.MAX_IMAGE_PIXELS = 16_000_000


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    is_sqlite = settings.database_url.startswith("sqlite:///")
    is_postgres = settings.database_url.startswith(("postgresql://", "postgresql+psycopg://"))
    if not (is_sqlite or is_postgres):
        raise ValueError("Unsupported database backend")
    database_path = settings.database_url.removeprefix("sqlite:///")
    store: Store
    service = MissionService(Perception(settings.model_path), load_slope(settings.slope_path))
    demo_router, guest_pool = create_demo_router(service, settings.cors_origins)
    workspace_manager = WorkspaceManager(settings, service)
    auth = Auth(settings.auth_users_file)
    if settings.environment == "showcase":
        auth.cookie = "marsense_showcase_session"
    authentication_required = settings.auth_required or settings.environment != "demo"
    registration_enabled = (
        settings.environment == "production" and (bool(settings.auth_users_file) or is_postgres)
        and not settings.read_only
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        nonlocal store, auth
        if is_sqlite and database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        store = Store(settings.database_url)
        application.state.store = store
        try:
            with store.session(write=True) as session:
                if store.postgres and settings.environment == "production":
                    if not all_of(session, Mission):
                        raise ValueError("Cloud production requires a verified mission migration")
                    if not settings.auth_users_file and not settings.read_only:
                        users = [
                            User.model_validate(payload) for payload in session.scalars(
                                text("SELECT payload FROM marsense.bootstrap_users ORDER BY id")
                            )
                        ]
                        if not users:
                            raise ValueError("Cloud production requires migrated operator identities")
                        auth = Auth("", users=users)
                else:
                    seed(session, service.slope_grid)
            yield
        finally:
            workspace_manager.close()
            guest_pool.close()
            store.engine.dispose()

    app = FastAPI(title="MARSENSE", version="1.0.0", lifespan=lifespan)
    app.include_router(demo_router)
    app.include_router(create_workspace_router(workspace_manager))
    app.add_middleware(WorkspaceDataMiddleware, manager=workspace_manager)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization", "X-Marsense-Demo"],
    )

    def mission_store() -> Store:
        context = workspace_context.get()
        return context.workspace.store if context is not None else store

    def mission_runtime() -> Path:
        context = workspace_context.get()
        return context.workspace.directory if context is not None else settings.runtime_dir

    def mission_api_prefix() -> str:
        return DATA_PREFIX if workspace_context.get() is not None else "/api"

    def authorize(
        request: Request, authorization: Annotated[str | None, Header()] = None
    ) -> User | None:
        mutation = request.method not in {"GET", "HEAD", "OPTIONS"}
        if mutation and settings.read_only:
            raise HTTPException(403, "Read-only demonstration")
        context = workspace_context.get()
        if context is not None:
            if mutation:
                check_origin(request, settings.cors_origins)
            return context.user
        with store.session(write=True) as session:
            user = auth.resolve(session, request.cookies.get(auth.cookie))
        if user and mutation:
            check_origin(request, settings.cors_origins)
            if request.url.path.endswith(("/verify", "/source")) and user.role not in {
                "MISSION_CONTROL",
                "ADMIN",
            }:
                raise HTTPException(403, "Mission Control or Admin review role required")
        if authentication_required and not user:
            # Legacy service token is read-only; it cannot impersonate a human reviewer.
            token_read = (
                not mutation
                and bool(settings.api_token)
                and hmac.compare_digest(authorization or "", f"Bearer {settings.api_token}")
            )
            if not token_read:
                raise HTTPException(401, "Authentication required")
        return user

    protected = [Depends(authorize)]

    def require_admin(user: User | None) -> User:
        if not registration_enabled:
            raise HTTPException(404, "Account registration is unavailable in this environment")
        if not user or user.role != "ADMIN":
            raise HTTPException(403, "Administrator access required")
        return user

    @app.post("/api/auth/register", status_code=201)
    def register(body: Registration, request: Request, response: Response) -> dict[str, Any]:
        if not registration_enabled:
            raise HTTPException(404, "Account registration is unavailable in this environment")
        check_origin(request, settings.cors_origins)
        with store.session(write=True) as session:
            user = auth.register(
                session, body, request.client.host if request.client else "unknown"
            )
        response.headers["Cache-Control"] = "no-store"
        return {"user": user.model_dump(exclude={"password_hash"})}

    @app.get("/api/auth/admin", dependencies=protected)
    def account_admin(
        response: Response, user: User | None = Depends(authorize)
    ) -> dict[str, Any]:
        require_admin(user)
        response.headers["Cache-Control"] = "no-store"
        with store.session() as session:
            return auth.admin_snapshot(session)

    @app.post("/api/auth/invitations", dependencies=protected, status_code=201)
    def create_invitation(
        body: InviteRequest, response: Response, user: User | None = Depends(authorize)
    ) -> dict[str, Any]:
        admin = require_admin(user)
        response.headers["Cache-Control"] = "no-store"
        with store.session(write=True) as session:
            return auth.issue_invite(session, admin, body)

    @app.post("/api/auth/invitations/{invite_id}/revoke", dependencies=protected)
    def revoke_invitation(
        invite_id: str, user: User | None = Depends(authorize)
    ) -> dict[str, bool]:
        admin = require_admin(user)
        with store.session(write=True) as session:
            auth.revoke_invite(session, admin, invite_id)
        return {"ok": True}

    @app.post("/api/auth/accounts/{account_id}/disable", dependencies=protected)
    def disable_account(account_id: str, user: User | None = Depends(authorize)) -> dict[str, bool]:
        admin = require_admin(user)
        with store.session(write=True) as session:
            auth.disable_account(session, admin, account_id)
        return {"ok": True}

    @app.post("/api/auth/login")
    def login(body: Login, request: Request, response: Response) -> dict[str, Any]:
        check_origin(request, settings.cors_origins)
        with store.session(write=True) as session:
            user, token = auth.login(
                session, body, request.client.host if request.client else "unknown"
            )
        response.set_cookie(
            auth.cookie,
            token,
            httponly=True,
            secure=settings.environment != "demo",
            samesite="strict",
            max_age=8 * 3600,
            path="/",
        )
        response.headers["Cache-Control"] = "no-store"
        return {"user": user.model_dump(exclude={"password_hash"})}

    @app.get("/api/auth/session")
    def auth_session(request: Request, response: Response) -> dict[str, Any]:
        with store.session(write=True) as session:
            user = auth.resolve(session, request.cookies.get(auth.cookie))
        response.headers["Cache-Control"] = "no-store"
        return {
            "user": user.model_dump(exclude={"password_hash"}) if user else None,
            "required": authentication_required,
            "read_only": settings.read_only,
            "registration_enabled": registration_enabled,
            "environment": settings.environment,
            "replay_enabled": (
                settings.environment in {"demo", "showcase"} and not settings.read_only
            ),
        }

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, bool]:
        check_origin(request, settings.cors_origins)
        with store.session(write=True) as session:
            auth.logout(session, request.cookies.get(auth.cookie))
        response.delete_cookie(
            auth.cookie,
            path="/",
            secure=settings.environment != "demo",
            httponly=True,
            samesite="strict",
        )
        return {"ok": True}

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> Response:
        if request.url.path.startswith(("/api/auth/", "/api/workspaces/auth/")):
            # FastAPI's default validation detail may include the original secret input.
            return JSONResponse(status_code=422, content={"detail": "Invalid authentication input"})
        return await request_validation_exception_handler(request, error)

    @app.exception_handler(KeyError)
    async def missing(_: Request, __: KeyError) -> JSONResponse:
        return JSONResponse(
            status_code=404, content={"detail": "Requested mission or evidence does not exist"}
        )

    @app.exception_handler(ValueError)
    async def invalid(_: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(Exception)
    async def internal(_: Request, error: Exception) -> JSONResponse:
        logger.error("request_failed", exc_info=error)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Operation failed. Stored evidence is preserved; "
                "retry or inspect the mission memory."
            },
        )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "environment": settings.environment,
            "cache_available": (ROOT / "data/nasa/jezero-ctx.png").exists(),
        }

    @app.get("/api/missions/{mission_id}", response_model=Snapshot, dependencies=protected)
    def snapshot(mission_id: str) -> Snapshot:
        with mission_store().session() as session:
            return service.snapshot(session, mission_id)

    @app.post("/api/observations/demo", response_model=Evidence, dependencies=protected)
    def demo(request: ObserveRequest) -> Evidence:
        if settings.environment not in {"demo", "showcase"}:
            raise HTTPException(404, "Demo replay is disabled")
        with mission_store().session(write=True) as session:
            return service.demo(session, request)

    @app.post("/api/showcase/reset", dependencies=protected)
    def reset_showcase(user: User | None = Depends(authorize)) -> dict[str, bool]:
        if settings.environment != "showcase":
            raise HTTPException(404, "Showcase reset unavailable")
        if not user or user.role != "ADMIN":
            raise HTTPException(403, "Showcase administrator required")
        with mission_store().session(write=True) as session:
            session.execute(
                delete(EntityRow).where(EntityRow.kind.not_in([
                    "AuthSession", "AuthAudit", "RegisteredAccount", "RegistrationInvite"
                ]))
            )
            seed(session, service.slope_grid)
            put(session, AuthAudit(id=identifier("auth"), user_id=user.id, action="SHOWCASE_RESET"))
        return {"ok": True}

    @app.get("/api/evidence/{evidence_id}", response_model=Evidence, dependencies=protected)
    def evidence_detail(evidence_id: str) -> Evidence:
        with mission_store().session() as session:
            return get(session, Evidence, evidence_id)

    @app.get("/api/evidence/{evidence_id}/ancestry", dependencies=protected)
    def ancestry(evidence_id: str) -> dict[str, Any]:
        with mission_store().session() as session:
            return synthesis(session, evidence_id)

    @app.post("/api/evidence/{evidence_id}/source", dependencies=protected)
    def source_declaration(
        evidence_id: str, request: SourceDeclaration, user: User | None = Depends(authorize)
    ) -> SourceDeclaration:
        from backend.domain import now

        with mission_store().session(write=True) as session:
            return declare_source(
                session,
                request.model_copy(
                    update={
                        "id": "source-" + evidence_id,
                        "evidence_id": evidence_id,
                        "timestamp": now(),
                        "reviewer": user.name if user else request.reviewer,
                    }
                ),
            )

    @app.get(
        "/api/evidence/{evidence_id}/history",
        response_model=EvidenceHistory,
        dependencies=protected,
    )
    def evidence_history(evidence_id: str) -> EvidenceHistory:
        with mission_store().session() as session:
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

    @app.get(
        "/api/observations/{observation_id}", response_model=Observation, dependencies=protected
    )
    def observation_detail(observation_id: str) -> Observation:
        with mission_store().session() as session:
            return get(session, Observation, observation_id)

    @app.get("/api/observations/{observation_id}/original", dependencies=protected)
    def original_asset(observation_id: str) -> Response:
        with mission_store().session() as session:
            observation = get(session, Observation, observation_id)
        name = observation.raw_asset_reference.rsplit("/", 1)[-1]
        if not observation.original_asset_reference or not (
            name.startswith("upload-")
            and name.endswith(".jpg")
            and len(name) == 43
            and all(c in "0123456789abcdef" for c in name[7:-4])
        ):
            raise HTTPException(404, "Original upload is unavailable for this observation")
        active = mission_store()
        if active.postgres:
            with active.session() as session:
                content = read_asset(session, active.schema, name.replace(".jpg", ".bin"))
            if content is None:
                raise HTTPException(404, "Original upload unavailable; derivative evidence remains")
            return Response(
                content, media_type="application/octet-stream",
                headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
                         "Content-Disposition": f'attachment; filename="{name}.original"'},
            )
        path = mission_runtime() / "originals" / name.replace(".jpg", ".bin")
        if not path.is_file():
            raise HTTPException(404, "Original upload unavailable; derivative evidence remains")
        return FileResponse(
            path,
            media_type="application/octet-stream",
            filename=name + ".original",
            headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
        )

    @app.post("/api/evidence/{evidence_id}/verify", response_model=Evidence, dependencies=protected)
    def verify(
        evidence_id: str, request: VerifyRequest, user: User | None = Depends(authorize)
    ) -> Evidence:
        with mission_store().session(write=True) as session:
            if user:
                request = request.model_copy(update={"reviewer": user.name})
            return service.verify(session, evidence_id, request, user_id=user.id if user else None)

    def safe_infer(content: bytes) -> ModelOutput:
        try:
            return service.perception.infer(content)
        except Exception:
            logger.exception("ground_inference_failed")
            return Perception.unavailable(
                "Inference unavailable; original image saved for retry or human review."
            )

    @app.post("/api/observations/upload", response_model=Evidence, dependencies=protected)
    async def upload(
        file: Annotated[UploadFile, File()],
        footprint: Annotated[str, Form()],
        mission_id: Annotated[str, Form()] = "eva-01",
        details: Annotated[str, Form(max_length=500)] = "",
    ) -> Evidence:
        if settings.environment == "showcase":
            raise HTTPException(403, "Showcase uses curated replay; uploads belong in production")
        if file.content_type not in {"image/jpeg", "image/png"}:
            raise HTTPException(415, "Only JPEG and PNG images are supported")
        content = await file.read(settings.max_upload_bytes + 1)
        await file.close()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(413, "Image exceeds the 8 MB upload limit")
        original_content = content
        details = details.strip()
        if any(ord(c) < 32 and c not in "\n\t" for c in details) or any(
            c in details for c in "<>"
        ):
            raise ValueError("Observation details must be plain text")
        try:
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG"} or image.width * image.height > 16_000_000:
                    raise ValueError("Unsupported image or excessive dimensions")
                image.verify()
            geometry = Footprint.model_validate(json.loads(footprint))
        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
            json.JSONDecodeError,
        ) as error:
            raise HTTPException(422, "Invalid image or footprint metadata") from error
        # Decode and re-encode: strip user metadata and never execute uploaded content.
        with Image.open(io.BytesIO(content)) as image:
            clean = io.BytesIO()
            image.convert("RGB").save(clean, format="JPEG", quality=90)
        content = clean.getvalue()
        active = mission_store()
        if workspace_context.get() is not None and not active.postgres:
            enforce_asset_quota(mission_runtime(), len(content) + len(original_content))
        output = safe_infer(content)
        asset_id = identifier("upload") + ".jpg"

        def record(session: Session) -> Evidence:
            return service.observe(
                session,
                mission_id,
                geometry,
                output,
                f"{mission_api_prefix()}/assets/{asset_id}",
                hashlib.sha256(content).hexdigest(),
                "ground",
                "Astronaut-uploaded image",
                "Footprint supplied manually in local meters; "
                "image is not independently geolocated. Display/model input is a sanitized "
                "JPEG derivative; original bytes/hash are retained separately."
                + (f" Observer note (unverified): {details}" if details else ""),
                original_digest=hashlib.sha256(original_content).hexdigest(),
            )

        if active.postgres:
            with active.session(write=True) as session:
                enforce_cloud_quota(session, active.schema, len(content) + len(original_content))
                put_asset(session, active.schema, asset_id, content)
                put_asset(session, active.schema, asset_id.replace(".jpg", ".bin"), original_content)
                return record(session)

        upload_dir = mission_runtime() / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        asset_path = upload_dir / asset_id
        asset_path.write_bytes(content)
        original_dir = mission_runtime() / "originals"
        original_dir.mkdir(parents=True, exist_ok=True)
        original_path = original_dir / asset_id.replace(".jpg", ".bin")
        try:
            original_path.write_bytes(original_content)
            with active.session(write=True) as session:
                return record(session)
        except Exception:
            asset_path.unlink(missing_ok=True)
            original_path.unlink(missing_ok=True)
            raise

    @app.post("/api/evidence/{evidence_id}/retry", response_model=Evidence, dependencies=protected)
    def retry_inference(
        evidence_id: str, body: RetryRequest, user: User | None = Depends(authorize)
    ) -> Evidence:
        if settings.environment == "showcase":
            raise HTTPException(403, "Showcase uses curated replay")
        attempt_id = f"inference-{evidence_id}-{body.request_id}"
        with mission_store().session(write=True) as session:
            evidence = get(session, Evidence, evidence_id)
            try:
                get(session, InferenceAttempt, attempt_id)
            except KeyError:
                pass
            else:
                return evidence
            if (
                evidence.source_type != "ground"
                or not evidence.observation_id
                or evidence.verification_state.value not in {"PROVISIONAL", "NEEDS_MORE_EVIDENCE"}
                or evidence.model_output is None
                or evidence.model_output.engine != "unavailable"
            ):
                raise ValueError(
                    "Only pending ground evidence with unavailable inference can retry"
                )
            observation = get(session, Observation, evidence.observation_id)
            name = observation.raw_asset_reference.rsplit("/", 1)[-1]
            if not (
                name.startswith("upload-") and name.endswith(".jpg") and len(name) == 43
                and all(c in "0123456789abcdef" for c in name[7:-4])
            ):
                raise HTTPException(404, "Saved ground image unavailable")
            active = mission_store()
            if active.postgres:
                content = read_asset(session, active.schema, name)
                original = read_asset(session, active.schema, name.replace(".jpg", ".bin"))
            else:
                path = mission_runtime() / "uploads" / name
                original_path = mission_runtime() / "originals" / name.replace(".jpg", ".bin")
                content = path.read_bytes() if path.is_file() else None
                original = original_path.read_bytes() if original_path.is_file() else None
            if content is None or original is None:
                raise HTTPException(404, "Saved image or original unavailable; evidence retained")
            if (
                hashlib.sha256(content).hexdigest() != observation.model_input_sha256
                or hashlib.sha256(original).hexdigest() != observation.asset_sha256
            ):
                raise HTTPException(409, "Saved image integrity check failed; evidence retained")
            return service.retry_inference(
                session, evidence, safe_infer(content), attempt_id, user.id if user else None
            )

    @app.get("/api/assets/{asset_id}")
    def asset(
        asset_id: str, request: Request, authorization: Annotated[str | None, Header()] = None
    ) -> Response:
        known = {"jezero-ctx.png", "ground-navcam.jpg", "jezero-hirise.png"}
        if asset_id in known:
            path = ROOT / "data/nasa" / asset_id
        elif asset_id in {"navcam-preview.png", "mastcamz-preview.png"}:
            path = ROOT / "data/processed" / asset_id
        elif asset_id == "crism-preview.png":
            path = ROOT / "data/nasa/crism/frt000047a3_07_brtanj_mtr3.png"
        elif asset_id.startswith("upload-") and asset_id.endswith(".jpg") and len(asset_id) == 43:
            authorize(request, authorization)
            if not all(c in "0123456789abcdef" for c in asset_id[7:-4]):
                raise HTTPException(404, "Asset not found")
            active = mission_store()
            if active.postgres:
                with active.session() as session:
                    content = read_asset(session, active.schema, asset_id)
                if content is None:
                    raise HTTPException(404, "Cached asset unavailable; mission evidence remains usable")
                return Response(
                    content, media_type="image/jpeg",
                    headers={"Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"},
                )
            path = mission_runtime() / "uploads" / asset_id
        else:
            raise HTTPException(404, "Asset not found")
        if not path.is_file():
            raise HTTPException(404, "Cached asset unavailable; mission evidence remains usable")
        return FileResponse(
            path,
            headers={
                "Cache-Control": "public, max-age=3600"
                if asset_id in known
                else "private, no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    return app


app = create_app()
