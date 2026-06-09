from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from utils.cache_retention import ttl_for
from utils.cache_store import store as _cache
from utils.feed_logger import log_feed_fetch
from utils.names import clean_player_name, normalize_name

_ESPN_NEWS_API = (
    "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news?limit=30"
)
_DAILY_NOTES_SLUG = "fantasy-baseball-pitcher-rankings-lineup-advice-tips-mlb-daily-notes"
_CACHE_NS = "collector"
_CACHE_KEY_PREFIX = "espn_daily_notes"

_FETCH_HEADERS = {"User-Agent": "curl/8.5.0"}


def _fetch_html(url: str, timeout: int = 20) -> str:
    response = requests.get(url, headers=_FETCH_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def _discover_article_url(for_date: date) -> str | None:
    """Discover today's daily notes article URL via ESPN's news API."""
    try:
        resp = requests.get(_ESPN_NEWS_API, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception:
        return None

    for article in articles:
        href = article.get("links", {}).get("web", {}).get("href", "")
        if _DAILY_NOTES_SLUG in href:
            return href
    return None


def _as_float(text: str) -> float | None:
    if not text or text in {"-", "—", "-.--"}:
        return None
    text = text.strip().rstrip("%")
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_col(text: str) -> str:
    return " ".join(text.split()).lower()


def _find_sp_table(soup: BeautifulSoup):
    """Return the SP rankings table — the one with a FPTS header column."""
    for table in soup.find_all("table"):
        headers = [_normalize_col(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        if "fpts" in headers and ("pitcher" in headers or "player" in headers):
            return table
    return None


def _parse_sp_table(table) -> dict[str, dict]:
    headers = [_normalize_col(th.get_text(" ", strip=True)) for th in table.find_all("th")]

    def col(name: str) -> int | None:
        try:
            return headers.index(name)
        except ValueError:
            return None

    idx_pitcher = col("pitcher") or col("player")
    idx_fpts = col("fpts")
    idx_win = col("w%") or col("win%") or col("win pct")
    idx_opp = col("opponent") or col("opp")

    if idx_pitcher is None or idx_fpts is None:
        return {}

    projections: dict[str, dict] = {}
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        max_idx = max(i for i in [idx_pitcher, idx_fpts, idx_win, idx_opp] if i is not None)
        if len(cells) <= max_idx:
            continue

        raw_name = cells[idx_pitcher].get_text(" ", strip=True)
        name = clean_player_name(raw_name)
        if not name:
            continue

        fpts_text = cells[idx_fpts].get_text(" ", strip=True) if idx_fpts is not None else None
        fpts = _as_float(fpts_text) if fpts_text else None

        win_text = cells[idx_win].get_text(" ", strip=True) if idx_win is not None else None
        win_raw = _as_float(win_text) if win_text else None
        # Normalize win% to 0–1 range (column may be "42" or "0.42")
        if win_raw is not None and win_raw > 1:
            win_raw = win_raw / 100.0

        opp_text = cells[idx_opp].get_text(" ", strip=True) if idx_opp is not None else None
        opponent = opp_text if opp_text and opp_text not in {"-", "—"} else None

        key = normalize_name(name)
        projections.setdefault(key, {"fpts": fpts, "win_pct": win_raw, "opponent": opponent})

    return projections


def _serialize(projections: dict[str, dict]) -> list[dict]:
    return [{"normalized_name": k, **v} for k, v in projections.items()]


def _deserialize(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        key = row.get("normalized_name")
        if key:
            result[key] = {
                "fpts": row.get("fpts"),
                "win_pct": row.get("win_pct"),
                "opponent": row.get("opponent"),
            }
    return result


def scrape_espn_daily_sp_rankings(
    for_date: date | None = None,
    force_refresh: bool = False,
) -> tuple[str | None, dict[str, dict]]:
    """Fetch and parse ESPN's daily SP rankings table.

    Returns (article_url, {normalized_name: {"fpts", "win_pct", "opponent"}}).
    Falls back to stale cache on any fetch/parse failure.
    """
    target = for_date or date.today()
    cache_key = f"{_CACHE_KEY_PREFIX}_{target.isoformat()}"
    _ttl = ttl_for(cache_key)

    stale = _cache.get_stale(_CACHE_NS, cache_key)
    if stale is None:
        yesterday_key = f"{_CACHE_KEY_PREFIX}_{(target - timedelta(days=1)).isoformat()}"
        stale = _cache.get_stale(_CACHE_NS, yesterday_key)
    fresh = None if force_refresh else _cache.get(_CACHE_NS, cache_key, ttl_seconds=_ttl)

    with log_feed_fetch("espn_daily_notes", "scrape_espn_daily_sp_rankings") as feed_log:
        if fresh is not None:
            feed_log.mark_cache_fallback()
            return fresh.get("url"), _deserialize(fresh.get("rows", []))

        try:
            article_url = _discover_article_url(target)
            if not article_url:
                raise ValueError("Could not discover ESPN daily notes article URL from homepage.")

            html = _fetch_html(article_url)
            soup = BeautifulSoup(html, "html.parser")

            table = _find_sp_table(soup)
            if table is None:
                raise ValueError("Could not find ESPN SP rankings table in article.")

            projections = _parse_sp_table(table)
            if not projections:
                raise ValueError("No rows parsed from ESPN SP rankings table.")

            payload = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "url": article_url,
                "rows": _serialize(projections),
            }
            _cache.set(_CACHE_NS, cache_key, payload, ttl_seconds=_ttl)
            return article_url, projections

        except Exception:
            if stale:
                feed_log.mark_cache_fallback()
                return stale.get("url"), _deserialize(stale.get("rows", []))
            return None, {}
