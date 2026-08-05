"""Screen digest: compact, model-readable summary of a dispatched screen.

The digest is what we feed back to the LLM after it runs a terminal command,
so its narration is grounded in real price action + news rather than guesses.
Kept provider-agnostic (any LLM can consume it).
"""
from __future__ import annotations

import datetime


def _fmt(v, nd: int = 2) -> str:
    if v is None:
        return "n/a"
    try:
        return f"{v:,.{nd}f}"
    except (TypeError, ValueError):
        return str(v)


def _fmt_ts(v) -> str:
    """History bars carry epoch seconds; render as YYYY-MM-DD."""
    if v is None:
        return "n/a"
    try:
        return datetime.datetime.fromtimestamp(int(v)).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError, OverflowError):
        return str(v)


def _summarize_quote(q: dict) -> str:
    if not q:
        return "n/a"
    sym = q.get("symbol") or "?"
    line = sym
    if q.get("name"):
        line += f" — {q['name']}"
    last, chg, pct = q.get("last"), q.get("change"), q.get("changePercent")
    if last is not None:
        line += f" @ {_fmt(last)}"
        if chg is not None:
            sign = "+" if chg >= 0 else ""
            line += f" ({sign}{_fmt(chg)} / {sign}{_fmt(pct)}%)"
    for key, lab in (
        ("open", "Open"),
        ("high", "High"),
        ("low", "Low"),
        ("prevClose", "Prev Close"),
        ("volume", "Volume"),
    ):
        if q.get(key) is not None:
            line += f" | {lab} {_fmt(q[key])}"
    return line


def screen_digest(data_provider, p, screen: dict) -> str:
    t = screen.get("type")
    lines = [f"Command: {p.raw}", f"Screen: {t}"]
    if t == "quote":
        lines.append(_summarize_quote(screen["quote"]))
    elif t == "chart":
        lines.append(_summarize_quote(screen["quote"]))
        readout = (screen.get("indicators") or {}).get("readout") or {}
        bits = [f"{k} {_fmt(v)}" for k, v in readout.items() if v is not None]
        if bits:
            lines.append("Indicators: " + ", ".join(bits))
        hist = screen.get("history") or []
        if hist:
            lines.append(
                f"Range {screen.get('range')}: {len(hist)} bars, "
                f"{_fmt_ts(hist[0].get('time'))} -> {_fmt_ts(hist[-1].get('time'))}"
            )
    elif t == "fundamentals":
        f = screen.get("fundamentals") or {}
        if f.get("name"):
            lines.append(f["name"])
        for item in f.get("fields", [])[:12]:
            lines.append(f"{item['label']}: {item['value']}")
    elif t == "news":
        for it in (screen.get("items") or [])[:8]:
            lines.append(f"- {it.get('title')}")
    elif t == "peers":
        lines.append(_summarize_quote(screen["quote"]))
        for peer in (screen.get("peers") or [])[:6]:
            lines.append(f"- {_summarize_quote(peer)}")
    elif t == "indices":
        for row in (screen.get("indices") or [])[:12]:
            lines.append(_summarize_quote(row.get("quote") or {}))
    elif t == "movers":
        for grp, lab in (("topGainers", "Top gainers"), ("topLosers", "Top losers")):
            lines.append(f"{lab}:")
            for q in (screen.get(grp) or [])[:5]:
                lines.append(f"- {_summarize_quote(q)}")
    # Always add headlines so the model can explain the WHY.
    if t != "help" and p.symbol:
        q = f"{p.symbol} index" if p.asset == "Index" else f"{p.symbol} stock"
        heads = data_provider.news(q, 6)
        if heads:
            lines.append("Recent headlines:")
            for it in heads:
                lines.append(f"- {it.get('title')}")
    return "\n".join(lines)
