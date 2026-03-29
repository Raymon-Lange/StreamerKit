# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the tools

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Load credentials, then run the main tool
source espn_cookies.env && python espn_free_agent.py

# Override league or year
python espn_free_agent.py --league-id <id> --year 2025

# Look up specific pitchers directly
python sp_recommender.py "Aaron Nola" "Shane Baz"
python sp_recommender.py "Aaron Nola" --url https://pitcherlist.com/...
```

## Credentials

The scripts require two ESPN session cookies as environment variables:

| Variable   | Source                                             |
|------------|----------------------------------------------------|
| `ESPN_S2`  | Browser DevTools → Application → Cookies → espn.com |
| `ESPN_SWID`| Same location; format: `{UUID}`                    |

`LEAGUE_ID` (hardcoded in `espn_free_agent.py:51`) identifies the ESPN fantasy league. It can be overridden at runtime with `--league-id`.

## Architecture

Two scripts, where `espn_free_agent.py` is the entry point and imports from `sp_recommender.py`.

**Data flow in `espn_free_agent.py`:**
1. Fetches today's MLB probable starters from ESPN's public scoreboard API
2. Connects to the private ESPN fantasy league via `espn-api` (requires cookies)
3. Fetches free agent SPs from the league
4. Cross-references with PitcherList tiers (delegated to `sp_recommender`)
5. Prints player cards sorted by % owned — starters today first, rest as a top-5 summary

**`sp_recommender.py` responsibilities:**
- `get_latest_pl_url()` — scrapes PitcherList category page to find the current week's SP streamer post
- `scrape_pl_tiers(url)` — parses that post into a dict of `normalized_name → (display_name, tier)`
- `get_pitcher_stats(name)` — looks up a pitcher in MLB StatsAPI and returns season record, last-10 record, and last-2 start box scores
- Can also be run standalone to look up specific pitchers by name

**External dependencies:**
- `espn-api` — ESPN fantasy league access (private, requires cookies)
- `MLB-StatsAPI` (`statsapi`) — player lookup, season stats, game logs
- `requests` + `beautifulsoup4` — PitcherList web scraping
- `pitcherlist.com` — streamer tier rankings (scraped, no API key needed)
