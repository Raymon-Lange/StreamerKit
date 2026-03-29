import os
import sys
import re
import argparse
from datetime import date
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup

load_dotenv()

LEAGUE_ID = int(os.getenv("LEAGUE_ID", 0))
YEAR = date.today().year
ESPN_S2 = os.getenv("ESPN_S2", "")
ESPN_SWID = os.getenv("ESPN_SWID", "")

HITTER_POSITIONS = {"C", "1B", "2B", "3B", "SS", "OF", "LF", "CF", "RF", "DH", "UTIL"}
POSITION_QUERIES = ["C", "1B", "2B", "3B", "SS", "OF", "DH"]
PL_HITTER_URL = "https://pitcherlist.com/top-300-hitters-for-fantasy-baseball-2026/"


def parse_args():
    parser = argparse.ArgumentParser(
        description="List top free-agent hitters in your ESPN league and compare them to Pitcher List Top 300 Hitters."
    )
    parser.add_argument("--league-id", type=int, default=LEAGUE_ID, help="ESPN fantasy league ID")
    parser.add_argument("--year", type=int, default=YEAR, help="Season year")
    parser.add_argument("--top", type=int, default=10, help="How many free-agent hitters to show")
    parser.add_argument("--size", type=int, default=75, help="How many free agents to fetch per ESPN position query")
    parser.add_argument("--url", type=str, default=PL_HITTER_URL, help="Pitcher List hitters URL")
    return parser.parse_args()


# ── Helpers ──────────────────────────────────────────────────────────────────

def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def get_league(args):
    try:
        from espn_api.baseball import League
    except ImportError:
        sys.exit("[error] espn-api is not installed.\nRun: pip install espn-api")

    if not args.league_id:
        sys.exit("[error] No league ID set.\nEdit LEAGUE_ID in the script or pass --league-id <id>.")

    if not ESPN_S2 or not ESPN_SWID:
        sys.exit(
            "[error] ESPN credentials missing.\n"
            "Set ESPN_S2 and ESPN_SWID environment variables."
        )

    print(f"Connecting to ESPN league {args.league_id} ({args.year})...")
    try:
        return League(league_id=args.league_id, year=args.year, espn_s2=ESPN_S2, swid=ESPN_SWID)
    except Exception as e:
        sys.exit(f"[error] Could not connect to ESPN: {e}")


def is_hitter(player) -> bool:
    slots = set(getattr(player, "eligibleSlots", []) or [])
    pos = getattr(player, "position", "") or ""
    pro_pos = getattr(player, "proPosition", "") or ""
    combined = {str(x).upper() for x in slots} | {pos.upper(), pro_pos.upper()}
    if {"P", "SP", "RP"} & combined:
        return False
    return bool(HITTER_POSITIONS & combined)


# ── Pitcher List Hitters ─────────────────────────────────────────────────────

def scrape_pl_hitters(url: str):
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    article = (
        soup.find("article")
        or soup.find("div", class_=re.compile("entry|content|post"))
        or soup
    )

    hitters = {}
    pattern = re.compile(r"^(\d+)\.\s+(.+?)\s*\((.*?)\)")

    for elem in article.find_all(["p", "li", "td"]):
        text = " ".join(elem.get_text(" ", strip=True).split())
        m = pattern.match(text)
        if not m:
            continue

        rank = int(m.group(1))
        raw_name = m.group(2)
        name = re.sub(r"\s+—.*$", "", raw_name).strip()
        if name.lower().startswith("tier "):
            continue

        key = normalize_name(name)
        if key not in hitters:
            hitters[key] = {
                "rank": rank,
                "name": name,
                "raw": text,
            }

    return hitters


def tier_from_rank(rank: int | None) -> str:
    if rank is None:
        return "Unranked"
    if rank <= 75:
        return "Impact"
    if rank <= 150:
        return "Strong"
    if rank <= 220:
        return "Consider"
    return "Depth"


