from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.schemas.waivers import WaiverReviewResponse
from services.waivers_service import get_recent_drops_waiver_review

router = APIRouter(prefix="/waivers", tags=["waivers"], dependencies=[Depends(require_api_key)])


@router.get(
    "/recent-drops",
    response_model=WaiverReviewResponse,
    summary="Recent Drops Waiver Review",
    description="Reviews add/drop activity for a lookback window and returns actionable waiver targets.",
)
def recent_drops(
    days: int = 2,
    trend_games: int = 10,
    top: int = 25,
    claim_mode: Literal["all", "wins"] = "all",
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return get_recent_drops_waiver_review(
        league_id=league_id,
        year=year,
        days=days,
        trend_games=trend_games,
        top=top,
        claim_mode=claim_mode,
    )
