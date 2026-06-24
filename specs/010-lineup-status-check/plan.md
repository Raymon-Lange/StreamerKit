# Implementation Plan: Player Lineup Status Check

**Branch**: `010-lineup-status-check` | **Date**: 2026-06-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-lineup-status-check/spec.md`

## Summary

Add a player lineup status lookup that, given a player name and optional date, returns whether that player is in the starting batting lineup for today's MLB game. Exposed via a new authenticated REST endpoint (`GET /api/lineup`) and a thin CLI script. Implemented as a new collector function in `collectors/mlb_stats.py`, a thin service in `services/lineup_service.py`, and a new FastAPI router in `app/routes/lineup.py`. A `LineupStatus` dataclass is added to `models/player.py` for inter-module data exchange.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI (existing), `requests` (existing), `statsapi` (existing for MLB data), `python-dotenv` (existing)

**Storage**: No persistent storage. Response cache (`app/response_cache`) used with 120s TTL.

**Testing**: pytest (existing test suite in `tests/`)

**Target Platform**: Linux server (Docker container), same as rest of project

**Project Type**: Web service + CLI tool

**Performance Goals**: Lineup query completes within 5 seconds (per spec SC-001); ESPN API calls are the bottleneck (~1–2s each; up to ~15 events on a full game day requiring one summary fetch per event until player found)

**Constraints**: ESPN public API must be hit per request (no event-level caching); response cache at the route level reduces repeat hits within 2-minute windows

**Scale/Scope**: Single-player lookup per request; no fan-out parallelism needed (early-exit once player found)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layer Separation | ✅ PASS | Route → `services/lineup_service` → `collectors/mlb_stats`. No collector calls from route. No HTTP in service. |
| II. Shared Data Model | ✅ PASS | New `LineupStatus` dataclass added to `models/player.py`. `normalize_name()` used for name matching. No raw `dict` across module boundaries. |
| III. Resilient External Data | ✅ PASS | ESPN fetch wrapped in try/except with graceful fallback (returns `status="no_game"` on failure). No caching needed at collector level — data is ephemeral. Route-level response cache applied. |
| IV. Weighted Scoring | N/A | No scoring or recommendation logic in this feature. |
| V. Simplicity First | ✅ PASS | One new collector function, one thin service, one router, one CLI script. No new abstractions. `services/lineup_service.py` is required by constitution even though it wraps a single collector call. |

**Post-design re-check**: All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/010-lineup-status-check/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/
│   └── api-lineup.md    # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
models/
└── player.py            # + LineupStatus dataclass (new)

collectors/
└── mlb_stats.py         # + get_player_lineup_status() (new function)

services/
└── lineup_service.py    # new thin service

app/
├── main.py              # + 1 line: include lineup.router
└── routes/
    └── lineup.py        # new FastAPI router

scripts/
└── check_lineup.py      # new thin CLI script

main.py                  # + menu entry for check_lineup
```

**Structure Decision**: Single-project layout, consistent with the rest of the codebase. No new directories added. Files placed in existing layers per constitution.

## Implementation Steps

### Step 1 — Add `LineupStatus` to `models/player.py`

Add after the existing `LineupSwap` dataclass:

```python
@dataclass(slots=True)
class LineupStatus:
    player_name: str
    in_lineup: bool
    status: str            # "starting" | "bench" | "no_game" | "not_found" | "lineup_not_posted"
    batting_slot: int | None = None
    team: str | None = None
    opponent: str | None = None
    game_time: str | None = None
```

---

### Step 2 — Add `get_player_lineup_status()` to `collectors/mlb_stats.py`

New function added after `get_todays_probable_starters()`. Hits the ESPN scoreboard to enumerate today's events, then fetches each game's summary until the player is found in the boxscore.

```python
def get_player_lineup_status(player_name: str, for_date: date | None = None) -> LineupStatus:
    query_key = normalize_name(player_name)
    date_str = (for_date or date.today()).strftime("%Y%m%d")
    scoreboard_url = (
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={date_str}"
    )

    try:
        with log_feed_fetch("mlb_stats", "get_player_lineup_status"):
            resp = requests.get(scoreboard_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return LineupStatus(player_name=player_name, in_lineup=False, status="no_game")

    events = data.get("events", [])
    if not events:
        return LineupStatus(player_name=player_name, in_lineup=False, status="no_game")

    for event in events:
        event_id = event.get("id")
        game_time = event.get("date")  # ISO 8601 UTC
        competitions = event.get("competitions", [])

        # Identify which team abbreviations are in this game
        team_abbrs: list[str] = []
        for comp in competitions:
            for competitor in comp.get("competitors", []):
                team_abbrs.append(_team_abbreviation(competitor.get("team", {})))

        # Fetch boxscore summary for this event
        summary_url = (
            f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?event={event_id}"
        )
        try:
            summary_resp = requests.get(summary_url, timeout=10)
            summary_resp.raise_for_status()
            summary = summary_resp.json()
        except Exception:
            continue

        players_sections = summary.get("boxscore", {}).get("players", [])
        if not players_sections:
            # Game exists but boxscore not yet populated
            # Still check name against roster; if found, return lineup_not_posted
            continue

        for section in players_sections:
            team_obj = section.get("team", {})
            team_abbr = _team_abbreviation(team_obj)
            opponent_abbr = next((a for a in team_abbrs if a != team_abbr), None)

            stats_list = section.get("statistics", [])
            if not stats_list:
                continue
            athletes = stats_list[0].get("athletes", [])

            for athlete_entry in athletes:
                athlete = athlete_entry.get("athlete", {})
                display_name = athlete.get("displayName") or athlete.get("fullName", "")
                if normalize_name(display_name) != query_key:
                    continue

                starter = athlete_entry.get("starter", False)
                bat_order = athlete_entry.get("batOrder")
                batting_slot = int(bat_order) if bat_order else None

                return LineupStatus(
                    player_name=display_name,
                    in_lineup=bool(starter),
                    status="starting" if starter else "bench",
                    batting_slot=batting_slot if starter else None,
                    team=team_abbr,
                    opponent=opponent_abbr,
                    game_time=game_time,
                )

    return LineupStatus(player_name=player_name, in_lineup=False, status="not_found")
```

