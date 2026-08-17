from autoporn_ops.classifier import SectionClassifier, should_reject
from autoporn_ops.models import Movie, Section, Tag


def test_rejects_risk_keywords_from_title_and_tags():
    movie = Movie(id="1", name="酒店偷拍视频", tags=[Tag(id="t", name="眼镜")])
    assert should_reject(movie, []) == "risk-keyword:偷拍"


def test_keyword_section_match_uses_dynamic_sections():
    movie = Movie(id="1", name="医生制服剧情", tags=[Tag(id="t", name="制服")])
    sections = [
        Section(id="a", name="清纯", module_name="精选", sub_module_name="精选"),
        Section(id="b", name="制服诱惑", module_name="精选", sub_module_name="精选"),
    ]
    section, confidence, reason = SectionClassifier().choose_section(movie, sections)
    assert section and section.id == "b"
    assert confidence > 0.3
    assert reason.startswith("keyword")
