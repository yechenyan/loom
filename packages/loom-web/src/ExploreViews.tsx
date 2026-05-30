import { useEffect, useState, type ReactNode } from "react";
import { fetchRawManifest, fetchRawText } from "./exploreApi";
import { useI18n } from "./i18n";
import type { ResolvedSelection } from "./ExplorePage";
import { RawCsvTable } from "./RawCsvTable";

export function DataCardView({ selected }: { selected: ResolvedSelection }) {
  const { locale } = useI18n();
  const copy = {
    en: {
      fileSummary: "This CSV has been recognized by Loom as an explorable file.",
      card: "Dataset Card",
      dataset: "Dataset",
      source: "Source",
      columns: "Columns",
      preview: "Preview",
      noSource: "No source summary",
      csvFiles: "CSV files",
      profiledRows: "profiled rows",
    },
    de: {
      fileSummary: "Diese CSV wurde von Loom als erkundbare Datei erkannt.",
      card: "Datenkarte",
      dataset: "Dataset",
      source: "Quelle",
      columns: "Spalten",
      preview: "Vorschau",
      noSource: "Keine Quellenzusammenfassung",
      csvFiles: "CSV-Dateien",
      profiledRows: "profilierte Zeilen",
    },
    zh: {
      fileSummary: "这个 CSV 已经被 Loom 识别为可探索文件。",
      card: "Dataset Card",
      dataset: "Dataset",
      source: "Source",
      columns: "Columns",
      preview: "Preview",
      noSource: "No source summary",
      csvFiles: "CSV files",
      profiledRows: "profiled rows",
    },
  }[locale];
  const { dataset, file, profile } = selected;

  return (
    <section className="detail-body datacard-page">
      <div className="datacard-hero">
        <p className="detail-path">{selected.rawPath}</p>
        <h2>{file.file_name}</h2>
        <p>{file.summary || copy.fileSummary}</p>
        <div className="metric-row">
          <span>{file.row_count} rows</span>
          <span>{file.column_count} columns</span>
          <span>{formatBytes(file.file_size_bytes)}</span>
        </div>
      </div>
      <div className="datacard-layout">
        <article className="card-sheet">
          <h3>{copy.card}</h3>
          <MarkdownSummary text={dataset.overview_markdown} />
        </article>
        <div className="card-sidebar">
          <InfoPanel title={copy.dataset}>
            <p>{dataset.name}</p>
            <p>{dataset.csv_count} {copy.csvFiles}</p>
            <p>{dataset.total_row_count} {copy.profiledRows}</p>
          </InfoPanel>
          <InfoPanel title={copy.source}>
            <p>{dataset.source.summary || copy.noSource}</p>
            {dataset.source.url ? <a href={firstUrl(dataset.source.url)}>{firstUrl(dataset.source.url)}</a> : null}
          </InfoPanel>
          <InfoPanel title={copy.columns}>
            <div className="column-chips">
              {file.columns.map((column) => (
                <span title={file.column_roles?.[column]} key={column}>
                  {column}
                </span>
              ))}
            </div>
          </InfoPanel>
          {profile?.head?.length ? (
            <InfoPanel title={copy.preview}>
              <KeyValuePreview row={profile.head[0]} />
            </InfoPanel>
          ) : null}
        </div>
      </div>
    </section>
  );
}

export function ProfileView({ selected }: { selected: ResolvedSelection }) {
  const { locale } = useI18n();
  const copy = {
    en: { empty: "This file has no available profile.", body: "Loom-generated machine-readable field profiling expanded as JSON." },
    de: { empty: "Fuer diese Datei ist kein Profil verfuegbar.", body: "Von Loom erzeugtes maschinenlesbares Feldprofil als JSON." },
    zh: { empty: "这个文件没有可用 profile。", body: "Loom 生成的机器可读字段画像，按 JSON 层级展开为单列内容。" },
  }[locale];
  const profile = selected.profile;

  if (!profile) {
    return <p className="empty-state">{copy.empty}</p>;
  }

  return (
    <section className="detail-body datacard-page">
      <div className="datacard-hero">
        <p className="detail-path">{selected.rawPath}</p>
        <h2>profile.json</h2>
        <p>{copy.body}</p>
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
  const { locale } = useI18n();
  const copy = {
    en: { loading: "Loading raw file...", missing: "raw manifest does not contain", body: "Raw CSV content loaded from the live raw object store." },
    de: { loading: "Rohdatei wird geladen...", missing: "Raw-Manifest enthaelt nicht", body: "CSV-Rohinhalt aus dem Live-Raw-Object-Store." },
    zh: { loading: "正在读取原始文件...", missing: "raw manifest 中找不到", body: "从线上 raw object 读取的原始 CSV 内容。" },
  }[locale];
  const [rawText, setRawText] = useState("");
  const [status, setStatus] = useState(copy.loading);

  useEffect(() => {
    setRawText("");
    setStatus(copy.loading);
    fetchRawManifest(selected.workspace)
      .then((manifest) => {
        const entry = manifest[selected.rawPath];
        if (!entry) throw new Error(`${copy.missing} ${selected.rawPath}`);
        return fetchRawText(entry.sha256);
      })
      .then((text) => {
        setRawText(text);
        setStatus("");
      })
      .catch((error: Error) => setStatus(error.message));
  }, [copy.loading, copy.missing, selected.rawPath, selected.workspace]);

  return (
    <section className="detail-body datacard-page">
      <div className="datacard-hero">
        <p className="detail-path">{selected.rawPath}</p>
        <h2>Raw Data</h2>
        <p>{copy.body}</p>
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
