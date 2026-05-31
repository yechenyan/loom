import { getExploreCopy } from "./exploreCopy";
import type { ExploreDataset, ExploreWorkspace } from "./exploreTypes";

export type WorkspaceSelection = { kind: "workspace"; workspace: string };
export type FileSelection = { kind: "file"; workspace: string; dataset: string; file: string };
export type Selection = WorkspaceSelection | FileSelection;

type ExploreCopy = ReturnType<typeof getExploreCopy>;

export function TreePanel({
  copy,
  open,
  selection,
  setOpen,
  setSelection,
  workspaces,
}: {
  copy: ExploreCopy;
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
            kind={copy.workspaceLevel}
            label={workspace.name}
            open={open.has(workspace.name)}
            tone="workspace"
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
  copy: ExploreCopy;
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
        count={`${dataset.csv_count} ${copy.csvCount}`}
        kind={copy.datasetLevel}
        label={dataset.name}
        open={open.has(key)}
        tone="dataset"
        onClick={() => toggle(key)}
      />
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
                <strong>{file.file_name}</strong>
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
  kind,
  label,
  onClick,
  open,
  tone,
}: {
  active?: boolean;
  count: string;
  kind: string;
  label: string;
  onClick: () => void;
  open: boolean;
  tone: "workspace" | "dataset";
}) {
  return (
    <button className={`tree-button ${tone}${active ? " active" : ""}`} onClick={onClick} type="button">
      <span>{open ? "−" : "+"}</span>
      <div className="tree-button-copy">
        <strong>{withKindSuffix(label, kind)}</strong>
        <em>{count}</em>
      </div>
    </button>
  );
}

function withKindSuffix(label: string, kind: string) {
  return `${label} [${kind.toLowerCase()}]`;
}
