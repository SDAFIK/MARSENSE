import hashlib
import io
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from PIL import Image
from shapely.geometry import LineString, shape

from backend.config import Settings
from backend.domain import Evidence, Verification, rectangle
from backend.main import create_app
from backend.store import all_of


def observe(client: TestClient, scenario: str = "obstacles") -> dict:
    response = client.post("/api/observations/demo", json={"scenario": scenario})
    assert response.status_code == 200, response.text
    return response.json()


def verify(client: TestClient, evidence: dict, decision: str = "CONFIRMED", **kwargs: str) -> dict:
    response = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        json={
            "decision": decision,
            "reviewer": "A. Rahman",
            "note": "I inspected the terrain within the footprint.",
            **kwargs,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def snapshot(client: TestClient, mission: str = "eva-01") -> dict:
    response = client.get(f"/api/missions/{mission}")
    assert response.status_code == 200
    return response.json()


def test_a_matching_soil_no_alert(client: TestClient) -> None:
    evidence = observe(client, "match")
    assert evidence["discrepancy"] == "MATCH"
    assert evidence["consequence"]["alert"] is None
    assert snapshot(client)["routes"][0]["status"] == "ACTIVE"


def test_b_minor_off_route_silent(client: TestClient) -> None:
    evidence = observe(client, "minor")
    assert evidence["discrepancy"] == "MINOR_DIFFERENCE"
    assert not evidence["consequence"]["relevant"]
    assert evidence["consequence"]["alert"] is None
    assert len(snapshot(client)["evidence"]) == 4


def test_c_significant_discrepancy_alert_without_overwrite(client: TestClient) -> None:
    original = snapshot(client)
    evidence = observe(client)
    state = snapshot(client)
    assert evidence["discrepancy"] == "SIGNIFICANT_DIFFERENCE"
    assert evidence["consequence"]["alert"] == "PROVISIONAL SAFETY ALERT"
    assert evidence["consequence"]["assumption_ids"] == ["assumption-corridor"]
    assert state["routes"][0]["coordinates"] == original["routes"][0]["coordinates"]
    assert state["routes"][0]["status"] == "CHALLENGED"
    assert (
        next(r for r in state["regions"] if r["id"] == "corridor")["prior_interpretation"] == "soil"
    )
    assert (
        next(r for r in state["regions"] if r["id"] == "corridor")["knowledge_state"]
        == "PROVISIONAL"
    )


def test_d_weak_confidence_alert_no_automatic_permanence(client: TestClient) -> None:
    evidence = observe(client, "weak")
    assert evidence["discrepancy"] == "INSUFFICIENT_EVIDENCE"
    assert evidence["consequence"]["safety_critical"]
    response = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        json={
            "decision": "CONFIRMED",
            "reviewer": "A. Rahman",
            "note": "Looks rough.",
        },
    )
    assert response.status_code == 422
    assert (
        client.get(f"/api/evidence/{evidence['id']}").json()["verification_state"] == "PROVISIONAL"
    )
    assert len(snapshot(client)["routes"]) == 1
    verify(client, evidence, human_terrain="obstacle-rich terrain")
    assert snapshot(client)["routes"][-1]["name"] == "Route Beta"


def test_e_verified_footprint_updates_cost_and_route(client: TestClient) -> None:
    priors = [e for e in snapshot(client)["evidence"] if e["source_type"] == "orbital"]
    evidence = observe(client)
    verify(client, evidence)
    state = snapshot(client)
    region = next(r for r in state["regions"] if r["id"] == "corridor")
    assert region["knowledge_state"] == "GROUND_OBSERVED"
    assert region["prior_interpretation"] == "soil"
    assert [e for e in state["evidence"] if e["source_type"] == "orbital"] == priors
    assert state["assumptions"][0]["status"] == "CHALLENGED"
    beta = state["routes"][-1]
    assert beta["name"] == "Route Beta"
    assert beta["distance_m"] > state["routes"][0]["distance_m"]
    assert not shape(evidence["spatial_footprint"]).intersects(LineString(beta["coordinates"]))
    assert evidence["id"] in beta["evidence_ids"]
    assert "A. Rahman" in beta["explanation"]
    future = snapshot(client, "eva-02")
    assert future["mission"]["inherited_evidence"] == [evidence["id"]]
    assert future["routes"][-1]["coordinates"] == beta["coordinates"]


def test_f_restart_retains_evidence_and_inheritance(settings: Settings) -> None:
    with TestClient(create_app(settings)) as first:
        evidence = observe(first)
        verify(first, evidence)
    with TestClient(create_app(settings)) as second:
        state = snapshot(second)
        assert (
            next(e for e in state["evidence"] if e["id"] == evidence["id"])["verified_by"]
            == "A. Rahman"
        )
        assert len(state["routes"]) == 2
        assert evidence["id"] in snapshot(second, "eva-02")["mission"]["inherited_evidence"]


