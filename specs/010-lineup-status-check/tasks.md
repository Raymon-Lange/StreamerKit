# Tasks: Player Lineup Status Check

**Input**: Design documents from `specs/010-lineup-status-check/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not explicitly requested — no test tasks generated. Verification tasks (manual run + curl) are included instead.

**Organization**: Tasks grouped by user story for independent implementation and testing.

---

## Phase 1: Setup

**Purpose**: Confirm existing codebase is clean before changes begin.

- [x] T001 Verify existing code runs cleanly — `python scripts/run_sp_streamers.py` should complete without errors before any files are modified

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Add the `LineupStatus` canonical dataclass — all three user stories depend on this model existing before any collector, service, or route code can be written.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Add `LineupStatus` dataclass to `models/player.py` after the existing `LineupSwap` dataclass — fields: `player_name: str`, `in_lineup: bool`, `status: str`, `batting_slot: int | None = None`, `team: str | None = None`, `opponent: str | None = None`, `game_time: str | None = None`

**Checkpoint**: `LineupStatus` importable from `models/player.py` — user story phases can now begin.

---

## Phase 3: User Story 1 — Check Player Lineup Before Setting Fantasy Lineup (Priority: P1) 🎯 MVP

**Goal**: A fantasy manager can look up any player by name and get a clear starting/bench/no-game status with batting slot and matchup context, via both CLI and API.

**Independent Test**: `python scripts/check_lineup.py --player "Jarren Duran"` prints one-line result with status, batting slot, team, and opponent. `curl -H "X-API-Key: $API_KEY" localhost:8000/api/lineup?player=Jarren+Duran` returns correct JSON matching the contract in `contracts/api-lineup.md`.

### Implementation for User Story 1

- [x] T003 [US1] Add `get_player_lineup_status(player_name: str, for_date: date | None = None) -> LineupStatus` to `collectors/mlb_stats.py` — hits ESPN scoreboard to enumerate events, fetches per-game summary to walk `boxscore.players[*].statistics[0].athletes`, matches via `normalize_name()`, returns first game found for the player's team (doubleheader rule), returns `status="no_game"` on any fetch exception (depends on T002)
- [x] T004 [US1] Create `services/lineup_service.py` with `get_lineup_status(player_name: str, for_date: date | None = None) -> LineupStatus` — thin wrapper calling `collectors/mlb_stats.get_player_lineup_status()` (depends on T003)
- [x] T005 [P] [US1] Create `app/routes/lineup.py` — FastAPI router with `GET /lineup`, 120s response cache keyed on `lineup_{player}_{date}`, validates optional `date` query param (400 on bad format), delegates to `services/lineup_service.get_lineup_status()`, returns dict matching contract in `contracts/api-lineup.md` (depends on T004)
- [x] T006 [P] [US1] Create `scripts/check_lineup.py` — thin CLI script with `--player` (required) and `--date` (optional) args, calls `services/lineup_service.get_lineup_status()`, prints one-line human-readable result per the output format in `specs/010-lineup-status-check/plan.md` Step 6 (depends on T004)
- [x] T007 [P] [US1] Register `lineup.router` in `app/main.py` — add `lineup` to the route imports line and add `app.include_router(lineup.router, prefix="/api", **_protected)` alongside the other protected routers (depends on T005)
- [x] T008 [P] [US1] Register `check_lineup` in root `main.py` menu — add a menu entry so `python main.py` surfaces the new script (depends on T006)
- [x] T009 [P] [US1] Verify CLI — run `python scripts/check_lineup.py --player "Jarren Duran"` on a game day and confirm output shows status, batting slot, team vs opponent on one line (depends on T006, T008)
- [x] T010 [P] [US1] Verify API — `curl -H "X-API-Key: $API_KEY" "localhost:8000/api/lineup?player=Jarren+Duran"` and confirm JSON response matches all fields in `contracts/api-lineup.md` (depends on T005, T007)

**Checkpoint**: User Story 1 fully functional. CLI and API both return correct lineup status for a known starting player.

---

## Phase 4: User Story 2 — Check Lineup for a Specific Past or Future Date (Priority: P2)

**Goal**: The `--date` CLI flag and `?date=` API query parameter correctly route queries to the specified date rather than defaulting to today.

**Independent Test**: `python scripts/check_lineup.py --player "Jarren Duran" --date 2026-06-23` returns a result for that historical date; the same query without `--date` returns today's result. A bad date string (`--date not-a-date`) exits with a clear error.

### Implementation for User Story 2

_(No new files — date parameter is already built into T003, T005, T006. These are verification tasks only.)_

- [x] T011 [P] [US2] Verify `--date` CLI flag — run `python scripts/check_lineup.py --player "Jarren Duran" --date <yesterday>` and confirm result differs from today's result or returns a valid historical status (depends on T006)
- [x] T012 [P] [US2] Verify `?date=` API param — curl with `?player=Jarren+Duran&date=<yesterday>` and confirm correct response; also curl with `?player=Jarren+Duran&date=notadate` and confirm `400` response (depends on T005)

**Checkpoint**: Date parameter works correctly in both interfaces.

---

## Phase 5: User Story 3 — Handle No Game Scheduled (Priority: P3)

**Goal**: The system returns unambiguous status for all edge-case states — no game, player not found, and lineup not yet posted — without returning a misleading "bench" status.

**Independent Test**: Querying on a known MLB off-day (e.g., All-Star break) returns `status: "no_game"`. Querying "Fake Player Xyz" returns `status: "not_found"`. Both return HTTP 200.

### Implementation for User Story 3

_(No new files — all status variants are handled in T003. These are verification tasks only.)_

- [x] T013 [P] [US3] Verify `no_game` status — query a player whose team has no game on a known off-day (or use `--date` to target a past off-day) and confirm `status: "no_game"`, not `"bench"` (depends on T003)
- [x] T014 [P] [US3] Verify `not_found` status — query `--player "Fake Player Xyz"` via both CLI and API and confirm `status: "not_found"` with HTTP 200 (depends on T003)

**Checkpoint**: All five status values (`starting`, `bench`, `no_game`, `not_found`, `lineup_not_posted`) are distinguishable; no misleading states surfaced to the caller.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T015 [P] Run `python main.py` interactive menu and confirm the new "Check Lineup" entry appears and launches `scripts/check_lineup.py` correctly (depends on T008)
- [x] T016 Cross-check accuracy — query 3 players known to be starting on a live game day and verify all three results match ESPN.com lineups (depends on T009, T010)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **blocks all user story phases**
- **User Story 1 (Phase 3)**: Depends on Phase 2 — T003 → T004 → T005/T006 (parallel) → T007/T008 (parallel) → T009/T010 (parallel)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T005, T006 complete)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (T003 complete)
- **Polish (Phase 6)**: Depends on all user story phases complete

### Within User Story 1 (sequential backbone)

```
T002 (model) → T003 (collector) → T004 (service) → T005 + T006 (parallel)
                                                   → T007 (from T005) + T008 (from T006)
                                                   → T009 (from T008) + T010 (from T007)
