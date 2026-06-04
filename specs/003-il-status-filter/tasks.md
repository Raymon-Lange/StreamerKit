# Tasks: IL Status Filter for Free Agent Suggestions

**Input**: Design documents from `specs/003-il-status-filter/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | data-model.md ✅ | contracts/ ✅ | research.md ✅

**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks grouped by user story; foundational layer extracted as a blocking phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Maps to user story in spec.md (US1=waiver hitters, US2=SP streamers, US3=roster optimizer)

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Shared data model and collector changes that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T001 Add `injury_status: str | None = None` field to `PlayerRecord` dataclass in `models/player.py`
- [x] T002 Extract `injuryStatus` from ESPN player object and populate `injury_status` in `player_to_record()` in `collectors/espn.py`

**Checkpoint**: `PlayerRecord` now carries `injury_status`; all downstream code can reference it.

---

## Phase 2: User Story 1 — Surface injury labels for waiver wire hitters (Priority: P1) 🎯 MVP

**Goal**: Free agent hitter CLI output shows `[IR]`, `[DTD]`, `[OUT]`, `[SUSP]`, `[QUES]` labels
inline after player name for any non-ACTIVE player.

**Independent Test**: Run `python scripts/run_free_agent_hitters.py --top 15`. Find a player
with a known injury on ESPN; confirm the correct label appears next to their name. Confirm
healthy players show no label. Confirm IR/OUT/SUSP players still appear (not filtered out).

- [x] T003 [P] [US1] Add `"injury_status": player.injury_status` to the row dict returned by `_build_row()` in `services/hitters_service.py`
- [x] T004 [P] [US1] Add `_INJURY_LABEL` map and inline label to player name line in `scripts/run_free_agent_hitters.py`

**Checkpoint**: US1 fully functional — run the free agent hitter script and verify labeled output.

---

## Phase 3: User Story 2 — Surface injury labels for SP streamers (Priority: P2)

**Goal**: SP streamer CLI output shows injury labels. Web UI `Streamers` and `TomorrowStreamers`
cards display colored pills (red/orange/yellow) inline next to pitcher names.

**Independent Test**:
- CLI: Run `python scripts/run_sp_streamers.py` — injured pitchers show correct label.
- Web UI: Start dev stack (`docker compose -f docker-compose.dev.yml up`), open `:9472` —
  injured pitchers in SP Streamers card show colored badge. Healthy pitchers show no badge.

- [x] T005 [P] [US2] Add `"injury_status": player.injury_status` to the dict returned by `_serialize_pitcher_row()` in `services/pitchers_service.py`
- [x] T006 [P] [US2] Add `_INJURY_LABEL` map and inline label to player name line in both the single-pitcher path and list-mode path in `scripts/run_sp_streamers.py`
- [x] T007 [P] [US2] Add `injury_status: string | null` to `StreamerRow` interface, add `injuryColor`/`injuryLabel` maps, and render colored badge inline after player name in `frontend/src/components/Streamers.tsx`
- [x] T008 [P] [US2] Apply identical interface extension and badge render as T007 to `frontend/src/components/TomorrowStreamers.tsx`

**Checkpoint**: US2 fully functional — CLI labels and web UI badges both working for SP streamers.

---

## Phase 4: User Story 3 — Roster optimizer skips severely injured players (Priority: P3)

**Goal**: `get_roster_optimizer()` filters out players with `INJURY_RESERVE`, `OUT`, or
`SUSPENSION` status before scoring, so they never surface as START recommendations.

**Independent Test**: Run `python scripts/run_team_hitter_eval.py`. Confirm no player whose
ESPN status is `INJURY_RESERVE`, `OUT`, or `SUSPENSION` appears as a START recommendation.

- [x] T009 [US3] Add `_IL_EXCLUDE` set and filter `hitters` list after `get_roster_players()` call, before scoring loop, in `services/optimizer_service.py`

**Checkpoint**: US3 fully functional — roster optimizer start recommendations contain no severely injured players.

---

## Phase 5: Polish & Verification

**Purpose**: End-to-end validation across all three user stories.

- [x] T010 [P] Verify healthy (`ACTIVE` / `None`) players produce identical CLI output to pre-change behavior in both `run_free_agent_hitters.py` and `run_sp_streamers.py` — no extra characters or labels
- [x] T011 [P] Verify web UI renders no badge for healthy pitchers in `Streamers.tsx` and `TomorrowStreamers.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately. **Blocks all user stories.**
- **US1 (Phase 2)**: Requires Phase 1 complete. T003 and T004 can run in parallel.
- **US2 (Phase 3)**: Requires Phase 1 complete. T005, T006, T007, T008 can all run in parallel.
- **US3 (Phase 4)**: Requires Phase 1 complete. Single task (T009).
- **Polish (Phase 5)**: Requires all desired stories complete.

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 1 only. No dependency on US2 or US3.
- **US2 (P2)**: Depends on Phase 1 only. No dependency on US1 or US3.
- **US3 (P3)**: Depends on Phase 1 only. No dependency on US1 or US2.

All three user stories can be worked in parallel once Phase 1 is complete.

---

## Parallel Example: Phase 3 (US2 — SP Streamers)

All four tasks touch different files and can be executed concurrently:

```text
T005 — services/pitchers_service.py
T006 — scripts/run_sp_streamers.py
T007 — frontend/src/components/Streamers.tsx
T008 — frontend/src/components/TomorrowStreamers.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Foundational (T001, T002) — ~10 min
2. Complete Phase 2: US1 (T003, T004) — ~10 min
3. **STOP and VALIDATE**: Run `python scripts/run_free_agent_hitters.py --top 15`
4. MVP delivered: waiver wire hitter output shows injury labels

### Full Delivery (all three stories)

1. Phase 1 → Phase 2 (US1) → Phase 3 (US2, all [P] in parallel) → Phase 4 (US3) → Phase 5
2. Estimated: ~45–60 min total across all 11 tasks

### Key Implementation Notes

- `_INJURY_LABEL` map defined in each script (not a shared helper — scripts are thin CLI entry points per constitution)
- `_IL_EXCLUDE` set in `optimizer_service.py` mirrors the existing `_BENCH_SLOTS` guard pattern in the same file
- Web badge color classes: red=`bg-red-900 text-red-300`, orange=`bg-orange-900 text-orange-300`, yellow=`bg-yellow-900 text-yellow-300`
- Badge text (no brackets): `IR`, `OUT`, `SUSP`, `DTD`, `QUES`
- CLI labels (with brackets): `[IR]`, `[OUT]`, `[SUSP]`, `[DTD]`, `[QUES]`
