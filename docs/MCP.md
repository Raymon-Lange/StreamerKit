# MCP Connector

This project includes an MCP server that proxies to the FastAPI service.

## Requirements

- FastAPI server running (default: `http://127.0.0.1:8000`)
- `fastmcp` installed

## Environment

- `STREAMERKIT_API_BASE_URL` (optional, defaults to `http://127.0.0.1:8000`)
- `API_KEY` (optional, passed as `x-api-key` to API)

## Run MCP Server

```bash
python -m mcp.server
```

## Tools Exposed

- `get_recent_drops_waiver_review(days, trend_games, top, claim_mode, league_id, year)`
- `get_free_agent_hitters(top, size, trend_games, trend_workers, league_id, year)`
- `get_streaming_pitchers(pitcher, league_id, year)`
