from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from shapely.geometry import shape


def now() -> str:
    return datetime.now(UTC).isoformat()


class KnowledgeState(StrEnum):
    ORBITAL_ONLY = "ORBITAL_ONLY"
    PROVISIONAL = "PROVISIONAL"
    GROUND_OBSERVED = "GROUND_OBSERVED"
    MULTI_SOURCE_CONFIRMED = "MULTI_SOURCE_CONFIRMED"
    CONFLICTING = "CONFLICTING"
    SUPERSEDED = "SUPERSEDED"


class Verification(StrEnum):
    PROVISIONAL = "PROVISIONAL"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


class Discrepancy(StrEnum):
    MATCH = "MATCH"
    MINOR_DIFFERENCE = "MINOR_DIFFERENCE"
    SIGNIFICANT_DIFFERENCE = "SIGNIFICANT_DIFFERENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Terrain(StrEnum):
    SOIL = "soil"
    SAND = "sand"
    BEDROCK = "bedrock"
    LARGE_ROCKS = "large rocks"
    ROUGH = "rough terrain"
    OBSTACLES = "obstacle-rich terrain"
    UNKNOWN = "unknown"


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str


class Footprint(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[tuple[float, float]]]

    @model_validator(mode="after")
    def validate_geometry(self) -> "Footprint":
        geom = shape(self.model_dump())
        if geom.is_empty or not geom.is_valid or geom.area <= 0 or len(self.coordinates) != 1:
            raise ValueError("Provide one valid, nonempty polygon without holes")
        if self.coordinates[0][0] != self.coordinates[0][-1]:
            raise ValueError("Polygon ring must be closed")
        x0, y0, x1, y1 = geom.bounds
        if not (0 <= x0 < x1 <= 1200 and 0 <= y0 < y1 <= 800):
            raise ValueError("Footprint must be inside the local mission extent (meters)")
        return self


