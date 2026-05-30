import { useNavigate } from "react-router-dom";
import { FileWorkbench } from "../components/home/FileWorkbench";
import { HomeHero } from "../components/home/HomeHero";
import { HomeSections } from "../components/home/HomeSections";
import { useHomeDemoState } from "../hooks/useHomeDemoState";
import { useAtomValue } from "jotai";
import { exploreStateAtom } from "../state/exploreState";

export function HomePage() {
  const navigate = useNavigate();
  const exploreState = useAtomValue(exploreStateAtom);
  const { state, activePrompt, installPrompt, setSelectedAgent, setSelectedFile, copyPrompt, copyText } = useHomeDemoState();
  const stats = {
    workspaceCount: exploreState.workspaces.length,
    datasetCount: exploreState.workspaces.reduce((count, workspace) => count + workspace.dataset_count, 0),
    csvProfileCount: exploreState.workspaces.reduce((count, workspace) => count + workspace.datasets.reduce((inner, dataset) => inner + dataset.csv_count, 0), 0),
  };

  return (
    <main className="page-stack">
      <HomeHero
        stats={stats}
        activePrompt={activePrompt}
        installPrompt={installPrompt}
        copied={state.copied}
        onOpenExplore={() => navigate("/explore")}
        onSelectAgent={setSelectedAgent}
        onCopyPrompt={copyPrompt}
        onCopyText={copyText}
      />
      <FileWorkbench selectedFile={state.selectedFile} onSelectFile={setSelectedFile} />
      <HomeSections />
    </main>
  );
}
