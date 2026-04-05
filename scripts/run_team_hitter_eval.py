from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from collectors.espn import build_context, get_roster_players, get_team
from collectors.espn_dynasty import scrape_espn_dynasty_hitters
from collectors.espn_keeper_cost import scrape_espn_keeper_cost
from collectors.espn_points import scrape_espn_points_top300
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_top_hitters
from engines.hitter_engine import build_hitter_weight_profile, evaluate_weighted_hitter
from utils.config import AppConfig


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        team_id=getattr(args, "team_id", None) or AppConfig().team_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    trend_games = getattr(args, "trend_games", 15) or 15
    configured_weights = build_hitter_weight_profile(
        intent="team_eval",
        override={
            "current_performance": getattr(args, "weight_current_performance", None),
            "current_year_rankings": getattr(args, "weight_current_year_rankings", None),
            "dynasty_rankings": getattr(args, "weight_dynasty_rankings", None),
        },
    )

    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)

    pl_redraft = scrape_top_hitters()
    espn_points = scrape_espn_points_top300()
    pl_dynasty = scrape_dynasty_hitters()
    espn_dynasty = scrape_espn_dynasty_hitters()
    keeper_cost = scrape_espn_keeper_cost(context)
    hitters = get_roster_players(context, team_id=team.team_id, player_type="hitters")

    rows = []
    for player in hitters:
        pl_redraft_rank = pl_redraft.get(player.normalized_name).rank if player.normalized_name in pl_redraft else None
        espn_points_rank = espn_points.get(player.normalized_name).rank if player.normalized_name in espn_points else None
        current_year_rank = min(
            (rank for rank in (pl_redraft_rank, espn_points_rank) if rank is not None),
            default=None,
        )
        pl_dynasty_rank = pl_dynasty.get(player.normalized_name).rank if player.normalized_name in pl_dynasty else None
        espn_dynasty_rank = espn_dynasty.get(player.normalized_name).rank if player.normalized_name in espn_dynasty else None
        keeper_entry = keeper_cost.get(player.normalized_name)
        keeper_projected_pick = keeper_entry.projected_keeper_overall_pick if keeper_entry else None
        dynasty_rank = min(
            (rank for rank in (pl_dynasty_rank, espn_dynasty_rank, keeper_projected_pick) if rank is not None),
            default=None,
        )
        trend = summarize_recent_hitting(player.name, trend_games=trend_games)
        rec, scoring = evaluate_weighted_hitter(
            intent="team_eval",
            trend_label=trend.label,
            current_year_ranks=[pl_redraft_rank, espn_points_rank],
            dynasty_ranks=[pl_dynasty_rank, espn_dynasty_rank, keeper_projected_pick],
            weight_profile=configured_weights,
        )
        rows.append(
            (
                player,
                current_year_rank,
                pl_redraft_rank,
                espn_points_rank,
                pl_dynasty_rank,
                espn_dynasty_rank,
                keeper_entry,
                dynasty_rank,
                trend,
                rec,
                scoring,
            )
        )

    rows.sort(key=lambda row: (-(row[9].score), (row[1] or 9999), (row[7] or 9999), row[0].name))

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   Team: {team.team_name}")
    print(f"Roster hitters: {len(rows)}")
    print(f"Trend window: {trend_games} games")
    print(
        "Weights (configured): "
        f"Performance {configured_weights['current_performance']:.1f}% | "
        f"Current-Year {configured_weights['current_year_rankings']:.1f}% | "
        f"Dynasty {configured_weights['dynasty_rankings']:.1f}%"
    )
    print(divider)

    for (
        player,
        current_year_rank,
        pl_redraft_rank,
        espn_points_rank,
        pl_dynasty_rank,
        espn_dynasty_rank,
        keeper_entry,
        dynasty_rank,
        trend,
        rec,
        scoring,
    ) in rows:
        positions = "/".join(player.positions[:4]) if player.positions else "N/A"
        print(f"{player.name} | {player.mlb_team or 'N/A'} | Pos: {positions}")
        print(
            f"  Current-Year Rank (Best): {current_year_rank or 'NR'} | "
            f"PL Redraft: {pl_redraft_rank or 'NR'} | "
            f"ESPN Points: {espn_points_rank or 'NR'}"
        )
        print(
            f"Dynasty Rank (Best): {dynasty_rank or 'NR'} | "
            f"PL: {pl_dynasty_rank or 'NR'} | ESPN: {espn_dynasty_rank or 'NR'}"
        )
        if keeper_entry:
            draft_slot = (
                f"{keeper_entry.drafted_round}.{keeper_entry.drafted_round_pick}"
                if keeper_entry.drafted_round_pick
                else str(keeper_entry.drafted_round)
            )
            print(
                f"  Keeper Cost: Drafted R{draft_slot} -> Keep in R{keeper_entry.projected_keeper_round}"
                f" (Overall {keeper_entry.projected_keeper_overall_pick or 'NR'})"
            )
        else:
            print("  Keeper Cost: NR")
        print(f"  Trend: {trend.label} | {trend.summary}")
        print(f"  Recommendation: {rec.action}")
        print(f"  Why: {rec.reason}")
        current_year_score = scoring["bucket_scores"]["current_year_rankings"]
        dynasty_score = scoring["bucket_scores"]["dynasty_rankings"]
        print(
            "  Bucket Scores: "
            f"Performance {scoring['bucket_scores']['current_performance']:.1f} | "
            f"Current-Year {f'{current_year_score:.1f}' if current_year_score is not None else 'N/A'} | "
            f"Dynasty {f'{dynasty_score:.1f}' if dynasty_score is not None else 'N/A'}"
        )
        print(
            "  Effective Weights: "
            f"Performance {scoring['effective_weights']['current_performance']:.1f}% | "
            f"Current-Year {scoring['effective_weights']['current_year_rankings']:.1f}% | "
            f"Dynasty {scoring['effective_weights']['dynasty_rankings']:.1f}%"
        )
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="Evaluate hitters on your ESPN roster.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--team-id", type=int, default=config.team_id or 1)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--trend-games", type=int, default=15)
    parser.add_argument("--weight-current-performance", type=float, default=None)
    parser.add_argument("--weight-current-year-rankings", type=float, default=None)
    parser.add_argument("--weight-dynasty-rankings", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
