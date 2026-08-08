# HTTP API reference

The FastAPI backend exposes a small JSON API on port 8000. Every route
defaults to `application/json`. Requests with bad commands return a JSON
`{"detail": "..."}` body with the matching HTTP status (400 = bad command,
500 = internal error, 502 = upstream data source failed).

## Health

### `GET /api/health`

Liveness probe. Returns the sqlite cache path.

```json
{ "ok": true, "db": "/path/to/terminal.db" }
```

## Command parsing

### `GET /api/parse?cmd=<COMMAND>`

Parse a command line without running it — useful for validating input or
building a typeahead.

| Query | Type | Meaning |
|---|---|---|
| `cmd` | string | raw command line, e.g. `AAPL US Equity GP <GO>` |

On success returns the parsed structure; on a syntax error returns `400`.

## Function screens

### `GET /api/function?cmd=<COMMAND>&range=<RANGE>`

The main endpoint: parse a Bloomberg-style command and run the matching
screen.

| Query | Type | Default | Meaning |
|---|---|---|---|
| `cmd` | string | — | command line, e.g. `RELIANCE IN Equity FA <GO>` |
| `range` | string | `1y` | chart range: `1d`, `5d`, `1m`, `6m`, `1y`, `5y` |

Returns both the parsed command and the rendered screen payload:

```json
{ "parsed": { "...": "..." }, "screen": { "type": "quote", "...": "..." } }
```

## Watchlist

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/watchlist` | — | `{ "symbols": ["AAPL", "..."] }` |
| `POST` | `/api/watchlist` | `{ "symbol": "AAPL" }` | updated `{ "symbols": [...] }` |
| `DELETE` | `/api/watchlist/{symbol}` | — | updated `{ "symbols": [...] }` |
| `GET` | `/api/watchlist/quotes` | — | `{ "quotes": [{ "symbol", "..." }] }` |

Symbols are upper-cased and persisted in the sqlite cache. A quote that fails
to load is returned as `{ "symbol": "...", "error": true }` so one bad name
doesn't kill the whole list.

## Market universes

### `GET /api/indices`

World equity indices (NIFTY, SENSEX, SPX, DOW, NASDAQ, …).

```json
{ "indices": [{ "symbol": "^NSEI", "name": "...", "price": 24600.5 }] }
```

### `GET /api/movers`

Top movers across the curated universe.

### `GET /api/news?q=<QUERY>&limit=<N>`

Google News RSS search.

| Query | Type | Default | Constraints |
|---|---|---|---|
| `q` | string | `stock market` | — |
| `limit` | integer | `15` | 1–40 |

## AI ask bar (local, optional)

### `GET /api/ai`

Detects whether a local model (Ollama) is available. The frontend uses this to
enable/disable the `ASK` toggle.

### `POST /api/ask`

```json
{ "query": "show me Apple's chart and why it moved" }
```

Runs the ask loop: NL → command → screen → narration. Requires Ollama to be
running with a tool-calling model pulled (`ollama pull qwen3:4b`); otherwise
it returns a clear message.
