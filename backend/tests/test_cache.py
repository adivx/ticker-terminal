"""Tests for the SQLite-backed TTL cache + watchlist store.

Hermetic: each test gets a fresh tmp db file.
"""
from app.data.cache import DEFAULT_WATCHLIST, TTLCache


def _cache(tmp_path):
    return TTLCache(str(tmp_path / "cache.db"))


def test_set_get_roundtrip(tmp_path):
    c = _cache(tmp_path)
    assert c.get("nope") is None
    c.set("key", {"a": 1, "b": [2, 3]}, ttl_seconds=60)
    assert c.get("key") == {"a": 1, "b": [2, 3]}


def test_set_overwrites_same_key(tmp_path):
    c = _cache(tmp_path)
    c.set("k", 1, 60)
    c.set("k", 2, 60)
    assert c.get("k") == 2


def test_delete_removes_key(tmp_path):
    c = _cache(tmp_path)
    c.set("k", 1, 60)
    assert c.delete("k") is None
    assert c.get("k") is None


def test_expired_entry_returned_as_miss(tmp_path):
    c = _cache(tmp_path)
    # ttl=-1: expires_at is already in the past, so get() must treat it as a miss.
    c.set("k", "stale", ttl_seconds=-1)
    assert c.get("k") is None


def test_watchlist_seeded_with_defaults(tmp_path):
    c = _cache(tmp_path)
    assert c.list_watchlist() == DEFAULT_WATCHLIST


def test_watchlist_add_remove(tmp_path):
    c = _cache(tmp_path)
    assert c.add_watchlist("TSLA") is True
    assert c.add_watchlist("TSLA") is False  # already present
    assert "TSLA" in c.list_watchlist()
    assert c.remove_watchlist("TSLA") is True
    assert c.remove_watchlist("TSLA") is False
    assert "TSLA" not in c.list_watchlist()
