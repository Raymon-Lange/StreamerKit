# Quickstart: Tomorrow's SP Streamer Card

**Feature**: 001-tomorrow-sp-streamer-card

## Prerequisites

- `.env` file present with `LEAGUE_ID`, `TEAM_ID`, `ESPN_S2`, `ESPN_SWID`, `API_KEY`
- Docker and docker compose available

## Run the dev stack

```bash
docker compose -f docker-compose.dev.yml up
```

- API: http://localhost:9471
- Dashboard: http://localhost:9472

## Verify the feature

1. Open http://localhost:9472 in a browser.
2. Confirm a "Tomorrow's SP Streamers" card appears in the dashboard grid alongside the
   existing "SP Streamers" card.
3. The tomorrow card should list up to 8 pitchers with tier labels colored consistently
   with the today card (green = Must Stream, blue = Strong Stream, etc.).
4. If no probable starters are scheduled for tomorrow, the card shows "No streamers tomorrow."

## Verify the API directly

```bash
curl -H "X-API-Key: $API_KEY" "http://localhost:9471/api/streamers?tomorrow=true"
```

Expected: `{ "rows": [...] }` — may be empty `{ "rows": [] }` if no games tomorrow.

## Test error state

Stop the dev stack API container while keeping the frontend running, then refresh — the
tomorrow card should display an inline error without crashing other cards.
