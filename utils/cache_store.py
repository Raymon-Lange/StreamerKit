from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).resolve().parents[1] / ".cache" / "cache.db"


class CacheStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        namespace   TEXT NOT NULL,
                        key         TEXT NOT NULL,
                        value       TEXT NOT NULL,
                        cached_at   REAL NOT NULL,
                        ttl_seconds REAL,
                        PRIMARY KEY (namespace, key)
                    )
                """)
                conn.commit()
            finally:
                conn.close()

    def get(self, namespace: str, key: str, ttl_seconds: float | None = None) -> Any | None:
        """Return deserialized value if the entry exists and is within TTL.
        ttl_seconds=None means no TTL is enforced — any existing value is returned."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value, cached_at FROM cache WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        value_json, cached_at = row
        if ttl_seconds is not None and (time.time() - cached_at) > ttl_seconds:
            return None
        try:
            return json.loads(value_json)
        except Exception:
            return None

    def get_stale(self, namespace: str, key: str) -> Any | None:
        """Return deserialized value regardless of TTL. None only if the key is absent."""
        return self.get(namespace, key, ttl_seconds=None)

    def set(self, namespace: str, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """Serialize value to JSON and upsert. ttl_seconds=None means permanent."""
        value_json = json.dumps(value, ensure_ascii=True, default=str)
        cached_at = time.time()
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """INSERT INTO cache (namespace, key, value, cached_at, ttl_seconds)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(namespace, key) DO UPDATE SET
                           value       = excluded.value,
                           cached_at   = excluded.cached_at,
                           ttl_seconds = excluded.ttl_seconds""",
                    (namespace, key, value_json, cached_at, ttl_seconds),
                )
                conn.commit()
            finally:
                conn.close()

    def get_latest_by_prefix(self, namespace: str, prefix: str) -> Any | None:
        """Return the most recently cached entry whose key starts with prefix."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value FROM cache WHERE namespace = ? AND key LIKE ? ORDER BY cached_at DESC LIMIT 1",
                (namespace, f"{prefix}%"),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def delete(self, namespace: str, key: str) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM cache WHERE namespace = ? AND key = ?", (namespace, key))
                conn.commit()
            finally:
                conn.close()

    def prune_expired(self) -> int:
        """Delete all rows past their TTL. Returns count of deleted rows."""
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """DELETE FROM cache
                       WHERE ttl_seconds IS NOT NULL
                         AND (? - cached_at) > ttl_seconds""",
                    (time.time(),),
                )
                conn.commit()
                return cur.rowcount
            finally:
                conn.close()


store = CacheStore(_DB_PATH)
