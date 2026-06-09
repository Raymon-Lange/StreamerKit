# Feature Specification: Waiver Drop ESPN Status Display

**Feature Branch**: `006-waiver-drop-espn-status`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "waiver drop should display ESPN Status like IR"

## Clarifications

### Session 2026-06-08

- Q: Where should status normalization live — in the service layer (normalized `espn_status` field in API) or in the frontend (raw `injury_status` field, frontend maps to labels using shared constants from `StreamerCard`)? → A: Option A — pass raw `injury_status` in the API; extract `injuryLabel`/`injuryColor` from `StreamerCard.tsx` to a shared module; `RecentDrops` imports and reuses them. CLI does its own thin mapping.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See injury status in waiver drop CLI output (Priority: P1)

When reviewing recent waiver drops from the command line, the user sees each dropped player's current ESPN status (IR, DTD, etc.) next to their name line, so they can immediately know whether a dropped player is injured before deciding to pick them up.

**Why this priority**: An IR player is not pickable in most leagues and the status is the single most actionable piece of context when evaluating a drop. Without it, the user might waste a claim on an injured player.

**Independent Test**: Run `python scripts/run_recent_drops_waiver_review.py` with a player in the results known to have a non-ACTIVE status. Verify the status label appears on their output line.

**Acceptance Scenarios**:

1. **Given** a dropped player whose ESPN status is `INJURY_RESERVE`, **When** the waiver drop review runs, **Then** the output line for that player shows `IR` next to their name/team info.
2. **Given** a dropped player whose ESPN status is `DAY_TO_DAY`, **When** the waiver drop review runs, **Then** the output shows `DTD` on their line.
3. **Given** a dropped player whose ESPN status is `ACTIVE` (or null), **When** the waiver drop review runs, **Then** no status label is shown — active status is the baseline and need not be called out.

---

### User Story 2 - Status included in API response (Priority: P2)

When the frontend or any API consumer calls `/api/recent-drops`, each row in the response includes an `injury_status` field (raw ESPN string) so the frontend can display or style it using the same shared constants as the streamers card.

**Why this priority**: The API is the data contract for the frontend; without the field in the response, the UI cannot show it regardless of how the frontend is updated.

**Independent Test**: Call `GET /api/recent-drops` and inspect the JSON rows. Each row has an `injury_status` key with a raw ESPN string value (e.g., `"INJURY_RESERVE"`, `"DAY_TO_DAY"`, or `null`).

**Acceptance Scenarios**:

1. **Given** the API is running, **When** `GET /api/recent-drops` is called, **Then** every row in `rows[]` contains an `injury_status` field.
2. **Given** a player with no ESPN injury status, **When** the API responds, **Then** `injury_status` is `null` rather than absent.

---

### User Story 3 - Status badge in frontend Recent Drops card (Priority: P3)

When the user views the dashboard's Recent Drops card, each dropped player shows a small status badge (e.g., "IR", "DTD") when their ESPN status is non-active, using the same color and label styling as the SP Streamers card.

**Why this priority**: The frontend is the primary consumer of the API for non-technical users. Reusing the existing badge style (from `StreamerCard`) ensures visual consistency across all cards.

**Independent Test**: Open the dashboard and locate a dropped player known to be on IR. Verify a badge showing `IR` appears next to their name, styled identically to how it appears on the SP Streamers card.

**Acceptance Scenarios**:

1. **Given** a dropped player with `injury_status: "INJURY_RESERVE"` in the API response, **When** the Recent Drops card renders, **Then** an `IR` badge appears with the same red background/text style as in the streamers card.
2. **Given** a dropped player with `injury_status: null`, **When** the Recent Drops card renders, **Then** no badge is shown — the row appears as normal.
3. **Given** an unrecognized status string (not in the label map), **When** the Recent Drops card renders, **Then** no badge is shown (guard against missing keys).

---

### Edge Cases

- What happens when ESPN returns an unrecognized status string? No badge is shown (key not in shared label map); raw value is still present in the API response for consumers who want it.
- What if `injury_status` is `None` on the `PlayerRecord`? Treat as active — no label shown in CLI or UI.
- Does the status reflect the player's current status at query time, or at the time of the drop? It reflects current status (sourced from the free-agent lookup, not the drop event).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The waiver drop service MUST include the raw `injury_status` field (ESPN string or `null`) in the serialized row output for both hitter and pitcher rows.
- **FR-002**: The CLI script MUST map raw ESPN status strings to short display labels using a local lookup dict (same label values as the shared frontend constants: `INJURY_RESERVE` → `IR`, `DAY_TO_DAY` → `DTD`, `SUSPENSION` → `SUSP`, `TEN_DAY_DL` → `IL10`, `FIFTEEN_DAY_DL` → `IL15`, `SIXTY_DAY_DL` → `IL60`, `OUT` → `OUT`). The label MUST appear on the player's header line when status is non-null and non-`ACTIVE`.
- **FR-003**: The `injuryLabel` and `injuryColor` dicts in `StreamerCard.tsx` MUST be extracted to a shared constants module so both `StreamerCard` and `RecentDrops` import from the same source.
- **FR-004**: The `RecentDrops` component MUST add `injury_status: string | null` to its `DropRow` interface and render a badge using the shared `injuryLabel`/`injuryColor` constants when the value is non-null and present in the label map.
- **FR-005**: Status display MUST be consistent for both hitter and pitcher drop rows.
- **FR-006**: No existing fields in the API response or CLI output may be removed or renamed — this change is purely additive.

### Key Entities

- **PlayerRecord**: Already carries `injury_status: str | None` (raw ESPN string). No model changes needed.
- **Drop row**: The serialized dict produced by `waivers_service.get_recent_drops_waiver_review()`. Gains `injury_status` (raw string or `null`), matching the field name already used by `pitchers_service.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every dropped player row in the CLI output includes the status label when the player is not active — zero rows with a non-active status omit the label.
- **SC-002**: Every row in the `/api/recent-drops` JSON response contains an `injury_status` key.
- **SC-003**: A user can determine a dropped player's injury status in under 3 seconds from either the CLI output or the dashboard, without needing to cross-reference another source.
- **SC-004**: The status badge in Recent Drops is visually identical to the badge in SP Streamers for the same status value.
- **SC-005**: No existing fields are removed or renamed in the CLI output or API response — the change is purely additive.

## Assumptions

- `injury_status` is already populated on `PlayerRecord` by the ESPN collector — no new ESPN API calls are required.
- The status reflects the player's current state at the time the waiver review runs, not historical state at drop time (the free-agent lookup provides current data).
- Status normalization is a display-only concern; no business logic (scoring, filtering) changes based on status.
- `injuryLabel` and `injuryColor` from `StreamerCard.tsx` cover all known ESPN status values; unrecognized values silently produce no badge (key-miss guard).
- Mobile/responsive layout of the frontend badge is not a separate concern; it inherits existing Tailwind responsive classes.
