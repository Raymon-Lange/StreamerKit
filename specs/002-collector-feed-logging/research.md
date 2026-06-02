# Research: Collector Feed Logging

**Phase 0 — resolves all unknowns before design**

## Decision 1: Instrumentation Pattern

**Decision**: Context manager (`with log_feed_fetch(collector, operation):`)

**Rationale**: A context manager cleanly brackets the call site, measures wall-clock time via `__enter__`/`__exit__`, catches exceptions without modifying the caller's control flow, and requires only 1 added line (the `with` statement) plus the existing call. A decorator would require wrapping free functions that are not methods, breaking the caller's signature visibility. Manual `start = time.monotonic()` / `log(...)` pairs require 3–4 lines and are easy to forget on error paths. The context manager handles all three outcomes (success, error, cache-fallback) in one place.

**Alternatives considered**:
- Decorator: cleaner at the definition site but harder to retrofit to private helpers and does not support "cache-fallback" as a distinct outcome.
- Manual timing: most flexible, but verbose and error-prone at every call site.

---

## Decision 2: Output Format

**Decision**: Human-readable single-line format to `stderr` via Python's `logging` module at `INFO` level.

Format: `[FEED] {timestamp} | {collector} | {operation} | {outcome} | {duration:.2f}s[ | {error}]`

Example lines:
```
[FEED] 2026-06-02T07:12:01Z | pitcherlist | scrape_top_hitters | success | 1.43s
[FEED] 2026-06-02T07:12:03Z | pitcherlist | scrape_dynasty_hitters | cache-fallback | 0.00s
[FEED] 2026-06-02T07:12:05Z | mlb_stats | get_probable_starters | error | 0.31s | ConnectionError: timed out
```

**Rationale**: Human-readable lines are immediately scannable in a terminal without a log parser. Python's built-in `logging` module routes to `stderr` by default, keeps it off stdout (which scripts use for results), and supports filtering by level. No new dependency required.

**Alternatives considered**:
- Structured JSON lines: useful for log aggregation pipelines, but this is a local CLI tool — no aggregation pipeline exists.
- Rich/colorlog: adds a dependency; not warranted for the use case.

---

## Decision 3: Triggering Script Detection

**Decision**: Capture `sys.argv[0]` at the time the log entry is written, trimmed to the filename only.

**Rationale**: `sys.argv[0]` is always available in the standard library and accurately reflects which script launched the process. Trimming to filename (e.g., `run_sp_streamers.py`) avoids leaking absolute paths. No thread-local or global context object needed.

**Alternatives considered**:
- Stack frame inspection: fragile, slow, and overly complex.
- Explicit `caller=` argument at call site: requires callers to pass context — violates FR-006 (single shared utility, no per-caller boilerplate).

---

## Decision 4: Cache-Fallback Signalling

**Decision**: The context manager exposes a `mark_cache_fallback()` method on the returned context object so callers can signal a cache hit without raising an exception.

Usage:
```python
with log_feed_fetch("pitcherlist", "scrape_top_hitters") as feed_log:
    if cached and _is_cache_fresh(path):
        feed_log.mark_cache_fallback()
        return _deserialize_rankings(cached["rows"])
    ...
```

**Rationale**: Cache fallback is not an error — it is a normal, desirable outcome. Signalling it via a return-path flag on the context object keeps the distinction clean without requiring two separate context managers or a return value from the `with` block.

**Alternatives considered**:
- A separate `with log_cache_hit(...)` context manager: would require callers to know upfront whether they'd hit the cache, which is often only determined mid-function.
- A raised sentinel exception: semantically wrong (not an error).

---

## Decision 5: Credential Redaction

**Decision**: The logger does not inspect or log any arguments passed to collector functions. It logs only collector name, operation name, outcome, duration, and exception type+message. Exception messages that happen to contain credentials are not redacted — the existing constitution rule (Principle III) prohibits collectors from logging credentials in the first place.

**Rationale**: No credential values flow through the logger; they are only in `AppConfig` and ESPN API call arguments. The logger never sees those values.

---

## Summary Table

| Unknown | Decision | Rationale |
|---------|----------|-----------|
| Instrumentation pattern | Context manager | Minimal code, handles all outcomes |
| Output format | `logging` to stderr, human-readable | No new deps, no stdout pollution |
| Triggering script | `sys.argv[0]` trimmed to filename | Always available, no boilerplate |
| Cache-fallback signal | `.mark_cache_fallback()` on context | Explicit, no exception abuse |
| Credential redaction | Logger never sees credentials | Already enforced by constitution |
