"""Version 1 → 2: repair legacy seeded dependency identities, retaining history."""

from sqlalchemy.orm import Session

from backend.domain import MissionAssumption, Route, RouteSegment
from backend.store import all_of, put


def migrate_legacy_segments(session: Session) -> None:
    segments = {s.id: s for s in all_of(session, RouteSegment)}
    replacements: dict[str, list[str]] = {}
    for route in all_of(session, Route):
        # Only known seeded Alpha routes are migrated; custom/revised paths are retained.
        if route.id != f"{route.mission_id}-alpha" or route.version != 1:
            continue
        expected_ids = [f"{route.id}-segment-{i}" for i in (1, 3, 4)]
        if route.segment_ids == expected_ids and all(
            s in segments and segments[s].route_id == route.id for s in route.segment_ids
        ):
            continue
        old_ids = route.segment_ids.copy()
        route.segment_ids = []
        for number, left, right in [(1, 0, 440), (3, 440, 760), (4, 760, 1200)]:
            segment = RouteSegment(
                id=f"{route.id}-segment-{number}",
                route_id=route.id,
                coordinates=[p for p in route.coordinates if left <= p[0] <= right],
                assumption_ids=["assumption-corridor"] if number == 3 else [],
            )
            put(session, segment)
            route.segment_ids.append(segment.id)
            if number == 3:
                for old in old_ids:
                    replacements.setdefault(old, []).append(segment.id)
        put(session, route)
    for assumption in all_of(session, MissionAssumption):
        # Retain old IDs because existing final evidence may refer to them.
        additions = [
            new for old in assumption.dependent_route_segments for new in replacements.get(old, [])
        ]
        if additions:
            assumption.dependent_route_segments = sorted(
                set(assumption.dependent_route_segments + additions)
            )
            put(session, assumption)
