from __future__ import annotations

import argparse
from difflib import get_close_matches
from datetime import date
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from collectors.espn import build_context, get_free_agent_pitchers
from collectors.mlb_stats import get_pitcher_stats, get_todays_probable_starters
from collectors.pitcherlist import scrape_sp_streamer_tiers
from engines.pitcher_engine import TIER_EMOJI, streamer_recommendation
from utils.config import AppConfig
from utils.names import normalize_name


def _find_pitcher_match(
    query: str,
    starters_today,
    streamer_ranks,
) -> tuple[str | None, object | None, list[str]]:
    query_key = normalize_name(query)
    starters_by_key = {normalize_name(p.name): p for p in starters_today}
    if query_key in starters_by_key or query_key in streamer_ranks:
        return query_key, starters_by_key.get(query_key), []

    all_names = {}
    for starter in starters_today:
        all_names.setdefault(normalize_name(starter.name), starter.name)
    for key in streamer_ranks:
        all_names.setdefault(key, key.title())

    matches = get_close_matches(query_key, all_names.keys(), n=3, cutoff=0.72)
    suggestions = [all_names[m] for m in matches]
    return None, None, suggestions


def _print_pitcher_lookup(pitcher, rank, query: str, position_rank: int | None = None) -> None:
    resolved_name = pitcher.name if pitcher else query
    tier = rank.tier if rank else "Not Ranked"
    rec = streamer_recommendation(tier)
    resolved_rank = rank.rank if rank and rank.rank else position_rank
    rank_text = f"#{resolved_rank}" if resolved_rank else "N/A"
    owned = f"{pitcher.percent_owned:.1f}%" if pitcher and pitcher.percent_owned is not None else "N/A"
    team = pitcher.mlb_team if pitcher and pitcher.mlb_team else "N/A"
    season_record, last_ten, last_two = get_pitcher_stats(resolved_name)

    print(f"{TIER_EMOJI.get(tier, '⚪')} {resolved_name} | {team} | Owned: {owned}")
    print(f"  Streamer Rank: {rank_text}")
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


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    context = build_context(config)

    probable_starters = get_todays_probable_starters()
    streamer_url, streamer_ranks = scrape_sp_streamer_tiers()
    streamer_positions = {name: idx for idx, name in enumerate(streamer_ranks.keys(), start=1)}
    free_agents = get_free_agent_pitchers(context, size=200, position="SP")
    pitcher_query = getattr(args, "pitcher", None)

    starters_today = [p for p in free_agents if not probable_starters or p.name in probable_starters]
    starters_today.sort(key=lambda player: -(player.percent_owned or 0.0))

    divider = "─" * 96
    print(divider)
    print(f"📅  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"🏟   League: {context.league.settings.name}")
    print(f"Source: {streamer_url}")
    print(divider)

    if pitcher_query:
        matched_key, matched_pitcher, suggestions = _find_pitcher_match(pitcher_query, starters_today, streamer_ranks)
        if not matched_key:
            print(f"No pitcher match found for: {pitcher_query}")
            if suggestions:
                print("Did you mean:")
                for name in suggestions:
                    print(f"  - {name}")
            return

        rank = streamer_ranks.get(matched_key)
        _print_pitcher_lookup(
            matched_pitcher,
            rank,
            query=pitcher_query,
            position_rank=streamer_positions.get(matched_key),
        )
        return

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
    parser.add_argument("--pitcher", type=str, default=None, help="Optional pitcher name to lookup directly.")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
