import pytest

pytest.importorskip("requests")

from autoporn_ops.config import ApiConfig, AppConfig, LearningConfig, SelectionConfig
from autoporn_ops.models import Movie, Section
from autoporn_ops.pipeline import OperationsPipeline


class FakeClient:
    def list_sections(self):
        return [Section(id="s1", name="网黄", module_name="首页", sub_module_name="网黄")]

    def search_movies(self, position, page, page_size):
        return [Movie(id="m1", name="高颜值主播自拍", img_x="missing.jpg", tags=[])]

    def add_movies(self, position, ids):
        return {"code": 200}

    def add_videos_to_section(self, section_id, video_ids):
        return {"code": 200}


def test_cover_fetch_or_decode_failure_falls_back_to_title_only(monkeypatch, tmp_path):
    import requests

    config = AppConfig(
        api=ApiConfig(base_url="https://example.test", dry_run=True),
        selection=SelectionConfig(section_targets={"网黄": 1}, cover_fetch_retries=2),
        learning=LearningConfig(model_dir=str(tmp_path)),
    )
    pipeline = OperationsPipeline(config)
    pipeline.client = FakeClient()

    def fail_fetch(*args, **kwargs):
        raise RuntimeError("unsupported bnc cover")

    monkeypatch.setattr("autoporn_ops.pipeline.fetch_and_score", fail_fetch)
    decisions = pipeline.plan()

    assert decisions[0].action == "publish_and_classify"
    assert "cover-fetch-failed" in decisions[0].reason
    assert "title-only" in decisions[0].reason
