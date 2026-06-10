from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.cache_retention import RETENTION, ttl_for
from utils.cache_store import store as _cache

_DIVIDER = "─" * 80


def _age_str(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86_400:
        return f"{seconds / 3600:.1f}h ago"
    return f"{seconds / 86_400:.1f}d ago"


def _ttl_str(ttl: float | None) -> str:
    if ttl is None:
        return "permanent"
    days = ttl / 86_400
    if days >= 1:
        return f"{days:.0f}d"
    return f"{ttl / 3600:.0f}h"


def _ts_local(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        local = dt.astimezone()
        return local.strftime("%b %d %H:%M")
    except Exception:
        return ts_str


def _cache_age_seconds(namespace: str, key_or_prefix: str, by_prefix: bool) -> float | None:
    """Return age in seconds of the most recent cache entry, or None if missing."""
    keys = _cache.list_keys(namespace)
    if by_prefix:
        matches = [(k, ts) for k, ts in keys if k.startswith(key_or_prefix)]
    else:
        matches = [(k, ts) for k, ts in keys if k == key_or_prefix]
    if not matches:
        return None
    _, cached_at = max(matches, key=lambda x: x[1])
    return time.time() - cached_at


def run() -> int:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(_DIVIDER)
    print(f"Feed Health Report · {now_str}")
    print(_DIVIDER)

    # ── Cache health per known collector ──────────────────────────────────────
    print()
    col_w = max(len(k) for k in RETENTION) + 2

    for cache_key, ttl in RETENTION.items():
        age_s = _cache_age_seconds("collector", cache_key, by_prefix=True)

        if age_s is None:
            status = "✗ MISSING"
            detail = "no cache entry"
        elif ttl is not None and age_s > ttl:
            status = "! STALE  "
            detail = f"cached {_age_str(age_s)}  TTL: {_ttl_str(ttl)}"
        else:
            status = "✓ FRESH  "
            detail = f"cached {_age_str(age_s)}  TTL: {_ttl_str(ttl)}"

        print(f"  {cache_key:{col_w}}  {status}  {detail}")

    # ── Recorded feed failures ────────────────────────────────────────────────
    failure_keys = _cache.list_keys("feed_failures")
    if failure_keys:
        print()
        print("Recent feed failures:")
        print()
        for key, _ in failure_keys:
            rec = _cache.get_stale("feed_failures", key)
            if not rec:
                continue
            ts = _ts_local(rec.get("timestamp", ""))
            err_type = rec.get("error_type", "?")
            err_msg = rec.get("error_message", "")
            triggered = rec.get("triggered_by", "?")
            label = f"  {rec.get('collector', key)} | {rec.get('operation', '')}"
            print(f"{label}")
            print(f"    {ts}  {err_type}: {err_msg}")
            print(f"    triggered by: {triggered}")
    else:
        print()
        print("  No feed failures recorded.")

    print()
    print(_DIVIDER)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show cache freshness and feed failure status.")
    parser.parse_args()
    raise SystemExit(run())


if __name__ == "__main__":
    main()
