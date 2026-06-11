# Implementation Plan: Add Analytics Tracking

**Branch**: `008-add-analytics-tracking` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-add-analytics-tracking/spec.md`

## Summary

Add the Fire-Hive analytics tracking script to the frontend entry point so that page visits to the main StreamerKit dashboard are recorded. The change is a single deferred `<script>` tag added to `frontend/index.html`. No application logic, data model, or API surface is affected.

## Technical Context

**Language/Version**: TypeScript 5.7 / React 18.3 (Vite 6)

**Primary Dependencies**: Vite, React — no new dependencies required

**Storage**: N/A

**Testing**: Manual — verify event appears in Fire-Hive dashboard after page load

**Target Platform**: Browser (served via Docker container, Vite dev server for development)

**Project Type**: Web application (React SPA + FastAPI backend)

**Performance Goals**: Script must load asynchronously (`defer`) — no blocking of initial render

**Constraints**: The tracking snippet must not increase time-to-interactive; failure of the external script must not surface errors to the user

**Scale/Scope**: Single HTML entry point (`frontend/index.html`); one-line change

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layer Separation | ✅ Pass | Change is confined to `frontend/index.html` — no Python layer touched |
| II. Shared Data Model | ✅ Pass | No data exchange involved |
| III. Resilient External Data Access | ✅ Pass | Script loads with `defer`; page renders regardless of script success |
| IV. Weighted Scoring | ✅ Pass | Not applicable |
| V. Simplicity First | ✅ Pass | Single-file, single-line change — no abstraction introduced |
| API/Auth Constraints | ✅ Pass | No API key or credential involved |

No violations. Complexity Tracking table is omitted.

## Project Structure

### Documentation (this feature)

```text
specs/008-add-analytics-tracking/
├── plan.md              # This file
├── research.md          # Phase 0 output (N/A — no unknowns)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
frontend/
└── index.html           # Only file modified — add <script> tag to <head>
```

**Structure Decision**: Web application layout. The sole change is `frontend/index.html`; no backend files, no new source files.

## Phase 0: Research

No NEEDS CLARIFICATION items and no external dependencies to evaluate. All decisions are resolved directly from the spec and codebase inspection:

| Decision | Rationale |
|----------|-----------|
| Modify `frontend/index.html` (not a React component) | Analytics scripts belong at the document level, not inside the React component tree. The `<head>` in `index.html` is the correct insertion point for Vite-based SPAs. |
| Use `defer` attribute | Matches spec FR-002 (async load, no render blocking). The Fire-Hive script tag already specifies `defer`. |
| No environment variable for site ID | The site ID is a public identifier (equivalent to a GA measurement ID) — it carries no security risk and does not vary by environment. Hardcoding it in `index.html` is the standard pattern. |
| No new npm package required | Fire-Hive (Umami-based) is a script-tag integration; no SDK install needed. |

## Phase 1: Design & Contracts

### Data Model

N/A — no new entities, no schema changes.

### Interface Contracts

N/A — the analytics integration is outbound-only (browser to Fire-Hive). No new endpoints, CLI commands, or public interfaces are introduced.

### Implementation Detail

Insert the following tag inside `<head>` in `frontend/index.html`, before the closing `</head>`:

```html
<script defer src="https://analytics.fire-hive.com/script" data-website-id="8119c720-a52b-492f-8fb0-c6389b3cf3bf"></script>
```

That is the complete implementation.
