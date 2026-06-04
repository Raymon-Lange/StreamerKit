# Feature Specification: IL Status Filter for Free Agent Suggestions

**Feature Branch**: `003-il-status-filter`

**Created**: 2026-06-04

**Status**: Draft

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Surface injury status for all waiver wire candidates (Priority: P1)

As a fantasy baseball manager reviewing free agent hitter suggestions, I want to see every
candidate's injury status clearly flagged in the output so I can make my own decision about
whether to use a waiver claim on an injured player. I do not want the tool to silently remove
players — I want the information and I'll make the call.

**Why this priority**: Hidden filtering removes options from the manager without explanation.
Transparent flagging preserves optionality while ensuring the manager is never surprised by
an injured player slipping through unlabeled.

**Independent Test**: Run the free agent hitter script. Verify that a player marked
`INJURY_RESERVE` still appears in output, accompanied by a visible `[IR]` label next to their
name in the CLI and a red badge in the web UI. Value delivered: complete, labeled candidate
list the manager can act on.

**Acceptance Scenarios**:

1. **Given** a player is marked `INJURY_RESERVE` in ESPN, **When** the free agent hitter
   suggestions are generated, **Then** that player appears in CLI results with an `[IR]` label
   and in the web UI with a red badge next to their name.
2. **Given** a player is marked `OUT` in ESPN, **When** suggestions are generated, **Then**
   that player appears with an `[OUT]` label (CLI) and red badge (web UI).
3. **Given** a player is marked `SUSPENSION` in ESPN, **When** suggestions are generated,
   **Then** that player appears with a `[SUSP]` label (CLI) and red badge (web UI).
4. **Given** a player is marked `DAY_TO_DAY` in ESPN, **When** suggestions are generated,
   **Then** that player appears with a `[DTD]` label (CLI) and orange badge (web UI).
5. **Given** a player is marked `QUESTIONABLE` in ESPN, **When** suggestions are generated,
   **Then** that player appears with a `[QUES]` label (CLI) and yellow badge (web UI).
6. **Given** a player is marked `ACTIVE` or has no injury status, **When** they appear in
   suggestions, **Then** no injury label or badge is displayed.

---

### User Story 2 - Same injury visibility for SP streamer suggestions (Priority: P2)

As a fantasy baseball manager reviewing streaming pitcher picks, I want to see injury status
labels on all pitchers in the output, so I can decide whether a DTD or IR pitcher is worth
a spot start pickup.

**Why this priority**: Consistent behavior across both suggestion scripts reduces confusion
and ensures I have the same level of information for both hitter and pitcher decisions.

**Independent Test**: Run the SP streamer script and verify that any pitcher with a non-ACTIVE
injury status has a visible label (CLI) and colored badge (web UI) next to their name.

**Acceptance Scenarios**:

1. **Given** a free agent pitcher is marked `INJURY_RESERVE`, **When** streaming pitcher
   suggestions are generated, **Then** that pitcher appears with an `[IR]` label (CLI) and
   red badge (web UI).
2. **Given** a free agent pitcher is marked `DAY_TO_DAY`, **When** they appear in streaming
   pitcher suggestions, **Then** a `[DTD]` label (CLI) and orange badge (web UI) are shown.

---

### User Story 3 - Roster optimization does not recommend injured players (Priority: P3)

As a fantasy baseball manager using the roster/lineup optimization feature, I do not want
the tool to recommend starting or acting on a player who is injured or on the IL, because
in that context the tool should protect me from a bad lineup decision.

**Why this priority**: Roster optimization is an automated recommendation the manager may
act on quickly without scrutinizing every player. Filtering out injured players there is the
right default to avoid lineup errors.

**Independent Test**: Run the team hitter evaluation script and confirm that no player with
status `INJURY_RESERVE`, `OUT`, or `SUSPENSION` appears as a recommendation.

**Acceptance Scenarios**:

1. **Given** a rostered player is marked `INJURY_RESERVE`, **When** the team hitter eval
   runs, **Then** that player is not surfaced as a start recommendation.
2. **Given** a rostered player is marked `OUT`, **When** the team hitter eval runs,
   **Then** that player is not surfaced as a start recommendation.

---

### Edge Cases

