from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.hitters_service import get_free_agent_hitter_recommendations
from utils.config import AppConfig


def run(args) -> None:
    result = get_free_agent_hitter_recommendations(
        league_id=getattr(args, "league_id", None),
        year=getattr(args, "year", None),
        top=getattr(args, "top", 10) or 10,
        size=getattr(args, "size", 75) or 75,
        trend_games=getattr(args, "trend_games", 15) or 15,
        trend_workers=max(1, getattr(args, "trend_workers", 12) or 12),
        weight_current_performance=getattr(args, "weight_current_performance", None),
        weight_current_year_rankings=getattr(args, "weight_current_year_rankings", None),
        weight_dynasty_rankings=getattr(args, "weight_dynasty_rankings", None),
    )

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {result['league']}")
    print(f"Top {result['top']} free-agent hitters")
    print(
        "Weights (configured): "
        f"Performance {result['weights']['current_performance']:.1f}% | "
        f"Current-Year {result['weights']['current_year_rankings']:.1f}% | "
        f"Dynasty {result['weights']['dynasty_rankings']:.1f}%"
    )
    print(divider)

    for row in result["rows"]:
        positions = "/".join((row["positions"] or [])[:4]) if row["positions"] else "N/A"
        owned = f"{row['percent_owned']:.1f}%" if row["percent_owned"] is not None else "N/A"
        current_year_score = row["scoring"]["bucket_scores"]["current_year_rankings"]
        dynasty_score = row["scoring"]["bucket_scores"]["dynasty_rankings"]
        print(f"{row['name']} | {row['mlb_team'] or 'N/A'} | Pos: {positions} | Owned: {owned}")
        print(
            f"  Current-Year Rank (Best): {row['current_year_rank'] or 'NR'} | "
            f"PL Redraft: {row['redraft_rank'] or 'NR'} | "
            f"ESPN Points: {row['espn_points_rank'] or 'NR'}"
        )
        print(
            f"Dynasty Rank (Best): {row['dynasty_rank'] or 'NR'} | "
            f"PL: {row['pl_dynasty_rank'] or 'NR'} | ESPN: {row['espn_dynasty_rank'] or 'NR'}"
        )
        if row["keeper_projected_round"] is not None:
            drafted_round = row["keeper_drafted_round"]
            drafted_round_pick = row["keeper_drafted_round_pick"]
            draft_slot = f"{drafted_round}.{drafted_round_pick}" if drafted_round_pick else str(drafted_round)
            print(
                f"  Keeper Cost: Drafted R{draft_slot} -> Keep in R{row['keeper_projected_round']}"
                f" (Overall {row['keeper_projected_pick'] or 'NR'})"
            )
        else:
            print("  Keeper Cost: NR")
        print(f"  Trend: {row['trend']['label']} | {row['trend']['summary']}")
        print(f"  Recommendation: {row['recommendation']['action']}")
        print(f"  Why: {row['recommendation']['reason']}")
        print(
            "  Bucket Scores: "
            f"Performance {row['scoring']['bucket_scores']['current_performance']:.1f} | "
            f"Current-Year {f'{current_year_score:.1f}' if current_year_score is not None else 'N/A'} | "
            f"Dynasty {f'{dynasty_score:.1f}' if dynasty_score is not None else 'N/A'}"
        )
        print(
            "  Effective Weights: "
            f"Performance {row['scoring']['effective_weights']['current_performance']:.1f}% | "
            f"Current-Year {row['scoring']['effective_weights']['current_year_rankings']:.1f}% | "
            f"Dynasty {row['scoring']['effective_weights']['dynasty_rankings']:.1f}%"
        )
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="List top free-agent hitters in your ESPN league.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--size", type=int, default=75)
    parser.add_argument("--trend-games", type=int, default=15)
    parser.add_argument("--trend-workers", type=int, default=12)
    parser.add_argument("--weight-current-performance", type=float, default=None)
    parser.add_argument("--weight-current-year-rankings", type=float, default=None)
    parser.add_argument("--weight-dynasty-rankings", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
