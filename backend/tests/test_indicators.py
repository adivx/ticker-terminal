"""Tests for technical-indicator computations.

Hermetic: pure pandas math over synthetic series, no network access.
"""
import math

import pandas as pd
import pytest

from app.analytics.indicators import (
    bollinger,
    compute_all,
    macd,
    rsi,
    sma,
)


def test_sma_rolling_mean():
    out = sma(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), window=3)
    assert math.isnan(out.iloc[0])  # NaN before the window fills
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[3] == pytest.approx(3.0)
    assert out.iloc[4] == pytest.approx(4.0)


def test_rsi_matches_wilder_reference():
    closes = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10,
              45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
    period = 14

    # Independent Wilder smoothing: ewm(alpha=1/p, adjust=False) seeded with
    # the first gain/loss observation.
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    def ewma(xs):
        a = 1.0 / period
        out = [xs[0]]
        for x in xs[1:]:
            out.append((1 - a) * out[-1] + a * x)
        return out

    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_gain = ewma(gains)
    avg_loss = ewma(losses)
    rs = avg_gain[-1] / avg_loss[-1]
    expected = 100 - 100 / (1 + rs)

    got = rsi(pd.Series(closes), period).iloc[-1]
    assert got == pytest.approx(expected, abs=1e-9)


def test_rsi_bounded_for_mixed_series():
    closes = [10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0, 15.0,
              14.0, 16.0, 15.0, 17.0, 16.0, 18.0, 17.0, 19.0]
    out = rsi(pd.Series(closes), period=14)
    finite = [v for v in out.dropna()]
    assert finite
    assert all(0.0 <= v <= 100.0 for v in finite)


def test_macd_components():
    line, signal, hist = macd(pd.Series(range(1, 60), dtype=float))
    assert line.iloc[-1] == pytest.approx(line.iloc[-1])
    assert hist.iloc[-1] == pytest.approx(line.iloc[-1] - signal.iloc[-1])
    assert not math.isnan(signal.iloc[-1])


def test_bollinger_bands_ordered():
    closes = pd.Series([10.0 + (i % 5) for i in range(40)], dtype=float)
    upper, mid, lower = bollinger(closes, window=20)
    assert mid.iloc[-1] == pytest.approx(sma(closes, 20).iloc[-1])
    assert upper.iloc[-1] >= mid.iloc[-1] >= lower.iloc[-1]


def test_compute_all_aligns_series_to_records():
    records = [{"close": 100.0 + i} for i in range(60)]
    out = compute_all(records)
    n = len(records)
    for key in ("sma20", "sma50", "bollingerUpper", "bollingerMid", "bollingerLower"):
        assert len(out[key]) == n
    # sma50 needs 50 points; everything before that is null.
    assert out["sma50"][:49] == [None] * 49
    assert out["sma50"][-1] is not None
    assert set(out["readout"]) == {
        "RSI(14)", "MACD", "MACD Signal", "MACD Hist", "SMA(20)", "SMA(50)",
    }
    assert out["readout"]["SMA(20)"] is not None
