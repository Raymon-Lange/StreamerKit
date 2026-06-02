# Data Model: Tomorrow's SP Streamer Card

**Feature**: 001-tomorrow-sp-streamer-card
**Date**: 2026-06-01

## Entities

### StreamerRow (existing — no changes)

The `TomorrowStreamers` component consumes the same response shape as the existing
`Streamers` component. No new type definitions are required.

```typescript
interface StreamerRow {
  name: string                              // pitcher display name
  mlb_team: string                          // MLB team abbreviation
  tier: string                              // Pitcher List tier label
  streamer_rank: number | null              // Pitcher List rank (null if unranked)
  percent_owned: number | null              // ESPN ownership % (null if unavailable)
  recommendation: {
    action: string                          // e.g. "STREAM", "SKIP"
    reason: string                          // human-readable explanation
  }
}
```

**Source**: `GET /api/streamers?tomorrow=true` → `{ rows: StreamerRow[] }`

**Valid tier values** (drives color coding):
- `"Must Stream"` → green
- `"Strong Stream"` → blue
- `"Streamer"` → yellow
- `"Deep League"` → orange
- `"Not Ranked"` → gray

## No new entities

This feature introduces no new data models, stores, or state shapes. All data is fetched
on mount and held in local React `useState` — no context, no global store, no persistence.
