# Data Model: IL Status Filter

**Feature**: 003-il-status-filter | **Date**: 2026-06-04

---

## Modified Entity: PlayerRecord

**File**: `models/player.py`

```python
@dataclass(slots=True)
class PlayerRecord:
    name: str
    normalized_name: str
    mlb_team: str | None = None
    positions: list[str] = field(default_factory=list)
    percent_owned: float | None = None
    source: str | None = None
    external_id: str | int | None = None
    espn_raw: Any = None
    injury_status: str | None = None      # ← NEW
```

**Field**: `injury_status`
- **Type**: `str | None`
- **Source**: `espn_api.baseball.player.Player.injuryStatus` (populated from ESPN payload)
- **Populated by**: `collectors/espn.py → player_to_record()`
- **Semantics**: Raw ESPN string value; `None` is treated as equivalent to `"ACTIVE"` by all consumers
- **Possible values**: `"ACTIVE"`, `"DAY_TO_DAY"`, `"QUESTIONABLE"`, `"OUT"`, `"INJURY_RESERVE"`, `"SUSPENSION"`, `None`
- **Mutability**: Read-only after creation; no business logic on the model itself

---

## InjuryStatus Value Reference

| ESPN Value | Severity | CLI Label | Web Badge | Web Color |
|------------|----------|-----------|-----------|-----------|
| `ACTIVE` or `None` | None | *(none)* | *(none)* | — |
| `QUESTIONABLE` | Low | `[QUES]` | `QUES` | yellow (`bg-yellow-900 text-yellow-300`) |
| `DAY_TO_DAY` | Medium | `[DTD]` | `DTD` | orange (`bg-orange-900 text-orange-300`) |
| `OUT` | High | `[OUT]` | `OUT` | red (`bg-red-900 text-red-300`) |
| `INJURY_RESERVE` | High | `[IR]` | `IR` | red (`bg-red-900 text-red-300`) |
| `SUSPENSION` | High | `[SUSP]` | `SUSP` | red (`bg-red-900 text-red-300`) |

---

## Behavior by Context

| Context | What happens to injured players |
|---|---|
| Waiver wire (free agent hitters) | Included in suggestions; label/badge displayed |
| SP streamers | Included in suggestions; label/badge displayed |
| Roster optimizer (start/sit swaps) | `INJURY_RESERVE`, `OUT`, `SUSPENSION` filtered out before scoring |

---

## No New Entities

No new tables, collections, or cache entries. `injury_status` is a transient field derived
from the ESPN API payload at fetch time. It is not persisted between runs.
