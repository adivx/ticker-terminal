# Security policy

ticker-terminal is a localhost developer tool. The FastAPI backend binds to
`127.0.0.1` by default, has no authentication, and holds no credentials or API
keys — all data comes from free public sources (Yahoo Finance, Google News RSS,
and optionally a local Ollama model).

## Intended usage

- Run on your own machine (`uvicorn app.main:app --reload --port 8000`).
- **Do not** expose the backend to a public network or reverse-proxy it without
  adding your own authentication — the API was designed for a single local
  user, not a production deployment.

## Reporting a vulnerability

If you find a bug with security implications (for example, a crash or
unexpected code execution from a crafted command line, or a path issue in the
cache layer), open a private issue or email the maintainer directly. We'll
respond within a few days.

## Scope / guarantees

- No analytics module may make a network call other than to the free public
  data sources listed in the README.
- Command parsing must fail cleanly with a `400`, never execute input.
- The AI ask loop runs against a **local** model by default and makes no
  cloud calls unless you configure a remote provider yourself.
