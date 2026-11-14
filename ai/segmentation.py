"""Bounded, explicitly uncalibrated pixel-mask presentation for research inference."""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

# Soil, bedrock, sand, large rocks, abstained. Presentation colors, not hazard levels.
PALETTE = [(185, 134, 86), (96, 171, 215), (244, 205, 126), (207, 107, 113), (95, 110, 126)]


def render_segmentation(
    labels: np.ndarray, scores: np.ndarray, threshold: float = 0.5,
) -> tuple[str, float]:
    """Return a small indexed PNG data URI and the fraction withheld by score."""
    if labels.shape != (256, 256) or scores.shape != labels.shape:
        raise ValueError("Expected 256 x 256 segmentation data")
    if not np.issubdtype(labels.dtype, np.integer) or not np.isin(labels, [0, 1, 2, 3]).all():
        raise ValueError("Invalid terrain class")
    if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any():
        raise ValueError("Invalid pixel scores")
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Invalid display abstention threshold")
    abstained = scores < threshold
    indices = np.where(abstained, 4, labels).astype(np.uint8)
    image = Image.fromarray(indices)
    palette = [value for color in PALETTE for value in color]
    image.putpalette(palette + [0] * (768 - len(palette)))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    content = buffer.getvalue()
    if len(content) > 100_000:
        raise ValueError("Segmentation PNG exceeds bounded presentation size")
    return "data:image/png;base64," + base64.b64encode(content).decode("ascii"), float(
        abstained.mean()
    )
