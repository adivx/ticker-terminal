export function num(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function price(n) {
  return num(n, 2);
}

export function money(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  const sign = n < 0 ? '-' : '';
  const a = Math.abs(n);
  if (a >= 1e12) return sign + (a / 1e12).toFixed(2) + 'T';
  if (a >= 1e9) return sign + (a / 1e9).toFixed(2) + 'B';
  if (a >= 1e6) return sign + (a / 1e6).toFixed(2) + 'M';
  if (a >= 1e3) return sign + (a / 1e3).toFixed(1) + 'K';
  return num(n, 2);
}

export function pct(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return num(n, digits) + '%';
}

// yfinance stores yields/margins as fractions (0.05 == 5%).
// Guard: some upstream fields occasionally arrive already scaled (0.35 == 0.35%).
export function fracPct(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return pct(Math.abs(n) > 1 ? n : n * 100);
}

export function signed(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return n > 0 ? '+' + num(n, digits) : num(n, digits);
}

export function chgClass(v) {
  if (v === null || v === undefined || v === 0) return 'flat';
  return v > 0 ? 'up' : 'down';
}
