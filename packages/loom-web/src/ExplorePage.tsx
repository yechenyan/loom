import { useEffect, useState } from "react";
import { fetchExploreWorkspaces } from "./exploreApi";
import { getExploreCopy } from "./exploreCopy";
import { DetailCommand, WorkspaceDetail } from "./ExploreDetailChrome";
import { TreePanel, type Selection } from "./ExploreTree";
import { DataCardView, ProfileView, RawDataView } from "./ExploreViews";
import { useI18n } from "./i18n";
import type { ExploreCsvFile, ExploreCsvProfile, ExploreDataset, ExploreWorkspace } from "./exploreTypes";
import { SiteHeader } from "./SiteHeader";

type Tab = "card" | "profile" | "raw";

export function ExplorePage() {
  const { locale } = useI18n();
  const copy = getExploreCopy(locale);
  const [workspaces, setWorkspaces] = useState<ExploreWorkspace[]>([]);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [tab, setTab] = useState<Tab>("card");
  const [status, setStatus] = useState(copy.loading);

  useEffect(() => {
    setStatus(copy.loading);
    fetchExploreWorkspaces()
      .then((items) => {
        setWorkspaces(items);
        setStatus(items.length ? "" : copy.empty);
      })
      .catch((error: Error) => setStatus(error.message));
  }, [copy.empty, copy.loading]);

  const selected = resolveSelection(workspaces, selection);
  const selectedWorkspace = resolveWorkspace(workspaces, selection);

  return (
    <main className="explore-shell">
      <SiteHeader />
      <section className="explore-hero">
        <p className="eyebrow">LIVE DATA EXPLORER</p>
        <h1>{copy.title}</h1>
      </section>
      <section className="explore-grid">
        <TreePanel
          copy={copy}
          open={open}
          selection={selection}
          setOpen={setOpen}
          setSelection={(next) => {
            setSelection(next);
            setTab("card");
          }}
          workspaces={workspaces}
        />
        <article className="explore-detail">
          {status ? <p className="empty-state">{status}</p> : null}
          {!status && selected ? <DetailTabs copy={copy} selected={selected} setTab={setTab} tab={tab} /> : null}
          {!status && !selected && selectedWorkspace ? <WorkspaceDetail copy={copy} workspace={selectedWorkspace} /> : null}
          {!status && !selected && !selectedWorkspace ? <ExploreEmptyState copy={copy} workspaces={workspaces} /> : null}
        </article>
      </section>
    </main>
  );
}

function ExploreEmptyState({
  copy,
  workspaces,
}: {
  copy: ReturnType<typeof getExploreCopy>;
  workspaces: ExploreWorkspace[];
}) {
  const datasetCount = workspaces.reduce((total, workspace) => total + workspace.dataset_count, 0);
  const csvCount = workspaces.reduce(
    (total, workspace) => total + workspace.datasets.reduce((datasetTotal, dataset) => datasetTotal + dataset.csv_count, 0),
    0,
  );

  return (
    <section className="explore-empty">
      <div className="empty-copy">
        <p className="section-kicker">{copy.start}</p>
        <h2>{copy.startTitle}</h2>
        <p>{copy.startBody}</p>
      </div>
      <div className="empty-stats" aria-label={copy.statsLabel}>
        <span>
          <strong>{workspaces.length}</strong>
          {copy.workspaces}
        </span>
        <span>
          <strong>{datasetCount}</strong>
          {copy.datasets}
        </span>
        <span>
          <strong>{csvCount}</strong>
          {copy.files}
        </span>
      </div>
      <div className="empty-steps">
        <article>
          <span>1</span>
          <h3>{copy.step1Title}</h3>
          <p>{copy.step1Body}</p>
        </article>
        <article>
          <span>2</span>
          <h3>{copy.step2Title}</h3>
          <p>{copy.step2Body}</p>
        </article>
        <article>
          <span>3</span>
          <h3>{copy.step3Title}</h3>
          <p>{copy.step3Body}</p>
        </article>
      </div>
    </section>
  );
}

function DetailTabs({
  copy,
  selected,
  setTab,
  tab,
}: {
  copy: ReturnType<typeof getExploreCopy>;
  selected: ResolvedSelection;
  setTab: (tab: Tab) => void;
  tab: Tab;
}) {
  return (
    <>
      <DetailCommand
        label={copy.fileCommandLabel}
        modes={[
          { key: "agent", label: copy.agentModeLabel, value: `loom get ${selected.resourcePath}` },
          { key: "cli", label: copy.cliModeLabel, value: `loomcli get ${selected.resourcePath}` },
        ]}
      />
      <div className="detail-tabs" aria-label={copy.tabAria}>
        <button className={tab === "card" ? "active" : ""} onClick={() => setTab("card")} type="button">
          {copy.cardTab}
        </button>
        <button className={tab === "profile" ? "active" : ""} onClick={() => setTab("profile")} type="button">
          {copy.profileTab}
        </button>
        <button className={tab === "raw" ? "active" : ""} onClick={() => setTab("raw")} type="button">
          {copy.rawTab}
        </button>
      </div>
      {tab === "card" ? <DataCardView selected={selected} /> : null}
      {tab === "profile" ? <ProfileView selected={selected} /> : null}
      {tab === "raw" ? <RawDataView selected={selected} /> : null}
    </>
  );
}

export type ResolvedSelection = {
  workspace: string;
  dataset: ExploreDataset;
  file: ExploreCsvFile;
  profile?: ExploreCsvProfile;
  rawPath: string;
  resourcePath: string;
};

function resolveSelection(workspaces: ExploreWorkspace[], selection: Selection | null): ResolvedSelection | null {
  if (!selection || selection.kind !== "file") return null;
  const workspace = workspaces.find((item) => item.name === selection.workspace);
  const dataset = workspace?.datasets.find((item) => item.path === selection.dataset);
  const file = dataset?.csv_files.find((item) => (item.dataset_relative_path || item.file_name) === selection.file);
  if (!workspace || !dataset || !file) return null;
  const profile = dataset.csv_profiles.find((item) => (item.dataset_relative_path || item.file_name) === selection.file);
  const rawPath = dataset.path === "." ? selection.file : `${dataset.path}/${selection.file}`;
  const resourcePath = `${workspace.name}/${rawPath}`;
  return { workspace: workspace.name, dataset, file, profile, rawPath, resourcePath };
}

function resolveWorkspace(workspaces: ExploreWorkspace[], selection: Selection | null): ExploreWorkspace | null {
  if (!selection) return null;
  return workspaces.find((item) => item.name === selection.workspace) || null;
}
