"""Append-only source declarations and human interpretation ancestry.

Independence is a reviewer's recorded assertion, never inferred from filenames.
Duplicate bytes and same-episode frames cannot count as independent support.
"""

from typing import Any

from pydantic import Field
from shapely.geometry import mapping, shape
from sqlalchemy.orm import Session

from backend.domain import Entity, Evidence, Observation, now
from backend.store import all_of, get, put


class SourceDeclaration(Entity):
    evidence_id: str
    source_key: str = Field(min_length=2, max_length=100)
    episode: str = Field(min_length=2, max_length=100)
    reviewer: str = Field(min_length=2, max_length=80)
    note: str = Field(min_length=3, max_length=500)
    timestamp: str = Field(default_factory=now)


class Supersession(Entity):
    previous_id: str
    replacement_id: str
    reviewer: str
    note: str
    timestamp: str = Field(default_factory=now)


def active_evidence(session: Session) -> list[Evidence]:
    retired = {s.previous_id for s in all_of(session, Supersession)}
    return [e for e in all_of(session, Evidence) if e.id not in retired]


def declare_source(session: Session, declaration: SourceDeclaration) -> SourceDeclaration:
    evidence = get(session, Evidence, declaration.evidence_id)
    if evidence.source_type == "orbital" or not evidence.observation_id:
        raise ValueError("Only recorded ground observations can receive source declarations")
    if any(d.evidence_id == evidence.id for d in all_of(session, SourceDeclaration)):
        raise ValueError("Source declarations are immutable; original assertion is retained")
    declaration.id = "source-" + evidence.id
    put(session, declaration)
    return declaration


def validate_supersession(session: Session, replacement: Evidence, ids: list[str]) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate supersession references")
    current = {e.id: e for e in active_evidence(session)}
    for old_id in ids:
        old = current.get(old_id)
        if (
            old is None
            or old.id == replacement.id
            or old.source_type == "orbital"
            or old.verification_state != "CONFIRMED"
            or old.persistence_type != "persistent"
            or replacement.persistence_type != "persistent"
        ):
            raise ValueError("Supersession requires current, confirmed persistent ground evidence")
        if not shape(replacement.spatial_footprint.model_dump()).covers(
            shape(old.spatial_footprint.model_dump())
        ):
            raise ValueError("Replacement must cover the entire retired footprint")


def synthesis(session: Session, evidence_id: str) -> dict[str, Any]:
    evidence = get(session, Evidence, evidence_id)
    ancestry = all_of(session, Supersession)
    successors = [s.replacement_id for s in ancestry if s.previous_id == evidence_id]
    result: dict[str, Any] = {
        "state": "SUPERSEDED" if successors else evidence.verification_state.value,
        "supporting_evidence": [evidence_id],
        "footprints": [],
        "superseded_by": successors,
        "supersedes": [s.previous_id for s in ancestry if s.replacement_id == evidence_id],
        "ancestry": [
            s.model_dump() for s in ancestry if evidence_id in (s.previous_id, s.replacement_id)
        ],
        "source_declarations": [d.model_dump() for d in all_of(session, SourceDeclaration)],
        "confidence_adjustment": None,
        "conflicting_evidence": [],
    }
    if (
        successors
        or evidence.verification_state != "CONFIRMED"
        or evidence.persistence_type != "persistent"
    ):
        return result
    result["state"] = "GROUND_OBSERVED"
    declarations = {d.evidence_id: d for d in all_of(session, SourceDeclaration)}
    own = declarations.get(evidence.id)
    own_observation = (
        get(session, Observation, evidence.observation_id) if evidence.observation_id else None
    )
    for other in active_evidence(session):
        if (
            other.id == evidence_id
            or other.source_type == "orbital"
            or other.persistence_type != "persistent"
            or other.verification_state == "REJECTED"
        ):
            continue
        overlap = shape(evidence.spatial_footprint.model_dump()).intersection(
            shape(other.spatial_footprint.model_dump())
        )
        if overlap.area <= 0:
            continue
        if other.observed_value != evidence.observed_value:
            result["conflicting_evidence"].append(other.id)
            continue
        declaration = declarations.get(other.id)
        if (
            not own
            or not declaration
            or own.episode == declaration.episode
            or other.verification_state != "CONFIRMED"
            or not other.observation_id
        ):
            continue
        observation = get(session, Observation, other.observation_id)
        if (
            not own_observation
            or observation.asset_sha256 == own_observation.asset_sha256
            or not observation.asset_sha256
        ):
            continue
        result["supporting_evidence"].append(other.id)
        result["footprints"].append(
            {"geometry": mapping(overlap), "supporting_evidence": [evidence_id, other.id]}
        )
    if len(result["supporting_evidence"]) > 1:
        result["state"] = "MULTI_SOURCE_CONFIRMED"
    if result["conflicting_evidence"]:
        result["state"] = "CONFLICTING"
    return result
