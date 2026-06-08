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

TOP_300_HITTERS_URL = "https://pitcherlist.com/top-300-hitters-for-fantasy-baseball-2026/"
TOP_400_DYNASTY_URL = "https://pitcherlist.com/2026-top-400-dynasty-rankings-v1-0/"
SP_STREAMERS_CATEGORY_URL = "https://pitcherlist.com/category/fantasy/starting-pitchers/sp-streamers/"

TIER_ORDER = ["Auto-Start", "Probably Start", "Questionable Start", "Do Not Start"]
OPPONENT_SCORE_ORDER = ["Top", "Solid", "Average", "Weak", "Poor"]

_CACHE_NS = "collector"
_HITTERS_KEY = "pitcherlist_top_hitters"
_DYNASTY_KEY = "pitcherlist_dynasty_hitters"


@dataclass(slots=True)
class ArticleMeta:
    url: str
    title: str | None = None
    date_text: str | None = None


def fetch_html(url: str, timeout: int = 20) -> BeautifulSoup:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_article_meta(soup: BeautifulSoup, fallback_url: str) -> ArticleMeta:
    title = None
    if soup.title and soup.title.text:
        title = soup.title.text.strip()

    date_text = None
    time_node = soup.find("time")
    if time_node:
        date_text = time_node.get_text(" ", strip=True) or time_node.get("datetime")

    return ArticleMeta(url=fallback_url, title=title, date_text=date_text)


def _combine_cell_links_and_suffix(cell) -> str:
    links = [a.get_text(" ", strip=True) for a in cell.find_all("a") if a.get_text(" ", strip=True)]
    whole = clean_player_name(cell.get_text(" ", strip=True))
    if not links:
        return whole
    base = " ".join(links).strip()
    suffix = whole.replace(base, "", 1).strip()
    return clean_player_name(f"{base} {suffix}" if suffix else base)


def _parse_ranked_table(table, limit: int, name_headers: tuple[str, ...], meta: ArticleMeta, source: str) -> dict[str, RankingEntry]:
    headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
    if "rank" not in headers:
        return {}

    name_idx = next((headers.index(h) for h in name_headers if h in headers), None)
    if name_idx is None:
        return {}
    rank_idx = headers.index("rank")

    ranked: dict[str, RankingEntry] = {}
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) <= max(rank_idx, name_idx):
            continue

        rank_text = cells[rank_idx].get_text(" ", strip=True)
        match = re.search(r"\d{1,3}", rank_text)
        if not match:
            continue
        rank = int(match.group())
        if rank > limit:
            continue

        name = _combine_cell_links_and_suffix(cells[name_idx])
        if not name:
            continue

        ranked.setdefault(
            normalize_name(name),
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
            source=row.get("source", ""),
            rank=row.get("rank"),
            tier=row.get("tier"),
            article_url=row.get("article_url"),
            article_title=row.get("article_title"),
            article_date=row.get("article_date"),
            position=row.get("position"),
            raw=row.get("raw"),
        )
    return ranked


def _canonical_team_code(code: str) -> str:
    normalized = code.strip().upper()
    remap = {
        "WSN": "WSH",
        "CHW": "CWS",
        "KCR": "KC",
        "SFG": "SF",
        "SDP": "SD",
        "TBR": "TB",
    }
    return remap.get(normalized, normalized)


def _extract_team_codes(text: str) -> list[str]:
    if not text:
        return []
    codes = re.findall(r"[A-Z]{2,3}", text.upper())
    return [_canonical_team_code(code) for code in codes]


def _parse_opponent_score_table(article) -> dict[str, str]:
    for table in article.find_all("table"):
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        if [h.strip().title() for h in headers[:5]] != OPPONENT_SCORE_ORDER:
            continue

        matchup_scores: dict[str, str] = {}
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue
            for idx, bucket in enumerate(OPPONENT_SCORE_ORDER):
                if idx >= len(cells):
                    break
                cell_text = cells[idx].get_text(" ", strip=True)
                for team_code in _extract_team_codes(cell_text):
                    matchup_scores.setdefault(team_code, bucket)
        if matchup_scores:
            return matchup_scores

    return {}


def _extract_matchup_opponent_team(text: str) -> str | None:
    codes = _extract_team_codes(text)
    if not codes:
        return None
    return codes[-1]


