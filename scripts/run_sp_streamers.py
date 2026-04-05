from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from engines.pitcher_engine import TIER_EMOJI, streamer_recommendation
from services.pitchers_service import get_streaming_pitcher_review
from utils.config import AppConfig


def run(args) -> None:
    for_date = date.today() + timedelta(days=1) if getattr(args, "tomorrow", False) else None
    result = get_streaming_pitcher_review(
        league_id=getattr(args, "league_id", None),
        year=getattr(args, "year", None),
        pitcher=getattr(args, "pitcher", None),
        for_date=for_date,
    )

    display_date = for_date or date.today()
    divider = "─" * 96
    print(divider)
    print(f"📅  {display_date.strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {result['league']}")
    print(f"Source: {result['source_url']}")
    print(divider)

    if getattr(args, "pitcher", None):
        if not result.get("found"):
            print(f"No pitcher match found for: {result.get('query')}")
            suggestions = result.get("suggestions", [])
            if suggestions:
                print("Did you mean:")
                for name in suggestions:
                    print(f"  - {name}")
            return
        row = result["row"]
        tier = row["tier"]
        owned = f"{row['percent_owned']:.1f}%" if row["percent_owned"] is not None else "N/A"
        rank_text = f"#{row['streamer_rank']}" if row.get("streamer_rank") else "N/A"
        print(f"{TIER_EMOJI.get(tier, '⚪')} {row['name']} | {row['mlb_team'] or 'N/A'} | Owned: {owned}")
        print(f"  Streamer Rank: {rank_text}")
        print(f"  Tier: {tier}")
        if row.get("opponent_score"):
            opp_team = row.get("opponent_team") or "N/A"
            print(f"  Opponent Score: {row['opponent_score']} ({opp_team})")
        print(f"  Recommendation: {row['recommendation']['action']}")
        print(f"  Season: {row['season_record']} | Last 10: {row['last_ten_record']}")
        if row["last_two_starts"]:
            for start in row["last_two_starts"]:
                print(
                    f"  {start['date']} {start['matchup']} {start['result']} | "
                    f"IP {start['ip']} H {start['h']} R {start['r']} ER {start['er']} "
                    f"BB {start['bb']} K {start['k']} ERA {start['era']}"
                )
        else:
            print("  No starts on record yet this season.")
        return

    for row in result.get("rows", []):
        tier = row["tier"]
        owned = f"{row['percent_owned']:.1f}%" if row["percent_owned"] is not None else "N/A"
        print(f"{TIER_EMOJI.get(tier, '⚪')} {row['name']} | {row['mlb_team'] or 'N/A'} | Owned: {owned}")
        print(f"  Tier: {tier}")
        if row.get("opponent_score"):
            opp_team = row.get("opponent_team") or "N/A"
            print(f"  Opponent Score: {row['opponent_score']} ({opp_team})")
        print(f"  Recommendation: {row['recommendation']['action']}")
        print(f"  Season: {row['season_record']} | Last 10: {row['last_ten_record']}")
        if row["last_two_starts"]:
            for start in row["last_two_starts"]:
                print(
                    f"  {start['date']} {start['matchup']} {start['result']} | "
                    f"IP {start['ip']} H {start['h']} R {start['r']} ER {start['er']} "
                    f"BB {start['bb']} K {start['k']} ERA {start['era']}"
                )
        else:
            print("  No starts on record yet this season.")
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="List free-agent SPs scheduled to start today in your ESPN fantasy league.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--pitcher", type=str, default=None, help="Optional pitcher name to lookup directly.")
    parser.add_argument("--tomorrow", action="store_true", help="Show starters for tomorrow instead of today.")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
