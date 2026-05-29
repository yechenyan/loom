import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/$/, "");

const defaultState = {
  workspaces: [],
  selectedWorkspace: null,
  selectedDatasetPath: null,
  selectedRawPath: null,
  rawManifestByPath: null,
  rawLoading: false,
  rawError: null,
  rawOpen: false,
  rawObject: null,
  loading: true,
  error: null,
};

const NAV_ITEMS = [
  { key: "home", label: "首页" },
  { key: "explore", label: "探索数据" },
];

const AGENT_INSTALL_PROMPTS = [
  {
    key: "chatgpt",
    label: "ChatGPT",
    assistant: "ChatGPT",
  },
  {
    key: "claude",
    label: "Claude",
    assistant: "Claude",
  },
  {
    key: "cursor",
    label: "Cursor",
    assistant: "Cursor",
  },
];

const HOME_FLOW = [
  {
    step: "01",
    title: "整理原始数据",
    body: "把 CSV、目录说明和原始资料放进 `raw_data/<workspace>/...`，Loom 识别带 `loom.md` 的数据集根目录。",
  },
  {
    step: "02",
    title: "生成轻量数据卡",
    body: "`loom scan` 会生成 overview、CSV 摘要、字段画像和统计信息，让 AI 先看结构再决定下一步。",
  },
  {
    step: "03",
    title: "按需取回原始文件",
    body: "`loom ask` 和 `loom get` 会先检索卡片，再精确定位真正需要打开的原始数据文件。",
  },
];

const HOME_OUTPUTS = [
  {
    title: "给 AI 的入口更轻",
    body: "从直接打开大 CSV，变成先读 `overview.md` 和每个 CSV 卡片，减少无效上下文。",
  },
  {
    title: "问题定位更快",
    body: "AI 先知道哪个 workspace、哪个 dataset、哪张表更相关，再决定要不要继续取 raw file。",
  },
  {
    title: "团队可复用",
    body: "扫描结果写进 `loom/`，后来的同事或 agent 可以复用同一套摘要，而不是重新读一遍大文件。",
  },
];

const HOME_USE_CASES = [
  "分析师先问问题，再下钻到准确的原始表",
  "工程师写脚本前先确认字段和分布",
  "报告生成时避免把大文件整份塞给 AI",
  "多数据源项目里，为每个 workspace 留下可搜索的数据说明",
];

