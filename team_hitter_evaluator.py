"""
ESPN Fantasy Baseball - My Team Hitter Evaluator
================================================
Evaluates the hitters currently on your roster using:
  • Pitcher List Top 300 Hitters (redraft)
  • Pitcher List Top 400 Dynasty Rankings
  • Recent trend from MLB game logs (hot/cold)

The script prints your current fielding hitters and whether they look like:
  • HOLD
  • START
  • BENCH / STREAM
  • SHOP / REPLACE

Requirements:
    pip install espn-api requests beautifulsoup4 MLB-StatsAPI python-dotenv

Setup:
    export ESPN_S2="your_espn_s2_cookie"
    export ESPN_SWID="{your-swid-cookie}"
    export LEAGUE_ID="your_league_id"

Usage:
    python team_hitter_evaluator.py
    python team_hitter_evaluator.py --league-id 12345
    python team_hitter_evaluator.py --team-id 3
    python team_hitter_evaluator.py --all-hitters
"""

import os
import re
import sys
import argparse
import unicodedata
from datetime import date
from statistics import mean

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import statsapi

load_dotenv()

LEAGUE_ID = int(os.getenv("LEAGUE_ID", 0) or 0)
YEAR = date.today().year
ESPN_S2 = os.getenv("ESPN_S2", "")
ESPN_SWID = os.getenv("ESPN_SWID", "")

TOP_300_URL = "https://pitcherlist.com/top-300-hitters-for-fantasy-baseball-2026/"
DYNASTY_400_URL = "https://pitcherlist.com/2026-top-400-dynasty-rankings/"

HITTER_POSITIONS = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "DH", "UTIL"}


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate hitters currently on your ESPN fantasy roster.")
    parser.add_argument("--league-id", type=int, default=LEAGUE_ID, help="ESPN league ID")
    parser.add_argument("--year", type=int, default=YEAR, help="Season year")
    parser.add_argument("--team-id", type=int, default=None, help="Your ESPN team ID (1-based). Defaults to first team.")
    parser.add_argument("--trend-games", type=int, default=10, help="Number of recent games to evaluate for trend")
    parser.add_argument("--all-hitters", action="store_true", help="Evaluate all hitters on roster, not just likely fielding lineup")
    return parser.parse_args()


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower().replace("jr.", "jr").replace("sr.", "sr")
    name = name.replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9 ]", "", name).strip()


def get_league(args):
    try:
        from espn_api.baseball import League
    except ImportError:
        sys.exit("[error] espn-api is not installed. Run: pip install espn-api")

    if not args.league_id:
        sys.exit("[error] No league ID set. Pass --league-id or set LEAGUE_ID.")

    if not ESPN_S2 or not ESPN_SWID:
        sys.exit("[error] ESPN credentials missing. Set ESPN_S2 and ESPN_SWID environment variables.")

    try:
        return League(league_id=args.league_id, year=args.year, espn_s2=ESPN_S2, swid=ESPN_SWID)
    except Exception as e:
        sys.exit(f"[error] Could not connect to ESPN: {e}")


def _parse_ranked_table(table, limit: int):
    headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
    if not headers or "rank" not in headers or "player" not in headers:
        return {}

    rank_idx = headers.index("rank")
    player_idx = headers.index("player")
    ranked = {}

    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) <= max(rank_idx, player_idx):
            continue

        rank_text = cells[rank_idx].get_text(" ", strip=True)
        m_rank = re.search(r"\d{1,3}", rank_text)
        if not m_rank:
            continue

        rank = int(m_rank.group())
        if rank > limit:
            continue

        player_cell = cells[player_idx]
        player_text = player_cell.get_text(" ", strip=True)
        if not player_text:
            continue

        links = [a.get_text(" ", strip=True) for a in player_cell.find_all("a") if a.get_text(" ", strip=True)]
        if links:
            base = " ".join(links).strip()
            whole = player_cell.get_text(" ", strip=True)
            suffix = whole.replace(base, "", 1).strip()
            name = f"{base} {suffix}".strip()
        else:
            name = player_text

        name = re.sub(r"/td.*$", "", name).strip()
        name = re.sub(r"\*+$", "", name).strip()
        name = " ".join(name.split())
        if not name:
            continue

        key = normalize_name(name)
        ranked.setdefault(key, (name, rank))

    return ranked


