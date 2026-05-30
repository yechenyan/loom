import { basename, formatBytes } from "../../lib/formatters";

export function RawViewer({ rawObject, rawError, relatedFromRaw, onClose, onJumpToCsv, onJumpToOverview }) {
  return (
    <section className="subpanel raw-viewer">
      <div className="raw-viewer-header">
        <h4>原始文件</h4>
        <button className="raw-close" onClick={onClose}>关闭</button>
      </div>
      {rawError ? <p className="empty-copy">{rawError}</p> : null}
      {!rawError && !rawObject ? <p className="empty-copy">从左侧点一个原始文件来预览。</p> : null}
      {rawObject ? (
        <>
          <div className="raw-meta">
            <span className="raw-path">{rawObject.path}</span>
            <span className="raw-size">{formatBytes(rawObject.size_bytes)}</span>
          </div>
          <div className="raw-related">
            <span className="raw-related-label">关联跳转</span>
            <button className="linkish" onClick={onJumpToOverview}>Overview</button>
            {relatedFromRaw?.hasCsvProfileMatch ? (
              <button className="linkish" onClick={() => onJumpToCsv(relatedFromRaw.fileName)}>CSV 卡片</button>
            ) : null}
          </div>
          {rawObject.tooLarge ? (
            <div className="raw-too-large">
              <p className="empty-copy">文件过大，请本地执行 <code>loom get {rawObject.path}</code> 获取。</p>
              <button className="linkish" onClick={() => onJumpToCsv(basename(rawObject.path))}>跳到对应 CSV 卡片</button>
            </div>
          ) : (
            <>
              <div className="raw-actions">
                <button className="linkish" onClick={() => onJumpToCsv(basename(rawObject.path))}>跳到对应 CSV 卡片</button>
              </div>
              <pre className="raw-pre">
                <code>{rawObject.text}</code>
              </pre>
            </>
          )}
        </>
      ) : null}
    </section>
  );
}
