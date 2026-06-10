# Feature Specification: Data Source Status Page

**Feature Branch**: `007-data-source-status-page`

**Created**: 2026-06-10

**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Data Source Health (Priority: P1)

As a user, I want to see a dedicated page that shows the health of every data source the app relies on, so I can immediately know whether my recommendations are based on fresh or stale data.

**Why this priority**: The feed health view is the core utility of this page — without it, the second card has no context. If rankings are stale, streamer recommendations may be wrong, and this is the fastest way to diagnose that.

**Independent Test**: Can be fully tested by navigating to the feed status page and verifying that each known data source appears with a status indicator, age, and TTL — delivering immediate data freshness awareness.

**Acceptance Scenarios**:

1. **Given** the app is open, **When** the user navigates to the Feed Status page, **Then** a card appears listing every data source with a visual status (fresh, stale, or missing), the time since last successful fetch, and the configured TTL.
2. **Given** a data source has a recent fetch failure on record, **When** the user views the feed status card, **Then** the error type and timestamp of the last failure are shown alongside the source.
3. **Given** a data source has never been fetched, **When** the user views the feed status card, **Then** that source is shown with a "missing" status and no age information.
4. **Given** the page is loaded, **When** the data cannot be retrieved from the server, **Then** a clear error state is shown rather than an empty or broken layout.
5. **Given** the feed status card is showing data, **When** the user clicks the Refresh button on that card, **Then** the card re-fetches and re-renders with updated data.

---

### User Story 2 - Inspect Short-Lived API Cache (Priority: P2)

As a user, I want to see what data is currently cached by the API layer (e.g. pitcher list rankings) and how fresh it is, so I can decide whether to trigger a fresh fetch or trust the cached response.

**Why this priority**: The API response cache has a much shorter TTL (minutes) than the collector cache (days). Knowing what's in this cache helps diagnose stale UI responses without digging into server logs.

**Independent Test**: Can be fully tested by viewing the API cache card and confirming each cached entry shows its key, age, and remaining TTL — independently delivering value as a cache inspector.

**Acceptance Scenarios**:

1. **Given** the Feed Status page is open, **When** the API cache card loads, **Then** it lists all currently active short-lived cache entries with their key name, age, and time remaining before expiry.
2. **Given** the API cache is empty (e.g. after a server restart), **When** the user views the cache card, **Then** an empty-state message is shown (not an error).
3. **Given** a cache entry has expired, **When** the user views the cache card, **Then** that entry is not shown (expired entries are excluded).
4. **Given** the API cache card is showing data, **When** the user clicks the Refresh button on that card, **Then** the card re-fetches and re-renders with current cache entries.

---

### Edge Cases

- What happens when the feed status API endpoint is unreachable or returns an error?
- How does the page handle a data source that exists in the cache but whose metadata (url, fetched_at) is partially missing?
- What if there are zero entries in the short-lived API cache?
- What if the same data source appears with multiple cache entries (e.g. keeper cost with league-year suffix)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST provide a navigable second page dedicated to feed and cache status, accessible from the existing app header or navigation.
- **FR-002**: The feed status card MUST display every known data source, showing its name, current status (fresh / stale / missing), age since last successful fetch, and configured TTL.
- **FR-003**: If a data source has a recorded fetch failure, the feed status card MUST display the failure's error type and timestamp.
- **FR-004**: The API cache card MUST list all non-expired short-lived cache entries, showing each entry's identifier, age, and remaining time before expiry.
- **FR-005**: If the API cache is empty, the cache card MUST display an empty-state message.
- **FR-006**: The page MUST expose a new API endpoint that returns the feed status and cache data needed to power both cards.
- **FR-007**: The API endpoint MUST reuse the same logic as `scripts/show_feed_health.py` — reading from the same cache store and retention configuration — rather than duplicating that logic.
- **FR-008**: The feed status page MUST be reachable without breaking the existing main dashboard page.
- **FR-009**: Each card MUST include an individual Refresh button that re-fetches data for that card independently, without reloading the other card or navigating away from the page.

### Key Entities

- **FeedSource**: Represents one tracked data source — name/key, status (fresh/stale/missing), age in seconds, TTL in seconds, last URL fetched, last fetched timestamp, last failure record (if any).
- **CacheEntry**: Represents one short-lived API cache entry — key name, age in seconds, remaining TTL in seconds.
- **FeedHealthSnapshot**: The full response payload returned by the new endpoint — list of FeedSources and list of CacheEntries, plus a snapshot timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can navigate from the main dashboard to the feed status page in one interaction (one click or one tap).
- **SC-002**: The feed status card loads and displays all tracked data sources within 2 seconds of page navigation under normal conditions.
- **SC-003**: 100% of tracked data sources defined in the retention configuration appear on the feed status card — none are silently omitted.
- **SC-004**: The feed status page does not disrupt the existing main dashboard; all existing cards continue to load and function correctly after the navigation feature is added.
- **SC-005**: The feed status and cache data shown in the UI is consistent with what `scripts/show_feed_health.py` reports when run at the same time.

## Assumptions

- The existing app already has a single-page layout; adding a "2nd page" means adding client-side navigation (a tab or nav link) rather than a separate URL route, though a route is acceptable.
- The short-lived cache to inspect in the second card is the API response cache (30-minute TTL), not the 15-day collector cache — the user described it as "cached for a short period of time."
- The new API endpoint will be authenticated the same way as all other `/api/*` endpoints (API key header).
- Each card has its own Refresh button; refreshing one card does not affect the other. No auto-polling is implemented — the page is otherwise read-only (no cache mutation).
- The page is for the same single user/operator who runs the tool; no multi-user or permission scoping is needed.

## Clarifications

### Session 2026-06-10

- Q: Does the feed status page auto-refresh on an interval, or does the user manually refresh? → A: Manual only — each card has its own Refresh button; no auto-polling.
