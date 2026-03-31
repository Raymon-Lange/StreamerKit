from __future__ import annotations

import argparse
from datetime import date

from collectors.espn import build_context, get_free_agent_hitters
from collectors.espn_dynasty import scrape_espn_dynasty_hitters
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_top_hitters
from engines.hitter_engine import evaluate_free_agent_hitter
from utils.config import AppConfig


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    top = getattr(args, "top", 10) or 10
    size = getattr(args, "size", 75) or 75
    trend_games = getattr(args, "trend_games", 15) or 15

    context = build_context(config)

    redraft = scrape_top_hitters()
    pl_dynasty = scrape_dynasty_hitters()
    espn_dynasty = scrape_espn_dynasty_hitters()
    free_agents = get_free_agent_hitters(context, size_per_pos=size)

    rows = []
    for player in free_agents:
        redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
        pl_dynasty_rank = pl_dynasty.get(player.normalized_name).rank if player.normalized_name in pl_dynasty else None
        espn_dynasty_rank = espn_dynasty.get(player.normalized_name).rank if player.normalized_name in espn_dynasty else None
        dynasty_rank = min((rank for rank in (pl_dynasty_rank, espn_dynasty_rank) if rank is not None), default=None)
        trend = summarize_recent_hitting(player.name, trend_games=trend_games)
        rec = evaluate_free_agent_hitter(redraft_rank, dynasty_rank, trend.label)
        rows.append((player, redraft_rank, pl_dynasty_rank, espn_dynasty_rank, dynasty_rank, trend, rec))

    rows.sort(key=lambda row: (-row[6].score, (row[1] or 9999), (row[4] or 9999), -(row[0].percent_owned or 0.0)))
    rows = rows[:top]

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {context.league.settings.name}")
    print(f"Top {len(rows)} free-agent hitters")
    print(divider)

    for player, redraft_rank, pl_dynasty_rank, espn_dynasty_rank, dynasty_rank, trend, rec in rows:
        positions = "/".join(player.positions[:4]) if player.positions else "N/A"
        owned = f"{player.percent_owned:.1f}%" if player.percent_owned is not None else "N/A"
        print(f"{player.name} | {player.mlb_team or 'N/A'} | Pos: {positions} | Owned: {owned}")
        print(
            f"  Redraft Rank: {redraft_rank or 'NR'} | "
            f"Dynasty Rank (Best): {dynasty_rank or 'NR'} | "
            f"PL: {pl_dynasty_rank or 'NR'} | ESPN: {espn_dynasty_rank or 'NR'}"
        )
        print(f"  Trend: {trend.label} | {trend.summary}")
        print(f"  Recommendation: {rec.action}")
        print(f"  Why: {rec.reason}")
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="List top free-agent hitters in your ESPN league.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--size", type=int, default=75)
    parser.add_argument("--trend-games", type=int, default=15)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
