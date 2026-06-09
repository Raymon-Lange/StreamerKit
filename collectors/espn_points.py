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
from utils.names import clean_player_name, normalize_name

ESPN_POINTS_TOP300_URL = (
    "https://www.espn.com/fantasy/baseball/story/_/id/35437997/"
    "fantasy-baseball-rankings-points-leagues-2026-espn-cockcroft"
)
_CACHE_NS = "collector"
_CACHE_KEY = "espn_points_top300"
TOP300_HEADING = "Top 300 Rankings for 2026"


@dataclass(slots=True)
class ArticleMeta:
    url: str
    title: str | None = None
    date_text: str | None = None


def fetch_html(url: str = ESPN_POINTS_TOP300_URL, timeout: int = 20) -> str:
    response = requests.get(url, headers={"User-Agent": "curl/8.5.0"}, timeout=timeout)
    response.raise_for_status()
    return response.text


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


def _find_top300_table(soup: BeautifulSoup):
    for heading in soup.find_all(["h2", "h3"]):
        text = heading.get_text(" ", strip=True).lower()
        if TOP300_HEADING.lower() not in text:
            continue
        table = heading.find_next("table")
        if table is not None:
            return table

    best_table = None
    best_rows = 0
    for table in soup.find_all("table"):
        headers = [_normalize_header(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        has_rank = "rank" in headers
        has_player = "player" in headers
        if not (has_rank and has_player):
            continue
        row_count = len(table.find_all("tr"))
        if row_count > best_rows:
            best_rows = row_count
            best_table = table
    return best_table


def _parse_table(
    table,
    meta: ArticleMeta,
    source: str = "espn_points_top300",
    limit: int = 300,
) -> dict[str, RankingEntry]:
    headers = [_normalize_header(th.get_text(" ", strip=True)) for th in table.find_all("th")]
    if not headers:
        return {}

    idx_rank = next((i for i, header in enumerate(headers) if header == "rank"), None)
    idx_player = next((i for i, header in enumerate(headers) if header == "player"), None)
    if idx_rank is None or idx_player is None:
        return {}

    ranked: dict[str, RankingEntry] = {}
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        if len(cells) <= max(idx_rank, idx_player):
            continue

        rank_text = cells[idx_rank].get_text(" ", strip=True)
        rank_match = re.search(r"\d{1,3}", rank_text)
        if not rank_match:
            continue
        rank = int(rank_match.group())
        if rank > limit:
            continue

        raw_name = cells[idx_player].get_text(" ", strip=True)
        name = clean_player_name(raw_name)
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
            source=row.get("source", "espn_points_top300"),
            rank=row.get("rank"),
            tier=row.get("tier"),
            article_url=row.get("article_url"),
            article_title=row.get("article_title"),
            article_date=row.get("article_date"),
            position=row.get("position"),
            raw=row.get("raw"),
        )
    return ranked


def scrape_espn_points_top300(
    url: str = ESPN_POINTS_TOP300_URL,
    force_refresh: bool = False,
    limit: int = 300,
) -> dict[str, RankingEntry]:
    _ttl = ttl_for(_CACHE_KEY)
    stale = _cache.get_stale(_CACHE_NS, _CACHE_KEY)
    fresh = None if force_refresh else _cache.get(_CACHE_NS, _CACHE_KEY, ttl_seconds=_ttl)

    with log_feed_fetch("espn_points", "scrape_espn_points_top300") as feed_log:
        if fresh is not None:
            feed_log.mark_cache_fallback()
            return _deserialize_rankings(fresh.get("rows", []))

        try:
            html = fetch_html(url=url)
            soup = BeautifulSoup(html, "html.parser")
            meta = extract_article_meta(soup, url)

            table = _find_top300_table(soup)
            if table is None:
                raise ValueError("Could not find ESPN points Top 300 table.")

            ranked = _parse_table(table, meta=meta, limit=limit)
            if not ranked:
                raise ValueError("No ESPN points Top 300 rows were parsed.")

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
