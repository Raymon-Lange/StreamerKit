from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from collectors.espn import build_context, get_free_agent_hitters, get_free_agent_pitchers, get_roster_players
from collectors.espn_activity import get_recent_drops
from collectors.espn_dynasty import scrape_espn_dynasty_hitters
from collectors.mlb_stats import get_pitcher_stats, summarize_recent_hitting
from collectors.pitcherlist import scrape_dynasty_hitters, scrape_sp_streamer_tiers, scrape_top_hitters
from engines.hitter_engine import evaluate_free_agent_hitter, evaluate_roster_hitter
from engines.pitcher_engine import TIER_EMOJI, streamer_recommendation
from utils.config import AppConfig

REQUIRED_SINGLETON_HITTER_SLOTS = ("C", "1B", "2B", "3B", "SS")


def _fmt_when(ts: datetime) -> str:
    local_ts = ts.astimezone()
    return local_ts.strftime("%Y-%m-%d %H:%M")


def _build_hitter_row(player, trend_games: int, redraft, pl_dynasty, espn_dynasty):
    redraft_rank = redraft.get(player.normalized_name).rank if player.normalized_name in redraft else None
    pl_dynasty_rank = pl_dynasty.get(player.normalized_name).rank if player.normalized_name in pl_dynasty else None
    espn_dynasty_rank = espn_dynasty.get(player.normalized_name).rank if player.normalized_name in espn_dynasty else None
    dynasty_rank = min((rank for rank in (pl_dynasty_rank, espn_dynasty_rank) if rank is not None), default=None)
    trend = summarize_recent_hitting(player.name, trend_games=trend_games)
    rec = evaluate_free_agent_hitter(redraft_rank, dynasty_rank, trend.label)
    return {
        "kind": "H",
        "player": player,
        "score": rec.score,
        "action": rec.action,
        "reason": rec.reason,
        "trend": trend,
        "redraft_rank": redraft_rank,
        "pl_dynasty_rank": pl_dynasty_rank,
        "espn_dynasty_rank": espn_dynasty_rank,
        "dynasty_rank": dynasty_rank,
    }


def _build_pitcher_row(player, streamer_ranks):
    rank = streamer_ranks.get(player.normalized_name)
    tier = rank.tier if rank else "Not Ranked"
    rec = streamer_recommendation(tier)
    season_record, last_ten, _ = get_pitcher_stats(player.name)
    return {
        "kind": "P",
        "player": player,
        "score": rec.score,
        "action": rec.action,
        "reason": rec.reason,
        "tier": tier,
        "season_record": season_record,
        "last_ten": last_ten,
    }


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


def _recommended_drop_for_hitter(add_player, roster_hitter_rows, slot_counts: dict[str, int]):
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

    chosen = min(
        pool,
        key=lambda row: (
            row["rec"].score,
            (row["redraft_rank"] or 9999),
            (row["dynasty_rank"] or 9999),
            -(row["player"].percent_owned or 0.0),
        ),
    )
    return chosen


