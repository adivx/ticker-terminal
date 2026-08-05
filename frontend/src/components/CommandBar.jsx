import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../lib/api.js';

const EXAMPLES = [
  'AAPL US Equity <GO>',
  'MSFT US Equity GP <GO>',
  'RELIANCE IN Equity FA <GO>',
  'NIFTY Index GP <GO>',
  'TOP <GO>',
  'WEI <GO>',
  'HELP <GO>',
];

export default function CommandBar({ onRun, onAsk, aiEnabled, aiModel, busy, lastError }) {
  const [mode, setMode] = useState('cmd'); // 'cmd' | 'ask'
  const [value, setValue] = useState('');
  const [preview, setPreview] = useState(null);
  const [hist, setHist] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('cmd-hist') || '[]');
    } catch {
      return [];
    }
  });
  const [histIdx, setHistIdx] = useState(-1);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  const hint = useMemo(() => EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)], []);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const pushHist = (cmd) => {
    const next = [cmd, ...hist.filter((h) => h !== cmd)].slice(0, 20);
    setHist(next);
    localStorage.setItem('cmd-hist', JSON.stringify(next));
  };

  const submit = (cmd) => {
    const c = (cmd ?? value).trim();
    if (!c) return;
    pushHist(c);
    setHistIdx(-1);
    if (mode === 'ask') {
      onAsk(c);
    } else {
      onRun(c);
    }
  };

  const onChange = (v) => {
    setValue(v);
    if (mode === 'ask') {
      setPreview(v.trim() ? 'natural language → Bloomberg command · AI' : null);
      return;
    }
    clearTimeout(debounceRef.current);
    if (!v.trim()) {
      setPreview(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const p = await api.parse(v);
        const label =
          p.function && !p.symbol
            ? `${p.function} — ${p.label}`
            : `${p.symbol} · ${p.country ? p.country + ' ' + p.asset : p.asset} · ${p.label}`;
        setPreview(label);
      } catch {
        setPreview(null);
      }
    }, 250);
  };

  const toggleMode = () => {
    const next = mode === 'ask' ? 'cmd' : 'ask';
    setMode(next);
    setPreview(null);
    setValue('');
    inputRef.current?.focus();
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (hist.length === 0) return;
      const i = histIdx < 0 ? hist.length - 1 : Math.max(0, histIdx - 1);
      setHistIdx(i);
      setValue(hist[i]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (histIdx < 0) return;
      const i = histIdx + 1;
      if (i >= hist.length) {
        setHistIdx(-1);
        setValue('');
      } else {
        setHistIdx(i);
        setValue(hist[i]);
      }
    }
  };

  const askOn = mode === 'ask';
  const placeholder = askOn
    ? 'ASK: describe what you want…'
    : 'TYPE A COMMAND…';

  return (
    <div className="cmdbar">
      <div className="cmdline">
        <button
          className={`mode-btn${askOn ? ' mode-btn-on' : ''}`}
          onClick={toggleMode}
          title={aiEnabled ? 'Toggle command / AI ask' : 'AI off — start Ollama'}
        >
          {askOn ? 'ASK' : 'CMD'}
        </button>
        <span className="cmd-prompt">{askOn ? '❯' : '⇥'}</span>
        <input
          ref={inputRef}
          className={`cmd-input${askOn ? ' ask-mode' : ''}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          spellCheck={false}
          autoComplete="off"
        />
        <button className="go-btn" onClick={() => submit()}>
          [&nbsp;GO&nbsp;]
        </button>
        {busy && <span className="cmd-busy">◌</span>}
      </div>
      <div className="cmd-preview">
        {preview && <span className="preview-ok">{preview}</span>}
        {!preview && lastError && <span className="preview-err">⚠ {lastError}</span>}
        {!preview && !lastError && askOn && (
          <span className="preview-hint">
            {aiEnabled
              ? `e.g. "show me Apple's chart and why it moved"${aiModel ? ` · ${aiModel}` : ''}`
              : 'AI off — install Ollama · ollama pull qwen3:4b'}
          </span>
        )}
        {!preview && !lastError && !askOn && <span className="preview-hint">{hint}</span>}
      </div>
    </div>
  );
}