def rectangle(x0: float, y0: float, x1: float, y1: float) -> Footprint:
    return Footprint(coordinates=[[(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]])


class ModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    terrain: Terrain
    confidence: float = Field(ge=0, le=1)
    confidence_label: Literal["reviewed demo annotation", "low", "moderate", "high", "unavailable"]
    engine: str
    version: str
    class_fractions: dict[str, float] = Field(default_factory=dict)
    features: dict[str, float] = Field(default_factory=dict)
    limitations: list[str]
    mask_reference: str | None = None


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    classification: Literal["observed", "derived", "simulated", "unavailable"] = "unavailable"
    source_mission: str | None = None
    instrument: str | None = None
    product_id: str | None = None
    source_url: str | None = None
    acquired_at: str | None = None
    resolution_m: float | None = Field(default=None, gt=0)
    source_crs: str | None = None
    processing: list[str] = Field(default_factory=list)
    registration: Literal["manual", "simulated", "validated", "unavailable"] = "unavailable"


class Region(Entity):
    name: str
    geometry: Footprint
    prior_interpretation: Terrain
    current_interpretation: str
    knowledge_state: KnowledgeState = KnowledgeState.ORBITAL_ONLY
    evidence_history: list[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=now)
    prior_evidence_id: str


class Observation(Entity):
    mission_id: str
    astronaut_id: str
    timestamp: str = Field(default_factory=now)
    region_id: str
    location: tuple[float, float]
    spatial_footprint: Footprint
    observation_type: Literal["terrain", "visibility"] = "terrain"
    raw_asset_reference: str
    asset_sha256: str
    original_asset_reference: str | None = None
    model_input_sha256: str | None = None
    metadata_note: str
    model_output: ModelOutput
    provenance: Provenance = Field(default_factory=Provenance)


class HumanDecision(Entity):
    evidence_id: str
    decision: Literal["CONFIRMED", "REJECTED", "NEEDS_MORE_EVIDENCE"]
    reviewer: str
    note: str
    timestamp: str = Field(default_factory=now)
    human_terrain: Terrain | None = None
    identity_basis: Literal["self-asserted local reviewer", "authenticated session"] = (
        "self-asserted local reviewer"
    )
    user_id: str | None = None
    mission_id: str | None = None
    observation_id: str | None = None


class Interpretation(Entity):
    evidence_id: str
    observation_id: str | None
    decision_id: str
    terrain: Terrain
    spatial_footprint: Footprint
    timestamp: str = Field(default_factory=now)
    persistence_type: Literal["persistent", "dynamic"]
    valid_until: str | None


class EvidenceHistory(BaseModel):
    decisions: list[HumanDecision]
    interpretations: list[Interpretation]
    legacy_decision: bool


class Consequence(BaseModel):
    relevant: bool
    safety_critical: bool
    alert: str | None
    assumption_ids: list[str]
    route_segment_ids: list[str]
    target_ids: list[str]
    explanation: str


class Evidence(Entity):
    superseded_by: list[str] = Field(default_factory=list)
    region_id: str
    observation_id: str | None
    mission_id: str
    source: str
    source_type: Literal["orbital", "ground", "demo_replay"]
    timestamp: str = Field(default_factory=now)
    location: tuple[float, float]
    spatial_footprint: Footprint
    observation_type: str
    observed_value: Terrain
    expected_value: Terrain
    model_output: ModelOutput | None
    model_confidence: float | None
    verification_state: Verification
    persistence_type: Literal["persistent", "dynamic"]
    valid_until: str | None = None
    raw_asset_reference: str
    discrepancy: Discrepancy
    consequence: Consequence
    verified_by: str | None = None
    verified_at: str | None = None
    verification_note: str | None = None
    stale: bool = False
    provenance: Provenance = Field(default_factory=Provenance)


class MissionAssumption(Entity):
    statement: str
    status: Literal["SUPPORTED", "PROVISIONALLY_CHALLENGED", "CHALLENGED"] = "SUPPORTED"
    supporting_evidence: list[str]
    challenging_evidence: list[str] = Field(default_factory=list)
    dependent_route_segments: list[str]
    dependent_targets: list[str]
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class RouteSegment(Entity):
    route_id: str
    coordinates: list[tuple[float, float]]
    assumption_ids: list[str]


class Route(Entity):
    mission_id: str
    name: str
    version: int
    status: Literal["ACTIVE", "CHALLENGED", "SUPERSEDED", "NO_ROUTE"]
    coordinates: list[tuple[float, float]]
    distance_m: float
    cost: float
    cost_breakdown: dict[str, float]
    segment_ids: list[str]
    evidence_ids: list[str]
    explanation: str
    created_at: str = Field(default_factory=now)


class MissionEvent(Entity):
    mission_id: str
    timestamp: str = Field(default_factory=now)
    kind: str
    title: str
    detail: str
    evidence_id: str | None = None


class ScienceTarget(Entity):
    name: str
    location: tuple[float, float]
    objective: str
    source_note: str


class AstronautState(Entity):
    name: str
    location: tuple[float, float]
    authority: str = "Human confirmation required for terrain updates"


class Mission(Entity):
    name: str
    eva: str
    astronaut_id: str
    habitat: tuple[float, float]
    target_id: str
    active_route_id: str
    inherited_evidence: list[str] = Field(default_factory=list)


class ObserveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission_id: Literal["eva-01", "eva-02"] = "eva-01"
    scenario: Literal["obstacles", "match", "minor", "weak", "failure", "dynamic"] = "obstacles"


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["CONFIRMED", "REJECTED", "NEEDS_MORE_EVIDENCE"]
    reviewer: str = Field(min_length=2, max_length=80)
    note: str = Field(min_length=3, max_length=500)
    human_terrain: Terrain | None = None
    supersedes: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("reviewer", "note", mode="before")
    @classmethod
    def plain_text(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Use a text value")
        if any(ord(c) < 32 for c in value) or "<" in value or ">" in value:
            raise ValueError("Use plain text without control characters or markup")
        return value.strip()


class Snapshot(BaseModel):
    mission: Mission
    astronaut: AstronautState
    target: ScienceTarget
    regions: list[Region]
    evidence: list[Evidence]
    routes: list[Route]
    assumptions: list[MissionAssumption]
    events: list[MissionEvent]
    data_status: dict[str, Any]
