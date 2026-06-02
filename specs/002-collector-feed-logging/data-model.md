# Data Model: Collector Feed Logging

## FeedLogEntry

Represents a single external data-fetch event. Internal to `utils/feed_logger.py` — not shared across module boundaries, so it does not belong in `models/player.py`.

| Field | Type | Description |
|-------|------|-------------|
| `collector` | `str` | Name of the collector module (e.g., `"pitcherlist"`, `"mlb_stats"`, `"espn"`) |
| `operation` | `str` | Name of the specific fetch operation (e.g., `"scrape_top_hitters"`, `"get_probable_starters"`) |
| `outcome` | `Literal["success", "error", "cache-fallback"]` | Result of the fetch attempt |
| `duration_s` | `float` | Wall-clock duration in seconds, measured from context entry to exit |
| `timestamp` | `datetime` | UTC timestamp when the context manager was entered (fetch started) |
| `error_type` | `str \| None` | Exception class name if `outcome == "error"`, else `None` |
| `error_message` | `str \| None` | Exception message if `outcome == "error"`, else `None` |
| `triggered_by` | `str \| None` | Filename from `sys.argv[0]` at log time, or `None` if unavailable |

**Validation rules**:
- `collector` and `operation` are non-empty strings.
- `duration_s` is non-negative.
- `error_type` and `error_message` are only populated when `outcome == "error"`.
- `triggered_by` is the basename only (no directory path).

## FeedLogContext (context manager handle)

The object yielded by `log_feed_fetch(...)`. Callers interact with it only to signal cache fallback.

| Method | Description |
|--------|-------------|
| `mark_cache_fallback()` | Sets `outcome` to `"cache-fallback"` for the current entry. Must be called before the `with` block exits. |

## Outcome States

```
[fetch starts]
      │
      ├─► mark_cache_fallback() called ──► "cache-fallback"
      │
      ├─► exception raised ───────────────► "error"
      │
      └─► block exits normally ───────────► "success"
```

## Log Line Format

```
[FEED] {ISO8601 UTC timestamp} | {collector} | {operation} | {outcome} | {duration:.2f}s[ | {error_type}: {error_message}]
```

**Examples**:
```
[FEED] 2026-06-02T07:12:01Z | pitcherlist | scrape_top_hitters | success | 1.43s
[FEED] 2026-06-02T07:12:03Z | pitcherlist | scrape_dynasty_hitters | cache-fallback | 0.00s
[FEED] 2026-06-02T07:12:05Z | mlb_stats | get_probable_starters | error | 0.31s | ConnectionError: timed out
[FEED] 2026-06-02T07:12:07Z | espn | fetch_roster | success | 0.87s
```
