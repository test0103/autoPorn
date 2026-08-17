from __future__ import annotations

from pathlib import Path

import requests

from .api import AdminApiClient
from .classifier import Decision, SectionClassifier, should_reject
from .config import AppConfig
from .image_quality import fetch_and_score
from .logging_excel import append_decisions, read_review_training


class OperationsPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = AdminApiClient(config.api)
        self.classifier = SectionClassifier(
            Path(config.learning.model_dir) / "section_classifier.joblib", aliases=config.selection.category_aliases
        )

    def learn_from_review(self) -> int:
        rows = read_review_training(self.config.learning.review_workbook)
        self.classifier.train(rows)
        return len(rows)

    def plan(self) -> list[Decision]:
        sections = self.client.list_sections()
        movies = []
        for page in range(1, self.config.selection.max_pages + 1):
            movies.extend(self.client.search_movies(self.config.selection.position, page, self.config.selection.page_size))
        remaining = dict(self.config.selection.section_targets)
        decisions: list[Decision] = []
        for movie in movies:
            if movie.is_add:
                continue
            reject_reason = should_reject(movie, self.config.selection.reject_keywords)
            title_score, title_reason = self.classifier.title_appeal_score(movie)
            if not reject_reason and title_score < self.config.selection.min_title_score:
                reject_reason = title_reason
            cover_score = None
            if not reject_reason and movie.img_x and not self.config.api.dry_run:
                try:
                    quality = fetch_and_score(movie.img_x, self.config.api.image_base_url, self.config.api.timeout_seconds)
                    cover_score = quality.score
                    if quality.score < self.config.selection.min_cover_score:
                        reject_reason = "low-cover-quality:" + quality.reason
                except requests.RequestException as exc:  # type: ignore[name-defined]
                    reject_reason = f"cover-fetch-failed:{exc.__class__.__name__}"
            if reject_reason:
                decisions.append(Decision(movie, "reject", None, 1.0, reject_reason, cover_score, title_score))
                continue
            candidates = [s for s in sections if s.name in remaining or s.module_name in remaining or s.sub_module_name in remaining]
            section, confidence, reason = self.classifier.choose_section(movie, candidates or sections)
            if section and remaining:
                key = section.name if section.name in remaining else section.module_name if section.module_name in remaining else section.sub_module_name
                if key in remaining and remaining[key] <= 0:
                    decisions.append(Decision(movie, "skip", section, confidence, "target-filled", cover_score, title_score))
                    continue
                if key in remaining:
                    remaining[key] -= 1
            decisions.append(Decision(movie, "publish_and_classify", section, confidence, reason + ";" + title_reason, cover_score, title_score))
        return decisions

    def execute(self, decisions: list[Decision]) -> None:
        for decision in decisions:
            if decision.action != "publish_and_classify" or not decision.section:
                continue
            self.client.add_movies(self.config.selection.position, [decision.movie.id])
            self.client.add_videos_to_section(decision.section.id, [decision.movie.id])
        append_decisions(self.config.learning.operations_workbook, decisions)
