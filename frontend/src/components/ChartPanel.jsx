import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts';
import { chgClass, num, pct, price } from '../lib/format.js';

const RANGES = [
  ['1d', '1D'],
  ['5d', '5D'],
  ['1m', '1M'],
  ['6m', '6M'],
  ['1y', '1Y'],
  ['5y', '5Y'],
];

export default function ChartPanel({ parsed, screen, onRange }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef({});
  const [ready, setReady] = useState(false);

  // Create the chart once.
  useEffect(() => {
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#000000' },
        textColor: '#7a7a7a',
        fontFamily: "'JetBrains Mono', Consolas, monospace",
        fontSize: 11,
        attributionLogo: false,
      },
      grid: { vertLines: { color: '#101010' }, horzLines: { color: '#101010' } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#222' },
      timeScale: { borderColor: '#222', timeVisible: true },
      autoSize: true,
    });

    const candle = chart.addCandlestickSeries({
      upColor: '#00c853',
      downColor: '#ff3d3d',
      wickUpColor: '#00c853',
      wickDownColor: '#ff3d3d',
      borderVisible: false,
    });

    const volume = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'vol',
    });
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    const ma20 = chart.addLineSeries({
      color: '#ffb300',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    const ma50 = chart.addLineSeries({
      color: '#26c6da',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    seriesRef.current = { chart, candle, volume, ma20, ma50 };
    setReady(true);

    return () => {
      chart.remove();
      seriesRef.current = {};
    };
  }, []);

  // Push new data whenever a screen arrives.
  useEffect(() => {
    const s = seriesRef.current;
    if (!s.chart || !screen) return;
    const hist = screen.history || [];
    const ind = screen.indicators || {};

    s.candle.setData(
      hist.map((r) => ({ time: r.time, open: r.open, high: r.high, low: r.low, close: r.close }))
    );
    s.volume.setData(
      hist.map((r) => ({
        time: r.time,
        value: r.volume,
        color: r.close >= r.open ? 'rgba(0,200,83,0.35)' : 'rgba(255,61,61,0.35)',
      }))
    );
    s.ma20.setData(zip(hist, ind.sma20));
    s.ma50.setData(zip(hist, ind.sma50));
    s.chart.timeScale().fitContent();
  }, [screen, ready]);

  const readout = screen?.indicators?.readout || {};
  const quote = screen?.quote;

  return (
    <section className="panel chart-panel">
      <header className="panel-head">
        <span className="head-label">GP — PRICE GRAPH</span>
        {parsed ? (
          <span className="head-sym">
            {parsed.symbol} {parsed.asset}
          </span>
        ) : null}
        <span className="range-btns">
          {RANGES.map(([key, label]) => (
            <button
              key={key}
              className={`range-btn ${screen?.range === key ? 'active' : ''}`}
              onClick={() => onRange(key)}
            >
              {label}
            </button>
          ))}
        </span>
      </header>
      <div className="chart-readout">
        {quote && quote.last != null && (
          <span className={`ro-price ${chgClass(quote.change)}`}>
            {price(quote.last)} {pct(quote.changePercent)}
          </span>
        )}
        {Object.entries(readout).map(([k, v]) => (
          <span key={k} className="ro-item">
            <span className="ro-k">{k}</span> <span className="ro-v">{v == null ? '—' : num(v)}</span>
          </span>
        ))}
      </div>
      <div ref={containerRef} className="chart-box" />
    </section>
  );
}

function zip(hist, series) {
  if (!series) return [];
  const out = [];
  for (let i = 0; i < hist.length; i++) {
    const v = series[i];
    if (v != null) out.push({ time: hist[i].time, value: v });
  }
  return out;
}
