from __future__ import annotations

from fastapi import APIRouter, Query

from app import response_cache
from services.optimizer_service import get_roster_optimizer

router = APIRouter()

_TTL = 300


@router.get("/roster-optimizer")
async def roster_optimizer(
    trend_games: int = Query(default=10, ge=1, description="Games to include in trend"),
    min_gap: float = Query(default=10.0, ge=0, description="Minimum score gap to flag a swap"),
) -> dict:
    cache_key = f"optimizer_{trend_games}_{min_gap}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_roster_optimizer(trend_games=trend_games, min_gap=min_gap)
    response_cache.set(cache_key, data)
    return data
