---
description: "Task list for Tomorrow's SP Streamer Card"
---

# Tasks: Tomorrow's SP Streamer Card

**Input**: Design documents from `specs/001-tomorrow-sp-streamer-card/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/streamers-api.md ✅

**Tests**: Not requested — no test tasks included.

**Organization**: Single user story. All implementation tasks belong to US1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1)
- File paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing infrastructure is ready before writing any code.

- [x] T001 Verify `GET /api/streamers?tomorrow=true` returns `{ "rows": [...] }` shape by starting dev stack (`docker compose -f docker-compose.dev.yml up`) and running `curl -H "X-API-Key: $API_KEY" "http://localhost:9471/api/streamers?tomorrow=true"`

**Checkpoint**: API returns expected shape — implementation can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

No new foundational infrastructure required. The API endpoint, response cache, `api.streamers(true)`
client method, `Card` component, and Tailwind setup all exist. Proceed directly to User Story 1.

---

## Phase 3: User Story 1 — View Tomorrow's Streaming Pitcher Recommendations (Priority: P1) 🎯 MVP

**Goal**: A "Tomorrow's SP Streamers" card appears on the dashboard, shows up to 8 pitchers for
tomorrow's games with tier, ownership, rank, and recommendation reason, and handles empty/error/loading states.

**Independent Test**: Open dashboard at http://localhost:9472 — a "Tomorrow's SP Streamers" card
renders alongside "SP Streamers". Pitchers display with colored tier labels. Empty state shows
"No streamers tomorrow." when no games scheduled.

### Implementation for User Story 1

- [x] T002 [P] [US1] Create `frontend/src/components/TomorrowStreamers.tsx` — independent component that calls `api.streamers(true)`, renders up to 8 rows with tierColor map, loading spinner via `Card` loading prop, inline error via `Card` error prop, and "No streamers tomorrow." empty state
- [x] T003 [US1] Add `TomorrowStreamers` import and `<TomorrowStreamers />` element to dashboard grid in `frontend/src/App.tsx`, placed immediately after the `<Streamers />` element (depends on T002)

**Checkpoint**: Dashboard shows both today's and tomorrow's SP Streamer cards. User Story 1 is
fully functional and independently testable.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Verify visual correctness and parity with the existing Streamers card.

- [x] T004 Visual validation: follow `specs/001-tomorrow-sp-streamer-card/quickstart.md` — confirm both cards render without layout regression on desktop (two-column) and mobile (single-column), tier colors match today's card, empty state is readable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run immediately
- **User Story 1 (Phase 3)**: Depends on Phase 1 confirming API shape — can start once T001 passes
- **Polish (Phase 4)**: Depends on T002 + T003 complete

### Within User Story 1

- T002: Write `TomorrowStreamers.tsx` — no file conflicts, can start immediately after T001
- T003: Wire into `App.tsx` — depends on T002 (needs the component to exist to import)
- T004: Visual check — depends on T002 + T003

### Parallel Opportunities

T002 has no dependency on any other in-progress task — it can be written while T001 API verification is running.

```bash
# T002 and T001 can overlap:
Task: "Verify API endpoint"             # T001 — confirms shape
Task: "Create TomorrowStreamers.tsx"    # T002 — safe to start immediately
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. T001 — Verify API endpoint
2. T002 — Create `TomorrowStreamers.tsx`
3. T003 — Wire into `App.tsx`
4. T004 — Visual validation
5. **DONE** — Feature complete, all acceptance criteria met

---

## Notes

- T002 should be a near-copy of `frontend/src/components/Streamers.tsx` with three changes:
  card title `"Tomorrow's SP Streamers"`, API call `api.streamers(true)`, and empty-state text
  `"No streamers tomorrow."` — per constitution Principle V (Simplicity First), no shared abstraction.
- [P] on T002 indicates it touches only the new file — no conflicts with any existing component.
- No backend changes, no new environment variables, no new dependencies.
