# Feature Specification: Lineup & Bench Card

**Feature Branch**: `011-lineup-bench-card`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "i like to create a new card/component that shows my starting line and bench, show the postion they are starting and if they are in the startline up."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Starting Lineup with Positions (Priority: P1)

As a fantasy team manager, I want to see all my starters in a card that shows who is starting, what position they are filling, and whether they are confirmed in their real-life lineup — so I can make last-minute decisions without leaving the tool.

**Why this priority**: The core value of the card is knowing who is starting and at what slot. Without this, the feature doesn't exist.

**Independent Test**: Open the dashboard and the card renders a list of starting players with their fantasy positions and a clear in-lineup or not-in-lineup indicator for each.

**Acceptance Scenarios**:

1. **Given** the user has an active fantasy team, **When** the lineup card loads, **Then** each starting player appears with their fantasy roster slot (e.g., C, 1B, SP1, UTIL) and a status badge indicating whether they are confirmed in their real-life starting lineup.
2. **Given** a player's real-life status has been confirmed (e.g., hitting in the batting order), **When** the card renders, **Then** that player shows a clear "In Lineup" indicator (e.g., green badge or checkmark).
3. **Given** a player is listed as questionable or not yet confirmed, **When** the card renders, **Then** that player shows a "Not Confirmed" or "Out" indicator distinct from the active status.

---

### User Story 2 - View Bench Players (Priority: P2)

As a fantasy team manager, I want to see my bench players in the same card so I can compare them against my starters and identify if a bench player should be swapped in.

**Why this priority**: Bench visibility alongside starters lets the user make swap decisions in one glance — it adds context that makes the starter view actionable.

**Independent Test**: The card has a distinct bench section below starters; bench players are listed with their position eligibility and lineup status.

**Acceptance Scenarios**:

1. **Given** the user has bench players on their roster, **When** the card loads, **Then** the bench section shows all bench players with their primary position and real-life lineup status.
2. **Given** a bench player is confirmed in their real-life lineup, **When** the card renders, **Then** that player shows the same "In Lineup" indicator used in the starter section, making the comparison immediate.
3. **Given** the user views the card, **When** they scan from starters to bench, **Then** the two sections are visually separated (e.g., a divider or heading) so the boundary is unambiguous.

---

### User Story 3 - Refresh Lineup Statuses on Demand (Priority: P3)

As a fantasy team manager, I want to be able to refresh the lineup status data so I can see the latest confirmations without reloading the entire page.

**Why this priority**: Lineup statuses change throughout the day; a stale view could cause the user to sit a starter who later gets confirmed. However, the card delivers value even without refresh — it is a lower priority enhancement.

**Independent Test**: A refresh button (or equivalent trigger) on the card fetches updated lineup status data and re-renders player badges without a full page reload.

**Acceptance Scenarios**:

1. **Given** the card is displayed, **When** the user triggers a refresh, **Then** the lineup status indicators update to reflect the latest data within a few seconds.
2. **Given** the data refresh fails (e.g., network error), **When** the user triggers a refresh, **Then** the card shows an error notice and retains the previously loaded data rather than going blank.

---

### Edge Cases

- What happens when the lineup data has not loaded yet? The card should show a loading state rather than an empty or broken layout.
- What happens when no players are in the starting lineup (e.g., all DNP)? The starters section should still render with "Not Confirmed" indicators rather than disappearing.
- What happens when the bench is empty? The bench section is hidden or shows an empty-state message.
- How does the card handle players whose position eligibility covers multiple slots (e.g., OF/UTIL)? The card shows the slot they are currently occupying on the fantasy roster, not all eligibilities.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The card MUST display all players currently slotted into starting roster positions, grouped separately from bench players.
- **FR-002**: Each player entry MUST show the fantasy roster slot they occupy (e.g., C, 1B, 2B, SS, 3B, OF, UTIL, SP, RP, P, BN).
- **FR-003**: Each player entry MUST show a real-life lineup status indicator that distinguishes at minimum: confirmed in lineup, not confirmed / questionable, and out / not starting.
- **FR-004**: The bench section MUST display all players in bench (BN) slots with the same position and status information shown for starters.
- **FR-005**: The card MUST show a loading state while data is being fetched.
- **FR-006**: The card MUST show a meaningful error state if data fails to load, without breaking the rest of the page.
- **FR-007**: The card layout MUST visually separate the starter section from the bench section using a clear divider or labeled heading.
- **FR-008**: The lineup status data displayed MUST come from the same data source used by the existing lineup status check feature (feature 010).

### Key Entities

- **Lineup Slot**: A position slot on the fantasy roster (e.g., C, 1B, SP1, BN1) with an assigned player and the player's real-life confirmation status.
- **Player Entry**: A display unit showing player name, the slot they fill, and their real-life lineup status badge.
- **Roster Section**: A grouping of lineup slots — either "Starters" (all non-bench slots) or "Bench" (BN slots).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All starting and bench players are visible in a single card without scrolling on a standard desktop viewport.
- **SC-002**: The lineup status for each player is readable at a glance — a user can determine every starter's status in under 10 seconds.
- **SC-003**: The card loads and displays data within 3 seconds of the page rendering under normal network conditions.
- **SC-004**: The card degrades gracefully — if data is unavailable, users still see a clear message rather than a broken component.
- **SC-005**: 100% of rostered players (starters and bench) appear in the card with no omissions when data is available.

## Assumptions

- The card is added to the existing React frontend dashboard alongside current cards (streamer, free agent, etc.).
- Lineup status data (real-life in-lineup confirmation) is already available via the API added in feature 010; this feature only displays it, not fetches new data.
- The fantasy team roster slots and player assignments are fetched from the existing ESPN collector, not a new data source.
- The card does not need to support inline swap actions (e.g., dragging a bench player to a starter slot) — display only.
- Mobile layout is out of scope for the initial version; the card targets the existing desktop layout.
- The user's team ID is already in context from the existing application session, so no additional authentication is needed for this card.
