from __future__ import annotations

from datetime import date
from difflib import get_close_matches

from collectors.espn import build_context, get_all_roster_pitchers, get_free_agent_pitchers, get_roster_players, get_team
from collectors.espn_keeper_cost import KeeperCostEntry, scrape_espn_keeper_cost
from collectors.mlb_stats import get_pitcher_stats, get_player_id, get_todays_probable_starters
from collectors.pitcherlist import scrape_sp_streamer_tiers
from engines.pitcher_engine import streamer_recommendation
from utils.config import AppConfig
from utils.names import normalize_name

import statsapi

_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}


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


def _serialize_pitcher_row(
    player,
    rank,
    position_rank: int | None = None,
    keeper_cost: dict[str, KeeperCostEntry] | None = None,
) -> dict:
    tier = rank.tier if rank else "Not Ranked"
    rec = streamer_recommendation(tier)
    season_record, last_ten, last_two = get_pitcher_stats(player.name)
    resolved_rank = rank.rank if rank and rank.rank else position_rank
    keeper_entry = (keeper_cost or {}).get(player.normalized_name)
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
        "keeper_drafted_round": keeper_entry.drafted_round if keeper_entry else None,
        "keeper_drafted_round_pick": keeper_entry.drafted_round_pick if keeper_entry else None,
        "keeper_projected_round": keeper_entry.projected_keeper_round if keeper_entry else None,
        "keeper_projected_pick": keeper_entry.projected_keeper_overall_pick if keeper_entry else None,
        "recommendation": {
            "action": rec.action,
            "reason": rec.reason,
            "score": rec.score,
        },
        "season_record": season_record,
        "last_ten_record": last_ten,
        "last_two_starts": last_two,
    }


def _as_float(value) -> float | None:
    try:
        if value in {None, "", "-.--"}:
            return None
        return float(value)
    except Exception:
        return None


def _as_int(value) -> int | None:
    try:
        if value in {None, ""}:
            return None
        return int(value)
    except Exception:
        return None


def _fetch_pitcher_season_metrics(name: str, season: int) -> dict:
    player_id = get_player_id(name, prefer_pitcher=True)
    if not player_id:
        return {"era": None, "k": None, "wins": None, "losses": None, "ip": None}

    try:
        payload = statsapi.player_stat_data(player_id, group="pitching", type="season", season=season)
        stat_groups = payload.get("stats", [])
        season_stats = stat_groups[0].get("stats", {}) if stat_groups else {}
    except Exception:
        season_stats = {}

    return {
        "era": _as_float(season_stats.get("era")),
        "k": _as_int(season_stats.get("strikeOuts")),
        "wins": _as_int(season_stats.get("wins")),
        "losses": _as_int(season_stats.get("losses")),
        "ip": season_stats.get("inningsPitched"),
    }


def _assign_rank(rows: list[dict], field: str, *, descending: bool) -> None:
    present = [row for row in rows if row.get(field) is not None]
    present.sort(key=lambda row: row[field], reverse=descending)
    rank = 1
    for row in present:
        row[f"{field}_rank"] = rank
        rank += 1
    for row in rows:
        row.setdefault(f"{field}_rank", None)


def _rank_to_score(rank: int | None, total: int) -> float:
    if rank is None or total <= 0:
        return 0.0
    return ((total - rank + 1) / total) * 100.0


def _lineup_slot(player) -> str:
    raw = getattr(player, "espn_raw", None)
    slot = (
        getattr(raw, "slot_position", None)
        or getattr(raw, "slotPosition", None)
        or getattr(raw, "lineupSlot", None)
        or ""
    )
    return str(slot).upper()


def _is_bench_slot(slot: str) -> bool:
    return slot in _BENCH_SLOTS or not slot


def _start_eval_sort_key(row: dict) -> tuple[float, int, float, str]:
    rec = row.get("recommendation") or {}
    return (
        float(rec.get("score") or 0.0),
        -int(row.get("streamer_rank") or 9999),
        float(row.get("percent_owned") or 0.0),
        str(row.get("name") or ""),
    )


def _streamer_rank_sort_key(row: dict) -> tuple[int, float, str]:
    return (
        int(row.get("streamer_rank") or 9999),
        -float(row.get("recommendation", {}).get("score") or 0.0),
        str(row.get("name") or ""),
    )


