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
    opponent_team: str | None = None
    opponent_score: str | None = None
    keeper_drafted_round: int | None = None
    keeper_drafted_round_pick: int | None = None
    keeper_projected_round: int | None = None
    keeper_projected_pick: int | None = None
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


class TeamPitcherEvalRow(BaseModel):
    overall_rank: int
    name: str
    normalized_name: str
    mlb_team: str | None = None
    positions: list[str]
    percent_owned: float | None = None
    era: float | None = None
    era_rank: int | None = None
    k: int | None = None
    k_rank: int | None = None
    wins: int | None = None
    losses: int | None = None
    ip: str | None = None
    drafted_round: int | None = None
    drafted_round_pick: int | None = None
    keeper_round: int | None = None
    keeper_pick: int | None = None
    keeper_pick_rank: int | None = None
    composite_score: float


class TeamPitcherEvalResponse(BaseModel):
    generated_on: str
    league: str
    team: str | None = None
    formula: str
    count: int
    rows: list[TeamPitcherEvalRow]


class PitcherStartEvalRow(PitcherReviewRow):
    slot: str
    is_bench: bool
    is_probable_today: bool


class PitcherStartEvalResponse(BaseModel):
    generated_on: str
    league: str
    team: str | None = None
    source_url: str
    roster_pitcher_count: int
    probable_roster_count: int
    fallback_to_streamers: bool
    recommended_count: int
    recommended_rows: list[PitcherStartEvalRow]
    bench_probable_rows: list[PitcherStartEvalRow]
    suggested_moves: list[str]
    selected_streamer_row: PitcherReviewRow | None = None
    streamer_fallback_rows: list[PitcherReviewRow] | None = None
