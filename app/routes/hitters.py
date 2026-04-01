from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.schemas.hitters import HitterRecommendationResponse
from services.hitters_service import get_free_agent_hitter_recommendations

router = APIRouter(prefix="/hitters", tags=["hitters"], dependencies=[Depends(require_api_key)])


@router.get(
    "/free-agents",
    response_model=HitterRecommendationResponse,
    summary="Free-Agent Hitter Recommendations",
    description="Returns ranked free-agent hitters using redraft, dynasty, and trend signals.",
)
def free_agent_hitters(
    top: int = 10,
    size: int = 75,
    trend_games: int = 15,
    trend_workers: int = 12,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return get_free_agent_hitter_recommendations(
        league_id=league_id,
        year=year,
        top=top,
        size=size,
        trend_games=trend_games,
        trend_workers=trend_workers,
    )
