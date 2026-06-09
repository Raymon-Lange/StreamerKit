# Data Model: Waiver Drop ESPN Status Display

## Existing entity — no schema changes

`PlayerRecord` (in `models/player.py`) already carries `injury_status: str | None`. No model changes are required.

## New derived field: `espn_status`

A normalized, display-ready version of `PlayerRecord.injury_status`. Produced at the service layer when serializing drop rows.

| Field | Type | Source | Notes |
|---|---|---|---|
| `espn_status` | `str \| null` | `player.injury_status` via normalization | `null` when player is active or status unknown |

## Normalization function

Input: raw ESPN status string or `None`
Output: short display label or `None`

```
_normalize_espn_status(raw) → label | None

ACTIVE       → None
None         → None
INJURY_RESERVE → "IR"
DAY_TO_DAY   → "DTD"
TEN_DAY_DL   → "10-IL"
FIFTEEN_DAY_DL → "15-IL"
SIXTY_DAY_DL → "60-IL"
SEVEN_DAY_DL → "7-IL"
OUT          → "OUT"
SUSPENSION   → "SSPD"
NA           → "N/A"
<unknown>    → raw value (pass-through)
```

## Serialized drop row (updated shape)

Both hitter and pitcher rows gain `espn_status`. All existing fields are unchanged.

```
{
  "kind": "H" | "P",
  "name": str,
  "mlb_team": str | null,
  "positions": [str],
  "percent_owned": float | null,
  "dropped_by": str,
  "dropped_at": str (ISO 8601),
  "espn_status": str | null,          ← NEW
  "recommendation": { "action": str, "reason": str, "score": float },
  // hitter-only fields ...
  // pitcher-only fields ...
}
```
