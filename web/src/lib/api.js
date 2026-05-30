const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/$/, "");

export function buildApiUrl(path) {
  return `${apiBaseUrl}${path}`;
}
