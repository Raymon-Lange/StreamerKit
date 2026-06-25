# API Contract: GET /api/lineup

## Endpoint

```
GET /api/lineup
```

## Authentication

Requires `X-API-Key` header matching the `API_KEY` environment variable. Returns `403 Forbidden` if missing or invalid (consistent with all other `/api/*` routes).

## Query Parameters

| Parameter | Type   | Required | Default      | Description |
|-----------|--------|----------|--------------|-------------|
| `player`  | string | Yes      | —            | Player name (URL-encoded). Matched via normalized name lookup. |
| `date`    | string | No       | Today's date | Date in `YYYY-MM-DD` format. Defaults to today if omitted. |

## Response: 200 OK

```json
{
  "player_name": "Jarren Duran",
  "in_lineup": true,
  "status": "starting",
  "batting_slot": 1,
  "team": "BOS",
  "opponent": "COL",
  "game_time": "2026-06-24T23:10:00Z"
}
```

### Status Values

| `status`           | `in_lineup` | Description |
|--------------------|-------------|-------------|
| `starting`         | `true`      | Player is in the starting lineup |
| `bench`            | `false`     | Player's team has a game; player is not starting |
| `no_game`          | `false`     | No game found for the player's team on the queried date |
| `not_found`        | `false`     | Player name could not be matched |
| `lineup_not_posted`| `false`     | Game exists but lineups not yet announced |

### Nullable Fields

- `batting_slot`: `null` unless `status == "starting"`
- `team`, `opponent`, `game_time`: `null` when `status` is `no_game` or `not_found`

## Response: 400 Bad Request

Returned when `player` parameter is missing or `date` is not a valid `YYYY-MM-DD` string.

```json
{"detail": "player query parameter is required"}
```

## Response: 403 Forbidden

```json
{"detail": "Not authenticated"}
```

## Example Requests

```bash
# Check today's lineup
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/lineup?player=Jarren+Duran"

# Check a specific date
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/lineup?player=Jarren+Duran&date=2026-06-24"
```
