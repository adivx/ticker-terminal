async function request(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* keep default message */
    }
    throw new Error(msg);
  }
  return res.json();
}

const getJSON = (path) => request(path);
const postJSON = (path, body) =>
  request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

export const api = {
  parse: (cmd) => getJSON(`/api/parse?cmd=${encodeURIComponent(cmd)}`),
  run: (cmd, params = {}) =>
    getJSON(`/api/function?cmd=${encodeURIComponent(cmd)}&${new URLSearchParams(params)}`),
  news: (q) => getJSON(`/api/news?q=${encodeURIComponent(q)}`),
  indices: () => getJSON('/api/indices'),
  movers: () => getJSON('/api/movers'),
  aiStatus: () => getJSON('/api/ai'),
  ask: (query) => postJSON('/api/ask', { query }),
  watchlist: () => getJSON('/api/watchlist'),
  watchlistQuotes: () => getJSON('/api/watchlist/quotes'),
  addWatch: (symbol) => postJSON('/api/watchlist', { symbol }),
  removeWatch: (symbol) =>
    fetch(`/api/watchlist/${encodeURIComponent(symbol)}`, { method: 'DELETE' }).then((r) => r.json()),
};
