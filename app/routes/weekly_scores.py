from __future__ import annotations

from fastapi import APIRouter, Query

from app import response_cache
from services.scores_service import get_weekly_scores

router = APIRouter()

_TTL = 3600


@router.get("/weekly-scores")
async def weekly_scores(
    period: int | None = Query(default=None, description="Specific matchup period; defaults to current week"),
    latest_scored: bool = Query(default=False, description="Use the most recently completed period"),
) -> dict:
    cache_key = f"weekly_scores_{period or 'current'}_{latest_scored}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_weekly_scores(period=period, latest_scored=latest_scored)
    response_cache.set(cache_key, data)
    return data
