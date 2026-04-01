from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import RecommendationModel


class PitcherStartModel(BaseModel):
    date: str
    matchup: str
    result: str
    ip: str
    h: int
    r: int
    er: int
    bb: int
    k: int
    era: str


class PitcherReviewRow(BaseModel):
    name: str
    normalized_name: str
    mlb_team: str | None = None
    positions: list[str]
    percent_owned: float | None = None
    streamer_rank: int | None = None
    tier: str
    recommendation: RecommendationModel
    season_record: str
    last_ten_record: str
    last_two_starts: list[PitcherStartModel]


class PitcherReviewResponse(BaseModel):
    generated_on: str
    league: str
    source_url: str
    count: int | None = None
    query: str | None = None
    found: bool | None = None
    suggestions: list[str] | None = None
    row: PitcherReviewRow | None = None
    rows: list[PitcherReviewRow] | None = None
