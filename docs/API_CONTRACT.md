# API contract

Implementation snapshot; required contract: [root API_CONTRACT.md](../API_CONTRACT.md).

All routes except health require `Authorization: Bearer <token>` in production API mode. Local demo mode uses no secret. Domain errors have a `detail` string; request validation uses a detail list; invalid metadata uses 422, missing entities 404, wrong media 415, oversized upload 413, missing auth 401. Internal errors preserve state and return a generic 500 message.

| Method and path | Contract |
|---|---|
| GET `/api/health` | Service mode and local-cache availability |
| GET `/api/missions/{id}` | Mission, astronaut, target, regions, evidence, versioned routes, assumptions, events, data status |
| POST `/api/observations/demo` | `{mission_id:"eva-01", scenario:"obstacles"}`; creates provisional replay evidence; disabled in production |
| POST `/api/observations/upload` | Multipart file, mission_id, footprint serialized Polygon in local meters; creates provisional actual-image evidence |
| GET `/api/observations/{id}` | Original raw observation and unaltered model interpretation |
| GET `/api/observations/{id}/original` | Exact validated upload bytes as a non-inline, no-sniff attachment; same API authorization |
| GET `/api/evidence/{id}` | Evidence, consequence and human review provenance |
| POST `/api/evidence/{id}/verify` | decision, reviewer, note; optional human_terrain for weak evidence |
| GET `/api/assets/{id}` | Cached NASA crop or cleaned generated-name upload; no arbitrary paths |

Verification example:

```json
{"decision":"CONFIRMED","reviewer":"A. Rahman","note":"Visual inspection confirms obstacles within the supported footprint."}
```

Weak-evidence review additionally requires `"human_terrain":"obstacle-rich terrain"` (or another supported terrain enum). The model output remains in the observation. Reviewer text is validated, but is self-asserted in the local demonstration; identity-bound review is a remaining production requirement.

Use `/docs` for the complete generated schema. The frontend uses same-origin `/api` rewrites to the backend; `BACKEND_URL` is a server build/runtime configuration, never a browser secret. There are no stub endpoints that pretend to ingest scientific archives or trained models.
