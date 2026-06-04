# Data Model: Expandable Streamer Pitcher Row

**Branch**: `005-streamer-row-expand` | **Date**: 2026-06-04

## StreamerRow (extended TypeScript interface)

The existing `StreamerRow` interface currently covers only the fields used in the compact view. The full interface required for this feature:

```
StreamerRow {
  // --- already in interface ---
  name:             string
  mlb_team:         string
  tier:             string
  streamer_rank:    number | null
  percent_owned:    number | null
  injury_status:    string | null
  recommendation:   { action: string; reason: string; score?: number }

  // --- new fields for expanded view ---
  season_record:    string | null     // e.g. "5-3"
  last_ten_record:  string | null     // e.g. "3-2"
  last_two_starts:  string | null     // free-text description of last 2 starts
  opponent_team:    string | null     // opponent abbreviation for today's start
  opponent_score:   number | null     // PitcherList matchup difficulty score
}
```

## UI State

```
StreamerCard component state {
  rows:         StreamerRow[]     // loaded from API
  loading:      boolean
  error:        string | null
  expandedName: string | null     // name of currently expanded row, or null
}
```

## State Transitions

```
expandedName = null
  → user clicks row R   → expandedName = R.name

expandedName = R.name
  → user clicks row R   → expandedName = null   (collapse)
  → user clicks row S   → expandedName = S.name  (switch)
```

## Null / Missing Value Handling

Any `string | null` or `number | null` field in the expanded view renders as `"—"` when the value is `null`, `undefined`, or an empty string. No raw null, "undefined", or blank cell is shown.
