from __future__ import annotations

import dataclasses

from fastapi import APIRouter

from services.feed_health_service import build_snapshot

router = APIRouter()


@router.get("/feed-status")
async def feed_status() -> dict:
    return dataclasses.asdict(build_snapshot())
