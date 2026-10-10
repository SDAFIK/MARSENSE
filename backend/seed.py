import json

import numpy as np
from sqlalchemy.orm import Session

from backend.config import ROOT
from backend.domain import (
    AstronautState,
    Consequence,
    Discrepancy,
    Evidence,
    Mission,
    MissionAssumption,
    MissionEvent,
    Provenance,
    Region,
    Route,
    RouteSegment,
    ScienceTarget,
    Terrain,
    Verification,
    rectangle,
)
from backend.routing import astar
from backend.store import all_of, put


def seed(session: Session, slope_grid: np.ndarray | None = None) -> None:
    if all_of(session, Mission):
        return
    manifest_path = ROOT / "data/processed/manifest.json"
    ctx = json.loads(manifest_path.read_text()).get("ctx", {}) if manifest_path.exists() else {}
    quiet = Consequence(
        relevant=False,
        safety_critical=False,
        alert=None,
        assumption_ids=[],
        route_segment_ids=[],
        target_ids=[],
        explanation="Orbital context prior.",
    )
    for region_id, name, bounds in [
        ("west", "Habitat approach", (0, 0, 440, 800)),
        ("corridor", "Area 14 · Traverse corridor", (440, 0, 760, 800)),
        ("east", "Delta approach", (760, 0, 1200, 800)),
    ]:
        geometry = rectangle(*bounds)
        prior_id = f"prior-{region_id}"
        put(
            session,
            Evidence(
                id=prior_id,
                region_id=region_id,
                observation_id=None,
                mission_id="nasa-prior",
                source="NASA Mars Trek / controlled Jezero CTX mosaic; "
                "mission interpretation is illustrative",
                source_type="orbital",
                location=((bounds[0] + bounds[2]) / 2, 400),
                spatial_footprint=geometry,
                observation_type="orbital terrain interpretation",
                observed_value=Terrain.SOIL,
                expected_value=Terrain.SOIL,
                model_output=None,
                model_confidence=None,
                verification_state=Verification.CONFIRMED,
                persistence_type="persistent",
                raw_asset_reference="/api/assets/jezero-ctx.png",
                discrepancy=Discrepancy.MATCH,
                consequence=quiet,
                provenance=Provenance(
                    classification="derived",
                    source_mission="Mars Reconnaissance Orbiter",
                    instrument="CTX",
                    product_id=ctx.get("layer"),
                    source_url=ctx.get("tiles", [{}])[0].get("url") if ctx.get("tiles") else None,
                    source_crs=ctx.get("source_crs"),
                    processing=[
                        "Bounded Mars Trek display crop; see cache manifest for byte hashes",
                        "Soil interpretation is illustrative, not a NASA measurement",
                    ],
                    registration="simulated",
                ),
            ),
        )
        put(
            session,
            Region(
                id=region_id,
                name=name,
                geometry=geometry,
                prior_interpretation=Terrain.SOIL,
                current_interpretation="soil (illustrative orbital interpretation)",
                prior_evidence_id=prior_id,
                evidence_history=[prior_id],
            ),
        )
    target = ScienceTarget(
        id="delta-target",
        name="Delta outcrop",
        location=(1080, 400),
        objective="Document exposed terrain at the science waypoint.",
        source_note="Illustrative mission target; no mineral composition inferred.",
    )
    put(session, target)
    put(session, AstronautState(id="astronaut-01", name="A. Rahman", location=(120, 400)))
    put(session, AstronautState(id="astronaut-02", name="S. Chen", location=(120, 400)))
    put(
        session,
        MissionAssumption(
            id="assumption-corridor",
            statement="A17: Area 14 contains continuous, low-obstacle soil along segment 3.",
            supporting_evidence=["prior-corridor"],
            dependent_route_segments=[f"{m}-alpha-segment-3" for m in ["eva-01", "eva-02"]],
            dependent_targets=[target.id],
        ),
    )
    path = astar((120, 400), target.location, [], slope_grid)
    for mission_id, eva, astronaut_id in [
        ("eva-01", "EVA 01", "astronaut-01"),
        ("eva-02", "EVA 02", "astronaut-02"),
    ]:
        route_id = f"{mission_id}-alpha"
        put(
            session,
            Route(
                id=route_id,
                mission_id=mission_id,
                name="Route Alpha",
                version=1,
                status="ACTIVE" if path.coordinates else "NO_ROUTE",
                coordinates=path.coordinates,
                distance_m=path.distance_m,
                cost=path.cost,
                cost_breakdown=path.breakdown,
                segment_ids=[f"{route_id}-segment-{i}" for i in [1, 3, 4]],
                evidence_ids=[],
                explanation="Shortest modeled traverse using the illustrative "
                "orbital-only soil assumption. "
                + (
                    "Configured DEM slope contributes to cost; field assessment is required."
                    if slope_grid is not None
                    else "Slope is unavailable and excluded; field assessment is required."
                ),
            ),
        )
        put(
            session,
            Mission(
                id=mission_id,
                name="Jezero / Delta reconnaissance",
                eva=eva,
                astronaut_id=astronaut_id,
                habitat=(120, 400),
                target_id=target.id,
                active_route_id=route_id,
            ),
        )
        put(
            session,
            MissionEvent(
                id=f"seed-{mission_id}",
                mission_id=mission_id,
                kind="MISSION_INITIALIZED",
                title="Orbital prior loaded",
                detail="Cached NASA CTX imagery. Illustrative mission geometry. "
                "No ground verification yet.",
            ),
        )
    for mission_id in ["eva-01", "eva-02"]:
        for segment, left, right in [(1, 0, 440), (3, 440, 760), (4, 760, 1200)]:
            put(
                session,
                RouteSegment(
                    id=f"{mission_id}-alpha-segment-{segment}",
                    route_id=f"{mission_id}-alpha",
                    coordinates=[p for p in path.coordinates if left <= p[0] <= right],
                    assumption_ids=["assumption-corridor"] if segment == 3 else [],
                ),
            )
