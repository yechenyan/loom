import { MetricCard } from "../shared/Cards";
import { MarkdownBlock } from "../shared/MarkdownBlock";

export function WorkspaceSummary({ workspace }) {
  const totalRows = workspace.datasets.reduce((count, dataset) => count + dataset.total_row_count, 0);
  return (
    <section className="panel workspace-summary">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">工作区</p>
          <h2>{workspace.name}</h2>
        </div>
        <div className="panel-metrics">
          <MetricCard label="数据集" value={workspace.dataset_count} compact />
          <MetricCard label="总行数" value={totalRows.toLocaleString("de-DE")} compact />
        </div>
      </div>
      <MarkdownBlock markdown={workspace.readme_markdown} />
    </section>
  );
}
