# API Contract: GET /streamers

**Feature**: 003-il-status-filter | **Change type**: Additive (backwards-compatible)

---

## Endpoint

`GET /api/streamers`

Optional query params: `pitcher` (string), `tomorrow` (bool)

---

## Response shape change

Each object in the `rows` array gains one new field:

```json
{
  "name": "Corbin Burnes",
  "mlb_team": "BAL",
  "tier": "Auto-Start",
  "streamer_rank": 1,
  "percent_owned": 72.4,
  "injury_status": "DAY_TO_DAY",
  "recommendation": { "action": "PICKUP — Auto-Start", "reason": "..." }
}
```

**New field**: `injury_status`
- **Type**: `string | null`
- **Values**: `"ACTIVE"`, `"DAY_TO_DAY"`, `"QUESTIONABLE"`, `"OUT"`, `"INJURY_RESERVE"`, `"SUSPENSION"`, or `null`
- **Null semantics**: `null` is equivalent to `"ACTIVE"` — no injury
- **Breaking change**: No. Additive field; existing clients that don't read it are unaffected.

---

## Service contract: `get_streaming_pitcher_review()`

`services/pitchers_service.py → _serialize_pitcher_row()` adds `injury_status` to the
returned dict. All downstream consumers (CLI script, FastAPI route) receive it automatically.

---

## CLI output change

`scripts/run_sp_streamers.py` appends a bracketed label to the player name line:

**Before**: `🟢 Corbin Burnes | BAL | Owned: 72.4%`
**After**: `🟢 Corbin Burnes [DTD] | BAL | Owned: 72.4%`

No label is printed when `injury_status` is `"ACTIVE"` or `None`.
