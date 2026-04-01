from __future__ import annotations

from datetime import datetime, timezone

from collectors.espn import build_context, get_free_agent_hitters, get_free_agent_pitchers, get_roster_players
from collectors.espn_activity import get_recent_drops
from collectors.espn_dynasty import scrape_espn_dynasty_hitters
from collectors.mlb_stats import get_pitcher_stats, summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_sp_streamer_tiers, scrape_top_hitters
from engines.hitter_engine import evaluate_free_agent_hitter, evaluate_roster_hitter
from engines.pitcher_engine import streamer_recommendation
from utils.config import AppConfig

REQUIRED_SINGLETON_HITTER_SLOTS = ("C", "1B", "2B", "3B", "SS")


def _is_pitcher_positions(positions: list[str]) -> bool:
    return bool({"P", "SP", "RP"} & {pos.upper() for pos in positions})


def _eligible_hitter_slots(player) -> set[str]:
    return {pos.upper() for pos in (player.positions or [])}


def _is_safe_drop(candidate_player, add_player, slot_counts: dict[str, int]) -> bool:
    candidate_slots = _eligible_hitter_slots(candidate_player)
    add_slots = _eligible_hitter_slots(add_player)
    for slot in REQUIRED_SINGLETON_HITTER_SLOTS:
        if slot in candidate_slots and slot_counts.get(slot, 0) <= 1 and slot not in add_slots:
            return False
    return True


def _recommended_drop_for_hitter(add_player, roster_hitter_rows: list[dict], slot_counts: dict[str, int]) -> dict | None:
    add_positions = {pos.upper() for pos in (add_player.positions or [])}
    overlap_pool = [
        row for row in roster_hitter_rows
        if add_positions & _eligible_hitter_slots(row["player"])
    ]
    pool = overlap_pool or roster_hitter_rows
    pool = [row for row in pool if _is_safe_drop(row["player"], add_player, slot_counts)]
    if not pool and overlap_pool:
        pool = [row for row in roster_hitter_rows if _is_safe_drop(row["player"], add_player, slot_counts)]
    if not pool:
        return None
    return min(
        pool,
        key=lambda row: (
            row["rec"].score,
            (row["redraft_rank"] or 9999),
            (row["dynasty_rank"] or 9999),
            -(row["player"].percent_owned or 0.0),
        ),
    )


def _serialize_hitter_row(player, trend_games: int, redraft: dict, pl_dynasty: dict, espn_dynasty: dict) -> dict:
    redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
    pl_dynasty_rank = pl_dynasty.get(player.normalized_name).rank if player.normalized_name in pl_dynasty else None
    espn_dynasty_rank = espn_dynasty.get(player.normalized_name).rank if player.normalized_name in espn_dynasty else None
    dynasty_rank = min((rank for rank in (pl_dynasty_rank, espn_dynasty_rank) if rank is not None), default=None)
    trend = summarize_recent_hitting(player.name, trend_games=trend_games)
    rec = evaluate_free_agent_hitter(redraft_rank, dynasty_rank, trend.label)
    return {
        "kind": "H",
        "player": player,
        "redraft_rank": redraft_rank,
        "pl_dynasty_rank": pl_dynasty_rank,
        "espn_dynasty_rank": espn_dynasty_rank,
        "dynasty_rank": dynasty_rank,
        "trend": trend,
        "recommendation": rec,
    }


def _serialize_pitcher_row(player, streamer_ranks: dict) -> dict:
    rank = streamer_ranks.get(player.normalized_name)
    tier = rank.tier if rank else "Not Ranked"
    rec = streamer_recommendation(tier)
    season_record, last_ten, _ = get_pitcher_stats(player.name)
    return {
        "kind": "P",
        "player": player,
        "tier": tier,
        "season_record": season_record,
        "last_ten_record": last_ten,
        "recommendation": rec,
    }


