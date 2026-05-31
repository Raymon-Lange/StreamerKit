from __future__ import annotations

import os

from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("API_KEY", "")


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not _API_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API_KEY not configured")
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
