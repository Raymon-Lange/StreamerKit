# Fantasy Baseball Tools

This repository evaluates ESPN fantasy baseball rosters and waiver options by combining ESPN league data, Pitcher List rankings, ESPN dynasty rankings, and MLB Stats API trends.

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
3. Pulls ESPN Top 300 dynasty rankings.
4. Builds recent trend stats from MLB Stats API.
5. Produces roster recommendations from the merged dynasty signal.

### Free-agent hitters

`scripts/run_free_agent_hitters.py`:

1. Connects to ESPN and gathers hitter free agents.
2. Pulls Pitcher List redraft and dynasty rankings.
3. Pulls ESPN Top 300 dynasty rankings.
4. Builds recent trend stats from MLB Stats API.
5. Produces waiver recommendations from the merged dynasty signal.

`scripts/run_hitter_free_agents.py` forwards to `scripts/run_free_agent_hitters.py` for compatibility.

### SP streamers

`scripts/run_sp_streamers.py`:

1. Connects to ESPN and fetches free-agent starting pitchers.
2. Pulls today's probable starters from ESPN's public MLB scoreboard endpoint.
3. Scrapes the latest Pitcher List SP Streamers article.
4. Maps streamer tiers to pickup/skip recommendations.

## Ranking caches

Ranking collectors cache data for 15 days at:

- `.cache/espn_dynasty_top300.json`
- `.cache/pitcherlist_top_hitters.json`
- `.cache/pitcherlist_dynasty_hitters.json`

If a cache file is not older than 15 days, the collector reads cached data and skips refresh. If refresh fails, collectors fall back to cached payloads when available.

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

## Run

```bash
python main.py
python scripts/run_team_hitter_eval.py --team-id 1 --trend-games 10
python scripts/run_free_agent_hitters.py --top 10 --size 75 --trend-games 15
python scripts/run_sp_streamers.py
```
