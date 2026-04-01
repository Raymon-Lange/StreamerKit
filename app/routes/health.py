from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health Check")
def health() -> dict:
    return {"status": "ok"}
