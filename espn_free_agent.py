"""
ESPN Fantasy Baseball - Available Starting Pitchers Today
=========================================================
Lists all free agent (unrostered) starting pitchers in your
ESPN fantasy baseball league who are scheduled to start today.
Cross-references with PitcherList SP Streamer tiers and shows
last 2 start box scores for each player.

Requirements:
    pip install espn-api requests beautifulsoup4 MLB-StatsAPI

Setup:
    You need two cookies from your ESPN session:
      - espn_s2
      - SWID

    How to get them:
      1. Log into ESPN in your browser
      2. Open DevTools (F12) → Application → Cookies → https://www.espn.com
      3. Copy the values for 'espn_s2' and 'SWID'

    Set them as environment variables:
        export ESPN_S2="your_espn_s2_cookie"
        export ESPN_SWID="{your-swid-cookie}"

    Both espn_free_agent.py and sp_recommender.py must be in the same folder.

Usage:
    python espn_free_agent.py
    python espn_free_agent.py --league-id <id>
"""

import os
import sys
import argparse
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

# Import sp_recommender from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sp_recommender import (
    get_latest_pl_url,
    scrape_pl_tiers,
    normalize_name,
    get_pitcher_stats,
    TIER_EMOJI,
    TIER_REC,
)

# ── Configuration ─────────────────────────────────────────────────────────────

LEAGUE_ID = int(os.getenv("LEAGUE_ID", 0))
YEAR      = date.today().year

ESPN_S2   = os.getenv("ESPN_S2",   "")
ESPN_SWID = os.getenv("ESPN_SWID", "")

# ─────────────────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="List free agent SPs scheduled to start today in your ESPN fantasy league."
    )
    parser.add_argument("--league-id", type=int, default=LEAGUE_ID, help="ESPN fantasy league ID")
    parser.add_argument("--year",      type=int, default=YEAR,      help="Season year")
    return parser.parse_args()


def get_todays_probable_starters():
    """Fetch today's MLB probable starters from the ESPN scoreboard API."""
    import requests
    today = date.today().strftime("%Y%m%d")
    url   = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[warning] Could not fetch today's MLB schedule: {e}")
        return set()

    starters = set()
    for event in data.get("events", []):
        for competition in event.get("competitions", []):
            for competitor in competition.get("competitors", []):
                for p in competitor.get("probables", []):
                    athlete = p.get("athlete", {})
                    name = athlete.get("displayName") or athlete.get("fullName")
                    if name:
                        starters.add(name)

    return starters


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


def print_player_card(p, pl_pitchers):
    """Print a full player card with PitcherList tier, records, and last 2 starts."""
    owned = f"{p.percent_owned:.1f}%" if p.percent_owned is not None else "N/A"
    team  = getattr(p, 'proTeam', 'N/A') or 'N/A'

    # PitcherList tier
    key = normalize_name(p.name)
    if key in pl_pitchers:
        _, tier = pl_pitchers[key]
        emoji = TIER_EMOJI[tier]
        rec   = TIER_REC[tier]
    else:
        tier  = "Not Ranked"
        emoji = "⚪"
        rec   = "Not in today's PitcherList post"

    # MLB stats + last 2 starts
    print(f"  Fetching stats for {p.name}...", end="\r")
    season, last_10, last_2 = get_pitcher_stats(p.name)

    # Header line
    print(f"  {emoji} {p.name:<24} {team:<6} {owned:>7}   Season: {season}  Last 10: {last_10}")
    print(f"     {tier}  —  {rec}")

    # Last 2 starts box score
    if last_2:
        print(f"     {'Date':<12} {'Opp':<10} {'Res':<5} {'IP':<6} {'H':<4} {'R':<4} {'ER':<4} {'BB':<4} {'K':<4} ERA")
        print(f"     {'─'*12} {'─'*10} {'─'*5} {'─'*6} {'─'*4} {'─'*4} {'─'*4} {'─'*4} {'─'*4} {'─'*6}")
        for s in last_2:
            icon = {"W": "✅", "L": "❌", "ND": "➖"}.get(s["result"], "➖")
            print(
                f"     {s['date']:<12} {s['matchup']:<10} {icon} {s['result']:<3}  "
                f"{str(s['ip']):<6} {str(s['h']):<4} {str(s['r']):<4} "
                f"{str(s['er']):<4} {str(s['bb']):<4} {str(s['k']):<4} {s['era']}"
            )
    else:
        print(f"     No starts on record yet this season.")

    print(f"  {'·' * 54}")


def main():
    args = parse_args()

    # 1. Fetch today's probable MLB starters
    print("Fetching today's MLB probable starters...")
    todays_starters = get_todays_probable_starters()
    if todays_starters:
        print(f"  Found {len(todays_starters)} probable starters on today's slate.")
    else:
        print("  [warning] No probable starters found — listing all available free agent SPs instead.")

    # 2. Connect to ESPN league
    league = get_league(args)
    print(f"  Connected: {league.settings.name}\n")

    # 3. Fetch PitcherList tiers
    print("  Fetching PitcherList rankings...")
    try:
        pl_url      = get_latest_pl_url()
        pl_pitchers = scrape_pl_tiers(pl_url)
        print(f"  Found {len(pl_pitchers)} ranked pitchers on PitcherList.\n")
    except Exception as e:
        print(f"  [warning] Could not fetch PitcherList rankings: {e}")
        pl_pitchers = {}

    # 4. Fetch free agents
    try:
        free_agents = league.free_agents(size=200, position="SP")
    except Exception as e:
        sys.exit(f"[error] Could not fetch free agents: {e}")

    # 5. Split into starting today vs. not
    starting_today = []
    not_starting   = []

    for player in free_agents:
        name = player.name
        if not todays_starters or name in todays_starters:
            starting_today.append(player)
        else:
            not_starting.append(player)

    # 6. Print results
    divider = "─" * 60
    print(divider)
    print(f"  📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"  🏟   League: {league.settings.name}")
    print(divider)

    if starting_today:
        print(f"\n✅  FREE AGENT SPs STARTING TODAY ({len(starting_today)} found)\n")
        for p in sorted(starting_today, key=lambda x: -(x.percent_owned or 0)):
            print_player_card(p, pl_pitchers)
    else:
        print("\n⚠️   No free agent SPs are scheduled to start today.")

    # 7. Show other available SPs (top 5, no box scores)
    if not_starting:
        print(f"\n💤  OTHER FREE AGENT SPs (not starting today) — top 5 by % owned\n")
        top = sorted(not_starting, key=lambda x: -(x.percent_owned or 0))[:5]
        for p in top:
            owned = f"{p.percent_owned:.1f}%" if p.percent_owned is not None else "N/A"
            team  = getattr(p, 'proTeam', 'N/A') or 'N/A'
            key   = normalize_name(p.name)
            if key in pl_pitchers:
                _, tier = pl_pitchers[key]
                emoji = TIER_EMOJI[tier]
            else:
                emoji = "⚪"
            print(f"  {emoji} {p.name:<28} {team:<6} {owned:>7}")

    print(f"\n  Source: {pl_url if pl_pitchers else 'N/A'}")
    print(divider)


if __name__ == "__main__":
    main()
