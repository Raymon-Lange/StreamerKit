from __future__ import annotations

from fastapi import Depends, FastAPI

from app.auth import verify_api_key
from app.routes import dashboard, drops, health, optimizer, pitcher_starts, streamers, weekly_scores

app = FastAPI(title="StreamerKit", version="1.0")

app.include_router(health.router)

_protected = {"dependencies": [Depends(verify_api_key)]}
app.include_router(streamers.router, prefix="/api", **_protected)
app.include_router(drops.router, prefix="/api", **_protected)
app.include_router(pitcher_starts.router, prefix="/api", **_protected)
app.include_router(weekly_scores.router, prefix="/api", **_protected)
app.include_router(optimizer.router, prefix="/api", **_protected)
app.include_router(dashboard.router, prefix="/api", **_protected)
