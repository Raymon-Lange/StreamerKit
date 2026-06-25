---
description: "Task list for Lineup & Bench Card feature"
---

# Tasks: Lineup & Bench Card

**Input**: Design documents from `specs/011-lineup-bench-card/`

**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/api-my-roster.md ✅

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing project structure matches the plan before starting work. No new directories or dependencies are needed.

- [x] T001 Verify `app/main.py` router registration pattern by reading the file and confirming `include_router` calls for existing routes (e.g. `optimizer`, `lineup`) — no changes yet
- [x] T002 [P] Verify `services/optimizer_service.py` exports `_BENCH_SLOTS` pattern and `_lineup_slot()` helper to confirm the implementation approach in the plan matches the actual code

**Checkpoint**: Implementation approach confirmed — no surprises before writing code

---

## Phase 2: Foundational (Backend — Blocking Prerequisite)

**Purpose**: `GET /api/my-roster` endpoint must exist before any frontend work can be tested end-to-end. Both US1 and US2 draw from the same endpoint.

**⚠️ CRITICAL**: Frontend phases (Phase 3+) cannot be fully tested until this phase is complete.

- [x] T003 Create `services/roster_card_service.py` — implement `get_roster_card()` function that: (1) calls `build_context()` + `get_roster_players()` from `collectors/espn.py`; (2) reads `lineup_slot = str(getattr(p.espn_raw, "lineupSlot", "") or "").upper()` for each player; (3) defines `_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}` locally; (4) splits players into `starters` and `bench` lists based on slot; (5) uses `ThreadPoolExecutor` to call `get_player_lineup_status(name)` from `collectors/mlb_stats.py` in parallel for hitters only (use `is_hitter()` from `collectors/espn.py`); (6) returns serialized dict matching `contracts/api-my-roster.md` shape (`generated_on`, `team`, `starters`, `bench`)
- [x] T004 Create `app/routes/my_roster.py` — `router = APIRouter()` with `@router.get("/my-roster")`, cache key `"my_roster_{today}"`, TTL 120 s via `response_cache.get/set`, delegates entirely to `roster_card_service.get_roster_card()`
- [x] T005 Register new router in `app/main.py` — add `from app.routes.my_roster import router as my_roster_router` and `app.include_router(my_roster_router, prefix="/api")` following the same two-line pattern used for existing routers

**Checkpoint**: `curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/my-roster` returns JSON with `starters` and `bench` arrays

---

## Phase 3: User Story 1 — View Starting Lineup with Positions (Priority: P1) 🎯 MVP

**Goal**: Dashboard shows a card with all starting players, each displaying their fantasy slot and real-life "in lineup" status badge.

**Independent Test**: Open the dashboard — the Lineup & Bench card renders a starters section. Each starter shows name, fantasy slot (e.g. OF, 1B, SP), MLB team, optional injury badge, and a green/yellow/gray status badge based on `lineup_status`. Loading and error states render correctly.

### Implementation for User Story 1

- [x] T006 [P] [US1] Add `myRoster: () => apiFetch('/api/my-roster')` to the `api` object in `frontend/src/api.ts` (one line, following the existing pattern)
- [x] T007 [P] [US1] Create `frontend/src/components/LineupCard.tsx` — scaffold the component with: `useEffect + useState([starters, bench, loading, error])` following the `RecentDrops.tsx` pattern; wrap in `<Card title="My Lineup" loading={loading} error={error}>`; render only the **starters section** in this task (bench section added in Phase 4); each starter row mirrors `RecentDrops.tsx` row markup — left column: player name (`font-medium text-white text-sm`) + optional injury badge using `injuryColor`/`injuryLabel` from `constants/injuryStatus.ts` + `text-xs text-gray-400` for MLB team and `lineup_slot`; right column: lineup status badge — `"▶ Starting"` in `text-green-400` when `in_lineup === true`, `"? Not Posted"` in `text-yellow-400` when `lineup_status === "lineup_not_posted"`, `"— No Game"` in `text-gray-500` when `lineup_status === "no_game"`, `"✕ Out"` in `text-red-400` when `in_lineup === false && lineup_status !== "no_game" && lineup_status !== "lineup_not_posted"`, no badge when `in_lineup === null` (pitcher)
- [x] T008 [US1] Add `import LineupCard from './components/LineupCard'` and place `<LineupCard />` in the dashboard grid in `frontend/src/App.tsx` — insert after `<WeeklyScores />` in the existing `grid-cols-1 lg:grid-cols-2` div

**Checkpoint**: US1 complete — starter section visible in the dashboard with correct status badges per player

---

## Phase 4: User Story 2 — View Bench Players (Priority: P2)

**Goal**: The same card extends below the starters to show bench players in a clearly separated section, with the same slot and status information.

**Independent Test**: Bench section appears below a visible divider/label in the Lineup card. Bench players show their `BE` slot, MLB team, injury badge if applicable, and lineup status. The visual separation from starters is immediate without reading labels.

### Implementation for User Story 2

