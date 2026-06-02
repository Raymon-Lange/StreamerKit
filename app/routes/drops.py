from __future__ import annotations

from fastapi import APIRouter, Query

from app import response_cache
from services.waivers_service import get_recent_drops_waiver_review

router = APIRouter()

_TTL = 300


@router.get("/recent-drops")
async def recent_drops(
    days: int = Query(default=2, ge=1, description="Lookback window in days"),
    top: int = Query(default=5, ge=1, description="Max results to return"),
    trend_games: int = Query(default=10, ge=1, description="Games to include in trend"),
    claim_mode: str = Query(default="all", pattern="^(all|wins)$", description="all or wins"),
) -> dict:
    cache_key = f"drops_{days}_{top}_{trend_games}_{claim_mode}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_recent_drops_waiver_review(days=days, top=top, trend_games=trend_games, claim_mode=claim_mode)
    response_cache.set(cache_key, data)
    return data
