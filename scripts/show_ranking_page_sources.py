from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))


REPO_ROOT = Path(__file__).resolve().parents[1]

RANKING_CACHE_FILES = [
    ("ESPN Points Top 300", REPO_ROOT / ".cache" / "espn_points_top300_2026.json"),
    ("ESPN Dynasty Top 300", REPO_ROOT / ".cache" / "espn_dynasty_top300.json"),
    ("Pitcher List Top Hitters", REPO_ROOT / ".cache" / "pitcherlist_top_hitters.json"),
    ("Pitcher List Dynasty Hitters", REPO_ROOT / ".cache" / "pitcherlist_dynasty_hitters.json"),
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


def _read_payload(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def run(show_missing: bool = False) -> int:
    divider = "-" * 110
    print(divider)
    print("Ranking Page Source Summary")
    print(divider)

    any_printed = False
    for label, path in RANKING_CACHE_FILES:
        payload = _read_payload(path)
        if payload is None:
            if show_missing:
                print(f"{label}: cache missing/unreadable at {path}")
            continue

        fetched_at = payload.get("fetched_at") or "N/A"
        source_url = payload.get("url") or "N/A"
        rows = payload.get("rows", [])
        article_dates = _collect_article_dates(rows if isinstance(rows, list) else [])
        article_date_text = ", ".join(article_dates) if article_dates else "N/A"

        print(f"\n[{label}]")
        print(f"cache_file: {path}")
        print(f"fetched_at: {fetched_at}")
        print(f"source_url: {source_url}")
        print(f"article_date(s): {article_date_text}")
        any_printed = True

    if not any_printed:
        print("No ranking cache files were found.")
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
