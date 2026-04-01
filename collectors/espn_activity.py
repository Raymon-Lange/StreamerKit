from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from collectors.espn import EspnContext, player_to_record
from models.player import PlayerRecord
from utils.names import normalize_name


@dataclass(slots=True)
class DropActivityRecord:
    occurred_at: datetime
    dropped_by: str
    player: PlayerRecord
    action: str


def _to_utc_datetime(epoch_ms: int | float | None) -> datetime | None:
    if epoch_ms is None:
        return None
    try:
        return datetime.fromtimestamp(float(epoch_ms) / 1000.0, tz=timezone.utc)
    except Exception:
        return None


def _team_label(team: object) -> str:
    if team is None:
        return "Unknown Team"
    for attr in ("team_name", "teamName", "name"):
        value = getattr(team, attr, None)
        if value:
            return str(value)
    return str(team)


def get_recent_drops(
    context: EspnContext,
    days: int = 2,
    page_size: int = 50,
    max_pages: int = 10,
) -> list[DropActivityRecord]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows: list[DropActivityRecord] = []

    for page in range(max_pages):
        offset = page * page_size
        try:
            activity = context.league.recent_activity(size=page_size, offset=offset)
        except Exception:
            break

        if not activity:
            break

        reached_older = False
        for entry in activity:
            occurred_at = _to_utc_datetime(getattr(entry, "date", None))
            if occurred_at is None:
                continue
            if occurred_at < cutoff:
                reached_older = True
                continue

            for team, action, player in getattr(entry, "actions", []):
                if action != "DROPPED" or not player:
                    continue
                if hasattr(player, "name"):
                    player_record = player_to_record(player, source="espn_recent_drop")
                else:
                    name = str(player).strip()
                    if not name:
                        continue
                    player_record = PlayerRecord(
                        name=name,
                        normalized_name=normalize_name(name),
                        source="espn_recent_drop",
                        espn_raw=player,
                    )
                rows.append(
                    DropActivityRecord(
                        occurred_at=occurred_at,
                        dropped_by=_team_label(team),
                        player=player_record,
                        action=action,
                    )
                )

        if reached_older:
            break

    rows.sort(key=lambda row: row.occurred_at, reverse=True)
    return rows
