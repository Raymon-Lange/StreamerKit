# Tasks: Collector Feed Logging

**Input**: Design documents from `specs/002-collector-feed-logging/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/feed-logger-api.md

**Organization**: Tasks grouped by user story — each story phase is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[US#]**: User story this task belongs to (US1/US2/US3 per spec.md)
- Exact file paths in all descriptions

---

## Phase 1: Setup

**Purpose**: Confirm no structural changes needed before implementation

- [x] T001 Verify `utils/__init__.py` is importable with no circular imports (file: `utils/__init__.py` — read-only check, no changes expected)

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Create the shared logging utility that all three user stories depend on. No collector instrumentation can begin until this phase is complete.

**⚠️ CRITICAL**: All user story phases depend on this phase.

- [x] T002 Create `utils/feed_logger.py` — define `FeedLogContext` class with fields: `outcome` (default `"success"`), `error_type: str | None`, `error_message: str | None`; implement `mark_cache_fallback()` method that sets `outcome = "cache-fallback"`
- [x] T003 Implement `log_feed_fetch(collector: str, operation: str)` context manager in `utils/feed_logger.py` — on `__enter__`: record `time.monotonic()` start and `triggered_by` from `Path(sys.argv[0]).name`; on `__exit__`: compute duration, capture exception type+message if exception present (set `outcome = "error"`, do not suppress), emit single-line `[FEED]` log entry to stderr via `logging.getLogger("feed")` at `INFO` level; format: `[FEED] {timestamp}Z | {triggered_by} | {collector} | {operation} | {outcome} | {duration:.2f}s[ | {error_type}: {error_message}]`; wrap entire method body in bare `except Exception: pass` so logger failures never propagate
- [x] T004 Implement `log_script_run(script_name: str)` context manager in `utils/feed_logger.py` — same timing and error-capture pattern as `log_feed_fetch`; on `__exit__`: emit single `[SCRIPT]` line to stderr; format: `[SCRIPT] {timestamp}Z | {script_name} | completed | {duration:.2f}s` on success, or `[SCRIPT] {timestamp}Z | {script_name} | error | {duration:.2f}s | {error_type}` on exception (do not suppress exception); wrap in bare `except Exception: pass` guard so logger failures never propagate

**Checkpoint**: `utils/feed_logger.py` exists and exports both `log_feed_fetch` and `log_script_run`. Each context manager produces its respective `[FEED]` / `[SCRIPT]` line on stderr.

---

## Phase 3: User Story 1 — View Feed Fetch Performance (Priority: P1) 🎯 MVP

**Goal**: Every fetch in the two most-used web-scraping collectors (PitcherList and MLB Stats) produces a `[FEED]` log entry showing collector name, duration, and outcome.

**Independent Test**: Run `python scripts/run_sp_streamers.py` and confirm `[FEED]` lines appear on stderr for PitcherList and MLB Stats fetches, each with a measured duration and correct outcome field.

### Implementation

- [x] T004 [US1] Instrument `collectors/pitcherlist.py` `scrape_top_hitters()` — wrap full function body in `with log_feed_fetch("pitcherlist", "scrape_top_hitters") as feed_log:`; call `feed_log.mark_cache_fallback()` on both cache-return paths (TTL-fresh path at top of function AND the `except Exception` fallback-to-cache path)
- [x] T005 [P] [US1] Instrument `collectors/pitcherlist.py` `scrape_dynasty_hitters()` — same pattern as T004 with `log_feed_fetch("pitcherlist", "scrape_dynasty_hitters")` and `mark_cache_fallback()` on both cache-return paths
- [x] T006 [P] [US1] Instrument `collectors/pitcherlist.py` `get_latest_streamer_url()` and `scrape_sp_streamer_tiers()` — wrap each function body in `log_feed_fetch("pitcherlist", "<function_name>")`; no cache paths to mark
- [x] T007 [P] [US1] Instrument `collectors/mlb_stats.py` `get_todays_probable_starters()` — wrap `requests.get()` call (and surrounding try/except) in `log_feed_fetch("mlb_stats", "get_todays_probable_starters")`; empty `set()` return on exception is not a cache-fallback so no `mark_cache_fallback()` needed
- [x] T008 [P] [US1] Instrument `collectors/mlb_stats.py` `get_hitter_game_log()` and `get_pitcher_game_log()` — wrap `statsapi.get()` call in each with `log_feed_fetch("mlb_stats", "get_hitter_game_log")` and `log_feed_fetch("mlb_stats", "get_pitcher_game_log")` respectively; bare `except Exception: return []` returns stay inside `with` block so exceptions are caught by context manager before the bare except silences them — use a nested try/except inside the `with` block to re-raise after logging

**Checkpoint**: US1 is complete. `run_sp_streamers.py` output to stderr includes `[FEED]` entries for every PitcherList and MLB Stats fetch. Cache hits show `cache-fallback`, successful live fetches show `success`.

---

## Phase 4: User Story 2 — Diagnose a Slow or Failed Feed (Priority: P2)

**Goal**: All ESPN collectors are also instrumented, completing full coverage. A developer can identify any failing feed — including ESPN API failures — from the log alone.

**Independent Test**: Simulate an ESPN API failure (e.g., invalid credentials in `.env`) and confirm a `[FEED]` error line appears with `error` outcome and a recognizable exception message.

### Implementation

- [x] T009 [US2] Instrument `collectors/espn.py` `get_league()` — wrap `League(...)` instantiation in `log_feed_fetch("espn", "get_league")`; this is the single ESPN API network call that `build_context()` depends on
- [x] T010 [P] [US2] Instrument `collectors/espn_dynasty.py` `scrape_espn_dynasty_hitters()` — wrap function body in `log_feed_fetch("espn_dynasty", "scrape_espn_dynasty_hitters")`; call `mark_cache_fallback()` on TTL-fresh cache-return path and on the `except Exception` cache-fallback path
- [x] T011 [P] [US2] Instrument `collectors/espn_points.py` `scrape_espn_points_top300()` — same pattern as T010 with `log_feed_fetch("espn_points", "scrape_espn_points_top300")`
- [x] T012 [P] [US2] Instrument `collectors/espn_keeper_cost.py` `scrape_espn_keeper_cost()` — wrap `_build_from_league(context)` call in `log_feed_fetch("espn_keeper_cost", "scrape_espn_keeper_cost")`; call `mark_cache_fallback()` on the cache-return path at top of function (note: keeper cost cache is write-once per season, not TTL-expired per constitution Principle III)
- [x] T013 [P] [US2] Instrument `collectors/espn_activity.py` `get_recent_drops()` — wrap ESPN league API call in `log_feed_fetch("espn", "get_recent_drops")`

**Checkpoint**: US2 is complete. All 6 collector modules are fully instrumented. Every external fetch produces a `[FEED]` entry. Error entries include exception type and message.

---

## Phase 5: User Story 3 — Review a Session's Feed Activity (Priority: P3)

**Goal**: Every script produces a `[SCRIPT]` summary entry with total runtime; `[FEED]` entries carry the triggering script name. A developer can review a full session — feed-level and script-level — from a single stderr stream.

**Independent Test**: Run two scripts back-to-back (`run_sp_streamers.py && run_free_agent_hitters.py`) — each `[FEED]` entry shows the correct script name, and each script produces one `[SCRIPT]` summary entry with total elapsed time.

### Implementation

- [x] T014 [US3] Verify `triggered_by` field is correctly populated in `utils/feed_logger.py` — confirm `Path(sys.argv[0]).name` produces the script filename (e.g., `run_sp_streamers.py`) and not an empty string or absolute path; handle edge case where `sys.argv` is empty by defaulting to `"unknown"`
- [x] T015 [P] [US3] Instrument `scripts/run_sp_streamers.py` `run()` — wrap body in `with log_script_run("run_sp_streamers.py"):`
- [x] T016 [P] [US3] Instrument `scripts/run_free_agent_hitters.py` `run()` — wrap body in `with log_script_run("run_free_agent_hitters.py"):`
- [x] T017 [P] [US3] Instrument `scripts/run_team_hitter_eval.py` `run()` — wrap body in `with log_script_run("run_team_hitter_eval.py"):`
- [x] T018 [P] [US3] Instrument `scripts/run_team_pitcher_eval.py` `run()` — wrap body in `with log_script_run("run_team_pitcher_eval.py"):`
- [x] T019 [P] [US3] Instrument `scripts/run_pitcher_start_eval.py` `run()` — wrap body in `with log_script_run("run_pitcher_start_eval.py"):`
- [x] T020 [P] [US3] Instrument `scripts/run_roster_optimizer.py` `run()` — wrap body in `with log_script_run("run_roster_optimizer.py"):`
- [x] T021 [P] [US3] Instrument `scripts/run_weekly_scores.py` `run()` — wrap body in `with log_script_run("run_weekly_scores.py"):`
- [x] T022 [P] [US3] Instrument `scripts/run_recent_drops_waiver_review.py` `run()` — wrap body in `with log_script_run("run_recent_drops_waiver_review.py"):`
- [x] T023 [P] [US3] Instrument `scripts/show_ranking_page_sources.py` `run()` — wrap body in `with log_script_run("show_ranking_page_sources.py"):`

**Checkpoint**: US3 is complete. Every script emits one `[SCRIPT]` summary line on stderr. `[FEED]` entries carry the correct script name. Running two scripts back-to-back produces interleaved `[FEED]` lines followed by a `[SCRIPT]` summary for each.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Clean up imports and verify the implementation is coherent end-to-end.

- [x] T024 [P] Add `log_feed_fetch` and `log_script_run` to `utils/__init__.py` exports so all callers can import via `from utils import log_feed_fetch, log_script_run`
- [x] T025 [P] Review all collector `except Exception: pass` or `except Exception: return` blocks to confirm they are nested inside the `with log_feed_fetch(...)` block, not wrapping it — any bare except that wraps the `with` block would silence exceptions before the context manager's `__exit__` can capture them
- [x] T026 Run `python scripts/run_sp_streamers.py` end-to-end and confirm `[FEED]` lines and a `[SCRIPT]` summary line appear on stderr with correct format, no stdout pollution, and no script failure caused by the logger

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — blocks all user story phases
- **User Stories (Phases 3–5)**: All depend on Phase 2 completion; can proceed in priority order
- **Polish (Phase 6)**: Depends on Phases 3–5 completion

### User Story Dependencies

- **US1 (Phase 3)**: Starts after Phase 2 — no dependency on US2 or US3
- **US2 (Phase 4)**: Starts after Phase 2 — no dependency on US1 (collectors are independent files)
- **US3 (Phase 5)**: Starts after Phase 2 — `log_script_run` and `triggered_by` are both in core logger

### Within Each Phase

- Tasks marked **[P]** touch different files — they can run concurrently
- Tasks without **[P]** depend on the previous task in the same phase completing first

### Parallel Opportunities

```bash
# After T004 completes, all of these can run concurrently:
T005  # pitcherlist scrape_top_hitters
T006  # pitcherlist scrape_dynasty_hitters    [P]
T007  # pitcherlist get_latest_streamer_url   [P]
T008  # mlb_stats probable starters           [P]
T009  # mlb_stats game log functions          [P]

