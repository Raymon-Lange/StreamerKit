# Fantasy Baseball Tools

This repository evaluates ESPN fantasy baseball rosters and waiver options by combining ESPN league data, Pitcher List rankings, ESPN points-leagues rankings, ESPN dynasty rankings, league draft keeper-cost projections, and MLB Stats API trends.

## Current architecture

- `collectors/` fetch and normalize data.
- `engines/` convert normalized inputs into recommendations.
- `models/` define shared dataclasses.
- `services/` coordinate collectors and engines for reusable workflows.
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

### Team pitcher evaluation

`scripts/run_team_pitcher_eval.py`:

1. Connects to ESPN and reads roster pitchers.
2. Pulls MLB season pitcher stats for ERA and strikeouts.
3. Pulls ESPN league draft picks and computes keeper-cost projection (`draft round - 2`, floor round 1).
4. Ranks pitchers by team-relative ERA rank (lower better), K rank (higher better), and keeper-cost rank (lower projected pick better).

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

### Roster optimizer

`scripts/run_roster_optimizer.py`:

1. Connects to ESPN and reads your active roster hitters and bench hitters.
2. Pulls Pitcher List redraft rankings and recent MLB trend stats.
3. Scores each hitter and identifies bench players who should start over active players.
4. Prints recommended lineup swaps with score gap and reasoning; skips if lineup is already optimal.

### Pitcher start eval

`scripts/run_pitcher_start_eval.py`:

1. Identifies your roster pitchers scheduled to start today (or tomorrow).
2. Pulls Pitcher List SP streamer tiers and maps roster starters to streamer ranks.
3. Recommends the top 2 starters to deploy.
4. Falls back to free-agent streaming options when no roster pitcher has a probable start.

### Weekly scores

`scripts/run_weekly_scores.py`:

1. Connects to ESPN and fetches the current (or specified) matchup period scoreboard.
2. Ranks all league teams by score and highlights your team's position.
3. Prints mean and median scores alongside top-half / bottom-half split.
4. Use `--latest-scored` to report the most recently completed period instead of the current week.

### Ranking page sources

`scripts/show_ranking_page_sources.py`:

Reads each ranking cache file and prints its source URL, fetch timestamp, and article date. Useful for verifying that cached rankings are current. Pass `--show-missing` to also flag cache files that are absent or unreadable.

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
API_KEY=your_api_key
```

Generate an `API_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as the `API_KEY` value. This key is required for all `/api/*` requests — pass it as the `X-API-Key` header.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Dev server

```bash
docker compose -f docker-compose.dev.yml up
```

- API: http://localhost:9471
- Web: http://localhost:9472

The dev compose maps `API_KEY` from `.env` to `VITE_API_KEY` automatically — no extra config needed.

## Run

```bash
python main.py
python scripts/run_team_hitter_eval.py --team-id 1 --trend-games 15
python scripts/run_team_pitcher_eval.py --team-id 1
python scripts/run_free_agent_hitters.py --top 10 --size 75 --trend-games 15
python scripts/run_sp_streamers.py
python scripts/run_recent_drops_waiver_review.py --days 2 --top 25
python scripts/run_roster_optimizer.py --team-id 1 --trend-games 10 --min-gap 10
python scripts/run_pitcher_start_eval.py --team-id 1
python scripts/run_weekly_scores.py --latest-scored
python scripts/show_ranking_page_sources.py --show-missing
```

---

## Deploy

```bash
# 1. Clone the repo
git clone https://github.com/Raymon-Lange/baseball.git /home/deploy/baseball
cd /home/deploy/baseball

# 2. Copy and configure environment
cp .env.example .env
nano .env   # fill in all values marked "changeme"

# 3. Deploy
docker compose pull
docker compose up -d
```

---

## Environment variables

See `.env.example` for the full list with descriptions.

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_NAME` | Yes | `baseball` | App identifier; controls container name prefix |
| `APP_DOMAIN` | Yes | — | Public domain (e.g. `baseball.hive.local`) |
| `COMPOSE_PROJECT_NAME` | Yes | `baseball` | Docker Compose project name |
| `STORAGE_MODE` | Yes | `local` | Storage mode (`local` or `s3`) |
| `STORAGE_PATH` | Yes | — | Base path for persistent data volumes |
| `TZ` | Yes | `UTC` | Timezone for all services |
| `ESPN_S2` | Yes | — | ESPN session cookie (from browser devtools) |
| `ESPN_SWID` | Yes | — | ESPN SWID cookie (UUID with braces) |
| `LEAGUE_ID` | Yes | — | ESPN fantasy league ID |
| `TEAM_ID` | Yes | — | Your team ID within the league |
| `API_KEY` | Yes | — | API key for all `/api/*` requests (`X-API-Key` header) |

---

## Backup and restore

```bash
# Back up the ranking cache
tar -czf baseball-cache-$(date +%Y%m%d).tar.gz ./data/.cache

# Restore from backup
tar -xzf baseball-cache-<date>.tar.gz
```

---

## Troubleshoot

```bash
# Check container health
docker compose ps

# View recent logs
docker compose logs --tail 50 streamerkit

# Follow logs live
docker compose logs -f

# Enter the app container
docker compose exec streamerkit sh

# Restart the service
docker compose restart streamerkit
```

### Common issues

- **ESPN auth errors**: `ESPN_S2` and `ESPN_SWID` cookies expire periodically — re-copy them from browser devtools.
- **Stale rankings**: Delete the relevant file under `./data/.cache/` to force a refresh on the next run.
- **Port 8000 in use**: Change the host port in `docker-compose.yml` (e.g. `"8001:8000"`).
