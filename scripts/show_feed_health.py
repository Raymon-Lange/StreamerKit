from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.feed_health_service import build_snapshot

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


def _ts_str(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%b %d %H:%M")
    except Exception:
        return ts


def run() -> int:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(_DIVIDER)
    print(f"Feed Health · {now_str}")
    print(_DIVIDER)

    snapshot = build_snapshot()

    print()
    for src in snapshot.sources:
        if src.status == "missing":
            status = "✗ MISSING"
            age_detail = "no cache entry"
        elif src.status == "stale":
            status = "! STALE  "
            age_detail = f"cached {_age_str(src.age_seconds)}  TTL: {_ttl_str(src.ttl_seconds)}"
        else:
            status = "✓ FRESH  "
            age_detail = f"cached {_age_str(src.age_seconds)}  TTL: {_ttl_str(src.ttl_seconds)}"

        print(f"  {status}  {src.key}")
        print(f"           {age_detail}")

        if src.last_url:
            print(f"           url: {src.last_url}")
        if src.fetched_at:
            print(f"           fetched: {_ts_str(src.fetched_at)}")
        if src.last_error_type:
            err = f"{src.last_error_type}: {src.last_error_message or ''}"
            print(f"           ! last error {_ts_str(src.last_error_at)} — {err}")

        print()

    print(_DIVIDER)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show cache freshness, source URLs, and feed failure status.")
    parser.parse_args()
    raise SystemExit(run())


if __name__ == "__main__":
    main()
