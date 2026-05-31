import { useEffect, useState } from "react";
import { fetchExploreWorkspaces } from "./exploreApi";
import { getExploreCopy } from "./exploreCopy";
import { DetailCommand, WorkspaceDetail } from "./ExploreDetailChrome";
import { DataCardView, ProfileView, RawDataView } from "./ExploreViews";
import { useI18n } from "./i18n";
import type { ExploreCsvFile, ExploreCsvProfile, ExploreDataset, ExploreWorkspace } from "./exploreTypes";
import { SiteHeader } from "./SiteHeader";

type WorkspaceSelection = { kind: "workspace"; workspace: string };
type FileSelection = { kind: "file"; workspace: string; dataset: string; file: string };
type Selection = WorkspaceSelection | FileSelection;
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

function TreePanel({
  copy,
  open,
  selection,
  setOpen,
  setSelection,
  workspaces,
}: {
  copy: ReturnType<typeof getExploreCopy>;
  open: Set<string>;
  selection: Selection | null;
  setOpen: (open: Set<string>) => void;
  setSelection: (selection: Selection) => void;
  workspaces: ExploreWorkspace[];
}) {
  function toggle(key: string) {
    const next = new Set(open);
    next.has(key) ? next.delete(key) : next.add(key);
    setOpen(next);
  }

  return (
    <aside className="explore-tree" id="explore-tree" aria-label={copy.treeAria}>
      <p className="tree-label">{copy.treeLabel}</p>
      {workspaces.map((workspace) => (
        <div className="tree-group" key={workspace.name}>
          <TreeButton
            active={selection?.kind === "workspace" && selection.workspace === workspace.name}
            count={`${workspace.dataset_count} ${copy.datasetCount}`}
            label={workspace.name}
            open={open.has(workspace.name)}
            onClick={() => {
              setSelection({ kind: "workspace", workspace: workspace.name });
              toggle(workspace.name);
            }}
          />
          {open.has(workspace.name)
            ? workspace.datasets.map((dataset) => (
                <DatasetBranch
                  copy={copy}
                  dataset={dataset}
                  key={dataset.path}
                  open={open}
                  selection={selection}
                  setSelection={setSelection}
                  toggle={toggle}
                  workspace={workspace.name}
                />
              ))
            : null}
        </div>
      ))}
    </aside>
  );
}

function DatasetBranch({
  copy,
  dataset,
  open,
  selection,
  setSelection,
  toggle,
  workspace,
}: {
  copy: ReturnType<typeof getExploreCopy>;
  dataset: ExploreDataset;
  open: Set<string>;
  selection: Selection | null;
  setSelection: (selection: Selection) => void;
  toggle: (key: string) => void;
  workspace: string;
}) {
  const key = `${workspace}/${dataset.path}`;
  return (
    <div className="tree-branch">
      <TreeButton count={`${dataset.csv_count} ${copy.csvCount}`} label={dataset.name} open={open.has(key)} onClick={() => toggle(key)} />
      {open.has(key)
        ? dataset.csv_files.map((file) => {
            const filePath = file.dataset_relative_path || file.file_name;
            const active =
              selection?.kind === "file" &&
              selection.workspace === workspace &&
              selection.dataset === dataset.path &&
              selection.file === filePath;
            return (
              <button
                className={`tree-file${active ? " active" : ""}`}
                key={filePath}
                onClick={() => setSelection({ kind: "file", workspace, dataset: dataset.path, file: filePath })}
                type="button"
              >
                {file.file_name}
              </button>
            );
          })
        : null}
    </div>
  );
}

function TreeButton({
  active,
  count,
  label,
  onClick,
  open,
}: {
  active?: boolean;
  count: string;
  label: string;
  onClick: () => void;
  open: boolean;
}) {
  return (
    <button className={`tree-button${active ? " active" : ""}`} onClick={onClick} type="button">
      <span>{open ? "−" : "+"}</span>
      <strong>{label}</strong>
      <em>{count}</em>
    </button>
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
  const fileCommand = `loomcli get ${selected.resourcePath}`;
  return (
    <>
      <DetailCommand label={copy.fileCommandLabel} value={fileCommand} />
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
