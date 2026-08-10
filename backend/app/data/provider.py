"""Orchestrates the data layer: caching + concurrency for the API."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from . import fundamentals as fund_mod
from . import history as hist_mod
from . import news as news_mod
from . import quote as quote_mod
from .cache import TTLCache
from .curated import MOVERS_UNIVERSE, SECTOR_PEERS, WORLD_INDICES


class DataProvider:
    def __init__(self, cache: TTLCache):
        self.cache = cache
        self._pool = ThreadPoolExecutor(max_workers=8)

    # --- single lookups ------------------------------------------------
    def quote_full(self, symbol: str) -> dict:
        key = f"quote_full:{symbol}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        data = quote_mod.quote_full(symbol)
        self.cache.set(key, data, 30)
        return data

    def quote_light(self, symbol: str) -> dict:
        key = f"quote_light:{symbol}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        data = quote_mod.quote_light(symbol)
        self.cache.set(key, data, 30)
        return data

    def history(self, symbol: str, range_key: str = "1y") -> list[dict]:
        key = f"hist:{symbol}:{range_key}"
        ttl = 120 if range_key in ("1d", "5d") else 600
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        data = hist_mod.history(symbol, range_key)
        self.cache.set(key, data, ttl)
        return data

    def fundamentals(self, symbol: str) -> dict:
        key = f"fund:{symbol}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        data = fund_mod.fundamentals(symbol)
        self.cache.set(key, data, 3600)
        return data

    def news(self, query: str, limit: int = 15) -> list[dict]:
        key = f"news:{query.lower()}:{limit}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        data = news_mod.fetch_news(query, limit)
        self.cache.set(key, data, 300)
        return data

    # --- aggregate screens ---------------------------------------------
    def indices(self) -> list[dict]:
        key = "screens:indices"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        futures = {
            self._pool.submit(quote_mod.quote_light, sym): sym
            for sym, *_ in WORLD_INDICES
        }
        rows = []
        for fut, sym in futures.items():
            try:
                rows.append({"symbol": sym, "display": _display(sym), "quote": fut.result()})
            except Exception:
                continue
        self.cache.set(key, rows, 30)
        return rows

    def movers(self) -> dict:
        key = "screens:movers"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        futures = {
            self._pool.submit(quote_mod.quote_light, sym): sym
            for sym in MOVERS_UNIVERSE
        }
        quotes = []
        for fut in futures:
            try:
                q = fut.result()
                if q.get("changePercent") is not None and q.get("last") is not None:
                    quotes.append(q)
            except Exception:
                continue
        quotes.sort(key=lambda q: q["changePercent"], reverse=True)
        gainers = quotes[:6]
        losers = quotes[-6:]
        if len(quotes) < 12:
            # Fewer than a full screen of movers: the top-6 and bottom-6 slices
            # overlap, so the same symbol used to appear on both sides.
            losers = [q for q in losers if q not in gainers]
        data = {"topGainers": gainers, "topLosers": list(reversed(losers))}
        self.cache.set(key, data, 30)
        return data

    def peers(self, sector: str) -> list[dict]:
        tickers = SECTOR_PEERS.get(sector or "", [])[:6]
        if not tickers:
            return []
        futures = [self._pool.submit(self.quote_full, t) for t in tickers]
        rows = []
        for fut in futures:
            try:
                rows.append(fut.result())
            except Exception:
                continue
        return rows


def _display(symbol: str) -> str:
    for sym, display, _region in WORLD_INDICES:
        if sym == symbol:
            return display
    return symbol


def get_provider(db_path: str) -> DataProvider:
    return DataProvider(TTLCache(db_path))
