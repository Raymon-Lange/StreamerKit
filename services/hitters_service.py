from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from collectors.espn import build_context, get_free_agent_hitters
from collectors.espn_dynasty import scrape_espn_dynasty_hitters
from collectors.espn_keeper_cost import scrape_espn_keeper_cost
from collectors.espn_points import scrape_espn_points_top300
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_top_hitters
from engines.hitter_engine import build_hitter_weight_profile, evaluate_weighted_hitter
from utils.config import AppConfig


def get_free_agent_hitter_recommendations(
    league_id: int | None = None,
    year: int | None = None,
    top: int = 10,
    size: int = 75,
    trend_games: int = 15,
    trend_workers: int = 12,
    weight_current_performance: float | None = None,
    weight_current_year_rankings: float | None = None,
    weight_dynasty_rankings: float | None = None,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        year=year or AppConfig().year,
    )
    trend_workers = max(1, trend_workers)
    context = build_context(config)
    configured_weights = build_hitter_weight_profile(
        intent="waiver",
        override={
            "current_performance": weight_current_performance,
            "current_year_rankings": weight_current_year_rankings,
            "dynasty_rankings": weight_dynasty_rankings,
        },
    )

    pl_redraft = scrape_top_hitters()
    espn_points = scrape_espn_points_top300()
    pl_dynasty = scrape_dynasty_hitters()
    espn_dynasty = scrape_espn_dynasty_hitters()
    keeper_cost = scrape_espn_keeper_cost(context)
    free_agents = get_free_agent_hitters(context, size_per_pos=size)

    def _build_row(player):
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
            intent="waiver",
            trend_label=trend.label,
            current_year_ranks=[pl_redraft_rank, espn_points_rank],
            dynasty_ranks=[pl_dynasty_rank, espn_dynasty_rank, keeper_projected_pick],
            weight_profile=configured_weights,
        )
        return {
            "name": player.name,
            "normalized_name": player.normalized_name,
            "mlb_team": player.mlb_team,
            "positions": player.positions,
            "percent_owned": player.percent_owned,
            "redraft_rank": pl_redraft_rank,
            "espn_points_rank": espn_points_rank,
            "current_year_rank": current_year_rank,
            "pl_dynasty_rank": pl_dynasty_rank,
            "espn_dynasty_rank": espn_dynasty_rank,
            "keeper_drafted_round": keeper_entry.drafted_round if keeper_entry else None,
            "keeper_drafted_round_pick": keeper_entry.drafted_round_pick if keeper_entry else None,
            "keeper_projected_round": keeper_entry.projected_keeper_round if keeper_entry else None,
            "keeper_projected_pick": keeper_projected_pick,
            "dynasty_rank": dynasty_rank,
            "trend": {
                "label": trend.label,
                "summary": trend.summary,
                "games": trend.games,
                "avg": trend.avg,
                "ops": trend.ops,
                "hr": trend.hr,
                "sb": trend.sb,
                "rbi": trend.rbi,
                "runs": trend.runs,
            },
            "recommendation": {
                "action": rec.action,
                "reason": rec.reason,
                "score": rec.score,
            },
            "scoring": scoring,
        }

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=trend_workers) as executor:
        futures = [executor.submit(_build_row, player) for player in free_agents]
        for future in as_completed(futures):
            rows.append(future.result())

    rows.sort(
        key=lambda row: (
            -(row["recommendation"]["score"]),
            (row["current_year_rank"] or 9999),
            (row["dynasty_rank"] or 9999),
            -(row["percent_owned"] or 0.0),
        )
    )
    rows = rows[:top]

    return {
        "generated_on": date.today().isoformat(),
        "league": context.league.settings.name,
        "top": len(rows),
        "weights": configured_weights,
        "rows": rows,
    }
