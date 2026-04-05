# Fantasy Baseball Tools

This repository evaluates ESPN fantasy baseball rosters and waiver options by combining ESPN league data, Pitcher List rankings, ESPN points-leagues rankings, ESPN dynasty rankings, league draft keeper-cost projections, and MLB Stats API trends.

## Current architecture

- `collectors/` fetch and normalize data.
- `engines/` convert normalized inputs into recommendations.
- `models/` define shared dataclasses.
- `scripts/` are thin CLI entry points.
- `main.py` provides a menu over the main scripts.

Shared data types are in `models/player.py`:

- `PlayerRecord`
- `RankingEntry`
- `TrendSummary`
- `Recommendation`

All cross-source player joins should use `utils/names.py`.

## Main workflows

### Team hitter evaluation

`scripts/run_team_hitter_eval.py`:

1. Connects to ESPN and reads roster hitters.
2. Pulls Pitcher List redraft and dynasty rankings.
3. Pulls ESPN points Top 300 and ESPN dynasty Top 300 rankings.
4. Pulls ESPN league draft picks and computes keeper-cost projection (`draft round - 2`, floor round 1).
5. Builds recent trend stats from MLB Stats API.
6. Produces roster recommendations from weighted intent-based scoring.

### Free-agent hitters

`scripts/run_free_agent_hitters.py`:

1. Connects to ESPN and gathers hitter free agents.
2. Pulls Pitcher List redraft and dynasty rankings.
3. Pulls ESPN points Top 300 and ESPN dynasty Top 300 rankings.
4. Pulls ESPN league draft picks and computes keeper-cost projection (`draft round - 2`, floor round 1).
5. Builds recent trend stats from MLB Stats API.
6. Produces waiver recommendations from weighted intent-based scoring.

`scripts/run_hitter_free_agents.py` forwards to `scripts/run_free_agent_hitters.py` for compatibility.

### SP streamers

`scripts/run_sp_streamers.py`:

1. Connects to ESPN and fetches free-agent starting pitchers.
2. Pulls today's probable starters from ESPN's public MLB scoreboard endpoint.
3. Scrapes the latest Pitcher List SP Streamers article.
4. Maps streamer tiers to pickup/skip recommendations.

### Recent drops waiver review

`scripts/run_recent_drops_waiver_review.py`:

1. Pulls ESPN recent league activity and filters to dropped players in a lookback window (default 2 days).
2. Keeps only dropped players that are currently available as free agents.
3. Evaluates hitter drops with redraft/dynasty/trend signals and pitcher drops with streamer-tier signal.
4. Filters out non-actionable results (`PASS`, `SKIP`, and pitcher `Not Ranked`) and prints claim-focused targets.

### SP streamers performance baseline (no cache)

Baseline profile captured on March 31, 2026 with:

```bash
python3 -m cProfile -s cumtime scripts/run_sp_streamers.py
```

Result was ~27.2s total runtime (no explicit caching in this script path). Main hotspots:

1. `collectors.espn.build_context` / ESPN league+roster load: ~13.5s
2. HTTP stack (`requests`/`urllib3` network I/O): ~8.6s across 35 calls
3. `collectors.mlb_stats.get_pitcher_stats` in per-pitcher loop: ~6.2s total
4. `collectors.espn.get_free_agent_pitchers`: ~3.8s

Interpretation: runtime is mostly external API/network and ESPN parsing overhead, not local computation.

## Hitter scoring weights

Hitter recommendations use three weighted buckets:

- `current_performance` (recent MLB trend stats)
- `current_year_rankings` (Pitcher List redraft + ESPN points Top 300)
- `dynasty_rankings` (Pitcher List dynasty + ESPN dynasty Top 300 + projected keeper draft cost converted to pick rank)

Default weights by script intent:

- Waiver (`scripts/run_free_agent_hitters.py`): `45% / 40% / 15%`
- Team eval (`scripts/run_team_hitter_eval.py`): `30% / 25% / 45%`

You can override weights per script run:

- `--weight-current-performance`
- `--weight-current-year-rankings`
- `--weight-dynasty-rankings`

When a player is missing a ranking source, that bucket score falls back to `0` instead of reallocating all weight to other buckets.

## Ranking caches

Ranking collectors cache data for 15 days at:

- `.cache/espn_dynasty_top300.json`
- `.cache/espn_keeper_cost_<league_id>_<year>.json`
- `.cache/espn_points_top300_2026.json`
- `.cache/pitcherlist_top_hitters.json`
- `.cache/pitcherlist_dynasty_hitters.json`

If a cache file is not older than 15 days, the collector reads cached data and skips refresh. If refresh fails, collectors fall back to cached payloads when available.
`espn_keeper_cost_<league_id>_<year>.json` is intentionally different: once it exists, it is reused without TTL refresh (unless explicitly force-refreshed in code).

## Environment

Create a `.env` file:

```env
LEAGUE_ID=your_league_id
TEAM_ID=your_team_id
ESPN_S2=your_espn_s2_cookie
ESPN_SWID={your-swid-cookie}
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## API server

FastAPI app entrypoint: `app/main.py`

Run locally:

```bash
uvicorn app.main:app --reload
```

OpenAPI docs:

- `/docs`
- `/redoc`
- `/openapi.json`

See `docs/API.md` for endpoint and parameter details.

### Docker dev workflow

Files:

- `Dockerfile`
- `docker-compose.yml`
- `tools/dev_up.sh`
- `tools/dev_down.sh`
- `tools/dev_logs.sh`

Commands:

```bash
tools/dev_up.sh
tools/dev_logs.sh
tools/dev_down.sh
```

## MCP connector

MCP server entrypoint: `streamer_mcp/server.py`

Run:

```bash
python -m streamer_mcp.server
```

See `docs/MCP.md` for setup and tool details.

## Run

```bash
python main.py
python scripts/run_team_hitter_eval.py --team-id 1 --trend-games 15
python scripts/run_free_agent_hitters.py --top 10 --size 75 --trend-games 15
python scripts/run_sp_streamers.py
python scripts/run_recent_drops_waiver_review.py --days 2 --top 25
```
