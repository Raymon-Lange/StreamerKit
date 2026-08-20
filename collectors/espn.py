from __future__ import annotations

import sys
from dataclasses import dataclass

import requests

from models.player import LineupMove, PlayerRecord
from utils.config import AppConfig
from utils.feed_logger import log_feed_fetch
from utils.names import normalize_name

HITTER_POSITIONS = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "DH", "UTIL"}
PITCHER_POSITIONS = {"P", "SP", "RP"}
DEFAULT_HITTER_QUERIES = ["C", "1B", "2B", "3B", "SS", "OF", "DH"]

# Undocumented ESPN endpoint, reverse-engineered from a captured browser request
# (docs/fantasy.espn.com.har) doing a real lineup swap. No official support or
# stability guarantee — ESPN can change this without notice.
_WRITE_ENDPOINT = (
    "https://lm-api-writes.fantasy.espn.com/apis/v3/games/flb"
    "/seasons/{year}/segments/0/leagues/{league_id}/transactions/"
)
_PLATFORM_VERSION = "92ddde53921921ea7953eb96dd0de450b18bcb8a"


class EspnWriteError(Exception):
    """Raised when ESPN rejects, or we cannot reach, a lineup-write request."""


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
        with log_feed_fetch("espn", "get_league"):
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
    injury_status = getattr(player, "injuryStatus", None) or None
    return PlayerRecord(
        name=player.name,
        normalized_name=normalize_name(player.name),
        mlb_team=team,
        positions=positions,
        percent_owned=percent_owned,
        source=source,
        external_id=external_id,
        espn_raw=player,
        injury_status=injury_status,
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


def swap_lineup_slots(context: EspnContext, team_id: int, moves: list[LineupMove]) -> dict:
    """POST a FUTURE_ROSTER LINEUP transaction to ESPN's write endpoint.

    ESPN rejects FUTURE_ROSTER transactions against the currently-open scoring
    period (HTTP 409, "Transaction type can only be executed in future scoring
    periods") — confirmed by testing against a live roster. This type only ever
    applies to the *next* day's lineup, so we target scoringPeriodId + 1.

    executionType is EXECUTE — this mutates the user's live roster for tomorrow.
    Raises EspnWriteError on any network failure, non-200 response, or a response
    whose status is not "EXECUTED".
    """
    cfg = context.config
    url = _WRITE_ENDPOINT.format(year=cfg.year, league_id=cfg.league_id)
    payload = {
        "isLeagueManager": False,
        "teamId": team_id,
        "type": "FUTURE_ROSTER",
        "memberId": cfg.espn_swid,
        "scoringPeriodId": context.league.scoringPeriodId + 1,
        "executionType": "EXECUTE",
        "items": [
            {
                "playerId": move.player_id,
                "type": "LINEUP",
                "fromLineupSlotId": move.from_slot_id,
                "toLineupSlotId": move.to_slot_id,
            }
            for move in moves
        ],
    }

    try:
        response = requests.post(
            url,
            params={"platformVersion": _PLATFORM_VERSION},
            json=payload,
            cookies={"espn_s2": cfg.espn_s2, "SWID": cfg.espn_swid},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Fantasy-Platform": "espn-fantasy-web",
                "X-Fantasy-Source": "kona",
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        raise EspnWriteError(f"Could not reach ESPN: {exc}") from exc

    if response.status_code != 200:
        raise EspnWriteError(f"ESPN rejected the swap (HTTP {response.status_code}): {response.text[:300]}")

    data = response.json()
    if data.get("status") != "EXECUTED":
        raise EspnWriteError(f"ESPN did not execute the swap (status={data.get('status')})")
    return data
