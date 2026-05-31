from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app import response_cache
from services.pitchers_service import get_pitcher_start_evaluation, get_streaming_pitcher_review
from services.scores_service import get_weekly_scores
from services.waivers_service import get_recent_drops_waiver_review

router = APIRouter()

_TTL = 300


@router.get("/dashboard")
async def dashboard() -> dict:
    today = date.today().isoformat()
    cache_key = f"dashboard_{today}"
    cached = response_cache.get(cache_key, ttl_seconds=_TTL)
    if cached is not None:
        return cached

    streamers_data = get_streaming_pitcher_review()
    top_streamer = None
    if streamers_data.get("rows"):
        top_streamer = min(
            streamers_data["rows"],
            key=lambda r: (int(r.get("streamer_rank") or 9999), -float((r.get("recommendation") or {}).get("score") or 0.0)),
        )

    drops_data = get_recent_drops_waiver_review(days=2, top=3)
    top_drop = drops_data["rows"][0] if drops_data.get("rows") else None

    pitcher_starts_data = get_pitcher_start_evaluation()
    scores_data = get_weekly_scores(latest_scored=True)

    data = {
        "generated_on": today,
        "top_streamer": top_streamer,
        "top_waiver_drop": top_drop,
        "pitcher_starts": {
            "team": pitcher_starts_data.get("team"),
            "probable_roster_count": pitcher_starts_data.get("probable_roster_count"),
            "recommended_rows": pitcher_starts_data.get("recommended_rows", [])[:2],
            "suggested_moves": pitcher_starts_data.get("suggested_moves", []),
        },
        "weekly_scores": {
            "period": scores_data.get("period"),
            "my_team": scores_data.get("my_team"),
            "median_score": scores_data.get("median_score"),
            "mean_score": scores_data.get("mean_score"),
        },
    }
    response_cache.set(cache_key, data)
    return data
