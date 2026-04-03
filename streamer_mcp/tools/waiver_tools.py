from __future__ import annotations

from streamer_mcp.tools.client import ApiClient


client = ApiClient()


def recent_drops_waiver_review(
    days: int = 2,
    trend_games: int = 10,
    top: int = 25,
    claim_mode: str = "all",
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return client.get(
        "/waivers/recent-drops",
        {
            "days": days,
            "trend_games": trend_games,
            "top": top,
            "claim_mode": claim_mode,
            "league_id": league_id,
            "year": year,
        },
    )
