# Research: IL Status Filter

**Feature**: 003-il-status-filter | **Date**: 2026-06-04

---

## Decision 1: Injury status data source

**Decision**: Use `espn_api.baseball.player.Player.injuryStatus` — the attribute already parsed
by the `espn-api` library from the ESPN payload.

**Rationale**: The library reads `injuryStatus` from `playerPoolEntry.player.injuryStatus` and
exposes it as `player.injuryStatus` (confirmed in
`.venv/lib/python3.12/site-packages/espn_api/baseball/player.py:14,19`). No extra network
call, no extra parsing, zero overhead. The `injured` boolean is also available but is
explicitly less authoritative — `injuryStatus` is the canonical field.

**Alternatives considered**:
- Scrape MLB Stats API injury report → rejected; adds latency, separate data source, name-join
  complexity, and the ESPN source is already in-flight.
- Use ESPN `injured: bool` alone → rejected; too coarse (no severity), and can disagree with
  `injuryStatus`.

---

## Decision 2: Where to extract and store injury status

**Decision**: Extract in `collectors/espn.py → player_to_record()`. Store in new
`PlayerRecord.injury_status: str | None` field. Collectors only store; they do not act.

**Rationale**: `player_to_record()` is the single conversion point from raw `espn-api` objects
to `PlayerRecord`. Centralizing extraction here means every downstream consumer (services,
scripts, API routes) automatically has access.

**Alternatives considered**:
- Extract ad hoc in each service → rejected; violates DRY and risks divergence between services.
- Store on `espn_raw` only and read in-place → rejected; couples consumers to raw ESPN object
  internals, breaking the data model abstraction principle.

---

## Decision 3: Filter placement for roster optimization

**Decision**: Filter in `services/optimizer_service.py → get_roster_optimizer()`, immediately
after `get_roster_players()` returns the `hitters` list, before scoring.

**Rationale**: The service layer is the correct place per constitution (services coordinate
collectors + engines). The existing `_BENCH_SLOTS` guard already lives here — this is
analogous. The filter is one line:
```python
_IL_EXCLUDE = {"INJURY_RESERVE", "OUT", "SUSPENSION"}
hitters = [p for p in hitters if (p.injury_status or "ACTIVE") not in _IL_EXCLUDE]
```

**Alternatives considered**:
- Filter in collector → rejected; collectors must be free of recommendation decisions.
- Filter in engine → rejected; engines must be free of ESPN/data-source knowledge.
- Filter in script → rejected; scripts are thin CLI entry points only.

---

## Decision 4: Waiver wire — label only, no filtering

**Decision**: Free agent hitter and SP streamer suggestions include all players regardless
of injury status. A label is appended to the name in CLI output and a colored badge is shown
in the web UI. No filtering at service level for waiver wire contexts.

**Rationale**: User explicitly requested this: "i still want to make the suggestion for
waiver wire pick up, let me make the call." An IR player on the waiver wire may still be
worth a stash pickup for a future return.

---

## Decision 5: Web UI — reuse Pill pattern from DailyBrief.tsx

**Decision**: Add an inline `InjuryBadge` component using Tailwind pill classes that match
the existing `Pill` component in `DailyBrief.tsx`. Apply to `Streamers.tsx` and
`TomorrowStreamers.tsx`.

Color mapping:
- `INJURY_RESERVE`, `OUT`, `SUSPENSION` → `bg-red-900 text-red-300`
- `DAY_TO_DAY` → `bg-orange-900 text-orange-300`
- `QUESTIONABLE` → `bg-yellow-900 text-yellow-300`

Badge text: short label (`IR`, `OUT`, `SUSP`, `DTD`, `QUES`) — no brackets, consistent with
pill label conventions in the existing UI.

**Rationale**: `DailyBrief.tsx` already defines a `Pill` helper with identical styling.
Reusing the same pattern avoids introducing a new shared component while keeping styling
consistent.

**Note**: There is no free agent hitters card in the current web UI
(`frontend/src/components/` has no hitters list component). Web UI badge scope is limited to
`Streamers.tsx` and `TomorrowStreamers.tsx`.

---

## Decision 6: CLI label format

**Decision**: Labels appended inline after player name: `[IR]`, `[OUT]`, `[SUSP]`, `[DTD]`,
`[QUES]`. No label for `ACTIVE` or `None`.

**Rationale**: Brackets are the conventional CLI inline annotation pattern. Short abbreviations
fit within the existing 96-char output width without wrapping.

---

## No open unknowns

All NEEDS CLARIFICATION items from the Technical Context are resolved above. No external
research required beyond confirmed library source inspection.
