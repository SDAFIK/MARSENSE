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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError
from starlette.requests import Request

from ai.perception import Perception
from backend.auth import Auth, Login, User, check_origin
from backend.config import ROOT, Settings
from backend.domain import (
    Evidence,
    EvidenceHistory,
    Footprint,
    HumanDecision,
    Interpretation,
    Observation,
    ObserveRequest,
    Snapshot,
    VerifyRequest,
)
from backend.knowledge import SourceDeclaration, declare_source, synthesis
from backend.routing import load_slope
from backend.seed import seed
from backend.service import MissionService, identifier
from backend.store import Store, all_of, get

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","event":"%(message)s"}')
logger = logging.getLogger(__name__)
Image.MAX_IMAGE_PIXELS = 16_000_000


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if not settings.database_url.startswith("sqlite:///"):
        raise ValueError(
            "This deterministic deployment supports SQLite; PostGIS is a documented extension"
        )
    database_path = settings.database_url.removeprefix("sqlite:///")
    store: Store
    service = MissionService(Perception(settings.model_path), load_slope(settings.slope_path))
    auth = Auth(settings.auth_users_file)
    authentication_required = settings.auth_required or settings.environment == "production"

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        nonlocal store
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        store = Store(settings.database_url)
        application.state.store = store
        try:
            with store.session(write=True) as session:
                seed(session, service.slope_grid)
            yield
        finally:
            store.engine.dispose()

    app = FastAPI(title="MARSENSE", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    def authorize(
        request: Request, authorization: Annotated[str | None, Header()] = None
    ) -> User | None:
        mutation = request.method not in {"GET", "HEAD", "OPTIONS"}
        if mutation and settings.read_only:
            raise HTTPException(403, "Read-only demonstration")
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
            secure=settings.environment == "production",
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
        }

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, bool]:
        check_origin(request, settings.cors_origins)
        with store.session(write=True) as session:
            auth.logout(session, request.cookies.get(auth.cookie))
        response.delete_cookie(
            auth.cookie,
            path="/",
            secure=settings.environment == "production",
            httponly=True,
            samesite="strict",
        )
        return {"ok": True}

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
        with store.session() as session:
            return service.snapshot(session, mission_id)

    @app.post("/api/observations/demo", response_model=Evidence, dependencies=protected)
    def demo(request: ObserveRequest) -> Evidence:
        if settings.environment != "demo":
            raise HTTPException(404, "Demo replay is disabled")
        with store.session(write=True) as session:
            return service.demo(session, request)

    @app.get("/api/evidence/{evidence_id}", response_model=Evidence, dependencies=protected)
    def evidence_detail(evidence_id: str) -> Evidence:
        with store.session() as session:
            return get(session, Evidence, evidence_id)

    @app.get("/api/evidence/{evidence_id}/ancestry", dependencies=protected)
    def ancestry(evidence_id: str) -> dict[str, Any]:
        with store.session() as session:
            return synthesis(session, evidence_id)

    @app.post("/api/evidence/{evidence_id}/source", dependencies=protected)
    def source_declaration(
        evidence_id: str, request: SourceDeclaration, user: User | None = Depends(authorize)
    ) -> SourceDeclaration:
        from backend.domain import now

        with store.session(write=True) as session:
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
        with store.session() as session:
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
            )

    @app.get(
        "/api/observations/{observation_id}", response_model=Observation, dependencies=protected
    )
    def observation_detail(observation_id: str) -> Observation:
        with store.session() as session:
            return get(session, Observation, observation_id)

    @app.get("/api/observations/{observation_id}/original", dependencies=protected)
    def original_asset(observation_id: str) -> FileResponse:
        with store.session() as session:
            observation = get(session, Observation, observation_id)
        name = observation.raw_asset_reference.rsplit("/", 1)[-1]
        if not observation.original_asset_reference or not (
            name.startswith("upload-")
            and name.endswith(".jpg")
            and len(name) == 43
            and all(c in "0123456789abcdef" for c in name[7:-4])
        ):
            raise HTTPException(404, "Original upload is unavailable for this observation")
        path = ROOT / "data/runtime/originals" / name.replace(".jpg", ".bin")
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
        with store.session(write=True) as session:
            if user:
                request = request.model_copy(update={"reviewer": user.name})
            return service.verify(session, evidence_id, request, user_id=user.id if user else None)

    @app.post("/api/observations/upload", response_model=Evidence, dependencies=protected)
    async def upload(
        file: Annotated[UploadFile, File()],
        footprint: Annotated[str, Form()],
        mission_id: Annotated[str, Form()] = "eva-01",
    ) -> Evidence:
        if file.content_type not in {"image/jpeg", "image/png"}:
            raise HTTPException(415, "Only JPEG and PNG images are supported")
        content = await file.read(settings.max_upload_bytes + 1)
        await file.close()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(413, "Image exceeds the 8 MB upload limit")
        original_content = content
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
        output = service.perception.infer(content)
        asset_id = identifier("upload") + ".jpg"
        upload_dir = ROOT / "data/runtime/uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        asset_path = upload_dir / asset_id
        asset_path.write_bytes(content)
        original_dir = ROOT / "data/runtime/originals"
        original_dir.mkdir(parents=True, exist_ok=True)
        original_path = original_dir / asset_id.replace(".jpg", ".bin")
        try:
            original_path.write_bytes(original_content)
            with store.session(write=True) as session:
                return service.observe(
                    session,
                    mission_id,
                    geometry,
                    output,
                    f"/api/assets/{asset_id}",
                    hashlib.sha256(content).hexdigest(),
                    "ground",
                    "Astronaut-uploaded image",
                    "Footprint supplied manually in local meters; "
                    "image is not independently geolocated. Display/model input is a sanitized "
                    "JPEG derivative; original bytes/hash are retained separately.",
                    original_digest=hashlib.sha256(original_content).hexdigest(),
                )
        except Exception:
            asset_path.unlink(missing_ok=True)
            original_path.unlink(missing_ok=True)
            raise

    @app.get("/api/assets/{asset_id}", dependencies=protected)
    def asset(asset_id: str) -> FileResponse:
        known = {"jezero-ctx.png", "ground-navcam.jpg", "jezero-hirise.png"}
        if asset_id in known:
            path = ROOT / "data/nasa" / asset_id
        elif asset_id in {"navcam-preview.png", "mastcamz-preview.png"}:
            path = ROOT / "data/processed" / asset_id
        elif asset_id == "crism-preview.png":
            path = ROOT / "data/nasa/crism/frt000047a3_07_brtanj_mtr3.png"
        elif asset_id.startswith("upload-") and asset_id.endswith(".jpg") and len(asset_id) == 43:
            if not all(c in "0123456789abcdef" for c in asset_id[7:-4]):
                raise HTTPException(404, "Asset not found")
            path = ROOT / "data/runtime/uploads" / asset_id
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