export default function App() {
  const [state, setState] = useState(defaultState);
  const [query, setQuery] = useState("");
  const [view, setView] = useState(getInitialView());
  const deferredQuery = useDeferredValue(query);
  const csvCardRefs = useRef(new Map());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch(buildApiUrl("/api/explore/workspaces"));
        if (!response.ok) {
          throw new Error(`Failed to load workspaces: ${response.status}`);
        }

        const payload = await response.json();
        if (cancelled) {
          return;
        }

        startTransition(() => {
          const firstWorkspace = payload.workspaces[0] ?? null;
          const firstDataset = firstWorkspace?.datasets?.[0]?.path ?? null;
          setState({
            workspaces: payload.workspaces,
            selectedWorkspace: firstWorkspace?.name ?? null,
            selectedDatasetPath: firstDataset,
            selectedRawPath: null,
            rawManifestByPath: null,
            rawLoading: false,
            rawError: null,
            rawOpen: false,
            rawObject: null,
            loading: false,
            error: null,
          });
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          loading: false,
          error: error instanceof Error ? error.message : "Unbekannter Fehler",
        }));
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    function onHashChange() {
      setView(getInitialView());
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const selectedWorkspace = useMemo(
    () => state.workspaces.find((workspace) => workspace.name === state.selectedWorkspace) ?? null,
    [state.workspaces, state.selectedWorkspace],
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
      const haystacks = [
        dataset.name,
        dataset.path,
        dataset.source?.summary ?? "",
        ...(dataset.csv_files ?? []).map((entry) => `${entry.file_name} ${entry.summary ?? ""}`),
      ];
      return haystacks.some((item) => item.toLowerCase().includes(needle));
    });
  }, [selectedWorkspace, deferredQuery]);

  const selectedDataset =
    filteredDatasets.find((dataset) => dataset.path === state.selectedDatasetPath) ??
    filteredDatasets[0] ??
    null;

  useEffect(() => {
    if (!selectedDataset && filteredDatasets.length === 0) {
      return;
    }

    if (selectedDataset) {
      return;
    }

    setState((current) => ({
      ...current,
      selectedDatasetPath: filteredDatasets[0]?.path ?? null,
    }));
  }, [filteredDatasets, selectedDataset]);

  useEffect(() => {
    if (!state.selectedWorkspace) {
      return;
    }

    let cancelled = false;

    async function loadRawManifest() {
      setState((current) => ({
        ...current,
        rawLoading: true,
        rawError: null,
        rawManifestByPath: null,
      }));
      try {
        const response = await fetch(buildApiUrl(`/api/workspaces/${encodeURIComponent(state.selectedWorkspace)}/raw-manifest`));
        if (!response.ok) {
          throw new Error(`Failed to load raw manifest: ${response.status}`);
        }
        const payload = await response.json();
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setState((current) => ({
            ...current,
            rawLoading: false,
            rawError: null,
            rawManifestByPath: payload.raw_manifest ?? {},
          }));
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          rawLoading: false,
          rawManifestByPath: null,
          rawError: error instanceof Error ? error.message : "Unbekannter Fehler",
        }));
      }
    }

    loadRawManifest();
    return () => {
      cancelled = true;
    };
  }, [state.selectedWorkspace]);

  const datasetRawFiles = useMemo(() => {
    if (!selectedDataset || !state.rawManifestByPath) {
      return [];
    }
    const prefix = selectedDataset.path ? `${selectedDataset.path.replace(/\/$/, "")}/` : "";
    const entries = Object.entries(state.rawManifestByPath)
      .filter(([path]) => (prefix ? path.startsWith(prefix) : true))
      .map(([path, meta]) => ({
        path,
        sha256: meta.sha256,
        size_bytes: meta.size_bytes,
      }));
    entries.sort((a, b) => a.path.localeCompare(b.path));
    return entries;
  }, [selectedDataset, state.rawManifestByPath]);

  const relatedExploreFiles = useMemo(() => {
    if (!selectedDataset) {
      return [];
    }
    const items = [];
    items.push({
      kind: "explore",
      label: "overview.md (Zusammenfassung)",
      action: { type: "scroll", target: "dataset-overview" },
    });

    for (const csvProfile of selectedDataset.csv_profiles ?? []) {
      if (!csvProfile?.file_name) {
        continue;
      }
      items.push({
        kind: "explore",
        label: csvProfile.file_name,
        action: { type: "scrollCsv", target: csvProfile.file_name },
      });
    }

    if ((selectedDataset.csv_profiles ?? []).length) {
      items.push({
        kind: "explore",
        label: "Alle CSV-Profile (Karten)",
        action: { type: "scroll", target: "dataset-csv-profiles" },
      });
    }

    return items;
  }, [selectedDataset]);

  const relatedFromRaw = useMemo(() => {
    if (!selectedDataset || !state.selectedRawPath) {
      return null;
    }

    const fileName = basename(state.selectedRawPath);
    const hasCsvProfileMatch = (selectedDataset.csv_profiles ?? []).some((profile) => profile?.file_name === fileName);

    return {
      fileName,
      hasCsvProfileMatch,
    };
  }, [selectedDataset, state.selectedRawPath]);

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <TopNav
        view={view}
        onNavigate={(nextView) => {
          setView(nextView);
          window.location.hash = nextView === "explore" ? "#/explore" : "#/";
        }}
      />

      {view === "home" ? (
        <HomePage
          workspaceCount={state.workspaces.length}
          datasetCount={state.workspaces.reduce((count, workspace) => count + workspace.dataset_count, 0)}
          csvProfileCount={state.workspaces.reduce(
            (count, workspace) =>
              count + workspace.datasets.reduce((datasetCount, dataset) => datasetCount + dataset.csv_count, 0),
            0,
          )}
          onOpenExplore={() => {
            setView("explore");
            window.location.hash = "#/explore";
          }}
        />
      ) : (
        <ExploreHero
          workspaceCount={state.workspaces.length}
          datasetCount={state.workspaces.reduce((count, workspace) => count + workspace.dataset_count, 0)}
          csvProfileCount={state.workspaces.reduce(
            (count, workspace) =>
              count + workspace.datasets.reduce((datasetCount, dataset) => datasetCount + dataset.csv_count, 0),
            0,
          )}
        />
      )}

      {state.loading ? <StatusPanel title="Katalog wird geladen" body="Lese Zusammenfassungen aus `loom`..." /> : null}
      {state.error ? <StatusPanel title="Daten konnten nicht geladen werden" body={state.error} variant="error" /> : null}

      {!state.loading && !state.error && view === "explore" ? (
        <main className="dashboard">
          <aside className="sidebar">
            <div className="sidebar-card workspace-list">
              <p className="sidebar-title">Arbeitsbereich</p>
              {state.workspaces.map((workspace) => (
                <button
                  key={workspace.name}
                  className={workspace.name === state.selectedWorkspace ? "workspace-pill active" : "workspace-pill"}
                  onClick={() =>
                    setState((current) => ({
                      ...current,
                      selectedWorkspace: workspace.name,
                      selectedDatasetPath: workspace.datasets[0]?.path ?? null,
                      selectedRawPath: null,
                      rawOpen: false,
                      rawObject: null,
                    }))
                  }
                >
                  <span>{workspace.name}</span>
                  <small>{workspace.dataset_count} Datensätze</small>
                </button>
              ))}
            </div>

            <div className="sidebar-card dataset-list">
              <p className="sidebar-title">Datensatz</p>
              <label className="search-label" htmlFor="dataset-search">
                Datensätze durchsuchen
              </label>
              <input
                id="dataset-search"
                className="search-input"
                placeholder="technology, plants, capacity..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              {filteredDatasets.map((dataset) => (
                <button
                  key={dataset.path}
                  className={dataset.path === selectedDataset?.path ? "dataset-item active" : "dataset-item"}
                  onClick={() =>
                    setState((current) => ({
                      ...current,
                      selectedDatasetPath: dataset.path,
                      selectedRawPath: null,
                      rawOpen: false,
                      rawObject: null,
                    }))
                  }
                >
                  <strong>{dataset.name}</strong>
                  <span>{dataset.total_row_count.toLocaleString()} rows</span>
                  <small>{dataset.csv_count} CSV-Dateien</small>
                </button>
              ))}
              {filteredDatasets.length === 0 ? <p className="empty-copy">Keine Datensätze passen zu dieser Suche.</p> : null}
            </div>

            <div className="sidebar-card file-list">
              <p className="sidebar-title">Dateien</p>
              {selectedDataset ? (
                <>
                  <FileSection
                    title="Übersichtsdateien"
                    items={relatedExploreFiles}
                    onClickItem={(item) => {
                      if (item.action?.type === "scroll") {
                        document.getElementById(item.action.target)?.scrollIntoView({ behavior: "smooth", block: "start" });
                      }
                      if (item.action?.type === "scrollCsv") {
                        const node = csvCardRefs.current.get(item.action.target);
                        node?.scrollIntoView({ behavior: "smooth", block: "start" });
                        node?.classList?.add?.("flash-outline");
                        window.setTimeout(() => node?.classList?.remove?.("flash-outline"), 1200);
                      }
                    }}
                  />
                  <FileSection
                    title="Rohdaten"
                    loading={state.rawLoading}
                    error={state.rawError}
                    items={datasetRawFiles.map((entry) => ({
                      kind: "raw",
                      label: entry.path,
                      meta: entry,
                    }))}
                    emptyCopy={state.rawLoading ? null : "Für diesen Datensatz sind noch keine Rohdateien zugeordnet."}
                    onClickItem={async (item) => {
                      if (item.kind !== "raw") {
                        return;
                      }
                      const rawMeta = item.meta;
                      if (!rawMeta) {
                        return;
                      }
                      setState((current) => ({
                        ...current,
                        selectedRawPath: rawMeta.path,
                        rawOpen: true,
                        rawObject: null,
                        rawError: null,
                      }));

                      if (rawMeta.size_bytes > 1_500_000) {
                        setState((current) => ({
                          ...current,
                          rawObject: {
                            tooLarge: true,
                            path: rawMeta.path,
                            size_bytes: rawMeta.size_bytes,
                            sha256: rawMeta.sha256,
                          },
                        }));
                        return;
                      }

                      try {
                        const response = await fetch(buildApiUrl(`/api/raw/objects/${encodeURIComponent(rawMeta.sha256)}`));
                        if (!response.ok) {
                          throw new Error(`Failed to load raw object: ${response.status}`);
                        }
                        const payload = await response.json();
                        const decoded = decodeBase64ToText(payload.content_base64 ?? "");
                        setState((current) => ({
                          ...current,
                          rawObject: {
                            tooLarge: false,
                            path: rawMeta.path,
                            size_bytes: rawMeta.size_bytes,
                            sha256: rawMeta.sha256,
                            text: decoded,
                          },
                        }));
                      } catch (error) {
                        setState((current) => ({
                          ...current,
                          rawError: error instanceof Error ? error.message : "Unbekannter Fehler",
                        }));
                      }
                    }}
                  />
                </>
              ) : (
                <p className="empty-copy">Wähle einen Datensatz, um Dateien und Rohdaten zu sehen.</p>
              )}
            </div>
          </aside>

          <section className="content">
            {selectedWorkspace ? <WorkspaceSummary workspace={selectedWorkspace} /> : null}
            {selectedDataset ? (
              <DatasetDetail
                dataset={selectedDataset}
                rawOpen={state.rawOpen}
                rawObject={state.rawObject}
                rawError={state.rawError}
                relatedFromRaw={relatedFromRaw}
                onCloseRaw={() =>
                  setState((current) => ({
                    ...current,
                    rawOpen: false,
                    selectedRawPath: null,
                    rawObject: null,
                    rawError: null,
                  }))
                }
                onJumpToCsv={(fileName) => {
                  const node = csvCardRefs.current.get(fileName);
                  node?.scrollIntoView({ behavior: "smooth", block: "start" });
                  node?.classList?.add?.("flash-outline");
                  window.setTimeout(() => node?.classList?.remove?.("flash-outline"), 1200);
                }}
                onJumpToOverview={() => {
                  document.getElementById("dataset-overview")?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
                registerCsvCardRef={(fileName, node) => {
                  if (!fileName) {
                    return;
                  }
                  if (node) {
                    csvCardRefs.current.set(fileName, node);
                  } else {
                    csvCardRefs.current.delete(fileName);
                  }
                }}
              />
            ) : null}
          </section>
        </main>
      ) : null}
    </div>
  );
}

