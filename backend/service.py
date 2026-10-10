import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

import numpy as np
from shapely.geometry import LineString, shape
from sqlalchemy.orm import Session

from ai.perception import Perception
from backend.comparison import compare, consequence, expected_at
from backend.config import ROOT
from backend.domain import (
    AstronautState,
    Discrepancy,
    Evidence,
    Footprint,
    HumanDecision,
    Interpretation,
    KnowledgeState,
    Mission,
    MissionAssumption,
    MissionEvent,
    ModelOutput,
    Observation,
    ObserveRequest,
    Provenance,
    Region,
    Route,
    RouteSegment,
    ScienceTarget,
    Snapshot,
    Terrain,
    Verification,
    VerifyRequest,
    now,
)
from backend.knowledge import Supersession, active_evidence, validate_supersession
from backend.routing import astar
from backend.science import crism_context
from backend.store import all_of, get, put


def identifier(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


class MissionService:
    def __init__(self, perception: Perception, slope_grid: np.ndarray | None = None):
        self.perception = perception
        self.slope_grid = slope_grid

    def demo(self, session: Session, request: ObserveRequest) -> Evidence:
        fixture = json.loads((ROOT / "data/demo/scenarios.json").read_text())[request.scenario]
        output = ModelOutput.model_validate(fixture["model_output"])
        asset = ROOT / "data/nasa/ground-navcam.jpg"
        return self.observe(
            session,
            request.mission_id,
            Footprint.model_validate(fixture["footprint"]),
            output,
            "/api/assets/ground-navcam.jpg",
            hashlib.sha256(asset.read_bytes()).hexdigest(),
            "demo_replay",
            "NASA/JPL-Caltech Navcam PIA26072 + curated scenario annotation",
            fixture["metadata_note"],
            fixture.get("observation_type", "terrain"),
        )

    def observe(
        self,
        session: Session,
        mission_id: str,
        footprint: Footprint,
        output: ModelOutput,
        asset: str,
        digest: str,
        source_type: Literal["ground", "demo_replay"],
        source: str,
        note: str,
        observation_type: Literal["terrain", "visibility"] = "terrain",
        original_digest: str | None = None,
    ) -> Evidence:
        mission = get(session, Mission, mission_id)
        centroid = shape(footprint.model_dump()).centroid
        region = next(
            (
                r
                for r in all_of(session, Region)
                if shape(r.geometry.model_dump()).covers(shape(footprint.model_dump()))
            ),
            None,
        )
        if region is None:
            raise ValueError("Footprint must be contained within one mapped region")
        history = sorted(active_evidence(session), key=lambda e: e.timestamp)
        expected, conflicting = expected_at(region.prior_interpretation, footprint, history)
        if any(
            e.verification_state == Verification.CONFIRMED
            and e.source_type != "orbital"
            and e.persistence_type == "persistent"
            and e.observed_value != output.terrain
            and shape(e.spatial_footprint.model_dump()).intersects(shape(footprint.model_dump()))
            for e in history
        ):
            conflicting = True
        discrepancy = compare(expected, output, conflicting)
        impact = consequence(
            footprint,
            output,
            discrepancy,
            [get(session, Route, mission.active_route_id)],
            all_of(session, MissionAssumption),
            all_of(session, RouteSegment),
        )
        observation = Observation(
            id=identifier("obs"),
            mission_id=mission_id,
            astronaut_id=mission.astronaut_id,
            region_id=region.id,
            location=(centroid.x, centroid.y),
            spatial_footprint=footprint,
            observation_type=observation_type,
            raw_asset_reference=asset,
            asset_sha256=original_digest or digest,
            model_input_sha256=digest,
            metadata_note=note,
            model_output=output,
            provenance=Provenance(
                classification="simulated" if source_type == "demo_replay" else "observed",
                source_mission="Mars 2020" if source_type == "demo_replay" else None,
                instrument="Navcam" if source_type == "demo_replay" else None,
                product_id="PIA26072" if source_type == "demo_replay" else None,
                source_url="https://www.jpl.nasa.gov/images/"
                "pia26072-perseverance-makes-tracks-in-boulder-field/"
                if source_type == "demo_replay"
                else None,
                acquired_at="2023-07-28" if source_type == "demo_replay" else None,
                processing=[note],
                registration="simulated" if source_type == "demo_replay" else "manual",
            ),
        )
        if original_digest:
            observation.original_asset_reference = f"/api/observations/{observation.id}/original"
        put(session, observation)
        dynamic = observation_type == "visibility"
        evidence = Evidence(
            id=identifier("ev"),
            region_id=region.id,
            observation_id=observation.id,
            mission_id=mission_id,
            source=source,
            source_type=source_type,
            location=observation.location,
            spatial_footprint=footprint,
            observation_type=observation_type,
            observed_value=output.terrain,
            expected_value=expected,
            model_output=output,
            model_confidence=output.confidence,
            verification_state=Verification.PROVISIONAL,
            persistence_type="dynamic" if dynamic else "persistent",
            valid_until=(datetime.now(UTC) + timedelta(minutes=30)).isoformat()
            if dynamic
            else None,
            raw_asset_reference=asset,
            discrepancy=discrepancy,
            consequence=impact,
            provenance=observation.provenance,
        )
        put(session, evidence)
        self._refresh_region(session, region.id)
        self._refresh_assumptions(session)
        if impact.relevant:
            route = get(session, Route, mission.active_route_id)
            route.status = "CHALLENGED"
            put(session, route)
        self._event(
            session,
            mission_id,
            "OBSERVATION_ANALYZED",
            impact.alert or "Evidence recorded",
            f"Expected {expected.value}; observed {output.terrain.value}. {impact.explanation}",
            evidence.id,
        )
        return evidence

    def verify(
        self, session: Session, evidence_id: str, request: VerifyRequest, user_id: str | None = None
    ) -> Evidence:
        evidence = get(session, Evidence, evidence_id)
        if evidence.source_type == "orbital":
            raise ValueError("NASA prior evidence is immutable")
        if evidence.verification_state in {Verification.CONFIRMED, Verification.REJECTED}:
            if evidence.verification_state.value == request.decision:
                return evidence
            raise ValueError("A final verification cannot be overwritten; submit new evidence")
        if request.decision == "CONFIRMED":
            validate_supersession(session, evidence, request.supersedes)
            if evidence.valid_until and datetime.fromisoformat(
                evidence.valid_until
            ) <= datetime.now(UTC):
                raise ValueError("Dynamic evidence has expired; record a new observation")
            if evidence.discrepancy == Discrepancy.CONFLICTING_EVIDENCE and not request.supersedes:
                raise ValueError(
                    "Conflicting evidence requires another observation; no persistent update"
                )
            if (
                evidence.persistence_type == "persistent"
                and request.human_terrain == Terrain.UNKNOWN
            ):
                raise ValueError("Persistent confirmation requires known terrain identification")
            if evidence.persistence_type == "persistent" and (
                evidence.model_confidence is None
                or evidence.model_confidence < 0.5
                or evidence.observed_value == Terrain.UNKNOWN
            ):
                if request.human_terrain is None or request.human_terrain == Terrain.UNKNOWN:
                    raise ValueError(
                        "Weak model evidence requires explicit human terrain identification"
                    )
            if request.human_terrain is not None and evidence.persistence_type == "persistent":
                evidence.observed_value = request.human_terrain
                # Preserve original inference; classify the human interpretation separately.
                evidence.discrepancy = (
                    Discrepancy.MATCH
                    if request.human_terrain == evidence.expected_value
                    else Discrepancy.SIGNIFICANT_DIFFERENCE
                    if request.human_terrain
                    in {Terrain.OBSTACLES, Terrain.LARGE_ROCKS, Terrain.ROUGH}
                    else Discrepancy.MINOR_DIFFERENCE
                )
            if evidence.persistence_type == "persistent" and any(
                other.id != evidence.id
                and other.id not in request.supersedes
                and other.source_type != "orbital"
                and other.verification_state == Verification.CONFIRMED
                and other.persistence_type == "persistent"
                and other.observed_value != evidence.observed_value
                and shape(other.spatial_footprint.model_dump())
                .intersection(shape(evidence.spatial_footprint.model_dump()))
                .area
                > 0
                for other in active_evidence(session)
            ):
                raise ValueError("Human interpretation conflicts with verified ground evidence")
            evidence.verified_by, evidence.verified_at = request.reviewer, now()
        evidence.verification_state = Verification(request.decision)
        evidence.verification_note = request.note
        put(session, evidence)
        decision = HumanDecision(
            user_id=user_id,
            mission_id=evidence.mission_id,
            observation_id=evidence.observation_id,
            identity_basis="authenticated session" if user_id else "self-asserted local reviewer",
            id=identifier("decision"),
            evidence_id=evidence.id,
            decision=request.decision,
            reviewer=request.reviewer,
            note=request.note,
            human_terrain=request.human_terrain,
        )
        put(session, decision)
        if request.supersedes and request.decision != "CONFIRMED":
            raise ValueError("Only confirmation can supersede earlier interpretation")
        for old_id in request.supersedes:
            put(
                session,
                Supersession(
                    id=identifier("supersession"),
                    previous_id=old_id,
                    replacement_id=evidence.id,
                    reviewer=request.reviewer,
                    note=request.note,
                ),
            )
        if request.decision == "CONFIRMED":
            put(
                session,
                Interpretation(
                    id=identifier("interpretation"),
                    evidence_id=evidence.id,
                    observation_id=evidence.observation_id,
                    decision_id=decision.id,
                    terrain=evidence.observed_value,
                    spatial_footprint=evidence.spatial_footprint,
                    persistence_type=evidence.persistence_type,
                    valid_until=evidence.valid_until,
                ),
            )
        self._refresh_region(session, evidence.region_id)
        self._refresh_assumptions(session)
        if (
            evidence.verification_state == Verification.CONFIRMED
            and evidence.persistence_type == "persistent"
        ):
            # Future EVAs inherit verified knowledge in the same transaction.
            for mission in all_of(session, Mission):
                self._reroute(session, mission, evidence)
        else:
            self._refresh_route_alerts(session)
        self._event(
            session,
            evidence.mission_id,
            "VERIFICATION",
            f"Evidence {request.decision.lower().replace('_', ' ')}",
            f"{request.reviewer}: {request.note}",
            evidence.id,
        )
        return evidence

    def _refresh_region(self, session: Session, region_id: str) -> None:
        region = get(session, Region, region_id)
        evidence = sorted(
            [e for e in all_of(session, Evidence) if e.region_id == region_id],
            key=lambda e: e.timestamp,
        )
        ground = [
            e
            for e in active_evidence(session)
            if e.region_id == region_id
            and e.source_type != "orbital"
            and e.persistence_type == "persistent"
        ]
        confirmed = [e for e in ground if e.verification_state == Verification.CONFIRMED]
        pending = [
            e
            for e in ground
            if e.verification_state in {Verification.PROVISIONAL, Verification.NEEDS_MORE_EVIDENCE}
        ]
        conflict = any(e.discrepancy == Discrepancy.CONFLICTING_EVIDENCE for e in pending)
        region.knowledge_state = (
            KnowledgeState.CONFLICTING
            if conflict
            else KnowledgeState.GROUND_OBSERVED
            if confirmed
            else KnowledgeState.PROVISIONAL
            if pending
            else KnowledgeState.ORBITAL_ONLY
        )
        observed_terrains = ", ".join(sorted({e.observed_value.value for e in confirmed}))
        region.current_interpretation = (
            f"{region.prior_interpretation.value}; verified {observed_terrains} "
            "within ground footprints only"
            if confirmed
            else f"{region.prior_interpretation.value} (orbital prior retained)"
        )
        region.evidence_history, region.updated_at = [e.id for e in evidence], now()
        put(session, region)

    def _refresh_assumptions(self, session: Session) -> None:
        for assumption in all_of(session, MissionAssumption):
            related = [
                e
                for e in active_evidence(session)
                if assumption.id in e.consequence.assumption_ids
                and e.persistence_type == "persistent"
                and e.discrepancy != Discrepancy.MATCH
            ]
            confirmed = [e for e in related if e.verification_state == Verification.CONFIRMED]
            pending = [
                e
                for e in related
                if e.verification_state
                in {Verification.PROVISIONAL, Verification.NEEDS_MORE_EVIDENCE}
            ]
            assumption.status = (
                "CHALLENGED"
                if confirmed
                else "PROVISIONALLY_CHALLENGED"
                if pending
                else "SUPPORTED"
            )
            assumption.challenging_evidence = [e.id for e in confirmed + pending]
            assumption.updated_at = now()
            put(session, assumption)

    def _refresh_route_alerts(self, session: Session) -> None:
        evidence = all_of(session, Evidence)
        for mission in all_of(session, Mission):
            route = get(session, Route, mission.active_route_id)
            if not route.coordinates:
                continue
            pending = any(
                e.mission_id == mission.id
                and e.consequence.relevant
                and shape(e.spatial_footprint.model_dump()).intersects(
                    LineString(route.coordinates)
                )
                and e.verification_state
                in {
                    Verification.PROVISIONAL,
                    Verification.NEEDS_MORE_EVIDENCE,
                }
                and (
                    e.valid_until is None
                    or datetime.fromisoformat(e.valid_until) > datetime.now(UTC)
                )
                for e in evidence
            )
            route.status = "CHALLENGED" if pending else "ACTIVE"
            put(session, route)

    def _reroute(self, session: Session, mission: Mission, trigger: Evidence) -> None:
        old = get(session, Route, mission.active_route_id)
        confirmed = sorted(
            [
                e
                for e in active_evidence(session)
                if e.source_type != "orbital"
                and e.verification_state == Verification.CONFIRMED
                and e.persistence_type == "persistent"
            ],
            key=lambda e: e.timestamp,
        )
        path = astar(
            mission.habitat,
            get(session, ScienceTarget, mission.target_id).location,
            confirmed,
            self.slope_grid,
        )
        mission.inherited_evidence = [e.id for e in confirmed if e.mission_id != mission.id]
        if (
            path.coordinates == old.coordinates
            and path.cost == old.cost
            and set(old.evidence_ids) == {e.id for e in confirmed}
        ):
            put(session, mission)
            self._refresh_route_alerts(session)
            return
        old.status = "SUPERSEDED"
        put(session, old)
        route_id = identifier(f"{mission.id}-route")
        explanation = (
            f"{trigger.verified_by} confirmed {trigger.observed_value.value} "
            "in the supported footprint "
            f"at local ({trigger.location[0]:.0f}, {trigger.location[1]:.0f}) m. "
            "Only cells/edges within that footprint receive the revised terrain cost. "
            f"A* recalculated the traverse from {old.distance_m:.0f} m to {path.distance_m:.0f} m. "
            "NASA prior evidence remains in the history. "
            + (
                "Configured DEM slope contributes to prototype cost; "
                "operational coverage validated."
                if self.slope_grid is not None
                else "Slope is unavailable and excluded."
            )
        )
        if not path.coordinates:
            explanation = (
                "No traversable path in the modeled grid. "
                "Stop and request mission planning review. " + explanation
            )
        new_route = Route(
            id=route_id,
            mission_id=mission.id,
            name="Route Beta" if old.version == 1 else f"Route revision {old.version + 1}",
            version=old.version + 1,
            status="ACTIVE" if path.coordinates else "NO_ROUTE",
            coordinates=path.coordinates,
            distance_m=path.distance_m,
            cost=path.cost,
            cost_breakdown=path.breakdown,
            segment_ids=[route_id + "-segment"],
            evidence_ids=[e.id for e in confirmed],
            explanation=explanation,
        )
        put(session, new_route)
        if path.coordinates:
            put(
                session,
                RouteSegment(
                    id=route_id + "-segment",
                    route_id=route_id,
                    coordinates=path.coordinates,
                    assumption_ids=[],
                ),
            )
        mission.active_route_id = route_id
        put(session, mission)
        self._event(
            session,
            mission.id,
            "ROUTE_RECALCULATED",
            new_route.name + " generated",
            explanation,
            trigger.id,
        )
        self._refresh_route_alerts(session)

    @staticmethod
    def _event(
        session: Session,
        mission_id: str,
        kind: str,
        title: str,
        detail: str,
        evidence_id: str | None,
    ) -> None:
        put(
            session,
            MissionEvent(
                id=identifier("event"),
                mission_id=mission_id,
                kind=kind,
                title=title,
                detail=detail,
                evidence_id=evidence_id,
            ),
        )

    def snapshot(self, session: Session, mission_id: str) -> Snapshot:
        mission = get(session, Mission, mission_id)
        manifest_path = ROOT / "data/processed/manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        try:
            science_target = get(session, ScienceTarget, mission.target_id)
            manifest["crism"] = crism_context(science_target.location)
        except (ValueError, KeyError, OSError, TypeError):
            manifest["crism"] = {"available": False, "reason": "CRISM cache validation failed"}
        camera_path = ROOT / "data/processed/cameras.json"
        if camera_path.exists():
            camera_data = json.loads(camera_path.read_text())
            manifest["cameras"] = [
                {
                    "product_id": c["product_id"],
                    "version_id": c["version_id"],
                    "instrument": c["instrument"],
                    "sol": c["sol"],
                    "sclk": c["sclk"],
                    "preview": f"/api/assets/{name}-preview.png",
                    "source_url": c["source_url"] + c["file_name"],
                    "raw_sha256": c["raw_sha256"],
                    "limitations": c["limitations"],
                    "clock_interval_matched": bool(c["places_exact_interval"]),
                    "observation_clock_matched": bool(c["places_observations"]),
                    "region_overlap": c["operational_region_overlap"],
                }
                for name, c in camera_data["products"].items()
            ]
        evidence = sorted(all_of(session, Evidence), key=lambda e: e.timestamp, reverse=True)
        for item in evidence:
            item.superseded_by = [
                s.replacement_id for s in all_of(session, Supersession) if s.previous_id == item.id
            ]
            item.stale = bool(
                item.valid_until and datetime.fromisoformat(item.valid_until) <= datetime.now(UTC)
            )
        routes = sorted(
            [r for r in all_of(session, Route) if r.mission_id == mission_id],
            key=lambda r: r.version,
        )
        for route in routes:
            if route.id == mission.active_route_id and route.coordinates:
                pending = any(
                    e.mission_id == mission_id
                    and not e.stale
                    and e.consequence.relevant
                    and e.verification_state
                    in {Verification.PROVISIONAL, Verification.NEEDS_MORE_EVIDENCE}
                    and shape(e.spatial_footprint.model_dump()).intersects(
                        LineString(route.coordinates)
                    )
                    for e in evidence
                )
                route.status = "CHALLENGED" if pending else "ACTIVE"
        return Snapshot(
            mission=mission,
            astronaut=get(session, AstronautState, mission.astronaut_id),
            target=get(session, ScienceTarget, mission.target_id),
            regions=all_of(session, Region),
            evidence=evidence,
            routes=routes,
            assumptions=all_of(session, MissionAssumption),
            events=sorted(
                [e for e in all_of(session, MissionEvent) if e.mission_id == mission_id],
                key=lambda e: e.timestamp,
                reverse=True,
            ),
            data_status={
                "mode": "LOCAL CACHE",
                "manifest": manifest,
                "terrain_prior": "Illustrative mission interpretation over real NASA imagery",
                "slope": "Configured DEM-derived slope; illustrative planning weights"
                if self.slope_grid is not None
                else "Unavailable; excluded from route cost",
                "model": "Configured TorchScript"
                if self.perception.model_path
                else "Curated demo replay / conservative CV fallback",
            },
        )
