import base64
import io

import numpy as np
import pytest
from PIL import Image

from ai.segmentation import render_segmentation


def test_mask_preserves_classes_and_marks_uncertain_pixels():
    labels = np.zeros((256, 256), dtype=np.int64)
    labels[:, 128:] = 3
    scores = np.ones((256, 256), dtype=float) * 0.9
    scores[:128] = 0.25
    uri, withheld = render_segmentation(labels, scores)
    assert uri.startswith("data:image/png;base64,")
    assert withheld == pytest.approx(0.5)
    with Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))) as image:
        assert image.size == (256, 256)
        assert image.mode == "P"
        assert image.getpixel((10, 10)) == 4
        assert image.getpixel((10, 200)) == 0
        assert image.getpixel((200, 200)) == 3


def test_nonfinite_or_unexpected_segmentation_is_refused():
    labels = np.zeros((256, 256), dtype=np.int64)
    with pytest.raises(ValueError, match="scores"):
        render_segmentation(labels, np.full((256, 256), np.nan))
    with pytest.raises(ValueError, match="class"):
        render_segmentation(labels + 6, np.ones((256, 256)))
    with pytest.raises(ValueError, match="256"):
        render_segmentation(labels[:2], np.ones((2, 256)))
