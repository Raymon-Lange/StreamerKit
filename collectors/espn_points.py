from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from models.player import RankingEntry
from utils.names import clean_player_name, normalize_name

ESPN_POINTS_TOP300_URL = (
    "https://www.espn.com/fantasy/baseball/story/_/id/35437997/"
    "fantasy-baseball-rankings-points-leagues-2026-espn-cockcroft"
)
CACHE_PATH = Path(__file__).resolve().parents[1] / ".cache" / "espn_points_top300_2026.json"
CACHE_TTL = timedelta(days=15)
TOP300_HEADING = "Top 300 Rankings for 2026"


@dataclass(slots=True)
class ArticleMeta:
    url: str
    title: str | None = None
    date_text: str | None = None


def fetch_html(url: str = ESPN_POINTS_TOP300_URL, timeout: int = 20) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=timeout)
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


def _is_cache_fresh() -> bool:
    if not CACHE_PATH.exists():
        return False
    modified_at = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
    return datetime.now(timezone.utc) - modified_at <= CACHE_TTL


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


def _save_cache(url: str, ranked: dict[str, RankingEntry]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "rows": _serialize_rankings(ranked),
    }
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def scrape_espn_points_top300(
    url: str = ESPN_POINTS_TOP300_URL,
    force_refresh: bool = False,
    limit: int = 300,
) -> dict[str, RankingEntry]:
    cached = _load_cache()
    if cached and not force_refresh and _is_cache_fresh():
        return _deserialize_rankings(cached.get("rows", []))

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

        _save_cache(url, ranked)
        return ranked
    except Exception:
        if cached:
            return _deserialize_rankings(cached.get("rows", []))
        raise
