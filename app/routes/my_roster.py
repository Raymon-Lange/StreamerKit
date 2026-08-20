from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import response_cache
from services.lineup_swap_service import swap_players
from services.roster_card_service import get_roster_card

router = APIRouter()

_TTL = 120


class SwapRequest(BaseModel):
    player_a_id: int
    player_b_id: int


@router.get("/my-roster")
async def my_roster() -> dict:
    cache_key = f"my_roster_{date.today().isoformat()}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached
    data = get_roster_card()
    response_cache.set(cache_key, data)
    return data


@router.post("/my-roster/swap")
async def my_roster_swap(payload: SwapRequest) -> dict:
    result = swap_players(payload.player_a_id, payload.player_b_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return {"success": True, "message": result.message}
