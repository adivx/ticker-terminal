"""Quote fetching from Yahoo Finance via yfinance.

quote_light  -> fast_info only (bulk / strips). One network call.
quote_full   -> fast_info + info dict (adds name, sector, valuation).
"""
from __future__ import annotations

import yfinance as yf


def _fast_info(symbol: str):
    try:
        return yf.Ticker(symbol).fast_info
    except Exception:
        return None


def _info(symbol: str):
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


def _price_fallback(ticker):
    """Off-hours fallback: derive last/prev close from recent daily bars."""
    try:
        df = ticker.history(period="5d", interval="1d", auto_adjust=False)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    closes = df["Close"].dropna()
    if len(closes) == 0:
        return None
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    return last, prev


def quote_light(symbol: str) -> dict:
    """Fast quote using only ticker.fast_info."""
    fi = _fast_info(symbol)
    if fi is None:
        raise ValueError(f"no data for {symbol}")
    last = fi.get("last_price")
    prev = fi.get("previous_close") or fi.get("regular_market_previous_close")
    if last is None:
        fallback = _price_fallback(yf.Ticker(symbol))
        if fallback:
            last, prev = fallback
    change = change_pct = None
    if last is not None and prev:
        change = last - prev
        change_pct = (change / prev) * 100.0
    return {
        "symbol": symbol,
        "last": last,
        "prevClose": prev,
        "open": fi.get("open"),
        "high": fi.get("day_high"),
        "low": fi.get("day_low"),
        "volume": fi.get("last_volume"),
        "marketCap": fi.get("market_cap"),
        "currency": fi.get("currency"),
        "change": change,
        "changePercent": change_pct,
        "yearHigh": fi.get("year_high"),
        "yearLow": fi.get("year_low"),
    }


def quote_full(symbol: str) -> dict:
    """Quote plus valuation/identity fields from ticker.info."""
    info = _info(symbol)
    q = quote_light(symbol)
    q.update({
        "name": info.get("shortName") or info.get("longName") or symbol,
        "exchange": info.get("exchange"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "trailingPE": info.get("trailingPE"),
        "forwardPE": info.get("forwardPE"),
        "priceToBook": info.get("priceToBook"),
        "dividendYield": info.get("trailingAnnualDividendYield"),
        "beta": info.get("beta"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh") or q.get("yearHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow") or q.get("yearLow"),
        "marketCap": info.get("marketCap") or q.get("marketCap"),
        "avgVolume": info.get("averageVolume"),
    })
    return q
