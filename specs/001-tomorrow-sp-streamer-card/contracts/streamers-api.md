# Contract: Streamers API

**Feature**: 001-tomorrow-sp-streamer-card
**Date**: 2026-06-01

## Endpoint

```
GET /api/streamers?tomorrow=true
```

**Auth**: `X-API-Key: <VITE_API_KEY>` header required

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tomorrow` | boolean | `false` | When `true`, returns streamers for tomorrow's probable starters |
| `pitcher` | string \| null | `null` | Optional filter to a single pitcher by name |

## Response

**Status 200**:

```json
{
  "rows": [
    {
      "name": "Corbin Burnes",
      "mlb_team": "BAL",
      "tier": "Must Stream",
      "streamer_rank": 1,
      "percent_owned": 94.2,
      "recommendation": {
        "action": "STREAM",
        "reason": "Elite tier, favorable matchup"
      }
    }
  ]
}
```

**Empty result** (no probable starters for tomorrow):

```json
{ "rows": [] }
```

**Status 401**: Missing or invalid API key

**Status 500**: Upstream data fetch failure (ESPN or Pitcher List unavailable)

## Caching

Responses are cached server-side for **300 seconds** (5 minutes) keyed by
`streamers_<date>_all`. The `TomorrowStreamers` component should not implement
its own client-side caching — the server TTL is sufficient.

## Frontend client

```typescript
// frontend/src/api.ts — already implemented
api.streamers(true)   // calls /api/streamers?tomorrow=true
```