def _find_tier_label(text: str) -> str | None:
    normalized = re.sub(r"[^a-z]", "", text.lower())
    for tier in TIER_ORDER:
        tier_normalized = re.sub(r"[^a-z]", "", tier.lower())
        if tier_normalized and tier_normalized in normalized:
            return tier
    return None


def _parse_streamer_pitcher_tables(article, meta: ArticleMeta, matchup_scores: dict[str, str]) -> dict[str, RankingEntry]:
    pitchers: dict[str, RankingEntry] = {}

    for table in article.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if not headers or "pitcher" not in headers or "matchup" not in headers:
            continue

        idx_pitcher = headers.index("pitcher")
        idx_matchup = headers.index("matchup")
        current_tier: str | None = None

        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) <= max(idx_pitcher, idx_matchup):
                continue

            pitcher_cell = cells[idx_pitcher]
            pitcher_text = pitcher_cell.get_text(" ", strip=True)
            matchup_text = cells[idx_matchup].get_text(" ", strip=True)

            tier_hit = _find_tier_label(pitcher_text)
            if tier_hit and not pitcher_cell.find("a"):
                current_tier = tier_hit
                continue

            anchors = [
                a for a in pitcher_cell.find_all("a", href=True)
                if "pitcherlist.com/player/" in a["href"]
            ]
            if not anchors:
                continue

            for anchor in anchors:
                name = anchor.get_text(strip=True)
                if not name:
                    continue
                key = normalize_name(name)
                opponent_team = _extract_matchup_opponent_team(matchup_text)
                pitchers.setdefault(
                    key,
                    RankingEntry(
                        source="pitcherlist_sp_streamers",
                        tier=current_tier or "Not Ranked",
                        article_url=meta.url,
                        article_title=meta.title,
                        article_date=meta.date_text,
                        opponent_team=opponent_team,
                        opponent_score=matchup_scores.get(opponent_team) if opponent_team else None,
                        raw=tr.get_text(" ", strip=True),
                    ),
                )

    return pitchers


def scrape_top_hitters(
    url: str = TOP_300_HITTERS_URL,
    limit: int = 300,
    force_refresh: bool = False,
) -> dict[str, RankingEntry]:
    _ttl = ttl_for(_HITTERS_KEY)
    stale = _cache.get_stale(_CACHE_NS, _HITTERS_KEY)
    fresh = None if force_refresh else _cache.get(_CACHE_NS, _HITTERS_KEY, ttl_seconds=_ttl)

    with log_feed_fetch("pitcherlist", "scrape_top_hitters") as feed_log:
        if fresh is not None:
            feed_log.mark_cache_fallback()
            return _deserialize_rankings(fresh.get("rows", []))

        try:
            soup = fetch_html(url)
            meta = extract_article_meta(soup, url)

            for table in soup.find_all("table"):
                headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
                if "rank" in headers and "hitter" in headers:
                    ranked = _parse_ranked_table(table, limit, ("hitter",), meta, source="pitcherlist_top_hitters")
                    if ranked:
                        payload = {
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                            "url": url,
                            "rows": _serialize_rankings(ranked),
                        }
                        _cache.set(_CACHE_NS, _HITTERS_KEY, payload, ttl_seconds=_ttl)
                        return ranked

            ranked: dict[str, RankingEntry] = {}
            article = soup.find("article") or soup.find("main") or soup
            for raw in article.get_text("\n", strip=True).splitlines():
                line = " ".join(raw.split())
                match = re.match(r"^(\d{1,3})\.\s+(.+?)\s+\(([A-Z0-9, /]+)\)$", line)
                if not match:
                    continue
                rank = int(match.group(1))
                if rank > limit:
                    continue
                name = clean_player_name(match.group(2))
                ranked.setdefault(
                    normalize_name(name),
                    RankingEntry(
                        source="pitcherlist_top_hitters",
                        rank=rank,
                        article_url=meta.url,
                        article_title=meta.title,
                        article_date=meta.date_text,
                        raw=line,
                    ),
                )

            if not ranked:
                raise ValueError("No Top 300 hitters were parsed from Pitcher List.")

            payload = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "url": url,
                "rows": _serialize_rankings(ranked),
            }
            _cache.set(_CACHE_NS, _HITTERS_KEY, payload, ttl_seconds=_ttl)
            return ranked
        except Exception:
            if stale:
                feed_log.mark_cache_fallback()
                return _deserialize_rankings(stale.get("rows", []))
            return {}


