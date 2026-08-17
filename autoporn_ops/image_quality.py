from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from io import BytesIO
from urllib.parse import urljoin

import requests


@dataclass(slots=True)
class CoverQuality:
    score: float
    reason: str


class CoverImageError(RuntimeError):
    """Raised when cover bytes cannot be decoded as a normal image."""


def score_image_bytes(content: bytes) -> CoverQuality:
    if find_spec("PIL") is None:
        raise CoverImageError("Install Pillow to score cover images")
    from PIL import Image, ImageStat, UnidentifiedImageError

    try:
        with Image.open(BytesIO(content)) as image:
            image = image.convert("RGB").resize((96, 96))
            stat = ImageStat.Stat(image)
            brightness = sum(stat.mean) / 3
            contrast = sum(stat.stddev) / 3
            pixels = list(image.getdata())
            red_ratio = sum(1 for r, g, b in pixels if r > 150 and g < 90 and b < 90) / len(pixels)
            dark_ratio = sum(1 for r, g, b in pixels if (r + g + b) / 3 < 25) / len(pixels)
            overbright_ratio = sum(1 for r, g, b in pixels if (r + g + b) / 3 > 245) / len(pixels)
            score = 50 + min(contrast, 45) - abs(brightness - 125) * 0.15
            if red_ratio > 0.22:
                score -= 35
            if dark_ratio > 0.55 or overbright_ratio > 0.55:
                score -= 25
            reasons = [f"brightness={brightness:.1f}", f"contrast={contrast:.1f}"]
            if red_ratio > 0.22:
                reasons.append("large-red-area")
            if dark_ratio > 0.55:
                reasons.append("too-dark")
            if overbright_ratio > 0.55:
                reasons.append("too-bright")
            return CoverQuality(max(0, min(100, score)), ";".join(reasons))
    except (UnidentifiedImageError, OSError) as exc:
        raise CoverImageError(f"cover bytes are not a supported image: {exc.__class__.__name__}") from exc


def fetch_and_score(
    path: str,
    base_url: str | None,
    timeout: int,
    retries: int = 3,
    headers: dict[str, str] | None = None,
) -> CoverQuality:
    url = urljoin((base_url or "").rstrip("/") + "/", path)
    last_error: requests.RequestException | None = None
    for _ in range(max(1, retries)):
        try:
            response = requests.get(url, timeout=timeout, headers=headers or {})
            response.raise_for_status()
            return score_image_bytes(response.content)
        except requests.RequestException as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise CoverImageError("cover fetch failed without a requests error")
