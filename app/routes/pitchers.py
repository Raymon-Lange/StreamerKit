from __future__ import annotations

from datetime import date, timedelta
from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.schemas.pitchers import PitcherReviewResponse, PitcherStartEvalResponse, TeamPitcherEvalResponse
from services.pitchers_service import get_pitcher_start_evaluation, get_streaming_pitcher_review, get_team_pitcher_evaluation

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
    tomorrow: bool = False,
) -> dict:
    for_date = date.today() + timedelta(days=1) if tomorrow else None
    return get_streaming_pitcher_review(
        league_id=league_id,
        year=year,
        pitcher=pitcher,
        for_date=for_date,
    )


@router.get(
    "/team-eval",
    response_model=TeamPitcherEvalResponse,
    summary="Team Pitcher Evaluation",
    description="Ranks roster pitchers by ERA, strikeouts, and keeper draft-cost level.",
)
def team_eval(
    team_id: int | None = None,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return get_team_pitcher_evaluation(
        league_id=league_id,
        team_id=team_id,
        year=year,
    )


@router.get(
    "/start-eval",
    response_model=PitcherStartEvalResponse,
    summary="Pitcher Start Evaluation",
    description=(
        "Evaluates roster pitchers for probable starts today, recommends the top 2 starts, "
        "and falls back to top streamers when no roster probable starters are found."
    ),
)
def start_eval(
    team_id: int | None = None,
    league_id: int | None = None,
    year: int | None = None,
    tomorrow: bool = False,
) -> dict:
    for_date = date.today() + timedelta(days=1) if tomorrow else date.today()
    return get_pitcher_start_evaluation(
        team_id=team_id,
        league_id=league_id,
        year=year,
        for_date=for_date,
    )
