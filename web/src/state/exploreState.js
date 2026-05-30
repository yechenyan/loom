import { startTransition } from "react";
import { atom } from "jotai";
import { buildApiUrl } from "../lib/api";
import { decodeBase64ToText } from "../lib/rawText";

const initialState = {
  workspaces: [],
  selectedWorkspaceName: null,
  selectedDatasetPath: null,
  selectedRawPath: null,
  query: "",
  rawManifestByPath: null,
  rawLoading: false,
  rawError: null,
  rawOpen: false,
  rawObject: null,
  loading: true,
  error: null,
};

export const exploreStateAtom = atom(initialState);

export const loadCatalogAtom = atom(null, async (_get, set) => {
  set(exploreStateAtom, (current) => ({ ...current, loading: true, error: null }));
  try {
    const response = await fetch(buildApiUrl("/api/explore/workspaces"));
    if (!response.ok) {
      throw new Error(`Failed to load workspaces: ${response.status}`);
    }
    const payload = await response.json();
    const firstWorkspace = payload.workspaces[0] ?? null;
    startTransition(() => {
      set(exploreStateAtom, (current) => ({
        ...current,
        workspaces: payload.workspaces,
        selectedWorkspaceName: firstWorkspace?.name ?? null,
        selectedDatasetPath: firstWorkspace?.datasets?.[0]?.path ?? null,
        selectedRawPath: null,
        rawManifestByPath: null,
        rawLoading: false,
        rawError: null,
        rawOpen: false,
        rawObject: null,
        loading: false,
        error: null,
      }));
    });
  } catch (error) {
    set(exploreStateAtom, (current) => ({ ...current, loading: false, error: error instanceof Error ? error.message : "Unknown error" }));
  }
});

export const loadRawManifestAtom = atom(null, async (_get, set, workspaceName) => {
  if (!workspaceName) {
    set(exploreStateAtom, (current) => ({ ...current, rawManifestByPath: null, rawLoading: false, rawError: null }));
    return;
  }
  set(exploreStateAtom, (current) => ({ ...current, rawLoading: true, rawError: null, rawManifestByPath: null }));
  try {
    const response = await fetch(buildApiUrl(`/api/workspaces/${encodeURIComponent(workspaceName)}/raw-manifest`));
    if (!response.ok) {
      throw new Error(`Failed to load raw manifest: ${response.status}`);
    }
    const payload = await response.json();
    startTransition(() => {
      set(exploreStateAtom, (current) => ({ ...current, rawLoading: false, rawError: null, rawManifestByPath: payload.raw_manifest ?? {} }));
    });
  } catch (error) {
    set(exploreStateAtom, (current) => ({ ...current, rawLoading: false, rawManifestByPath: null, rawError: error instanceof Error ? error.message : "Unknown error" }));
  }
});

export const selectWorkspaceAtom = atom(null, (_get, set, workspace) => {
  set(exploreStateAtom, (current) => ({
    ...current,
    selectedWorkspaceName: workspace.name,
    selectedDatasetPath: workspace.datasets[0]?.path ?? null,
    selectedRawPath: null,
    rawOpen: false,
    rawObject: null,
  }));
});

export const selectDatasetAtom = atom(null, (_get, set, datasetPath) => {
  set(exploreStateAtom, (current) => ({ ...current, selectedDatasetPath: datasetPath, selectedRawPath: null, rawOpen: false, rawObject: null }));
});

export const setQueryAtom = atom(null, (_get, set, query) => {
  set(exploreStateAtom, (current) => ({ ...current, query }));
});

export const closeRawViewerAtom = atom(null, (_get, set) => {
  set(exploreStateAtom, (current) => ({ ...current, rawOpen: false, selectedRawPath: null, rawObject: null, rawError: null }));
});

export const openRawFileAtom = atom(null, async (_get, set, rawMeta) => {
  set(exploreStateAtom, (current) => ({ ...current, selectedRawPath: rawMeta.path, rawOpen: true, rawObject: null, rawError: null }));
  if (rawMeta.size_bytes > 1_500_000) {
    set(exploreStateAtom, (current) => ({ ...current, rawObject: { tooLarge: true, path: rawMeta.path, size_bytes: rawMeta.size_bytes, sha256: rawMeta.sha256 } }));
    return;
  }
  try {
    const response = await fetch(buildApiUrl(`/api/raw/objects/${encodeURIComponent(rawMeta.sha256)}`));
    if (!response.ok) {
      throw new Error(`Failed to load raw object: ${response.status}`);
    }
    const payload = await response.json();
    set(exploreStateAtom, (current) => ({
      ...current,
      rawObject: { tooLarge: false, path: rawMeta.path, size_bytes: rawMeta.size_bytes, sha256: rawMeta.sha256, text: decodeBase64ToText(payload.content_base64 ?? "") },
    }));
  } catch (error) {
    set(exploreStateAtom, (current) => ({ ...current, rawError: error instanceof Error ? error.message : "Unknown error" }));
  }
});
