from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter()

_build_sha = os.getenv("BUILD_SHA", "dev")


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "build": _build_sha}
