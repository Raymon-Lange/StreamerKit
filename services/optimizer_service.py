from __future__ import annotations

from datetime import date

from collectors.espn import build_context, get_roster_players, get_team
from collectors.mlb_stats import summarize_recent_hitting
from collectors.pitcherlist import scrape_top_hitters
from engines.hitter_engine import evaluate_daily_hitter, find_lineup_upgrades
from utils.config import AppConfig

_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}


def _lineup_slot(player_record) -> str:
    return str(getattr(player_record.espn_raw, "lineupSlot", "") or "").upper()


def get_roster_optimizer(
    league_id: int | None = None,
    team_id: int | None = None,
    year: int | None = None,
    trend_games: int = 10,
    min_gap: float = 10.0,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        team_id=team_id or AppConfig().team_id,
        year=year or AppConfig().year,
    )
    trend_games = trend_games or 10
    min_gap = min_gap or 10.0

    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)
    redraft = scrape_top_hitters()
    hitters = get_roster_players(context, team_id=team.team_id, player_type="hitters")

    rows = []
    for player in hitters:
        redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
        trend = summarize_recent_hitting(player.name, trend_games=trend_games)
        rec = evaluate_daily_hitter(redraft_rank, trend.label)
        lineup_slot = _lineup_slot(player)
        rows.append((player, redraft_rank, None, trend, rec, lineup_slot))

    active_count = sum(1 for *_, s in rows if s not in _BENCH_SLOTS and s)
    bench_count = len(rows) - active_count
    swaps = find_lineup_upgrades(rows, min_score_gap=min_gap)

    serialized_swaps = []
    for swap in swaps:
        serialized_swaps.append({
            "start": {
                "name": swap.start.name,
                "mlb_team": swap.start.mlb_team,
                "positions": swap.start.positions,
                "action": swap.start_rec.action,
                "reason": swap.start_rec.reason,
                "trend_label": swap.start_trend.label,
                "trend_summary": swap.start_trend.summary,
            },
            "sit": {
                "name": swap.sit.name,
                "mlb_team": swap.sit.mlb_team,
                "positions": swap.sit.positions,
                "action": swap.sit_rec.action,
                "trend_label": swap.sit_trend.label,
                "trend_summary": swap.sit_trend.summary,
            },
            "slot": swap.slot,
            "score_gap": round(swap.score_gap, 1),
        })

    return {
        "generated_on": date.today().isoformat(),
        "league": context.league.settings.name,
        "team": getattr(team, "team_name", None),
        "roster_hitter_count": len(rows),
        "active_count": active_count,
        "bench_count": bench_count,
        "swap_count": len(serialized_swaps),
        "swaps": serialized_swaps,
    }
