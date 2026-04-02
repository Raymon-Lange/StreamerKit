from __future__ import annotations

import sys
from dataclasses import dataclass

from models.player import PlayerRecord
from utils.config import AppConfig
from utils.names import normalize_name

HITTER_POSITIONS = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "DH", "UTIL"}
PITCHER_POSITIONS = {"P", "SP", "RP"}
DEFAULT_HITTER_QUERIES = ["C", "1B", "2B", "3B", "SS", "OF", "DH"]


@dataclass(slots=True)
class EspnContext:
    league: object
    config: AppConfig


def get_league(config: AppConfig):
    try:
        from espn_api.baseball import League
    except ImportError:
        sys.exit("[error] espn-api is not installed. Run: pip install espn-api")

    if not config.league_id:
        sys.exit("[error] No league ID set. Pass --league-id or set LEAGUE_ID.")

    if not config.espn_s2 or not config.espn_swid:
        sys.exit("[error] ESPN credentials missing. Set ESPN_S2 and ESPN_SWID environment variables.")

    try:
        return League(
            league_id=config.league_id,
            year=config.year,
            espn_s2=config.espn_s2,
            swid=config.espn_swid,
        )
    except Exception as exc:
        sys.exit(f"[error] Could not connect to ESPN: {exc}")


def build_context(config: AppConfig | None = None) -> EspnContext:
    cfg = config or AppConfig()
    return EspnContext(league=get_league(cfg), config=cfg)


def _raw_positions(player) -> set[str]:
    eligible = {str(x).upper() for x in (getattr(player, "eligibleSlots", []) or [])}
    slot = str(getattr(player, "slot_position", "") or getattr(player, "slotPosition", "") or "").upper()
    pos = str(getattr(player, "position", "") or "").upper()
    pro_pos = str(getattr(player, "proPosition", "") or "").upper()
    return eligible | {slot, pos, pro_pos}


def is_hitter(player) -> bool:
    combined = _raw_positions(player)
    if PITCHER_POSITIONS & combined:
        return False
    return bool(HITTER_POSITIONS & combined)


def is_pitcher(player) -> bool:
    return bool(PITCHER_POSITIONS & _raw_positions(player))


def player_to_record(player, source: str) -> PlayerRecord:
    positions = [
        str(x) for x in (getattr(player, "eligibleSlots", []) or [])
        if str(x) not in {"BE", "IL", "IL10", "IL15", "IL60", "NA"}
    ]
    team = getattr(player, "proTeam", None) or None
    external_id = getattr(player, "playerId", None)
    percent_owned = getattr(player, "percent_owned", None)
    return PlayerRecord(
        name=player.name,
        normalized_name=normalize_name(player.name),
        mlb_team=team,
        positions=positions,
        percent_owned=percent_owned,
        source=source,
        external_id=external_id,
        espn_raw=player,
    )


def get_team(context: EspnContext, team_id: int | None = None):
    if team_id is None:
        team_id = context.config.team_id or 1
    if team_id < 1 or team_id > len(context.league.teams):
        sys.exit(f"[error] team-id must be between 1 and {len(context.league.teams)}")
    return context.league.teams[team_id - 1]


def get_roster_players(context: EspnContext, team_id: int | None = None, player_type: str = "all") -> list[PlayerRecord]:
    team = get_team(context, team_id=team_id)
    roster = getattr(team, "roster", []) or []

    if player_type == "hitters":
        roster = [p for p in roster if is_hitter(p)]
    elif player_type == "pitchers":
        roster = [p for p in roster if is_pitcher(p)]

    return [player_to_record(player, source="espn_roster") for player in roster]


def get_free_agent_hitters(context: EspnContext, size_per_pos: int = 75) -> list[PlayerRecord]:
    deduped: dict[str | int, object] = {}

    for pos in DEFAULT_HITTER_QUERIES:
        try:
            batch = context.league.free_agents(size=size_per_pos, position=pos)
        except Exception as exc:
            print(f"[warning] Could not fetch {pos} free agents: {exc}")
            continue

        for player in batch:
            if not is_hitter(player):
                continue
            key = getattr(player, "playerId", None) or normalize_name(player.name)
            current = deduped.get(key)
            if current is None:
                deduped[key] = player
                continue
            current_owned = getattr(current, "percent_owned", 0.0) or 0.0
            new_owned = getattr(player, "percent_owned", 0.0) or 0.0
            if new_owned > current_owned:
                deduped[key] = player

    return [player_to_record(player, source="espn_free_agent") for player in deduped.values()]


def get_free_agent_pitchers(context: EspnContext, size: int = 200, position: str = "SP") -> list[PlayerRecord]:
    try:
        batch = context.league.free_agents(size=size, position=position)
    except Exception as exc:
        sys.exit(f"[error] Could not fetch free agents: {exc}")
    return [player_to_record(player, source="espn_free_agent") for player in batch if is_pitcher(player)]


def get_all_roster_pitchers(context: EspnContext) -> list[PlayerRecord]:
    deduped: dict[str | int, object] = {}

    for team in context.league.teams:
        for player in (getattr(team, "roster", []) or []):
            if not is_pitcher(player):
                continue
            key = getattr(player, "playerId", None) or normalize_name(player.name)
            current = deduped.get(key)
            if current is None:
                deduped[key] = player
                continue
            current_owned = getattr(current, "percent_owned", 0.0) or 0.0
            new_owned = getattr(player, "percent_owned", 0.0) or 0.0
            if new_owned > current_owned:
                deduped[key] = player

    return [player_to_record(player, source="espn_roster") for player in deduped.values()]
