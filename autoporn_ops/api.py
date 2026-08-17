from __future__ import annotations

import os
from typing import Any

import requests

from .config import ApiConfig
from .models import Movie, Section


class AdminApiClient:
    def __init__(self, config: ApiConfig) -> None:
        self.config = config
        self.session = requests.Session()
        token = config.authorization or (os.getenv(config.authorization_env, "") if config.authorization_env else "")
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": config.base_url,
            "Referer": f"{config.base_url}/",
        })
        if token:
            self.session.headers["Authorization"] = token

    def _post(self, path: str, payload: dict[str, Any], *, mutate: bool = False) -> dict[str, Any]:
        if mutate and self.config.dry_run:
            return {"code": 200, "data": "", "msg": "dry-run", "request": {"path": path, "payload": payload}}
        response = self.session.post(
            f"{self.config.base_url.rstrip('/')}{path}", json=payload, timeout=self.config.timeout_seconds
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise RuntimeError(f"API failed: {data}")
        return data

    def search_movies(self, position: str, page: int, page_size: int) -> list[Movie]:
        data = self._post("/api/web/admin/laosiji/movie/search", {
            "position": position, "page": str(page), "page_size": str(page_size)
        })
        rows = data.get("data", {}).get("data", []) if isinstance(data.get("data"), dict) else []
        return [Movie.from_api(row) for row in rows]

    def add_movies(self, position: str, ids: list[str]) -> dict[str, Any]:
        return self._post("/api/web/admin/laosiji/movie/add", {"position": position, "ids": ids}, mutate=True)

    def list_sections(self) -> list[Section]:
        data = self._post("/api/web/admin/module/section/all", {})
        return Section.flatten_from_api(data.get("data", []))

    def add_videos_to_section(self, section_id: str, video_ids: list[str]) -> dict[str, Any]:
        return self._post("/api/web/admin/module/video/add/batch", {
            "sectionID": section_id, "videoIDs": ",".join(video_ids)
        }, mutate=True)
