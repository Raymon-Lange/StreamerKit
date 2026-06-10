from __future__ import annotations

import time
from datetime import datetime, timezone

from models.feed_health import CacheEntry, FeedHealthSnapshot, FeedSource
from utils.cache_retention import RETENTION
from utils.cache_store import store as _cache


def _latest_collector_entry(cache_key: str) -> tuple[dict | None, float | None]:
    keys = _cache.list_keys("collector")
    matches = [(k, ts) for k, ts in keys if k.startswith(cache_key)]
    if not matches:
        return None, None
    best_key, cached_at = max(matches, key=lambda x: x[1])
    payload = _cache.get_stale("collector", best_key)
    return payload, time.time() - cached_at


def build_snapshot() -> FeedHealthSnapshot:
    failure_records: dict[str, dict] = {}
    for key, _ in _cache.list_keys("feed_failures"):
        rec = _cache.get_stale("feed_failures", key)
        if rec:
            failure_records[rec.get("collector", key)] = rec

    sources: list[FeedSource] = []
    for cache_key, ttl in RETENTION.items():
        payload, age_s = _latest_collector_entry(cache_key)

        if age_s is None:
            status = "missing"
        elif ttl is not None and age_s > ttl:
            status = "stale"
        else:
            status = "fresh"

        failure = failure_records.get(cache_key)
        sources.append(FeedSource(
            key=cache_key,
            status=status,
            age_seconds=age_s,
            ttl_seconds=ttl,
            last_url=payload.get("url") if payload else None,
            fetched_at=payload.get("fetched_at") if payload else None,
            last_error_type=failure.get("error_type") if failure else None,
            last_error_message=failure.get("error_message") if failure else None,
            last_error_at=failure.get("timestamp") if failure else None,
        ))

    now = time.time()
    response_entries: list[CacheEntry] = []
    for key, cached_at, ttl_s in _cache.list_entries("response"):
        if ttl_s is None:
            continue
        age_s = now - cached_at
        remaining = ttl_s - age_s
        if remaining <= 0:
            continue
        response_entries.append(CacheEntry(
            key=key,
            age_seconds=age_s,
            ttl_seconds=ttl_s,
            remaining_seconds=remaining,
        ))

    return FeedHealthSnapshot(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sources=sources,
        response_cache=response_entries,
    )
