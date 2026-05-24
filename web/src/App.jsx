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
  { key: "home", label: "Start" },
  { key: "explore", label: "Erkunden" },
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

      {state.loading ? <StatusPanel title="Katalog wird geladen" body="Lese Zusammenfassungen aus `loom_explore`..." /> : null}
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
        <span className="brand-sub">Datenkarten für große Datensätze</span>
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
  const topSteps = [
    {
      number: "1",
      title: "Installieren",
      detail: "Installiere Loom im aktuellen Projekt. Dafür brauchst du nur zwei Befehle.",
      lines: ["uv add loom-data", "uv run loom install"],
    },
    {
      number: "2",
      title: "Dateien ablegen",
      detail: "Lege echte Dateien in `loom/loom_raw/<workspace>/` ab. Im Beispiel unten verwenden wir nur eine `costs.csv`.",
      lines: ["mkdir -p loom/loom_raw/energy", "cp costs.csv loom/loom_raw/energy/"],
    },
    {
      number: "3",
      title: "scan + find",
      detail: "Nach dem Scan schreibst du keine Pfade von Hand, sondern fragst direkt im Chat – zum Beispiel nach den CAPEX von OCGT.",
      lines: ["loom scan energy", "loom find OCGT CAPEX"],
    },
  ];

  const bashSteps = [
    {
      command: "uv add loom-data",
      explanation: "Installiert Loom. Danach kannst du im aktuellen Projekt den Befehl `loom` verwenden.",
    },
    {
      command: "uv run loom install",
      explanation: "Initialisiert Loom. Im Projektverzeichnis wird ein Ordner `loom/` mit `loom_raw`, `loom_explore` und `.loom` angelegt.",
    },
    {
      command: "mkdir -p loom/loom_raw/energy",
      explanation: "Erstellt einen Arbeitsbereich namens `energy`. Hier kannst du alle Rohdateien zu einem Thema sammeln.",
    },
    {
      command: "cp costs.csv loom/loom_raw/energy/",
      explanation: "`costs.csv` ist ein echtes Beispiel. Du kannst sie dir als Kostentabelle mit Spalten wie `technology`, `year`, `region` und `capex_usd_per_kw` vorstellen.",
    },
  ];

  const chatMessages = [
    {
      role: "user",
      text: "Scanne bitte zuerst `energy` und schau nach, welche Daten etwas mit Stromerzeugungskosten zu tun haben.",
    },
    {
      role: "assistant",
      text: "Gern. Ich führe zuerst `loom scan energy` aus und schaue mir danach die erzeugten Zusammenfassungen und CSV-Karten an.",
    },
    {
      role: "assistant",
      text: "Ich habe eine Karte zur Datei `costs.csv` gefunden. Sie beschreibt Technologiekosten und enthält Felder wie `technology`, `year`, `region` und `capex_usd_per_kw`.",
    },
    {
      role: "user",
      text: "Dann such mir bitte die CAPEX für OCGT heraus.",
    },
    {
      role: "assistant",
      text: "Klar. Ich nutze zuerst Karten und Zusammenfassungen, um die richtige Datei zu finden, und lese dann die passenden OCGT-CAPEX-Werte aus `costs.csv` aus.",
    },
  ];

  return (
    <>
      <header className="hero hero-home hero-home-light">
        <div className="hero-copy-column">
          <p className="eyebrow">So funktioniert es</p>
          <h1>Ordne deine Daten zuerst – und nutze sie dann im Chat.</h1>
          <p className="hero-copy">
            Du legst deine Rohdateien ab, Loom erstellt Zusammenfassungen und einen Index. Danach kannst du im Chat direkt fragen, zum Beispiel: „Finde die CAPEX für OCGT“.
          </p>
          <p className="hero-copy hero-copy-compact">
            Im Grunde sind es nur 3 Schritte: <strong>Installieren</strong> → <strong>Dateien ablegen</strong> → <strong>scan + find</strong>
          </p>
          <div className="hero-cta-row">
            <button className="primary-cta" onClick={onOpenExplore}>Zur Übersicht</button>
            <span className="cta-hint">Erst ordnen, dann fragen</span>
          </div>
        </div>

        <div className="hero-summary panel">
          <div className="hero-summary-steps">
            {topSteps.map((step) => (
              <article key={step.number} className="hero-step-card">
                <span className="hero-step-number">{step.number}</span>
                <div>
                  <strong>{step.title}</strong>
                  <p>{step.detail}</p>
                  <pre>{step.lines.join("\n")}</pre>
                </div>
              </article>
            ))}
          </div>
          <div className="hero-visual-stats">
            <MetricCard label="Arbeitsbereiche" value={workspaceCount} />
            <MetricCard label="Datensätze" value={datasetCount} />
            <MetricCard label="CSV-Profile" value={csvProfileCount} />
          </div>
        </div>
      </header>

      <section className="home-stack">
        <section className="panel home-section">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Beispiele</p>
              <h2>Diese zwei Beispiele zeigen den typischen Ablauf</h2>
            </div>
          </div>
          <p className="hero-copy">
            Oben steht die Kurzfassung. Hier siehst du die Details: links die Befehle, rechts ein echtes Chat-Beispiel.
          </p>

          <div className="demo-grid">
            <article className="demo-card bash-demo">
              <div className="demo-header">
                <p className="eyebrow">Demo 1</p>
                <h3>Zuerst Bash: so legst du eine echte Datei Schritt für Schritt ab</h3>
              </div>
              <div className="terminal-window" aria-label="Bash-Demo">
                <div className="terminal-bar">
                  <span />
                  <span />
                  <span />
                </div>
                <div className="terminal-body">
                  {bashSteps.map((step) => (
                    <div key={step.command} className="terminal-step">
                      <pre className="terminal-command">$ {step.command}</pre>
                      <p className="terminal-explanation">{step.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </article>

            <article className="demo-card chat-demo">
              <div className="demo-header">
                <p className="eyebrow">Demo 2</p>
                <h3>Dann der Chat: du fragst direkt, statt Pfade von Hand zu schreiben</h3>
              </div>
              <div className="chat-window" aria-label="Chat-Demo">
                {chatMessages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={message.role === "user" ? "chat-bubble chat-user" : "chat-bubble chat-assistant"}
                  >
                    <span className="chat-role">{message.role === "user" ? "Du" : "Codex"}</span>
                    <p>{message.text}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="folder-layout-card">
            <div className="demo-header">
              <p className="eyebrow">Ordner</p>
              <h3>Nach der Installation sieht `loom/` ungefähr so aus</h3>
            </div>
            <div className="folder-layout-grid">
              <CodeBlock
                title="Projektstruktur"
                lines={[
                  "loom/",
                  "├── loom_raw/        # Hier liegen die Rohdateien",
                  "│   └── energy/",
                  "│       └── costs.csv",
                  "├── loom_explore/    # Hier landen Zusammenfassungen und Karten nach dem Scan",
                  "│   └── energy/",
                  "│       ├── overview.md",
                  "│       └── costs.csv.md",
                  "└── .loom/           # Interne Daten von Loom",
                ]}
              />
            </div>
          </div>
        </section>

        <section className="panel home-section">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Ablauf</p>
              <h2>Was Loom im Hintergrund macht</h2>
            </div>
          </div>
          <FlowAnimation />
          <div className="workflow-caption-grid">
            <p><strong>1.</strong> Du legst Rohdateien in einen Arbeitsbereich.</p>
            <p><strong>2.</strong> `loom scan` erzeugt Zusammenfassungen, Beschreibungen und CSV-Karten.</p>
            <p><strong>3.</strong> Danach stellst du im Chat direkt eine Frage, zum Beispiel zu OCGT-CAPEX.</p>
          </div>
        </section>
      </section>
    </>
  );
}

function ExploreHero({ workspaceCount, datasetCount, csvProfileCount }) {
  return (
    <header className="hero">
      <div>
        <p className="eyebrow">Loom Erkunden</p>
        <h1>Sieh dir erst die Übersicht an – und entscheide dann, welche Rohdatei du brauchst.</h1>
        <p className="hero-copy">
          Wähle links einen Arbeitsbereich und einen Datensatz, lies zuerst die Zusammenfassung und öffne dann die passenden Dateien.
        </p>
      </div>
      <div className="hero-stats">
        <MetricCard label="Arbeitsbereiche" value={workspaceCount} />
        <MetricCard label="Datensätze" value={datasetCount} />
        <MetricCard label="CSV-Profile" value={csvProfileCount} />
      </div>
    </header>
  );
}

function FlowAnimation() {
  return (
    <div className="flow-anim flow-anim-light" aria-label="Loom-Ablauf">
      <div className="flow-node flow-raw">
        <span className="flow-title">Rohdaten</span>
        <span className="flow-sub">`loom/loom_raw`</span>
      </div>
      <div className="flow-arrow" />
      <div className="flow-node flow-scan">
        <span className="flow-title">loom scan</span>
        <span className="flow-sub">profilieren + zusammenfassen</span>
      </div>
      <div className="flow-arrow" />
      <div className="flow-node flow-cards">
        <span className="flow-title">Karten</span>
        <span className="flow-sub">`loom/loom_explore`</span>
      </div>
      <div className="flow-arrow" />
      <div className="flow-node flow-get">
        <span className="flow-title">loom get</span>
        <span className="flow-sub">genaue Datei holen</span>
      </div>
      <div className="flow-spark" />
    </div>
  );
}

function CodeBlock({ title, lines }) {
  return (
    <section className="code-block">
      <div className="code-block-title">{title}</div>
      <pre className="code-block-pre">
        <code>{lines.join("\n")}</code>
      </pre>
    </section>
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
