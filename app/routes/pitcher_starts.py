from __future__ import annotations

from fastapi import APIRouter, Query

from app import response_cache
from services.pitchers_service import get_pitcher_start_evaluation

router = APIRouter()

_TTL = 300


@router.get("/pitcher-starts")
async def pitcher_starts(
    tomorrow: bool = Query(default=False, description="Evaluate tomorrow instead of today"),
) -> dict:
    from datetime import date, timedelta
    for_date = date.today() + timedelta(days=1) if tomorrow else date.today()
    cache_key = f"pitcher_starts_{for_date.isoformat()}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_pitcher_start_evaluation(for_date=for_date)
    response_cache.set(cache_key, data)
    return data
