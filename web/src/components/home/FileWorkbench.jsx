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
        <aside className="workbench-sidebar">
          <div className="workbench-sidebar-title">EXPLORER</div>
          {groups.map((group) => (
            <div key={group.name} className="file-group">
              <div className="file-group-name">▾ {group.name}</div>
              {group.files.map((file) => (
                <button
                  key={file.id}
                  className={file.id === activeFile.id ? "workbench-file-item active" : "workbench-file-item"}
                  onClick={() => onSelectFile(file.id)}
                >
                  <span>{file.language === "csv" ? "▦" : "◇"}</span>
                  <span>{file.label}</span>
                </button>
              ))}
            </div>
          ))}
        </aside>
        <div className="workbench-preview">
          <div className="workbench-preview-tabs">
            <span className="workbench-file-tab active">{activeFile.label}</span>
          </div>
          <div className="workbench-preview-body">
            <div className="workbench-preview-meta">{activeFile.group}</div>
            <pre className="workbench-preview-code">
              <code>{activeFile.content}</code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
