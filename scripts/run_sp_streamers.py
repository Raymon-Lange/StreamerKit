from __future__ import annotations

import argparse
from datetime import date

from collectors.espn import build_context, get_free_agent_pitchers
from collectors.mlb_stats import get_pitcher_stats, get_todays_probable_starters
from collectors.pitcherlist import scrape_sp_streamer_tiers
from engines.pitcher_engine import TIER_EMOJI, streamer_recommendation
from utils.config import AppConfig
from utils.names import normalize_name


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    context = build_context(config)

    probable_starters = get_todays_probable_starters()
    streamer_url, streamer_ranks = scrape_sp_streamer_tiers()
    free_agents = get_free_agent_pitchers(context, size=200, position="SP")

    starters_today = [p for p in free_agents if not probable_starters or p.name in probable_starters]
    starters_today.sort(key=lambda player: -(player.percent_owned or 0.0))

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {context.league.settings.name}")
    print(f"Source: {streamer_url}")
    print(divider)

    for pitcher in starters_today:
        rank = streamer_ranks.get(normalize_name(pitcher.name))
        tier = rank.tier if rank else "Not Ranked"
        rec = streamer_recommendation(tier)
        season_record, last_ten, last_two = get_pitcher_stats(pitcher.name)
        owned = f"{pitcher.percent_owned:.1f}%" if pitcher.percent_owned is not None else "N/A"

        print(f"{TIER_EMOJI.get(tier, '⚪')} {pitcher.name} | {pitcher.mlb_team or 'N/A'} | Owned: {owned}")
        print(f"  Tier: {tier}")
        print(f"  Recommendation: {rec.action}")
        print(f"  Season: {season_record} | Last 10: {last_ten}")
        if last_two:
            for start in last_two:
                print(
                    f"  {start['date']} {start['matchup']} {start['result']} | "
                    f"IP {start['ip']} H {start['h']} R {start['r']} ER {start['er']} "
                    f"BB {start['bb']} K {start['k']} ERA {start['era']}"
                )
        else:
            print("  No starts on record yet this season.")
        print(f"  {'·' * 88}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="List free-agent SPs scheduled to start today in your ESPN fantasy league.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--year", type=int, default=config.year)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
