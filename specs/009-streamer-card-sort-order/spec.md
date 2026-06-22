# Feature Specification: Streamer Card Sort Order

**Feature Branch**: `009-streamer-card-sort-order`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "on the streamer cards, i like evualte the order in which the player are show, right now it seems random, maybe should follow the Pitcher list ranking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Players Listed by PitcherList Rank (Priority: P1)

When I open the SP Streamers card (today's or tomorrow's), I want the pitchers listed from best to worst according to their PitcherList ranking, so I can immediately see who the top streaming options are without having to scan for rank numbers.

**Why this priority**: The primary reason to open the streamer card is to evaluate who to pick up. Without a meaningful sort order, the user must mentally re-sort the list by reading the rank badge on each row — extra work that defeats the purpose of ranking.

**Independent Test**: Load the SP Streamers card and verify that the rows appear in ascending PitcherList rank order (rank #1 at the top, higher numbers below), with unranked players at the bottom.

**Acceptance Scenarios**:

1. **Given** the streamer card is loaded with ranked players, **When** I view the list, **Then** the player with the lowest PitcherList rank number appears first and subsequent rows follow ascending rank order.
2. **Given** some players are not on the PitcherList, **When** I view the list, **Then** unranked players ("NR") appear at the bottom, after all ranked players.
3. **Given** multiple players share no rank (all NR), **When** I view the list, **Then** the relative order among unranked players is consistent and does not change between page loads.

---

### User Story 2 - Tomorrow's Card Also Sorted (Priority: P2)

The same rank-based ordering should apply when viewing tomorrow's streamers.

**Why this priority**: The tomorrow card is a companion view to today's. Inconsistent ordering between the two cards would be confusing.

**Independent Test**: Toggle to tomorrow's streamers and verify the same ascending PitcherList rank ordering applies.

**Acceptance Scenarios**:

1. **Given** the tomorrow's streamers card is loaded, **When** I view the list, **Then** players appear in ascending PitcherList rank order with unranked players at the bottom.

---

### Edge Cases

- What happens when all starters today are unranked (no one appears on PitcherList)? — The list is still shown; order among unranked players may be arbitrary.
- What happens when only one pitcher has a rank and the rest are unranked? — Ranked pitcher appears first, others follow.
- What happens when the PitcherList data fails to load? — Existing fallback behavior applies (cache or graceful error); this feature does not affect error handling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The streamer card rows MUST be ordered by PitcherList rank, ascending (rank #1 first).
- **FR-002**: Unranked players (no PitcherList rank) MUST appear after all ranked players.
- **FR-003**: The sort order MUST apply to both today's and tomorrow's streamer cards.
- **FR-004**: The sort order MUST be stable — players with the same rank value (or both unranked) MUST not swap positions between page loads.
- **FR-005**: No other displayed information (tier labels, rank badges, recommendation text) MUST change as a result of this sort.

### Key Entities

- **StreamerRow**: A single pitcher displayed in the card. Has a `streamer_rank` field (integer or null) sourced from PitcherList. This field is the sort key.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the change, the first row in the streamer card always has the lowest `streamer_rank` value among all displayed rows.
- **SC-002**: Unranked rows (null rank) never appear above a ranked row.
- **SC-003**: The sort order is identical whether the data is freshly fetched or served from the response cache.
- **SC-004**: No regression in any other displayed field or card behavior is introduced.

## Assumptions

- `streamer_rank` is the correct field to sort by — it directly reflects the PitcherList ordering and is already displayed as the rank badge on each row.
- Ties in `streamer_rank` (same integer) are unlikely in practice; stable sort order by name or fetch order is acceptable as a tiebreaker.
- The sort should be applied at the data layer (where the rows are assembled) rather than the display layer, so the ordering is consistent for any future consumer of the same data.
- The card currently shows up to 8 rows via a frontend slice; sort order must be correct before that slice is applied so the top-8 are the best-ranked 8.