# After T010 completes, all of these can run concurrently:
T011  # espn_dynasty     [P]
T012  # espn_points      [P]
T013  # espn_keeper_cost [P]
T014  # espn_activity    [P]

# After T014 (triggered_by verify), all 9 script tasks can run concurrently:
T015–T023  # one per script  [P]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) + Phase 2 (Foundational)
2. Complete Phase 3 (US1) — instrument PitcherList and MLB Stats
3. **STOP and VALIDATE**: Run `run_sp_streamers.py`, confirm `[FEED]` lines on stderr
4. Deploy/use as-is if that coverage is sufficient

### Incremental Delivery

1. Phase 1 + 2 → logger utility ready (both `log_feed_fetch` and `log_script_run`)
2. Phase 3 (US1) → PitcherList + MLB Stats covered → run `run_sp_streamers.py` to validate
3. Phase 4 (US2) → ESPN collectors covered → test with `run_free_agent_hitters.py`
4. Phase 5 (US3) → all 9 scripts instrumented → test multi-script session, verify `[SCRIPT]` summaries
5. Phase 6 (Polish) → clean imports and final end-to-end validation

---

## Notes

- **[P]** tasks touch different collector files — safe to run in parallel
- Cache-fallback paths appear in TWO places in PitcherList and ESPN dynasty/points collectors: (1) the TTL-fresh check at the top, and (2) the `except Exception` fallback — both need `mark_cache_fallback()`
- ESPN keeper cost cache is write-once per season (not TTL-expired) — per constitution Principle III; the cache path is still a `cache-fallback` outcome
- No new Python package dependencies required — standard library only
- No test tasks generated — tests not explicitly requested in spec.md
