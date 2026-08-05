import { fracPct, money, num } from '../lib/format.js';

export default function FundamentalsPanel({ parsed, screen }) {
  const f = screen?.fundamentals || {};
  return (
    <section className="panel fund-panel">
      <header className="panel-head">
        <span className="head-label">FA — FINANCIAL ANALYSIS</span>
        <span className="head-sym">{f.name || parsed?.symbol}</span>
      </header>
      <table className="fund-table">
        <tbody>
          {(f.fields || []).map((row) => (
            <tr key={row.key}>
              <td className="fund-label">{row.label}</td>
              <td className="fund-value">{formatVal(row.kind, row.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {f.description ? <p className="fund-desc">{f.description}</p> : null}
    </section>
  );
}

function formatVal(kind, v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  if (kind === 'currency') return money(v);
  if (kind === 'percent') return fracPct(v);
  if (kind === 'text') return String(v);
  if (kind === 'number') return num(v);
  return String(v);
}
