from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.pitchers_service import get_team_pitcher_evaluation
from utils.config import AppConfig


def run(args) -> None:
    result = get_team_pitcher_evaluation(
        league_id=getattr(args, "league_id", None),
        team_id=getattr(args, "team_id", None),
        year=getattr(args, "year", None),
    )

    divider = "─" * 108
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {result['league']}")
    print(f"Team: {result.get('team') or 'N/A'}")
    print(f"Roster pitchers: {result['count']}")
    print(f"Rank formula: {result['formula']}")
    print(divider)

    for row in result.get("rows", []):
        positions = "/".join((row.get("positions") or [])[:4]) if row.get("positions") else "N/A"
        owned = f"{row['percent_owned']:.1f}%" if row.get("percent_owned") is not None else "N/A"
        era_text = f"{row['era']:.2f}" if row.get("era") is not None else "N/A"
        k_text = str(row["k"]) if row.get("k") is not None else "N/A"
        wl_text = (
            f"{row['wins']}-{row['losses']}"
            if row.get("wins") is not None and row.get("losses") is not None
            else "N/A"
        )
        ip_text = row.get("ip") or "N/A"

        print(
            f"{row.get('overall_rank')}. {row['name']} | {row.get('mlb_team') or 'N/A'} | "
            f"Pos: {positions} | Owned: {owned} | Score: {row['composite_score']:.1f}"
        )
        print(
            f"  ERA: {era_text} (team rank {row.get('era_rank') or 'N/A'}) | "
            f"K: {k_text} (team rank {row.get('k_rank') or 'N/A'}) | "
            f"W-L: {wl_text} | IP: {ip_text}"
        )

        if row.get("keeper_round") is not None:
            drafted_round = row.get("drafted_round")
            drafted_round_pick = row.get("drafted_round_pick")
            draft_slot = f"{drafted_round}.{drafted_round_pick}" if drafted_round_pick else str(drafted_round)
            print(
                f"  Keeper Cost: Drafted R{draft_slot} -> Keep in R{row['keeper_round']} "
                f"(Overall {row.get('keeper_pick') or 'N/A'}, team rank {row.get('keeper_pick_rank') or 'N/A'})"
            )
        else:
            print("  Keeper Cost: N/A")
        print(f"  {'·' * 100}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="Evaluate roster pitchers by ERA, strikeouts, and keeper draft cost.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--team-id", type=int, default=config.team_id or 1)
    parser.add_argument("--year", type=int, default=config.year)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
