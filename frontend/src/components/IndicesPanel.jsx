import { chgClass, pct, price, signed } from '../lib/format.js';

export default function IndicesPanel({ data }) {
  return (
    <section className="panel indices-panel">
      <header className="panel-head">
        <span className="head-label">WEI — WORLD EQUITY INDICES</span>
      </header>
      <table className="idx-table">
        <thead>
          <tr>
            <th>INDEX</th>
            <th>LAST</th>
            <th>CHG</th>
            <th>CHG %</th>
          </tr>
        </thead>
        <tbody>
          {(data?.indices || []).map((r) => {
            const q = r.quote || {};
            const cls = chgClass(q.change);
            return (
              <tr key={r.symbol}>
                <td className="idx-name">
                  {r.display} <span className="idx-sym">{q.symbol}</span>
                </td>
                <td className={`idx-price ${cls}`}>{price(q.last)}</td>
                <td className={`idx-chg ${cls}`}>{signed(q.change)}</td>
                <td className={`idx-chg ${cls}`}>{pct(q.changePercent)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
