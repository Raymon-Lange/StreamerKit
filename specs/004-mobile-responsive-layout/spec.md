# Feature Specification: Mobile Responsive Card Layout

**Feature Branch**: `004-mobile-responsive-layout`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "i like to support a moblie or smaller res, where the main cards with from being two per row to one per row."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single-Column Layout on Small Screens (Priority: P1)

A user opens the StreamerKit web dashboard on a mobile phone or a narrow browser window. Instead of seeing two cards squeezed side by side, all cards flow into a single column, each taking the full available width.

**Why this priority**: This is the core request. Without it, the dashboard is difficult to read and interact with on any device narrower than the current two-column breakpoint.

**Independent Test**: Resize the browser window below the responsive breakpoint (or use a mobile device/emulator) — every card on the page should render in a single column, top to bottom, with no horizontal overflow.

**Acceptance Scenarios**:

1. **Given** the dashboard is viewed on a screen narrower than the breakpoint, **When** the page loads, **Then** all cards stack vertically in a single column filling the available width.
2. **Given** the dashboard is viewed on a screen at or wider than the breakpoint, **When** the page loads, **Then** cards appear in the two-column layout as before, with full-width cards (Daily Brief, Profile) spanning both columns.
3. **Given** the user resizes the browser window from wide to narrow, **When** the window crosses the breakpoint, **Then** the layout transitions from two columns to one without a page refresh or broken overflow.

---

### User Story 2 - No Horizontal Overflow on Small Screens (Priority: P2)

A user on a small screen scrolls through the dashboard and does not encounter any card or inner element that forces a horizontal scrollbar or extends beyond the viewport edge.

**Why this priority**: Horizontal overflow is the most common visual symptom of a broken responsive layout. It breaks usability even when the grid itself stacks correctly.

**Independent Test**: On a device or emulator at 375px wide (common phone width), confirm no horizontal scroll exists on the page.

**Acceptance Scenarios**:

1. **Given** the dashboard is viewed at 375px width, **When** inspecting the page, **Then** no element extends beyond the viewport width and no horizontal scroll is present.
2. **Given** the Daily Brief card (which has an internal stat grid) is visible on a small screen, **When** the page renders, **Then** its internal content adapts to the narrower width without overflow.

---

### Edge Cases

- What happens at exactly the breakpoint width? Layout should be deterministic — it is either one-column or two-column, with no ambiguous overlap.
- What if a card's content is very long? Content should wrap within the card; the card should not force the column wider than the viewport.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The dashboard MUST render all main cards in a single column when the viewport width is below the responsive breakpoint.
- **FR-002**: The dashboard MUST render main cards in a two-column layout when the viewport width is at or above the responsive breakpoint, consistent with the current desktop behavior.
- **FR-003**: Full-width cards (Daily Brief, Profile) MUST span the full available width on both small and large screens — they MUST NOT create implicit extra columns on small screens.
- **FR-004**: No dashboard card or inner component MUST cause horizontal overflow or a horizontal scrollbar at any supported viewport width.
- **FR-005**: The layout transition between one-column and two-column MUST occur without a page refresh.
- **FR-006**: The responsive breakpoint MUST be a single, clearly defined threshold applied consistently across all cards in the layout.

### Key Entities

- **Card**: A self-contained UI panel representing a data section (e.g., Streamers, Optimizer, Weekly Scores). Stacks vertically on small screens; two-per-row on large screens.
- **Full-width Card**: A card designated to span the entire row regardless of column count (Daily Brief, Profile). Must behave correctly in both one-column and two-column layouts.
- **Responsive Breakpoint**: The viewport width threshold at which the layout switches between one-column and two-column modes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At 375px viewport width, all cards render in a single column with no horizontal scrollbar present.
- **SC-002**: At 1280px viewport width, the two-column layout is preserved — Daily Brief and Profile span full width, remaining cards appear two per row.
- **SC-003**: At the defined breakpoint width (±1px), the layout is unambiguously one-column or two-column with no rendering artifacts.
- **SC-004**: No card content overflows its container at any viewport width between 320px and 1920px.

## Assumptions

- The responsive breakpoint will be chosen from the project's existing utility class system (e.g., a standard named breakpoint), not a custom arbitrary pixel value.
- Only the main card grid layout is in scope — navigation, header, and card-internal content are secondary concerns, adjusted only where they directly cause overflow.
- The two streamer cards (Today and Tomorrow) are both present in the layout; their removal or consolidation is a separate feature decision not included here.
- No changes are required to backend APIs or data models — this is a purely presentational change to the frontend.
- Desktop behavior (two-column layout, full-width spanning cards) is preserved exactly as-is; only small-screen behavior is being added or corrected.