def scrape_ranked_players(url: str, limit: int):
    """Scrape Pitcher List ranking pages.

    Prefer parsing a real HTML table first. This is the correct approach for the
    dynasty page, which exposes a Rank / Player / Team / Pos table.
    Fall back to line parsing for article-style pages.
    """
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Preferred path: real table parsing.
    table_candidates = []
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if "rank" in headers and "player" in headers:
            table_candidates.append(table)

    for table in table_candidates:
        ranked = _parse_ranked_table(table, limit)
        if ranked:
            return ranked

    # 2) Fallback path: line parsing for non-table content.
    article = soup.find("article") or soup.find("main") or soup
    ranked = {}
    lines = []
    for raw in article.get_text("\n", strip=True).splitlines():
        line = " ".join(raw.split())
        if line:
            lines.append(line)

    for line in lines:
        m = re.match(r"^(\d{1,3})\.?\s+(.*)$", line)
        if not m:
            continue

        rank = int(m.group(1))
        if rank > limit:
            continue

        rest = m.group(2).strip()
        name = None

        m_redraft = re.match(r"^([A-Za-zÀ-ÖØ-öø-ÿ'’\-. ]+?)\s+\(([A-Z0-9/, ]+)\)", rest)
        if m_redraft:
            name = m_redraft.group(1).strip()
        else:
            m_team_pos = re.match(r"^([A-Za-zÀ-ÖØ-öø-ÿ'’\-. ]+?)\s+([A-Z]{2,3})\s+([A-Z0-9/*,]+(?:/[A-Z0-9/*,]+)*)$", rest)
            if m_team_pos:
                name = m_team_pos.group(1).strip()

        if not name:
            continue

        name = re.sub(r"\*+$", "", name).strip()
        key = normalize_name(name)
        ranked.setdefault(key, (name, rank))

    return ranked


def get_player_id(name: str):
    try:
        results = statsapi.lookup_player(name)
    except Exception:
        return None
    if not results:
        return None
    for p in results:
        pos = (p.get("primaryPosition") or {}).get("abbreviation", "")
        if pos not in ("P", "SP", "RP"):
            return p["id"]
    return results[0]["id"]


def get_hitter_game_log(player_id: int):
    try:
        data = statsapi.get("people", {
            "personIds": player_id,
            "hydrate": f"stats(group=hitting,type=gameLog,season={YEAR})"
        })
    except Exception:
        return []

    people = data.get("people", [])
    if not people:
        return []

    for group in people[0].get("stats", []):
        if group.get("type", {}).get("displayName") == "gameLog":
            splits = group.get("splits", [])
            return sorted(splits, key=lambda x: x.get("date", ""), reverse=True)
    return []


def summarize_recent_hitting(name: str, trend_games: int = 10):
    player_id = get_player_id(name)
    if not player_id:
        return {
            "avg": None,
            "ops": None,
            "hr": 0,
            "sb": 0,
            "r": 0,
            "rbi": 0,
            "games": 0,
            "trend": "UNKNOWN",
        }

    logs = get_hitter_game_log(player_id)[:trend_games]
    if not logs:
        return {
            "avg": None,
            "ops": None,
            "hr": 0,
            "sb": 0,
            "r": 0,
            "rbi": 0,
            "games": 0,
            "trend": "UNKNOWN",
        }

    at_bats = 0
    hits = 0
    hr = 0
    sb = 0
    runs = 0
    rbi = 0
    ops_values = []

    for g in logs:
        s = g.get("stat", {})
        at_bats += int(s.get("atBats", 0) or 0)
        hits += int(s.get("hits", 0) or 0)
        hr += int(s.get("homeRuns", 0) or 0)
        sb += int(s.get("stolenBases", 0) or 0)
        runs += int(s.get("runs", 0) or 0)
        rbi += int(s.get("rbi", 0) or 0)
        try:
            game_ops = float(s.get("ops", 0) or 0)
            if game_ops > 0:
                ops_values.append(game_ops)
        except Exception:
            pass

    avg = round(hits / at_bats, 3) if at_bats else None
    ops = round(mean(ops_values), 3) if ops_values else None

    score = 0
    if avg is not None:
        if avg >= 0.320:
            score += 2
        elif avg >= 0.275:
            score += 1
        elif avg < 0.220:
            score -= 2
        elif avg < 0.245:
            score -= 1

    if ops is not None:
        if ops >= 0.950:
            score += 2
        elif ops >= 0.800:
            score += 1
        elif ops < 0.650:
            score -= 2
        elif ops < 0.720:
            score -= 1

    if hr >= 3:
        score += 1
    if sb >= 2:
        score += 1

    if score >= 4:
        trend = "HOT"
    elif score >= 2:
        trend = "WARM"
    elif score <= -3:
        trend = "COLD"
    else:
        trend = "NEUTRAL"

    return {
        "avg": avg,
        "ops": ops,
        "hr": hr,
        "sb": sb,
        "r": runs,
        "rbi": rbi,
        "games": len(logs),
        "trend": trend,
    }


def get_roster_hitters(team, all_hitters=False):
    hitters = []
    seen = set()

    for p in team.roster:
        name = getattr(p, "name", "")
        if not name:
            continue

        pos = getattr(p, "position", "") or ""
        eligible = set(getattr(p, "eligibleSlots", []) or [])
        normalized_slots = {str(x) for x in eligible}

        is_hitter = pos in HITTER_POSITIONS or any(slot in HITTER_POSITIONS for slot in normalized_slots)
        if not is_hitter:
            continue

        if not all_hitters:
            slot = str(getattr(p, "slot_position", "") or getattr(p, "slotPosition", "") or "")
            if slot in {"BE", "IL", "IR"}:
                continue

        key = normalize_name(name)
        if key in seen:
            continue
        seen.add(key)
        hitters.append(p)

    return hitters


