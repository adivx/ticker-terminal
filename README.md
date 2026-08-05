# Ticker Terminal

A Bloomberg-style financial terminal — web app. Type function codes into the
command bar and get quotes, price graphs, fundamentals, news, comparables,
world indices and movers for **US and Indian** markets. No API keys required
(all free data sources).

```
┌─ AAPL US Equity ─────────────────────────────────────────────┐
│  Apple Inc · NASDAQ                                          │
│  196.10  +1.55 (+0.79%)   Mkt cap 3.02T · P/E 34.2           │
│  Open 195.4  High 197.1  Low 194.8  Prev 194.55  Vol 48.1M   │
│  [  candlestick chart  ]                                     │
│ ⇥ AAPL US Equity GP <GO>                          [ GO ]     │
└──────────────────────────────────────────────────────────────┘
```

## Quickstart

```bash
# 1. Backend (port 8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Frontend (port 5173) — in another terminal
cd frontend
npm install
npm run dev

# 3. Open http://localhost:5173
```

## Command syntax

`SYMBOL [COUNTRY] ASSET [FUNCTION] <GO>`

| Function | Screen | Example |
|----------|--------|---------|
| `DES` | Quote / description | `AAPL US Equity <GO>` |
| `GP` | Price graph (chart) | `MSFT US Equity GP <GO>` |
| `FA` | Financial analysis | `RELIANCE IN Equity FA <GO>` |
| `CN` | Related news | `NVDA US Equity CN <GO>` |
| `CRPR` | Comparable analysis | `JPM US Equity CRPR <GO>` |
| `WEI` | World equity indices | `WEI <GO>` |
| `TOP` | Top movers | `TOP <GO>` |
| `HELP` | Command reference | `HELP <GO>` |

**Country / asset classes:** `US Equity` (US stocks), `IN Equity` (NSE),
`BSE Equity` (BSE), `Index` (NIFTY, SENSEX, SPX, DOW, NASDAQ…), `Curncy`
(FX, e.g. `USDJPY Curncy`). The default function is `DES`.

## Architecture

```
ticker-terminal/
├── backend/                  FastAPI + yfinance + sqlite
│   ├── app/
│   │   ├── main.py           routes
│   │   ├── parser.py         Bloomberg command grammar
│   │   ├── dispatch.py       command -> screen payload (shared)
│   │   ├── ai/               local AI ask bar (Ollama, keyless)
│   │   │   ├── agent.py      NL -> command -> narrate loop
│   │   │   ├── llm.py        swappable provider + auto-detection
│   │   │   └── digest.py     screen summary fed to the model
│   │   ├── analytics/        indicators (SMA/EMA/RSI/MACD/Bollinger)
│   │   └── data/
│   │       ├── provider.py   caching + concurrency orchestration
│   │       ├── cache.py      TTL cache + watchlist store (sqlite)
│   │       ├── quote.py      yfinance fast_info/info
│   │       ├── history.py    OHLCV fetching
│   │       ├── fundamentals.py
│   │       ├── news.py       Google News RSS (keyless)
│   │       └── curated.py    index / movers / peers universes
│   └── tests/                parser + AI unit tests
├── frontend/                 Vite + React + lightweight-charts
│   └── src/
│       ├── components/       command bar, quote, chart, news, …
│       ├── lib/              api client, formatters
│       └── terminal.css      the CRT theme
└── data/                     sqlite cache (gitignored)
```

## Data sources & limits

- **Quotes / history / fundamentals:** Yahoo Finance (`yfinance`).
  Free, delayed (≈15 min). Indian names via the `.NS` / `.BO` suffixes.
- **News:** Google News RSS. Keyless.
- Everything is cached in `data/terminal.db` (30 s for quotes, up to 1 h for
  history) so you won't hammer the upstream APIs.

## AI ask bar (local, free)

Flip the command bar to `ASK` and type plain English — *"show me Apple's chart
and why it moved"*. A **local** LLM translates it into a Bloomberg command, the
terminal runs it through the same path as `/api/function`, and the model
explains the move from the real price data + headlines.

- **No API keys, works offline.** The model runs through
  [Ollama](https://ollama.com). The terminal auto-detects Ollama and picks a
  tool-calling model (`qwen3` preferred; override with `OLLAMA_MODEL`).
- **Setup:**
  ```bash
  brew install ollama      # or from https://ollama.com
  ollama pull qwen3:4b
  ./run.sh
  ```
- **Graceful degradation:** if Ollama isn't running (or no model is pulled),
  the ASK toggle is disabled and `/api/ask` returns a clear message — the
  classic Bloomberg command line always works.

## Roadmap ideas

- [ ] Live tick via a websocket polling loop (auto-refresh quotes)
- [ ] `CRUNCH`-style sector screener, earnings calendar, option chains
- [ ] Terminal look-alike keyboarding (function-key shortcuts, typeahead)
- [ ] Docker Compose for one-command startup
- [ ] Backtest a strategy on `GP` history and plot it on the chart
