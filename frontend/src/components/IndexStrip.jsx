import { chgClass, pct, price } from '../lib/format.js';

export default function IndexStrip({ indices }) {
  return (
    <div className="index-strip">
      {indices.map((r) => {
        const q = r.quote || {};
        const cls = chgClass(q.change);
        return (
          <span key={r.symbol} className="idx-item">
            <span className="idx-name">{r.display}</span>
            <span className={`idx-price ${cls}`}>{price(q.last)}</span>
            <span className={`idx-chg ${cls}`}>{pct(q.changePercent)}</span>
          </span>
        );
      })}
    </div>
  );
}
