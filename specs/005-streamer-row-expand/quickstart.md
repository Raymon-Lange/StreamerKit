# Quickstart: Verifying Expandable Streamer Rows

## Start the dev server

```bash
docker compose -f docker-compose.dev.yml up
# Web UI at http://localhost:9472
```

## Test expand / collapse

1. Open the SP Streamers card (Today or Tomorrow).
2. Confirm each pitcher row shows a chevron indicator on the right.
3. **Click any row** → the row expands below the compact summary showing:
   - Season record
   - Last 10 starts record
   - Last 2 starts detail
   - Opponent team and difficulty score
   - Chevron rotates to indicate open state
4. **Click the same row again** → it collapses; chevron returns to closed state.
5. **Click a second row while first is open** → second row expands, first collapses automatically.

## Test null / missing data

6. Find a pitcher with `null` opponent data (e.g., a pitcher not starting today appearing via PitcherList rank only).
7. Expand their row → null fields should show `—`, not blank or "undefined".

## Test mobile layout

8. Resize browser to 375px width.
9. Expand a row → expanded content should be fully readable with no horizontal overflow.

## Regression check

10. Compact view (collapsed rows) should look identical to before — no layout shift, no extra padding.
11. Both "SP Streamers · Today" and "Tomorrow's SP Streamers" cards should both support expand/collapse.
