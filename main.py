from __future__ import annotations

import sys
import types
import statistics


# ── input helpers ─────────────────────────────────────────────────────────────

def ask_int(prompt: str, default: int | None = None) -> int | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"  {prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        if not raw and default is None:
            return None
        if raw.lstrip("-").isdigit():
            return int(raw)
        print("    Please enter a whole number.")


def ask_bool(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"  {prompt} {suffix}: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes"}


def ask_text(prompt: str, default: str | None = None) -> str | None:
    suffix = f" [{default}]" if default else ""
    raw = input(f"  {prompt}{suffix}: ").strip()
    if not raw:
        return default
    return raw


# ── menu ──────────────────────────────────────────────────────────────────────

def _menu_line(text: str, width: int = 78) -> str:
    trimmed = text[:width]
    return f"│ {trimmed:<{width}} │"


def _matchup_score(matchup, side: str) -> float:
    if side == "home":
        live = getattr(matchup, "home_team_live_score", None)
        final = getattr(matchup, "home_final_score", None)
    else:
        live = getattr(matchup, "away_team_live_score", None)
        final = getattr(matchup, "away_final_score", None)
    if live not in (None, 0, 0.0):
        score = live
    elif final is not None:
        score = final
    else:
        score = live
    return float(score or 0.0)


def _scoreboard_for_period(league, period: int):
    try:
        return league.scoreboard(matchupPeriod=period)
    except TypeError:
        return league.scoreboard(period=period)


def _resolve_latest_scored_period(league) -> int:
    max_period = int(getattr(league.settings, "matchup_period_count", 30) or 30)
    latest = int(getattr(league, "current_week", 1) or 1)
    for period in range(1, max_period + 1):
        board = _scoreboard_for_period(league, period)
        total = 0.0
        for matchup in board:
            total += _matchup_score(matchup, "home")
            total += _matchup_score(matchup, "away")
        if total > 0.0:
            latest = period
    return latest


def _weekly_header_line() -> str:
    try:
        from collectors.espn import build_context
        from utils.config import AppConfig

        cfg = AppConfig()
        if not cfg.league_id or not cfg.team_id:
            return "Weekly Score: set LEAGUE_ID and TEAM_ID in .env"

        context = build_context(cfg)
        league = context.league
        period = _resolve_latest_scored_period(league)
        board = _scoreboard_for_period(league, period)

        rows: list[tuple[str, float, int]] = []
        for matchup in board:
            rows.append((matchup.home_team.team_name, _matchup_score(matchup, "home"), matchup.home_team.team_id))
            rows.append((matchup.away_team.team_name, _matchup_score(matchup, "away"), matchup.away_team.team_id))
        if not rows:
            return f"Weekly Score: no matchup scores found for period {period}"

        rows.sort(key=lambda item: item[1], reverse=True)
        scores = [score for _, score, _ in rows]
        median_score = statistics.median(scores) if scores else 0.0
        top_half_cutoff = (len(rows) + 1) // 2
        team_idx = next((idx for idx, (_, _, team_id) in enumerate(rows, start=1) if team_id == cfg.team_id), None)
        if team_idx is None:
            return "Weekly Score: your TEAM_ID is not in this league"

        team_name, team_score, _ = rows[team_idx - 1]
        half_label = "TOP" if team_idx <= top_half_cutoff else "BTM"
        short_name = team_name[:26]
        return (
            f"Weekly: {short_name} {team_score:.1f} | "
            f"Rank {team_idx}/{len(rows)} {half_label} | Med {median_score:.1f} | Wk {period}"
        )
    except Exception as exc:
        return f"Weekly Score: unavailable ({exc})"


def _render_menu(weekly_line: str) -> str:
    return "\n".join(
        [
            "┌──────────────────────────────────────────────────────────────────────────────┐",
            _menu_line("BASEBALL TOOLKIT".center(78)),
            "├──────────────────────────────────────────────────────────────────────────────┤",
            _menu_line("Workflow lane: Morning lineup prep"),
            _menu_line("Recommended order: 5 Waiver Review -> 2 Free Agent Hitters -> 6 Optimizer"),
            _menu_line("Active defaults: team_id=config, trend=10, top=10"),
            _menu_line(weekly_line),
            "└──────────────────────────────────────────────────────────────────────────────┘",
            "",
            "┌───────────────────────────────── ACTION BOARD ───────────────────────────────┐",
            "│ [DISCOVER]                                                                   │",
            "│  1  Streaming Pitchers     Best for: daily streamers                         │",
            "│  2  Free Agent Hitters     Best for: replacement bats                        │",
            "│  5  Waiver Pickup Review   Best for: recent dropped value                    │",
            "│                                                                              │",
            "│ [AUDIT + DECIDE]                                                             │",
            "│  3  Team Hitters           Best for: lineup performance check                │",
            "│  4  Team Pitchers          Best for: staff health check                      │",
            "│  6  Roster Optimizer       Best for: clear add/drop recommendations          │",
            "│  7  Pitcher Start Eval     Best for: start/sit confidence                    │",
            "│                                                                              │",
            "│ [SYSTEM]                                                                     │",
            "│  8  Ranking Page Sources  Best for: verify ranking page URL/date refresh    │",
            "│  9  Exit                                                                     │",
            "└──────────────────────────────────────────────────────────────────────────────┘",
        ]
    )


