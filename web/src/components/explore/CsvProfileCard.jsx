import { formatBytes, formatNumber } from "../../lib/formatters";
import { SampleTable } from "./SampleTable";

export function CsvProfileCard({ csvProfile, registerRef }) {
  const numericColumns = csvProfile.columns.filter((column) => column.numeric_stats);
  const topValueColumns = csvProfile.columns.filter((column) => Array.isArray(column.top_values) && column.top_values.length);

  return (
    <article className="csv-card" ref={(node) => registerRef?.(csvProfile.file_name, node)}>
      <div className="csv-card-header">
        <div>
          <h3>{csvProfile.file_name}</h3>
          <p>{csvProfile.row_count.toLocaleString("de-DE")} 行 · {csvProfile.columns.length} 列</p>
        </div>
        <span className="csv-size">{formatBytes(csvProfile.file_size_bytes)}</span>
      </div>

      <section className="subpanel">
        <h4>列结构</h4>
        <div className="chip-row">
          {csvProfile.columns.map((column) => <span key={column.name || "(blank)"} className="column-chip">{column.name || "(空)"}</span>)}
        </div>
      </section>

      {numericColumns.length ? (
        <section className="subpanel">
          <h4>数值范围</h4>
          <div className="stats-grid">
            {numericColumns.slice(0, 6).map((column) => (
              <div key={column.name} className="stat-box">
                <strong>{column.name}</strong>
                <span>Min {formatNumber(column.numeric_stats.min)}</span>
                <span>Max {formatNumber(column.numeric_stats.max)}</span>
                <span>Mean {formatNumber(column.numeric_stats.mean)}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {topValueColumns.length ? (
        <section className="subpanel">
          <h4>高频类别</h4>
          <div className="top-values-list">
            {topValueColumns.slice(0, 3).map((column) => (
              <div key={column.name} className="top-values-card">
                <strong>{column.name}</strong>
                {column.top_values.slice(0, 4).map((value) => (
                  <div key={`${column.name}-${value.value}`} className="top-values-row">
                    <span>{String(value.value)}</span>
                    <span>{value.count}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <div className="samples-grid">
        <SampleTable title="开头" rows={csvProfile.head ?? []} />
        <SampleTable title="结尾" rows={csvProfile.tail ?? []} />
      </div>
    </article>
  );
}