def test_g_rejection_auditable_prior_retained(client: TestClient) -> None:
    evidence = observe(client)
    verify(client, evidence, "REJECTED")
    state = snapshot(client)
    assert (
        next(e for e in state["evidence"] if e["id"] == evidence["id"])["verification_state"]
        == "REJECTED"
    )
    assert (
        next(r for r in state["regions"] if r["id"] == "corridor")["knowledge_state"]
        == "ORBITAL_ONLY"
    )
    assert state["routes"][0]["status"] == "ACTIVE"
    assert state["assumptions"][0]["status"] == "SUPPORTED"
    assert len(state["routes"]) == 1


def test_h_external_nasa_offline_cached_demo(client: TestClient, monkeypatch) -> None:
    import urllib.request

    def offline(*args, **kwargs):
        raise OSError("NASA unavailable")

    monkeypatch.setattr(urllib.request, "urlopen", offline)
    assert client.get("/api/assets/jezero-ctx.png").status_code == 200
    assert client.get("/api/assets/jezero-hirise.png").status_code == 200
    verify(client, observe(client))
    assert snapshot(client)["routes"][-1]["name"] == "Route Beta"


def test_dynamic_never_updates_permanent_terrain(client: TestClient) -> None:
    evidence = observe(client, "dynamic")
    assert evidence["valid_until"]
    verify(client, evidence)
    state = snapshot(client)
    assert len(state["routes"]) == 1
    assert all(r["knowledge_state"] == "ORBITAL_ONLY" for r in state["regions"])
    assert not snapshot(client, "eva-02")["mission"]["inherited_evidence"]


def test_idempotent_verification_no_duplicate_routes(client: TestClient) -> None:
    evidence = observe(client)
    verify(client, evidence)
    verify(client, evidence)
    assert len(snapshot(client)["routes"]) == 2
    assert len([e for e in snapshot(client)["events"] if e["kind"] == "VERIFICATION"]) == 1


def test_concurrent_confirmation_serializes(client: TestClient) -> None:
    evidence = observe(client)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: verify(client, evidence), range(2)))
    assert all(r["verification_state"] == "CONFIRMED" for r in results)
    assert len(snapshot(client)["routes"]) == 2


def test_prior_and_final_decision_immutable(client: TestClient) -> None:
    response = client.post(
        "/api/evidence/prior-corridor/verify",
        json={
            "decision": "REJECTED",
            "reviewer": "Astronaut",
            "note": "Cannot replace prior",
        },
    )
    assert response.status_code == 422
    evidence = observe(client)
    verify(client, evidence)
    response = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        json={
            "decision": "REJECTED",
            "reviewer": "Astronaut",
            "note": "Cannot undo history",
        },
    )
    assert response.status_code == 422


def test_conflicting_ground_evidence_requires_new_observation(client: TestClient) -> None:
    verify(client, observe(client))
    match = observe(client, "match")
    assert match["discrepancy"] == "CONFLICTING_EVIDENCE"
    response = client.post(
        f"/api/evidence/{match['id']}/verify",
        json={
            "decision": "CONFIRMED",
            "reviewer": "Astronaut",
            "note": "Conflicting observation",
        },
    )
    assert response.status_code == 422
    assert (
        next(r for r in snapshot(client)["regions"] if r["id"] == "corridor")["knowledge_state"]
        == "CONFLICTING"
    )


def test_real_upload_conservative_fallback(client: TestClient) -> None:
    content = io.BytesIO()
    Image.new("RGB", (80, 80), "gray").save(content, "PNG")
    response = client.post(
        "/api/observations/upload",
        files={"file": ("terrain.png", content.getvalue(), "image/png")},
        data={
            "mission_id": "eva-01",
            "footprint": rectangle(520, 320, 680, 480).model_dump_json(),
        },
    )
    assert response.status_code == 200, response.text
    evidence = response.json()
    assert evidence["source_type"] == "ground"
    assert evidence["model_output"]["engine"] == "opencv-texture-candidate"
    assert evidence["model_confidence"] < 0.5
    assert client.get(evidence["raw_asset_reference"]).status_code == 200
    observation = client.get(f"/api/observations/{evidence['observation_id']}").json()
    assert len(observation["asset_sha256"]) == 64
    assert observation["asset_sha256"] == hashlib.sha256(content.getvalue()).hexdigest()
    assert observation["model_input_sha256"] != observation["asset_sha256"]
    original = client.get(observation["original_asset_reference"])
    assert original.content == content.getvalue()
    assert original.headers["content-type"] == "application/octet-stream"
    assert original.headers["x-content-type-options"] == "nosniff"
    verify(client, evidence, human_terrain="obstacle-rich terrain")
    assert snapshot(client)["routes"][-1]["name"] == "Route Beta"


def test_upload_rejects_invalid_and_oversized_files(client: TestClient) -> None:
    form = {"footprint": rectangle(520, 320, 680, 480).model_dump_json()}
    for content, mime, status in [
        (b"fake", "image/jpeg", 422),
        (b"<script>", "text/html", 415),
        (b"0" * (8 * 1024 * 1024 + 1), "image/jpeg", 413),
    ]:
        response = client.post(
            "/api/observations/upload", files={"file": ("file", content, mime)}, data=form
        )
        assert response.status_code == status
    assert client.get("/api/assets/not-a-file.jpg").status_code == 404


