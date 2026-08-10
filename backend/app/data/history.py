"""Historical OHLCV fetching from Yahoo Finance."""
from __future__ import annotations

import pandas as pd
import yfinance as yf

# range key -> (yfinance period, yfinance interval)
RANGES = {
    "1d": ("5d", "1m"),
    "5d": ("5d", "15m"),
    "1m": ("1mo", "1d"),
    "6m": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "5y": ("5y", "1wk"),
}


def history(symbol: str, range_key: str = "1y") -> list[dict]:
    """Returns ascending OHLCV records keyed for lightweight-charts:
    time = unix seconds (UTC), plus open/high/low/close/volume.
    """
    period, interval = RANGES.get(range_key, RANGES["1y"])
    try:
        df = yf.Ticker(symbol).history(
            period=period, interval=interval, auto_adjust=False
        )
    except Exception as exc:
        raise ValueError(f"history failed for {symbol}: {exc}") from exc
    if df is None or df.empty:
        raise ValueError(f"no history for {symbol}")
    df = df.reset_index()
    records = []
    for _, row in df.iterrows():
        col = "Datetime" if "Datetime" in df.columns else "Date"
        ts = pd.Timestamp(row[col])
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC").tz_localize(None)
        records.append({
            "time": int(ts.timestamp()),
            "open": round(float(row["Open"]), 4),
            "high": round(float(row["High"]), 4),
            "low": round(float(row["Low"]), 4),
            "close": round(float(row["Close"]), 4),
            "volume": int(row["Volume"]),
        })
    return records
