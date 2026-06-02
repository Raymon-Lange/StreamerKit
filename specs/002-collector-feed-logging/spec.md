# Feature Specification: Collector Feed Logging

**Feature Branch**: `002-collector-feed-logging`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "let add a commonad logging source the feeds that pulling information from the websites, like ranking. We should capture long around perfance, runtime and success or errors."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Feed Fetch Performance (Priority: P1)

As a developer running scripts that pull data from external sources (ESPN, PitcherList, MLB Stats), I want each data fetch to be automatically logged with its runtime and outcome so I can see at a glance which feeds are slow or failing.

**Why this priority**: Without this, there is no visibility into whether a data fetch succeeded, how long it took, or what went wrong. This is the core value of the feature.

**Independent Test**: Run any script (e.g., `python scripts/run_sp_streamers.py`) and observe that a log entry is written for each external data pull, showing collector name, duration, and success/failure status.

**Acceptance Scenarios**:

1. **Given** the SP streamers script is run, **When** the PitcherList ranking collector fetches data, **Then** a log entry is written recording the collector name, fetch duration in seconds, and a "success" status.
2. **Given** the SP streamers script is run, **When** a ranking fetch fails due to a network error, **Then** a log entry is written recording the collector name, duration up to failure, "error" status, and the error message.
3. **Given** a script completes, **When** the user inspects the log, **Then** each external data feed fetch has exactly one log entry, in chronological order.

---

### User Story 2 - Diagnose a Slow or Failed Feed (Priority: P2)

As a developer troubleshooting why a recommendation run returned stale or incomplete data, I want the log to include enough detail to identify which specific feed failed and why.

**Why this priority**: A success/failure flag alone is not enough to diagnose problems. Error details and timing make failures actionable.

**Independent Test**: Simulate a network timeout or HTTP error on one collector and confirm the log entry contains the error type and message alongside timing.

**Acceptance Scenarios**:

1. **Given** a collector raises an exception during fetch, **When** the log entry is written, **Then** it includes the exception type and a human-readable message.
2. **Given** a collector falls back to a cached response due to a fetch failure (per constitution Principle III), **When** the log entry is written, **Then** it records that a cache fallback occurred rather than a fresh fetch.
3. **Given** a collector fetch exceeds 10 seconds, **When** the log entry is written, **Then** the duration is recorded accurately and the entry is distinguishable from normal-duration fetches.

---

### User Story 3 - Review a Session's Feed Activity (Priority: P3)

As a developer who runs multiple scripts in sequence, I want all feed log entries from a single session to be accessible together — including the total runtime of each script — so I can review overall data pipeline health at a glance.

**Why this priority**: Session-level visibility helps identify patterns (e.g., "every morning run the PitcherList feed is slow" or "run_free_agent_hitters.py takes 30s total") that single-entry logs do not surface.

**Independent Test**: Run two scripts back-to-back and confirm both sessions' log entries are present, distinguishable, and each script produces a summary entry showing total elapsed time.

**Acceptance Scenarios**:

1. **Given** multiple scripts are run in the same terminal session, **When** logs are reviewed, **Then** entries from all scripts are present with timestamps.
2. **Given** the log output is reviewed, **When** the developer scans it, **Then** each entry shows which script triggered the feed fetch.
3. **Given** a script completes successfully, **When** the log is reviewed, **Then** a single summary entry shows the script name, total wall-clock duration, and a "completed" outcome.
4. **Given** a script exits due to an unhandled exception, **When** the log is reviewed, **Then** the summary entry shows the script name, duration up to failure, and an "error" outcome with the exception type.

---

### Edge Cases

- What happens when a collector is called but makes no external network request (e.g., returns immediately from cache)? Log should still record the cache hit and duration.
- What happens when the logging mechanism itself fails (e.g., file permissions, disk full)? The script must continue running — logging failure must not surface as a script error.
- What happens when the same collector is invoked multiple times in a single script run? Each invocation gets its own log entry.
- What happens when a script is invoked via `main.py` menu rather than directly? The script summary entry should still record the script module name, not `main.py`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST record a log entry for every external data feed fetch initiated by any collector.
- **FR-002**: Each log entry MUST include: timestamp, collector name, operation description, duration in seconds, and outcome (success / error / cache-fallback).
- **FR-003**: Each error log entry MUST include the error type and message in addition to the standard fields.
- **FR-004**: Logging MUST NOT disrupt normal script execution — any failure in the logging mechanism MUST be silently suppressed.
- **FR-005**: Log output MUST be written to the console (stderr) so it does not pollute script output intended for the user.
- **FR-006**: The logging source MUST be a single shared utility usable by all collectors without duplicating instrumentation logic.
- **FR-007**: Cache fallback events (per Principle III of the constitution) MUST be distinguishable from successful fresh fetches in the log.
- **FR-008**: Each log entry MUST record which script or entry point triggered the fetch, when available.
- **FR-009**: The system MUST record a summary log entry for each complete script run, capturing the script name, total wall-clock duration, and overall outcome (completed / error).

### Key Entities *(include if feature involves data)*

- **FeedLogEntry**: Represents a single data fetch event. Key attributes: timestamp, collector name, operation, duration (seconds), outcome (success/error/cache-fallback), error details (optional), triggering script (optional).
- **ScriptRunEntry**: Represents a complete script execution. Key attributes: timestamp (start), script name, total duration (seconds), outcome (completed/error), error type (optional).
- **Collector**: Any module in `collectors/` that fetches data from an external source. Each collector produces one or more FeedLogEntry values per run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every external data fetch across all collectors produces a corresponding log entry — 0 unlogged fetches when logging is enabled.
- **SC-002**: A developer can determine the root cause of a failed fetch within 60 seconds of reviewing the log output, without requiring additional debugging steps.
- **SC-003**: Adding logging to a new collector requires no more than 2 lines of instrumentation code at the call site.
- **SC-004**: Logging overhead adds no more than 5 ms per fetch event to total script runtime.
- **SC-005**: A logging failure never causes a script to exit with a non-zero status when the underlying fetch itself succeeded.
- **SC-006**: Every script run produces exactly one summary log entry showing the script name and total elapsed time, readable at a glance without parsing individual feed entries.

## Assumptions

- Logging output to the console (stderr) is acceptable for v1; file-based or structured log storage is out of scope.
- All collectors that fetch from external websites are in the `collectors/` directory — no collectors exist elsewhere.
- The logging utility will live in `utils/` to respect the layer separation defined in the constitution (Principle I).
- Scripts do not need to opt in explicitly — logging is on by default whenever a collector fetch occurs.
- Log verbosity does not need to be runtime-configurable for v1; all feed events are always logged.
- Feed logging is always active regardless of execution context (scripts, tests, or other callers). Test authors who want to silence it may configure their test framework to suppress stderr or set the logger's level.
- ESPN credential values (`ESPN_S2`, `ESPN_SWID`) MUST NOT appear in log output (aligns with constitution Principle III).

## Clarifications

### Session 2026-06-02

- Q: Should the feed logger suppress output during automated test runs? → A: Always log regardless — test authors silence it via test config (e.g., log level filter) if needed.
- Q: Should error log entries include a stack trace in addition to exception type and message? → A: Exception type and message only — no stack trace.
