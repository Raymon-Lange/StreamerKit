"""
SP Streamer Recommender
=======================
Pass in pitcher names — get back:
  • PitcherList streamer tier + recommendation
  • Season W-L record
  • Last 10 starts W-L record
  • Last 2 start box scores (date, opponent, result, IP/H/R/ER/BB/K)

Requirements:
    pip install requests beautifulsoup4 MLB-StatsAPI

Usage:
    python sp_recommender.py "Chad Patrick" "Aaron Nola" "Shane Baz"

    # With a specific PitcherList post URL:
    python sp_recommender.py "Chad Patrick" --url https://pitcherlist.com/...
"""

import sys
import argparse
import re
from datetime import date

import requests
from bs4 import BeautifulSoup
import statsapi

PL_CATEGORY_URL = "https://pitcherlist.com/category/fantasy/starting-pitchers/sp-streamers/"
CURRENT_YEAR    = date.today().year

TIER_ORDER = ["Auto-Start", "Probably Start", "Questionable Start", "Do Not Start"]
TIER_EMOJI = {
    "Auto-Start":        "🟢",
    "Probably Start":    "🟡",
    "Questionable Start":"🟠",
    "Do Not Start":      "🔴",
}
TIER_REC = {
    "Auto-Start":        "PICKUP   — Auto-Start, high-confidence",
    "Probably Start":    "PICKUP   — Probable start, solid option",
    "Questionable Start":"CONSIDER — Questionable, only if desperate",
    "Do Not Start":      "SKIP     — Do Not Start",
}

# ─────────────────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="Look up pitchers on PitcherList and pull their W-L records + recent starts."
    )
    parser.add_argument("players", nargs="+", help='Player names e.g. "Chad Patrick" "Aaron Nola"')
    parser.add_argument("--url", type=str, default=None,
                        help="Override PitcherList post URL (default: auto-detect latest)")
    return parser.parse_args()


# ── PitcherList ───────────────────────────────────────────────────────────────

