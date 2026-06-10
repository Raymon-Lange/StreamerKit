# Data Model: Data Source Status Page

All types live in `models/feed_health.py` as `@dataclass(slots=True)` value objects.

## FeedSource

Represents the health snapshot for one tracked collector data source.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Cache key / collector identifier (e.g. `pitcherlist_top_hitters`) |
| `status` | `str` | One of `"fresh"`, `"stale"`, `"missing"` |
| `age_seconds` | `float \| None` | Seconds since last successful cache write; `None` if missing |
| `ttl_seconds` | `float \| None` | Configured TTL; `None` if permanent |
| `last_url` | `str \| None` | Source URL from cached payload; `None` if unavailable |
| `fetched_at` | `str \| None` | ISO timestamp from cached payload; `None` if unavailable |
| `last_error_type` | `str \| None` | Error type from most recent failure record; `None` if no failure |
| `last_error_message` | `str \| None` | Error message from most recent failure record; `None` if no failure |
| `last_error_at` | `str \| None` | ISO timestamp of most recent failure; `None` if no failure |

**Status rules**:
- `"missing"` — no cache entry exists (`age_seconds is None`)
- `"stale"` — entry exists and `ttl_seconds is not None` and `age_seconds > ttl_seconds`
- `"fresh"` — entry exists and (ttl is None or age within TTL)

---

## CacheEntry

Represents one non-expired entry in the short-lived API response cache.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Cache key (e.g. `streamers_2026-06-10_all`) |
| `age_seconds` | `float` | Seconds since the entry was written |
| `ttl_seconds` | `float` | The TTL this entry was stored with |
| `remaining_seconds` | `float` | `ttl_seconds - age_seconds` (always > 0 for non-expired entries) |

**Inclusion rule**: Only entries where `age_seconds < ttl_seconds` are included. Expired entries are excluded.

---

## FeedHealthSnapshot

Top-level response payload returned by `GET /api/feed-status`.

| Field | Type | Description |
|-------|------|-------------|
| `generated_at` | `str` | ISO 8601 UTC timestamp when the snapshot was built |
| `sources` | `list[FeedSource]` | One entry per key in `utils/cache_retention.RETENTION`, in definition order |
| `response_cache` | `list[CacheEntry]` | All non-expired entries in the `response` namespace, sorted by age ascending |

---

## Serialisation

The route converts `FeedHealthSnapshot` to a plain dict for JSON serialisation using `dataclasses.asdict()`. No ORM mapping; no database writes. This feature is entirely read-only.