def run(args) -> None:
    config = AppConfig(
        league_id=getattr(args, "league_id", None) or AppConfig().league_id,
        year=getattr(args, "year", None) or AppConfig().year,
    )
    days = max(1, getattr(args, "days", 2) or 2)
    trend_games = getattr(args, "trend_games", 10) or 10
    top = getattr(args, "top", 25) or 25
    claim_mode = (getattr(args, "claim_mode", "all") or "all").lower()

    context = build_context(config)
    recent_drops = get_recent_drops(context, days=days, page_size=50, max_pages=12)
    if not recent_drops:
        print(f"No dropped players found in the last {days} day(s).")
        return

    redraft = scrape_top_hitters()
    pl_dynasty = scrape_dynasty_hitters()
    espn_dynasty = scrape_espn_dynasty_hitters()
    _, streamer_ranks = scrape_sp_streamer_tiers()
    roster_hitters = get_roster_players(context, team_id=context.config.team_id, player_type="hitters")

    fa_hitters = get_free_agent_hitters(context, size_per_pos=100)
    fa_pitchers = get_free_agent_pitchers(context, size=350, position="P")
    fa_lookup = {p.normalized_name: p for p in fa_hitters + fa_pitchers}

    roster_hitter_rows = []
    slot_counts = {slot: 0 for slot in REQUIRED_SINGLETON_HITTER_SLOTS}
    for roster_player in roster_hitters:
        redraft_rank = redraft.get(roster_player.normalized_name).rank if roster_player.normalized_name in redraft else None
        pl_dynasty_rank = pl_dynasty.get(roster_player.normalized_name).rank if roster_player.normalized_name in pl_dynasty else None
        espn_dynasty_rank = espn_dynasty.get(roster_player.normalized_name).rank if roster_player.normalized_name in espn_dynasty else None
        dynasty_rank = min((rank for rank in (pl_dynasty_rank, espn_dynasty_rank) if rank is not None), default=None)
        trend = summarize_recent_hitting(roster_player.name, trend_games=trend_games)
        rec = evaluate_roster_hitter(redraft_rank, dynasty_rank, trend.label)
        roster_hitter_rows.append(
            {
                "player": roster_player,
                "redraft_rank": redraft_rank,
                "dynasty_rank": dynasty_rank,
                "trend": trend,
                "rec": rec,
            }
        )
        eligible = _eligible_hitter_slots(roster_player)
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

        is_pitcher = _is_pitcher_positions(player.positions or [])
        row = _build_pitcher_row(player, streamer_ranks) if is_pitcher else _build_hitter_row(
            player, trend_games=trend_games, redraft=redraft, pl_dynasty=pl_dynasty, espn_dynasty=espn_dynasty
        )
        if row["action"] == "PASS" or str(row["action"]).startswith("SKIP"):
            continue
        if row["kind"] == "P" and row.get("tier") == "Not Ranked":
            continue
        if claim_mode == "wins" and row["action"] not in {"WIN-NOW ADD", "MUST ADD"}:
            continue

        row["dropped_by"] = drop.dropped_by
        row["dropped_at"] = drop.occurred_at
        if row["kind"] == "H" and row["action"] in {"WIN-NOW ADD", "MUST ADD"}:
            row["drop_candidate"] = _recommended_drop_for_hitter(player, roster_hitter_rows, slot_counts)
        rows.append(row)

    rows.sort(key=lambda row: (-row["score"], row["player"].name))
    rows = rows[:top]

    if not rows:
        print(f"No waiver-worthy drops found in the last {days} day(s) after filtering out PASS/SKIP.")
        return

    divider = "─" * 108
    now_local = datetime.now(timezone.utc).astimezone().strftime("%A, %B %d, %Y %I:%M %p")
    print(divider)
    print(f"📅  {now_local}")
    print(f"🏟   League: {context.league.settings.name}")
    print(f"Lookback: Last {days} day(s) | Showing top {len(rows)} waiver-worthy dropped players")
    print("Filtered out: PASS and SKIP recommendations")
    print(f"Mode: {claim_mode}")
    print(divider)

    for row in rows:
        player = row["player"]
        positions = "/".join(player.positions[:4]) if player.positions else "N/A"
        owned = f"{player.percent_owned:.1f}%" if player.percent_owned is not None else "N/A"
        print(
            f"{player.name} | {player.mlb_team or 'N/A'} | Pos: {positions} | Owned: {owned} | "
            f"Dropped by: {row['dropped_by']} ({_fmt_when(row['dropped_at'])})"
        )
        if row["kind"] == "H":
            trend = row["trend"]
            print(
                f"  Redraft Rank: {row['redraft_rank'] or 'NR'} | "
                f"Dynasty Rank (Best): {row['dynasty_rank'] or 'NR'} | "
                f"PL: {row['pl_dynasty_rank'] or 'NR'} | ESPN: {row['espn_dynasty_rank'] or 'NR'}"
            )
            print(f"  Trend: {trend.label} | {trend.summary}")
        else:
            tier = row["tier"]
            print(f"  {TIER_EMOJI.get(tier, '⚪')} Streamer Tier: {tier}")
            print(f"  Pitching: Season {row['season_record']} | Last 10 {row['last_ten']}")
        print(f"  Recommendation: {row['action']}")
        print(f"  Why: {row['reason']}")
        drop_candidate = row.get("drop_candidate")
        if drop_candidate:
            drop_player = drop_candidate["player"]
            drop_owned = f"{drop_player.percent_owned:.1f}%" if drop_player.percent_owned is not None else "N/A"
            drop_positions = "/".join(drop_player.positions[:4]) if drop_player.positions else "N/A"
            print(
                f"  Suggested drop (win-now): {drop_player.name} | Pos: {drop_positions} | "
                f"Owned: {drop_owned} | Roster score: {drop_candidate['rec'].score:.0f}"
            )
        print(f"  {'·' * 100}")


def parse_args() -> argparse.Namespace:
    config = AppConfig()
    parser = argparse.ArgumentParser(description="Review recent league drops and surface waiver-worthy adds.")
    parser.add_argument("--league-id", type=int, default=config.league_id)
    parser.add_argument("--year", type=int, default=config.year)
    parser.add_argument("--days", type=int, default=2, help="Lookback window in days (default: 2).")
    parser.add_argument("--trend-games", type=int, default=10)
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument(
        "--claim-mode",
        choices=["all", "wins"],
        default="all",
        help="Filter output: 'all' actionable targets, or only 'wins' (WIN-NOW ADD / MUST ADD).",
    )
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
