# Fantasy Baseball Refactor README

This repo is split into three clear layers so you can prompt Codex or Claude with focused, smaller tasks instead of asking it to reason about one giant script.

## Goal

Separate the project into:

1. **Website fetchers** — collect ranking and article data from sites like Pitcher List.
2. **ESPN collectors** — connect to ESPN Fantasy and return your roster or free agents.
3. **Recommendation engines** — score players and decide whether they are adds, starts, holds, streams, or cuts.

That keeps scraping, league access, and recommendation logic independent.

---

## File structure

```text
baseball_refactor/
├── README.md
├── collectors/
│   ├── espn.py
│   ├── mlb_stats.py
│   └── pitcherlist.py
├── engines/
│   ├── hitter_engine.py
│   └── pitcher_engine.py
├── models/
│   └── player.py
├── scripts/
│   ├── run_free_agent_hitters.py
│   ├── run_sp_streamers.py
│   └── run_team_hitter_eval.py
└── utils/
    ├── config.py
    └── names.py
```

---

## What each folder does

### `collectors/`
These files fetch or normalize raw data.

- `pitcherlist.py`
  - scrapes Top 300 hitters
  - scrapes Top 400 dynasty rankings
  - finds the latest SP Streamers article
  - scrapes streamer tiers

- `espn.py`
  - connects to ESPN Fantasy Baseball
  - gets roster players
  - gets free-agent hitters
  - gets free-agent pitchers
  - converts raw ESPN player objects into shared `PlayerRecord` objects

- `mlb_stats.py`
  - gets MLB player IDs
  - gets hitter game logs
  - builds hitter trend summaries
  - gets pitcher season record and recent starts
  - gets today’s probable starters

### `engines/`
These files should **not scrape websites or call ESPN directly**. They only score or recommend.

- `hitter_engine.py`
  - evaluates roster hitters
  - evaluates free-agent hitters

- `pitcher_engine.py`
  - converts Pitcher List streamer tiers into actions

### `models/`
Shared structured objects.

- `player.py`
  - `PlayerRecord`
  - `RankingEntry`
  - `TrendSummary`
  - `Recommendation`

### `utils/`
Shared helpers.

- `names.py`
  - player name normalization
  - cleaning scraped names

- `config.py`
  - `.env` loading
  - app config

### `scripts/`
Thin entry-point scripts.

- `run_team_hitter_eval.py`
  - evaluates hitters on your ESPN team

- `run_free_agent_hitters.py`
  - ranks hitter waiver options

- `run_sp_streamers.py`
  - shows free-agent SPs starting today and their streamer tier

---

## Design rules for future prompts

Use these as guardrails when prompting Codex or Claude.

### Rule 1: collectors only collect
A collector can:
- fetch HTML
- call ESPN
- call MLB Stats API
- parse raw data
- return structured objects

A collector should **not**:
- decide whether a player is a must-add
- print final recommendation text
- contain league strategy logic

### Rule 2: engines only evaluate
An engine can:
- accept normalized inputs
- assign scores
- build recommendation labels
- explain why

An engine should **not**:
- call requests
- scrape a website
- connect to ESPN

### Rule 3: scripts stay thin
A script should:
- read CLI args
- call collectors
- call engines
- print output

A script should **not**:
- reimplement parsing logic
- duplicate name normalization
- contain large blocks of ranking logic

### Rule 4: all player matching uses normalized names
Any cross-source player join should use `normalize_name()` from `utils/names.py`.

### Rule 5: shared data shapes first
Before adding new recommendation logic, make sure new data is stored in:
- `PlayerRecord`
- `RankingEntry`
- `TrendSummary`
- `Recommendation`

---

## Good prompts to use with Codex or Claude

### Add a new collector
> Add a new collector file in `collectors/` called `fangraphs.py` that fetches hitter projections and returns a dictionary keyed by normalized player name. Reuse `RankingEntry` where possible and keep all parsing logic inside the collector.

### Add a new engine rule
> Update `engines/hitter_engine.py` so stolen-base upside adds bonus score for players ranked outside the top 150. Do not add any requests or scraping logic.

### Add a new script
> Create `scripts/run_dynasty_targets.py` that uses `collectors/pitcherlist.py`, `collectors/espn.py`, and `engines/hitter_engine.py` to show the best dynasty hitter adds from ESPN free agency.

### Improve matching
> Refactor all player matching so suffixes like Jr, Sr, II, and III are normalized consistently in `utils/names.py`. Do not duplicate that logic anywhere else.

### Add caching
> Add local JSON caching to `collectors/pitcherlist.py` and `collectors/mlb_stats.py` with a TTL, but keep recommendation logic unchanged.

---

## Suggested next steps

1. Add `__init__.py` files so the project works as a package cleanly.
2. Add a small test suite for:
   - name normalization
   - table parsing
   - recommendation thresholds
3. Add a cache layer to reduce repeated scraping.
4. Add a unified script for comparing your roster vs free agents.
5. Add support for more sources like FanGraphs or Baseball Savant.

---

## Environment variables

Create a `.env` file with:

```env
LEAGUE_ID=your_league_id
TEAM_ID=your_team_id
ESPN_S2=your_espn_s2_cookie
ESPN_SWID={your-swid-cookie}
```

---

## Install

```bash
pip install espn-api requests beautifulsoup4 MLB-StatsAPI python-dotenv
```

---

## Run examples

```bash
python scripts/run_team_hitter_eval.py --team-id 1
python scripts/run_free_agent_hitters.py --top 15
python scripts/run_sp_streamers.py
```

---

## Prompting summary

When prompting Codex or Claude:

- tell it which layer to change
- tell it which files it can touch
- tell it what it must not do
- ask for shared logic to stay centralized
- ask it to preserve `PlayerRecord`, `RankingEntry`, and `Recommendation` unless a change is necessary

Example:

> Refactor only the `collectors/pitcherlist.py` file to support a fallback parser for changed table layouts. Do not change the recommendation engines. Keep returned objects compatible with `RankingEntry`.
