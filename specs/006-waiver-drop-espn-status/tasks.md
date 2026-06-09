# Tasks: Waiver Drop ESPN Status Display

**Input**: Design documents from `specs/006-waiver-drop-espn-status/`

**Branch**: `006-waiver-drop-espn-status`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story label (US1 = CLI, US2 = API, US3 = Frontend)

---

## Phase 1: Foundational (Blocking Prerequisite)

**Purpose**: Add `injury_status` to the waiver drop service output. All three user stories depend on this — US1 (CLI) reads it for display, US2 (API) includes it automatically, US3 (frontend) consumes it from the API.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T001 Add `"injury_status": player.injury_status` to the return dict of both `_serialize_hitter_row()` and `_serialize_pitcher_row()` in `services/waivers_service.py`, and add `"injury_status": row["injury_status"]` to the `serialized` dict inside `get_recent_drops_waiver_review()` (applies to both the hitter and pitcher branches)

**Checkpoint**: Service now includes raw `injury_status` in every drop row. US1, US2, and US3 can proceed.

---

## Phase 2: User Story 1 — CLI Status Display (Priority: P1) 🎯 MVP

**Goal**: Each player's header line in the CLI waiver drop output shows a short status label (e.g., `[IR]`, `[DTD]`) when their ESPN status is non-active.

**Independent Test**: `python scripts/run_recent_drops_waiver_review.py --days 3` — find a player with a non-ACTIVE injury status and confirm `[IR]`, `[DTD]`, or similar appears on their name line. A player with no injury status should show no label.

- [x] T002 [US1] Add `_INJURY_LABELS` dict and status display to `scripts/run_recent_drops_waiver_review.py`: define the mapping (`INJURY_RESERVE` → `IR`, `DAY_TO_DAY` → `DTD`, `TEN_DAY_DL` → `IL10`, `FIFTEEN_DAY_DL` → `IL15`, `SIXTY_DAY_DL` → `IL60`, `SEVEN_DAY_DL` → `IL7`, `OUT` → `OUT`, `SUSPENSION` → `SUSP`), read `row.get("injury_status")`, and append `[LABEL]` to the player name header print line when status is non-null and non-`ACTIVE`

**Checkpoint**: CLI output shows injury status labels. US1 is fully functional and independently testable.

---

## Phase 3: User Story 2 — API Response Field (Priority: P2)

**Goal**: `GET /api/recent-drops` includes `injury_status` in every row — no route code changes needed since the service dict flows through automatically from T001.

**Independent Test**: `curl -s http://localhost:8000/api/recent-drops | python3 -c "import sys,json; rows=json.load(sys.stdin)['rows']; print(all('injury_status' in r for r in rows), [r['name']+':'+str(r['injury_status']) for r in rows[:3]])"` — all rows must contain the key; values should match live ESPN statuses.

- [x] T003 [US2] Verify `GET /api/recent-drops` response includes `injury_status` in each row using the curl check from the Independent Test above; confirm the field value matches what ESPN reports for players currently on IL/IR in the league

**Checkpoint**: API contract is satisfied. US2 complete.

---

## Phase 4: User Story 3 — Frontend Recent Drops Badge (Priority: P3)

**Goal**: Recent Drops card shows a styled injury badge next to the player name, using the same shared constants as the SP Streamers card.

**Independent Test**: Open the dashboard, locate a dropped player on IR or IL. Confirm a badge (e.g., `IR`) appears next to their name with the same red badge style as in the SP Streamers card. A player with null status shows no badge.

- [x] T004 [US3] Extract `injuryColor` and `injuryLabel` constant objects from `frontend/src/components/StreamerCard.tsx` into a new shared file `frontend/src/constants/injuryStatus.ts`; export both constants
- [x] T005 [P] [US3] Update `frontend/src/components/StreamerCard.tsx` to import `injuryColor` and `injuryLabel` from `frontend/src/constants/injuryStatus.ts` and remove the local definitions (depends on T004)
- [x] T006 [P] [US3] Update `frontend/src/components/RecentDrops.tsx`: add `injury_status: string | null` to the `DropRow` interface; import `injuryColor` and `injuryLabel` from `frontend/src/constants/injuryStatus.ts`; render a badge inline next to `r.name` when `r.injury_status` is non-null and present in `injuryLabel` (depends on T004)

**Checkpoint**: All three user stories complete. Recent Drops badge matches Streamers badge styling.

---

## Phase 5: Polish

- [x] T007 Run the manual verification scenarios from `specs/006-waiver-drop-espn-status/quickstart.md` end-to-end (CLI curl + API curl) and confirm all three user stories pass their independent test criteria

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **US1 CLI (Phase 2)**: Depends on T001
- **US2 API (Phase 3)**: Depends on T001 (field auto-included via service dict)
- **US3 Frontend (Phase 4)**: Depends on T001 (field in API) + T004 (shared constants)
  - T005 and T006 can run in parallel after T004
- **Polish (Phase 5)**: Depends on all prior phases

### Task Dependency Graph

```
T001 (service)
  ├── T002 (CLI)
  ├── T003 (API verify)
  └── T004 (extract constants)
        ├── T005 (StreamerCard import)  [parallel]
        └── T006 (RecentDrops badge)   [parallel]
              └── T007 (verify all)
```

### Parallel Opportunities

After T004 completes, T005 and T006 touch different files and can be done simultaneously.

---

## Implementation Strategy

### MVP (US1 only — 2 tasks)

1. T001 — service serialization
2. T002 — CLI display

At this point the CLI shows injury status and the API automatically exposes the field. Stop here and verify before continuing.

### Full delivery (all 3 stories — 7 tasks)

1. T001 → T002, T003 → T004 → T005 + T006 (parallel) → T007

---

## Notes

- No new ESPN API calls — `injury_status` is already on `PlayerRecord`
- No route changes in `app/routes/drops.py` — field flows through service dict automatically
- T005 is a pure refactor of `StreamerCard.tsx`; existing streamer badge behaviour must not change
- Label dict in CLI (T002) must use identical label strings as `injuryLabel` in the shared constants (T004) for consistency
