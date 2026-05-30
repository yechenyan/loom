import type { ExploreWorkspace, RawManifest } from "./exploreTypes";

const DEFAULT_API_BASE_URL = "https://loom-api-free.onrender.com";

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export async function fetchExploreWorkspaces(): Promise<ExploreWorkspace[]> {
  const payload = await getJson<{ workspaces: ExploreWorkspace[] }>("/api/explore/workspaces");
  return payload.workspaces;
}

export async function fetchRawManifest(workspace: string): Promise<RawManifest> {
  const payload = await getJson<{ raw_manifest: RawManifest }>(
    `/api/workspaces/${encodeURIComponent(workspace)}/raw-manifest`,
  );
  return payload.raw_manifest;
}

export async function fetchRawText(sha256: string): Promise<string> {
  const payload = await getJson<{ content_base64: string }>(
    `/api/raw/objects/${encodeURIComponent(sha256)}`,
  );
  return decodeBase64(payload.content_base64);
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`);
  if (!response.ok) {
    throw new Error(`Loom API ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

function decodeBase64(value: string) {
  const binary = atob(value);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}
