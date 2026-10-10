import pytest

from ai.perception import Perception
from backend.domain import ObserveRequest, Terrain, VerifyRequest
from backend.knowledge import SourceDeclaration, active_evidence, declare_source, synthesis
from backend.seed import seed
from backend.service import MissionService
from backend.store import Store


def test_independent_sources_and_correlated_frames(tmp_path):
    store = Store(f"sqlite:///{tmp_path / 'knowledge.db'}")
    service = MissionService(Perception())
    with store.session(write=True) as session:
        seed(session)
        first = service.demo(session, ObserveRequest())
        service.verify(
            session,
            first.id,
            VerifyRequest(decision="CONFIRMED", reviewer="Reviewer", note="Inspected terrain"),
        )
        original = first.model_output
        second = service.observe(
            session,
            "eva-01",
            first.spatial_footprint,
            original,
            "second.png",
            "b" * 64,
            "ground",
            "camera B",
            "separate viewpoint",
        )
        service.verify(
            session,
            second.id,
            VerifyRequest(decision="CONFIRMED", reviewer="Reviewer", note="Inspected second view"),
        )
        for evidence, episode in [(first, "burst-a"), (second, "burst-a")]:
            declare_source(
                session,
                SourceDeclaration(
                    id="source-" + evidence.id,
                    evidence_id=evidence.id,
                    source_key="camera",
                    episode=episode,
                    reviewer="Reviewer",
                    note="Same burst",
                ),
            )
        assert synthesis(session, first.id)["state"] == "GROUND_OBSERVED"
        with pytest.raises(ValueError, match="immutable"):
            declare_source(
                session,
                SourceDeclaration(
                    id="source-" + second.id,
                    evidence_id=second.id,
                    source_key="camera",
                    episode="changed",
                    reviewer="Reviewer",
                    note="Cannot rewrite",
                ),
            )
        third = service.observe(
            session,
            "eva-01",
            first.spatial_footprint,
            original,
            "third.png",
            "c" * 64,
            "ground",
            "camera C",
            "later episode",
        )
        service.verify(
            session,
            third.id,
            VerifyRequest(decision="CONFIRMED", reviewer="Reviewer", note="Inspected later view"),
        )
        declare_source(
            session,
            SourceDeclaration(
                id="source-" + third.id,
                evidence_id=third.id,
                source_key="camera C",
                episode="later",
                reviewer="Reviewer",
                note="Independent acquisition",
            ),
        )
        result = synthesis(session, first.id)
        assert result["state"] == "MULTI_SOURCE_CONFIRMED"
        assert {first.id, third.id} <= set(result["supporting_evidence"])
        assert result["footprints"] and result["confidence_adjustment"] is None


def test_supersession_preserves_decision_and_current_route_support(tmp_path):
    store = Store(f"sqlite:///{tmp_path / 'supersession.db'}")
    service = MissionService(Perception())
    with store.session(write=True) as session:
        seed(session)
        first = service.demo(session, ObserveRequest())
        service.verify(
            session,
            first.id,
            VerifyRequest(decision="CONFIRMED", reviewer="Reviewer", note="First assessment"),
        )
        replacement = service.observe(
            session,
            "eva-01",
            first.spatial_footprint,
            first.model_output.model_copy(update={"terrain": Terrain.SOIL}),
            "new.png",
            "d" * 64,
            "ground",
            "new view",
            "New evidence contradicts earlier interpretation",
        )
        assert synthesis(session, first.id)["state"] == "CONFLICTING"
        with pytest.raises(ValueError):
            service.verify(
                session,
                replacement.id,
                VerifyRequest(
                    decision="CONFIRMED", reviewer="Reviewer", note="Unresolved conflict"
                ),
            )
        service.verify(
            session,
            replacement.id,
            VerifyRequest(
                decision="CONFIRMED",
                reviewer="Reviewer",
                note="New view supersedes initial interpretation",
                supersedes=[first.id],
                human_terrain=Terrain.SOIL,
            ),
        )
        history = synthesis(session, first.id)
        assert history["state"] == "SUPERSEDED"
        assert history["superseded_by"] == [replacement.id]
        assert first.id not in {e.id for e in active_evidence(session)}
        snapshot = service.snapshot(session, "eva-01")
        assert (
            next(e for e in snapshot.evidence if e.id == first.id).verification_state == "CONFIRMED"
        )
        assert (
            first.id
            not in next(
                r for r in snapshot.routes if r.id == snapshot.mission.active_route_id
            ).evidence_ids
        )
