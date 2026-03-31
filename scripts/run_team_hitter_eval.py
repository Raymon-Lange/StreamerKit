from __future__ import annotations

import argparse
from datetime import date

from collectors.espn import build_context, get_roster_players, get_team
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_top_hitters
from engines.hitter_engine import evaluate_roster_hitter
from utils.config import AppConfig


def run(args) -> None:
    base_config = AppConfig()
    team_id = getattr(args, "team_id", None) or base_config.team_id or 1
    trend_games = getattr(args, "trend_games", 10) or 10
    all_hitters = getattr(args, "all_hitters", False)

    config = AppConfig(
        league_id=getattr(args, "league_id", None) or base_config.league_id,
        team_id=team_id,
        year=getattr(args, "year", None) or base_config.year,
    )
    context = build_context(config)
    team = get_team(context, team_id=team_id)
    player_type = "all" if all_hitters else "hitters"
    hitters = get_roster_players(context, team_id=team_id, player_type=player_type)

    redraft = scrape_top_hitters()
    dynasty = scrape_dynasty_hitters()

    rows = []
    for hitter in hitters:
        redraft_rank = redraft.get(hitter.normalized_name).rank if hitter.normalized_name in redraft else None
        dynasty_rank = dynasty.get(hitter.normalized_name).rank if hitter.normalized_name in dynasty else None
        trend = summarize_recent_hitting(hitter.name, trend_games=trend_games)
        rec = evaluate_roster_hitter(redraft_rank, dynasty_rank, trend.label)
        rows.append((hitter, redraft_rank, dynasty_rank, trend, rec))

    rows.sort(key=lambda row: ((row[1] or 9999), (row[2] or 9999), -row[4].score))

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {context.league.settings.name}")
    print(f"🧢  Team: {team.team_name}")
    print(f"⚾  Hitters evaluated: {len(rows)}")
    print(divider)

    for hitter, redraft_rank, dynasty_rank, trend, rec in rows:
        positions = "/".join(hitter.positions[:4]) if hitter.positions else "N/A"
        print(f"{hitter.name} | {hitter.mlb_team or 'N/A'} | Pos: {positions}")
        print(f"  Redraft Rank: {redraft_rank or 'NR'} | Dynasty Rank: {dynasty_rank or 'NR'}")
        print(f"  Trend: {trend.label} | {trend.summary}")
        print(f"  Recommendation: {rec.action}")
        print(f"  Why: {rec.reason}")
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="Evaluate hitters currently on your ESPN fantasy roster.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--team-id", type=int, default=config.team_id or 1)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--trend-games", type=int, default=10)
    parser.add_argument("--all-hitters", action="store_true", default=False)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
