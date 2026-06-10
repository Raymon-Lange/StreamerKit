# API Contract: GET /api/feed-status

## Endpoint

`GET /api/feed-status`

**Authentication**: `X-API-Key` header required (same as all `/api/*` routes)

**Parameters**: None

**Caching**: Not cached via `response_cache` — always returns a live snapshot from the cache store. The cache store reads are cheap (SQLite queries).

---

## Response: 200 OK

```json
{
  "generated_at": "2026-06-10T14:32:01Z",
  "sources": [
    {
      "key": "espn_dynasty_top300",
      "status": "fresh",
      "age_seconds": 43200,
      "ttl_seconds": 1296000,
      "last_url": null,
      "fetched_at": "2026-06-10T02:15:00Z",
      "last_error_type": null,
      "last_error_message": null,
      "last_error_at": null
    },
    {
      "key": "pitcherlist_top_hitters",
      "status": "stale",
      "age_seconds": 1400000,
      "ttl_seconds": 1296000,
      "last_url": "https://pitcherlist.com/...",
      "fetched_at": "2026-05-25T10:00:00Z",
      "last_error_type": "HTTPError",
      "last_error_message": "503 Service Unavailable",
      "last_error_at": "2026-06-09T22:00:00Z"
    },
    {
      "key": "espn_keeper_cost",
      "status": "fresh",
      "age_seconds": 864000,
      "ttl_seconds": null,
      "last_url": null,
      "fetched_at": null,
      "last_error_type": null,
      "last_error_message": null,
      "last_error_at": null
    }
  ],
  "response_cache": [
    {
      "key": "streamers_2026-06-10_all",
      "age_seconds": 120,
      "ttl_seconds": 300,
      "remaining_seconds": 180
    },
    {
      "key": "optimizer",
      "age_seconds": 900,
      "ttl_seconds": 1800,
      "remaining_seconds": 900
    }
  ]
}
```

---

## Response: 401 Unauthorized

Missing or invalid API key — same response as all other protected routes.

---

## Field Notes

- `sources` order matches the definition order of `utils/cache_retention.RETENTION`.
- `ttl_seconds: null` means the entry is permanent (no expiry) — shown as "permanent" in the UI.
- `response_cache` is empty array `[]` when no non-expired entries exist.
- All timestamps are ISO 8601 UTC strings.
- `age_seconds` and `ttl_seconds` are floating-point seconds.

---

## Frontend API Client Addition

```typescript
// In frontend/src/api.ts
feedStatus: () => apiFetch('/api/feed-status'),
```
