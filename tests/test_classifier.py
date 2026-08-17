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


def test_parent_category_alias_maps_dynamic_section():
    movie = Movie(id="2", name="高颜值主播自拍", tags=[Tag(id="t", name="主播")])
    sections = [
        Section(id="domestic", name="国产", module_name="首页", sub_module_name="国产"),
        Section(id="web", name="网黄", module_name="首页", sub_module_name="网黄"),
    ]
    section, confidence, reason = SectionClassifier().choose_section(movie, sections)
    assert section and section.id == "web"
    assert confidence >= 0.47
    assert "主播" in reason


def test_title_appeal_scores_clickable_and_negative_titles():
    good = Movie(id="3", name="高颜值女神制服剧情", tags=[Tag(id="t", name="女神")])
    bad = Movie(id="4", name="重口猎奇包皮垢", tags=[])
    good_score, _ = SectionClassifier.title_appeal_score(good)
    bad_score, reason = SectionClassifier.title_appeal_score(bad)
    assert good_score > bad_score
    assert "negative" in reason
