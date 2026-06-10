# Tasks: Data Source Status Page

**Branch**: `007-data-source-status-page`
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (touches different files, no blocking dependencies)
- **[US1]**: User Story 1 — View Data Source Health
- **[US2]**: User Story 2 — Inspect Short-Lived API Cache

---

## Phase 1: Setup

**Purpose**: No new directories are needed — `models/`, `services/`, `app/routes/`, and `frontend/src/components/` all already exist. This phase is a single orientation check.

- [x] T001 Confirm no file naming conflicts: verify `models/feed_health.py`, `services/feed_health_service.py`, `app/routes/feed_status.py`, `frontend/src/components/FeedSourcesCard.tsx`, `frontend/src/components/ResponseCacheCard.tsx` do not yet exist

---

## Phase 2: Foundational (Backend API)

**Purpose**: Build the shared API layer that powers both cards. Neither user story can be tested end-to-end until this phase is complete.

**⚠️ CRITICAL**: US1 and US2 both depend on `GET /api/feed-status`. Complete this phase first.

- [x] T002 [P] Create `models/feed_health.py` with `@dataclass(slots=True)` types: `FeedSource`, `CacheEntry`, `FeedHealthSnapshot` — fields per `data-model.md`
- [x] T003 Create `services/feed_health_service.py` with `build_snapshot() -> FeedHealthSnapshot` — extracts collector cache query logic from `scripts/show_feed_health.py`; reads `utils/cache_retention.RETENTION` and `utils/cache_store.store`; returns `FeedHealthSnapshot` (depends on T002)
- [x] T004 Refactor `scripts/show_feed_health.py` to call `feed_health_service.build_snapshot()` and print the result, removing duplicated cache-query logic (depends on T003)
- [x] T005 Create `app/routes/feed_status.py` with `GET /api/feed-status` route: calls `feed_health_service.build_snapshot()`, returns `dataclasses.asdict(snapshot)` — no response cache (always live); per `contracts/feed-status-api.md` (depends on T003)
- [x] T006 Register `feed_status` router in `app/main.py` under `/api` prefix with `verify_api_key` dependency (depends on T005)

**Checkpoint**: `GET /api/feed-status` should return a valid `FeedHealthSnapshot` JSON payload. Verify with `curl -H "X-API-Key: $API_KEY" http://localhost:9471/api/feed-status`.

---

## Phase 3: User Story 1 — View Data Source Health (Priority: P1) 🎯 MVP

**Goal**: A second page in the app with a feed sources card showing every tracked data source, its freshness status, age, TTL, and any recorded error — with a per-card Refresh button.

**Independent Test**: Navigate to the Feed Status tab. Confirm all 5 sources from `utils/cache_retention.RETENTION` appear. Confirm the Refresh button re-fetches and re-renders the card without reloading the other card or navigating away.

- [x] T007 [P] [US1] Add `feedStatus: () => apiFetch('/api/feed-status')` to `frontend/src/api.ts`
- [x] T008 [P] [US1] Add two-tab header navigation to `frontend/src/App.tsx`: `Dashboard` and `Feed Status` tabs using `useState`; render either the existing dashboard grid or a new Feed Status page container based on active tab (depends on T006)
- [x] T009 [US1] Create `frontend/src/components/FeedSourcesCard.tsx`: fetches from `api.feedStatus()`, renders one row per source with colour-coded status badge (fresh=green, stale=amber, missing=red), age and TTL formatted as human-readable strings, error type and timestamp if present, loading state, error state, and a Refresh button that re-calls `api.feedStatus()` (depends on T007, T008)
- [x] T010 [US1] Wire `FeedSourcesCard` into the Feed Status page container in `frontend/src/App.tsx` (depends on T009)

**Checkpoint**: Feed Status tab renders. All tracked sources show. Clicking Refresh on the feed sources card re-fetches independently.

---

## Phase 4: User Story 2 — Inspect Short-Lived API Cache (Priority: P2)

**Goal**: A second card on the Feed Status page listing all non-expired API response cache entries (key, age, remaining TTL), with an empty-state when the cache is cold and a per-card Refresh button.

**Independent Test**: Navigate to Feed Status tab. Confirm the response cache card appears alongside the feed sources card. When no non-expired entries exist, confirm the empty-state message is shown. Clicking Refresh re-fetches only this card.

- [x] T011 [US2] Create `frontend/src/components/ResponseCacheCard.tsx`: reads `response_cache` array from `api.feedStatus()` response, renders each entry with key name, age, and remaining TTL; shows empty-state message when array is empty; includes a Refresh button that re-calls `api.feedStatus()` for this card only (depends on T007, T008)
- [x] T012 [US2] Wire `ResponseCacheCard` into the Feed Status page container in `frontend/src/App.tsx` alongside `FeedSourcesCard` (depends on T010, T011)

**Checkpoint**: Both cards appear side-by-side on the Feed Status page. Refresh buttons on each card operate independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T013 [P] Verify `scripts/show_feed_health.py` output still matches the API response — run both against the same cache state and confirm consistency (SC-005)
- [x] T014 Build frontend with `npm run build` and smoke-test the production build end-to-end: navigate to both tabs, verify no console errors, confirm existing dashboard cards remain unaffected (SC-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks both user stories**
- **Phase 3 (US1)**: Depends on Phase 2 completion
- **Phase 4 (US2)**: Depends on Phase 3 completion (shares `App.tsx` page container)
- **Phase 5 (Polish)**: Depends on Phase 4 completion

### Within Phase 2

```
T002 (models) ──► T003 (service) ──► T004 (script refactor)
                              └──► T005 (route) ──► T006 (register)
```

### Within Phase 3 (US1)

```
T006 (register) ─────────────────────────────────┐
T007 (api.ts) [P] ──┐                             │
T008 (App.tsx) [P] ─┤── T009 (FeedSourcesCard) ──► T010 (wire card)
```

### Parallel Opportunities

- T002 (models) and T007 (api.ts feedStatus) and T008 (App.tsx nav shell) have no inter-dependencies and can start in parallel once Phase 1 is done
- T004 (script refactor) and T005 (route) can proceed in parallel after T003

---

## Notes

- [P] tasks touch different files and have no blocking dependencies on each other
- US1 and US2 share the same API endpoint — the endpoint is foundational, not story-specific
- Both Refresh buttons call the same API endpoint but maintain independent loading state per card
- No auto-polling: the page is static until the user clicks Refresh on a specific card
- `scripts/show_feed_health.py` must continue to work after T004 (T013 validates this)
