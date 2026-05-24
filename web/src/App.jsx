import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/$/, "");

const defaultState = {
  workspaces: [],
  selectedWorkspace: null,
  selectedDatasetPath: null,
  loading: true,
  error: null,
};

export default function App() {
  const [state, setState] = useState(defaultState);
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch(buildApiUrl("/api/explore/workspaces"));
        if (!response.ok) {
          throw new Error(`Failed to load workspaces: ${response.status}`);
        }

        const payload = await response.json();
        if (cancelled) {
          return;
        }

        startTransition(() => {
          const firstWorkspace = payload.workspaces[0] ?? null;
          const firstDataset = firstWorkspace?.datasets?.[0]?.path ?? null;
          setState({
            workspaces: payload.workspaces,
            selectedWorkspace: firstWorkspace?.name ?? null,
            selectedDatasetPath: firstDataset,
            loading: false,
            error: null,
          });
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        }));
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedWorkspace = useMemo(
    () => state.workspaces.find((workspace) => workspace.name === state.selectedWorkspace) ?? null,
    [state.workspaces, state.selectedWorkspace],
  );

  const filteredDatasets = useMemo(() => {
    if (!selectedWorkspace) {
      return [];
    }

    const needle = deferredQuery.trim().toLowerCase();
    if (!needle) {
      return selectedWorkspace.datasets;
    }

    return selectedWorkspace.datasets.filter((dataset) => {
      const haystacks = [
        dataset.name,
        dataset.path,
        dataset.source?.summary ?? "",
        ...(dataset.csv_files ?? []).map((entry) => `${entry.file_name} ${entry.summary ?? ""}`),
      ];
      return haystacks.some((item) => item.toLowerCase().includes(needle));
    });
  }, [selectedWorkspace, deferredQuery]);

  const selectedDataset =
    filteredDatasets.find((dataset) => dataset.path === state.selectedDatasetPath) ??
    filteredDatasets[0] ??
    null;

  useEffect(() => {
    if (!selectedDataset && filteredDatasets.length === 0) {
      return;
    }

    if (selectedDataset) {
      return;
    }

    setState((current) => ({
      ...current,
      selectedDatasetPath: filteredDatasets[0]?.path ?? null,
    }));
  }, [filteredDatasets, selectedDataset]);

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <header className="hero">
        <div>
          <p className="eyebrow">Loom Explore</p>
          <h1>Dataset cards, profiles, and row shapes in one browsable web view.</h1>
          <p className="hero-copy">
            Inspect workspace-level summaries, compare profiled CSVs, and dive into column statistics
            without opening raw files by hand.
          </p>
        </div>
        <div className="hero-stats">
          <MetricCard label="Workspaces" value={state.workspaces.length} />
          <MetricCard
            label="Datasets"
            value={state.workspaces.reduce((count, workspace) => count + workspace.dataset_count, 0)}
          />
          <MetricCard
            label="CSV Profiles"
            value={state.workspaces.reduce(
              (count, workspace) =>
                count +
                workspace.datasets.reduce((datasetCount, dataset) => datasetCount + dataset.csv_count, 0),
              0,
            )}
          />
        </div>
      </header>

      {state.loading ? <StatusPanel title="Loading catalog" body="Reading loom_explore summaries..." /> : null}
      {state.error ? <StatusPanel title="Could not load data" body={state.error} variant="error" /> : null}

      {!state.loading && !state.error ? (
        <main className="dashboard">
          <aside className="sidebar">
            <div className="sidebar-card">
              <label className="search-label" htmlFor="dataset-search">
                Search datasets
              </label>
              <input
                id="dataset-search"
                className="search-input"
                placeholder="technology, plants, capacity..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>

            <div className="sidebar-card workspace-list">
              {state.workspaces.map((workspace) => (
                <button
                  key={workspace.name}
                  className={workspace.name === state.selectedWorkspace ? "workspace-pill active" : "workspace-pill"}
                  onClick={() =>
                    setState((current) => ({
                      ...current,
                      selectedWorkspace: workspace.name,
                      selectedDatasetPath: workspace.datasets[0]?.path ?? null,
                    }))
                  }
                >
                  <span>{workspace.name}</span>
                  <small>{workspace.dataset_count} datasets</small>
                </button>
              ))}
            </div>

            <div className="sidebar-card dataset-list">
              {filteredDatasets.map((dataset) => (
                <button
                  key={dataset.path}
                  className={dataset.path === selectedDataset?.path ? "dataset-item active" : "dataset-item"}
                  onClick={() =>
                    setState((current) => ({
                      ...current,
                      selectedDatasetPath: dataset.path,
                    }))
                  }
                >
                  <strong>{dataset.name}</strong>
                  <span>{dataset.total_row_count.toLocaleString()} rows</span>
                  <small>{dataset.csv_count} CSV files</small>
                </button>
              ))}
              {filteredDatasets.length === 0 ? <p className="empty-copy">No datasets match that search.</p> : null}
            </div>
          </aside>

          <section className="content">
            {selectedWorkspace ? <WorkspaceSummary workspace={selectedWorkspace} /> : null}
            {selectedDataset ? <DatasetDetail dataset={selectedDataset} /> : null}
          </section>
        </main>
      ) : null}
    </div>
  );
}

function buildApiUrl(path) {
  return `${apiBaseUrl}${path}`;
}

