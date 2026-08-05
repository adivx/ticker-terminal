#!/usr/bin/env bash
# Start both servers. Backend on :8000, frontend on :5173.
set -e
cd "$(dirname "$0")"

if ! curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
  (cd backend && .venv/bin/uvicorn app.main:app --port 8000 >/tmp/terminal-api.log 2>&1 &)
  echo "backend  → http://localhost:8000  (log: /tmp/terminal-api.log)"
else
  echo "backend  → already running on :8000"
fi

(cd frontend && npm run dev >/tmp/terminal-vite.log 2>&1 &)
echo "frontend → http://localhost:5173   (log: /tmp/terminal-vite.log)"
echo
echo "Open http://localhost:5173 and type e.g.  AAPL US Equity GP <GO>"
