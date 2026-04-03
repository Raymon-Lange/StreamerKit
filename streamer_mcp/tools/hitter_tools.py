from __future__ import annotations

from streamer_mcp.tools.client import ApiClient


client = ApiClient()


def free_agent_hitters(
    top: int = 10,
    size: int = 75,
    trend_games: int = 15,
    trend_workers: int = 12,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return client.get(
        "/hitters/free-agents",
        {
            "top": top,
            "size": size,
            "trend_games": trend_games,
            "trend_workers": trend_workers,
            "league_id": league_id,
            "year": year,
        },
    )
