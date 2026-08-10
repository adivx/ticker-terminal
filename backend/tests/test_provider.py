"""Tests for the data-provider orchestration layer (caching + screens).

Hermetic: network modules are monkeypatched, so nothing touches Yahoo or
Google News.
"""
import pytest

import app.data.provider as prov_mod
from app.data.cache import TTLCache
from app.data.provider import DataProvider


@pytest.fixture
def provider(tmp_path):
    return DataProvider(TTLCache(str(tmp_path / "test.db")))


def test_news_cache_key_includes_limit(monkeypatch, provider):
    # Fetching the same query at two different limits must not share a cache
    # entry: /api/news?q=X&limit=40 must return 40 items, not the 15 that a
    # previous limit=15 call cached under the same key.
    calls = []
    monkeypatch.setattr(
        prov_mod.news_mod, "fetch_news",
        lambda query, limit: calls.append((query, limit)) or [{"title": "x"}],
    )
    provider.news("aapl", limit=15)
    provider.news("aapl", limit=40)
    provider.news("aapl", limit=15)  # hits the limit=15 cache entry
    assert len(calls) == 2
