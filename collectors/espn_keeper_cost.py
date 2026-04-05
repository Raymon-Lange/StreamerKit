from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from collectors.espn import EspnContext
from utils.names import normalize_name


@dataclass(slots=True)
class KeeperCostEntry:
    normalized_name: str
    player_name: str
    drafted_round: int
    drafted_round_pick: int | None
    projected_keeper_round: int
    projected_keeper_overall_pick: int | None
    team_id: int | None = None
    team_name: str | None = None
    keeper_status: bool | None = None


def _cache_path(league_id: int, year: int) -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / ".cache" / f"espn_keeper_cost_{league_id}_{year}.json"


def _serialize_rows(rows: dict[str, KeeperCostEntry]) -> list[dict]:
    return [
        {
            "normalized_name": entry.normalized_name,
            "player_name": entry.player_name,
            "drafted_round": entry.drafted_round,
            "drafted_round_pick": entry.drafted_round_pick,
            "projected_keeper_round": entry.projected_keeper_round,
            "projected_keeper_overall_pick": entry.projected_keeper_overall_pick,
            "team_id": entry.team_id,
            "team_name": entry.team_name,
            "keeper_status": entry.keeper_status,
        }
        for entry in rows.values()
    ]


def _deserialize_rows(rows: list[dict]) -> dict[str, KeeperCostEntry]:
    out: dict[str, KeeperCostEntry] = {}
    for row in rows:
        key = row.get("normalized_name")
        if not key:
            continue
        out[key] = KeeperCostEntry(
            normalized_name=key,
            player_name=row.get("player_name") or "",
            drafted_round=int(row.get("drafted_round") or 0),
            drafted_round_pick=row.get("drafted_round_pick"),
            projected_keeper_round=int(row.get("projected_keeper_round") or 0),
            projected_keeper_overall_pick=row.get("projected_keeper_overall_pick"),
            team_id=row.get("team_id"),
            team_name=row.get("team_name"),
            keeper_status=row.get("keeper_status"),
        )
    return out


def _load_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cache(path: Path, *, league_id: int, year: int, rows: dict[str, KeeperCostEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "league_id": league_id,
        "year": year,
        "rows": _serialize_rows(rows),
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _build_from_league(context: EspnContext) -> dict[str, KeeperCostEntry]:
    league = context.league
    team_count = max(len(getattr(league, "teams", []) or []), 1)
    picks = getattr(league, "draft", []) or []

    results: dict[str, KeeperCostEntry] = {}
    for pick in picks:
        name = getattr(pick, "playerName", None) or ""
        if not name:
            continue

        round_num = getattr(pick, "round_num", None)
        if round_num is None:
            continue
        drafted_round = int(round_num)
        if drafted_round <= 0:
            continue

        raw_round_pick = getattr(pick, "round_pick", None)
        drafted_round_pick = int(raw_round_pick) if raw_round_pick else None
        projected_keeper_round = max(1, drafted_round - 2)
        projected_keeper_overall_pick = None
        if drafted_round_pick is not None and drafted_round_pick > 0:
            projected_keeper_overall_pick = ((projected_keeper_round - 1) * team_count) + drafted_round_pick

        team = getattr(pick, "team", None)
        team_id = getattr(team, "team_id", None) if team is not None else None
        team_name = getattr(team, "team_name", None) if team is not None else None

        entry = KeeperCostEntry(
            normalized_name=normalize_name(name),
            player_name=name,
            drafted_round=drafted_round,
            drafted_round_pick=drafted_round_pick,
            projected_keeper_round=projected_keeper_round,
            projected_keeper_overall_pick=projected_keeper_overall_pick,
            team_id=team_id,
            team_name=team_name,
            keeper_status=getattr(pick, "keeper_status", None),
        )
        results[entry.normalized_name] = entry

    return results


def scrape_espn_keeper_cost(context: EspnContext, force_refresh: bool = False) -> dict[str, KeeperCostEntry]:
    league_id = int(context.config.league_id or 0)
    year = int(context.config.year)
    path = _cache_path(league_id=league_id, year=year)

    cached = _load_cache(path)
    if cached and not force_refresh:
        return _deserialize_rows(cached.get("rows", []))

    built = _build_from_league(context)
    _save_cache(path, league_id=league_id, year=year, rows=built)
    return built
