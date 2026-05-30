import { TUTORIAL_FILES } from "../../lib/content/tutorialFiles";

export function FileWorkbench({ selectedFile, onSelectFile }) {
  const activeFile = TUTORIAL_FILES.find((file) => file.id === selectedFile) ?? TUTORIAL_FILES[0];
  const groups = [
    { name: "loom/tutorial", files: TUTORIAL_FILES.filter((file) => file.group === "tutorial") },
    { name: "raw_data/tutorial", files: TUTORIAL_FILES.filter((file) => file.group === "raw_data/tutorial") },
  ];

  return (
    <section className="file-workbench panel">
      <div className="home-section-head">
        <p className="eyebrow">文件结构</p>
        <h2>安装教学数据后会生成这些文件</h2>
      </div>
      <div className="file-workbench-shell">
        <aside className="file-sidebar">
          <div className="file-sidebar-title">EXPLORER</div>
          {groups.map((group) => (
            <div key={group.name} className="file-group">
              <div className="file-group-name">▾ {group.name}</div>
              {group.files.map((file) => (
                <button
                  key={file.id}
                  className={file.id === activeFile.id ? "file-item active" : "file-item"}
                  onClick={() => onSelectFile(file.id)}
                >
                  <span>{file.language === "csv" ? "▦" : "◇"}</span>
                  <span>{file.label}</span>
                </button>
              ))}
            </div>
          ))}
        </aside>
        <div className="file-preview">
          <div className="file-preview-tabs">
            <span className="file-tab active">{activeFile.label}</span>
          </div>
          <div className="file-preview-body">
            <div className="file-preview-meta">{activeFile.group}</div>
            <pre className="file-preview-code">
              <code>{activeFile.content}</code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
