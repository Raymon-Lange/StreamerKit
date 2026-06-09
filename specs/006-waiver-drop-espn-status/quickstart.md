# Quickstart: Waiver Drop ESPN Status Display

## What changes

Three touch points, all additive — no existing behaviour is removed or modified.

## 1. `services/waivers_service.py`

Add a normalization helper and call it when serializing each row.

```python
_ESPN_STATUS_LABELS = {
    "ACTIVE": None,
    "INJURY_RESERVE": "IR",
    "DAY_TO_DAY": "DTD",
    "TEN_DAY_DL": "10-IL",
    "FIFTEEN_DAY_DL": "15-IL",
    "SIXTY_DAY_DL": "60-IL",
    "SEVEN_DAY_DL": "7-IL",
    "OUT": "OUT",
    "SUSPENSION": "SSPD",
    "NA": "N/A",
}

def _normalize_espn_status(raw: str | None) -> str | None:
    if raw is None:
        return None
    return _ESPN_STATUS_LABELS.get(raw, raw)
```

In both `_serialize_hitter_row` and `_serialize_pitcher_row`, return `"espn_status": _normalize_espn_status(player.injury_status)`.

In `get_recent_drops_waiver_review`, include `espn_status` in the `serialized` dict built for each row (sourced from `row["espn_status"]` after the serialize call).

## 2. `scripts/run_recent_drops_waiver_review.py`

On the player header print line, append the status label when non-null:

```python
status = row.get("espn_status")
status_str = f" [{status}]" if status else ""
print(
    f"{row['name']}{status_str} | {row.get('mlb_team') or 'N/A'} | Pos: {positions} | ..."
)
```

## 3. `frontend/src/components/RecentDrops.tsx`

Add `espn_status` to the `DropRow` interface and render a badge when non-null:

```typescript
interface DropRow {
  name: string
  mlb_team: string
  kind: 'H' | 'P'
  dropped_by: string
  espn_status: string | null       // ← new
  recommendation: { action: string; reason: string; score: number }
}
```

Badge render (next to name):
```tsx
{r.espn_status && (
  <span className="text-xs font-semibold text-red-400 ml-1">[{r.espn_status}]</span>
)}
```

## Verification

```bash
# CLI: run against live league data and look for [IR] / [DTD] labels
python scripts/run_recent_drops_waiver_review.py --days 3

# API: confirm field appears in every row
curl -s http://localhost:8000/api/recent-drops | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data['rows']:
    print(r['name'], '→', r.get('espn_status'))
"
```
