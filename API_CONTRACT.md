# API contract

FastAPI base: /api. Runtime schema: /openapi.json; interactive docs: /docs.
Current response models: backend/domain.py. Proposed changes below are not yet
implemented and must preserve existing persisted history.

| Method / path | Input | Output / current behavior |
| --- | --- | --- |
| GET /health | none | status, environment, cache_available (currently checks CTX existence only) |
| GET /missions/{mission_id} | eva-01 or eva-02 | Snapshot: mission, astronaut, target, regions, all evidence, mission routes/events, assumptions, data_status |
| POST /observations/demo | JSON mission_id, scenario | Provisional Evidence from curated replay; disabled with 404 in production |
| POST /observations/upload | Multipart file, footprint JSON, mission_id | Provisional Evidence from configured TorchScript or conservative local CV |
| GET /observations/{id} | observation identity | Original inference, asset digest, footprint, timestamp, metadata note |
| GET /observations/{id}/original | observation identity | Exact validated original upload as private no-sniff attachment; unavailable for replay/older records without originals |
| GET /evidence/{id} | evidence identity | Evidence, consequence and verification metadata |
| POST /evidence/{id}/verify | JSON decision, reviewer, note, optional human_terrain | Final/pending Evidence; atomic state/route/history update; repeated same final decision is idempotent |
| GET /assets/{asset_id} | allowlisted cached name or generated upload ID | JPEG/PNG; no arbitrary filesystem access |

Replay scenarios: obstacles, match, minor, weak, failure, dynamic. Decisions:
CONFIRMED, REJECTED, NEEDS_MORE_EVIDENCE. Terrain: soil, sand, bedrock, large rocks,
rough terrain, obstacle-rich terrain, unknown.

Upload bounds: JPEG/PNG, 8 MiB request image, 16 million decoded pixels. Polygon
coordinates are **local x/y meters**, not WGS84 GeoJSON. Extent x=0..1200,
y=0..800. One closed non-self-intersecting polygon, no holes; contained in one
mapped region. Current endpoint retains exact validated original bytes/hash
separately and sanitizes metadata by re-encoding a display/model-input JPEG.
Observation.original_asset_reference points to the protected original endpoint;
asset_sha256 hashes original bytes and model_input_sha256 hashes the derivative.
Older/replay records may not have an original reference; this is explicit absence,
not permission to label a reconstructed derivative as the original.

Current errors use {"detail": "message"}: 401 unauthenticated, 404 unknown entity
or unavailable asset, 413 oversized image, 415 unsupported media, 422 invalid
request/decision, 500 unexpected failure. FastAPI request validation uses its
standard structured detail list. Do not expose stack traces, filesystem paths,
tokens or raw model loading errors. A stable {code, detail, retryable, request_id}
envelope and generated TypeScript schemas are planned acceptance requirements.

Demo authentication is disabled for loopback development. Production requires
Authorization: Bearer <server-side secret>, at least 32 characters, with explicit
CORS origins. The current frontend rewrite does not add authentication and cannot
serve the protected production workflow. Introduce an authenticated server-side
proxy/session boundary; never place this secret in the browser bundle.

Health readiness must eventually validate DB access, required cache checksums,
manifest alignment, inference capability and configured deployment mode. A
successful process response alone is insufficient for demo readiness.

Safety of retries: committed confirmation is idempotent. Upload/observe is
currently not deduplicated; add idempotency keys before exposing unreliable-network
automatic retries. Transport failure must not be interpreted as proof a write
did not commit; refetch the evidence record before issuing another decision.
