---
name: baseball-add-source
description: Add or integrate a new external ranking/stats source into this baseball repository. Use when asked to scrape or pull data from a new website/API, create or update a collector in collectors/, apply the 15-day file-age cache policy in .cache/, and wire the new source into hitter/pitcher scripts without breaking existing recommendation flows.
---

# Baseball Add Source

## Overview

Use this workflow whenever adding a new source.

## Workflow

1. Inspect data shape and integration points.
- Read `models/player.py` and target script(s) in `scripts/`.
- Decide whether the new source feeds `RankingEntry`, trend stats, or both.

2. Build a collector in `collectors/`.
- Fetch and parse source data.
- Normalize join keys with `utils.names.normalize_name`.
- Return structured objects keyed by normalized name.
- Keep recommendation logic out of collectors.

3. Apply 15-day file-age cache policy.
- Cache into `.cache/<source>_<dataset>.json`.
- Refresh only when cache file is older than 15 days (mtime check).
- On refresh failure, fall back to existing cache if present.
- Keep cache payload stable: metadata + rows list.

4. Wire into scripts.
- Update `scripts/run_free_agent_hitters.py` and/or `scripts/run_team_hitter_eval.py`.
- Combine multiple rankings into one signal using explicit rule (for example, best rank).
- Print per-source values in output so users can audit how the merged signal was computed.

5. Keep engine boundaries clean.
- Use existing engine functions in `engines/`.
- If new rules are required, update engine functions only; do not embed scoring in scripts.

6. Validate before finishing.
- Run syntax checks with `python3 -m py_compile` for edited modules.
- If credentials/deps are available, run the affected script path from `main.py` or direct script.

7. Update docs.
- Reflect new source and cache files in `README.md`.
- Keep examples aligned with real script arguments and behavior.

## Repository constraints

- Collectors collect and normalize data only.
- Engines evaluate recommendations only.
- Scripts orchestrate and print only.
- All cross-source joins use normalized player names.

## Reference

For a concrete checklist and cache payload shape, read:

- `references/add-source-checklist.md`
