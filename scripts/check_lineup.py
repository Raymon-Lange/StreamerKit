from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.lineup_service import get_lineup_status


def run(args) -> None:
    for_date: date | None = None
    if args.date:
        try:
            for_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"Invalid date {args.date!r} — use YYYY-MM-DD format.")
            sys.exit(1)

    result = get_lineup_status(args.player, for_date=for_date)

    game_ctx = ""
    if result.team and result.opponent:
        game_ctx = f" ({result.team} vs {result.opponent})"

    if result.status == "starting":
        print(f"{result.player_name}: IN LINEUP — batting {result.batting_slot}{game_ctx}")
    elif result.status == "bench":
        print(f"{result.player_name}: NOT in starting lineup{game_ctx}")
    elif result.status == "no_game":
        print(f"{result.player_name}: No game scheduled today")
    elif result.status == "lineup_not_posted":
        print(f"{result.player_name}: Game scheduled{game_ctx}, lineup not yet posted")
    else:
        print(f"{result.player_name}: Player not found in today's lineups")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check if an MLB player is in the starting lineup"
    )
    parser.add_argument("--player", required=True, help="Player name")
    parser.add_argument(
        "--date", default=None, help="Date in YYYY-MM-DD format (default: today)"
    )
    run(parser.parse_args())


if __name__ == "__main__":
    main()
