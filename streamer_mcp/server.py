from __future__ import annotations

from streamer_mcp.tools.hitter_tools import free_agent_hitters
from streamer_mcp.tools.pitcher_tools import pitcher_start_eval, streamer_review, team_pitcher_eval
from streamer_mcp.tools.waiver_tools import recent_drops_waiver_review

try:
    from fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "fastmcp is required for MCP connector. Install with: pip install fastmcp"
    ) from exc


mcp = FastMCP("streamerkit")


@mcp.tool(description="Get recent dropped-player waiver targets from the StreamerKit API.")
def get_recent_drops_waiver_review(
    days: int = 2,
    trend_games: int = 10,
    top: int = 25,
    claim_mode: str = "all",
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return recent_drops_waiver_review(
        days=days,
        trend_games=trend_games,
        top=top,
        claim_mode=claim_mode,
        league_id=league_id,
        year=year,
    )


@mcp.tool(description="Get free-agent hitter recommendations from the StreamerKit API.")
def get_free_agent_hitters(
    top: int = 10,
    size: int = 75,
    trend_games: int = 15,
    trend_workers: int = 12,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return free_agent_hitters(
        top=top,
        size=size,
        trend_games=trend_games,
        trend_workers=trend_workers,
        league_id=league_id,
        year=year,
    )


@mcp.tool(description="Get streaming pitcher review from the StreamerKit API.")
def get_streaming_pitchers(
    pitcher: str | None = None,
    league_id: int | None = None,
    year: int | None = None,
    tomorrow: bool = False,
) -> dict:
    return streamer_review(
        pitcher=pitcher,
        league_id=league_id,
        year=year,
        tomorrow=tomorrow,
    )


@mcp.tool(description="Get team pitcher evaluation (ERA, strikeouts, keeper-cost rank) from the StreamerKit API.")
def get_team_pitcher_evaluation(
    team_id: int | None = None,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return team_pitcher_eval(
        team_id=team_id,
        league_id=league_id,
        year=year,
    )


@mcp.tool(description="Get pitcher start recommendations for your roster, with streamer fallback when no probable starters are on your team.")
def get_pitcher_start_evaluation(
    team_id: int | None = None,
    league_id: int | None = None,
    year: int | None = None,
    tomorrow: bool = False,
) -> dict:
    return pitcher_start_eval(
        team_id=team_id,
        league_id=league_id,
        year=year,
        tomorrow=tomorrow,
    )


if __name__ == "__main__":
    mcp.run()