def _run_streaming_pitchers() -> None:
    from scripts.run_sp_streamers import run
    pitcher = ask_text("Optional pitcher name (leave blank for full list)", default=None)
    tomorrow = ask_bool("Show tomorrow's starters?", default=False)
    run(types.SimpleNamespace(pitcher=pitcher, tomorrow=tomorrow))


def _run_free_agent_hitters() -> None:
    from scripts.run_free_agent_hitters import run
    top = ask_int("Top N hitters to show", default=10)
    size = ask_int("Free agent scan size (per position)", default=75)
    trend = ask_int("Trend games to look back", default=15)
    run(types.SimpleNamespace(top=top, size=size, trend_games=trend))


def _run_team_hitters() -> None:
    from scripts.run_team_hitter_eval import run
    team_id = ask_int("Team ID (leave blank to use default from config)", default=None)
    trend = ask_int("Trend games to look back", default=10)
    run(types.SimpleNamespace(team_id=team_id, trend_games=trend))


def _run_team_pitchers() -> None:
    from scripts.run_team_pitcher_eval import run
    team_id = ask_int("Team ID (leave blank to use default from config)", default=None)
    run(types.SimpleNamespace(team_id=team_id))


def _run_roster_optimizer() -> None:
    from scripts.run_roster_optimizer import run
    team_id = ask_int("Team ID (leave blank to use default from config)", default=None)
    trend = ask_int("Trend games to look back", default=10)
    min_gap = ask_int("Min score gap to flag a swap", default=10)
    run(types.SimpleNamespace(team_id=team_id, trend_games=trend, min_gap=float(min_gap or 10)))


def _run_pitcher_start_eval() -> None:
    from scripts.run_pitcher_start_eval import run
    team_id = ask_int("Team ID (leave blank to use default from config)", default=None)
    tomorrow = ask_bool("Evaluate tomorrow instead of today?", default=False)
    run(types.SimpleNamespace(team_id=team_id, tomorrow=tomorrow))


def _run_waiver_pickup_review() -> None:
    from scripts.run_recent_drops_waiver_review import run
    days = ask_int("Look back how many days", default=2)
    top = ask_int("Top N targets to show", default=25)
    trend = ask_int("Trend games to look back", default=10)
    claim_mode = (ask_text("Claim mode (all or wins)", default="all") or "all").strip().lower()
    if claim_mode not in {"all", "wins"}:
        print("    Invalid claim mode, using 'all'.")
        claim_mode = "all"
    run(types.SimpleNamespace(days=days, top=top, trend_games=trend, claim_mode=claim_mode))


def _run_ranking_page_sources() -> None:
    from scripts.show_ranking_page_sources import run

    show_missing = ask_bool("Show missing/unreadable cache files?", default=False)
    run(show_missing=show_missing)


HANDLERS: dict[str, tuple[str, object]] = {
    "1": ("Streaming Pitchers", _run_streaming_pitchers),
    "2": ("Free Agent Hitters", _run_free_agent_hitters),
    "3": ("Team Hitters", _run_team_hitters),
    "4": ("Team Pitchers", _run_team_pitchers),
    "5": ("Waiver Pickup Review", _run_waiver_pickup_review),
    "6": ("Roster Optimizer", _run_roster_optimizer),
    "7": ("Pitcher Start Eval", _run_pitcher_start_eval),
    "8": ("Ranking Page Sources", _run_ranking_page_sources),
    "9": ("Exit", None),
}


def main() -> None:
    weekly_line = _weekly_header_line()
    while True:
        print(_render_menu(weekly_line))
        choice = input("Choose tool: ").strip()

        if choice not in HANDLERS:
            print(f"\n  Invalid choice {choice!r}. Enter 1–9.\n")
            continue

        label, handler = HANDLERS[choice]

        if handler is None:
            print("\nGoodbye.\n")
            sys.exit(0)

        print(f"\n── {label} " + "─" * (60 - len(label)) + "\n")
        try:
            handler()
        except KeyboardInterrupt:
            print("\n\n  (interrupted)\n")
            continue
        except SystemExit:
            raise
        except Exception as exc:
            print(f"\n[error] {exc}\n")

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()
