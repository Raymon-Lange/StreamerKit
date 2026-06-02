# Implementation Plan: Tomorrow's SP Streamer Card

**Branch**: `001-tomorrow-sp-streamer-card` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-tomorrow-sp-streamer-card/spec.md`

## Summary

Add a "Tomorrow's SP Streamers" dashboard card that displays free-agent starting pitcher
streaming recommendations for tomorrow's games. The card is an independent React component
(`TomorrowStreamers.tsx`) that calls the existing `/api/streamers?tomorrow=true` endpoint and
mirrors the visual layout of the existing `Streamers.tsx` (today) card. No backend changes required.

## Technical Context

**Language/Version**: TypeScript (React 18, Vite)

**Primary Dependencies**: React, Tailwind CSS, existing `api.streamers(true)` client method

**Storage**: N/A — stateless fetch from existing API; API response is cached server-side for 5 min

**Testing**: No tests requested for this feature

**Target Platform**: Web browser (React SPA served from Vite dev server / Docker container)

**Project Type**: Web application — frontend card addition

**Performance Goals**: Match existing Streamers card; data load visually indistinguishable
from today's card (server-side 5-min TTL cache already in place)

**Constraints**: Frontend-only; no backend changes; no new environment variables

**Scale/Scope**: Single user; personal fantasy baseball dashboard

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layer Separation | ✅ Pass | New code is `frontend/src/components/` only. `app/routes/streamers.py` already handles `tomorrow=true`. No layer boundary crossed. |
| II. Shared Data Model | ✅ Pass | Reuses existing `StreamerRow` TypeScript interface. No new Python dataclass needed (frontend feature). |
| III. Resilient External Data Access | ✅ Pass | Relies on existing `/api/streamers` with its 5-min `response_cache` TTL. No new data-access patterns introduced. |
| IV. Weighted Intent-Aware Scoring | N/A | Display-only frontend feature; scoring happens in the existing engine layer. |
| V. Simplicity First | ✅ Pass | Independent `TomorrowStreamers.tsx` per user clarification — no shared abstraction with `Streamers.tsx`. Aligns with "similar lines > premature helper." |

**Gate result**: All applicable gates pass. No Complexity Tracking justification required.

## Project Structure

### Documentation (this feature)

```text
specs/001-tomorrow-sp-streamer-card/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── streamers-api.md # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
frontend/
└── src/
    ├── api.ts                          # existing — no changes needed
    ├── App.tsx                         # add <TomorrowStreamers /> to grid
    └── components/
        ├── Streamers.tsx               # existing today card — no changes
        └── TomorrowStreamers.tsx       # NEW — independent tomorrow card
```

**Structure Decision**: Web application (Option 2 layout). Change is confined to
`frontend/src/components/` (new file) and `frontend/src/App.tsx` (one import + one JSX element).
