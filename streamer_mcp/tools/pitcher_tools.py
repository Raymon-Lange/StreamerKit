from __future__ import annotations

from streamer_mcp.tools.client import ApiClient


client = ApiClient()


def streamer_review(
    pitcher: str | None = None,
    league_id: int | None = None,
    year: int | None = None,
    tomorrow: bool = False,
) -> dict:
    return client.get(
        "/pitchers/streamers",
        {
            "pitcher": pitcher,
            "league_id": league_id,
            "year": year,
            "tomorrow": tomorrow or None,
        },
    )


def team_pitcher_eval(
    team_id: int | None = None,
    league_id: int | None = None,
    year: int | None = None,
) -> dict:
    return client.get(
        "/pitchers/team-eval",
        {
            "team_id": team_id,
            "league_id": league_id,
            "year": year,
        },
    )