**Import additions needed at top of `mlb_stats.py`**:
- `from models.player import LineupStatus` (add to existing import)
- `from utils.names import normalize_name` (add new import)

---

### Step 3 — Add `services/lineup_service.py`

```python
from __future__ import annotations

from datetime import date

from collectors.mlb_stats import get_player_lineup_status
from models.player import LineupStatus


def get_lineup_status(player_name: str, for_date: date | None = None) -> LineupStatus:
    return get_player_lineup_status(player_name, for_date=for_date)
```

---

### Step 4 — Add `app/routes/lineup.py`

Follow the `pitcher_starts.py` pattern exactly.

```python
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app import response_cache
from services.lineup_service import get_lineup_status

router = APIRouter()

_TTL = 120


@router.get("/lineup")
async def lineup_status(
    player: str = Query(..., description="Player name to look up"),
    date: str | None = Query(default=None, description="Date in YYYY-MM-DD format (defaults to today)"),
) -> dict:
    for_date: date | None = None
    if date is not None:
        from datetime import date as _date
        try:
            for_date = _date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be in YYYY-MM-DD format")

    cache_key = f"lineup_{player}_{(for_date or _date.today()).isoformat()}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached

    result = get_lineup_status(player, for_date=for_date)
    data = {
        "player_name": result.player_name,
        "in_lineup": result.in_lineup,
        "status": result.status,
        "batting_slot": result.batting_slot,
        "team": result.team,
        "opponent": result.opponent,
        "game_time": result.game_time,
    }
    response_cache.set(cache_key, data)
    return data
```

---

### Step 5 — Register router in `app/main.py`

In the imports line, add `lineup` alongside the existing route imports:

```python
from app.routes import dashboard, drops, feed_status, health, lineup, optimizer, pitcher_starts, streamers, weekly_scores
```

After the existing `app.include_router(optimizer.router, ...)` line:

```python
app.include_router(lineup.router, prefix="/api", **_protected)
```

---

### Step 6 — Add `scripts/check_lineup.py`

```python
from __future__ import annotations

import argparse
from datetime import date

from services.lineup_service import get_lineup_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Check if an MLB player is in today's starting lineup")
    parser.add_argument("--player", required=True, help="Player name")
    parser.add_argument("--date", default=None, help="Date in YYYY-MM-DD format (default: today)")
    args = parser.parse_args()

    for_date: date | None = None
    if args.date:
        for_date = date.fromisoformat(args.date)

    result = get_lineup_status(args.player, for_date=for_date)

    game_ctx = ""
    if result.team and result.opponent:
        game_ctx = f" ({result.team} vs {result.opponent})"

    if result.status == "starting":
        print(f"{result.player_name}: IN LINEUP — batting {result.batting_slot}{game_ctx}")
    elif result.status == "bench":
        print(f"{result.player_name}: NOT in starting lineup{game_ctx}")
    elif result.status == "no_game":
        print(f"{result.player_name}: No game scheduled today")
    elif result.status == "lineup_not_posted":
        print(f"{result.player_name}: Game scheduled{game_ctx}, lineup not yet posted")
    else:
        print(f"{result.player_name}: Player not found in today's lineups")


if __name__ == "__main__":
    main()
```

---

### Step 7 — Register in `main.py` menu

Add a menu entry in `main.py` so `python main.py` surfaces the new script alongside the others.

---

## Verification Steps

1. `python scripts/check_lineup.py --player "Jarren Duran"` — produces one-line human-readable output
2. `python scripts/check_lineup.py --player "Nonexistent Player"` — returns "not found" cleanly
3. `curl -H "X-API-Key: $API_KEY" "localhost:8000/api/lineup?player=Jarren+Duran"` — returns JSON with all fields
4. Query on a known off-day or for a player with no game → `status: "no_game"`
5. Query before lineups are posted → `status: "lineup_not_posted"` (boxscore athletes empty)

## Complexity Tracking

> No constitution violations. No complexity justification required.
