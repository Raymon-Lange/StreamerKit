from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import RecommendationModel, TrendSummaryModel


class HitterRecommendationRow(BaseModel):
    name: str
    normalized_name: str
    mlb_team: str | None = None
    positions: list[str]
    percent_owned: float | None = None
    redraft_rank: int | None = None
    pl_dynasty_rank: int | None = None
    espn_dynasty_rank: int | None = None
    dynasty_rank: int | None = None
    trend: TrendSummaryModel
    recommendation: RecommendationModel


class HitterRecommendationResponse(BaseModel):
    generated_on: str
    league: str
    top: int
    rows: list[HitterRecommendationRow]
