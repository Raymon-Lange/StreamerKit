---
description: "Task list for analytics tracking implementation"
---

# Tasks: Add Analytics Tracking

**Input**: Design documents from `specs/008-add-analytics-tracking/`

**Prerequisites**: plan.md ✅, spec.md ✅

**Tests**: Not requested — manual verification via Fire-Hive dashboard.

**Organization**: Two user stories; US2 (build persistence) is automatically satisfied by the same source edit as US1, so both are addressed in a single phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: User Story 1 + 2 — Track Visits & Persist Across Builds (P1 + P2) 🎯 MVP

**Goal**: Add Fire-Hive page-view tracking to the main page. Because the tag is added to the HTML source file (not a build artifact), build persistence (US2) is inherently satisfied by the same change.

**Independent Test (US1)**: Load the app, open the Fire-Hive dashboard for site `8119c720-a52b-492f-8fb0-c6389b3cf3bf`, and confirm a page view event appears within 30 seconds.

**Independent Test (US2)**: Run `npm run build` inside `frontend/`, then verify the built `dist/index.html` contains the Fire-Hive script tag.

### Implementation

- [ ] T001 [US1] Add `<script defer src="https://analytics.fire-hive.com/script" data-website-id="8119c720-a52b-492f-8fb0-c6389b3cf3bf"></script>` inside `<head>` in `frontend/index.html`

**Checkpoint**: US1 and US2 are both complete and independently verifiable after T001.

---

## Phase 2: Polish & Verification

**Purpose**: Confirm end-to-end tracking works in the live environment.

- [ ] T002 [P] Start the dev server (`npm run dev` in `frontend/`) and load `http://localhost:5173` — confirm no console errors related to the analytics script
- [ ] T003 [P] Open the Fire-Hive analytics dashboard and confirm a page view event is recorded for site `8119c720-a52b-492f-8fb0-c6389b3cf3bf`
- [ ] T004 Run `npm run build` in `frontend/` and verify the script tag is present in `frontend/dist/index.html`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies — can start immediately.
- **Phase 2**: Depends on T001 completion.

### User Story Dependencies

- **US1 (P1)**: T001 — no prior dependencies.
- **US2 (P2)**: Satisfied by T001 (source edit persists through builds); T004 verifies it.

### Within Each Phase

- T001 is the sole implementation task and unblocks all Phase 2 tasks.
- T002, T003, T004 are independent verifications and can run in parallel once T001 is done.

---

## Parallel Example

```bash
# After T001 is complete, run all verifications in parallel:
Task: "Start dev server and confirm no console errors (T002)"
Task: "Confirm page view in Fire-Hive dashboard (T003)"
Task: "Build frontend and verify dist/index.html (T004)"
```

---

## Implementation Strategy

### MVP (Full feature = 1 task)

1. Complete T001 in `frontend/index.html`
2. **STOP and VALIDATE**: Check Fire-Hive dashboard for page view event
3. Done — feature is complete

### Incremental Delivery

This feature is a single atomic change; no incremental delivery is applicable.

---

## Notes

- T001 is the entire implementation — no new files, no new dependencies, no Python changes.
- The site ID `8119c720-a52b-492f-8fb0-c6389b3cf3bf` is a public tracking identifier; hardcoding it directly in `index.html` is correct (not a secret).
- The `defer` attribute is required by spec FR-002 to prevent render blocking.
