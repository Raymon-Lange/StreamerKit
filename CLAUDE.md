# CLAUDE.md

This repository is a small Python package for fantasy baseball tooling.

## Current entry points

Use the menu wrapper:

```bash
python main.py
```

Or run the scripts directly:

```bash
python scripts/run_team_hitter_eval.py --team-id 1 --trend-games 10
python scripts/run_free_agent_hitters.py --top 10 --size 75 --trend-games 15
python scripts/run_sp_streamers.py
```

## Environment

The scripts expect these environment variables:

- `LEAGUE_ID`
- `TEAM_ID`
- `ESPN_S2`
- `ESPN_SWID`

They are loaded through `python-dotenv` from `.env`.

## Architecture

- `collectors/` handle external data access and parsing.
- `engines/` contain recommendation logic only.
- `models/player.py` contains the shared dataclasses.
- `utils/names.py` is the single source of truth for player-name normalization.
- `scripts/` orchestrate collectors plus engines and print results.

## Notes for future changes

- Keep collectors free of recommendation decisions.
- Keep engines free of HTTP requests and ESPN access.
- Prefer `PlayerRecord`, `RankingEntry`, `TrendSummary`, and `Recommendation` over ad hoc dicts.
- Reuse `normalize_name()` from `utils/names.py` for all joins across sources.
