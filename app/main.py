from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_api_key
from app.routes import dashboard, drops, feed_status, health, optimizer, pitcher_starts, streamers, weekly_scores
from utils.cache_store import store as _cache

_build_sha = os.getenv("BUILD_SHA", "dev")
logging.getLogger("uvicorn.error").info("StreamerKit build=%s", _build_sha)

_api_logger = logging.getLogger("baseball.api")
if not _api_logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(message)s"))
    _api_logger.addHandler(_h)
    _api_logger.setLevel(logging.INFO)
    _api_logger.propagate = False


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _cache.prune_expired()
    yield


app = FastAPI(title="StreamerKit", version="1.0", lifespan=_lifespan)


@app.middleware("http")
async def _timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.0f}ms"
        _api_logger.info(
            "[API] %sZ | %s %s | %d | %dms",
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            request.method,
            request.url.path,
            response.status_code,
            round(duration_ms),
        )
    return response


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
app.include_router(feed_status.router, prefix="/api", **_protected)
app.include_router(pitcher_starts.router, prefix="/api", **_protected)
app.include_router(weekly_scores.router, prefix="/api", **_protected)
app.include_router(optimizer.router, prefix="/api", **_protected)
app.include_router(dashboard.router, prefix="/api", **_protected)

_frontend = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")
