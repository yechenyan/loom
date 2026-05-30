import { useRef } from "react";
import { DatasetDetail } from "../components/explore/DatasetDetail";
import { ExploreHero } from "../components/explore/ExploreHero";
import { ExploreSidebar } from "../components/explore/ExploreSidebar";
import { WorkspaceSummary } from "../components/explore/WorkspaceSummary";
import { StatusPanel } from "../components/shared/Cards";
import { useExploreViewModel } from "../hooks/useExploreViewModel";

export function ExplorePage() {
  const csvCardRefs = useRef(new Map());
  const { state, stats, selectedWorkspace, filteredDatasets, selectedDataset, datasetRawFiles, relatedExploreFiles, relatedFromRaw, actions } = useExploreViewModel();

  const jumpToCsv = (fileName) => {
    const node = csvCardRefs.current.get(fileName);
    node?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <>
      <ExploreHero stats={stats} />
      {state.loading ? <StatusPanel title="目录加载中" body="正在读取 loom 数据卡..." /> : null}
      {state.error ? <StatusPanel title="目录加载失败" body={state.error} variant="error" /> : null}
      {!state.loading && !state.error ? (
        <main className="dashboard">
          <ExploreSidebar
            state={state}
            selectedDataset={selectedDataset}
            filteredDatasets={filteredDatasets}
            datasetRawFiles={datasetRawFiles}
            relatedExploreFiles={relatedExploreFiles}
            onSelectWorkspace={actions.selectWorkspace}
            onSelectDataset={actions.selectDataset}
            onSetQuery={actions.setQuery}
            onSelectRawFile={(item) => item.meta && actions.openRawFile(item.meta)}
            onExploreItemClick={(item) => {
              if (item.action?.type === "scroll") {
                document.getElementById(item.action.target)?.scrollIntoView({ behavior: "smooth", block: "start" });
              }
              if (item.action?.type === "scrollCsv") {
                jumpToCsv(item.action.target);
              }
            }}
          />
          <section className="content">
            {selectedWorkspace ? <WorkspaceSummary workspace={selectedWorkspace} /> : null}
            {selectedDataset ? (
              <DatasetDetail
                dataset={selectedDataset}
                rawOpen={state.rawOpen}
                rawObject={state.rawObject}
                rawError={state.rawError}
                relatedFromRaw={relatedFromRaw}
                onCloseRaw={actions.closeRawViewer}
                onJumpToCsv={jumpToCsv}
                onJumpToOverview={() => document.getElementById("dataset-overview")?.scrollIntoView({ behavior: "smooth", block: "start" })}
                registerCsvCardRef={(fileName, node) => (node ? csvCardRefs.current.set(fileName, node) : csvCardRefs.current.delete(fileName))}
              />
            ) : null}
          </section>
        </main>
      ) : null}
    </>
  );
}
