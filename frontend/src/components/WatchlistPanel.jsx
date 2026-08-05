import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { chgClass, pct, price } from '../lib/format.js';

export default function WatchlistPanel({ onSelect, activeSymbol }) {
  const [symbols, setSymbols] = useState([]);
  const [quotes, setQuotes] = useState({});
  const [addVal, setAddVal] = useState('');

  const load = async () => {
    const [wl, qs] = await Promise.all([api.watchlist(), api.watchlistQuotes()]);
    setSymbols(wl.symbols);
    const map = {};
    (qs.quotes || []).forEach((q) => {
      map[q.symbol] = q;
    });
    setQuotes(map);
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    if (!addVal.trim()) return;
    const s = addVal.trim().toUpperCase();
    await api.addWatch(s);
    setAddVal('');
    load();
  };

  const remove = async (e, s) => {
    e.stopPropagation();
    await api.removeWatch(s);
    load();
  };

  return (
    <section className="panel watch-panel">
      <header className="panel-head">
        <span className="head-label">MON — WATCHLIST</span>
      </header>
      <div className="watch-list">
        {symbols.map((s) => {
          const q = quotes[s];
          const cls = chgClass(q?.change);
          return (
            <div
              key={s}
              className={`watch-row ${activeSymbol === s ? 'active' : ''}`}
              onClick={() => onSelect(s)}
            >
              <span className="watch-sym">{s}</span>
              <span className={`watch-price ${cls}`}>{q ? price(q.last) : '—'}</span>
              <span className={`watch-chg ${cls}`}>{q ? pct(q.changePercent) : ''}</span>
              <button className="watch-del" onClick={(e) => remove(e, s)}>
                ×
              </button>
            </div>
          );
        })}
      </div>
      <div className="watch-add">
        <input
          value={addVal}
          onChange={(e) => setAddVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
          placeholder="ADD SYMBOL"
          spellCheck={false}
        />
        <button onClick={add}>+</button>
      </div>
    </section>
  );
}
