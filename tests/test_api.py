import pytest

pytest.importorskip("requests")

from autoporn_ops.api import AdminApiClient
from autoporn_ops.config import ApiConfig


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append((url, json, timeout))
        if url.endswith("/api/web/admin/laosiji/movie/search"):
            return FakeResponse({"code": 200, "data": {"data": [{"id": "m1", "name": "测试", "isAdd": False}]}})
        if url.endswith("/api/web/admin/module/section/all"):
            return FakeResponse({"code": 200, "data": []})
        return FakeResponse({"code": 200, "data": "", "msg": "success"})


def test_authorization_can_be_read_from_yaml_config():
    client = AdminApiClient(ApiConfig(base_url="https://example.test", authorization="yaml-token"))
    assert client.session.headers["Authorization"] == "yaml-token"


def test_dry_run_reads_search_but_blocks_mutations():
    client = AdminApiClient(ApiConfig(base_url="https://example.test", authorization="token", dry_run=True))
    fake_session = FakeSession()
    fake_session.headers.update(client.session.headers)
    client.session = fake_session

    movies = client.search_movies("guochan", 1, 100)
    add_response = client.add_movies("guochan", ["m1"])

    assert movies[0].id == "m1"
    assert len(fake_session.calls) == 1
    assert fake_session.calls[0][0].endswith("/api/web/admin/laosiji/movie/search")
    assert add_response["msg"] == "dry-run"
    assert add_response["request"]["path"].endswith("/movie/add")
