import hashlib
import io
import json
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from backend.domain import ModelOutput, Terrain

logger = logging.getLogger(__name__)
CLASSES = [Terrain.SOIL, Terrain.BEDROCK, Terrain.SAND, Terrain.LARGE_ROCKS]


class Perception:
    """A local trained TorchScript model, or a deliberately conservative CV fallback."""

    def __init__(self, model_path: str = ""):
        self.model_path = model_path

    def infer(self, content: bytes) -> ModelOutput:
        pixels = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
        if pixels is None:
            raise ValueError("Image cannot be decoded")
        if self.model_path:
            try:
                return self._torch(pixels)
            except Exception:
                logger.exception("terrain_model_failed")
                return self.unavailable(
                    "Configured terrain model failed; image remains available for review."
                )
        gray = cv2.cvtColor(cv2.resize(pixels, (256, 256)), cv2.COLOR_BGR2GRAY)
        edge_fraction = float(np.mean(cv2.Canny(gray, 70, 140) > 0))
        contrast = float(gray.std() / 255)
        return ModelOutput(
            terrain=Terrain.ROUGH if edge_fraction > 0.12 else Terrain.UNKNOWN,
            confidence=0.3,
            confidence_label="low",
            engine="opencv-texture-candidate",
            version="1.0",
            features={"edge_fraction": round(edge_fraction, 4), "contrast": round(contrast, 4)},
            limitations=[
                "Texture heuristic is not a trained Mars terrain classifier.",
                "Lighting and perspective can mimic roughness. "
                "Human terrain identification is required.",
                "No physical soil strength, mineral, or hazard measurement is inferred.",
            ],
        )

    def _torch(self, pixels: np.ndarray) -> ModelOutput:
        import torch

        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        model_bytes = Path(self.model_path).read_bytes()
        digest = hashlib.sha256(model_bytes).hexdigest()
        metadata_bytes = Path(self.model_path).with_suffix(".json").read_bytes()
        metadata = json.loads(metadata_bytes)
        version = (
            f"{Path(self.model_path).stem}:{digest}:" + hashlib.sha256(metadata_bytes).hexdigest()
        )
        if metadata.get("model_sha256") != digest:
            raise ValueError("Checkpoint hash does not match model metadata")
        if metadata.get("preprocessing_version") != "rgb-bilinear256-mask-nearest-v1":
            raise ValueError("Unsupported model preprocessing version")
        if metadata.get("prototype_validation_passed") is False:
            return self.unavailable(
                "Candidate failed prototype validation; human identification required."
            ).model_copy(update={"version": version})
        model = torch.jit.load(io.BytesIO(model_bytes), map_location="cpu").eval()
        rgb = np.array(
            Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)).resize(
                (256, 256), Image.Resampling.BILINEAR
            )
        )
        tensor = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255
        with torch.inference_mode():
            logits = model(tensor)
            if tuple(logits.shape) != (1, 4, 256, 256):
                raise ValueError("Expected AI4Mars-compatible four-class pixel logits")
            probabilities = torch.softmax(logits, dim=1)
            labels = probabilities.argmax(dim=1)
            fractions = {
                c.value: float((labels == i).float().mean()) for i, c in enumerate(CLASSES)
            }
            confidence = float(probabilities.max(dim=1).values.mean())
            if not np.isfinite(confidence):
                raise ValueError("Nonfinite model output")
        terrain = max(CLASSES, key=lambda c: fractions[c.value])
        supported = terrain.value in metadata.get("trained_classes", [c.value for c in CLASSES])
        classification_enabled = metadata.get("classification_enabled", True)
        return ModelOutput(
            terrain=terrain
            if confidence >= 0.5 and supported and classification_enabled
            else Terrain.UNKNOWN,
            confidence=confidence,
            confidence_label="high"
            if confidence >= 0.8
            else "moderate"
            if confidence >= 0.5
            else "low",
            engine="torchscript-ai4mars",
            version=version,
            class_fractions=fractions,
            limitations=[
                "Model confidence is uncalibrated evidence, not a safety probability.",
                "Single-view terrain classification does not establish traversability.",
                *(
                    []
                    if classification_enabled
                    else [
                        "Experimental checkpoint: weak held-out performance; mission terrain "
                        "classification disabled. Raw scores/fractions retained; "
                        "human identification required."
                    ]
                ),
            ],
        )

    @staticmethod
    def unavailable(message: str) -> ModelOutput:
        return ModelOutput(
            terrain=Terrain.UNKNOWN,
            confidence=0,
            confidence_label="unavailable",
            engine="unavailable",
            version="1.0",
            limitations=[message],
        )
