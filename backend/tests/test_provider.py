"""Tests for the data-provider orchestration layer (caching + screens).

Hermetic: network modules are monkeypatched, so nothing touches Yahoo or
Google News.
"""
import pytest

import app.data.provider as prov_mod
from app.data.cache import TTLCache
from app.data.curated import MOVERS_UNIVERSE
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


def test_movers_no_double_count_when_quotes_short(monkeypatch, provider):
    # With fewer than 12 valid quotes, gainers[:6] and losers[-6:] overlap, so
    # the same symbol previously appeared on both sides of the screen.
    ok = MOVERS_UNIVERSE[:8]
    pcts = [-3.0, 3.0, 2.5, -2.0, 1.8, -1.5, 0.9, -0.4]

    def fake_quote(sym):
        if sym not in ok:
            raise ValueError("no data")
        return {"symbol": sym, "last": 100.0, "changePercent": pcts[ok.index(sym)]}

    monkeypatch.setattr(prov_mod.quote_mod, "quote_light", fake_quote)
    data = provider.movers()
    gainers = {q["symbol"] for q in data["topGainers"]}
    losers = {q["symbol"] for q in data["topLosers"]}
    assert gainers.isdisjoint(losers)
    assert len(data["topGainers"]) == 6
    assert len(data["topLosers"]) == 2
