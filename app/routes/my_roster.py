from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app import response_cache
from services.roster_card_service import get_roster_card

router = APIRouter()

_TTL = 120


@router.get("/my-roster")
async def my_roster() -> dict:
    cache_key = f"my_roster_{date.today().isoformat()}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_roster_card()
    response_cache.set(cache_key, data)
    return data
