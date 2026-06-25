# API Contract: GET /api/my-roster

## Endpoint

`GET /api/my-roster`

## Authentication

`X-API-Key` header (same as all other `/api/*` routes).

## Query Parameters

None required. Team and league are resolved from server-side environment variables (`TEAM_ID`, `LEAGUE_ID`).

## Response

**Status 200**

```json
{
  "generated_on": "YYYY-MM-DD",
  "team": "string | null",
  "starters": [
    {
      "name": "string",
      "mlb_team": "string | null",
      "lineup_slot": "string",
      "injury_status": "string | null",
      "in_lineup": "boolean | null",
      "lineup_status": "string | null",
      "batting_slot": "integer | null"
    }
  ],
  "bench": [
    {
      "name": "string",
      "mlb_team": "string | null",
      "lineup_slot": "string",
      "injury_status": "string | null",
      "in_lineup": "boolean | null",
      "lineup_status": "string | null",
      "batting_slot": "integer | null"
    }
  ]
}
```

**Status 500** — ESPN API or MLB Stats API unavailable. Body: `{ "detail": "string" }`

## Caching

Response is cached server-side with a 120-second TTL (same as existing `/api/lineup` route) using `response_cache`.

## `lineup_status` Values

| Value | Meaning |
|-------|---------|
| `"starting"` | Player is confirmed in the real-life batting order |
| `"bench"` | Player is not in the batting order today |
| `"no_game"` | Player's team has no game today |
| `"lineup_not_posted"` | Team's lineup has not been released yet |
| `"not_found"` | Player could not be matched in MLB Stats |
| `null` | Not applicable (pitcher) |

## `in_lineup` Values

| Value | Meaning |
|-------|---------|
| `true` | Player is confirmed in the real-life batting order |
| `false` | Player is not in the batting order |
| `null` | Not checked (pitcher) |
