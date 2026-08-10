"""Curated market universes used by the screener / mover screens."""

# (yahoo symbol, display name, region)
WORLD_INDICES = [
    ("^NSEI", "NIFTY 50", "India"),
    ("^BSESN", "SENSEX", "India"),
    ("^GSPC", "S&P 500", "US"),
    ("^DJI", "Dow Jones", "US"),
    ("^IXIC", "NASDAQ", "US"),
    ("^FTSE", "FTSE 100", "UK"),
    ("^GDAXI", "DAX", "Germany"),
    ("^N225", "Nikkei 225", "Japan"),
    ("^HSI", "Hang Seng", "HK"),
    ("^FCHI", "CAC 40", "France"),
]

# Liquid US + Indian names used for the TOP (movers) screen.
MOVERS_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "GS", "V",
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "BAJFINANCE.NS",
]

# Sector -> comparable peers (CRPR screen). Sectors are the GICS sector
# strings yfinance reports via ticker.info["sector"].
SECTOR_PEERS = {
    "Technology": ["MSFT", "GOOGL", "META", "ORCL", "CRM", "ADBE"],
    "Financial Services": ["JPM", "GS", "BAC", "MS", "WFC"],
    "Financial": ["JPM", "GS", "BAC", "MS", "WFC"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "OXY"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
    "Communication Services": ["GOOGL", "META", "DIS", "T", "VZ"],
    "Healthcare": ["UNH", "JNJ", "PFE", "MRK", "ABBV"],
    "Consumer Defensive": ["PG", "KO", "WMT", "COST", "PEP"],
    "Industrials": ["CAT", "BA", "GE", "HON", "UPS"],
    "Basic Materials": ["LIN", "APD", "FCX", "NEM", "DOW"],
}
