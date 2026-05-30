export function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "0 B";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  const digits = Math.abs(value) >= 1000 ? 1 : 3;
  return value.toLocaleString("de-DE", { maximumFractionDigits: digits });
}

export function basename(path) {
  const parts = String(path ?? "").split("/");
  return parts[parts.length - 1] || "";
}
