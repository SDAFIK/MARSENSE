"""Create reviewed, explicit replay annotations, never masquerading as model inference."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import ROOT
from backend.domain import ModelOutput, Terrain, rectangle


def main() -> None:
    scenarios = {}
    for name, terrain, confidence, bounds in [
        ("obstacles", Terrain.OBSTACLES, 0.9, (520, 320, 680, 480)),
        ("match", Terrain.SOIL, 0.9, (520, 320, 680, 480)),
        ("minor", Terrain.SAND, 0.9, (520, 640, 680, 760)),
        ("weak", Terrain.ROUGH, 0.3, (520, 320, 680, 480)),
        ("failure", Terrain.UNKNOWN, 0, (520, 320, 680, 480)),
        ("dynamic", Terrain.UNKNOWN, 0.3, (520, 320, 680, 480)),
    ]:
        output = ModelOutput(
            terrain=terrain,
            confidence=confidence,
            confidence_label="reviewed demo annotation"
            if confidence >= 0.5
            else "low"
            if confidence
            else "unavailable",
            engine="curated-demo-replay",
            version="jezero-scenario-v1",
            limitations=[
                "Replay annotation for a fictional EVA; not a trained model prediction.",
                "PIA26072 is a public-release Navcam mosaic; location and footprint are simulated.",
                "No mechanical strength, mineral composition, or safety probability is measured.",
            ],
        )
        scenarios[name] = {
            "footprint": rectangle(*bounds).model_dump(),
            "model_output": output.model_dump(),
            "metadata_note": "Simulated 160 × 160 m local footprint (minor scenario 160 × 120 m). "
            "No camera-to-ground reconstruction or PLACES registration is claimed.",
            "observation_type": "visibility" if name == "dynamic" else "terrain",
        }
    (ROOT / "data/demo/scenarios.json").write_text(json.dumps(scenarios, indent=2))


if __name__ == "__main__":
    main()