def recommendation(rank: int | None, percent_owned: float | None) -> str:
    owned = percent_owned or 0.0
    if rank is not None and rank <= 120:
        return "PICK UP"
    if rank is not None and rank <= 180:
        return "ADD IF NEED FIT"
    if rank is not None and rank <= 240:
        return "WATCHLIST"
    if owned >= 50:
        return "CHECK FORMAT FIT"
    return "PASS"


def why(rank: int | None, percent_owned: float | None) -> str:
    owned = percent_owned or 0.0
    if rank is None:
        return "Not in Pitcher List Top 300 hitters"
    if rank <= 120:
        return "Ranked high enough to matter in most 12-team formats"
    if rank <= 180:
        return "Viable add depending on category need and roster spot"
    if rank <= 240:
        return "More of a depth play than a must-add"
    if owned >= 50:
        return "Outside the preferred range but still broadly rostered"
    return "Lower-priority waiver option"


# ── ESPN Free Agents ─────────────────────────────────────────────────────────

def get_free_agent_hitters(league, size_per_pos=75):
    players = {}

    for pos in POSITION_QUERIES:
        try:
            batch = league.free_agents(size=size_per_pos, position=pos)
        except Exception as e:
            print(f"[warning] Could not fetch {pos} free agents: {e}")
            continue

        for p in batch:
            if not is_hitter(p):
                continue
            key = getattr(p, "playerId", None) or normalize_name(p.name)
            if key not in players:
                players[key] = p
            else:
                existing = players[key]
                old_owned = existing.percent_owned or 0.0
                new_owned = p.percent_owned or 0.0
                if new_owned > old_owned:
                    players[key] = p

    return list(players.values())


def format_positions(player) -> str:
    slots = [str(x) for x in (getattr(player, "eligibleSlots", []) or [])]
    slots = [s for s in slots if s not in {"BE", "IL", "IL10", "IL15", "IL60", "NA", "P", "SP", "RP"}]
    seen = []
    for s in slots:
        if s not in seen:
            seen.append(s)
    return "/".join(seen[:4]) if seen else (getattr(player, "position", "") or "N/A")


def print_player_card(player, pl_hitters):
    owned = player.percent_owned if player.percent_owned is not None else 0.0
    team = getattr(player, "proTeam", "N/A") or "N/A"
    positions = format_positions(player)

    key = normalize_name(player.name)
    pl = pl_hitters.get(key)
    rank = pl["rank"] if pl else None
    bucket = tier_from_rank(rank)
    rec = recommendation(rank, owned)
    note = why(rank, owned)

    rank_str = f"#{rank}" if rank else "Unranked"
    print(f"  {player.name:<24} {team:<5} {positions:<12} {owned:>6.1f}%")
    print(f"     Pitcher List: {rank_str:<9} Tier: {bucket:<8} Recommendation: {rec}")
    print(f"     Why: {note}")
    print(f"  {'·' * 70}")


def main():
    args = parse_args()

    league = get_league(args)
    print(f"  Connected: {league.settings.name}\n")

    print("Fetching Pitcher List hitter rankings...")
    try:
        pl_hitters = scrape_pl_hitters(args.url)
        print(f"  Found {len(pl_hitters)} ranked hitters.\n")
    except Exception as e:
        sys.exit(f"[error] Could not fetch Pitcher List hitters: {e}")

    print("Fetching ESPN free-agent hitters...")
    free_agents = get_free_agent_hitters(league, size_per_pos=args.size)
    if not free_agents:
        sys.exit("[error] No free-agent hitters found.")

    # Sort: ranked hitters first, then by percent owned
    def sort_key(p):
        pl = pl_hitters.get(normalize_name(p.name))
        rank = pl["rank"] if pl else 9999
        owned = -(p.percent_owned or 0.0)
        return (rank, owned)

    top_hitters = sorted(free_agents, key=sort_key)[: args.top]

    divider = "─" * 78
    print(divider)
    print(f"  Top {args.top} Free-Agent Hitters vs Pitcher List Top 300")
    print(f"  📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"  🏟   League: {league.settings.name}")
    print(divider)

    for player in top_hitters:
        print_player_card(player, pl_hitters)

    print(f"\n  Source: {args.url}")
    print(divider)


if __name__ == "__main__":
    main()
