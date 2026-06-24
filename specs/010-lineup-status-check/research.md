# Research: Player Lineup Status Check

## Decision: Data Source

**Decision**: Use the ESPN public scoreboard API (`site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard`) combined with per-game summary API (`site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?event={event_id}`).

**Rationale**: The scoreboard endpoint is already used in `collectors/mlb_stats.py::get_todays_probable_starters()`. The summary endpoint provides `boxscore.players[*].statistics[0].athletes` which contains `starter` (bool), `batOrder` (int), and `position.abbreviation` per player. This was live-tested by the developer prior to spec creation.

**Alternatives considered**:
- MLB Stats API (`statsapi`): Provides live box scores via `statsapi.get("game", ...)` but requires a game ID lookup and returns a different data structure. The ESPN path was already proven in this codebase for scoreboard data.
- Baseball-Reference / other scrapers: Not appropriate; no existing scraping infrastructure in this project.

---

## Decision: Service Layer

**Decision**: Add `services/lineup_service.py` as a thin wrapper around `collectors/mlb_stats.get_player_lineup_status()`.

**Rationale**: The project constitution (Principle I) is explicit — app route handlers must delegate to `services/`, not directly to collectors. The existing `app/routes/pitcher_starts.py` follows this pattern: route → `services/pitchers_service.get_pitcher_start_evaluation()` → collectors. A service wrapper for lineup is required to stay compliant, even though it performs no multi-collector coordination.

**Alternatives considered**:
- Calling the collector directly from the route (as suggested in the original spec plan): Violates the constitution's layer boundary rule. Rejected.

---

## Decision: Data Model

**Decision**: Add a `LineupStatus` dataclass to `models/player.py` using `@dataclass(slots=True)`.

**Rationale**: The constitution (Principle II) requires all inter-module data exchange to use canonical types from `models/player.py`. Returning a plain `dict` across the service and route layer boundary is not permitted. The existing `LineupSwap` dataclass in `models/player.py` is for fantasy lineup decisions and is unrelated — a new `LineupStatus` dataclass is needed.

**Fields**: `player_name: str`, `in_lineup: bool`, `batting_slot: int | None`, `team: str | None`, `opponent: str | None`, `game_time: str | None`, `status: str` (one of: `"starting"`, `"bench"`, `"no_game"`, `"not_found"`, `"lineup_not_posted"`).

---

## Decision: Name Normalization

**Decision**: Use `utils/names.normalize_name()` for all player name matching.

**Rationale**: The constitution (Principle II) mandates `normalize_name()` for all cross-source player-name joins. Raw name comparison between ESPN API response names and the user-supplied query string must go through the same normalization. The function strips diacritics, lowercases, removes punctuation — sufficient for MLB roster names.

---

## Decision: Response Caching

**Decision**: Apply `app/response_cache` with a short TTL (120 seconds) in the route handler.

**Rationale**: Lineup data is volatile (changes at most once per day, but queried multiple times). A 2-minute cache avoids hammering the ESPN API for repeated queries of the same player. The `pitcher_starts` route uses a 5-minute TTL; 2 minutes is appropriate for lineup data since it may be updated closer to game time.

---

## Decision: CLI Script Pattern

**Decision**: Add `scripts/check_lineup.py` as a thin CLI entry point.

**Rationale**: The constitution (Development Workflow section) requires a `scripts/run_<workflow>.py` for each new workflow and registration in `main.py`. The CLI should follow the thin-script pattern: parse args → call service → print result.

---

## Resolved Unknowns

| Unknown | Resolution |
|---------|------------|
| ESPN boxscore endpoint structure | Confirmed: `summary?event={id}` → `boxscore.players[*].statistics[0].athletes[*]` contains `starter`, `batOrder`, `position.abbreviation` |
| How to get event IDs | From scoreboard response: `events[*].id` |
| Game time field | Available in scoreboard response as `events[*].date` (ISO 8601 UTC string) |
| Multi-game players (doubleheaders) | Return the first game found for the player's team; note limitation in response if needed |
