from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from .models import Movie, Section


RISK_KEYWORDS = ["未成年", "幼女", "偷拍", "迷奸", "昏迷", "猎奇", "重口", "血", "排泄", "包皮垢"]
DEFAULT_CATEGORY_ALIASES: dict[str, list[str]] = {
    "精选": ["女神", "极品", "高颜值", "清纯", "纯欲", "明星", "美乳", "黑丝"],
    "国产": ["国产", "国语", "大陆", "酒店", "探花", "约炮", "按摩", "足浴"],
    "网黄": ["网红", "网黄", "主播", "直播", "福利姬", "自拍", "原创"],
    "AV": ["AV", "女优", "番号", "日本", "无码", "有码", "中文字幕"],
    "乱伦": ["乱伦", "继母", "嫂子", "姐夫", "岳母", "母子", "父女"],
    "传媒": ["传媒", "麻豆", "天美", "蜜桃", "果冻", "皇家华人", "剧情", "导演"],
    "重口味": ["重口", "猎奇", "另类", "粗暴"],
    "猎奇": ["猎奇", "奇葩", "变态", "异物"],
    "调教": ["调教", "SM", "捆绑", "羞辱", "奴", "主仆"],
}
ATTRACTIVE_KEYWORDS = ["女神", "极品", "高颜值", "清纯", "纯欲", "明星", "黑丝", "美腿", "制服", "剧情", "巨乳", "粉嫩"]
UNATTRACTIVE_KEYWORDS = ["呕吐", "排泄", "包皮垢", "重口", "猎奇", "血腥", "脏", "恶心"]


@dataclass(slots=True)
class Decision:
    movie: Movie
    action: str
    section: Section | None
    confidence: float
    reason: str
    cover_score: float | None = None
    title_score: float | None = None


class SectionClassifier:
    def __init__(self, model_path: str | Path | None = None, aliases: dict[str, list[str]] | None = None) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.aliases = {**DEFAULT_CATEGORY_ALIASES, **(aliases or {})}
        self.pipeline: Any | None = None
        if self.model_path and self.model_path.exists() and find_spec("joblib") is not None:
            import joblib

            self.pipeline = joblib.load(self.model_path)

    @staticmethod
    def text_for(movie: Movie) -> str:
        return " ".join([movie.name, movie.cat_name, *movie.tag_names])

    @staticmethod
    def title_appeal_score(movie: Movie) -> tuple[float, str]:
        text = SectionClassifier.text_for(movie)
        score = 50.0
        hits: list[str] = []
        for keyword in ATTRACTIVE_KEYWORDS:
            if keyword in text:
                score += 6
                hits.append(keyword)
        for keyword in UNATTRACTIVE_KEYWORDS:
            if keyword in text:
                score -= 18
                hits.append(f"negative:{keyword}")
        if 8 <= len(movie.name) <= 36:
            score += 8
            hits.append("readable-length")
        elif len(movie.name) > 60:
            score -= 10
            hits.append("too-long")
        return max(0, min(100, score)), "title-appeal:" + (",".join(hits) if hits else "neutral")

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
            for canonical, aliases in self.aliases.items():
                section_text = " ".join(words)
                if canonical in section_text:
                    words.extend(aliases)
            hits = [word for word in words if word and (word in text or any(part and part in word for part in movie.tag_names))]
            scored.append((len(set(hits)), section, sorted(set(hits))))
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored[0][0] > 0:
            return scored[0][1], min(0.9, 0.35 + scored[0][0] * 0.12), "keyword:" + ",".join(scored[0][2])
        return sections[0], 0.2, "fallback-first-section"


def should_reject(movie: Movie, reject_keywords: list[str]) -> str | None:
    text = SectionClassifier.text_for(movie)
    for keyword in [*RISK_KEYWORDS, *reject_keywords]:
        if keyword and keyword in text:
            return f"risk-keyword:{keyword}"
    return None
