from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FeedSource:
    key: str
    status: str  # "fresh" | "stale" | "missing"
    age_seconds: float | None
    ttl_seconds: float | None
    last_url: str | None
    fetched_at: str | None
    last_error_type: str | None
    last_error_message: str | None
    last_error_at: str | None


@dataclass(slots=True)
class CacheEntry:
    key: str
    age_seconds: float
    ttl_seconds: float
    remaining_seconds: float


@dataclass(slots=True)
class FeedHealthSnapshot:
    generated_at: str
    sources: list[FeedSource]
    response_cache: list[CacheEntry]
