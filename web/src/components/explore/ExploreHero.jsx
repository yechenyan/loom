import { MetricCard } from "../shared/Cards";

export function ExploreHero({ stats }) {
  return (
    <header className="hero">
      <div>
        <p className="eyebrow">探索数据</p>
        <h1>先看摘要和卡片，再决定要打开哪份原始数据。</h1>
        <p className="hero-copy">
          左侧选择 workspace 和 dataset，先读 overview 与 CSV 卡片，再按需打开真正相关的 raw file。
        </p>
      </div>
      <div className="hero-stats">
        <MetricCard label="工作区" value={stats.workspaceCount} />
        <MetricCard label="数据集" value={stats.datasetCount} />
        <MetricCard label="CSV 卡片" value={stats.csvProfileCount} />
      </div>
    </header>
  );
}
