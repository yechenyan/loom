import { useEffect, useState } from "react";
import { getSiteCopy } from "./copy";
import { fetchExploreWorkspaces } from "./exploreApi";
import { useI18n } from "./i18n";
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
  const { locale } = useI18n();
  const copy = getSiteCopy(locale).heroStats;
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
    <div className="stats-panel" aria-label={copy.label}>
      <StatItem label={copy.workspaces} loading={status === "loading"} value={stats.workspaceCount} />
      <StatItem label={copy.datasets} loading={status === "loading"} value={stats.datasetCount} />
      <StatItem label={copy.rawFiles} loading={status === "loading"} value={stats.rawFileCount} />
      <button className="explore-button" onClick={() => window.location.assign("/explore")} type="button">
        {copy.button}
      </button>
      {status === "error" ? <p className="stats-note">{copy.error}</p> : null}
    </div>
  );
}

function StatItem({ label, loading, value }: { label: string; loading: boolean; value: number }) {
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
