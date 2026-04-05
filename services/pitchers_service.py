from __future__ import annotations

from datetime import date
from difflib import get_close_matches

from collectors.espn import build_context, get_all_roster_pitchers, get_free_agent_pitchers
from collectors.mlb_stats import get_pitcher_stats, get_todays_probable_starters
from collectors.pitcherlist import scrape_sp_streamer_tiers
from engines.pitcher_engine import streamer_recommendation
from utils.config import AppConfig
from utils.names import normalize_name


def _find_pitcher_match(
    query: str,
    starters_today: list,
    streamer_ranks: dict,
    fallback_players: list | None = None,
) -> tuple[str | None, object | None, list[str]]:
    query_key = normalize_name(query)
    starters_by_key = {normalize_name(player.name): player for player in starters_today}
    fallback_by_key = {normalize_name(player.name): player for player in (fallback_players or [])}

    if query_key in starters_by_key:
        return query_key, starters_by_key.get(query_key), []
    if query_key in fallback_by_key:
        return query_key, fallback_by_key.get(query_key), []
    if query_key in streamer_ranks:
        return query_key, starters_by_key.get(query_key), []

    all_names = {}
    for starter in starters_today:
        all_names.setdefault(normalize_name(starter.name), starter.name)
    for player in fallback_players or []:
        all_names.setdefault(normalize_name(player.name), player.name)
    for key in streamer_ranks:
        all_names.setdefault(key, key.title())
    matches = get_close_matches(query_key, all_names.keys(), n=3, cutoff=0.72)
    return None, None, [all_names[name] for name in matches]


def _serialize_pitcher_row(player, rank, position_rank: int | None = None) -> dict:
    tier = rank.tier if rank else "Not Ranked"
    rec = streamer_recommendation(tier)
    season_record, last_ten, last_two = get_pitcher_stats(player.name)
    resolved_rank = rank.rank if rank and rank.rank else position_rank
    return {
        "name": player.name,
        "normalized_name": player.normalized_name,
        "mlb_team": player.mlb_team,
        "positions": player.positions,
        "percent_owned": player.percent_owned,
        "streamer_rank": resolved_rank,
        "tier": tier,
        "opponent_team": rank.opponent_team if rank else None,
        "opponent_score": rank.opponent_score if rank else None,
        "recommendation": {
            "action": rec.action,
            "reason": rec.reason,
            "score": rec.score,
        },
        "season_record": season_record,
        "last_ten_record": last_ten,
        "last_two_starts": last_two,
    }


def get_streaming_pitcher_review(
    league_id: int | None = None,
    year: int | None = None,
    pitcher: str | None = None,
    for_date: date | None = None,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        year=year or AppConfig().year,
    )
    context = build_context(config)
    probable_starters = get_todays_probable_starters(for_date=for_date)
    streamer_url, streamer_ranks = scrape_sp_streamer_tiers()
    streamer_positions = {name: idx for idx, name in enumerate(streamer_ranks.keys(), start=1)}

    free_agents = get_free_agent_pitchers(context, size=200, position="SP")
    roster_pitchers = get_all_roster_pitchers(context)
    starters_today = [player for player in free_agents if not probable_starters or player.name in probable_starters]
    starters_today.sort(key=lambda player: -(player.percent_owned or 0.0))

    all_pitchers_by_key = {player.normalized_name: player for player in roster_pitchers}
    for player in free_agents:
        all_pitchers_by_key[player.normalized_name] = player

    payload = {
        "generated_on": (for_date or date.today()).isoformat(),
        "league": context.league.settings.name,
        "source_url": streamer_url,
    }

    if pitcher:
        matched_key, matched_player, suggestions = _find_pitcher_match(
            pitcher,
            starters_today,
            streamer_ranks,
            fallback_players=list(all_pitchers_by_key.values()),
        )
        if not matched_key:
            payload["query"] = pitcher
            payload["found"] = False
            payload["suggestions"] = suggestions
            return payload

        row_player = matched_player
        if row_player is None:
            for player_row in starters_today:
                if player_row.normalized_name == matched_key:
                    row_player = player_row
                    break
        if row_player is None:
            row_player = all_pitchers_by_key.get(matched_key)
        if row_player is None:
            return {
                **payload,
                "query": pitcher,
                "found": False,
                "suggestions": suggestions,
            }
        rank = streamer_ranks.get(matched_key)
        payload["found"] = True
        payload["query"] = pitcher
        payload["row"] = _serialize_pitcher_row(row_player, rank, position_rank=streamer_positions.get(matched_key))
        return payload

    rows = []
    for player in starters_today:
        rank = streamer_ranks.get(player.normalized_name)
        rows.append(_serialize_pitcher_row(player, rank, position_rank=streamer_positions.get(player.normalized_name)))
    payload["rows"] = rows
    payload["count"] = len(rows)
    return payload
