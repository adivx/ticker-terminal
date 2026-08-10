"""Free news headlines via Google News RSS (no API key required)."""
from __future__ import annotations

from urllib.parse import quote

import feedparser


def fetch_news(query: str, limit: int = 15) -> list[dict]:
    q = quote(query)
    url = (
        "https://news.google.com/rss/search"
        f"?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    )
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    items = []
    for entry in feed.entries[:limit]:
        items.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "source": (entry.source.title if entry.source else ""),
            "published": entry.get("published", ""),
        })
    return items
