from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.schemas.pitchers import PitcherReviewResponse
from services.pitchers_service import get_streaming_pitcher_review

router = APIRouter(prefix="/pitchers", tags=["pitchers"], dependencies=[Depends(require_api_key)])


@router.get(
    "/streamers",
    response_model=PitcherReviewResponse,
    summary="Streaming Pitcher Review",
    description="Returns today's streamer review, or a single-pitcher lookup when pitcher is provided.",
)
def streamers(
    pitcher: str | None = None,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return get_streaming_pitcher_review(
        league_id=league_id,
        year=year,
        pitcher=pitcher,
    )
