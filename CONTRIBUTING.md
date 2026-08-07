# Contributing

## Setup
    cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    cd frontend && npm install

## Run the tests
    cd backend && .venv/bin/python -m pytest
    cd frontend && npm run build

## Layout
- `backend/` — FastAPI service: market data ingestion, indicators, REST endpoints.
- `frontend/` — React client: Bloomberg-style watchlist, charts, order book.
- `data/` — cached snapshots for offline dev.

## Style
- Typed Python on the backend; type hints on every endpoint and data function.
- One concern per module: `data` (I/O), `indicators` (math), `api` (routes).
- Every new endpoint needs a pytest and a client that exercises it.

## Adding a new indicator
- Implement the pure function in `backend/app/indicators`.
- Expose it as a query param on the existing quote endpoint.
- A pytest on a known-value case (hand-computed, not eyeballed).

## Pull requests
- Small, single-purpose commits. Back every claim with a test.
- Keep frontend builds clean: `npm run build` must pass before pushing.
