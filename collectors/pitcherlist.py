from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from models.player import RankingEntry
from utils.names import clean_player_name, normalize_name

TOP_300_HITTERS_URL = "https://pitcherlist.com/top-300-hitters-for-fantasy-baseball-2026/"
TOP_400_DYNASTY_URL = "https://pitcherlist.com/2026-top-400-dynasty-rankings/"
SP_STREAMERS_CATEGORY_URL = "https://pitcherlist.com/category/fantasy/starting-pitchers/sp-streamers/"

TIER_ORDER = ["Auto-Start", "Probably Start", "Questionable Start", "Do Not Start"]


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


def scrape_top_hitters(url: str = TOP_300_HITTERS_URL, limit: int = 300) -> dict[str, RankingEntry]:
    soup = fetch_html(url)
    meta = extract_article_meta(soup, url)

    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if "rank" in headers and "hitter" in headers:
            ranked = _parse_ranked_table(table, limit, ("hitter",), meta, source="pitcherlist_top_hitters")
            if ranked:
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
    return ranked


def scrape_dynasty_hitters(url: str = TOP_400_DYNASTY_URL, limit: int = 400) -> dict[str, RankingEntry]:
    soup = fetch_html(url)
    meta = extract_article_meta(soup, url)

    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if "rank" in headers and "player" in headers:
            ranked = _parse_ranked_table(table, limit, ("player",), meta, source="pitcherlist_dynasty")
            if ranked:
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
    return ranked


def get_latest_streamer_url() -> str:
    soup = fetch_html(SP_STREAMERS_CATEGORY_URL, timeout=10)
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/starting-pitcher-streamer-ranks" in href:
            return href
    raise ValueError("Could not find latest SP Streamers post.")


def scrape_sp_streamer_tiers(url: str | None = None) -> tuple[str, dict[str, RankingEntry]]:
    resolved_url = url or get_latest_streamer_url()
    soup = fetch_html(resolved_url, timeout=10)
    meta = extract_article_meta(soup, resolved_url)
    pitchers: dict[str, RankingEntry] = {}
    current_tier: str | None = None

    article = soup.find("article") or soup.find("div", class_=re.compile("entry|content|post")) or soup
    for elem in article.find_all(["h2", "h3", "h4", "strong", "b", "p", "li", "td"]):
        text = elem.get_text(strip=True)
        for tier in TIER_ORDER:
            if tier.lower() in text.lower() and len(text) < 60:
                current_tier = tier
                break
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
            pitchers.setdefault(
                key,
                RankingEntry(
                    source="pitcherlist_sp_streamers",
                    tier=current_tier,
                    article_url=meta.url,
                    article_title=meta.title,
                    article_date=meta.date_text,
                    raw=text,
                ),
            )

    return resolved_url, pitchers
