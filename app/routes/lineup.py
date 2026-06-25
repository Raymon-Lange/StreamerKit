from __future__ import annotations

from datetime import date as _date

from fastapi import APIRouter, HTTPException, Query

from app import response_cache
from services.lineup_service import get_lineup_status

router = APIRouter()

_TTL = 120


@router.get("/lineup")
async def lineup_status(
    player: str = Query(..., description="Player name to look up"),
    date: str | None = Query(default=None, description="Date in YYYY-MM-DD format (defaults to today)"),
) -> dict:
    for_date: _date | None = None
    if date is not None:
        try:
            for_date = _date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be in YYYY-MM-DD format")

    cache_key = f"lineup_{player}_{(for_date or _date.today()).isoformat()}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached

    result = get_lineup_status(player, for_date=for_date)
    data = {
        "player_name": result.player_name,
        "in_lineup": result.in_lineup,
        "status": result.status,
        "batting_slot": result.batting_slot,
        "team": result.team,
        "opponent": result.opponent,
        "game_time": result.game_time,
    }
    response_cache.set(cache_key, data)
    return data
