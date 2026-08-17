"""Technical indicators computed over OHLCV history.

All functions return NaN-padded Series aligned to input length, so callers can
index them directly against the original records.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(values: pd.Series, window: int) -> pd.Series:
    return values.rolling(window).mean()


def ema(values: pd.Series, window: int) -> pd.Series:
    return values.ewm(span=window, adjust=False).mean()


def rsi(values: pd.Series, period: int = 14) -> pd.Series:
    delta = values.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(values: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(values, fast) - ema(values, slow)
    signal_line = line.ewm(span=signal, adjust=False).mean()
    return line, signal_line, line - signal_line


def bollinger(values: pd.Series, window: int = 20, num_std: int = 2):
    mid = values.rolling(window).mean()
    std = values.rolling(window).std()
    return mid + num_std * std, mid, mid - num_std * std


def _to_list(s: pd.Series) -> list:
    return [None if pd.isna(v) else round(float(v), 4) for v in s]


def _round(v) -> float | None:
    return None if pd.isna(v) else round(float(v), 4)


def compute_all(records: list[dict]) -> dict:
    """Compute all indicator series and a latest-value readout.

    Args:
        records: List of OHLCV dicts with at least a "close" key.

    Returns:
        Dict with indicator series (lists of float|None, same length as
        `records`) and a "readout" dict of latest scalar values.
    """
    closes = pd.Series([r["close"] for r in records], dtype=float)
    ma20 = sma(closes, 20)
    ma50 = sma(closes, 50)
    r14 = rsi(closes, 14)
    macd_line, signal_line, hist = macd(closes)
    bb_upper, bb_mid, bb_lower = bollinger(closes)

    return {
        "sma20": _to_list(ma20),
        "sma50": _to_list(ma50),
        "bollingerUpper": _to_list(bb_upper),
        "bollingerMid": _to_list(bb_mid),
        "bollingerLower": _to_list(bb_lower),
        "readout": {
            "RSI(14)": _round(r14.iloc[-1]),
            "MACD": _round(macd_line.iloc[-1]),
            "MACD Signal": _round(signal_line.iloc[-1]),
            "MACD Hist": _round(hist.iloc[-1]),
            "SMA(20)": _round(ma20.iloc[-1]),
            "SMA(50)": _round(ma50.iloc[-1]),
        },
    }