- [x] T009 [US2] Extend `frontend/src/components/LineupCard.tsx` — add bench section below the starters list: insert a section divider (`<div className="border-t border-gray-700 my-2" />`) followed by a `"BENCH"` label (`text-xs font-semibold uppercase tracking-widest text-gray-500`); render bench players using identical row markup to the starters section (same name/slot/badge structure); add empty-state message `<p className="text-gray-500 text-sm">No bench players.</p>` when `bench.length === 0`; add a `"STARTERS"` label at the top of the starters section using the same style to make the two-section structure explicit

**Checkpoint**: US1 + US2 complete — full card shows starters and bench in two labeled sections; switching between players via ESPN app and refreshing confirms correct slot assignments

---

## Phase 5: User Story 3 — Refresh Lineup Statuses on Demand (Priority: P3)

**Goal**: A refresh control on the card triggers a fresh fetch of lineup status data and re-renders badges without a full page reload.

**Independent Test**: Click the refresh button on the card — spinner shows briefly, then all status badges update. If the network is unavailable, the previous data remains and an error notice appears without clearing the player list.

### Implementation for User Story 3

- [x] T010 [US3] Add refresh capability to `frontend/src/components/LineupCard.tsx` — add a `refreshing` state boolean; add a refresh button (`↺` icon, `text-xs text-gray-500 hover:text-gray-300`) in the card title area (place it in the `Card` title by wrapping the card content manually or by placing it as a sibling element inside the card body at the top); on click, set `refreshing = true`, re-call `api.myRoster()`, update `starters`/`bench` state, set `refreshing = false`; on error during refresh, set `error` to the error message while keeping existing `starters`/`bench` data intact (do not clear player rows on refresh failure); show a muted spinner or `"Refreshing…"` text while `refreshing === true`

**Checkpoint**: US3 complete — refresh button functions and degrades gracefully on error; stale data is retained on failure

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and any cross-cutting improvements.

- [x] T011 Run the full dev stack (`docker compose -f docker-compose.dev.yml up`) and visually verify the card in the browser: starters and bench render correctly, status badges are readable, injury badges appear on affected players, loading state shows on initial load, error state shows when API is unreachable
- [x] T012 [P] Verify `app/routes/my_roster.py` uses `response_cache` correctly — confirm cache key includes today's date so stale data is not served across days (e.g. `f"my_roster_{date.today().isoformat()}"`)
- [x] T013 [P] Confirm `services/roster_card_service.py` handles ESPN API errors gracefully — if `get_roster_players()` raises, the route should return a 500 with a clear `detail` message rather than an unhandled exception trace

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 confirmation — **blocks all frontend phases**
- **Phase 3 (US1)**: Depends on Phase 2 completion; T006 and T007 can run in parallel, T008 depends on both
- **Phase 4 (US2)**: Depends on Phase 3 (extends the same component)
- **Phase 5 (US3)**: Depends on Phase 4 (extends the same component)
- **Phase 6 (Polish)**: Depends on Phase 5 (or Phase 3 for MVP stop)

### User Story Dependencies

- **US1 (P1)**: Depends on backend (Phase 2) — no dependency on US2 or US3
- **US2 (P2)**: Depends on US1 being scaffolded (extends `LineupCard.tsx`) — no dependency on US3
- **US3 (P3)**: Depends on US2 (extends the same component) — adds to existing state and JSX

### Within Each User Story

- Backend (Phase 2): T003 → T004 → T005 (sequential — each depends on the previous)
- US1: T006 and T007 run in parallel (different files), then T008 depends on both
- US2: T009 is a single task extending T007
- US3: T010 is a single task extending T009

### Parallel Opportunities

- T006 (`api.ts` edit) and T007 (`LineupCard.tsx` creation) can run in parallel
- T001 and T002 (Phase 1 verification) can run in parallel
- T012 and T013 (Phase 6 verification) can run in parallel

---

## Parallel Example: Phase 3 (US1)

```bash
# These two tasks touch different files — run in parallel:
Task T006: "Add myRoster() to frontend/src/api.ts"
Task T007: "Create frontend/src/components/LineupCard.tsx (starters section)"

# T008 depends on both T006 and T007 completing:
Task T008: "Add <LineupCard /> to frontend/src/App.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — 5 tasks)

1. Complete Phase 1: Verify project structure (T001, T002)
2. Complete Phase 2: Backend service + route + registration (T003, T004, T005)
3. Complete Phase 3: Frontend card with starters section (T006, T007, T008)
4. **STOP and VALIDATE**: `GET /api/my-roster` returns data; card renders starters with correct badges
5. Demo-ready: starters view is the full MVP

### Incremental Delivery

1. Phase 1 + Phase 2 → Backend endpoint live
2. Phase 3 (US1) → Starters card visible — **MVP!**
3. Phase 4 (US2) → Bench section added
4. Phase 5 (US3) → Refresh button added
5. Phase 6 → Polish + verification

---

## Notes

- All new Python code must follow the layer rules in the constitution: no HTTP in services, no logic in routes
- `_BENCH_SLOTS` is intentionally repeated in the new service rather than shared — three similar lines, Principle V
- The `LineupCard.tsx` component structure is a near-clone of `RecentDrops.tsx` — read that file before writing
- If `lineupSlot` is missing from `espn_raw`, default the slot to `"?"` rather than crashing
- Pitchers in the roster (those where `is_hitter()` returns `False`) must have `in_lineup: null` in the response — do not call `get_player_lineup_status()` for them