def _select_top_streamer(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    return min(rows, key=_streamer_rank_sort_key)


def get_team_pitcher_evaluation(
    league_id: int | None = None,
    team_id: int | None = None,
    year: int | None = None,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        team_id=team_id or AppConfig().team_id,
        year=year or AppConfig().year,
    )

    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)
    pitchers = get_roster_players(context, team_id=team.team_id, player_type="pitchers")
    keeper_cost = scrape_espn_keeper_cost(context)

    rows: list[dict] = []
    for player in pitchers:
        season_stats = _fetch_pitcher_season_metrics(player.name, season=config.year)
        keeper_entry = keeper_cost.get(player.normalized_name)
        rows.append(
            {
                "name": player.name,
                "normalized_name": player.normalized_name,
                "mlb_team": player.mlb_team,
                "positions": player.positions,
                "percent_owned": player.percent_owned,
                "era": season_stats["era"],
                "k": season_stats["k"],
                "wins": season_stats["wins"],
                "losses": season_stats["losses"],
                "ip": season_stats["ip"],
                "keeper_round": keeper_entry.projected_keeper_round if keeper_entry else None,
                "keeper_pick": keeper_entry.projected_keeper_overall_pick if keeper_entry else None,
                "drafted_round": keeper_entry.drafted_round if keeper_entry else None,
                "drafted_round_pick": keeper_entry.drafted_round_pick if keeper_entry else None,
            }
        )

    _assign_rank(rows, "era", descending=False)
    _assign_rank(rows, "k", descending=True)
    _assign_rank(rows, "keeper_pick", descending=False)

    total = len(rows)
    for row in rows:
        era_score = _rank_to_score(row["era_rank"], total)
        k_score = _rank_to_score(row["k_rank"], total)
        keeper_score = _rank_to_score(row["keeper_pick_rank"], total)
        row["composite_score"] = round((era_score + k_score + keeper_score) / 3.0, 1)

    rows.sort(
        key=lambda row: (
            -row["composite_score"],
            (row["era_rank"] or 9999),
            (row["k_rank"] or 9999),
            (row["keeper_pick_rank"] or 9999),
            row["name"],
        )
    )
    for idx, row in enumerate(rows, start=1):
        row["overall_rank"] = idx

    return {
        "generated_on": date.today().isoformat(),
        "league": context.league.settings.name,
        "team": getattr(team, "team_name", None),
        "formula": "ERA rank (lower better) + K rank (higher better) + Keeper-cost rank (lower pick better)",
        "count": len(rows),
        "rows": rows,
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
    keeper_cost = scrape_espn_keeper_cost(context)

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
        payload["row"] = _serialize_pitcher_row(
            row_player,
            rank,
            position_rank=streamer_positions.get(matched_key),
            keeper_cost=keeper_cost,
        )
        return payload

    rows = []
    for player in starters_today:
        rank = streamer_ranks.get(player.normalized_name)
        rows.append(
            _serialize_pitcher_row(
                player,
                rank,
                position_rank=streamer_positions.get(player.normalized_name),
                keeper_cost=keeper_cost,
            )
        )
    payload["rows"] = rows
    payload["count"] = len(rows)
    return payload


def get_pitcher_start_evaluation(
    team_id: int | None = None,
    league_id: int | None = None,
    year: int | None = None,
    for_date: date | None = None,
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        team_id=team_id or AppConfig().team_id,
        year=year or AppConfig().year,
    )
    target_date = for_date or date.today()

    context = build_context(config)
    team = get_team(context, team_id=config.team_id or None)
    roster_pitchers = get_roster_players(context, team_id=team.team_id, player_type="pitchers")

    probable_starters = {normalize_name(name) for name in get_todays_probable_starters(for_date=target_date)}
    streamer_url, streamer_ranks = scrape_sp_streamer_tiers()
    streamer_positions = {name: idx for idx, name in enumerate(streamer_ranks.keys(), start=1)}
    keeper_cost = scrape_espn_keeper_cost(context)

    probable_rows: list[dict] = []
    for player in roster_pitchers:
        if player.normalized_name not in probable_starters:
            continue
        rank = streamer_ranks.get(player.normalized_name)
        row = _serialize_pitcher_row(
            player,
            rank,
            position_rank=streamer_positions.get(player.normalized_name),
            keeper_cost=keeper_cost,
        )
        slot = _lineup_slot(player)
        row["slot"] = slot or "N/A"
        row["is_bench"] = _is_bench_slot(slot)
        row["is_probable_today"] = True
        probable_rows.append(row)

    probable_rows_sorted = sorted(probable_rows, key=_start_eval_sort_key, reverse=True)
    recommended_rows = probable_rows_sorted[:2]
    recommended_keys = {row["normalized_name"] for row in recommended_rows}

    bench_probable_rows = [row for row in probable_rows_sorted if row.get("is_bench")]
    active_non_recommended = sorted(
        [row for row in probable_rows if not row.get("is_bench") and row["normalized_name"] not in recommended_keys],
        key=_start_eval_sort_key,
    )

    suggested_moves: list[str] = []
    for start_row in [row for row in recommended_rows if row.get("is_bench")]:
        if active_non_recommended:
            sit_row = active_non_recommended.pop(0)
            suggested_moves.append(f"START {start_row['name']} (bench) -> SIT {sit_row['name']} ({sit_row['slot']})")
        else:
            suggested_moves.append(f"START {start_row['name']} (bench) -> Move into an open SP/P slot")

    response = {
        "generated_on": target_date.isoformat(),
        "league": context.league.settings.name,
        "team": getattr(team, "team_name", None),
        "source_url": streamer_url,
        "roster_pitcher_count": len(roster_pitchers),
        "probable_roster_count": len(probable_rows),
        "fallback_to_streamers": False,
        "recommended_count": len(recommended_rows),
        "recommended_rows": recommended_rows,
        "bench_probable_rows": bench_probable_rows,
        "suggested_moves": suggested_moves,
        "selected_streamer_row": None,
        "streamer_fallback_rows": None,
    }

    streamers = get_streaming_pitcher_review(
        league_id=config.league_id,
        year=config.year,
        for_date=target_date,
    )
    streamer_rows = streamers.get("rows") or []
    sorted_streamer_rows = sorted(streamer_rows, key=_streamer_rank_sort_key)
    response["selected_streamer_row"] = _select_top_streamer(sorted_streamer_rows)

    if probable_rows:
        return response

    fallback_rows = sorted_streamer_rows[:2]
    response["fallback_to_streamers"] = True
    response["recommended_count"] = len(fallback_rows)
    response["recommended_rows"] = []
    response["bench_probable_rows"] = []
    response["suggested_moves"] = []
    response["streamer_fallback_rows"] = fallback_rows
    return response