def get_recent_drops_waiver_review(
    league_id: int | None = None,
    year: int | None = None,
    days: int = 2,
    trend_games: int = 10,
    top: int = 25,
    claim_mode: str = "all",
) -> dict:
    config = AppConfig(
        league_id=league_id or AppConfig().league_id,
        year=year or AppConfig().year,
    )
    days = max(1, days)
    claim_mode = (claim_mode or "all").lower()

    context = build_context(config)
    recent_drops = get_recent_drops(context, days=days, page_size=50, max_pages=12)
    if not recent_drops:
        return {
            "generated_on": datetime.now(timezone.utc).isoformat(),
            "league": context.league.settings.name,
            "days": days,
            "claim_mode": claim_mode,
            "rows": [],
        }

    redraft = scrape_top_hitters()
    pl_dynasty = scrape_dynasty_hitters()
    espn_dynasty = scrape_espn_dynasty_hitters()
    _, streamer_ranks = scrape_sp_streamer_tiers()
    roster_hitters = get_roster_players(context, team_id=context.config.team_id, player_type="hitters")

    fa_hitters = get_free_agent_hitters(context, size_per_pos=100)
    fa_pitchers = get_free_agent_pitchers(context, size=350, position="P")
    fa_lookup = {player.normalized_name: player for player in fa_hitters + fa_pitchers}

    roster_hitter_rows = []
    slot_counts = {slot: 0 for slot in REQUIRED_SINGLETON_HITTER_SLOTS}
    for player in roster_hitters:
        redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
        pl_dynasty_rank = pl_dynasty.get(player.normalized_name).rank if player.normalized_name in pl_dynasty else None
        espn_dynasty_rank = espn_dynasty.get(player.normalized_name).rank if player.normalized_name in espn_dynasty else None
        dynasty_rank = min((rank for rank in (pl_dynasty_rank, espn_dynasty_rank) if rank is not None), default=None)
        trend = summarize_recent_hitting(player.name, trend_games=trend_games)
        rec = evaluate_roster_hitter(redraft_rank, dynasty_rank, trend.label)
        roster_hitter_rows.append(
            {
                "player": player,
                "redraft_rank": redraft_rank,
                "dynasty_rank": dynasty_rank,
                "trend": trend,
                "rec": rec,
            }
        )
        eligible = _eligible_hitter_slots(player)
        for slot in REQUIRED_SINGLETON_HITTER_SLOTS:
            if slot in eligible:
                slot_counts[slot] += 1

    latest_drop_by_player = {}
    for drop in recent_drops:
        latest_drop_by_player.setdefault(drop.player.normalized_name, drop)

    rows = []
    for key, drop in latest_drop_by_player.items():
        player = fa_lookup.get(key)
        if not player:
            continue

        row = _serialize_pitcher_row(player, streamer_ranks) if _is_pitcher_positions(player.positions or []) else _serialize_hitter_row(
            player,
            trend_games=trend_games,
            redraft=redraft,
            pl_dynasty=pl_dynasty,
            espn_dynasty=espn_dynasty,
        )

        action = row["recommendation"].action
        if action == "PASS" or str(action).startswith("SKIP"):
            continue
        if row["kind"] == "P" and row.get("tier") == "Not Ranked":
            continue
        if claim_mode == "wins" and action not in {"WIN-NOW ADD", "MUST ADD"}:
            continue

        serialized = {
            "kind": row["kind"],
            "name": player.name,
            "normalized_name": player.normalized_name,
            "mlb_team": player.mlb_team,
            "positions": player.positions,
            "percent_owned": player.percent_owned,
            "dropped_by": drop.dropped_by,
            "dropped_at": drop.occurred_at.isoformat(),
            "recommendation": {
                "action": action,
                "reason": row["recommendation"].reason,
                "score": row["recommendation"].score,
            },
        }

        if row["kind"] == "H":
            trend = row["trend"]
            serialized.update(
                {
                    "redraft_rank": row["redraft_rank"],
                    "pl_dynasty_rank": row["pl_dynasty_rank"],
                    "espn_dynasty_rank": row["espn_dynasty_rank"],
                    "dynasty_rank": row["dynasty_rank"],
                    "trend": {
                        "label": trend.label,
                        "summary": trend.summary,
                        "games": trend.games,
                        "avg": trend.avg,
                        "ops": trend.ops,
                        "hr": trend.hr,
                        "sb": trend.sb,
                        "rbi": trend.rbi,
                        "runs": trend.runs,
                    },
                }
            )
            if action in {"WIN-NOW ADD", "MUST ADD"}:
                drop_candidate = _recommended_drop_for_hitter(player, roster_hitter_rows, slot_counts)
                if drop_candidate:
                    drop_player = drop_candidate["player"]
                    serialized["suggested_drop"] = {
                        "name": drop_player.name,
                        "positions": drop_player.positions,
                        "percent_owned": drop_player.percent_owned,
                        "roster_score": drop_candidate["rec"].score,
                    }
        else:
            serialized.update(
                {
                    "tier": row["tier"],
                    "season_record": row["season_record"],
                    "last_ten_record": row["last_ten_record"],
                }
            )
        rows.append(serialized)

    rows.sort(key=lambda row: (-row["recommendation"]["score"], row["name"]))
    rows = rows[:top]
    return {
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "league": context.league.settings.name,
        "days": days,
        "claim_mode": claim_mode,
        "top": len(rows),
        "rows": rows,
    }

