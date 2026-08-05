"""Screen dispatch: a resolved command becomes a panel payload.

Kept separate from main.py so the AI module can run a command through the
exact same path as /api/function without a circular import.
"""
from __future__ import annotations

from .analytics import indicators
from .parser import CommandError

HELP_REF = [
    {"fn": "DES", "label": "Description / Quote", "example": "AAPL US Equity <GO>"},
    {"fn": "GP", "label": "Price Graph", "example": "MSFT US Equity GP <GO>"},
    {"fn": "FA", "label": "Financial Analysis", "example": "RELIANCE IN Equity FA <GO>"},
    {"fn": "CN", "label": "Related News", "example": "NVDA US Equity CN <GO>"},
    {"fn": "CRPR", "label": "Comparable Analysis", "example": "JPM US Equity CRPR <GO>"},
    {"fn": "WEI", "label": "World Equity Indices", "example": "WEI <GO>"},
    {"fn": "TOP", "label": "Top Movers", "example": "TOP <GO>"},
    {"fn": "HELP", "label": "Command Reference", "example": "HELP <GO>"},
]

SYNTAX = "SYMBOL [COUNTRY] ASSET [FUNCTION] <GO>"
NOTE = (
    "US Equity = US stocks · IN Equity = NSE/BSE stocks · "
    "Index = major indices (NIFTY, SENSEX, SPX, DOW, NASDAQ…) · "
    "Curncy = FX pairs. Default function without a code is DES."
)


def dispatch(provider, p, range_key: str = "1y") -> dict:
    """Return the screen payload for a parsed command (mirrors /api/function)."""
    yahoo = p.yahoo
    if p.function == "DES":
        return {"type": "quote", "quote": provider.quote_full(yahoo)}
    if p.function == "GP":
        hist = provider.history(yahoo, range_key)
        ind = indicators.compute_all(hist)
        return {
            "type": "chart",
            "range": range_key,
            "quote": provider.quote_full(yahoo),
            "history": hist,
            "indicators": ind,
        }
    if p.function == "FA":
        return {
            "type": "fundamentals",
            "fundamentals": provider.fundamentals(yahoo),
            "quote": provider.quote_full(yahoo),
        }
    if p.function == "CN":
        query = f"{p.symbol} index" if p.asset == "Index" else f"{p.symbol} stock"
        return {"type": "news", "query": query, "items": provider.news(query)}
    if p.function == "CRPR":
        quote = provider.quote_full(yahoo)
        return {"type": "peers", "quote": quote, "peers": provider.peers(quote.get("sector"))}
    if p.function == "WEI":
        return {"type": "indices", "indices": provider.indices()}
    if p.function == "TOP":
        return {"type": "movers", **provider.movers()}
    if p.function == "HELP":
        return {"type": "help", "reference": HELP_REF, "syntax": SYNTAX, "note": NOTE}
    raise CommandError(f"Unhandled function {p.function}")
