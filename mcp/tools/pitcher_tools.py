from __future__ import annotations

from mcp.tools.client import ApiClient


client = ApiClient()


def streamer_review(
    pitcher: str | None = None,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return client.get(
        "/pitchers/streamers",
        {
            "pitcher": pitcher,
            "league_id": league_id,
            "year": year,
        },
    )
