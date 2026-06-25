# n8n: Lineup Monitor & Auto-Replacement

## Purpose

Run on a schedule during game-day mornings to detect starting roster players who are
confirmed out of their MLB lineup, then surface the best available replacement from
your bench using the roster optimizer. Send a notification so you can make the swap
before first pitch.

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
                          [Get Optimizer Swaps] ← [Roster Optimizer]
                                         ↓
                             [Match Swap to Problem Slot]
                                         ↓
                                  [Notify]
```

---

## Production Base URL

```
https://streamerkit.fire-hive.com
```

All n8n HTTP Request nodes should use this as the base URL with the path appended.

---

## n8n Credential Setup

In n8n, create one **Header Auth** credential:

| Field | Value |
|---|---|
| Name | `StreamerKit API Key` |
| Header Name | `X-API-Key` |
| Header Value | *(your API key from `.env`)* |

Attach this credential to every HTTP Request node in the workflow.

---

## Endpoints & Purpose

### 1. `GET /api/my-roster`

**Full URL**: `https://streamerkit.fire-hive.com/api/my-roster`

**n8n HTTP Request node settings**:

| Field | Value |
|---|---|
| Method | `GET` |
| URL | `https://streamerkit.fire-hive.com/api/my-roster` |
| Authentication | Header Auth → `StreamerKit API Key` |
| Response Format | `JSON` |

**Used in**: Fetch My Roster node

**Purpose**: Single call that returns your entire fantasy roster split into `starters`
and `bench`, each player tagged with their current fantasy slot and real-life batting
lineup status.

**What to extract**:

From `starters` — flag any player matching **all** of:
- `in_lineup === false`
- `lineup_status` is `"bench"` or `"not_found"` (confirmed absent; skip `"lineup_not_posted"` and `"no_game"`)
- `lineup_slot` does **not** start with `SP`/`RP`/`P` (pitchers are irrelevant here)

From `bench` — note any players with `in_lineup === true` and `lineup_slot === "BE"`
as context; the optimizer will rank them properly in the next step.

**Key fields**:

| Field | Use |
|---|---|
| `name` | Display name and lookup key for subsequent calls |
| `lineup_slot` | Which fantasy slot the problem player occupies (e.g. `OF`, `1B`) |
| `in_lineup` | `false` = confirmed out, `null` = pitcher (skip), `true` = fine |
| `lineup_status` | `"bench"` / `"not_found"` = act now; `"lineup_not_posted"` = wait |
| `batting_slot` | On bench candidates: shows they're actually in the batting order |
| `injury_status` | Surface to the notification — `DAY_TO_DAY` etc. provides context |

---

### 2. `GET /api/roster-optimizer`

**Full URL**: `https://streamerkit.fire-hive.com/api/roster-optimizer?trend_games=10&min_gap=5.0`

**n8n HTTP Request node settings**:

| Field | Value |
|---|---|
| Method | `GET` |
| URL | `https://streamerkit.fire-hive.com/api/roster-optimizer` |
| Authentication | Header Auth → `StreamerKit API Key` |
| Response Format | `JSON` |

**Query parameters** (add in the n8n "Query Parameters" section):

| Name | Value |
|---|---|
| `trend_games` | `10` |
| `min_gap` | `5.0` |

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

---

## Decision Logic (n8n IF nodes)

```
For each flagged-out starter:

  1. Does /api/roster-optimizer swaps[] contain an entry where sit.name matches
     the flagged player?
       YES → recommend start.name as the replacement; include score_gap and slot
       NO  → notify "no optimizer swap found for <player> — check roster manually"
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
    Optimizer score gap: <score_gap>

No replacement found:
  • <player_name> — no optimizer swap available, check roster manually
```

---

## Rate / Cache Notes

| Endpoint | Cache TTL | n8n implication |
|---|---|---|
| `https://streamerkit.fire-hive.com/api/my-roster` | 2 min | Polling every 30 min is well within the TTL window |
| `https://streamerkit.fire-hive.com/api/roster-optimizer` | 5 min | One call per workflow run is fine |
