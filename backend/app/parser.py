"""Bloomberg-style command parser.

Turns terminal syntax into a resolved request:

    AAPL US Equity <GO>          -> quote for AAPL (US)
    MSFT US Equity GP <GO>       -> price graph for MSFT
    NIFTY Index GP <GO>          -> index price graph (^NSEI)
    RELIANCE IN Equity FA <GO>   -> fundamentals for RELIANCE.NS
    TOP / WEI / HELP <GO>        -> special screens

Grammar:  SYMBOL [COUNTRY] ASSET [FUNCTION] <GO>
"""
from __future__ import annotations

import re
from dataclasses import dataclass

ASSET_CLASSES = {"EQUITY", "INDEX", "CURNCY", "GOVT", "COMDTY", "ETF"}
SPECIALS = {"TOP", "WEI", "HELP", "MON"}

SPECIAL_LABELS = {
    "TOP": "Top Movers",
    "WEI": "World Equity Indices",
    "HELP": "Command Reference",
    "MON": "Market Monitor",
}

FUNCTIONS = {
    "DES": "Description / Quote",
    "GP": "Price Graph",
    "FA": "Financial Analysis",
    "CN": "Related News",
    "CRPR": "Comparable Analysis",
    "WEI": "World Equity Indices",
    "TOP": "Top Movers",
    "HELP": "Command Reference",
}

# Country -> Yahoo suffix
COUNTRY_SUFFIX = {
    "US": "",
    "IN": ".NS",
    "NS": ".NS",
    "NSE": ".NS",
    "BSE": ".BO",
    "GB": ".L",
    "UK": ".L",
    "JP": ".T",
    "DE": ".DE",
}

# Recognised index names -> Yahoo symbol
# Source: Yahoo Finance convention (^ prefix for indices)
INDEX_MAP = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
    "SPX": "^GSPC",
    "S&P": "^GSPC",
    "DOW": "^DJI",
    "DJIA": "^DJI",
    "NASDAQ": "^IXIC",
    "NDX": "^NDX",
    "NIKKEI": "^N225",
    "N225": "^N225",
    "FTSE": "^FTSE",
    "DAX": "^GDAXI",
    "CAC": "^FCHI",
    "HSI": "^HSI",
}


class CommandError(Exception):
    pass


@dataclass
class ParsedCommand:
    raw: str
    function: str
    label: str
    symbol: str = ""
    country: str = ""
    asset: str = ""
    yahoo: str = ""
    special: bool = False


def parse(raw: str) -> ParsedCommand:
    if not raw or not raw.strip():
        raise CommandError("Empty command. Try `AAPL US Equity <GO>` or `HELP <GO>`.")

    text = re.sub(r"<GO>", "", raw, flags=re.IGNORECASE).strip()
    tokens = text.split()
    uppered = [t.upper() for t in tokens]

    # Bare special commands: TOP / WEI / HELP / MON
    if len(tokens) == 1 and uppered[0] in SPECIALS:
        fn = uppered[0]
        return ParsedCommand(raw=raw, function=fn, label=SPECIAL_LABELS[fn], special=True)

    # Find the asset-class token ("Equity", "Index", ...), case-insensitively
    asset_idx = next((i for i, t in enumerate(uppered) if t in ASSET_CLASSES), None)
    if asset_idx is None:
        # Bare symbol, default US Equity.  e.g. "AAPL" or "AAPL GP"
        symbol = tokens[0]
        fn = uppered[1] if len(tokens) > 1 else None
        return _build(raw, symbol, "US", "Equity", fn)

    symbol = tokens[0]
    country = tokens[asset_idx - 1].upper() if asset_idx >= 2 else None
    if country in ASSET_CLASSES or country in SPECIALS:
        country = None
    asset = tokens[asset_idx]
    fn_token = tokens[asset_idx + 1] if asset_idx + 1 < len(tokens) else None
    fn = fn_token.upper() if fn_token else None
    return _build(raw, symbol, country, asset, fn)


def _build(raw: str, symbol: str, country: str | None, asset: str, fn: str | None) -> ParsedCommand:
    fn = fn or "DES"
    if fn not in FUNCTIONS:
        raise CommandError(
            f"Unknown function code `{fn}`. Valid: DES, GP, FA, CN, CRPR, WEI, TOP, HELP."
        )
    yahoo = _resolve_yahoo(symbol, country, asset)
    return ParsedCommand(
        raw=raw,
        function=fn,
        label=FUNCTIONS[fn],
        symbol=symbol.upper(),
        country=country,
        asset=asset,
        yahoo=yahoo,
    )


def _resolve_yahoo(symbol: str, country: str | None, asset: str) -> str:
    s = symbol.upper()
    if asset == "Index":
        return INDEX_MAP.get(s, "^" + s)
    if asset == "Curncy":
        return s + "=X"
    if asset == "Govt":
        return "^" + s
    return s + COUNTRY_SUFFIX.get(country or "US", "")
