# Feature Specification: Player Lineup Status Check

**Feature Branch**: `010-lineup-status-check`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Check Player Starting Lineup via ESPN Public API"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check Player Lineup Before Setting Fantasy Lineup (Priority: P1)

A fantasy baseball manager wants to know whether a specific player is in today's starting lineup before locking in their fantasy team. The manager needs to quickly verify starting status, batting order position, and the matchup context (opponent) to decide whether to start the player.

**Why this priority**: This is the primary use case — acting on real-time lineup data is time-sensitive and directly impacts fantasy decisions before daily lock times.

**Independent Test**: Can be fully tested by querying a player known to be in the starting lineup on a game day and verifying the response includes starting status, batting slot, team, and opponent.

**Acceptance Scenarios**:

1. **Given** a player is in today's starting lineup, **When** a user queries by player name, **Then** the system returns in-lineup status, batting order slot, team name, opponent, and game time.
2. **Given** a player is listed but not in the starting lineup (bench), **When** a user queries by player name, **Then** the system returns not-in-lineup status with team and game context still included.
3. **Given** a partial or alternate-casing player name, **When** a user queries, **Then** the system matches via normalized name lookup and returns the correct result.

---

### User Story 2 - Check Lineup for a Specific Past or Future Date (Priority: P2)

A manager preparing for a specific matchup period wants to check lineup data for a date other than today — for instance, confirming historical lineup data or previewing a known scheduled game.

**Why this priority**: Useful for verification and planning but the primary value is real-time today's status. Date flexibility makes the tool more versatile without significant added complexity.

**Independent Test**: Can be tested by querying a known game date and verifying results match publicly available box score data.

**Acceptance Scenarios**:

1. **Given** a valid date with a game for the player's team, **When** a user queries with player name and date, **Then** the system returns lineup status for that specific date.
2. **Given** no date is specified, **When** a user queries, **Then** the system defaults to today's date.

---

### User Story 3 - Handle No Game Scheduled (Priority: P3)

A manager queries a player on an off day when no game is scheduled for that team.

**Why this priority**: Edge case coverage ensures the tool does not mislead users into thinking a player is benched when they simply have no game.

**Independent Test**: Can be tested by querying on a known off day and verifying the response clearly indicates no game is scheduled.

**Acceptance Scenarios**:

1. **Given** a player's team has no game on the queried date, **When** a user queries by player name, **Then** the system returns a clear "no game scheduled" status rather than "not in lineup."
2. **Given** a player name that cannot be matched to any team or game, **When** a user queries, **Then** the system returns a clear not-found response.

---

### Edge Cases

- **Name ambiguity**: When a player name matches multiple players, the system returns the first/best normalized-name match — consistent with the existing `get_player_id()` pattern used throughout the collectors. No disambiguation error is surfaced to the caller.
- **Doubleheaders**: When a team plays two games in a day, the system returns lineup status for the first game only — this aligns with fantasy roster lock timing, which occurs before game 1.
- How does the system handle a player who is injured and not rostered for the day?
- What happens if game data is not yet available (e.g., queried early morning before lineups are posted)?
- **External data source unavailable**: The system returns `200` with `status: "no_game"` — graceful degradation, consistent with how other collectors in this project handle network or API failures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a player name and return that player's lineup status for a given game day.
- **FR-002**: System MUST indicate whether the player is in the starting lineup (true/false).
- **FR-003**: System MUST return the player's batting order slot when the player is in the starting lineup.
- **FR-004**: System MUST return the player's team name and opponent team name when a game is found.
- **FR-005**: System MUST return the scheduled game time when available.
- **FR-006**: System MUST distinguish between "not in starting lineup" and "no game scheduled today" as separate statuses.
- **FR-007**: System MUST default to today's date when no date is specified by the caller.
- **FR-008**: System MUST accept an optional date parameter to query lineup status for a date other than today.
- **FR-009**: System MUST normalize player names before matching to handle common name variations (capitalization, diacritics, abbreviations).
- **FR-010**: System MUST expose lineup status lookup via a command-line interface accepting a player name argument.
- **FR-011**: System MUST expose lineup status lookup via an authenticated REST API endpoint accepting a player name query parameter.
- **FR-012**: The REST API endpoint MUST require authentication consistent with other protected API routes in this project.

### Key Entities

- **LineupStatus**: Represents a player's game-day lineup state — includes: player name, in-lineup flag, batting order slot (nullable), team, opponent, game time (nullable), and a status reason (e.g., "starting", "bench", "no game", "not found").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can determine a player's lineup status within 5 seconds of submitting a query.
- **SC-002**: The system returns accurate lineup information (within the resolution of publicly available data) for players with active game schedules.
- **SC-003**: All three edge-case states — "starting," "bench," and "no game" — are distinguishable in every interface (CLI and API) without ambiguity.
- **SC-004**: Queries using common name variations (e.g., "J. Duran" vs. "Jarren Duran") succeed at least 90% of the time for standard MLB roster names.
- **SC-005**: The CLI produces human-readable output sufficient to make a start/sit decision without additional context.

## Clarifications

### Session 2026-06-24

- Q: How should the system handle a player name that matches multiple players? → A: Return first/best normalized-name match, following the existing collector pattern (same as `get_player_id()`).
- Q: How should doubleheaders be handled? → A: Return the first game of the day — fantasy roster lock occurs before the first game.
- Q: What should the system return when the external data source (ESPN API) is unavailable? → A: Return `200` with `status: "no_game"` — graceful degradation consistent with other collectors in this project.

## Assumptions

- Lineup data is sourced from a publicly accessible data feed that reflects real-time or near-real-time MLB lineup decisions.
- Name normalization uses the existing `normalize_name()` utility already present in this project.
- The REST API authentication mechanism (API key via `X-API-Key` header) is the same as all other protected routes.
- The CLI is a thin wrapper and does not introduce any recommendation or scoring logic.
- Mobile or browser-based UI display of lineup status is out of scope for this feature; the API response supports future UI integration.
- Lineup data for a given date may not be available until shortly before game time; early-morning queries may return a "lineup not yet posted" state not explicitly modeled in FR-006 — this is a known limitation.
