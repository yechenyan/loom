import { useDeferredValue, useEffect, useMemo } from "react";
import { useAtomValue, useSetAtom } from "jotai";
import { closeRawViewerAtom, exploreStateAtom, loadRawManifestAtom, openRawFileAtom, selectDatasetAtom, selectWorkspaceAtom, setQueryAtom } from "../state/exploreState";
import { basename } from "../lib/formatters";

export function useExploreViewModel() {
  const state = useAtomValue(exploreStateAtom);
  const deferredQuery = useDeferredValue(state.query);
  const loadRawManifest = useSetAtom(loadRawManifestAtom);
  const selectWorkspace = useSetAtom(selectWorkspaceAtom);
  const selectDataset = useSetAtom(selectDatasetAtom);
  const openRawFile = useSetAtom(openRawFileAtom);
  const closeRawViewer = useSetAtom(closeRawViewerAtom);
  const setQuery = useSetAtom(setQueryAtom);

  useEffect(() => {
    loadRawManifest(state.selectedWorkspaceName);
  }, [loadRawManifest, state.selectedWorkspaceName]);

  const selectedWorkspace = useMemo(
    () => state.workspaces.find((workspace) => workspace.name === state.selectedWorkspaceName) ?? null,
    [state.workspaces, state.selectedWorkspaceName],
  );

  const filteredDatasets = useMemo(() => {
    if (!selectedWorkspace) {
      return [];
    }
    const needle = deferredQuery.trim().toLowerCase();
    if (!needle) {
      return selectedWorkspace.datasets;
    }
    return selectedWorkspace.datasets.filter((dataset) => {
      const haystacks = [dataset.name, dataset.path, dataset.source?.summary ?? "", ...(dataset.csv_files ?? []).map((entry) => `${entry.file_name} ${entry.summary ?? ""}`)];
      return haystacks.some((item) => item.toLowerCase().includes(needle));
    });
  }, [deferredQuery, selectedWorkspace]);

  const selectedDataset = filteredDatasets.find((dataset) => dataset.path === state.selectedDatasetPath) ?? filteredDatasets[0] ?? null;

  useEffect(() => {
    if (filteredDatasets.length > 0 && !filteredDatasets.some((dataset) => dataset.path === state.selectedDatasetPath)) {
      selectDataset(filteredDatasets[0].path);
    }
  }, [filteredDatasets, selectDataset, state.selectedDatasetPath]);

  const datasetRawFiles = useMemo(() => {
    if (!selectedDataset || !state.rawManifestByPath) {
      return [];
    }
    const prefix = selectedDataset.path ? `${selectedDataset.path.replace(/\/$/, "")}/` : "";
    return Object.entries(state.rawManifestByPath)
      .filter(([path]) => (prefix ? path.startsWith(prefix) : true))
      .map(([path, meta]) => ({ path, sha256: meta.sha256, size_bytes: meta.size_bytes }))
      .sort((a, b) => a.path.localeCompare(b.path));
  }, [selectedDataset, state.rawManifestByPath]);

  const stats = useMemo(() => ({
    workspaceCount: state.workspaces.length,
    datasetCount: state.workspaces.reduce((count, workspace) => count + workspace.dataset_count, 0),
    csvProfileCount: state.workspaces.reduce((count, workspace) => count + workspace.datasets.reduce((inner, dataset) => inner + dataset.csv_count, 0), 0),
  }), [state.workspaces]);

  const relatedExploreFiles = useMemo(() => {
    if (!selectedDataset) {
      return [];
    }
    return [
      { kind: "explore", label: "overview.md", action: { type: "scroll", target: "dataset-overview" } },
      ...(selectedDataset.csv_profiles ?? []).filter((item) => item?.file_name).map((item) => ({ kind: "explore", label: item.file_name, action: { type: "scrollCsv", target: item.file_name } })),
    ];
  }, [selectedDataset]);

  const relatedFromRaw = useMemo(() => {
    if (!selectedDataset || !state.selectedRawPath) {
      return null;
    }
    const fileName = basename(state.selectedRawPath);
    return { fileName, hasCsvProfileMatch: (selectedDataset.csv_profiles ?? []).some((profile) => profile?.file_name === fileName) };
  }, [selectedDataset, state.selectedRawPath]);

  return {
    state,
    stats,
    selectedWorkspace,
    filteredDatasets,
    selectedDataset,
    datasetRawFiles,
    relatedExploreFiles,
    relatedFromRaw,
    actions: { selectWorkspace, selectDataset, openRawFile, closeRawViewer, setQuery },
  };
}
