<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE] → 1.0.0 (initial population from blank template)

Modified principles: N/A (first-time fill — no prior principles to rename)

Added sections:
  - Core Principles (I–V)
  - API & Deployment Constraints
  - Development Workflow
  - Governance

Removed sections: N/A

Templates reviewed:
  - .specify/templates/plan-template.md   ✅ no changes needed (Constitution Check section is dynamic)
  - .specify/templates/spec-template.md   ✅ no changes needed
  - .specify/templates/tasks-template.md  ✅ no changes needed
  - .specify/templates/commands/          ✅ directory does not exist — skipped

Follow-up TODOs: none — all placeholders resolved
-->

# Fantasy Baseball Tools Constitution

## Core Principles

### I. Layer Separation (NON-NEGOTIABLE)

Every module MUST belong to exactly one layer and MUST NOT cross layer boundaries:

- `collectors/` fetch and normalize external data only — no recommendation logic, no scoring.
- `engines/` contain recommendation and scoring logic only — no HTTP requests, no ESPN access.
- `services/` coordinate collectors and engines for reusable multi-step workflows — no raw HTTP calls.
- `scripts/` are thin CLI entry points — argument parsing, one service/engine call, print result. No business logic.
- `app/` exposes the FastAPI REST layer — route handlers delegate to services, not directly to engines or collectors.

**Rationale**: Layer violations have historically caused ESPN auth logic to leak into scoring code and
HTTP calls to appear inside engines, making unit testing and offline development impossible.

### II. Shared Data Model

All inter-module data exchange MUST use the canonical types defined in `models/player.py`:
`PlayerRecord`, `RankingEntry`, `TrendSummary`, `Recommendation`, `LineupSwap`.

Ad hoc `dict` payloads are NOT permitted across module boundaries.

All cross-source player-name joins MUST use `normalize_name()` from `utils/names.py`. Raw name
strings MUST NOT be compared directly between collectors or between a collector and an engine.

Model classes are `@dataclass(slots=True)` value objects. Business logic MUST NOT be added to them.

**Rationale**: Inconsistent name handling caused silent join failures between ESPN, Pitcher List,
and MLB Stats data. A single normalization point makes failures visible at the join site.

### III. Resilient External Data Access

Ranking collectors MUST cache responses locally under `.cache/` with a 15-day TTL. On any refresh
failure, a collector MUST fall back to the existing cached payload rather than raising.

The keeper-cost cache (`espn_keeper_cost_<league_id>_<year>.json`) is intentionally write-once
for the season — it MUST NOT be TTL-expired or auto-refreshed.

ESPN auth credentials (`ESPN_S2`, `SWID`, `LEAGUE_ID`, `TEAM_ID`) MUST be sourced from environment
variables loaded via `.env`. They MUST NOT be hardcoded or logged.

**Rationale**: External data sources (ESPN private API, Pitcher List articles, MLB Stats API) are
unreliable during the season. Offline fallback is essential for nightly or automated runs.

### IV. Weighted, Intent-Aware Scoring

All hitter recommendations MUST use three named scoring buckets:
`current_performance`, `current_year_rankings`, `dynasty_rankings`.

Weights MUST be caller-configurable via CLI flags (`--weight-current-performance`, etc.).
When a player is missing a ranking source, that bucket score MUST resolve to `0` —
weight MUST NOT be reallocated to other buckets.

Default weight profiles are fixed per script intent (waiver: `45/40/15`, team eval: `30/25/45`).
New scripts introducing a different intent MUST define and document their default weights explicitly.

**Rationale**: Silent weight reallocation masked under-ranked players as highly recommended. Zero-
fallback makes data gaps explicit in the score output rather than hiding them.

### V. Simplicity First

New abstraction layers, base classes, or plugin patterns require a concrete, immediate justification.
Hypothetical future use cases do not qualify.

Scripts MUST stay thin: parse args → call service or engine → print. Any logic that would repeat
across two or more scripts belongs in `services/` or `engines/`, not in a shared script helper.

Three similar lines in a script are better than a premature shared helper that obscures intent.

**Rationale**: This is a solo-developer tooling project with a narrow domain. Complexity compounds
quickly when abstractions are added speculatively; readability and debuggability outweigh DRY purity.

## API & Deployment Constraints

The FastAPI layer in `app/` MUST authenticate all `/api/*` requests via the `X-API-Key` header.
The key MUST be sourced from the `API_KEY` environment variable — never hardcoded, never logged,
never returned in API responses.

The response cache (`app/response_cache.py`) MUST be used to avoid redundant upstream calls within
a single API session. Cache invalidation is TTL-based, not event-based.

Docker is the standard delivery mechanism. Two compose files are maintained:
- `docker-compose.yml` — single-container production deployment.
- `docker-compose.dev.yml` — dev setup with hot reload; API on `:8000`, Web (Vite) on `:5173`.

The React frontend (`frontend/`) MUST source the API key from `VITE_API_KEY`, which the dev compose
maps automatically from `.env`. No API credentials belong in frontend source files.

## Development Workflow

Environment variables (`LEAGUE_ID`, `TEAM_ID`, `ESPN_S2`, `ESPN_SWID`, `API_KEY`) MUST be loaded
from a `.env` file via `python-dotenv`. The `.env` file MUST NOT be committed to version control.

Primary entry points:
- `python main.py` — interactive menu over all scripts.
- `python scripts/<script>.py [flags]` — direct CLI invocation.
- `docker compose -f docker-compose.dev.yml up` — full dev stack.

When adding a new workflow, a corresponding `scripts/run_<workflow>.py` entry point MUST be added
and registered in `main.py`'s menu.

## Governance

This constitution supersedes all other project practices when conflicts arise. Amendments require
updating this file, incrementing the version, and including the rationale in the commit message.

**Versioning policy**:
- MAJOR: removing a layer boundary, removing a canonical model type, or redefining a principle
  in a way incompatible with existing code.
- MINOR: adding a new principle, adding a new section, or materially expanding guidance.
- PATCH: clarifications, wording improvements, typo fixes, non-semantic refinements.

**Compliance**: All implementation plans (`plan.md`) MUST include a Constitution Check gate before
Phase 0 research. Pull requests that introduce layer boundary violations require explicit justification
in the Complexity Tracking table of the relevant `plan.md`.

**Version**: 1.0.1 | **Ratified**: 2026-06-01 | **Last Amended**: 2026-06-10