- What if ESPN returns `None` or an empty string for `injuryStatus`? → Treat as `ACTIVE`; no label shown, not filtered in any context.
- What if a player's injury status changes between the ESPN fetch and the time the output is read? → Not in scope; we use the status at fetch time.
- What if all candidates for a position are labeled injured on the waiver wire? → All still appear with labels/badges; the manager sees the full picture.
- What if an active player's `injured` boolean is `True` but `injuryStatus` is `ACTIVE`? → `injuryStatus` is authoritative; `injured` boolean alone does not trigger filtering or labeling.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST store the ESPN injury status for every player fetched from ESPN as part of the player record.
- **FR-002**: The waiver wire free agent hitter suggestion script MUST display a visible injury label next to any player whose status is not `ACTIVE` or `None`. No players are removed from waiver wire suggestions based on injury status.
- **FR-003**: The SP streamer suggestion script MUST display a visible injury label next to any pitcher whose status is not `ACTIVE` or `None`. No pitchers are removed from streaming suggestions based on injury status.
- **FR-004**: CLI injury status labels MUST be: `[IR]` for `INJURY_RESERVE`, `[OUT]` for `OUT`, `[SUSP]` for `SUSPENSION`, `[DTD]` for `DAY_TO_DAY`, `[QUES]` for `QUESTIONABLE`.
- **FR-005**: The system MUST treat a `None`, missing, or empty `injuryStatus` value as equivalent to `ACTIVE` (no label, no badge, not filtered in any context).
- **FR-006**: The injury status field MUST be passed through the service layer row dictionaries so it is available to all downstream scripts and the web API.
- **FR-007**: Injury status capture MUST occur in the collector layer only — collectors store the value, services and scripts consume it.
- **FR-008**: The roster optimization / team hitter eval MUST NOT surface players with status `INJURY_RESERVE`, `OUT`, or `SUSPENSION` as actionable start recommendations.
- **FR-009**: The web UI MUST display a colored badge/pill next to the player name for any non-`ACTIVE` injury status. Color coding: red for `INJURY_RESERVE`, `OUT`, `SUSPENSION`; orange for `DAY_TO_DAY`; yellow for `QUESTIONABLE`. The badge text matches the CLI short label (e.g., `IR`, `DTD`, `QUES`).

### Key Entities

- **PlayerRecord**: Extended with an `injury_status: str | None` field sourced from ESPN's `injuryStatus` attribute. Represents a player with their full metadata including health state.
- **InjuryStatus**: The string value ESPN assigns to a player's health state. Possible values: `ACTIVE`, `DAY_TO_DAY`, `QUESTIONABLE`, `OUT`, `INJURY_RESERVE`, `SUSPENSION`, or absent/`None`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every player with a non-`ACTIVE` injury status that appears in waiver wire or SP streamer output displays a visible injury label (CLI) or colored badge (web UI) — zero unlabeled injured players in output.
- **SC-002**: Zero players with status `INJURY_RESERVE`, `OUT`, or `SUSPENSION` appear as actionable start recommendations in the roster optimization output.
- **SC-003**: Players with no injury status or `ACTIVE` status produce identical output to the current behavior (no regression for healthy players).
- **SC-004**: The total wall-clock runtime of scripts does not increase by more than 2 seconds (the injury status is derived from already-fetched ESPN data; no extra network calls are made).

---

## Assumptions

- ESPN's `injuryStatus` field is always present on the `Player` object returned by the `espn-api` library; if absent, a safe default of `None` (treat as active) is used.
- The `espn-api` `Player` object already parses `injuryStatus` from the ESPN payload — no additional API call or scrape is needed.
- The SP streamer script's probable starters list comes from MLB Stats API, but the injury status enrichment comes from the ESPN player record (which is already fetched for ownership/roster data). The two sources are joined by player name.
- Waiver wire context (free agent hitter and SP streamer scripts) and roster optimization context (team hitter eval) require different behavior: label/badge-only vs. filter-out respectively.
- The set of filtered statuses for roster optimization (`INJURY_RESERVE`, `OUT`, `SUSPENSION`) is fixed for this feature; adding or removing statuses from this set is a future configuration concern.
- The web UI badge is rendered in the React frontend components (`Streamers.tsx` and equivalent hitter component) using Tailwind CSS color classes consistent with the existing tier color pattern.

---

## Clarifications

### Session 2026-06-04

- Q: Should waiver wire suggestions filter out or just flag players with severe injury statuses (INJURY_RESERVE, OUT, SUSPENSION)? → A: Flag only — never filter from waiver wire. The manager decides. Filtering applies only to roster optimization recommendations.
- Q: How should injury status be shown in the web UI player cards? → A: Colored badge/pill next to player name — red for IR/OUT/SUSP, orange for DTD, yellow for QUES.
- Q: How should injury status appear in the CLI output? → A: Inline bracketed label after player name, e.g. `Shohei Ohtani [DTD] | LAA | ...` — confirms FR-004 as specified.
