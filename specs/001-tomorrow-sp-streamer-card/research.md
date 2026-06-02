# Research: Tomorrow's SP Streamer Card

**Feature**: 001-tomorrow-sp-streamer-card
**Date**: 2026-06-01

## Findings

### Decision: Independent component vs. shared parameterized component

**Decision**: New independent `TomorrowStreamers.tsx`

**Rationale**: Constitution Principle V (Simplicity First) explicitly favors direct repetition
over premature abstraction. The two cards differ by exactly one API flag (`tomorrow=true`),
one title string, and one empty-state message. A shared component parameterized for this
single difference would add indirection with no concrete benefit at this point in the project.
User confirmed this choice during clarification (Session 2026-06-01).

**Alternatives considered**:
- Refactor `Streamers.tsx` to accept `tomorrow?: boolean` prop — rejected (speculative
  abstraction; constitution says three similar lines beat a premature helper)

### Decision: API endpoint

**Decision**: Use existing `GET /api/streamers?tomorrow=true`

**Rationale**: The endpoint is already implemented in `app/routes/streamers.py` with correct
`tomorrow` flag handling, `response_cache` TTL (5 min), and `for_date` derivation. The
frontend API client (`frontend/src/api.ts`) already exposes `api.streamers(tomorrow = false)`.
No backend work is required.

**Alternatives considered**: None — reuse was the only sensible option.

### Decision: Tier color mapping

**Decision**: Copy the `tierColor` map from `Streamers.tsx` directly into `TomorrowStreamers.tsx`

**Rationale**: Consistent with the independent-component decision. The tier label strings
(`Must Stream`, `Strong Stream`, `Streamer`, `Deep League`, `Not Ranked`) are stable API
vocabulary defined by the Pitcher List integration. Duplicating the small map avoids shared
state while preserving visual consistency.

### Decision: Row limit

**Decision**: Cap display at 8 rows (`.slice(0, 8)`)

**Rationale**: Matches today's `Streamers.tsx` behavior. Keeps both cards visually balanced
in the two-column dashboard grid.

### Decision: Grid placement

**Decision**: Place `<TomorrowStreamers />` immediately after `<Streamers />` in `App.tsx`

**Rationale**: Groups today/tomorrow cards together for logical proximity. The two-column
Tailwind grid handles layout automatically — no custom positioning needed.