def normalize_name(name):
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def get_latest_pl_url():
    resp = requests.get(PL_CATEGORY_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "/starting-pitcher-streamer-ranks" in a["href"]:
            return a["href"]
    raise ValueError("Could not find latest SP Streamers post.")


def scrape_pl_tiers(url):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pitchers = {}
    current_tier = None
    article = (
        soup.find("article")
        or soup.find("div", class_=re.compile("entry|content|post"))
        or soup
    )

    for elem in article.find_all(["h2", "h3", "h4", "strong", "b", "p", "li", "td"]):
        text = elem.get_text(strip=True)
        for tier in TIER_ORDER:
            if tier.lower() in text.lower() and len(text) < 60:
                current_tier = tier
                break
        if current_tier:
            for a in elem.find_all("a", href=True):
                if "pitcherlist.com/player/" in a["href"]:
                    name = a.get_text(strip=True)
                    if name:
                        key = normalize_name(name)
                        if key not in pitchers:
                            pitchers[key] = (name, current_tier)

    return pitchers


# ── MLB Stats API ─────────────────────────────────────────────────────────────

def get_player_id(name):
    """Look up MLB player ID by name."""
    results = statsapi.lookup_player(name)
    if not results:
        return None
    for p in results:
        if p.get("primaryPosition", {}).get("abbreviation", "") in ("SP", "P", "RP"):
            return p["id"]
    return results[0]["id"]


def get_season_record(player_id):
    """Get season W-L from MLB Stats API."""
    try:
        data = statsapi.player_stat_data(
            player_id,
            group="pitching",
            type="season",
            season=CURRENT_YEAR
        )
        stats = data.get("stats", [])
        if not stats:
            return "0-0"
        s = stats[0].get("stats", {})
        return f"{s.get('wins', 0)}-{s.get('losses', 0)}"
    except Exception:
        return "N/A"


def get_game_log(player_id):
    """Return game log splits for the current season, sorted newest first."""
    try:
        data = statsapi.get("people", {
            "personIds": player_id,
            "hydrate": f"stats(group=pitching,type=gameLog,season={CURRENT_YEAR})"
        })
        people = data.get("people", [])
        if not people:
            return []
        for group in people[0].get("stats", []):
            if group.get("type", {}).get("displayName") == "gameLog":
                splits = group.get("splits", [])
                return sorted(splits, key=lambda x: x.get("date", ""), reverse=True)
        return []
    except Exception:
        return []


def get_last_10_record(game_log):
    """Compute W-L over the last 10 starts from a pre-fetched game log."""
    starts = game_log[:10]
    if not starts:
        return "0-0 (0 GS)"
    wins   = sum(1 for g in starts if g.get("stat", {}).get("wins", 0) > 0)
    losses = sum(1 for g in starts if g.get("stat", {}).get("losses", 0) > 0)
    return f"{wins}-{losses} (last {len(starts)} GS)"


def get_last_2_boxscores(game_log):
    """
    Return a list of dicts for the last 2 starts:
      date, matchup, result, IP, H, R, ER, BB, K, ERA
    """
    rows = []
    for g in game_log[:2]:
        s       = g.get("stat", {})
        opp     = g.get("opponent", {}).get("abbreviation", "???")
        is_home = g.get("isHome", True)
        matchup = f"vs {opp}" if is_home else f"@ {opp}"

        if s.get("wins", 0):
            result = "W"
        elif s.get("losses", 0):
            result = "L"
        else:
            result = "ND"

        rows.append({
            "date":    g.get("date", "N/A"),
            "matchup": matchup,
            "result":  result,
            "ip":      s.get("inningsPitched", "0.0"),
            "h":       s.get("hits", 0),
            "r":       s.get("runs", 0),
            "er":      s.get("earnedRuns", 0),
            "bb":      s.get("baseOnBalls", 0),
            "k":       s.get("strikeOuts", 0),
            "era":     s.get("era", "-.--"),
        })
    return rows


def get_pitcher_stats(name):
    """Return (season_record, last_10_record, last_2_boxscores) for a pitcher."""
    player_id = get_player_id(name)
    if not player_id:
        return "N/A", "N/A", []
    season   = get_season_record(player_id)
    game_log = get_game_log(player_id)
    last_10  = get_last_10_record(game_log)
    last_2   = get_last_2_boxscores(game_log)
    return season, last_10, last_2


# ── Main ──────────────────────────────────────────────────────────────────────

def print_boxscore_row(start, indent="    "):
    result_color = {"W": "✅", "L": "❌", "ND": "➖"}.get(start["result"], "➖")
    print(
        f"{indent}{start['date']}  {start['matchup']:<8}  {result_color} {start['result']}"
        f"  IP:{start['ip']}  H:{start['h']}  R:{start['r']}  ER:{start['er']}"
        f"  BB:{start['bb']}  K:{start['k']}  ERA:{start['era']}"
    )


def main():
    args = parse_args()

    divider     = "─" * 72
    sub_divider = "  " + "·" * 68

    print(divider)
    print("  SP Streamer Recommender")
    print(f"  📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(divider)

    # 1. Scrape PitcherList
    print("  Fetching PitcherList rankings...")
    try:
        pl_url      = args.url or get_latest_pl_url()
        pl_pitchers = scrape_pl_tiers(pl_url)
    except Exception as e:
        sys.exit(f"[error] PitcherList scrape failed: {e}")

    if not pl_pitchers:
        sys.exit("[error] No pitchers found. Page structure may have changed.")

    print(f"  Found {len(pl_pitchers)} ranked pitchers.\n")

    not_found = []

    for name in args.players:
        key = normalize_name(name)

        # PitcherList tier
        if key in pl_pitchers:
            _, tier = pl_pitchers[key]
            emoji = TIER_EMOJI[tier]
            rec   = TIER_REC[tier]
        else:
            tier  = "Not Ranked"
            emoji = "⚪"
            rec   = "Not in today's PitcherList post"
            not_found.append(name)

        # MLB stats
        print(f"  Fetching stats for {name}...", end="\r")
        season, last_10, last_2 = get_pitcher_stats(name)

        # ── Player header line ──
        print(f"  {emoji} {name:<24} Season: {season:<6}  Last 10: {last_10}")
        print(f"     {tier:<30} {rec}")

        # ── Last 2 starts box scores ──
        if last_2:
            print(f"     Last 2 starts:")
            print(f"     {'Date':<12} {'Opp':<10} {'Res':<5} {'IP':<6} {'H':<4} {'R':<4} {'ER':<4} {'BB':<4} {'K':<4} ERA")
            print(f"     {'─'*12} {'─'*10} {'─'*5} {'─'*6} {'─'*4} {'─'*4} {'─'*4} {'─'*4} {'─'*4} {'─'*6}")
            for start in last_2:
                result_icon = {"W": "✅", "L": "❌", "ND": "➖"}.get(start["result"], "➖")
                print(
                    f"     {start['date']:<12} {start['matchup']:<10} "
                    f"{result_icon} {start['result']:<3}  "
                    f"{str(start['ip']):<6} {str(start['h']):<4} {str(start['r']):<4} "
                    f"{str(start['er']):<4} {str(start['bb']):<4} {str(start['k']):<4} "
                    f"{start['era']}"
                )
        else:
            print(f"     No starts on record yet this season.")

        print(sub_divider)

    if not_found:
        print(f"\n  ⚠️  Not ranked on PitcherList today: {', '.join(not_found)}")

    print(f"\n  Source: {pl_url}")
    print(divider)


if __name__ == "__main__":
    main()
