# Contract: GET /api/recent-drops

## Change

`espn_status` is added to every object in the `rows` array. All existing fields are unchanged — this is a purely additive change.

## Response shape (updated)

```json
{
  "generated_on": "2026-06-08T01:00:00Z",
  "league": "My League",
  "days": 2,
  "claim_mode": "all",
  "top": 5,
  "rows": [
    {
      "kind": "H",
      "name": "Player Name",
      "mlb_team": "NYY",
      "positions": ["OF"],
      "percent_owned": 42.1,
      "dropped_by": "Team A",
      "dropped_at": "2026-06-07T18:30:00+00:00",
      "espn_status": "IR",
      "recommendation": {
        "action": "CONSIDER",
        "reason": "Ranked but trending cold",
        "score": 55.0
      },
      "redraft_rank": 120,
      "dynasty_rank": 98,
      "trend": { ... }
    },
    {
      "kind": "P",
      "name": "Pitcher Name",
      "mlb_team": "LAD",
      "positions": ["SP"],
      "percent_owned": 15.0,
      "dropped_by": "Team B",
      "dropped_at": "2026-06-07T12:00:00+00:00",
      "espn_status": null,
      "recommendation": {
        "action": "PICKUP",
        "reason": "Tier 2 streamer",
        "score": 60.0
      },
      "tier": "Tier 2",
      "season_record": "5-3, 3.21 ERA",
      "last_ten_record": "2-1, 2.80 ERA"
    }
  ]
}
```

## Field: `espn_status`

| Value | Meaning |
|---|---|
| `"IR"` | Player is on the Injured Reserve |
| `"DTD"` | Day-to-day |
| `"10-IL"` / `"15-IL"` / `"60-IL"` | On the IL |
| `"OUT"` | Listed as out |
| `"SSPD"` | Suspended |
| `"N/A"` | Not available |
| `null` | Active or status unknown — no injury concern |
