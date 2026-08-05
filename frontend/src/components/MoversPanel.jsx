import { chgClass, pct, price } from '../lib/format.js';

export default function MoversPanel({ data, onSelect }) {
  return (
    <section className="panel movers-panel">
      <header className="panel-head">
        <span className="head-label">TOP — TOP MOVERS</span>
      </header>
      <div className="movers-cols">
        <MoverCol title="TOP GAINERS" rows={data?.topGainers || []} cls="up" onSelect={onSelect} />
        <MoverCol title="TOP LOSERS" rows={data?.topLosers || []} cls="down" onSelect={onSelect} />
      </div>
    </section>
  );
}

function MoverCol({ title, rows, cls, onSelect }) {
  return (
    <div className="mover-col">
      <div className="mover-col-title">{title}</div>
      {rows.map((q) => (
        <div key={q.symbol} className="mover-row" onClick={() => onSelect(q.symbol)}>
          <span className="mover-sym">{q.symbol}</span>
          <span className={`mover-price ${chgClass(q.change)}`}>{price(q.last)}</span>
          <span className={`mover-chg ${cls}`}>{pct(q.changePercent)}</span>
        </div>
      ))}
    </div>
  );
}
