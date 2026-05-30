import { InfoCard, MetricCard } from "../shared/Cards";
import { MarkdownBlock } from "../shared/MarkdownBlock";
import { CsvProfileCard } from "./CsvProfileCard";
import { RawViewer } from "./RawViewer";

export function DatasetDetail({
  dataset,
  rawOpen,
  rawObject,
  rawError,
  relatedFromRaw,
  onCloseRaw,
  onJumpToCsv,
  onJumpToOverview,
  registerCsvCardRef,
}) {
  return (
    <section className="panel dataset-detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">数据集</p>
          <h2>{dataset.name}</h2>
          <p className="dataset-path">{dataset.path}</p>
        </div>
        <div className="panel-metrics">
          <MetricCard label="CSV 文件" value={dataset.csv_count} compact />
          <MetricCard label="总行数" value={dataset.total_row_count.toLocaleString("de-DE")} compact />
        </div>
      </div>

      <div className="source-grid">
        <InfoCard title="来源摘要" body={dataset.source?.summary || "暂无来源摘要。"} />
        <InfoCard title="来源链接" body={dataset.source?.url || "暂无来源链接。"} />
        <InfoCard title="许可证" body={dataset.source?.license || "暂无许可证信息。"} />
      </div>

      <div className="markdown-panel">
        <h3 id="dataset-overview">Overview</h3>
        <MarkdownBlock markdown={dataset.overview_markdown} />
      </div>

      {rawOpen ? (
        <RawViewer
          rawObject={rawObject}
          rawError={rawError}
          relatedFromRaw={relatedFromRaw}
          onClose={onCloseRaw}
          onJumpToCsv={onJumpToCsv}
          onJumpToOverview={onJumpToOverview}
        />
      ) : null}

      <div className="csv-grid" id="dataset-csv-profiles">
        {(dataset.csv_profiles ?? []).map((csvProfile) => (
          <CsvProfileCard key={csvProfile.file_name} csvProfile={csvProfile} registerRef={registerCsvCardRef} />
        ))}
      </div>
    </section>
  );
}
