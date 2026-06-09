from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from models.player import RankingEntry
from utils.cache_retention import ttl_for
from utils.cache_store import store as _cache
from utils.feed_logger import log_feed_fetch
from utils.names import normalize_name

ESPN_DYNASTY_URL = (
    "https://www.espn.com/fantasy/baseball/story/_/id/29312971/"
    "fantasy-baseball-dynasty-rankings-top-300-players-2026-beyond"
)
_CACHE_NS = "collector"
_CACHE_KEY = "espn_dynasty_top300"
TABLE_CAPTION = "top 300 dynasty league rankings"


@dataclass(slots=True)
class ArticleMeta:
    url: str
    title: str | None = None
    date_text: str | None = None


def fetch_html(url: str = ESPN_DYNASTY_URL, timeout: int = 20) -> str:
    resp = requests.get(url, headers={"User-Agent": "curl/8.5.0"}, timeout=timeout)
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


def scrape_espn_dynasty_hitters(url: str = ESPN_DYNASTY_URL, force_refresh: bool = False) -> dict[str, RankingEntry]:
    _ttl = ttl_for(_CACHE_KEY)
    stale = _cache.get_stale(_CACHE_NS, _CACHE_KEY)
    fresh = None if force_refresh else _cache.get(_CACHE_NS, _CACHE_KEY, ttl_seconds=_ttl)

    with log_feed_fetch("espn_dynasty", "scrape_espn_dynasty_hitters") as feed_log:
        if fresh is not None:
            feed_log.mark_cache_fallback()
            return _deserialize_rankings(fresh.get("rows", []))

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

            payload = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "url": url,
                "rows": _serialize_rankings(ranked),
            }
            _cache.set(_CACHE_NS, _CACHE_KEY, payload, ttl_seconds=_ttl)
            return ranked
        except Exception:
            if stale:
                feed_log.mark_cache_fallback()
                return _deserialize_rankings(stale.get("rows", []))
            return {}
