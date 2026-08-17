from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from .models import Movie, Section


RISK_KEYWORDS = ["未成年", "幼女", "偷拍", "迷奸", "昏迷", "猎奇", "重口", "血", "排泄", "包皮垢"]


@dataclass(slots=True)
class Decision:
    movie: Movie
    action: str
    section: Section | None
    confidence: float
    reason: str
    cover_score: float | None = None


class SectionClassifier:
    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.pipeline: Any | None = None
        if self.model_path and self.model_path.exists() and find_spec("joblib") is not None:
            import joblib

            self.pipeline = joblib.load(self.model_path)

    @staticmethod
    def text_for(movie: Movie) -> str:
        return " ".join([movie.name, movie.cat_name, *movie.tag_names])

    def train(self, rows: list[tuple[str, str]]) -> None:
        if not rows:
            return
        if find_spec("joblib") is None or find_spec("sklearn") is None:
            raise RuntimeError("Install scikit-learn and joblib to train the local classifier")
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import SGDClassifier
        from sklearn.pipeline import Pipeline

        texts, labels = zip(*rows)
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))),
            ("clf", SGDClassifier(loss="log_loss", random_state=42, max_iter=1000, tol=1e-3)),
        ])
        self.pipeline.fit(list(texts), list(labels))
        if self.model_path:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.pipeline, self.model_path)

    def choose_section(self, movie: Movie, sections: list[Section]) -> tuple[Section | None, float, str]:
        if not sections:
            return None, 0.0, "no-sections"
        text = self.text_for(movie)
        if self.pipeline is not None:
            label = str(self.pipeline.predict([text])[0])
            for section in sections:
                if section.id == label or section.name == label:
                    return section, 0.85, "trained-model"
        scored: list[tuple[int, Section, list[str]]] = []
        for section in sections:
            words = [section.name, section.module_name, section.sub_module_name, *section.tags]
            hits = [word for word in words if word and (word in text or any(part and part in word for part in movie.tag_names))]
            scored.append((len(hits), section, hits))
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored[0][0] > 0:
            return scored[0][1], min(0.8, 0.35 + scored[0][0] * 0.15), "keyword:" + ",".join(scored[0][2])
        return sections[0], 0.2, "fallback-first-section"


def should_reject(movie: Movie, reject_keywords: list[str]) -> str | None:
    text = SectionClassifier.text_for(movie)
    for keyword in [*RISK_KEYWORDS, *reject_keywords]:
        if keyword and keyword in text:
            return f"risk-keyword:{keyword}"
    return None
