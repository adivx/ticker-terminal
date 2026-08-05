import { chgClass, fracPct, money, pct, price, signed } from '../lib/format.js';

export default function QuotePanel({ parsed, quote }) {
  const q = quote || {};
  const cls = chgClass(q.change);
  return (
    <section className="panel quote-panel">
      <header className="panel-head">
        <span className="head-label">DES — DESCRIPTION</span>
        <span className="head-sym">{q.symbol}</span>
      </header>
      <div className="quote-hero">
        <div className="quote-name">
          {q.name || q.symbol}
          {q.exchange ? <span className="quote-exch"> · {q.exchange}</span> : null}
        </div>
        <div className="quote-price-row">
          <span className={`quote-price ${cls}`}>{price(q.last)}</span>
          <span className={`quote-chg ${cls}`}>
            {signed(q.change)} ({pct(q.changePercent)})
          </span>
        </div>
        <div className="quote-meta">
          <span>{q.currency || ''}</span>
          {q.marketCap != null && <span> · Mkt cap {money(q.marketCap)}</span>}
          {q.trailingPE != null && <span> · P/E {num2(q.trailingPE)}</span>}
        </div>
      </div>
      <div className="stat-grid">
        <Stat label="Open" value={price(q.open)} />
        <Stat label="High" value={price(q.high)} />
        <Stat label="Low" value={price(q.low)} />
        <Stat label="Prev Close" value={price(q.prevClose)} />
        <Stat label="Volume" value={int(q.volume)} />
        <Stat label="Avg Volume" value={int(q.avgVolume)} />
        <Stat label="52W High" value={price(q.fiftyTwoWeekHigh)} />
        <Stat label="52W Low" value={price(q.fiftyTwoWeekLow)} />
        <Stat label="Beta" value={q.beta != null ? num2(q.beta) : '—'} />
        <Stat label="Div Yield" value={q.dividendYield != null ? fracPct(q.dividendYield) : '—'} />
        <Stat label="Forward P/E" value={q.forwardPE != null ? num2(q.forwardPE) : '—'} />
        <Stat label="P/B" value={q.priceToBook != null ? num2(q.priceToBook) : '—'} />
      </div>
      {q.sector || q.industry ? (
        <div className="quote-sector">
          {[q.sector, q.industry].filter(Boolean).join(' · ')}
        </div>
      ) : null}
    </section>
  );
}

function num2(n) {
  return n == null ? '—' : Number(n).toFixed(2);
}

function int(n) {
  return n == null ? '—' : Number(n).toLocaleString();
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
