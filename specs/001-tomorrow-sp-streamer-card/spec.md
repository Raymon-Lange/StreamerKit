# Feature Specification: Tomorrow's SP Streamer Card

**Feature Branch**: `001-tomorrow-sp-streamer-card`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "add a new card for the page look at streaming pitchers for tomorrow game, it should use the API already created but the flag tomorrow."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Tomorrow's Streaming Pitcher Recommendations (Priority: P1)

As a fantasy baseball manager, I want to see a dedicated card on the dashboard showing
which pitchers to stream for tomorrow's games, so I can make waiver or roster decisions
the night before.

**Why this priority**: This is the entire feature — the card must exist and display actionable
streamer data for tomorrow before any other work makes sense.

**Independent Test**: Navigate to the dashboard. A "Tomorrow's SP Streamers" card is visible
alongside the existing "SP Streamers" card. The tomorrow card lists pitchers with starts
scheduled for tomorrow, each with tier, ownership, and recommendation reason.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** tomorrow has scheduled probable starters,
   **Then** the Tomorrow's SP Streamers card displays up to 8 pitchers ranked by tier with
   name, team, ownership %, tier label, and recommendation reason.

2. **Given** the dashboard is loaded, **When** no probable starters are found for tomorrow,
   **Then** the Tomorrow's SP Streamers card displays a "No streamers tomorrow." empty state
   rather than a blank or broken card.

3. **Given** the API is temporarily unavailable, **When** the tomorrow card fetches data,
   **Then** an inline error message is shown inside the card without disrupting any other card
   on the page.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The page MUST display a "Tomorrow's SP Streamers" card as a distinct card from
  the existing "SP Streamers" (today) card, implemented as an independent `TomorrowStreamers.tsx`
  component with no shared abstraction with the today `Streamers.tsx` component.
- **FR-002**: The card MUST call the existing streamers endpoint with the `tomorrow=true` flag.
- **FR-003**: The card MUST show the same data fields as the today card: pitcher name, MLB team,
  ownership %, streamer tier, rank, and recommendation reason.
- **FR-004**: The card MUST display a maximum of 8 pitchers, sorted by streamer tier
  (best tier first), matching the today card's display order.
- **FR-005**: The card MUST display an empty state message when no pitchers are returned.
- **FR-006**: The card MUST display an inline error message when the data fetch fails, without
  affecting other cards.
- **FR-007**: The card MUST show a loading state while data is being fetched.

### Key Entities

- **StreamerRow**: Pitcher entry with `name`, `mlb_team`, `tier`, `streamer_rank`,
  `percent_owned`, `recommendation.action`, `recommendation.reason` — same shape as today's
  streamer card (no new data model required).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Tomorrow's SP Streamers card appears on the dashboard alongside existing cards
  without layout regression on both single-column (mobile) and two-column (desktop) views.
- **SC-002**: The card loads and displays pitcher data within the same time as the existing
  Streamers card under normal network conditions.
- **SC-003**: When tomorrow has streamers, 100% of returned pitchers render with at minimum a
  name and tier label — no silent blank rows.
- **SC-004**: The empty state message is visible and readable when no streamers are available
  for tomorrow.

## Clarifications

### Session 2026-06-01

- Q: Should the today and tomorrow streamer cards share a single parameterized component, or be separate components? → A: New independent `TomorrowStreamers.tsx` — no shared abstraction with `Streamers.tsx`.

## Assumptions

- The existing `/api/streamers?tomorrow=true` endpoint and `api.streamers(true)` client method
  are already fully functional — no backend changes are required for this feature.
- The tier color mapping and display logic from the existing Streamers component apply identically
  to tomorrow's data (same tier labels returned by the API).
- The new card is added to the dashboard grid in `App.tsx` adjacent to the existing Streamers
  card; exact grid position (before or after) is implementation preference.
- No new API key, auth flow, or environment variable is required.
