import { useCallback, useEffect, useState } from 'react';
import { api } from './lib/api.js';
import CommandBar from './components/CommandBar.jsx';
import IndexStrip from './components/IndexStrip.jsx';
import WatchlistPanel from './components/WatchlistPanel.jsx';
import QuotePanel from './components/QuotePanel.jsx';
import ChartPanel from './components/ChartPanel.jsx';
import FundamentalsPanel from './components/FundamentalsPanel.jsx';
import NewsPanel from './components/NewsPanel.jsx';
import MoversPanel from './components/MoversPanel.jsx';
import IndicesPanel from './components/IndicesPanel.jsx';
import PeersPanel from './components/PeersPanel.jsx';
import HelpPanel from './components/HelpPanel.jsx';

export default function App() {
  const [parsed, setParsed] = useState(null);
  const [screen, setScreen] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [indices, setIndices] = useState([]);
  const [relatedNews, setRelatedNews] = useState({ items: [], query: 'stock market' });
  const [aiAnswer, setAiAnswer] = useState(null);
  const [aiStatus, setAiStatus] = useState({ enabled: false, model: null });

  const execute = useCallback(async (cmd, params = {}) => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.run(cmd, params);
      setParsed(res.parsed);
      setScreen(res.screen);
      setAiAnswer(null); // a hand-typed command supersedes any AI narration
    } catch (e) {
      setParsed(null);
      setScreen(null);
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }, []);

  const ask = useCallback(async (query) => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.ask(query);
      setParsed(res.parsed);
      setScreen(res.screen);
      setAiAnswer(res.answer);
    } catch (e) {
      setError(e.message);
      setAiAnswer(null);
    } finally {
      setBusy(false);
    }
  }, []);

  const loadIndices = useCallback(async () => {
    try {
      const r = await api.indices();
      setIndices(r.indices);
    } catch {
      /* non-fatal */
    }
  }, []);

  useEffect(() => {
    loadIndices();
    execute('WEI <GO>');
  }, [execute, loadIndices]);

  useEffect(() => {
    api
      .aiStatus()
      .then((r) => setAiStatus({ enabled: !!r.enabled, model: r.model || null }))
      .catch(() => setAiStatus({ enabled: false, model: null }));
  }, []);

  // Related news for the active symbol (right rail).
  useEffect(() => {
    let cancelled = false;
    const q = parsed?.asset === 'Index' ? `${parsed.symbol} index` : parsed ? `${parsed.symbol} stock` : 'stock market';
    api
      .news(q)
      .then((r) => {
        if (!cancelled) setRelatedNews(r);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [parsed]);

  const loadRange = (range) => {
    if (!parsed) return;
    const cmd = `${parsed.symbol} ${parsed.country ? parsed.country + ' ' : ''}${parsed.asset} GP <GO>`;
    execute(cmd, { range });
  };

  const loadSymbol = (symbol) => execute(`${symbol} <GO>`);

  let center;
  if (error) {
    center = (
      <section className="panel error-panel">
        <div className="error-msg">⚠ {error}</div>
        <div className="error-hint">
          Try <span className="mono">HELP {'<GO>'}</span>
        </div>
      </section>
    );
  } else if (screen?.type === 'chart') {
    center = <ChartPanel parsed={parsed} screen={screen} onRange={loadRange} />;
  } else if (screen?.type === 'quote') {
    center = <QuotePanel parsed={parsed} quote={screen.quote} />;
  } else if (screen?.type === 'fundamentals') {
    center = <FundamentalsPanel parsed={parsed} screen={screen} />;
  } else if (screen?.type === 'news') {
    center = <NewsPanel data={screen} large />;
  } else if (screen?.type === 'peers') {
    center = <PeersPanel data={screen} onSelect={loadSymbol} />;
  } else if (screen?.type === 'indices') {
    center = <IndicesPanel data={screen} />;
  } else if (screen?.type === 'movers') {
    center = <MoversPanel data={screen} onSelect={loadSymbol} />;
  } else if (screen?.type === 'help') {
    center = <HelpPanel data={screen} onRun={execute} />;
  } else {
    center = (
      <section className="panel empty-panel">
        <div className="empty-cursor">▌</div>
        <div className="empty-text">
          Type a command below · e.g. <span className="mono">AAPL US Equity GP {'<GO>'}</span>
        </div>
      </section>
    );
  }

  return (
    <div className="app">
      <IndexStrip indices={indices} />
      {aiAnswer && (
        <div className="ai-banner">
          <span className="ai-badge">◆ AI</span>
          <div className="ai-text">{aiAnswer}</div>
          <button className="ai-close" onClick={() => setAiAnswer(null)} title="Dismiss">
            ✕
          </button>
        </div>
      )}
      <main className="main-grid">
        <WatchlistPanel onSelect={loadSymbol} activeSymbol={parsed?.yahoo} />
        <div className="center-col">{center}</div>
        <NewsPanel data={relatedNews} />
      </main>
      <CommandBar
        onRun={execute}
        onAsk={ask}
        aiEnabled={aiStatus.enabled}
        aiModel={aiStatus.model}
        busy={busy}
        lastError={error}
      />
    </div>
  );
}
