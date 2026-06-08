from __future__ import annotations

import argparse
from pathlib import Path
import sys
from utils.feed_logger import log_script_run

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.cache_store import store as _cache

_RANKING_KEYS = [
    ("ESPN Points Top 300",          "espn_points_top300"),
    ("ESPN Dynasty Top 300",         "espn_dynasty_top300"),
    ("Pitcher List Top Hitters",     "pitcherlist_top_hitters"),
    ("Pitcher List Dynasty Hitters", "pitcherlist_dynasty_hitters"),
]


def _collect_article_dates(rows: list[dict]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for row in rows:
        value = row.get("article_date")
        if not value:
            continue
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered


def run(show_missing: bool = False) -> int:
    with log_script_run("show_ranking_page_sources.py"):
        divider = "-" * 110
        print(divider)
        print("Ranking Page Source Summary")
        print(divider)

        any_printed = False
        for label, key in _RANKING_KEYS:
            payload = _cache.get_stale("collector", key)
            if payload is None:
                if show_missing:
                    print(f"{label}: not found in cache (key={key!r})")
                continue

            fetched_at = payload.get("fetched_at") or "N/A"
            source_url = payload.get("url") or "N/A"
            rows = payload.get("rows", [])
            article_dates = _collect_article_dates(rows if isinstance(rows, list) else [])
            article_date_text = ", ".join(article_dates) if article_dates else "N/A"

            print(f"\n[{label}]")
            print(f"cache_key:  {key}")
            print(f"fetched_at: {fetched_at}")
            print(f"source_url: {source_url}")
            print(f"article_date(s): {article_date_text}")
            any_printed = True

        if not any_printed:
            print("No ranking cache entries were found.")
            return 1

        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show source URLs and article dates for cached ranking pages.")
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="Also print cache files that are missing or unreadable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(run(show_missing=args.show_missing))


if __name__ == "__main__":
    main()
