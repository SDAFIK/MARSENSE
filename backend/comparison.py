from shapely.geometry import LineString, shape

from backend.domain import (
    Consequence,
    Discrepancy,
    Evidence,
    Footprint,
    MissionAssumption,
    ModelOutput,
    Route,
    RouteSegment,
    Terrain,
    Verification,
)

OBSTACLES = {Terrain.OBSTACLES, Terrain.LARGE_ROCKS, Terrain.ROUGH}


def compare(expected: Terrain, output: ModelOutput, conflicting: bool = False) -> Discrepancy:
    if output.confidence < 0.5 or output.terrain == Terrain.UNKNOWN:
        return Discrepancy.INSUFFICIENT_EVIDENCE
    if conflicting:
        return Discrepancy.CONFLICTING_EVIDENCE
    if expected == output.terrain:
        return Discrepancy.MATCH
    if output.terrain in OBSTACLES or expected in OBSTACLES:
        return Discrepancy.SIGNIFICANT_DIFFERENCE
    return Discrepancy.MINOR_DIFFERENCE


def expected_at(
    prior: Terrain, footprint: Footprint, evidence: list[Evidence]
) -> tuple[Terrain, bool]:
    supported = [
        e
        for e in evidence
        if e.source_type != "orbital"
        and e.verification_state == Verification.CONFIRMED
        and e.persistence_type == "persistent"
        and shape(e.spatial_footprint.model_dump()).covers(shape(footprint.model_dump()))
    ]
    if not supported:
        return prior, False
    return supported[-1].observed_value, len({e.observed_value for e in supported}) > 1


def consequence(
    footprint: Footprint,
    output: ModelOutput,
    discrepancy: Discrepancy,
    routes: list[Route],
    assumptions: list[MissionAssumption],
    route_segments: list[RouteSegment],
) -> Consequence:
    geom = shape(footprint.model_dump())
    affected = [
        r
        for r in routes
        if r.status in {"ACTIVE", "CHALLENGED"}
        and r.coordinates
        and geom.intersects(LineString(r.coordinates))
    ]
    active_segment_ids = {segment for r in affected for segment in r.segment_ids}
    segments = sorted(
        s.id
        for s in route_segments
        if s.id in active_segment_ids
        and s.coordinates
        and geom.intersects(LineString(s.coordinates))
    )
    relevant_assumptions = [
        a for a in assumptions if set(a.dependent_route_segments) & set(segments)
    ]
    different = discrepancy != Discrepancy.MATCH
    relevant = bool(affected) and different
    safety = relevant and (output.terrain in OBSTACLES or output.terrain == Terrain.UNKNOWN)
    alert = "PROVISIONAL SAFETY ALERT" if safety else "MISSION DISCREPANCY" if relevant else None
    explanation = (
        "The observation footprint intersects the active traverse and its return corridor. "
        + (
            "The low-obstacle assumption needs human review. "
            if relevant_assumptions
            else "No mapped assumption depends on the intersected segment. "
        )
        + "No permanent route change before confirmation."
        if relevant
        else "Evidence stored without interrupting the mission: no challenged active dependency."
    )
    return Consequence(
        relevant=relevant,
        safety_critical=safety,
        alert=alert,
        assumption_ids=[a.id for a in relevant_assumptions] if relevant else [],
        route_segment_ids=segments if relevant else [],
        target_ids=sorted({t for a in relevant_assumptions for t in a.dependent_targets})
        if relevant
        else [],
        explanation=explanation,
    )
