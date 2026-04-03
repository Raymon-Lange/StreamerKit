from __future__ import annotations

import sys
import types


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

MENU = """
┌──────────────────────────────┐
│        Baseball Tools        │
├──────────────────────────────┤
│  1) Streaming Pitchers       │
│  2) Free Agent Hitters       │
│  3) Team Hitters             │
│  4) Waiver Pickup Review     │
│  5) Exit                     │
└──────────────────────────────┘"""


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


HANDLERS: dict[str, tuple[str, object]] = {
    "1": ("Streaming Pitchers", _run_streaming_pitchers),
    "2": ("Free Agent Hitters", _run_free_agent_hitters),
    "3": ("Team Hitters", _run_team_hitters),
    "4": ("Waiver Pickup Review", _run_waiver_pickup_review),
    "5": ("Exit", None),
}


def main() -> None:
    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        if choice not in HANDLERS:
            print(f"\n  Invalid choice {choice!r}. Enter 1–5.\n")
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
