export default function HelpPanel({ data, onRun }) {
  return (
    <section className="panel help-panel">
      <header className="panel-head">
        <span className="head-label">HELP — COMMAND REFERENCE</span>
      </header>
      <p className="help-syntax">{data?.syntax}</p>
      <p className="help-note">{data?.note}</p>
      <table className="idx-table help-table">
        <thead>
          <tr>
            <th>FUNC</th>
            <th>SCREEN</th>
            <th>EXAMPLE</th>
          </tr>
        </thead>
        <tbody>
          {(data?.reference || []).map((r) => (
            <tr key={r.fn}>
              <td className="help-fn">{r.fn}</td>
              <td>{r.label}</td>
              <td>
                <button className="help-example" onClick={() => onRun(r.example)}>
                  {r.example}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
