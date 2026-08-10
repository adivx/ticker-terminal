"""FastAPI application exposing the terminal's command surface."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import ai
from .data.provider import get_provider
from .dispatch import dispatch
from .parser import CommandError, parse

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = os.environ.get("TERMINAL_DB", str(REPO_ROOT / "data" / "terminal.db"))

app = FastAPI(title="Ticker Terminal", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = get_provider(DB_PATH)


# --- routes ---------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"ok": True, "db": DB_PATH}


@app.get("/api/parse")
def api_parse(cmd: str = Query(..., description="Raw command line")):
    try:
        return parse(cmd).__dict__
    except CommandError as exc:
        raise HTTPException(400, str(exc))


class WatchAdd(BaseModel):
    symbol: str


@app.get("/api/watchlist")
def get_watchlist():
    return {"symbols": provider.cache.list_watchlist()}


@app.post("/api/watchlist")
def add_watchlist(body: WatchAdd):
    symbol = body.symbol.strip().upper()
    if not symbol:
        raise HTTPException(400, "symbol required")
    provider.cache.add_watchlist(symbol)
    return {"symbols": provider.cache.list_watchlist()}


@app.delete("/api/watchlist/{symbol}")
def remove_watchlist(symbol: str):
    provider.cache.remove_watchlist(symbol)
    return {"symbols": provider.cache.list_watchlist()}


@app.get("/api/watchlist/quotes")
def watchlist_quotes():
    quotes = []
    for s in provider.cache.list_watchlist():
        try:
            quotes.append(provider.quote_light(s))
        except Exception:
            quotes.append({"symbol": s, "error": True})
    return {"quotes": quotes}


@app.get("/api/indices")
def api_indices():
    return {"indices": provider.indices()}


@app.get("/api/movers")
def api_movers():
    return provider.movers()


@app.get("/api/news")
def api_news(q: str = Query("stock market"), limit: int = Query(15, ge=1, le=40)):
    return {"query": q, "items": provider.news(q, limit)}


@app.get("/api/function")
def run_function(
    cmd: str = Query(..., description="Raw command line, e.g. 'AAPL US Equity GP <GO>'"),
    range: str = Query("1y", description="Chart range: 1d, 5d, 1m, 6m, 1y, 5y"),
):
    try:
        parsed = parse(cmd)
    except CommandError as exc:
        raise HTTPException(400, str(exc))
    try:
        screen = dispatch(provider, parsed, range)
    except CommandError as exc:
        # Unhandled functions (e.g. `MON <GO>`) are user errors, not server
        # faults — return 400 like parse failures, never a 500 traceback.
        raise HTTPException(400, str(exc))
    except ValueError as exc:
        raise HTTPException(502, str(exc))
    except Exception as exc:  # defensive: never leak stack traces
        raise HTTPException(500, f"internal error: {exc}")
    return {"parsed": parsed.__dict__, "screen": screen}


# --- AI ask -----------------------------------------------------------------


class AskBody(BaseModel):
    query: str


@app.get("/api/ai")
def ai_status():
    return ai.status()


@app.post("/api/ask")
def api_ask(body: AskBody):
    q = body.query.strip()
    if not q:
        raise HTTPException(400, "ask query required")
    try:
        return ai.ask(q, provider)
    except ai.AIUnavailable as exc:
        raise HTTPException(501, str(exc))
    except Exception as exc:  # defensive: never leak stack traces
        raise HTTPException(500, f"internal error: {exc}")
