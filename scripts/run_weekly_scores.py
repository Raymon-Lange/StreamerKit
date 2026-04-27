from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import statistics
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from collectors.espn import build_context
from utils.config import AppConfig


def _matchup_score(matchup, side: str) -> float:
    if side == "home":
        live = getattr(matchup, "home_team_live_score", None)
        final = getattr(matchup, "home_final_score", None)
    else:
        live = getattr(matchup, "away_team_live_score", None)
        final = getattr(matchup, "away_final_score", None)
    # espn_api may keep live score at 0.0 even for completed periods;
    # prefer final score unless live is actively non-zero.
    if live not in (None, 0, 0.0):
        score = live
    elif final is not None:
        score = final
    else:
        score = live
    return float(score or 0.0)


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
        total = 0.0
        for matchup in board:
            total += _matchup_score(matchup, "home")
            total += _matchup_score(matchup, "away")
        if total > 0.0:
            latest = period
    return latest


def run(args) -> None:
    cfg = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        team_id=getattr(args, "team_id", None) or AppConfig().team_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    context = build_context(cfg)
    league = context.league
    selected_period = _resolve_period(
        league,
        requested_period=getattr(args, "period", None),
        latest_scored=getattr(args, "latest_scored", False),
    )
    scoreboard = _scoreboard_for_period(league, selected_period)

    rows: list[tuple[str, float, int]] = []
    for matchup in scoreboard:
        home_team = matchup.home_team
        away_team = matchup.away_team
        rows.append((home_team.team_name, _matchup_score(matchup, "home"), home_team.team_id))
        rows.append((away_team.team_name, _matchup_score(matchup, "away"), away_team.team_id))

    rows.sort(key=lambda item: item[1], reverse=True)
    scores = [score for _, score, _ in rows]
    mean_score = statistics.mean(scores) if scores else 0.0
    median_score = statistics.median(scores) if scores else 0.0
    top_half_cutoff = (len(rows) + 1) // 2
    target_team_id = cfg.team_id or -1
    target_summary: tuple[int, str, float] | None = None
    for idx, (team_name, score, team_id) in enumerate(rows, start=1):
        if team_id == target_team_id:
            target_summary = (idx, team_name, score)
            break

    divider = "─" * 88
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {league.settings.name}")
    print(f"Season: {cfg.year} | Matchup Period: {selected_period}")
    print(f"Teams: {len(rows)} | Mean: {mean_score:.1f} | Median: {median_score:.1f}")
    if target_summary is not None:
        rank, team_name, score = target_summary
        half_label = "TOP HALF" if rank <= top_half_cutoff else "BOTTOM HALF"
        print(f"Your Team: {team_name} | Rank: {rank}/{len(rows)} | Score: {score:.1f} | {half_label}")
    print(divider)

    for idx, (team_name, score, team_id) in enumerate(rows, start=1):
        marker = "★" if team_id == target_team_id else " "
        half_label = "TOP HALF" if idx <= top_half_cutoff else "BOTTOM HALF"
        print(f"{marker} {idx:>2}. {team_name:<32} {score:>6.1f}  {half_label}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(
        description="Rank league teams by weekly matchup score and highlight your team."
    )
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--team-id", type=int, default=config.team_id or 1)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument(
        "--period",
        type=int,
        default=None,
        help="Specific ESPN matchup period to report. If omitted, uses current week.",
    )
    parser.add_argument(
        "--latest-scored",
        action="store_true",
        help="Use the latest matchup period with non-zero scores.",
    )
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
