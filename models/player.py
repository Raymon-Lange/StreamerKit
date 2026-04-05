from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RankingEntry:
    source: str
    rank: int | None = None
    tier: str | None = None
    article_url: str | None = None
    article_title: str | None = None
    article_date: str | None = None
    position: str | None = None
    opponent_team: str | None = None
    opponent_score: str | None = None
    raw: str | None = None


@dataclass(slots=True)
class TrendSummary:
    label: str = "UNKNOWN"
    games: int = 0
    avg: float | None = None
    ops: float | None = None
    hr: int = 0
    sb: int = 0
    rbi: int = 0
    runs: int = 0
    summary: str = "No trend data"


@dataclass(slots=True)
class PlayerRecord:
    name: str
    normalized_name: str
    mlb_team: str | None = None
    positions: list[str] = field(default_factory=list)
    percent_owned: float | None = None
    source: str | None = None
    external_id: str | int | None = None
    espn_raw: Any = None


@dataclass(slots=True)
class Recommendation:
    action: str
    reason: str
    score: float = 0.0


@dataclass(slots=True)
class LineupSwap:
    start: "PlayerRecord"
    sit: "PlayerRecord"
    slot: str
    start_rec: Recommendation
    sit_rec: Recommendation
    score_gap: float
    start_trend: "TrendSummary"
    sit_trend: "TrendSummary"
