from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.waivers_service import get_recent_drops_waiver_review
from utils.config import AppConfig


def _fmt_when(iso_value: str) -> str:
    try:
        ts = datetime.fromisoformat(iso_value)
        return ts.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_value


def run(args) -> None:
    result = get_recent_drops_waiver_review(
        league_id=getattr(args, "league_id", None),
        year=getattr(args, "year", None),
        days=max(1, getattr(args, "days", 2) or 2),
        trend_games=getattr(args, "trend_games", 10) or 10,
        top=getattr(args, "top", 25) or 25,
        claim_mode=(getattr(args, "claim_mode", "all") or "all"),
    )

    if not result["rows"]:
        print(f"No waiver-worthy drops found in the last {result['days']} day(s).")
        return

    divider = "─" * 108
    now_local = datetime.now(timezone.utc).astimezone().strftime("%A, %B %d, %Y %I:%M %p")
    print(divider)
    print(f"📅  {now_local}")
    print(f"🏟   League: {result['league']}")
    print(f"Lookback: Last {result['days']} day(s) | Showing top {result['top']} waiver-worthy dropped players")
    print("Filtered out: PASS and SKIP recommendations")
    print(f"Mode: {result['claim_mode']}")
    print(divider)

    for row in result["rows"]:
        positions = "/".join((row.get("positions") or [])[:4]) if row.get("positions") else "N/A"
        owned = f"{row['percent_owned']:.1f}%" if row.get("percent_owned") is not None else "N/A"
        print(
            f"{row['name']} | {row.get('mlb_team') or 'N/A'} | Pos: {positions} | Owned: {owned} | "
            f"Dropped by: {row['dropped_by']} ({_fmt_when(row['dropped_at'])})"
        )
        if row["kind"] == "H":
            print(
                f"  Redraft Rank: {row.get('redraft_rank') or 'NR'} | "
                f"Dynasty Rank (Best): {row.get('dynasty_rank') or 'NR'} | "
                f"PL: {row.get('pl_dynasty_rank') or 'NR'} | ESPN: {row.get('espn_dynasty_rank') or 'NR'}"
            )
            trend = row["trend"]
            print(f"  Trend: {trend['label']} | {trend['summary']}")
        else:
            print(f"  Streamer Tier: {row['tier']}")
            print(f"  Pitching: Season {row['season_record']} | Last 10 {row['last_ten_record']}")
        print(f"  Recommendation: {row['recommendation']['action']}")
        print(f"  Why: {row['recommendation']['reason']}")
        if row.get("suggested_drop"):
            candidate = row["suggested_drop"]
            candidate_positions = "/".join((candidate.get("positions") or [])[:4]) if candidate.get("positions") else "N/A"
            candidate_owned = f"{candidate['percent_owned']:.1f}%" if candidate.get("percent_owned") is not None else "N/A"
            print(
                f"  Suggested drop (win-now): {candidate['name']} | Pos: {candidate_positions} | "
                f"Owned: {candidate_owned} | Roster score: {candidate['roster_score']:.0f}"
            )
        print(f"  {'·' * 100}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="Review recent league drops and surface waiver-worthy adds.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--days", type=int, default=2, help="Lookback window in days (default: 2).")
    parser.add_argument("--trend-games", type=int, default=10)
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument(
        "--claim-mode",
        choices=["all", "wins"],
        default="all",
        help="Filter output: 'all' actionable targets, or only 'wins' (WIN-NOW ADD / MUST ADD).",
    )
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()

