from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from collectors.espn import build_context, get_free_agent_hitters
from collectors.espn_dynasty import scrape_espn_dynasty_hitters
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_top_hitters
from engines.hitter_engine import evaluate_free_agent_hitter
from utils.config import AppConfig


def get_free_agent_hitter_recommendations(
    league_id: int | None = None,
    year: int | None = None,
    top: int = 10,
    size: int = 75,
    trend_games: int = 15,
    trend_workers: int = 12,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        year=year or AppConfig().year,
    )
    trend_workers = max(1, trend_workers)
    context = build_context(config)

    redraft = scrape_top_hitters()
    pl_dynasty = scrape_dynasty_hitters()
    espn_dynasty = scrape_espn_dynasty_hitters()
    free_agents = get_free_agent_hitters(context, size_per_pos=size)

    def _build_row(player):
        redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
        pl_dynasty_rank = pl_dynasty.get(player.normalized_name).rank if player.normalized_name in pl_dynasty else None
        espn_dynasty_rank = espn_dynasty.get(player.normalized_name).rank if player.normalized_name in espn_dynasty else None
        dynasty_rank = min((rank for rank in (pl_dynasty_rank, espn_dynasty_rank) if rank is not None), default=None)
        trend = summarize_recent_hitting(player.name, trend_games=trend_games)
        rec = evaluate_free_agent_hitter(redraft_rank, dynasty_rank, trend.label)
        return {
            "name": player.name,
            "normalized_name": player.normalized_name,
            "mlb_team": player.mlb_team,
            "positions": player.positions,
            "percent_owned": player.percent_owned,
            "redraft_rank": redraft_rank,
            "pl_dynasty_rank": pl_dynasty_rank,
            "espn_dynasty_rank": espn_dynasty_rank,
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
        }

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=trend_workers) as executor:
        futures = [executor.submit(_build_row, player) for player in free_agents]
        for future in as_completed(futures):
            rows.append(future.result())

    rows.sort(
        key=lambda row: (
            -(row["recommendation"]["score"]),
            (row["redraft_rank"] or 9999),
            (row["dynasty_rank"] or 9999),
            -(row["percent_owned"] or 0.0),
        )
    )
    rows = rows[:top]

    return {
        "generated_on": date.today().isoformat(),
        "league": context.league.settings.name,
        "top": len(rows),
        "rows": rows,
    }

