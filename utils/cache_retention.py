from __future__ import annotations

from typing import Optional

# Maps cache keys to their TTL in seconds. None = permanent (no expiry).
# To adjust any collector's retention period, edit this file only.
RETENTION: dict[str, Optional[float]] = {
    "espn_dynasty_top300":          15 * 86_400,   # 15 days
    "espn_points_top300":           15 * 86_400,   # 15 days
    "pitcherlist_top_hitters":      15 * 86_400,   # 15 days
    "pitcherlist_dynasty_hitters":  15 * 86_400,   # 15 days
    "espn_keeper_cost":             None,           # permanent — league draft data
    "espn_daily_notes":             86_400,         # 1 day — keyed by date
}


def ttl_for(key: str) -> Optional[float]:
    """Return TTL seconds for a collector cache key.

    Dynamic-suffix keys (e.g. 'espn_keeper_cost_42_2026') match by prefix.
    Raises KeyError for unknown keys so mis-spellings surface immediately.
    """
    if key in RETENTION:
        return RETENTION[key]
    for prefix, ttl in RETENTION.items():
        if key.startswith(prefix):
            return ttl
    raise KeyError(f"No retention configured for cache key: {key!r}")
