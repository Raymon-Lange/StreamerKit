from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import RecommendationModel, TrendSummaryModel


class SuggestedDropModel(BaseModel):
    name: str
    positions: list[str]
    percent_owned: float | None = None
    roster_score: float


class WaiverReviewRow(BaseModel):
    kind: str
    name: str
    normalized_name: str
    mlb_team: str | None = None
    positions: list[str]
    percent_owned: float | None = None
    dropped_by: str
    dropped_at: str
    recommendation: RecommendationModel
    redraft_rank: int | None = None
    pl_dynasty_rank: int | None = None
    espn_dynasty_rank: int | None = None
    dynasty_rank: int | None = None
    trend: TrendSummaryModel | None = None
    tier: str | None = None
    season_record: str | None = None
    last_ten_record: str | None = None
    suggested_drop: SuggestedDropModel | None = None


class WaiverReviewResponse(BaseModel):
    generated_on: str
    league: str
    days: int
    claim_mode: str
    top: int | None = None
    rows: list[WaiverReviewRow]
