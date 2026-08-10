"""Fundamental fields pulled from ticker.info."""
from __future__ import annotations

import yfinance as yf

# (info key, display label, kind) where kind drives frontend formatting.
# kind: currency | percent | number | text
FUND_FIELDS = [
    ("marketCap", "Market Cap", "currency"),
    ("trailingPE", "P/E (TTM)", "number"),
    ("forwardPE", "P/E (Forward)", "number"),
    ("priceToBook", "Price / Book", "number"),
    ("trailingAnnualDividendYield", "Dividend Yield", "percent"),
    ("returnOnEquity", "Return on Equity", "percent"),
    ("profitMargins", "Profit Margin", "percent"),
    ("grossMargins", "Gross Margin", "percent"),
    ("operatingMargins", "Operating Margin", "percent"),
    ("revenueGrowth", "Revenue Growth (YoY)", "percent"),
    ("earningsGrowth", "Earnings Growth (YoY)", "percent"),
    ("debtToEquity", "Debt / Equity", "number"),
    ("currentRatio", "Current Ratio", "number"),
    ("quickRatio", "Quick Ratio", "number"),
    ("beta", "Beta (5Y)", "number"),
    ("targetMeanPrice", "Analyst Target", "currency"),
    ("totalRevenue", "Total Revenue", "currency"),
    ("totalDebt", "Total Debt", "currency"),
    ("totalCash", "Total Cash", "currency"),
    ("netIncomeToCommon", "Net Income", "currency"),
    ("freeCashflow", "Free Cash Flow", "currency"),
    ("sharesOutstanding", "Shares Outstanding", "currency"),
    ("floatShares", "Float Shares", "currency"),
    ("bookValue", "Book Value", "currency"),
    ("sector", "Sector", "text"),
    ("industry", "Industry", "text"),
    ("website", "Website", "text"),
]


def fundamentals(symbol: str) -> dict:
    info = {}
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        pass
    fields = []
    for key, label, kind in FUND_FIELDS:
        if key in info and info[key] is not None:
            fields.append({"key": key, "label": label, "kind": kind, "value": info[key]})
    return {
        "symbol": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "fields": fields,
        "description": info.get("longBusinessSummary") or "",
    }
