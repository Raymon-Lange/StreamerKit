from __future__ import annotations

from fastapi import APIRouter, Query

from app import response_cache
from services.pitchers_service import get_streaming_pitcher_review

router = APIRouter()

_TTL = 300


@router.get("/streamers")
async def streamers(
    pitcher: str | None = Query(default=None, description="Filter to a specific pitcher by name"),
    tomorrow: bool = Query(default=False, description="Show tomorrow's starters"),
) -> dict:
    from datetime import date, timedelta
    for_date = date.today() + timedelta(days=1) if tomorrow else date.today()
    cache_key = f"streamers_{for_date.isoformat()}_{pitcher or 'all'}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_streaming_pitcher_review(pitcher=pitcher, for_date=for_date)
    response_cache.set(cache_key, data)
    return data
