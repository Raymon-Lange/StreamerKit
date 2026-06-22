---
description: "Task list for streamer card sort order implementation"
---

# Tasks: Streamer Card Sort Order

**Input**: Design documents from `specs/009-streamer-card-sort-order/`

**Prerequisites**: plan.md ✅, spec.md ✅

**Tests**: Not requested — manual verification via the streamer cards.

**Organization**: Two user stories; both are satisfied by the same single-line service change (today's and tomorrow's cards both call `get_streaming_pitcher_review()`), so they are addressed in a single phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: User Story 1 + 2 — Sort Rows by PitcherList Rank (P1 + P2) 🎯 MVP

**Goal**: Players in the SP Streamers card (today and tomorrow) appear in ascending PitcherList rank order, with unranked players at the bottom.

**Independent Test (US1)**: Load today's streamer card and verify the player with the lowest `streamer_rank` value appears first; unranked players appear last.

**Independent Test (US2)**: Toggle to tomorrow's streamer card and verify the same ascending PitcherList rank ordering applies.

### Implementation

- [ ] T001 [US1] [US2] In `services/pitchers_service.py` line 332, change `payload["rows"] = rows` to `payload["rows"] = sorted(rows, key=_streamer_rank_sort_key)`

**Checkpoint**: US1 and US2 are both complete and independently verifiable after T001. The `_streamer_rank_sort_key` function already exists at line 165 and requires no changes.

---

## Phase 2: Polish & Verification

**Purpose**: Confirm sort order is correct end-to-end, including cache behavior.

- [ ] T002 [P] Start the dev stack (`docker compose -f docker-compose.dev.yml up`) and load `http://localhost:5173` — confirm the streamer card shows players in ascending rank order
- [ ] T003 [P] Toggle to tomorrow's streamers and confirm the same ascending rank order
- [ ] T004 Reload the page a second time (to hit the response cache) and confirm the row order is identical to the first load

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies — can start immediately.
- **Phase 2**: Depends on T001 completion.

### User Story Dependencies

- **US1 (P1)**: T001 — no prior dependencies.
- **US2 (P2)**: Satisfied by T001; the same `get_streaming_pitcher_review()` call handles both today and tomorrow.

### Within Each Phase

- T001 is the sole implementation task and unblocks all Phase 2 tasks.
- T002, T003, T004 are independent verifications and can run in parallel once T001 is done (except T004 which depends on T002 or T003 having loaded the page first).

---

## Parallel Example

```bash
# After T001 is complete, run verifications in parallel:
Task: "Load today's streamers and confirm rank order (T002)"
Task: "Load tomorrow's streamers and confirm rank order (T003)"
# Then:
Task: "Reload page to verify cache preserves sort order (T004)"
```

---

## Implementation Strategy

### MVP (Full feature = 1 task)

1. Complete T001 in `services/pitchers_service.py`
2. **STOP and VALIDATE**: Load both streamer cards and verify rank order
3. Done — feature is complete

### Incremental Delivery

This feature is a single atomic change; no incremental delivery is applicable.

---

## Notes

- T001 is the entire implementation — no new files, no new functions, no schema changes.
- `_streamer_rank_sort_key` (line 165 in `services/pitchers_service.py`) sorts by: rank ascending (9999 for unranked), then recommendation score descending, then name alphabetically. The tiebreaker is already correct.
- The response cache stores the full sorted payload; cache hits will return the correct order without any additional changes.
- The frontend `.slice(0, 8)` in `StreamerCard.tsx` runs after the API response, so sorting at the service layer ensures the top-8 displayed are always the best-ranked 8.
