# Data Model: Lineup & Bench Card

## Entities

### RosterSlot (API response unit)
Represents one player on the user's fantasy roster with their slot assignment and real-life status.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Player display name |
| `mlb_team` | `string \| null` | Player's MLB team abbreviation |
| `lineup_slot` | `string` | Fantasy roster slot (e.g., `C`, `1B`, `SP`, `BE`) |
| `injury_status` | `string \| null` | ESPN injury code (e.g., `DAY_TO_DAY`, `TEN_DAY_DL`) |
| `in_lineup` | `boolean \| null` | Real-life starting lineup status; `null` for pitchers |
| `lineup_status` | `string \| null` | Human-readable status: `"starting"`, `"bench"`, `"no_game"`, `"lineup_not_posted"`, `"not_found"`, `null` |
| `batting_slot` | `integer \| null` | Batting order position (1–9); `null` if not applicable |

### API Response Shape

```json
{
  "generated_on": "2026-06-24",
  "team": "My Team Name",
  "starters": [
    {
      "name": "Yordan Alvarez",
      "mlb_team": "HOU",
      "lineup_slot": "OF",
      "injury_status": null,
      "in_lineup": true,
      "lineup_status": "starting",
      "batting_slot": 3
    }
  ],
  "bench": [
    {
      "name": "Brandon Lowe",
      "mlb_team": "TB",
      "lineup_slot": "BE",
      "injury_status": "DAY_TO_DAY",
      "in_lineup": false,
      "lineup_status": "bench",
      "batting_slot": null
    }
  ]
}
```

## Slot Classification

Fantasy slots are classified as starters or bench using the constant already defined in `optimizer_service.py`:

```python
_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}
```

Players whose `lineup_slot` is in `_BENCH_SLOTS` appear in the `bench` array. All others appear in `starters`.

## Player Type Classification

Hitter detection reuses `is_hitter()` from `collectors/espn.py`. Only hitters receive a real-life lineup status lookup. Pitchers get `in_lineup: null` and `lineup_status: null`.

## Source Mapping

| Field | Source |
|-------|--------|
| `name`, `mlb_team`, `injury_status`, `lineup_slot` | ESPN roster via `get_roster_players()` + `lineupSlot` from `espn_raw` |
| `in_lineup`, `lineup_status`, `batting_slot` | MLB Stats API via `get_player_lineup_status()` (hitters only) |
