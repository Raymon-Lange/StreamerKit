# Tasks: Mobile Responsive Card Layout

**Input**: Design documents from `specs/004-mobile-responsive-layout/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, quickstart.md ✅

**Scope**: 3 files, 4 Tailwind class changes. No setup or foundational phase required — changes go directly into user story phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: User Story 1 — Single-Column Layout on Small Screens (Priority: P1) 🎯 MVP

**Goal**: All 7 dashboard cards render in a single column at viewport widths below 1024px, with no overflow.

**Independent Test**: Open DevTools, set viewport to 375px — all cards stack vertically in one column.

### Implementation

- [x] T001 [US1] Change main grid breakpoint from `md:grid-cols-2` to `lg:grid-cols-2` in `frontend/src/App.tsx` (line 17)
- [x] T002 [P] [US1] Change `col-span-2` to `col-span-1 lg:col-span-2` on the `<Card>` element in `frontend/src/components/DailyBrief.tsx` (line 48)
- [x] T003 [P] [US1] Change internal stat grid from `md:grid-cols-4` to `lg:grid-cols-4` in `frontend/src/components/DailyBrief.tsx` (line 50)
- [x] T004 [P] [US1] Change `col-span-2` to `col-span-1 lg:col-span-2` on the `<Card>` element in `frontend/src/components/Profile.tsx` (line 30)

**Checkpoint**: Start dev server (`cd frontend && npm run dev`), open at 375px width — all cards should be single-column with no horizontal scroll.

---

## Phase 2: User Story 2 — No Horizontal Overflow on Small Screens (Priority: P2)

**Goal**: Confirm no card or inner element forces horizontal overflow at any narrow viewport.

**Independent Test**: At 375px width, browser shows no horizontal scrollbar and no element extends past the viewport edge.

### Verification

- [x] T005 [US2] Verify single-column layout at 375px viewport using `specs/004-mobile-responsive-layout/quickstart.md` small-screen steps
- [x] T006 [US2] Verify breakpoint transition: one-column at 1023px, two-column at 1024px per quickstart.md breakpoint steps
- [x] T007 [US2] Verify desktop layout intact at 1280px: DailyBrief and Profile span full width, remaining cards two-per-row, DailyBrief stats in 4 columns

**Checkpoint**: All three viewport checks pass — layout is correct across the full width range.

---

## Phase 3: Polish

- [x] T008 Run full end-to-end walkthrough in `specs/004-mobile-responsive-layout/quickstart.md` at all four specified widths (375px, 1023px, 1024px, 1280px)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No prerequisites — start immediately
- **Phase 2 (US2)**: Depends on Phase 1 completion (changes must be in place to verify)
- **Phase 3 (Polish)**: Depends on Phase 2 completion

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — start immediately
- **User Story 2 (P2)**: Verification of US1 changes — start after T001–T004 are complete

### Within User Story 1

- T001 can start independently
- T002, T003, T004 are marked [P] — all touch different files and can be done in any order alongside T001 (T003 is a second change in the same file as T002 and should follow T002 in practice)

---

## Parallel Example: User Story 1

```text
# All four implementation tasks can be done in a single pass:
T001 — App.tsx (grid breakpoint)
T002 — DailyBrief.tsx (col-span on Card)
T003 — DailyBrief.tsx (internal stat grid)
T004 — Profile.tsx (col-span on Card)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: User Story 1 (T001–T004) — 4 class changes, ~5 minutes
2. **STOP and VALIDATE**: Open dev server at 375px — confirm single-column stacking
3. Ship if ready

### Incremental Delivery

1. Apply T001–T004 → verify US1 at 375px → MVP complete
2. Run T005–T007 → verify US2 overflow behavior at all breakpoints
3. Run T008 → full end-to-end sign-off

---

## Notes

- [P] tasks = different files or no sequential dependency
- T003 is in the same file as T002 — complete T002 first, then T003 in the same editing session
- No backend, API, data model, or Docker changes required
- Verification references `specs/004-mobile-responsive-layout/quickstart.md` for exact viewport widths and expected outcomes
