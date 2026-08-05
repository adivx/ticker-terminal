export default function NewsPanel({ data, large }) {
  const items = data?.items || [];
  return (
    <section className={`panel news-panel ${large ? 'large' : ''}`}>
      <header className="panel-head">
        <span className="head-label">CN — NEWS</span>
        {data?.query ? <span className="head-sym">{data.query}</span> : null}
      </header>
      <div className="news-list">
        {items.length === 0 && <div className="news-empty">No headlines found.</div>}
        {items.map((item, i) => (
          <a key={i} className="news-item" href={item.link} target="_blank" rel="noreferrer">
            <div className="news-title">{item.title}</div>
            <div className="news-meta">
              {[item.source, item.published].filter(Boolean).join(' · ')}
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
