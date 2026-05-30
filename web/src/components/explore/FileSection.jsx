import { formatBytes } from "../../lib/formatters";

export function FileSection({ title, items, onClickItem, loading = false, error = null, emptyCopy = null }) {
  return (
    <section className="file-section">
      <div className="file-section-title">
        <span>{title}</span>
        {loading ? <small>加载中…</small> : null}
      </div>
      {error ? <p className="empty-copy">{error}</p> : null}
      {!error && items.length === 0 && emptyCopy ? <p className="empty-copy">{emptyCopy}</p> : null}
      <div className="file-items">
        {items.map((item) => (
          <button key={`${title}-${item.label}`} className="file-item" onClick={() => onClickItem?.(item)}>
            <span className="file-item-label">{item.label}</span>
            {item.kind === "raw" && item.meta ? <span className="file-item-meta">{formatBytes(item.meta.size_bytes)}</span> : null}
          </button>
        ))}
      </div>
    </section>
  );
}