```

### Parallel Opportunities

- T005 and T006 can run in parallel (different files, both depend only on T004)
- T007 and T008 can run in parallel (different files)
- T009 and T010 can run in parallel (different interfaces)
- T011 and T012 can run in parallel (CLI vs API)
- T013 and T014 can run in parallel (different edge cases)
- T015 and T016 can run in parallel

---

## Parallel Example: User Story 1

```bash
# After T004 (lineup_service.py) is complete, launch these together:
Task T005: "Create app/routes/lineup.py"
Task T006: "Create scripts/check_lineup.py"

# After T005 and T006 complete, launch together:
Task T007: "Register lineup.router in app/main.py"
Task T008: "Register check_lineup in root main.py menu"

# After T007 and T008 complete, verify together:
Task T009: "python scripts/check_lineup.py --player 'Jarren Duran'"
Task T010: "curl localhost:8000/api/lineup?player=Jarren+Duran"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — `LineupStatus` in `models/player.py`
3. Complete Phase 3: User Story 1 — collector → service → route + CLI
4. **STOP and VALIDATE**: CLI and API both return correct lineup status
5. Ship if ready — US2/US3 add date flexibility and edge-case hardening but US1 alone is production-usable

### Incremental Delivery

1. Setup + Foundational → model ready
2. US1 → core lookup working via CLI and API (MVP)
3. US2 → date parameter verified end-to-end
4. US3 → edge cases confirmed (no game, not found)
5. Polish → menu integration + accuracy cross-check

---

## Notes

- [P] = different files, no blocking dependency on an incomplete task — can run in parallel
- [Story] label maps each task to its user story for traceability
- US2 and US3 require no new files — the implementation in T003/T005/T006 already covers date params and all status variants
- All verification tasks (T009–T016) require a live API key in `.env` and a running FastAPI server for API tasks
- Commit after each checkpoint (T002, T004, T007+T008, T012, T014, T016)