function buildApiUrl(path) {
  return `${apiBaseUrl}${path}`;
}

function getInitialView() {
  const hash = (window.location.hash ?? "").toLowerCase();
  if (hash.startsWith("#/explore")) {
    return "explore";
  }
  return "home";
}

function TopNav({ view, onNavigate }) {
  return (
    <header className="top-nav">
      <div className="brand">
        <span className="brand-mark">loom</span>
        <span className="brand-sub">让 AI 先读数据卡，再按需读取原始文件</span>
      </div>
      <nav className="nav-tabs" aria-label="Hauptnavigation">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            className={item.key === view ? "nav-tab active" : "nav-tab"}
            onClick={() => onNavigate(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}

function HomePage({ workspaceCount, datasetCount, csvProfileCount, onOpenExplore }) {
  const [selectedAgent, setSelectedAgent] = useState(AGENT_INSTALL_PROMPTS[0].key);
  const [copiedAgent, setCopiedAgent] = useState(null);
  const [includeTutorial, setIncludeTutorial] = useState(true);
  const [selectedFile, setSelectedFile] = useState("overview.md");
  const activePrompt = AGENT_INSTALL_PROMPTS.find((item) => item.key === selectedAgent) ?? AGENT_INSTALL_PROMPTS[0];
  const installPrompt = buildInstallPrompt(activePrompt.assistant, includeTutorial);
  const handleCopy = async () => {
    if (!navigator?.clipboard?.writeText) {
      return;
    }
    await navigator.clipboard.writeText(installPrompt);
    setCopiedAgent(activePrompt.key);
    window.setTimeout(() => {
      setCopiedAgent((current) => (current === activePrompt.key ? null : current));
    }, 1800);
  };

  const copyText = async (text) => {
    if (!navigator?.clipboard?.writeText) {
      return;
    }
    await navigator.clipboard.writeText(text);
  };

  return (
    <>
      <section className="home-reboot">
        <header className="home-hero-shell panel">
          <div className="home-hero-copy">
            <p className="eyebrow">AI Data Workflow</p>
            <h1>把大数据集变成 AI 看得懂、找得到、按需再深入的工作流。</h1>
            <p className="home-hero-lead">
              Loom 会先把原始数据扫描成轻量数据卡，让 AI 优先理解数据结构、主题和关键文件，只有在真的需要时才读取原始 CSV。
            </p>
            <div className="hero-cta-row">
              <button className="primary-cta" onClick={onOpenExplore}>查看真实数据卡</button>
              <span className="cta-hint">适合先检索、后取数的 AI 数据分析流程</span>
            </div>
            <div className="home-stage-stats">
              <MetricCard label="工作区" value={workspaceCount} />
              <MetricCard label="数据集" value={datasetCount} />
              <MetricCard label="CSV 卡片" value={csvProfileCount} />
            </div>
            <div className="home-command-strip">
              <div className="home-command-card">
                <span>1. 扫描</span>
                <code>loom scan raw_data/energy to energy</code>
              </div>
              <div className="home-command-card">
                <span>2. 提问</span>
                <code>loom ask OCGT 的成本是多少</code>
              </div>
              <div className="home-command-card">
                <span>3. 深挖</span>
                <code>loom get energy/technology-data/costs.csv</code>
              </div>
            </div>
          </div>

          <div className="home-chat-stage home-chat-stage-preserved">
            <div className="home-chat-head">
              <p className="eyebrow">轻松开始</p>
              <h2>轻松开始</h2>
            </div>
            <div className="chat-toolbar">
              <div className="agent-tabs" role="tablist" aria-label="AI Agent">
                {AGENT_INSTALL_PROMPTS.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    role="tab"
                    aria-selected={item.key === activePrompt.key}
                    className={item.key === activePrompt.key ? "agent-tab active" : "agent-tab"}
                    onClick={() => setSelectedAgent(item.key)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <label className="tutorial-toggle">
                <input
                  type="checkbox"
                  checked={includeTutorial}
                  onChange={(event) => setIncludeTutorial(event.target.checked)}
                />
                <span>安装时启用教学</span>
              </label>
            </div>
            <div className="chat-window home-chat-window" aria-label={`${activePrompt.assistant} onboarding chat`}>
              <div className="chat-shell-top">
                <div className="chat-shell-meta">
                  <span className="chat-shell-dot" />
                  <strong>{activePrompt.label}</strong>
                  <span>tutorial workspace</span>
                </div>
                <div className="chat-shell-badge">Ready</div>
              </div>
              <div className="chat-thread">
                <ChatStepLabel text="第一步-安装：把下面话直接粘贴给 AI Agent。" />
                <ChatSnippet role="user" text={installPrompt} onCopy={() => handleCopy()} />
                <ChatSnippet
                  role="assistant"
                  text={`我会先检查并安装 uv，然后安装 loom-data，运行 loom init，并按 ${activePrompt.assistant} 的方式完成初始化${includeTutorial ? "，同时安装 tutorial dataset" : ""}。`}
                />
                <ChatDivider />
                <ChatStepLabel text="第 2 步：让 Agent 扫描 tutorial dataset 并创建数据卡片。" />
                <ChatSnippet
                  role="user"
                  text="loom scan loom/loom_raw/tutorial to tutorial"
                  onCopy={() => copyText("loom scan loom/loom_raw/tutorial to tutorial")}
                />
                <ChatSnippet
                  role="assistant"
                  text="我会扫描 tutorial dataset，生成 overview、CSV 字段画像和可供后续检索的数据卡片。"
                />
                <ChatDivider />
                <ChatStepLabel text="第 3 步：直接基于 tutorial dataset 提问。" />
                <ChatSnippet role="user" text="loom ask OCGT 的成本是多少" onCopy={() => copyText("loom ask OCGT 的成本是多少")} />
                <ChatSnippet
                  role="assistant"
                  text="我会先读取 tutorial workspace 的卡片和摘要，再定位 OCGT 对应的成本数据。拿到目标文件后，你也可以直接在代码里继续处理它。"
                  code={`import loom\n\ndata = loom.get("tutorial/costs.csv")\nprint(data)`}
                />
              </div>
            </div>
            <FileWorkbench selectedFile={selectedFile} onSelectFile={setSelectedFile} />
          </div>
        </header>

        <section className="home-story-grid">
          <article className="panel home-problem-card">
            <p className="eyebrow">一眼看懂</p>
            <h2>Loom 是什么</h2>
            <p>
              Loom 是给 AI 用的数据入口层。它不替代原始数据，也不做 BI；它做的是先把大体量原始资料整理成可搜索、可复用的数据卡，让 agent 少走弯路。
            </p>
          </article>
          <article className="panel home-problem-card">
            <p className="eyebrow">为什么需要</p>
            <h2>大文件不该成为 AI 的默认起点</h2>
            <p>
              直接把几万行 CSV 丢给 AI，通常既慢又贵，也难复用。Loom 把“先理解数据，再打开原文”做成默认流程，让每次问答和分析都更稳。
            </p>
          </article>
        </section>

        <section className="panel home-flow-panel">
          <div className="home-section-head">
            <p className="eyebrow">工作方式</p>
            <h2>先扫描，再检索，最后按需取数</h2>
          </div>
          <div className="home-flow-grid">
            {HOME_FLOW.map((item) => (
              <article key={item.step} className="home-flow-card">
                <span className="home-flow-step">{item.step}</span>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="home-story-grid">
          <article className="panel home-output-card">
            <div className="home-section-head">
              <p className="eyebrow">扫描后会得到什么</p>
              <h2>不是一句摘要，而是一套可继续工作的上下文</h2>
            </div>
            <div className="home-output-list">
              {HOME_OUTPUTS.map((item) => (
                <div key={item.title} className="home-output-item">
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="panel home-use-case-card">
            <div className="home-section-head">
              <p className="eyebrow">适用场景</p>
              <h2>什么时候最有价值</h2>
            </div>
            <div className="home-use-case-list">
              {HOME_USE_CASES.map((item) => (
                <div key={item} className="home-use-case-item">
                  <span className="home-use-case-dot" />
                  <p>{item}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      </section>
    </>
  );
}

function ChatStepLabel({ text }) {
  return <div className="chat-step-label">{text}</div>;
}

function ChatDivider() {
  return <div className="chat-divider" aria-hidden="true" />;
}

function ChatSnippet({ role, text, onCopy, code }) {
  const isUser = role === "user";
  return (
    <div className={isUser ? "chat-row chat-row-user" : "chat-row chat-row-assistant"}>
      <div className={isUser ? "chat-avatar chat-avatar-user" : "chat-avatar chat-avatar-assistant"}>
        {isUser ? "U" : "A"}
      </div>
      <div className={isUser ? "chat-bubble chat-user" : "chat-bubble chat-assistant"}>
        <div className="chat-bubble-top">
          <span className="chat-role">{isUser ? "User" : "Agent"}</span>
          {isUser && onCopy ? (
            <button type="button" className="message-copy-button" onClick={onCopy}>
              Copy
            </button>
          ) : null}
        </div>
        <p>{text}</p>
        {code ? (
          <pre className="chat-code-block">
            <code>{code}</code>
          </pre>
        ) : null}
      </div>
    </div>
  );
}

const TUTORIAL_FILES = [
  {
    id: "overview.md",
    label: "overview.md",
    group: "tutorial",
    language: "md",
    content: `# tutorial

本工作区包含 tutorial dataset 的摘要卡片。

- 主题：发电技术成本
- 关键文件：costs.csv
- 用途：先给 AI 一个轻量入口，再按需读取原始数据
`,
  },
  {
    id: "costs.csv.md",
    label: "costs.csv.md",
    group: "tutorial",
    language: "md",
    content: `# costs.csv

## Summary
- rows: 128
- columns: technology, year, region, capex_usd_per_kw
- focus: OCGT, CCGT, solar, wind

## Quick read
这个卡片告诉 AI：哪几列重要、值分布大概是什么、应先去哪里找成本数据。
`,
  },
  {
    id: "costs.csv",
    label: "costs.csv",
    group: "raw_data/tutorial",
    language: "csv",
    content: `technology,year,region,capex_usd_per_kw
OCGT,2023,Global,850
CCGT,2023,Global,1100
Solar PV,2023,Global,700
Wind Onshore,2023,Global,1350
`,
  },
  {
    id: "loom.md",
    label: "loom.md",
    group: "raw_data/tutorial",
    language: "md",
    content: `# tutorial dataset

这个目录表示一个教学数据集根目录。
其中的 CSV 会被 Loom 扫描，并在 loom_explore/tutorial 下生成数据卡片。
`,
  },
];

function FileWorkbench({ selectedFile, onSelectFile }) {
  const activeFile = TUTORIAL_FILES.find((file) => file.id === selectedFile) ?? TUTORIAL_FILES[0];
  const groups = [
    { name: "loom/tutorial", files: TUTORIAL_FILES.filter((file) => file.group === "tutorial") },
    { name: "raw_data/tutorial", files: TUTORIAL_FILES.filter((file) => file.group === "raw_data/tutorial") },
  ];

  return (
    <section className="file-workbench">
      <div className="file-workbench-head">
        <div>
          <p className="eyebrow">文件结构</p>
          <h3>安装教学数据后会生成这些文件</h3>
        </div>
      </div>
      <div className="file-workbench-shell">
        <aside className="file-sidebar">
          <div className="file-sidebar-title">EXPLORER</div>
          {groups.map((group) => (
            <div key={group.name} className="file-group">
              <div className="file-group-name">
                <span className="file-group-chevron">▾</span>
                <span>{group.name}</span>
              </div>
              {group.files.map((file) => (
                <button
                  key={file.id}
                  type="button"
                  className={file.id === activeFile.id ? "file-item active" : "file-item"}
                  onClick={() => onSelectFile(file.id)}
                >
                  <span className="file-item-icon">{file.language === "csv" ? "▦" : "◇"}</span>
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

function buildInstallPrompt(assistant, includeTutorial) {
  return `请在当前项目里帮我安装 Loom：先确保 \`uv\` 可用，再运行 \`uv add loom-data\` 和 \`uv run loom init\`；初始化时请选择 \`${assistant}\`，workspace 用默认值，${includeTutorial ? "安装 tutorial dataset" : "不要安装 tutorial dataset"}，最后告诉我 \`loom/\` 是否创建成功。`;
}

function ExploreHero({ workspaceCount, datasetCount, csvProfileCount }) {
  return (
    <header className="hero">
      <div>
        <p className="eyebrow">探索数据</p>
        <h1>先看摘要和卡片，再决定要打开哪份原始数据。</h1>
        <p className="hero-copy">
          左侧选择 workspace 和 dataset，先读 overview 与 CSV 卡片，再按需打开真正相关的 raw file。
        </p>
      </div>
      <div className="hero-stats">
        <MetricCard label="工作区" value={workspaceCount} />
        <MetricCard label="数据集" value={datasetCount} />
        <MetricCard label="CSV 卡片" value={csvProfileCount} />
      </div>
    </header>
  );
}

function WorkspaceSummary({ workspace }) {
  return (
    <section className="panel workspace-summary">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Arbeitsbereich</p>
          <h2>{workspace.name}</h2>
        </div>
        <div className="panel-metrics">
          <MetricCard label="Datensätze" value={workspace.dataset_count} compact />
          <MetricCard
            label="Zeilen"
            value={workspace.datasets
              .reduce((count, dataset) => count + dataset.total_row_count, 0)
              .toLocaleString("de-DE")}
            compact
          />
        </div>
      </div>
      <MarkdownBlock markdown={workspace.readme_markdown} />
    </section>
  );
}

function DatasetDetail({
  dataset,
  rawOpen,
  rawObject,
  rawError,
  relatedFromRaw,
  onCloseRaw,
  onJumpToCsv,
  onJumpToOverview,
  registerCsvCardRef,
}) {
  return (
    <section className="panel dataset-detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Datensatz</p>
          <h2>{dataset.name}</h2>
          <p className="dataset-path">{dataset.path}</p>
        </div>
        <div className="panel-metrics">
          <MetricCard label="CSV-Dateien" value={dataset.csv_count} compact />
          <MetricCard label="Zeilen" value={dataset.total_row_count.toLocaleString("de-DE")} compact />
        </div>
      </div>

      <div className="source-grid">
        <InfoCard title="Quellen-Zusammenfassung" body={dataset.source?.summary || "Keine Quellen-Zusammenfassung vorhanden."} />
        <InfoCard title="Quell-URL" body={dataset.source?.url || "Keine Quell-URL angegeben."} />
        <InfoCard title="Lizenz" body={dataset.source?.license || "Keine Lizenz erfasst."} />
      </div>

      <div className="markdown-panel">
        <h3 id="dataset-overview">Überblick</h3>
        <MarkdownBlock markdown={dataset.overview_markdown} />
      </div>

      {rawOpen ? (
        <RawViewer
          rawObject={rawObject}
          rawError={rawError}
          relatedFromRaw={relatedFromRaw}
          onClose={onCloseRaw}
          onJumpToCsv={onJumpToCsv}
          onJumpToOverview={onJumpToOverview}
        />
      ) : null}

      <div className="csv-grid" id="dataset-csv-profiles">
        {dataset.csv_profiles.map((csvProfile) => (
          <CsvProfileCard
            key={csvProfile.file_name}
            csvProfile={csvProfile}
            registerRef={registerCsvCardRef}
          />
        ))}
      </div>
    </section>
  );
}

function CsvProfileCard({ csvProfile, registerRef }) {
  const numericColumns = csvProfile.columns.filter((column) => column.numeric_stats);
  const topValueColumns = csvProfile.columns.filter((column) => Array.isArray(column.top_values) && column.top_values.length);

  return (
    <article
      className="csv-card"
      ref={(node) => registerRef?.(csvProfile.file_name, node)}
      id={`csv-${cssEscape(csvProfile.file_name)}`}
    >
      <div className="csv-card-header">
        <div>
          <h3>{csvProfile.file_name}</h3>
          <p>
            {csvProfile.row_count.toLocaleString("de-DE")} Zeilen · {csvProfile.columns.length} Spalten
          </p>
        </div>
        <span className="csv-size">{formatBytes(csvProfile.file_size_bytes)}</span>
      </div>

      <section className="subpanel">
        <h4>Spaltenstruktur</h4>
        <div className="chip-row">
          {csvProfile.columns.map((column) => (
            <span key={column.name || "(blank)"} className="column-chip">
              {column.name || "(leer)"}
            </span>
          ))}
        </div>
      </section>

      {numericColumns.length ? (
        <section className="subpanel">
          <h4>Zahlenbereiche</h4>
          <div className="stats-grid">
            {numericColumns.slice(0, 6).map((column) => (
              <div key={column.name} className="stat-box">
                <strong>{column.name}</strong>
                <span>Min {formatNumber(column.numeric_stats.min)}</span>
                <span>Max {formatNumber(column.numeric_stats.max)}</span>
                <span>Mittel {formatNumber(column.numeric_stats.mean)}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {topValueColumns.length ? (
        <section className="subpanel">
          <h4>Häufigste Kategorien</h4>
          <div className="top-values-list">
            {topValueColumns.slice(0, 3).map((column) => (
              <div key={column.name} className="top-values-card">
                <strong>{column.name}</strong>
                {column.top_values.slice(0, 4).map((valueEntry) => (
                  <div key={`${column.name}-${valueEntry.value}`} className="top-values-row">
                    <span>{String(valueEntry.value)}</span>
                    <span>{valueEntry.count}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <div className="samples-grid">
        <SampleTable title="Anfang" rows={csvProfile.head ?? []} />
        <SampleTable title="Ende" rows={csvProfile.tail ?? []} />
      </div>
    </article>
  );
}

function RawViewer({ rawObject, rawError, relatedFromRaw, onClose, onJumpToCsv, onJumpToOverview }) {
  return (
    <section className="subpanel raw-viewer">
      <div className="raw-viewer-header">
        <h4>Rohdaten</h4>
        <button className="raw-close" onClick={onClose}>Schließen</button>
      </div>

      {rawError ? <p className="empty-copy">{rawError}</p> : null}
      {!rawError && !rawObject ? <p className="empty-copy">Wähle links eine Rohdatei aus, um sie hier zu öffnen.</p> : null}

      {rawObject ? (
        <>
          <div className="raw-meta">
            <span className="raw-path">{rawObject.path}</span>
            <span className="raw-size">{formatBytes(rawObject.size_bytes)}</span>
          </div>

          <div className="raw-related">
            <span className="raw-related-label">Verknüpft</span>
            <button className="linkish" onClick={() => onJumpToOverview?.()}>
              Überblick
            </button>
            {relatedFromRaw?.hasCsvProfileMatch ? (
              <button className="linkish" onClick={() => onJumpToCsv?.(relatedFromRaw.fileName)}>
                CSV-Profil
              </button>
            ) : null}
          </div>

          {rawObject.tooLarge ? (
            <div className="raw-too-large">
              <p className="empty-copy">
                Diese Rohdatei ist groß. Hole sie lokal mit <code>loom get {rawObject.path}</code>.
              </p>
              <button className="linkish" onClick={() => onJumpToCsv?.(basename(rawObject.path))}>
                Zum passenden CSV-Profil springen
              </button>
            </div>
          ) : (
            <>
              <div className="raw-actions">
                <button className="linkish" onClick={() => onJumpToCsv?.(basename(rawObject.path))}>
                  Zum passenden CSV-Profil springen
                </button>
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

function FileSection({ title, items, onClickItem, loading = false, error = null, emptyCopy = null }) {
  return (
    <section className="file-section">
      <div className="file-section-title">
        <span>{title}</span>
        {loading ? <small>Lädt…</small> : null}
      </div>
      {error ? <p className="empty-copy">{error}</p> : null}
      {!error && items.length === 0 && emptyCopy ? <p className="empty-copy">{emptyCopy}</p> : null}
      <div className="file-items">
        {items.map((item) => (
          <button key={`${title}-${item.label}`} className="file-item" onClick={() => onClickItem?.(item)}>
            <span className="file-item-label">{item.label}</span>
            {item.kind === "raw" && item.meta ? (
              <span className="file-item-meta">{formatBytes(item.meta.size_bytes)}</span>
            ) : null}
          </button>
        ))}
      </div>
    </section>
  );
}

function SampleTable({ title, rows }) {
  const columnNames = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <section className="subpanel sample-table">
      <h4>{title}</h4>
      {rows.length === 0 ? (
        <p className="empty-copy">Keine Beispielzeilen vorhanden.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columnNames.map((columnName) => (
                  <th key={columnName}>{columnName || "(leer)"}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${title}-${index}`}>
                  {columnNames.map((columnName) => (
                    <td key={`${title}-${index}-${columnName}`}>{String(row[columnName] ?? "")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function MetricCard({ label, value, compact = false }) {
  return (
    <div className={compact ? "metric-card compact" : "metric-card"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function InfoCard({ title, body }) {
  return (
    <div className="info-card">
      <span>{title}</span>
      <p>{body}</p>
    </div>
  );
}

function StatusPanel({ title, body, variant = "normal" }) {
  return (
    <section className={variant === "error" ? "status-panel error" : "status-panel"}>
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}

function MarkdownBlock({ markdown }) {
  const lines = markdown
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line, index, array) => !(line === "" && array[index - 1] === ""));

  return (
    <div className="markdown-block">
      {lines.map((line, index) => {
        if (line.startsWith("# ")) {
          return <h3 key={index}>{line.slice(2)}</h3>;
        }
        if (line.startsWith("## ")) {
          return <h4 key={index}>{line.slice(3)}</h4>;
        }
        if (line.startsWith("- ")) {
          return <p key={index} className="markdown-bullet">{line}</p>;
        }
        if (!line) {
          return <div key={index} className="markdown-spacer" />;
        }
        return <p key={index}>{line}</p>;
      })}
    </div>
  );
}

function formatBytes(bytes) {
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

function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  if (Math.abs(value) >= 1000) {
    return value.toLocaleString("de-DE", { maximumFractionDigits: 1 });
  }
  return value.toLocaleString("de-DE", { maximumFractionDigits: 3 });
}

function decodeBase64ToText(value) {
  if (!value) {
    return "";
  }
  const binary = atob(value);
  const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
  try {
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  } catch {
    return Array.from(bytes)
      .map((byte) => (byte >= 32 && byte < 127 ? String.fromCharCode(byte) : "�"))
      .join("");
  }
}

function basename(path) {
  const parts = String(path ?? "").split("/");
  return parts[parts.length - 1] || "";
}

function cssEscape(value) {
  return String(value ?? "").replace(/[^a-zA-Z0-9_-]/g, "_");
}
