from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from models.player import RankingEntry
from utils.names import normalize_name

ESPN_DYNASTY_URL = (
    "https://www.espn.com/fantasy/baseball/story/_/id/29312971/"
    "fantasy-baseball-dynasty-rankings-top-300-players-2026-beyond"
)
CACHE_PATH = Path(__file__).resolve().parents[1] / ".cache" / "espn_dynasty_top300.json"
CACHE_TTL = timedelta(days=15)
TABLE_CAPTION = "top 300 dynasty league rankings"


@dataclass(slots=True)
class ArticleMeta:
    url: str
    title: str | None = None
    date_text: str | None = None


def fetch_html(url: str = ESPN_DYNASTY_URL, timeout: int = 20) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_article_meta(soup: BeautifulSoup, fallback_url: str) -> ArticleMeta:
    title = soup.title.get_text(" ", strip=True) if soup.title else None

    date_text = None
    time_node = soup.find("time")
    if time_node:
        date_text = time_node.get_text(" ", strip=True) or time_node.get("datetime")

    return ArticleMeta(url=fallback_url, title=title, date_text=date_text)


def _normalize_header(text: str) -> str:
    compact = " ".join(text.split()).lower()
    compact = compact.replace(". ", ".")
    compact = compact.replace(" ?", "?")
    return compact


def _table_text(cell) -> str:
    return " ".join(cell.get_text(" ", strip=True).split())


def _find_dynasty_table(soup: BeautifulSoup):
    for caption in soup.find_all(["h2", "h3"]):
        if TABLE_CAPTION in caption.get_text(" ", strip=True).lower():
            table = caption.find_next("table")
            if table is not None:
                return table

    # Fallback: choose the largest table that looks like rank/player data.
    best_table = None
    best_rows = 0
    for table in soup.find_all("table"):
        headers = [_normalize_header(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        has_rank = any("rank" in header for header in headers)
        has_player = any("player" in header for header in headers)
        if not (has_rank and has_player):
            continue
        row_count = len(table.find_all("tr"))
        if row_count > best_rows:
            best_rows = row_count
            best_table = table
    if best_table is not None:
        return best_table
    return None


def _parse_table(table, meta: ArticleMeta, source: str = "espn_dynasty") -> dict[str, RankingEntry]:
    headers = [_normalize_header(th.get_text(" ", strip=True)) for th in table.find_all("th")]
    if not headers:
        return {}

    idx_rank = next((i for i, header in enumerate(headers) if "rank" in header), None)
    idx_player = next((i for i, header in enumerate(headers) if "player" in header), None)
    if idx_rank is None or idx_player is None:
        return {}

    ranked: dict[str, RankingEntry] = {}
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        if len(cells) <= max(idx_rank, idx_player):
            continue

        rank_text = _table_text(cells[idx_rank])
        match = re.search(r"\d{1,3}", rank_text)
        if not match:
            continue
        rank = int(match.group())

        name = _table_text(cells[idx_player])
        if not name:
            continue

        key = normalize_name(name)
        ranked.setdefault(
            key,
            RankingEntry(
                source=source,
                rank=rank,
                article_url=meta.url,
                article_title=meta.title,
                article_date=meta.date_text,
                raw=tr.get_text(" ", strip=True),
            ),
        )
    return ranked


def _is_cache_fresh() -> bool:
    if not CACHE_PATH.exists():
        return False
    modified_at = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    return now - modified_at <= CACHE_TTL


def _load_cache() -> dict | None:
    if not CACHE_PATH.exists():
        return None
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _serialize_rankings(ranked: dict[str, RankingEntry]) -> list[dict]:
    rows = []
    for key, entry in ranked.items():
        rows.append(
            {
                "normalized_name": key,
                "source": entry.source,
                "rank": entry.rank,
                "tier": entry.tier,
                "article_url": entry.article_url,
                "article_title": entry.article_title,
                "article_date": entry.article_date,
                "position": entry.position,
                "raw": entry.raw,
            }
        )
    return rows


def _deserialize_rankings(rows: list[dict]) -> dict[str, RankingEntry]:
    ranked: dict[str, RankingEntry] = {}
    for row in rows:
        key = row.get("normalized_name")
        if not key:
            continue
        ranked[key] = RankingEntry(
            source=row.get("source", "espn_dynasty"),
            rank=row.get("rank"),
            tier=row.get("tier"),
            article_url=row.get("article_url"),
            article_title=row.get("article_title"),
            article_date=row.get("article_date"),
            position=row.get("position"),
            raw=row.get("raw"),
        )
    return ranked


def _save_cache(url: str, ranked: dict[str, RankingEntry]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "rows": _serialize_rankings(ranked),
    }
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def scrape_espn_dynasty_hitters(url: str = ESPN_DYNASTY_URL, force_refresh: bool = False) -> dict[str, RankingEntry]:
    cached = _load_cache()
    if cached and not force_refresh and _is_cache_fresh():
        return _deserialize_rankings(cached.get("rows", []))

    try:
        html = fetch_html(url=url)
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_article_meta(soup, url)
        table = _find_dynasty_table(soup)
        if table is None:
            raise ValueError("Could not find 'Top 300 dynasty league rankings' table.")

        ranked = _parse_table(table, meta=meta)
        if not ranked:
            raise ValueError("No ESPN dynasty rows were parsed from the table.")

        _save_cache(url, ranked)
        return ranked
    except Exception:
        if cached:
            return _deserialize_rankings(cached.get("rows", []))
        raise