function WorkspaceSummary({ workspace }) {
  return (
    <section className="panel workspace-summary">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>{workspace.name}</h2>
        </div>
        <div className="panel-metrics">
          <MetricCard label="Datasets" value={workspace.dataset_count} compact />
          <MetricCard
            label="Rows"
            value={workspace.datasets
              .reduce((count, dataset) => count + dataset.total_row_count, 0)
              .toLocaleString()}
            compact
          />
        </div>
      </div>
      <MarkdownBlock markdown={workspace.readme_markdown} />
    </section>
  );
}

function DatasetDetail({ dataset }) {
  return (
    <section className="panel dataset-detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Dataset</p>
          <h2>{dataset.name}</h2>
          <p className="dataset-path">{dataset.path}</p>
        </div>
        <div className="panel-metrics">
          <MetricCard label="CSV files" value={dataset.csv_count} compact />
          <MetricCard label="Rows" value={dataset.total_row_count.toLocaleString()} compact />
        </div>
      </div>

      <div className="source-grid">
        <InfoCard title="Source Summary" body={dataset.source?.summary || "No source summary available."} />
        <InfoCard title="Source URL" body={dataset.source?.url || "No source URL provided."} />
        <InfoCard title="License" body={dataset.source?.license || "License not captured."} />
      </div>

      <div className="markdown-panel">
        <h3>Overview</h3>
        <MarkdownBlock markdown={dataset.overview_markdown} />
      </div>

      <div className="csv-grid">
        {dataset.csv_profiles.map((csvProfile) => (
          <CsvProfileCard key={csvProfile.file_name} csvProfile={csvProfile} />
        ))}
      </div>
    </section>
  );
}

function CsvProfileCard({ csvProfile }) {
  const numericColumns = csvProfile.columns.filter((column) => column.numeric_stats);
  const topValueColumns = csvProfile.columns.filter((column) => Array.isArray(column.top_values) && column.top_values.length);

  return (
    <article className="csv-card">
      <div className="csv-card-header">
        <div>
          <h3>{csvProfile.file_name}</h3>
          <p>
            {csvProfile.row_count.toLocaleString()} rows · {csvProfile.columns.length} columns
          </p>
        </div>
        <span className="csv-size">{formatBytes(csvProfile.file_size_bytes)}</span>
      </div>

      <section className="subpanel">
        <h4>Column layout</h4>
        <div className="chip-row">
          {csvProfile.columns.map((column) => (
            <span key={column.name || "(blank)"} className="column-chip">
              {column.name || "(blank)"}
            </span>
          ))}
        </div>
      </section>

      {numericColumns.length ? (
        <section className="subpanel">
          <h4>Numeric ranges</h4>
          <div className="stats-grid">
            {numericColumns.slice(0, 6).map((column) => (
              <div key={column.name} className="stat-box">
                <strong>{column.name}</strong>
                <span>min {formatNumber(column.numeric_stats.min)}</span>
                <span>max {formatNumber(column.numeric_stats.max)}</span>
                <span>mean {formatNumber(column.numeric_stats.mean)}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {topValueColumns.length ? (
        <section className="subpanel">
          <h4>Top categorical values</h4>
          <div className="top-values-list">
            {topValueColumns.slice(0, 3).map((column) => (
              <div key={column.name} className="top-values-card">
                <strong>{column.name}</strong>
                {column.top_values.slice(0, 4).map((valueEntry) => (
                  <div key={`${column.name}-${valueEntry.value}`} className="top-values-row">
                    <span>{String(valueEntry.value)}</span>
                    <span>{valueEntry.count}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <div className="samples-grid">
        <SampleTable title="Head sample" rows={csvProfile.head ?? []} />
        <SampleTable title="Tail sample" rows={csvProfile.tail ?? []} />
      </div>
    </article>
  );
}

function SampleTable({ title, rows }) {
  const columnNames = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <section className="subpanel sample-table">
      <h4>{title}</h4>
      {rows.length === 0 ? (
        <p className="empty-copy">No sample rows available.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columnNames.map((columnName) => (
                  <th key={columnName}>{columnName || "(blank)"}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${title}-${index}`}>
                  {columnNames.map((columnName) => (
                    <td key={`${title}-${index}-${columnName}`}>{String(row[columnName] ?? "")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function MetricCard({ label, value, compact = false }) {
  return (
    <div className={compact ? "metric-card compact" : "metric-card"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function InfoCard({ title, body }) {
  return (
    <div className="info-card">
      <span>{title}</span>
      <p>{body}</p>
    </div>
  );
}

function StatusPanel({ title, body, variant = "normal" }) {
  return (
    <section className={variant === "error" ? "status-panel error" : "status-panel"}>
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}

function MarkdownBlock({ markdown }) {
  const lines = markdown
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line, index, array) => !(line === "" && array[index - 1] === ""));

  return (
    <div className="markdown-block">
      {lines.map((line, index) => {
        if (line.startsWith("# ")) {
          return <h3 key={index}>{line.slice(2)}</h3>;
        }
        if (line.startsWith("## ")) {
          return <h4 key={index}>{line.slice(3)}</h4>;
        }
        if (line.startsWith("- ")) {
          return <p key={index} className="markdown-bullet">{line}</p>;
        }
        if (!line) {
          return <div key={index} className="markdown-spacer" />;
        }
        return <p key={index}>{line}</p>;
      })}
    </div>
  );
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "0 B";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  if (Math.abs(value) >= 1000) {
    return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 3 });
}
