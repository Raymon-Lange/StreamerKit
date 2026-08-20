from __future__ import annotations

from espn_api.baseball.constant import POSITION_MAP

from app import response_cache
from collectors.espn import EspnWriteError, build_context, get_roster_players, get_team, swap_lineup_slots
from models.player import LineupMove, SwapResult
from utils.config import AppConfig

_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}


def _lineup_slot_label(player_record) -> str:
    return str(getattr(player_record.espn_raw, "lineupSlot", "") or "").upper()


def _find_player(players, player_id: int):
    for player in players:
        if player.external_id == player_id:
            return player
    return None


def _eligibility_error(mover, target_slot: str) -> str | None:
    """Return an error message if `mover` cannot legally occupy `target_slot`, else None."""
    if target_slot in _BENCH_SLOTS:
        return None
    if target_slot not in mover.positions:
        eligible = ", ".join(mover.positions) or "none"
        return f"{mover.name} is not eligible for {target_slot} (eligible: {eligible})"
    return None


def swap_players(
    player_a_id: int,
    player_b_id: int,
    team_id: int | None = None,
    dry_run: bool = False,
) -> SwapResult:
    config = AppConfig(team_id=team_id or AppConfig().team_id)
    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)
    players = get_roster_players(context, team_id=team.team_id)

    player_a = _find_player(players, player_a_id)
    player_b = _find_player(players, player_b_id)
    if player_a is None or player_b is None:
        missing = "first player" if player_a is None else "second player"
        return SwapResult(success=False, message=f"Could not find the {missing} on this roster.")

    slot_a = _lineup_slot_label(player_a)
    slot_b = _lineup_slot_label(player_b)
    if slot_a not in POSITION_MAP or slot_b not in POSITION_MAP:
        return SwapResult(success=False, message="Could not resolve a lineup slot for one of the selected players.")

    error = _eligibility_error(player_a, slot_b) or _eligibility_error(player_b, slot_a)
    if error:
        return SwapResult(success=False, message=error)

    moves = [
        LineupMove(player_id=player_a.external_id, from_slot_id=POSITION_MAP[slot_a], to_slot_id=POSITION_MAP[slot_b]),
        LineupMove(player_id=player_b.external_id, from_slot_id=POSITION_MAP[slot_b], to_slot_id=POSITION_MAP[slot_a]),
    ]

    if dry_run:
        return SwapResult(
            success=True,
            message=f"Dry run OK: would swap {player_a.name} ({slot_a}) <-> {player_b.name} ({slot_b}) for tomorrow.",
        )

    try:
        swap_lineup_slots(context, team.team_id, moves)
    except EspnWriteError as exc:
        return SwapResult(success=False, message=str(exc))

    response_cache.invalidate_prefix("my_roster_")
    response_cache.invalidate_prefix("optimizer_")
    return SwapResult(
        success=True,
        message=f"Swapped {player_a.name} ({slot_a}) <-> {player_b.name} ({slot_b}) for tomorrow's lineup.",
    )
