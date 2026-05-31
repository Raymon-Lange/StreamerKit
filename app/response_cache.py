from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"


def _path(key: str) -> Path:
    return _CACHE_DIR / f"api_{key}.json"


def get(key: str, ttl_seconds: int = 300) -> dict | None:
    path = _path(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(payload["cached_at"])
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age > ttl_seconds:
            return None
        return payload["data"]
    except Exception:
        return None


def set(key: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    _path(key).write_text(json.dumps(payload, ensure_ascii=True, default=str), encoding="utf-8")
