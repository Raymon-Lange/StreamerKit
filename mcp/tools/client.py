from __future__ import annotations

import os

import requests


class ApiClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("STREAMERKIT_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        self.api_key = os.getenv("API_KEY", "").strip()

    def get(self, path: str, params: dict | None = None) -> dict:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        response = requests.get(f"{self.base_url}{path}", params=params or {}, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
