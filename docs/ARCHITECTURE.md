# Architecture

Implementation snapshot; required boundaries: [root ARCHITECTURE.md](../ARCHITECTURE.md).

Next.js App Router, strict TypeScript, React, Tailwind and MapLibre render the mission workspace. FastAPI validates requests with Pydantic and delegates decisions to MissionService. SQLAlchemy stores typed aggregates in SQLite with WAL and serialized `BEGIN IMMEDIATE` write transactions. Shapely checks spatial support and route intersections. PyTorch/OpenCV handle actual image perception. Rasterio and NumPy process local Mars elevation products.

The seven responsibilities are separate modules: perception (`ai/perception.py`), comparison (`backend/comparison.py`), mission reasoning (consequence dependencies), verification (`MissionService.verify`), map knowledge (immutable prior plus local evidence), routing (`backend/routing.py`), and mission memory (persisted events and future-EVA inheritance).

Raw observation and model interpretation are stored separately from the human decision. A rejected record remains auditable. Provisional evidence can challenge an active route but cannot change its permanent terrain cost. Human confirmation and its evidence/map/route/events are committed in one database transaction. No browser-only confirmation or optimistic map update exists. Conflicting confirmed footprints require new evidence; they are not silently overwritten.

SQLite plus GeoJSON is the explicit local fallback. There is no unused PostGIS service masquerading as an integration. For larger operations, migrate aggregates to typed relational tables with spatial indexes and identity-bound transactions while preserving current API/entity semantics. The present JSON-aggregate schema is version 1 and requires a migration strategy before schema changes against deployed data.

Each browser request reads durable state. A connection failure retains the last loaded snapshot and offers retry. Expired dynamic evidence remains history but no longer challenges the current route or contributes to permanent terrain. The demonstration uses pre-cached imagery and replay annotations; actual uploads use the local perception adapter.

Production API mode requires an explicit token of at least 32 characters and rejects wildcard CORS. Assets use a strict allowlist or generated hexadecimal names. Uploads retain exact original bytes/hash separately; display/model derivatives
are decoded, dimension-limited, stripped of metadata and re-encoded; no executable upload type is served. The local UI is not yet an authenticated multi-user operations console.
