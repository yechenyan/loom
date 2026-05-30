import { FileSection } from "./FileSection";

export function ExploreSidebar({
  state,
  selectedDataset,
  filteredDatasets,
  datasetRawFiles,
  relatedExploreFiles,
  onSelectWorkspace,
  onSelectDataset,
  onSelectRawFile,
  onSetQuery,
  onExploreItemClick,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-card workspace-list">
        <p className="sidebar-title">工作区</p>
        {state.workspaces.map((workspace) => (
          <button
            key={workspace.name}
            className={workspace.name === state.selectedWorkspaceName ? "workspace-pill active" : "workspace-pill"}
            onClick={() => onSelectWorkspace(workspace)}
          >
            <span>{workspace.name}</span>
            <small>{workspace.dataset_count} 个数据集</small>
          </button>
        ))}
      </div>

      <div className="sidebar-card dataset-list">
        <p className="sidebar-title">数据集</p>
        <label className="search-label" htmlFor="dataset-search">搜索数据集</label>
        <input
          id="dataset-search"
          className="search-input"
          placeholder="technology, plants, capacity..."
          value={state.query}
          onChange={(event) => onSetQuery(event.target.value)}
        />
        {filteredDatasets.map((dataset) => (
          <button
            key={dataset.path}
            className={dataset.path === selectedDataset?.path ? "dataset-item active" : "dataset-item"}
            onClick={() => onSelectDataset(dataset.path)}
          >
            <strong>{dataset.name}</strong>
            <span>{dataset.total_row_count.toLocaleString()} rows</span>
            <small>{dataset.csv_count} 个 CSV</small>
          </button>
        ))}
        {filteredDatasets.length === 0 ? <p className="empty-copy">没有匹配当前搜索的数据集。</p> : null}
      </div>

      <div className="sidebar-card file-list">
        <p className="sidebar-title">文件</p>
        {selectedDataset ? (
          <>
            <FileSection title="概览文件" items={relatedExploreFiles} onClickItem={onExploreItemClick} />
            <FileSection
              title="原始文件"
              loading={state.rawLoading}
              error={state.rawError}
              items={datasetRawFiles.map((entry) => ({ kind: "raw", label: entry.path, meta: entry }))}
              emptyCopy={state.rawLoading ? null : "当前数据集还没有关联原始文件。"}
              onClickItem={onSelectRawFile}
            />
          </>
        ) : (
          <p className="empty-copy">先选择一个数据集。</p>
        )}
      </div>
    </aside>
  );
}
