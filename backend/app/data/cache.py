"""SQLite-backed TTL cache + persistent watchlist store.

One small sqlite file backs both the key/value cache (with per-key
expiry) and the watchlist table. Thread-safe via a single lock.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS watchlist (
    symbol   TEXT PRIMARY KEY,
    added_at REAL NOT NULL
);
"""

DEFAULT_WATCHLIST = ["AAPL", "MSFT", "NVDA", "RELIANCE.NS", "TCS.NS", "^NSEI"]


class TTLCache:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._seed_watchlist()

    # --- key/value cache ------------------------------------------------
    def get(self, key: str):
        with self._lock:
            row = self._conn.execute(
                "SELECT value, expires_at FROM kv WHERE key = ?", (key,)
            ).fetchone()
        if not row:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            self.delete(key)
            return None
        return json.loads(value)

    def set(self, key: str, value, ttl_seconds: int):
        with self._lock:
            self._conn.execute(
                "INSERT INTO kv (key, value, expires_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
                "expires_at = excluded.expires_at",
                (key, json.dumps(value), time.time() + ttl_seconds),
            )
            self._conn.commit()

    def delete(self, key: str):
        with self._lock:
            self._conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            self._conn.commit()

    # --- watchlist -------------------------------------------------------
    def _seed_watchlist(self):
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()
            if row[0] == 0:
                now = time.time()
                self._conn.executemany(
                    "INSERT INTO watchlist (symbol, added_at) VALUES (?, ?)",
                    [(s, now) for s in DEFAULT_WATCHLIST],
                )
                self._conn.commit()

    def list_watchlist(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT symbol FROM watchlist ORDER BY added_at"
            ).fetchall()
        return [r[0] for r in rows]

    def add_watchlist(self, symbol: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO watchlist (symbol, added_at) VALUES (?, ?)",
                (symbol, time.time()),
            )
            self._conn.commit()
            return cur.rowcount > 0

    def remove_watchlist(self, symbol: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM watchlist WHERE symbol = ?", (symbol,)
            )
            self._conn.commit()
            return cur.rowcount > 0
