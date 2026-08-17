from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ApiConfig:
    base_url: str
    authorization: str = ""
    authorization_env: str = "AIPAPA_AUTHORIZATION"
    timeout_seconds: int = 20
    dry_run: bool = True
    image_base_url: str | None = None
    image_headers: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class SelectionConfig:
    position: str = "guochan"
    page_size: int = 100
    max_pages: int = 1
    min_cover_score: float = 45.0
    cover_fetch_retries: int = 3
    cover_failure_action: str = "title_only"
    reject_keywords: list[str] = field(default_factory=list)
    section_targets: dict[str, int] = field(default_factory=dict)
    category_aliases: dict[str, list[str]] = field(default_factory=dict)
    min_title_score: float = 35.0


@dataclass(slots=True)
class LearningConfig:
    model_dir: str = "data/models"
    review_workbook: str = "data/review.xlsx"
    operations_workbook: str = "data/operations.xlsx"


@dataclass(slots=True)
class AppConfig:
    api: ApiConfig
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)


def load_config(path: str | Path) -> AppConfig:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    api = ApiConfig(**raw.get("api", {}))
    selection = SelectionConfig(**raw.get("selection", {}))
    learning = LearningConfig(**raw.get("learning", {}))
    return AppConfig(api=api, selection=selection, learning=learning)
