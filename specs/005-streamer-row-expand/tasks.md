# Tasks: Expandable Streamer Pitcher Row

**Input**: Design documents from `specs/005-streamer-row-expand/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Scope**: 1 new file (`StreamerCard.tsx`), 2 simplified wrappers. No backend changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Foundational — Shared StreamerCard Component

**Purpose**: Create the `StreamerCard.tsx` component that both wrappers depend on. Must be complete before US1 or US2 can be wired up.

**⚠️ CRITICAL**: Both wrapper simplification tasks (T002, T003) depend on this phase.

- [x] T001 Create `frontend/src/components/StreamerCard.tsx` with the full `StreamerRow` interface (including `season_record`, `last_ten_record`, `last_two_starts`, `opponent_team`, `opponent_score`), `tomorrow?: boolean` prop, all existing constants (`tierColor`, `injuryColor`, `injuryLabel`, `DAYS`, label functions), data fetch via `api.streamers(tomorrow)`, and the compact row render (identical layout to current `Streamers.tsx`)

**Checkpoint**: `StreamerCard` renders correctly as a drop-in for today's streamers before any expand logic is added.

---

## Phase 2: User Story 1 — Click-to-Expand/Collapse Row (Priority: P1) 🎯 MVP

**Goal**: Each pitcher row in both streamer cards is clickable and expands/collapses inline.

**Independent Test**: Click any row in SP Streamers → row expands below the compact summary. Click again → collapses. Click a second row → first collapses, second expands.

### Implementation

- [x] T002 [US1] Add `expandedName: string | null` state and click handler (`onClick={() => setExpandedName(prev => prev === r.name ? null : r.name)}`) to each row `<div>` in `frontend/src/components/StreamerCard.tsx`; add `cursor-pointer select-none` to row div
- [x] T003 [US1] Add chevron indicator (`›` character with `inline-block transition-transform duration-150` and conditional `rotate(90deg)` style) to the right-side column of each row in `frontend/src/components/StreamerCard.tsx`
- [x] T004 [US1] Add expanded section below compact row content in `frontend/src/components/StreamerCard.tsx`: renders when `expandedName === r.name`, uses a 2-column grid showing Season, Last 10, Last 2 starts, and Opponent fields with `?? '—'` fallback for null values
- [x] T005 [P] [US1] Simplify `frontend/src/components/Streamers.tsx` to a thin wrapper: import `StreamerCard`, return `<StreamerCard />`
- [x] T006 [P] [US1] Simplify `frontend/src/components/TomorrowStreamers.tsx` to a thin wrapper: import `StreamerCard`, return `<StreamerCard tomorrow />`

**Checkpoint**: Both streamer cards show clickable rows with chevrons. Expand/collapse works. One row open at a time. Compact view unchanged for collapsed rows.

---

## Phase 3: User Story 2 — Null/Missing Data Renders as "—" (Priority: P2)

**Goal**: Every null or missing field in the expanded section shows `—` — no raw null, blank, or "undefined" visible.

**Independent Test**: Expand a row for a pitcher with missing opponent data — all null fields show `—`.

### Implementation

- [x] T007 [US2] Audit all expanded section fields in `frontend/src/components/StreamerCard.tsx` to confirm `?? '—'` fallback is applied to every nullable field (`season_record`, `last_ten_record`, `last_two_starts`, `opponent_team`); confirm `opponent_score` only appended when non-null

**Checkpoint**: Null fields show `—` consistently. No raw nulls or blanks in expanded view.

---

## Phase 4: Polish

- [ ] T008 Run full verification per `specs/005-streamer-row-expand/quickstart.md` — all 11 steps including mobile at 375px, null handling, and regression check on compact view appearance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No prerequisites — start immediately
- **Phase 2 (US1)**: Depends on T001 (StreamerCard must exist before wiring expand logic or wrappers)
- **Phase 3 (US2)**: Can begin once T004 is done (expanded section must exist to audit null handling)
- **Phase 4 (Polish)**: Depends on all phases complete

### Within Phase 2

- T002, T003, T004 are sequential within `StreamerCard.tsx` (same file)
- T005 and T006 are marked [P] — different files, can be done in parallel once T001 is done

### Within Phase 3

- T007 is a review/audit of T004's output — no new file creation needed

---

## Parallel Example: Phase 2

```text
# After T001–T004 complete (StreamerCard with expand logic):
T005 — Streamers.tsx (wrapper)      ← parallel
T006 — TomorrowStreamers.tsx (wrapper)  ← parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: T001 — create StreamerCard (foundational)
2. Complete Phase 2: T002–T006 — expand/collapse + wire wrappers
3. **STOP and VALIDATE**: Open dev server, click rows, confirm expand/collapse
4. Ship if ready

### Incremental Delivery

1. T001 → StreamerCard renders correctly (same as before, just refactored)
2. T002–T004 → add expand state + chevron + expanded section
3. T005–T006 → wire wrappers (both cards now have expand behavior)
4. T007 → null-handling audit
5. T008 → full sign-off

---

## Notes

- [P] tasks = different files or no sequential dependency within the phase
- T002, T003, T004 edit the same file (`StreamerCard.tsx`) — do them in order in a single session
- T005 and T006 edit different files — safe to do in parallel
- All data fields (`season_record` etc.) are already returned by the API; no API changes needed
- Verification references `specs/005-streamer-row-expand/quickstart.md`
