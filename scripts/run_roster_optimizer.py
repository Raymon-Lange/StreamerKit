from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from collectors.espn import build_context, get_roster_players, get_team
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_top_hitters
from engines.hitter_engine import evaluate_daily_hitter, find_lineup_upgrades
from utils.config import AppConfig

_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}


def _lineup_slot(player_record) -> str:
    return str(getattr(player_record.espn_raw, "lineupSlot", "") or "").upper()


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        team_id=getattr(args, "team_id", None) or AppConfig().team_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    trend_games = getattr(args, "trend_games", 10) or 10
    min_gap = getattr(args, "min_gap", 10.0) or 10.0

    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)

    redraft = scrape_top_hitters()
    hitters = get_roster_players(context, team_id=team.team_id, player_type="hitters")

    rows = []
    for player in hitters:
        redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
        trend = summarize_recent_hitting(player.name, trend_games=trend_games)
        rec = evaluate_daily_hitter(redraft_rank, trend.label)
        lineup_slot = _lineup_slot(player)
        rows.append((player, redraft_rank, None, trend, rec, lineup_slot))

    active_count = sum(1 for *_, s in rows if s not in _BENCH_SLOTS and s)
    bench_count = len(rows) - active_count
    swaps = find_lineup_upgrades(rows, min_score_gap=min_gap)

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   Team: {team.team_name}")
    print(f"Roster hitters: {len(rows)} | Active: {active_count} | Bench: {bench_count}")
    print(divider)

    if not swaps:
        print("✅  Lineup looks optimal — no clear upgrades found on the bench.")
        print(divider)
        return

    print(f"⚡  {len(swaps)} lineup upgrade(s) recommended:\n")
    for swap in swaps:
        print(f"  START  {swap.start.name} ({swap.start.mlb_team or 'N/A'}) — {swap.start_rec.action}")
        print(f"         Trend: {swap.start_trend.label} | {swap.start_trend.summary}")
        print(f"         {swap.start_rec.reason}")
        print(f"  SIT    {swap.sit.name} ({swap.sit.mlb_team or 'N/A'}) — {swap.sit_rec.action}")
        print(f"         Trend: {swap.sit_trend.label} | {swap.sit_trend.summary}")
        print(f"  Slot: {swap.slot} | Score gap: {swap.score_gap:.0f}")
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="Recommend lineup swaps based on trend and ranking.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--team-id", type=int, default=config.team_id or 1)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--trend-games", type=int, default=10)
    parser.add_argument("--min-gap", type=float, default=10.0, help="Minimum score gap to flag a swap (default 10).")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
