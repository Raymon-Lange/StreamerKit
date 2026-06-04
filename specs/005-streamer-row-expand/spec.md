# Feature Specification: Expandable Streamer Pitcher Row

**Feature Branch**: `005-streamer-row-expand`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "let create a feature in on the streaming pitcher card where you click on the row and it expands the row with additional information not displayed"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Expand a Pitcher Row to See Detailed Stats (Priority: P1)

A user views the SP Streamers card and wants more context about a pitcher before making a streaming decision. They click on a pitcher row and it expands inline to reveal additional stats not visible in the compact view — including season record, recent start performance, and matchup difficulty.

**Why this priority**: This is the core feature. Without it the card has no interactive behavior and users must look up stats elsewhere.

**Independent Test**: Click any pitcher row in the SP Streamers card — the row expands below the summary line to show additional fields. Clicking again collapses it.

**Acceptance Scenarios**:

1. **Given** the SP Streamers card is loaded with pitcher rows, **When** the user clicks a pitcher row, **Then** the row expands to reveal additional stats beneath the compact summary.
2. **Given** a pitcher row is expanded, **When** the user clicks that same row again, **Then** the row collapses back to its compact state.
3. **Given** one pitcher row is expanded, **When** the user clicks a different pitcher row, **Then** the newly clicked row expands and the previously expanded row collapses (only one expanded at a time).
4. **Given** a pitcher row is expanded, **When** the page is viewed on a narrow mobile screen, **Then** the expanded content remains fully readable without horizontal overflow.

---

### User Story 2 - Expanded View Shows All Relevant Available Data (Priority: P2)

A user expands a pitcher row and sees a complete picture of the pitcher's recent performance and matchup context, drawn from data already returned by the API but not shown in the compact row.

**Why this priority**: The expanded view is only valuable if it surfaces meaningful data. The compact row already shows name, team, ownership, tier, and recommendation reason — the expanded view should add everything else.

**Independent Test**: Expand any pitcher row and confirm these fields are visible: season W-L record, last 10 starts record, last 2 starts detail, opponent team, and opponent difficulty score.

**Acceptance Scenarios**:

1. **Given** a pitcher row is expanded, **When** the expanded section renders, **Then** the season W-L record is displayed.
2. **Given** a pitcher row is expanded, **When** the expanded section renders, **Then** the last 10 starts record is displayed.
3. **Given** a pitcher row is expanded, **When** the expanded section renders, **Then** the last 2 starts detail is displayed.
4. **Given** a pitcher row is expanded, **When** the expanded section renders, **Then** the opponent team and opponent difficulty score are displayed.
5. **Given** a field has no data (e.g., opponent score is null), **When** the expanded section renders, **Then** the field is either hidden or shown with a clear "—" placeholder rather than showing a raw null or error.

---

### Edge Cases

- What if a pitcher has no recent start data? The expanded section should still open and display available fields, showing "—" for any missing values.
- What if the API returns no opponent info (pitcher not starting today)? The opponent fields should be omitted or show "—".
- What happens on a very long pitcher name or team name in the expanded view? Content should wrap gracefully without overflow.
- What if the user rapidly clicks multiple rows? The UI should handle quick toggling without visual glitches.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each pitcher row in the SP Streamers card MUST be clickable.
- **FR-002**: Clicking a collapsed row MUST expand it to show additional pitcher details inline below the compact summary.
- **FR-003**: Clicking an already-expanded row MUST collapse it back to its compact state.
- **FR-004**: Only one row MAY be expanded at a time — expanding a new row MUST collapse the previously expanded row.
- **FR-005**: The expanded section MUST display: season W-L record, last 10 starts record, last 2 starts detail, opponent team, and opponent difficulty score.
- **FR-006**: Any field with a null or missing value MUST render as "—" rather than blank, undefined, or an error.
- **FR-007**: The expand/collapse interaction MUST work on both desktop and mobile viewports without layout breakage.
- **FR-008**: The compact row summary (name, team, ownership, tier, rank, recommendation reason) MUST remain visible when the row is expanded — the expanded content is additive, not a replacement.
- **FR-009**: A visual affordance (e.g., a chevron or arrow icon) MUST indicate that rows are expandable and show the current expanded/collapsed state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clicking a pitcher row expands it within 100ms of the click event with no visible loading delay (data is already in the page).
- **SC-002**: 100% of pitcher rows in the card are clickable and expand/collapse correctly.
- **SC-003**: The expanded view displays all 5 data fields (season record, last-10 record, last-2 starts, opponent team, opponent score) when the API provides them.
- **SC-004**: Null or missing fields render as "—" in 100% of cases — no raw nulls, "undefined", or blank cells visible to the user.
- **SC-005**: The expand/collapse behavior works correctly on viewports from 375px to 1280px wide with no horizontal overflow.

## Assumptions

- The additional data fields (season record, last-10 record, last-2 starts, opponent team, opponent score) are already returned by the existing streamers API and available on the frontend — no backend changes are required.
- Only one row is expanded at a time; there is no requirement to support multiple simultaneous expanded rows.
- The feature applies to both the Today and Tomorrow SP Streamers cards, since they share the same row structure and API data shape.
- Keeper cost fields (`keeper_drafted_round`, `keeper_projected_round`, etc.) are excluded from the expanded view as they are less relevant to streaming decisions and would add clutter.
- The expand/collapse transition may be instant or use a subtle animation — no specific animation duration is required.
- No persistence of expanded state is required — collapsing on page reload is acceptable.
