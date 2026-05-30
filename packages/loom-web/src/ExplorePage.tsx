import { useEffect, useState } from "react";
import { fetchExploreWorkspaces } from "./exploreApi";
import { DataCardView, ProfileView, RawDataView } from "./ExploreViews";
import type { ExploreCsvFile, ExploreCsvProfile, ExploreDataset, ExploreWorkspace } from "./exploreTypes";
import { SiteHeader } from "./SiteHeader";

type Selection = { workspace: string; dataset: string; file: string };
type Tab = "card" | "profile" | "raw";

export function ExplorePage() {
  const [workspaces, setWorkspaces] = useState<ExploreWorkspace[]>([]);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [tab, setTab] = useState<Tab>("card");
  const [status, setStatus] = useState("正在加载线上数据...");

  useEffect(() => {
    fetchExploreWorkspaces()
      .then((items) => {
        setWorkspaces(items);
        setStatus(items.length ? "" : "线上服务暂时没有可探索的工作区。");
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  const selected = resolveSelection(workspaces, selection);

  return (
    <main className="explore-shell">
      <SiteHeader />
      <section className="explore-hero">
        <p className="eyebrow">LIVE DATA EXPLORER</p>
        <h1>数据探索</h1>
      </section>
      <section className="explore-grid">
        <TreePanel
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
          {!status && selected ? (
            <DetailTabs selected={selected} tab={tab} setTab={setTab} />
          ) : null}
          {!status && !selected ? <ExploreEmptyState workspaces={workspaces} /> : null}
        </article>
      </section>
    </main>
  );
}

function ExploreEmptyState({ workspaces }: { workspaces: ExploreWorkspace[] }) {
  const datasetCount = workspaces.reduce((total, workspace) => total + workspace.dataset_count, 0);
  const csvCount = workspaces.reduce(
    (total, workspace) =>
      total + workspace.datasets.reduce((datasetTotal, dataset) => datasetTotal + dataset.csv_count, 0),
    0,
  );

  return (
    <section className="explore-empty">
      <div className="empty-copy">
        <p className="section-kicker">START HERE</p>
        <h2>选择一个 CSV，Loom 会展示三层事实。</h2>
        <p>
          左侧目录默认收起。先展开工作区，再展开数据集，最后选择一个 CSV 文件查看数据卡、
          profile.json 和线上原始表格。
        </p>
      </div>
      <div className="empty-stats" aria-label="当前线上数据概览">
        <span>
          <strong>{workspaces.length}</strong>
          工作区
        </span>
        <span>
          <strong>{datasetCount}</strong>
          数据集
        </span>
        <span>
          <strong>{csvCount}</strong>
          CSV 文件
        </span>
      </div>
      <div className="empty-steps">
        <article>
          <span>1</span>
          <h3>展开工作区</h3>
          <p>从 demo、energy 等线上工作区开始定位数据来源。</p>
        </article>
        <article>
          <span>2</span>
          <h3>选择数据集</h3>
          <p>进入 dataset 层级，查看它包含的 CSV 文件。</p>
        </article>
        <article>
          <span>3</span>
          <h3>查看真实数据</h3>
          <p>在 DataCard、profile 和 Raw Data 之间切换。</p>
        </article>
      </div>
    </section>
  );
}

function TreePanel({
  open,
  selection,
  setOpen,
  setSelection,
  workspaces,
}: {
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
    <aside className="explore-tree" id="explore-tree" aria-label="Loom 数据树">
      <p className="tree-label">工作区 / 数据集 / 文件</p>
      {workspaces.map((workspace) => (
        <div className="tree-group" key={workspace.name}>
          <TreeButton
            count={`${workspace.dataset_count} datasets`}
            label={workspace.name}
            open={open.has(workspace.name)}
            onClick={() => toggle(workspace.name)}
          />
          {open.has(workspace.name)
            ? workspace.datasets.map((dataset) => (
                <DatasetBranch
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
  dataset,
  open,
  selection,
  setSelection,
  toggle,
  workspace,
}: {
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
      <TreeButton
        count={`${dataset.csv_count} csv`}
        label={dataset.name}
        open={open.has(key)}
        onClick={() => toggle(key)}
      />
      {open.has(key)
        ? dataset.csv_files.map((file) => {
            const filePath = file.dataset_relative_path || file.file_name;
            const active =
              selection?.workspace === workspace &&
              selection.dataset === dataset.path &&
              selection.file === filePath;
            return (
              <button
                className={`tree-file${active ? " active" : ""}`}
                key={filePath}
                onClick={() => setSelection({ workspace, dataset: dataset.path, file: filePath })}
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
  count,
  label,
  onClick,
  open,
}: {
  count: string;
  label: string;
  onClick: () => void;
  open: boolean;
}) {
  return (
    <button className="tree-button" onClick={onClick} type="button">
      <span>{open ? "−" : "+"}</span>
      <strong>{label}</strong>
      <em>{count}</em>
    </button>
  );
}

function DetailTabs({
  selected,
  setTab,
  tab,
}: {
  selected: ResolvedSelection;
  setTab: (tab: Tab) => void;
  tab: Tab;
}) {
  return (
    <>
      <div className="detail-tabs" aria-label="文件详情标签">
        <button className={tab === "card" ? "active" : ""} onClick={() => setTab("card")} type="button">
          DataCard
        </button>
        <button className={tab === "profile" ? "active" : ""} onClick={() => setTab("profile")} type="button">
          profile
        </button>
        <button className={tab === "raw" ? "active" : ""} onClick={() => setTab("raw")} type="button">
          rawData
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
};

function resolveSelection(workspaces: ExploreWorkspace[], selection: Selection | null): ResolvedSelection | null {
  if (!selection) return null;
  const workspace = workspaces.find((item) => item.name === selection.workspace);
  const dataset = workspace?.datasets.find((item) => item.path === selection.dataset);
  const file = dataset?.csv_files.find((item) => (item.dataset_relative_path || item.file_name) === selection.file);
  if (!workspace || !dataset || !file) return null;
  const profile = dataset.csv_profiles.find((item) => (item.dataset_relative_path || item.file_name) === selection.file);
  const rawPath = dataset.path === "." ? selection.file : `${dataset.path}/${selection.file}`;
  return { workspace: workspace.name, dataset, file, profile, rawPath };
}
