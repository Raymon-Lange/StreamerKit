# Implementation Plan: Streamer Card Sort Order

**Branch**: `009-streamer-card-sort-order` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-streamer-card-sort-order/spec.md`

## Summary

Sort the rows returned by the `/api/streamers` endpoint by PitcherList rank (ascending), so the streamer cards always display players from best-ranked to unranked. The change is a single line in `services/pitchers_service.py` — applying the existing `_streamer_rank_sort_key` function to the final row list before it is returned. No schema changes, no new dependencies, no frontend changes required.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI (API layer), `services/pitchers_service.py` (business logic)

**Storage**: N/A — response cache is TTL-based and inherits the sorted order automatically

**Testing**: Manual — load the streamer card and verify rank-ascending order; no automated test suite is in place for this project

**Target Platform**: FastAPI service running in Docker

**Project Type**: Web application (React SPA + FastAPI backend)

**Performance Goals**: No change — sort over ≤ ~20 rows is negligible

**Constraints**: Sort must be applied before `payload["rows"]` is set, so the frontend `.slice(0, 8)` selects the top-8 by rank

**Scale/Scope**: One line in one file (`services/pitchers_service.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layer Separation | ✅ Pass | Change is in `services/` which coordinates collectors and engines — the correct layer for ordering decisions |
| II. Shared Data Model | ✅ Pass | No model changes; `streamer_rank` is already a field on serialized rows |
| III. Resilient External Data Access | ✅ Pass | Sort is applied after data is fetched; fallback behavior is unaffected |
| IV. Weighted Scoring | ✅ Pass | Not applicable — sort uses rank, not a new scoring formula |
| V. Simplicity First | ✅ Pass | Reuses the existing `_streamer_rank_sort_key` function; zero new abstraction |
| API/Auth Constraints | ✅ Pass | No API surface or auth changes |

No violations. Complexity Tracking table omitted.

## Project Structure

### Documentation (this feature)

```text
specs/009-streamer-card-sort-order/
├── plan.md              # This file
├── research.md          # Phase 0 output (N/A — no unknowns)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
services/
└── pitchers_service.py   # Only file modified — sort rows before returning payload
```

**Structure Decision**: Web application layout. The sole change is one line in `services/pitchers_service.py`; no frontend files, no new source files.

## Phase 0: Research

No NEEDS CLARIFICATION items. All decisions are resolved directly from the spec and codebase inspection:

| Decision | Rationale |
|----------|-----------|
| Modify `services/pitchers_service.py`, not `frontend/StreamerCard.tsx` | Per constitution Principle I, ordering decisions belong in the service layer, not the display layer. The sorted order should be consistent for any future consumer of the same API response. |
| Use `_streamer_rank_sort_key` | Already defined at line 165; already used for the same purpose at line 416 (`sorted_streamer_rows`). Zero duplication. |
| Apply sort at line 332 before `payload["rows"] = rows` | The frontend does `.slice(0, 8)` on the raw response; the sort must precede this slice so the top 8 displayed are always the best-ranked 8. |
| No tiebreaker change needed | `_streamer_rank_sort_key` already breaks ties by descending recommendation score then alphabetical name — a reasonable, stable default. |
| Response cache inherits sorted order | The cache stores the full `payload` dict; once sorted rows are cached, subsequent cache hits return the same order. No cache invalidation needed. |

## Phase 1: Design & Contracts

### Data Model

N/A — no new entities, no schema changes. `streamer_rank` (int | null) already exists on each serialized row.

### Interface Contracts

The `/api/streamers` endpoint contract is unchanged. The response shape is identical; only the ordering of the `rows` array changes (from percent-owned order to PitcherList-rank order). No client-side changes required.

### Implementation Detail

In `services/pitchers_service.py`, change line 332 from:

```python
payload["rows"] = rows
```

to:

```python
payload["rows"] = sorted(rows, key=_streamer_rank_sort_key)
```

That is the complete implementation.
