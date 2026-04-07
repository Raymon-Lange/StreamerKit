# API Documentation

## Base URL

`http://127.0.0.1:8000`

## Auth

If `API_KEY` is set on the server, send header:

`x-api-key: <API_KEY>`

If `API_KEY` is not set, routes are open.

## Interactive Docs

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Endpoints

### GET `/health`
Health check.

### GET `/waivers/recent-drops`
Recent dropped-player waiver review.

Parameters:
- `days` (default `2`)
- `trend_games` (default `10`)
- `top` (default `25`)
- `claim_mode` (`all` or `wins`, default `all`)
- `league_id` (optional override)
- `year` (optional override)

Behavior:
- Filters out `PASS`, `SKIP`, and pitcher `Not Ranked`.
- In `wins` mode, returns only `WIN-NOW ADD` and `MUST ADD`.
- Adds `suggested_drop` for win-now hitter targets when safe roster coverage allows it.

### GET `/hitters/free-agents`
Free-agent hitter recommendations.

Parameters:
- `top` (default `10`)
- `size` (default `75`)
- `trend_games` (default `15`)
- `trend_workers` (default `12`)
- `league_id` (optional override)
- `year` (optional override)

### GET `/pitchers/streamers`
Streaming pitcher review.

Parameters:
- `pitcher` (optional single-player lookup)
- `league_id` (optional override)
- `year` (optional override)

Behavior:
- No `pitcher`: returns the full streamers list.
- With `pitcher`: returns exact/close-match lookup payload.

### GET `/pitchers/team-eval`
Team pitcher evaluation based on roster-only pitchers.

Parameters:
- `team_id` (optional override)
- `league_id` (optional override)
- `year` (optional override)

Behavior:
- Ranks roster pitchers by:
  - ERA rank (lower better)
  - Strikeout rank (higher better)
  - Keeper-cost rank using projected keeper pick from draft history (lower better)

### GET `/pitchers/start-eval`
Daily pitcher start evaluation for your roster.

Parameters:
- `team_id` (optional override)
- `league_id` (optional override)
- `year` (optional override)
- `tomorrow` (default `false`)

Behavior:
- Evaluates roster pitchers who are probable starters for the selected date.
- Recommends the top 2 pitchers to start using streaming-tier recommendation scores.
- Includes bench probable starters and suggested bench-to-active moves.
- If no roster probable starters are found, falls back to top streaming pitchers for that same date.

## Run Locally

```bash
uvicorn app.main:app --reload
```
