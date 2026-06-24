from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date

from collectors.espn import build_context, get_roster_players, get_team, is_hitter
from collectors.mlb_stats import get_player_lineup_status
from utils.config import AppConfig

_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}


def _lineup_slot(player_record) -> str:
    return str(getattr(player_record.espn_raw, "lineupSlot", "") or "").upper() or "?"


def _serialize_player(player, slot: str, status) -> dict:
    return {
        "name": player.name,
        "mlb_team": player.mlb_team,
        "lineup_slot": slot,
        "injury_status": player.injury_status,
        "in_lineup": status.in_lineup if status is not None else None,
        "lineup_status": status.status if status is not None else None,
        "batting_slot": status.batting_slot if status is not None else None,
    }


def get_roster_card(
    league_id: int | None = None,
    team_id: int | None = None,
    year: int | None = None,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        team_id=team_id or AppConfig().team_id,
        year=year or AppConfig().year,
    )

    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)
    players = get_roster_players(context, team_id=team.team_id)

    hitters = [p for p in players if is_hitter(p)]

    def _fetch_status(player):
        try:
            return get_player_lineup_status(player.name)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(_fetch_status, hitters))

    hitter_status = dict(zip(hitters, statuses))

    starters = []
    bench = []

    for player in players:
        slot = _lineup_slot(player)
        status = hitter_status.get(player)
        row = _serialize_player(player, slot, status)
        if slot in _BENCH_SLOTS:
            bench.append(row)
        else:
            starters.append(row)

    return {
        "generated_on": date.today().isoformat(),
        "team": getattr(team, "team_name", None),
        "starters": starters,
        "bench": bench,
    }
