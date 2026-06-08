from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_api_key
from app.routes import dashboard, drops, health, optimizer, pitcher_starts, streamers, weekly_scores
from utils.cache_store import store as _cache

_build_sha = os.getenv("BUILD_SHA", "dev")
logging.getLogger("uvicorn.error").info("StreamerKit build=%s", _build_sha)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _cache.prune_expired()
    yield


app = FastAPI(title="StreamerKit", version="1.0", lifespan=_lifespan)

_cors_origins = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_methods=["GET"],
        allow_headers=["X-API-Key"],
    )

app.include_router(health.router)

_protected = {"dependencies": [Depends(verify_api_key)]}
app.include_router(streamers.router, prefix="/api", **_protected)
app.include_router(drops.router, prefix="/api", **_protected)
app.include_router(pitcher_starts.router, prefix="/api", **_protected)
app.include_router(weekly_scores.router, prefix="/api", **_protected)
app.include_router(optimizer.router, prefix="/api", **_protected)
app.include_router(dashboard.router, prefix="/api", **_protected)

_frontend = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")