def scrape_dynasty_hitters(
    url: str = TOP_400_DYNASTY_URL,
    limit: int = 400,
    force_refresh: bool = False,
) -> dict[str, RankingEntry]:
    _ttl = ttl_for(_DYNASTY_KEY)
    stale = _cache.get_stale(_CACHE_NS, _DYNASTY_KEY)
    fresh = None if force_refresh else _cache.get(_CACHE_NS, _DYNASTY_KEY, ttl_seconds=_ttl)

    with log_feed_fetch("pitcherlist", "scrape_dynasty_hitters") as feed_log:
        if fresh is not None:
            feed_log.mark_cache_fallback()
            return _deserialize_rankings(fresh.get("rows", []))

        try:
            soup = fetch_html(url)
            meta = extract_article_meta(soup, url)

            for table in soup.find_all("table"):
                headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
                if "rank" in headers and "player" in headers:
                    ranked = _parse_ranked_table(table, limit, ("player",), meta, source="pitcherlist_dynasty")
                    if ranked:
                        payload = {
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                            "url": url,
                            "rows": _serialize_rankings(ranked),
                        }
                        _cache.set(_CACHE_NS, _DYNASTY_KEY, payload, ttl_seconds=_ttl)
                        return ranked

            ranked: dict[str, RankingEntry] = {}
            article = soup.find("article") or soup.find("main") or soup
            for raw in article.get_text("\n", strip=True).splitlines():
                line = " ".join(raw.split())
                match = re.match(r"^(\d{1,3})\s+(.+?)\s+[A-Z]{2,3}\s+[A-Z0-9/*,]+(?:/[A-Z0-9/*,]+)*$", line)
                if not match:
                    continue
                rank = int(match.group(1))
                if rank > limit:
                    continue
                name = clean_player_name(match.group(2))
                ranked.setdefault(
                    normalize_name(name),
                    RankingEntry(
                        source="pitcherlist_dynasty",
                        rank=rank,
                        article_url=meta.url,
                        article_title=meta.title,
                        article_date=meta.date_text,
                        raw=line,
                    ),
                )

            if not ranked:
                raise ValueError("No Top 400 dynasty hitters were parsed from Pitcher List.")

            payload = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "url": url,
                "rows": _serialize_rankings(ranked),
            }
            _cache.set(_CACHE_NS, _DYNASTY_KEY, payload, ttl_seconds=_ttl)
            return ranked
        except Exception:
            if stale:
                feed_log.mark_cache_fallback()
                return _deserialize_rankings(stale.get("rows", []))
            return {}


def get_latest_streamer_url() -> str:
    with log_feed_fetch("pitcherlist", "get_latest_streamer_url"):
        soup = fetch_html(SP_STREAMERS_CATEGORY_URL, timeout=10)
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if "/starting-pitcher-streamer-ranks" in href:
                return href
        raise ValueError("Could not find latest SP Streamers post.")


def scrape_sp_streamer_tiers(url: str | None = None) -> tuple[str, dict[str, RankingEntry]]:
    resolved_url = url or get_latest_streamer_url()
    with log_feed_fetch("pitcherlist", "scrape_sp_streamer_tiers"):
        soup = fetch_html(resolved_url, timeout=10)
        meta = extract_article_meta(soup, resolved_url)
        article = soup.find("article") or soup.find("div", class_=re.compile("entry|content|post")) or soup
        matchup_scores = _parse_opponent_score_table(article)
        pitchers = _parse_streamer_pitcher_tables(article, meta=meta, matchup_scores=matchup_scores)
        current_tier: str | None = None
        for elem in article.find_all(["h2", "h3", "h4", "strong", "b", "p", "li", "td"]):
            text = elem.get_text(strip=True)
            tier_hit = _find_tier_label(text)
            if tier_hit and len(text) < 60:
                current_tier = tier_hit
            if not current_tier:
                continue
            for anchor in elem.find_all("a", href=True):
                href = anchor["href"]
                if "pitcherlist.com/player/" not in href:
                    continue
                name = anchor.get_text(strip=True)
                if not name:
                    continue
                key = normalize_name(name)
                opponent_team = _extract_matchup_opponent_team(text)
                pitchers.setdefault(
                    key,
                    RankingEntry(
                        source="pitcherlist_sp_streamers",
                        tier=current_tier,
                        article_url=meta.url,
                        article_title=meta.title,
                        article_date=meta.date_text,
                        opponent_team=opponent_team,
                        opponent_score=matchup_scores.get(opponent_team) if opponent_team else None,
                        raw=text,
                    ),
                )

        return resolved_url, pitchers
