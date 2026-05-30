import { useEffect, useState } from "react";
import { fetchExploreWorkspaces } from "./exploreApi";
import type { ExploreWorkspace } from "./exploreTypes";

type HeroStatsState = {
  workspaceCount: number;
  datasetCount: number;
  rawFileCount: number;
};

const emptyStats: HeroStatsState = {
  workspaceCount: 0,
  datasetCount: 0,
  rawFileCount: 0,
};

export function HeroStats() {
  const [stats, setStats] = useState<HeroStatsState>(emptyStats);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchExploreWorkspaces()
      .then((workspaces) => {
        setStats(calculateStats(workspaces));
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div className="stats-panel" aria-label="Loom live dataset stats">
      <StatItem label="工作区" loading={status === "loading"} value={stats.workspaceCount} />
      <StatItem label="数据集" loading={status === "loading"} value={stats.datasetCount} />
      <StatItem label="原始数据" loading={status === "loading"} value={stats.rawFileCount} />
      <button className="explore-button" onClick={() => window.location.assign("/explore")} type="button">
        探索数据集
      </button>
      {status === "error" ? <p className="stats-note">线上数据暂时不可用</p> : null}
    </div>
  );
}

function StatItem({
  label,
  loading,
  value,
}: {
  label: string;
  loading: boolean;
  value: number;
}) {
  return (
    <div className="stat-item">
      <strong>{loading ? "—" : value}</strong>
      <span>{label}</span>
    </div>
  );
}

function calculateStats(workspaces: ExploreWorkspace[]): HeroStatsState {
  return workspaces.reduce(
    (totals, workspace) => ({
      workspaceCount: totals.workspaceCount + 1,
      datasetCount: totals.datasetCount + workspace.dataset_count,
      rawFileCount:
        totals.rawFileCount +
        workspace.datasets.reduce((sum, dataset) => sum + (dataset.csv_files.length || dataset.csv_count), 0),
    }),
    emptyStats,
  );
}
