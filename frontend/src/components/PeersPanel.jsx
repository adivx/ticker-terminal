import { chgClass, money, num, pct, price } from '../lib/format.js';

export default function PeersPanel({ data, onSelect }) {
  const q = data?.quote || {};
  const peers = data?.peers || [];
  return (
    <section className="panel peers-panel">
      <header className="panel-head">
        <span className="head-label">CRPR — COMPARABLE ANALYSIS</span>
        {q.symbol ? <span className="head-sym">{q.symbol} · {q.sector || 'Sector'}</span> : null}
      </header>
      <table className="idx-table peers-table">
        <thead>
          <tr>
            <th>PEER</th>
            <th>LAST</th>
            <th>CHG %</th>
            <th>P/E</th>
            <th>P/B</th>
            <th>MKT CAP</th>
          </tr>
        </thead>
        <tbody>
          {peers.map((p) => (
            <tr key={p.symbol} onClick={() => onSelect(p.symbol)}>
              <td className="peer-name">
                {p.name || p.symbol} <span className="idx-sym">{p.symbol}</span>
              </td>
              <td className={`idx-price ${chgClass(p.change)}`}>{price(p.last)}</td>
              <td className={`idx-chg ${chgClass(p.change)}`}>{pct(p.changePercent)}</td>
              <td>{p.trailingPE != null ? num(p.trailingPE) : '—'}</td>
              <td>{p.priceToBook != null ? num(p.priceToBook) : '—'}</td>
              <td>{money(p.marketCap)}</td>
            </tr>
          ))}
          {peers.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No sector peers found for this instrument.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
