from __future__ import annotations

from pydantic import BaseModel


class RecommendationModel(BaseModel):
    action: str
    reason: str
    score: float


class TrendSummaryModel(BaseModel):
    label: str
    summary: str
    games: int
    avg: float | None = None
    ops: float | None = None
    hr: int
    sb: int
    rbi: int
    runs: int
