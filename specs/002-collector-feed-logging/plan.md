# Implementation Plan: Collector Feed Logging

**Branch**: `002-collector-feed-logging` | **Date**: 2026-06-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-collector-feed-logging/spec.md`

## Summary

Add a shared logging utility in `utils/feed_logger.py` with two context managers: `log_feed_fetch()` for per-collector-call timing and `log_script_run()` for total script runtime. All collector call sites emit `[FEED]` lines to stderr; all script `run()` functions emit a `[SCRIPT]` summary line. Instrumentation at each call site requires 2–3 lines.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library only (`logging`, `time`, `sys`, `contextlib`) — no new packages required.

**Storage**: No persistent storage. Log events are written to stderr only.

**Testing**: pytest (existing test runner in project)

**Target Platform**: Linux / macOS CLI — same as existing scripts

**Project Type**: CLI tooling library — scripts invoke collectors which invoke the logger

**Performance Goals**: Logging overhead < 5 ms per fetch event (per SC-004)

**Constraints**: Must not raise; must not expose ESPN credentials; must not pollute stdout

**Scale/Scope**: 6 collector modules, ~10 external fetch call sites across the codebase

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layer Separation | PASS | Logger lives in `utils/` — accessed by `collectors/` only. No engine or script logic involved. |
| II. Shared Data Model | PASS | `FeedLogEntry` is internal to `utils/feed_logger.py` (not inter-module data exchange). No addition to `models/player.py` required. |
| III. Resilient External Data Access | PASS | Cache-fallback events are explicitly logged as a distinct outcome (FR-007). |
| IV. Weighted Scoring | N/A | Feature does not touch scoring. |
| V. Simplicity First | PASS | Context manager pattern — no base classes, decorators, or plugin machinery. Adds one file to `utils/`. |
| API/Deployment | N/A | No API layer changes. |
| Credentials | PASS | Logger redacts credential values; only collector name and operation are logged. |

**Gate result**: All applicable gates PASS. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/002-collector-feed-logging/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── feed-logger-api.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
utils/
├── config.py            # existing
├── names.py             # existing
└── feed_logger.py       # NEW — log_feed_fetch() and log_script_run() context managers

collectors/
├── pitcherlist.py       # instrument scrape_*() and cache-fallback paths
├── mlb_stats.py         # instrument statsapi.get() calls, requests.get() call
├── espn.py              # instrument get_league() call
├── espn_activity.py     # instrument get_recent_drops()
├── espn_dynasty.py      # instrument scrape_espn_dynasty_hitters() and cache-fallback
├── espn_keeper_cost.py  # instrument scrape_espn_keeper_cost() and cache path
└── espn_points.py       # instrument scrape_espn_points_top300() and cache-fallback

scripts/
├── run_sp_streamers.py          # wrap run() with log_script_run()
├── run_free_agent_hitters.py    # wrap run() with log_script_run()
├── run_team_hitter_eval.py      # wrap run() with log_script_run()
├── run_team_pitcher_eval.py     # wrap run() with log_script_run()
├── run_pitcher_start_eval.py    # wrap run() with log_script_run()
├── run_roster_optimizer.py      # wrap run() with log_script_run()
├── run_weekly_scores.py         # wrap run() with log_script_run()
├── run_recent_drops_waiver_review.py  # wrap run() with log_script_run()
└── show_ranking_page_sources.py       # wrap run() with log_script_run()
```

**Structure Decision**: Single-project layout. The only new file is `utils/feed_logger.py`. No new directories in source code.

## Complexity Tracking

> No constitution violations — table not required.
