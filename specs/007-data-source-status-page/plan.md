# Implementation Plan: Data Source Status Page

**Branch**: `007-data-source-status-page` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

## Summary

Add a second page to the StreamerKit web app showing two cards: (1) feed health for all tracked collector data sources, and (2) a response cache inspector for short-lived API cache entries. A new `GET /api/feed-status` endpoint powers both cards, reusing logic currently in `scripts/show_feed_health.py` via a new `services/feed_health_service.py`. The frontend gains tab-based navigation between the existing dashboard and the new feed status page.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript (frontend)

**Primary Dependencies**: FastAPI, React + Vite, SQLite (via `utils/cache_store.py`)

**Storage**: SQLite `.cache/cache.db` — existing `CacheStore` with `collector`, `response`, and `feed_failures` namespaces

**Testing**: pytest (backend); no frontend test suite currently exists

**Target Platform**: Linux server + web browser (single-user tool)

**Project Type**: Web service (FastAPI) + SPA (React/Vite)

**Performance Goals**: Feed status page loads in under 2 seconds; no real-time polling required

**Constraints**: API key authenticated (`X-API-Key`); read-only page (no cache mutation from UI); single-user

**Scale/Scope**: Handful of tracked data sources; response cache holds O(10s) of entries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Layer Separation | ✅ Pass | New route in `app/routes/` calls `services/feed_health_service.py`. Service reads `utils/cache_store` directly (no HTTP). Script calls the same service. No cross-layer leakage. |
| II. Shared Data Model | ✅ Pass | New `models/feed_health.py` defines `FeedSource`, `CacheEntry`, `FeedHealthSnapshot` as `@dataclass(slots=True)`. Service returns these; route serialises to dict. |
| III. Resilient External Data Access | ✅ N/A | This feature reads local cache only — no external HTTP calls. |
| IV. Weighted Scoring | ✅ N/A | No scoring or recommendation logic. |
| V. Simplicity First | ✅ Pass | Logic extracted from the existing script into a service that both the script and route call. No new abstractions beyond what is immediately needed. |
| API Constraints | ✅ Pass | New endpoint registered under `/api` with `verify_api_key` dependency, same as all other protected routes. |
| Dev Workflow | ✅ Pass | New script entry point not needed (feature is a UI page, not a new CLI workflow). Existing `show_feed_health.py` delegates to the shared service. |

**Post-design re-check**: No violations introduced by Phase 1 design. Complexity Tracking table omitted (no violations).

## Project Structure

### Documentation (this feature)

```text
specs/007-data-source-status-page/
├── plan.md              ← this file
├── research.md          ← Phase 0
├── data-model.md        ← Phase 1
├── contracts/
│   └── feed-status-api.md   ← Phase 1
└── tasks.md             ← Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
models/
└── feed_health.py           ← NEW: FeedSource, CacheEntry, FeedHealthSnapshot

services/
└── feed_health_service.py   ← NEW: build_snapshot() — shared by script and route

app/routes/
└── feed_status.py           ← NEW: GET /api/feed-status

app/
└── main.py                  ← EDIT: register feed_status router

scripts/
└── show_feed_health.py      ← EDIT: delegate to feed_health_service.build_snapshot()

frontend/src/
├── api.ts                   ← EDIT: add feedStatus()
├── App.tsx                  ← EDIT: add tab nav + page switch
└── components/
    ├── FeedSourcesCard.tsx  ← NEW: Card 1 — collector feed health
    └── ResponseCacheCard.tsx← NEW: Card 2 — response cache inspector

tests/
└── (no new tests required for this read-only, single-user tool)
```

**Structure Decision**: Web application layout. Backend changes are confined to `models/`, `services/`, and `app/routes/`. Frontend changes are confined to `frontend/src/`. The existing `scripts/show_feed_health.py` is refactored to call the new service rather than duplicate logic.
