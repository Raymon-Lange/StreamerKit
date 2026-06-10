from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.cache_retention import RETENTION
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


def _ts_str(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%b %d %H:%M")
    except Exception:
        return ts


def _latest_entry(cache_key: str) -> tuple[dict | None, float | None]:
    """Return (payload, age_seconds) for the most recent entry matching cache_key as prefix."""
    keys = _cache.list_keys("collector")
    matches = [(k, ts) for k, ts in keys if k.startswith(cache_key)]
    if not matches:
        return None, None
    best_key, cached_at = max(matches, key=lambda x: x[1])
    payload = _cache.get_stale("collector", best_key)
    return payload, time.time() - cached_at


def run() -> int:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(_DIVIDER)
    print(f"Feed Health · {now_str}")
    print(_DIVIDER)

    failure_records: dict[str, dict] = {}
    for key, _ in _cache.list_keys("feed_failures"):
        rec = _cache.get_stale("feed_failures", key)
        if rec:
            failure_records[rec.get("collector", key)] = rec

    print()
    for cache_key, ttl in RETENTION.items():
        payload, age_s = _latest_entry(cache_key)

        if age_s is None:
            status = "✗ MISSING"
            age_detail = "no cache entry"
        elif ttl is not None and age_s > ttl:
            status = "! STALE  "
            age_detail = f"cached {_age_str(age_s)}  TTL: {_ttl_str(ttl)}"
        else:
            status = "✓ FRESH  "
            age_detail = f"cached {_age_str(age_s)}  TTL: {_ttl_str(ttl)}"

        print(f"  {status}  {cache_key}")
        print(f"           {age_detail}")

        if payload:
            url = payload.get("url")
            fetched_at = payload.get("fetched_at")
            if url:
                print(f"           url: {url}")
            if fetched_at:
                print(f"           fetched: {_ts_str(fetched_at)}")

        failure = failure_records.get(cache_key)
        if failure:
            ts = _ts_str(failure.get("timestamp", ""))
            err = f"{failure.get('error_type', '?')}: {failure.get('error_message', '')}"
            print(f"           ! last error {ts} — {err}")

        print()

    failure_keys = _cache.list_keys("feed_failures")
    uncorrelated = [
        rec for key, _ in failure_keys
        if (rec := _cache.get_stale("feed_failures", key))
        and rec.get("collector") not in RETENTION
    ]
    if uncorrelated:
        print("Other feed failures:")
        print()
        for rec in uncorrelated:
            ts = _ts_str(rec.get("timestamp", ""))
            err = f"{rec.get('error_type', '?')}: {rec.get('error_message', '')}"
            print(f"  {rec.get('collector', '?')} | {rec.get('operation', '')}")
            print(f"    {ts} — {err}")
            print()

    print(_DIVIDER)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show cache freshness, source URLs, and feed failure status.")
    parser.parse_args()
    raise SystemExit(run())


if __name__ == "__main__":
    main()
