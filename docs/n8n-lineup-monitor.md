# n8n: Lineup Monitor & Auto-Replacement

## Purpose

Run on a schedule during game-day mornings to detect starting roster players who are
confirmed out of their MLB lineup, then surface the best available replacement from
the bench or waiver wire. Send a notification so you can make the swap before first pitch.

---

## Trigger

**Schedule node** — every 30 minutes between 10:00 AM and 2:00 PM ET.

Lineups for day games are typically posted by 11:30 AM; night game lineups post around 5 PM.
Run a second schedule (every 30 min, 4:00–6:00 PM ET) if you carry players with night games.

---

## Workflow Overview

```
[Schedule] → [Fetch My Roster] → [Filter Out Starters]
                                         ↓
                              [Find Bench Replacements]
                                         ↓
                          [Score & Rank Replacements] ← [Roster Optimizer]
                                         ↓
                     [Check Waiver Wire if No Bench Option] ← [Recent Drops]
                                         ↓
                                  [Notify]
```

---

## Endpoints & Purpose

### 1. `GET /api/my-roster`

**Used in**: Fetch My Roster node

**Purpose**: Single call that returns your entire fantasy roster split into `starters`
and `bench`, each player tagged with their current fantasy slot and real-life batting
lineup status.

**What to extract**:

From `starters` — flag any player matching **all** of:
- `in_lineup === false`
- `lineup_status` is `"bench"` or `"not_found"` (confirmed absent; skip `"lineup_not_posted"` and `"no_game"`)
- `lineup_slot` does **not** start with `SP`/`RP`/`P` (pitchers are irrelevant here)

From `bench` — collect players matching:
- `in_lineup === true`
- `lineup_slot === "BE"` (active bench, not IL)

These bench players are your first-pass replacement candidates: they're healthy, confirmed
in their lineup today, and currently warming the bench in your fantasy roster.

**Key fields**:

| Field | Use |
|---|---|
| `name` | Display name and lookup key for subsequent calls |
| `lineup_slot` | Which fantasy slot the problem player occupies (e.g. `OF`, `1B`) |
| `in_lineup` | `false` = confirmed out, `null` = pitcher (skip), `true` = fine |
| `lineup_status` | `"bench"` / `"not_found"` = act now; `"lineup_not_posted"` = wait |
| `batting_slot` | On bench candidates: shows they're actually in the batting order |
| `injury_status` | Surface to the notification — `DAY_TO_DAY` etc. provides context |

**Headers**: `X-API-Key: <key>`

---

### 2. `GET /api/roster-optimizer`

**Used in**: Score & Rank Replacements node

**Purpose**: Returns pre-scored swap recommendations — bench hitters who should be
starting over current starters, ranked by score gap. Use this to validate and rank the
bench candidates identified from `/api/my-roster` and to surface the optimizer's top pick.

**What to extract**:

`swaps[]` — each entry has:
- `sit.name` — the underperforming starter (may overlap with your flagged-out players)
- `start.name` — the recommended bench player to bring in
- `slot` — the fantasy position slot the swap targets
- `score_gap` — magnitude of the improvement; higher = more urgent

**How to use it**: If a flagged-out starter appears as `sit.name` in any swap, the `start`
player in that swap is the optimizer's ranked replacement. Present it as the top suggestion.

**Query params**:

| Param | Recommended value | Why |
|---|---|---|
| `trend_games` | `10` | Enough recency without noise |
| `min_gap` | `5.0` | Lower than default to surface more options when a replacement is needed |

**Headers**: `X-API-Key: <key>`

---

### 3. `GET /api/recent-drops`

**Used in**: Check Waiver Wire node (only if no bench replacement found)

**Purpose**: Shows players recently dropped by other teams that are available on waivers.
If no bench player is confirmed in their lineup today, check here for a same-day pickup.

**What to extract**:

`rows[]` filtered to:
- `kind === "H"` (hitters only, unless a pitcher slot is the problem)
- `recommendation.action` not in `["PASS", "SKIP"]`

Then cross-reference each dropped player's name against `GET /api/lineup` (see below) to
confirm they're actually in their lineup today before recommending the pickup.

**Query params**:

| Param | Recommended value | Why |
|---|---|---|
| `days` | `1` | Only today's drops — fresher options |
| `top` | `15` | Wide enough net to find a playable hitter |

**Headers**: `X-API-Key: <key>`

---

### 4. `GET /api/lineup?player=<name>`

**Used in**: Waiver wire confirmation step

**Purpose**: Per-player lineup check. Use this to confirm a dropped player (from
`/api/recent-drops`) is actually in their MLB lineup today before recommending the pickup.
This avoids suggesting a waiver claim on someone who is also sitting out.

**What to check**:
- `in_lineup === true` → safe to recommend
- `lineup_status === "lineup_not_posted"` → too early, skip or retry
- `in_lineup === false` → do not recommend regardless of waiver status

**Query params**:

| Param | Required | Notes |
|---|---|---|
| `player` | Yes | Full name; normalized server-side so minor variations are handled |
| `date` | No | Omit to default to today |

**Headers**: `X-API-Key: <key>`

---

## Decision Logic (n8n IF nodes)

```
For each flagged-out starter:

  1. Does any bench player (in_lineup=true, slot=BE) share position eligibility
     with the starter's lineup_slot?
       YES → recommend that bench player (prioritize highest batting_slot number
              that appears in optimizer swaps, else any confirmed starter)
       NO  → continue to waiver check

  2. Does /api/recent-drops return an H-type player with a non-PASS recommendation
     whose /api/lineup confirms in_lineup=true?
       YES → recommend as waiver pickup
       NO  → notify "no same-day replacement found, consider checking manually"
```

---

## Notification Payload (Slack / webhook)

Suggested fields to include in the alert:

```
⚠️ LINEUP ALERT — <timestamp>

Sitting out today:
  • <player_name> (<lineup_slot>) — status: <lineup_status> | <injury_status>

Recommended replacement:
  • <replacement_name> (<mlb_team>) — batting #<batting_slot>
    Source: [bench / waiver] | Optimizer gap: <score_gap>

No replacement found:
  • <player_name> — no confirmed bench or waiver option yet
```

---

## Rate / Cache Notes

| Endpoint | Cache TTL | n8n implication |
|---|---|---|
| `/api/my-roster` | 2 min | Calls closer than 2 min return cached data; polling every 30 min is safe |
| `/api/roster-optimizer` | 5 min | One call per workflow run is fine |
| `/api/recent-drops` | 5 min | One call per workflow run is fine |
| `/api/lineup` | 2 min | Safe to call per-player; avoid tight loops |

All requests need `X-API-Key` header. Store the key as an n8n credential (HTTP Header Auth).
