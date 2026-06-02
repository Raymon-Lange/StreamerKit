# Contract: utils/feed_logger — Public API

This document defines the public interface of `utils/feed_logger.py`. Consumers are collector modules in `collectors/`. Nothing outside `collectors/` is expected to call this API directly.

## `log_feed_fetch(collector, operation)`

A context manager that wraps a single external data-fetch call.

**Signature** (intent, not implementation):

```
log_feed_fetch(collector: str, operation: str) -> FeedLogContext
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `collector` | `str` | Short name of the collector (e.g., `"pitcherlist"`, `"mlb_stats"`, `"espn"`) |
| `operation` | `str` | Name of the specific fetch being performed (e.g., `"scrape_top_hitters"`) |

**Yields**: A `FeedLogContext` object with one method:
- `mark_cache_fallback()` — call this before returning cached data to log the outcome as `"cache-fallback"` instead of `"success"`.

**Guarantees**:
- Never raises. If the logging mechanism itself fails, the failure is silently suppressed and the caller's code continues normally.
- Exceptions raised inside the `with` block propagate to the caller unchanged — the logger records them but does not swallow them.
- Output goes to `stderr` only, never `stdout`.

## Usage Pattern

### Fresh fetch (success or error)

```python
with log_feed_fetch("pitcherlist", "scrape_top_hitters"):
    soup = fetch_html(url)
    ranked = _parse_ranked_table(...)
    _save_cache(...)
    return ranked
```

### Cache-fallback path

```python
with log_feed_fetch("pitcherlist", "scrape_top_hitters") as feed_log:
    if cached and _is_cache_fresh(path):
        feed_log.mark_cache_fallback()
        return _deserialize_rankings(cached["rows"])
    # ... live fetch follows
```

## Non-goals

- Does not accept structured metadata beyond collector and operation names.
- Does not write to files, databases, or external services.
- Does not provide a query or retrieval API.
- Does not filter or suppress log output based on runtime configuration.
