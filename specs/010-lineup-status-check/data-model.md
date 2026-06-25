# Data Model: Player Lineup Status Check

## New Entity: LineupStatus

**Location**: `models/player.py` (new dataclass, added to existing canonical model file)

```python
@dataclass(slots=True)
class LineupStatus:
    player_name: str
    in_lineup: bool
    status: str            # "starting" | "bench" | "no_game" | "not_found" | "lineup_not_posted"
    batting_slot: int | None = None
    team: str | None = None
    opponent: str | None = None
    game_time: str | None = None   # ISO 8601 UTC string from ESPN events[*].date
```

### Status Values

| Status | Meaning |
|--------|---------|
| `starting` | Player is in the starting lineup with a known batting order slot |
| `bench` | Player's team has a game today, but the player is not in the starting lineup |
| `no_game` | No game found for the player's team on the queried date |
| `not_found` | Player name could not be matched to any MLB roster |
| `lineup_not_posted` | Game exists but boxscore has no athletes yet (pre-game, lineups not yet announced) |

### Validation Rules

- `batting_slot` is set only when `status == "starting"` (1–9 for standard batting order)
- `team` and `opponent` are populated whenever a game is found (status is not `no_game` or `not_found`)
- `game_time` is populated whenever a game is found

---

## Existing Models Used (unchanged)

- `utils/names.normalize_name()` — used for player name matching in the collector
- No other existing models are modified or extended

---

## Data Flow

```
User query (player_name, date?)
    │
    ▼
services/lineup_service.py
    │  get_lineup_status(player_name, for_date) → LineupStatus
    ▼
collectors/mlb_stats.py
    │  get_player_lineup_status(player_name, date_str) → LineupStatus
    │
    ├─► ESPN Scoreboard API → list of events with event IDs and game times
    │
    └─► ESPN Summary API (per event) → boxscore athletes with starter/batOrder
            │
            └─► normalize_name() match → populate LineupStatus fields
```
