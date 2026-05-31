from __future__ import annotations

import statistics
from datetime import date

from collectors.espn import build_context
from utils.config import AppConfig


def _matchup_score(matchup, side: str) -> float:
    if side == "home":
        live = getattr(matchup, "home_team_live_score", None)
        final = getattr(matchup, "home_final_score", None)
    else:
        live = getattr(matchup, "away_team_live_score", None)
        final = getattr(matchup, "away_final_score", None)
    if live not in (None, 0, 0.0):
        return float(live)
    if final is not None:
        return float(final)
    return float(live or 0.0)


def _scoreboard_for_period(league, period: int):
    try:
        return league.scoreboard(matchupPeriod=period)
    except TypeError:
        return league.scoreboard(period=period)


def _resolve_period(league, requested_period: int | None, latest_scored: bool) -> int:
    if requested_period:
        return requested_period
    current = getattr(league, "current_week", None)
    if current and not latest_scored:
        return int(current)
    max_period = int(getattr(league.settings, "matchup_period_count", 30) or 30)
    latest = 1
    for period in range(1, max_period + 1):
        board = _scoreboard_for_period(league, period)
        total = sum(
            _matchup_score(m, "home") + _matchup_score(m, "away") for m in board
        )
        if total > 0.0:
            latest = period
    return latest


def get_weekly_scores(
    league_id: int | None = None,
    team_id: int | None = None,
    year: int | None = None,
    period: int | None = None,
    latest_scored: bool = False,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        team_id=team_id or AppConfig().team_id,
        year=year or AppConfig().year,
    )
    context = build_context(config)
    league = context.league
    selected_period = _resolve_period(league, period, latest_scored)
    scoreboard = _scoreboard_for_period(league, selected_period)

    rows: list[dict] = []
    for matchup in scoreboard:
        for team_obj, side in [(matchup.home_team, "home"), (matchup.away_team, "away")]:
            rows.append({
                "team_id": team_obj.team_id,
                "team_name": team_obj.team_name,
                "score": _matchup_score(matchup, side),
            })

    rows.sort(key=lambda r: r["score"], reverse=True)
    scores = [r["score"] for r in rows]
    mean_score = round(statistics.mean(scores), 1) if scores else 0.0
    median_score = round(statistics.median(scores), 1) if scores else 0.0
    top_half_cutoff = (len(rows) + 1) // 2
    target_team_id = config.team_id or -1

    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
        row["half"] = "top" if idx <= top_half_cutoff else "bottom"
        row["is_my_team"] = row["team_id"] == target_team_id

    my_team = next((r for r in rows if r["is_my_team"]), None)

    return {
        "generated_on": date.today().isoformat(),
        "league": league.settings.name,
        "year": config.year,
        "period": selected_period,
        "team_count": len(rows),
        "mean_score": mean_score,
        "median_score": median_score,
        "my_team": my_team,
        "rows": rows,
    }
