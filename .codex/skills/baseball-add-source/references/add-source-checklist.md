# Add Source Checklist

Use this checklist for every new source integration.

## Collector checklist

- Add `collectors/<source>.py`.
- Parse source rows into `RankingEntry` or other shared model shapes.
- Normalize player names with `normalize_name`.
- Return dictionary keyed by normalized name.

## Cache checklist

- Cache path: `.cache/<source>_<dataset>.json`.
- TTL: 15 days based on file modified time.
- If cache is fresh, return cached rows and skip network.
- If refresh fails, fall back to cached rows when available.

## Cache payload shape

```json
{
  "fetched_at": "2026-03-31T00:00:00+00:00",
  "url": "https://example.com/source",
  "rows": [
    {
      "normalized_name": "player name",
      "source": "source_name",
      "rank": 123,
      "tier": null,
      "article_url": "https://example.com/source",
      "article_title": "Source Title",
      "article_date": "March 30, 2026",
      "position": null,
      "raw": "Raw row text"
    }
  ]
}
```

## Script integration checklist

- Import new collector in target script.
- Read source data once per run.
- Compute merged rank explicitly (for example, `min(valid_ranks)`).
- Print merged rank plus per-source rank values.

## Validation checklist

- `python3 -m py_compile` on changed collector and scripts.
- Run affected script path if environment is configured.
- Update `README.md` source list and cache section.