def get_rank(rankings, player_name):
    key = normalize_name(player_name)
    if key in rankings:
        return rankings[key][1]

    alt = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", key)
    alt = " ".join(alt.split())
    if alt in rankings:
        return rankings[alt][1]

    return None


def build_recommendation(redraft_rank, dynasty_rank, trend):
    if redraft_rank is not None and redraft_rank <= 15:
        if dynasty_rank is not None and dynasty_rank <= 40:
            return "AUTO-START / BUILD AROUND"
        return "AUTO-START"

    if redraft_rank is not None and redraft_rank <= 40:
        return "START"

    if redraft_rank is not None and redraft_rank <= 80:
        if trend == "HOT":
            return "START"
        if trend == "COLD":
            return "HOLD"
        return "HOLD / MATCHUP START"

    if redraft_rank is not None and redraft_rank <= 150:
        if trend == "HOT":
            return "BENCH / STREAM"
        return "BENCH / DEPTH"

    if dynasty_rank is not None and dynasty_rank <= 120:
        return "HOLD / DYNASTY VALUE"

    if trend == "HOT":
        return "STREAM / WATCHLIST"

    return "SHOP / REPLACE"


def main():
    args = parse_args()

    print("Fetching Pitcher List hitter rankings...")
    try:
        redraft = scrape_ranked_players(TOP_300_URL, 300)
    except Exception as e:
        print(f"[warning] Could not load Top 300 hitters: {e}")
        redraft = {}

    try:
        dynasty = scrape_ranked_players(DYNASTY_400_URL, 400)
    except Exception as e:
        print(f"[warning] Could not load Top 400 dynasty rankings: {e}")
        dynasty = {}

    print(f"Loaded {len(redraft)} redraft hitters and {len(dynasty)} dynasty players from Pitcher List.\n")

    league = get_league(args)

    if args.team_id is not None:
        if args.team_id < 1 or args.team_id > len(league.teams):
            sys.exit(f"[error] team-id must be between 1 and {len(league.teams)}")
        team = league.teams[args.team_id - 1]
    else:
        team = league.teams[0]

    hitters = get_roster_hitters(team, all_hitters=args.all_hitters)

    divider = "─" * 92
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {league.settings.name}")
    print(f"🧢  Team: {team.team_name}")
    print(f"⚾  Evaluating {'all roster hitters' if args.all_hitters else 'current fielding hitters'}: {len(hitters)}")
    print(divider)

    if not hitters:
        print("No hitters found on the selected roster view.")
        return

    results = []
    for p in hitters:
        name = p.name
        redraft_rank = get_rank(redraft, name)
        dynasty_rank = get_rank(dynasty, name)
        trend = summarize_recent_hitting(name, args.trend_games)
        action = build_recommendation(redraft_rank, dynasty_rank, trend["trend"])
        results.append((p, redraft_rank, dynasty_rank, trend, action))

    def sort_key(row):
        _, redraft_rank, dynasty_rank, trend, _ = row
        rr = redraft_rank if redraft_rank is not None else 9999
        dr = dynasty_rank if dynasty_rank is not None else 9999
        t = {"HOT": 0, "WARM": 1, "NEUTRAL": 2, "COLD": 3, "UNKNOWN": 4}.get(trend["trend"], 5)
        return (rr, dr, t)

    for p, redraft_rank, dynasty_rank, trend, action in sorted(results, key=sort_key):
        team_abbr = getattr(p, 'proTeam', 'N/A') or 'N/A'
        slot = str(getattr(p, 'slot_position', '') or getattr(p, 'slotPosition', '') or '')
        avg = f"{trend['avg']:.3f}" if trend["avg"] is not None else "N/A"
        ops = f"{trend['ops']:.3f}" if trend["ops"] is not None else "N/A"
        print(f"{p.name}  |  {team_abbr}  |  Slot: {slot or 'N/A'}")
        print(f"  Redraft Rank: {redraft_rank or 'NR'}   Dynasty Rank: {dynasty_rank or 'NR'}")
        print(
            f"  Last {trend['games']} G: AVG {avg} | OPS {ops} | HR {trend['hr']} | RBI {trend['rbi']} | R {trend['r']} | SB {trend['sb']} | Trend: {trend['trend']}"
        )
        print(f"  Recommendation: {action}")
        print(f"  {'·' * 84}")

    print("Legend: START/HOLD = keep active, HOLD = roster comfortably, BENCH/STREAM = matchup/flex only, SHOP/REPLACE = easiest upgrade spot")
    print(f"Sources: {TOP_300_URL} | {DYNASTY_400_URL}")
    print(divider)


if __name__ == "__main__":
    main()
