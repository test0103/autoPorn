from io import BytesIO

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image

from autoporn_ops.image_quality import score_image_bytes


def make_image(color):
    image = Image.new("RGB", (32, 32), color)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_red_dominant_cover_is_penalized():
    score = score_image_bytes(make_image((220, 20, 20)))
    assert score.score < 45
    assert "large-red-area" in score.reason
