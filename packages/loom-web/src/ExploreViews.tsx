import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { fetchRawManifest, fetchRawText } from "./exploreApi";
import type { ResolvedSelection } from "./ExplorePage";
import { RawCsvTable } from "./RawCsvTable";

export function DataCardView({ selected }: { selected: ResolvedSelection }) {
  const { dataset, file, profile } = selected;
  return (
    <section className="detail-body datacard-page">
      <div className="datacard-hero">
        <p className="detail-path">{selected.rawPath}</p>
        <h2>{file.file_name}</h2>
        <p>{file.summary || "这个 CSV 已经被 Loom 识别为可探索文件。"}</p>
        <div className="metric-row">
          <span>{file.row_count} rows</span>
          <span>{file.column_count} columns</span>
          <span>{formatBytes(file.file_size_bytes)}</span>
        </div>
      </div>
      <div className="datacard-layout">
        <article className="card-sheet">
          <h3>Dataset Card</h3>
          <MarkdownSummary text={dataset.overview_markdown} />
        </article>
        <div className="card-sidebar">
          <InfoPanel title="Dataset">
            <p>{dataset.name}</p>
            <p>{dataset.csv_count} CSV files</p>
            <p>{dataset.total_row_count} profiled rows</p>
          </InfoPanel>
          <InfoPanel title="Source">
            <p>{dataset.source.summary || "No source summary"}</p>
            {dataset.source.url ? <a href={firstUrl(dataset.source.url)}>{firstUrl(dataset.source.url)}</a> : null}
          </InfoPanel>
          <InfoPanel title="Columns">
            <div className="column-chips">
              {file.columns.map((column) => (
                <span title={file.column_roles?.[column]} key={column}>
                  {column}
                </span>
              ))}
            </div>
          </InfoPanel>
          {profile?.head?.length ? (
            <InfoPanel title="Preview">
              <KeyValuePreview row={profile.head[0]} />
            </InfoPanel>
          ) : null}
        </div>
      </div>
    </section>
  );
}

export function ProfileView({ selected }: { selected: ResolvedSelection }) {
  const profile = selected.profile;
  if (!profile) {
    return <p className="empty-state">这个文件没有可用 profile。</p>;
  }

  return (
    <section className="detail-body datacard-page">
      <div className="datacard-hero">
        <p className="detail-path">{selected.rawPath}</p>
        <h2>profile.json</h2>
        <p>Loom 生成的机器可读字段画像，按 JSON 层级展开为单列内容。</p>
        <div className="metric-row">
          <span>{profile.row_count} rows</span>
          <span>{profile.columns.length} columns</span>
          <span>{formatBytes(profile.file_size_bytes)}</span>
        </div>
      </div>
      <pre className="json-block">{JSON.stringify(profile, null, 2)}</pre>
    </section>
  );
}

export function RawDataView({ selected }: { selected: ResolvedSelection }) {
  const [rawText, setRawText] = useState("");
  const [status, setStatus] = useState("正在读取原始文件...");

  useEffect(() => {
    setRawText("");
    setStatus("正在读取原始文件...");
    fetchRawManifest(selected.workspace)
      .then((manifest) => {
        const entry = manifest[selected.rawPath];
        if (!entry) throw new Error(`raw manifest 中找不到 ${selected.rawPath}`);
        return fetchRawText(entry.sha256);
      })
      .then((text) => {
        setRawText(text);
        setStatus("");
      })
      .catch((error: Error) => setStatus(error.message));
  }, [selected.rawPath, selected.workspace]);

  return (
    <section className="detail-body datacard-page">
      <div className="datacard-hero">
        <p className="detail-path">{selected.rawPath}</p>
        <h2>Raw Data</h2>
        <p>从线上 raw object 读取的原始 CSV 内容。</p>
      </div>
      {status ? <p className="empty-state">{status}</p> : <RawCsvTable csvText={rawText} />}
    </section>
  );
}

function KeyValuePreview({ row }: { row: Record<string, string> }) {
  return (
    <dl className="preview-list">
      {Object.entries(row).map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{value || "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

function InfoPanel({ children, title }: { children: ReactNode; title: string }) {
  return (
    <section className="info-panel">
      <h4>{title}</h4>
      {children}
    </section>
  );
}

function MarkdownSummary({ text }: { text: string }) {
  return (
    <div className="markdown-summary">
      {text
        .split("\n")
        .filter((line) => line.trim())
        .slice(0, 18)
        .map((line) => (
          <p key={line}>{line.replace(/^#+\s*/, "").replace(/^- /, "")}</p>
        ))}
    </div>
  );
}

function firstUrl(value: string) {
  return value.split(/\s+/).find((item) => item.startsWith("http")) || value;
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}
