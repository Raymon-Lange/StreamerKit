from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

_log_level = getattr(logging, os.getenv("LOG_LEVEL", "info").upper(), logging.INFO)

_logger = logging.getLogger("baseball.feed")
if not _logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(_log_level)
    _logger.propagate = False


class FeedLogContext:
    __slots__ = ("outcome", "error_type", "error_message")

    def __init__(self) -> None:
        self.outcome: str = "success"
        self.error_type: str | None = None
        self.error_message: str | None = None

    def mark_cache_fallback(self) -> None:
        self.outcome = "cache-fallback"

    def mark_error(self, exc: Exception) -> None:
        self.outcome = "error"
        self.error_type = type(exc).__name__
        self.error_message = str(exc)


def _triggered_by() -> str:
    try:
        return Path(sys.argv[0]).name if sys.argv else "unknown"
    except Exception:
        return "unknown"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


@contextmanager
def log_feed_fetch(collector: str, operation: str) -> Generator[FeedLogContext, None, None]:
    ctx = FeedLogContext()
    triggered = _triggered_by()
    start = time.monotonic()
    try:
        yield ctx
    except Exception as exc:
        ctx.outcome = "error"
        ctx.error_type = type(exc).__name__
        ctx.error_message = str(exc)
        raise
    finally:
        try:
            duration = time.monotonic() - start
            if ctx.error_type:
                line = (
                    f"[FEED] {_now_utc()}Z | {triggered} | {collector} | {operation}"
                    f" | {ctx.outcome} | {duration:.2f}s | {ctx.error_type}: {ctx.error_message}"
                )
            else:
                line = (
                    f"[FEED] {_now_utc()}Z | {triggered} | {collector} | {operation}"
                    f" | {ctx.outcome} | {duration:.2f}s"
                )
            _logger.info(line)
        except Exception:
            pass
        if ctx.error_type:
            try:
                from utils.cache_store import store as _cache  # noqa: PLC0415
                _cache.set(
                    "feed_failures",
                    f"{collector}|{operation}",
                    {
                        "timestamp": _now_utc() + "Z",
                        "collector": collector,
                        "operation": operation,
                        "error_type": ctx.error_type,
                        "error_message": ctx.error_message,
                        "triggered_by": triggered,
                    },
                )
            except Exception:
                pass


@contextmanager
def log_script_run(script_name: str) -> Generator[None, None, None]:
    start = time.monotonic()
    try:
        yield
    except Exception as exc:
        try:
            duration = time.monotonic() - start
            line = (
                f"[SCRIPT] {_now_utc()}Z | {script_name} | error"
                f" | {duration:.2f}s | {type(exc).__name__}"
            )
            _logger.info(line)
        except Exception:
            pass
        raise
    else:
        try:
            duration = time.monotonic() - start
            line = f"[SCRIPT] {_now_utc()}Z | {script_name} | completed | {duration:.2f}s"
            _logger.info(line)
        except Exception:
            pass
