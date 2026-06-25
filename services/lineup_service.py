from __future__ import annotations

from datetime import date

from collectors.mlb_stats import get_player_lineup_status
from models.player import LineupStatus


def get_lineup_status(player_name: str, for_date: date | None = None) -> LineupStatus:
    return get_player_lineup_status(player_name, for_date=for_date)