def test_needs_more_evidence_remains_provisional(client: TestClient) -> None:
    evidence = observe(client, "weak")
    verify(client, evidence, "NEEDS_MORE_EVIDENCE")
    assert len(snapshot(client)["routes"]) == 1
    with client.app.state.store.session() as session:
        assert all_of(session, Evidence)[-1].verification_state in set(Verification)


def test_expired_dynamic_evidence_cannot_confirm_or_challenge_route(client: TestClient) -> None:
    from backend.store import get, put

    evidence = observe(client, "dynamic")
    with client.app.state.store.session(write=True) as session:
        expired = get(session, Evidence, evidence["id"])
        expired.valid_until = "2020-01-01T00:00:00+00:00"
        put(session, expired)
    state = snapshot(client)
    assert next(e for e in state["evidence"] if e["id"] == evidence["id"])["stale"]
    assert state["routes"][-1]["status"] == "ACTIVE"
    response = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        json={
            "decision": "CONFIRMED",
            "reviewer": "Astronaut",
            "note": "Expired condition reviewed",
        },
    )
    assert response.status_code == 422
    assert "expired" in response.json()["detail"]


def test_unknown_high_score_needs_human_identification(client: TestClient) -> None:
    from backend.store import get, put

    evidence = observe(client, "failure")
    with client.app.state.store.session(write=True) as session:
        record = get(session, Evidence, evidence["id"])
        record.model_confidence = 0.95
        put(session, record)
    response = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        json={"decision": "CONFIRMED", "reviewer": "Astronaut", "note": "Unknown terrain reviewed"},
    )
    assert response.status_code == 422
    assert len(snapshot(client)["routes"]) == 1


def test_whitespace_reviewer_and_note_rejected(client: TestClient) -> None:
    evidence = observe(client)
    for reviewer, note in [("   ", "Ground reviewed"), ("Astronaut", "    ")]:
        response = client.post(
            f"/api/evidence/{evidence['id']}/verify",
            json={"decision": "CONFIRMED", "reviewer": reviewer, "note": note},
        )
        assert response.status_code == 422
    assert (
        client.get(f"/api/evidence/{evidence['id']}").json()["verification_state"] == "PROVISIONAL"
    )


def test_strong_model_cannot_confirm_explicit_unknown_override(client: TestClient) -> None:
    evidence = observe(client, "match")
    before = snapshot(client)
    response = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        json={
            "decision": "CONFIRMED",
            "reviewer": "Astronaut",
            "note": "The terrain cannot be identified.",
            "human_terrain": "unknown",
        },
    )
    assert response.status_code == 422
    assert client.get(f"/api/evidence/{evidence['id']}").json() == evidence
    assert snapshot(client) == before


def test_human_interpretation_and_decision_preserve_original_inference(client: TestClient) -> None:
    evidence = observe(client, "weak")
    original = client.get(f"/api/observations/{evidence['observation_id']}").json()
    reviewed = verify(client, evidence, human_terrain="large rocks")
    record = client.get(f"/api/evidence/{evidence['id']}/history").json()
    assert record["decisions"][0]["decision"] == "CONFIRMED"
    assert record["decisions"][0]["reviewer"] == "A. Rahman"
    assert record["interpretations"][0]["terrain"] == "large rocks"
    assert record["interpretations"][0]["decision_id"] == record["decisions"][0]["id"]
    assert reviewed["observed_value"] == "large rocks"
    assert client.get(f"/api/observations/{evidence['observation_id']}").json() == original
    verify(client, evidence, human_terrain="large rocks")
    assert client.get(f"/api/evidence/{evidence['id']}/history").json() == record


def test_consequence_names_only_intersected_segment(client: TestClient) -> None:
    content = io.BytesIO()
    Image.new("RGB", (32, 32), "gray").save(content, "PNG")
    evidence = client.post(
        "/api/observations/upload",
        files={"file": ("terrain.png", content.getvalue(), "image/png")},
        data={"mission_id": "eva-02", "footprint": rectangle(160, 320, 240, 480).model_dump_json()},
    ).json()
    assert evidence["consequence"]["route_segment_ids"] == ["eva-02-alpha-segment-1"]
    assert evidence["consequence"]["assumption_ids"] == []
    assert evidence["consequence"]["target_ids"] == []


def test_api_validation_and_production_auth(settings: Settings) -> None:
    settings.environment = "production"
    settings.api_token = "x" * 32
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/missions/eva-01").status_code == 401
        assert (
            client.get(
                "/api/missions/eva-01", headers={"Authorization": "Bearer " + settings.api_token}
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/observations/demo",
                json={"scenario": "obstacles"},
                headers={"Authorization": "Bearer " + settings.api_token},
            ).status_code
            == 401
        )
