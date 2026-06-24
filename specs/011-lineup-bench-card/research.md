# Research: Lineup & Bench Card

## Existing Components Available for Reuse

### Decision: Use `Card.tsx` as the wrapper (no changes)
- **Rationale**: `Card.tsx` already handles loading state (`loading` prop), error state (`error` prop), title, and the `bg-gray-900` container. Zero changes needed.
- **Usage**: `<Card title="My Lineup" loading={loading} error={error}>…</Card>`

### Decision: Reuse `injuryColor` / `injuryLabel` from `constants/injuryStatus.ts`
- **Rationale**: Injury badges are already defined and consistent across StreamerCard and RecentDrops. Import directly into `LineupCard.tsx`.

### Decision: Follow `StreamerCard.tsx` / `RecentDrops.tsx` fetch pattern exactly
- **Rationale**: `useEffect + useState([rows, loading, error])` + `api.X().then().catch().finally()` is the established fetch convention. No deviation needed.
- **Alternatives considered**: React Query, SWR — rejected per Principle V (no new abstractions without concrete justification).

### Decision: Reuse `_lineup_slot()` logic from `optimizer_service.py`
- **Rationale**: `_lineup_slot(player_record)` reads `player_record.espn_raw.lineupSlot` — exactly the data needed to know which fantasy slot a player occupies. The `_BENCH_SLOTS` constant is also already defined there.
- **How**: Extract the slot logic into the new service; `_BENCH_SLOTS` constant is repeated (3 lines) rather than shared — Principle V prefers three similar lines over premature abstraction.

### Decision: Reuse `get_roster_players()` from `collectors/espn.py`
- **Rationale**: Already fetches the full roster with `espn_raw` attached (which contains `lineupSlot`). No new ESPN calls needed.

### Decision: Reuse `get_player_lineup_status()` from `collectors/mlb_stats.py` via `services/lineup_service.py`
- **Rationale**: Feature 010 already exposes real-life "in lineup" status. New service calls it for each hitter in the roster. Pitchers are marked as "no check" (starting pitchers don't have a meaningful "in batting lineup" status).

### Decision: Add `myRoster()` to existing `api.ts` (not a new file)
- **Rationale**: All API calls live in the single `api` object in `api.ts`. Adding one method is the pattern.

### Decision: New API endpoint `GET /api/my-roster`
- **Rationale**: The existing `GET /api/lineup` route is per-player lookup by name (feature 010). A roster-level endpoint returning the full team's players + slots + status is a distinct resource.
- **Response shape**: `{ starters: RosterSlot[], bench: RosterSlot[], generated_on: string }`

### Decision: Fetch lineup status only for position players (hitters)
- **Rationale**: MLB lineup status (batting order) is meaningful only for hitters. SP/RP starting status is captured by the pitchers-starts feature. Fetching batting-lineup status for pitchers returns noise. Pitchers in the lineup card get a `in_lineup: null` or omit the indicator.
- **Alternatives considered**: Fetch for all players — rejected as confusing and wasteful.

### Decision: Parallelize per-player lineup status lookups
- **Rationale**: `optimizer_service.py` already uses sequential calls; the mlb_stats collector and pitchers stats service both use `ThreadPoolExecutor`. Match the same pattern for the roster card service.

## Complexity Assessment

No new abstractions, no new layers, no new dependencies. All technology choices are already present in the codebase.
