from __future__ import annotations

from utils.cache_store import store as _cache

_NS = "response"
_DEFAULT_TTL = 1800


def get(key: str, ttl_seconds: int = _DEFAULT_TTL) -> dict | None:
    return _cache.get(_NS, key, ttl_seconds=float(ttl_seconds))


def set(key: str, data: dict, ttl_seconds: int = _DEFAULT_TTL) -> None:
    _cache.set(_NS, key, data, ttl_seconds=float(ttl_seconds))


def invalidate_prefix(prefix: str) -> None:
    for key, _cached_at in _cache.list_keys(_NS):
        if key.startswith(prefix):
            _cache.delete(_NS, key)
