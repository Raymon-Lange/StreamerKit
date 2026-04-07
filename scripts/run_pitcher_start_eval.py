from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from engines.pitcher_engine import TIER_EMOJI
from services.pitchers_service import get_pitcher_start_evaluation
from utils.config import AppConfig


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        team_id=getattr(args, "team_id", None) or AppConfig().team_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )

    for_date = date.today() + timedelta(days=1) if getattr(args, "tomorrow", False) else date.today()

    result = get_pitcher_start_evaluation(
        team_id=config.team_id or None,
        league_id=config.league_id,
        year=config.year,
        for_date=for_date,
    )

    divider = "─" * 104
    print(divider)
    print(f"📅  {for_date.strftime('%A, %B %d, %Y')}")
    print(f"🏟   Team: {result.get('team') or 'N/A'}")
    print(f"Streaming source: {result['source_url']}")
    print(
        f"Roster pitchers: {result['roster_pitcher_count']} | "
        f"Probable starts on roster today: {result['probable_roster_count']}"
    )
    print(divider)

    if result.get("fallback_to_streamers"):
        print("No probable starting pitchers found on your roster for this date.")
        print("Falling back to streaming pitcher recommendations for this date.\n")
        streamer_rows = result.get("streamer_fallback_rows", [])
        if not streamer_rows:
            print("No streaming pitchers found for this date.")
            return
        print("Top streaming pitchers to consider:")
        for idx, row in enumerate(streamer_rows, start=1):
            tier = row.get("tier") or "Not Ranked"
            tier_emoji = TIER_EMOJI.get(tier, "⚪")
            owned = f"{row['percent_owned']:.1f}%" if row.get("percent_owned") is not None else "N/A"
            rank_text = f"#{row['streamer_rank']}" if row.get("streamer_rank") else "NR"
            print(
                f"{idx}. {tier_emoji} {row['name']} | {row.get('mlb_team') or 'N/A'} | "
                f"Tier: {tier} | Streamer: {rank_text} | Owned: {owned}"
            )
            recommendation = row.get("recommendation") or {}
            print(
                f"   {recommendation.get('action') or 'CONSIDER'} — "
                f"{recommendation.get('reason') or 'No recommendation detail available'}"
            )
        return

    print("Top 2 pitchers to start today:")
    for idx, choice in enumerate(result.get("recommended_rows", []), start=1):
        owned = f"{choice['percent_owned']:.1f}%" if choice.get("percent_owned") is not None else "N/A"
        tier_emoji = TIER_EMOJI.get(choice["tier"], "⚪")
        rank_text = f"#{choice['streamer_rank']}" if choice.get("streamer_rank") else "NR"
        bench_text = "BENCH" if choice.get("is_bench") else f"ACTIVE ({choice.get('slot')})"
        print(
            f"{idx}. {tier_emoji} {choice['name']} | {choice.get('mlb_team') or 'N/A'} | "
            f"{bench_text} | Tier: {choice['tier']} | Streamer: {rank_text} | Owned: {owned}"
        )
        recommendation = choice.get("recommendation") or {}
        print(
            f"   {recommendation.get('action') or 'CONSIDER'} — "
            f"{recommendation.get('reason') or 'No recommendation detail available'}"
        )

    bench_probable_rows = result.get("bench_probable_rows", [])
    print(f"\nBench probable starters: {len(bench_probable_rows)}")
    for choice in bench_probable_rows:
        tier_emoji = TIER_EMOJI.get(choice["tier"], "⚪")
        rank_text = f"#{choice['streamer_rank']}" if choice.get("streamer_rank") else "NR"
        print(f"  {tier_emoji} {choice['name']} | Tier: {choice['tier']} | Streamer: {rank_text}")

    suggested_moves = result.get("suggested_moves", [])
    if suggested_moves:
        print("\nSuggested lineup moves:")
        for idx, move in enumerate(suggested_moves, start=1):
            print(f"{idx}. {move}")
    else:
        print("\nNo bench-to-active SP move needed based on today's probable starts and streamer ranks.")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(
        description="Recommend the best 2 roster pitchers to start today using probable starters + Pitcher List streamer tiers."
    )
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--team-id", type=int, default=config.team_id or 1)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--tomorrow", action="store_true", help="Evaluate for tomorrow instead of today.")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
