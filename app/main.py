from __future__ import annotations

from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.hitters import router as hitters_router
from app.routes.pitchers import router as pitchers_router
from app.routes.waivers import router as waivers_router

app = FastAPI(
    title="Baseball StreamerKit API",
    version="0.1.0",
    description=(
        "API for fantasy baseball waiver and streaming workflows. "
        "Includes recent-drop waiver review, free-agent hitter recommendations, and streaming pitcher review."
    ),
)

app.include_router(health_router)
app.include_router(waivers_router)
app.include_router(hitters_router)
app.include_router(pitchers_router)
