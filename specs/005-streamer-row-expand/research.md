# Research: Expandable Streamer Pitcher Row

**Branch**: `005-streamer-row-expand` | **Date**: 2026-06-04

## Decision 1 — No Backend Changes Needed

**Decision**: The `/api/streamers` endpoint already returns all the fields needed for the expanded view. No API changes are required.

**Fields currently returned but not used by the frontend**:
- `season_record` — season W-L string (e.g., `"5-3"`)
- `last_ten_record` — W-L over last 10 starts
- `last_two_starts` — detail on the two most recent starts
- `opponent_team` — today's opponent abbreviation (from PitcherList)
- `opponent_score` — PitcherList difficulty score for the matchup
- `recommendation.score` — numeric score (only `action` and `reason` are currently used)
- `positions` — ESPN position eligibility list

**Fields excluded from the expanded view** (per spec assumptions):
- `keeper_drafted_round`, `keeper_drafted_round_pick`, `keeper_projected_round`, `keeper_projected_pick` — keeper-focused, not relevant to streaming decisions

The only frontend change needed is to extend the `StreamerRow` TypeScript interface to include the new fields and render them in the expanded section.

---

## Decision 2 — Shared Component to Avoid Duplication

**Decision**: Extract a shared `StreamerCard` component used by both `Streamers.tsx` and `TomorrowStreamers.tsx`.

**Rationale**: The two components are currently line-for-line identical except for the card title label (`todayLabel()` vs `tomorrowLabel()`) and the API call (`api.streamers()` vs `api.streamers(true)`). The expand/collapse feature adds ~40 lines of logic (state, click handler, expanded section render). Duplicating that across both files would create an immediate, concrete maintenance burden — the exact condition that justifies a shared component.

The shared component takes a `tomorrow?: boolean` prop. Both existing files become one-line wrappers or can be replaced directly.

**Alternatives considered**:
- Apply the changes independently to both files: correct but creates duplicated expand logic that must be kept in sync.
- Utility hook only: sharing a hook still leaves duplicated JSX for the expanded section.

---

## Decision 3 — Expand/Collapse State: One Row at a Time

**Decision**: Track a single `expandedName: string | null` state — the name of the currently expanded pitcher. Clicking a collapsed row sets it; clicking the same row (already expanded) clears it; clicking a different row replaces it.

**Rationale**: Matches FR-004 (only one row expanded at a time). Simpler than a `Set<string>` of expanded names. Name is unique within a given card's data set.

**Alternatives considered**:
- `Set<string>` for multi-row expansion: not required by spec, adds complexity.
- Index-based tracking: fragile if rows reorder; name is more stable.

---

## Decision 4 — Chevron Indicator

**Decision**: Use a simple inline Unicode chevron (`›` rotated, or `▾`/`▸`) styled via Tailwind `transition-transform rotate-90` to indicate expanded state. No external icon library import needed.

**Rationale**: The codebase has no existing icon library (no `lucide-react`, `heroicons`, etc.). A Unicode character avoids a new dependency. Tailwind's `transition-transform` provides a smooth rotation on toggle.

---

## Files to Change

| File | Change |
|------|--------|
| `frontend/src/components/Streamers.tsx` | Thin wrapper → delegates to `StreamerCard` with `tomorrow={false}` |
| `frontend/src/components/TomorrowStreamers.tsx` | Thin wrapper → delegates to `StreamerCard` with `tomorrow={true}` |
| `frontend/src/components/StreamerCard.tsx` | New shared component — full expand/collapse logic |
