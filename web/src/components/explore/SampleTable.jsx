export function SampleTable({ title, rows }) {
  const columnNames = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <section className="subpanel sample-table">
      <h4>{title}</h4>
      {rows.length === 0 ? (
        <p className="empty-copy">没有示例行。</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>{columnNames.map((name) => <th key={name}>{name || "(空)"}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${title}-${index}`}>
                  {columnNames.map((name) => <td key={`${title}-${index}-${name}`}>{String(row[name] ?? "")}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
