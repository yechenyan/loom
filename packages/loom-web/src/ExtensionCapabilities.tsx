import { useI18n, type Locale } from "./i18n";

type CapabilityCopy = {
  kicker: string;
  title: string;
  body: string;
  loadersTitle: string;
  loadersBody: string;
  loaderExamples: string[];
  loaderItems: string[];
  pipelineTitle: string;
  pipelineBody: string;
  pipelineSpotlight: { title: string; body: string };
  pipelineExamples: string[];
  pipelineItems: { label: string; href?: string }[];
};

const capabilityCopy = {
  en: {
    kicker: "Extensible by design",
    title: "Loom can grow in two directions.",
    body: "The core flow stays the same: understand sources, create cards, then move data where the task needs it.",
    loadersTitle: "More loaders",
    loadersBody: "Add loaders for more file formats, APIs, online datasets, and project-specific sources.",
    loaderExamples: [
      "CSV/table loaders read fields, units, ranges, samples, and table structure.",
      "Document loaders extract tables, figures, methods, definitions, and citations from PDFs or reports.",
      "API and online-data loaders understand endpoints, query parameters, update cadence, and access rules.",
    ],
    loaderItems: ["CSV and tables", "PDF and documents", "Images", "APIs", "Online datasets"],
    pipelineTitle: "Pipelines",
    pipelineBody:
      "Pipeline hooks can run after scan, review, confirm, or push. For example, the push step can send curated data and metadata to an external platform while Loom keeps the local cards as the index.",
    pipelineExamples: [
      "sync reviewed energy datasets to Open Energy Platform during push",
      "publish reusable dataset cards or artifacts to Hugging Face",
      "send cleaned data to a team warehouse or project API",
    ],
    pipelineSpotlight: {
      title: "Open Energy Platform",
      body:
        "OEP is a research data infrastructure and community database for energy, climate, and mobility data. A Loom pipeline could run during `loom push` to send confirmed datasets, metadata, license notes, and source context to OEP while keeping Loom cards available for local agents.",
    },
    pipelineItems: [
      { label: "Open Energy Platform", href: "https://openenergyplatform.org/" },
      { label: "Hugging Face", href: "https://huggingface.co/" },
      { label: "team data stores" },
      { label: "custom workflows" },
    ],
  },
  de: {
    kicker: "Erweiterbar angelegt",
    title: "Loom kann in zwei Richtungen wachsen.",
    body: "Der Kernfluss bleibt gleich: Quellen verstehen, Karten erzeugen und Daten dorthin bewegen, wo die Aufgabe sie braucht.",
    loadersTitle: "Mehr Loader",
    loadersBody: "Ergaenze Loader fuer weitere Dateiformate, APIs, Online-Daten und projektspezifische Quellen.",
    loaderExamples: [
      "CSV- und Tabellen-Loader lesen Felder, Einheiten, Wertebereiche, Beispiele und Tabellenstruktur.",
      "Dokument-Loader extrahieren Tabellen, Abbildungen, Methoden, Definitionen und Quellen aus PDFs oder Berichten.",
      "API- und Online-Daten-Loader verstehen Endpunkte, Query-Parameter, Aktualisierungstakt und Zugriffsregeln.",
    ],
    loaderItems: ["CSV und Tabellen", "PDF und Dokumente", "Bilder", "APIs", "Online-Daten"],
    pipelineTitle: "Pipelines",
    pipelineBody:
      "Pipeline-Hooks koennen nach Scan, Review, Confirm oder Push laufen. Zum Beispiel kann der Push-Schritt kuratierte Daten und Metadaten an eine externe Plattform senden, waehrend Loom die lokalen Karten als Index behaelt.",
    pipelineExamples: [
      "gepruefte Energiedaten beim Push zu Open Energy Platform synchronisieren",
      "wiederverwendbare Datenkarten oder Artefakte auf Hugging Face veroeffentlichen",
      "bereinigte Daten an ein Team-Warehouse oder eine Projekt-API senden",
    ],
    pipelineSpotlight: {
      title: "Open Energy Platform",
      body:
        "OEP ist Forschungsdateninfrastruktur und Community-Datenbank fuer Energie-, Klima- und Mobilitaetsdaten. Eine Loom-Pipeline koennte bei `loom push` bestaetigte Datensaetze, Metadaten, Lizenzhinweise und Quellenkontext an OEP senden, waehrend Loom-Karten lokal nutzbar bleiben.",
    },
    pipelineItems: [
      { label: "Open Energy Platform", href: "https://openenergyplatform.org/" },
      { label: "Hugging Face", href: "https://huggingface.co/" },
      { label: "Team-Datenspeicher" },
      { label: "eigene Workflows" },
    ],
  },
  zh: {
    kicker: "扩展能力",
    title: "Loom 可以沿着两条方向扩展。",
    body: "核心流程不变：理解数据源，生成数据卡，再把合适的数据送到任务需要的地方。",
    loadersTitle: "更多 loader",
    loadersBody: "增加 loader 后，可以支持更多文件格式、API、线上数据集，以及项目自己的数据源。",
    loaderExamples: [
      "CSV / table loader：读取字段、单位、取值范围、样例行和表结构。",
      "Document / PDF loader：提取表格、图、方法说明、术语定义和引用来源。",
      "API / online data loader：理解 endpoint、查询参数、更新频率、权限和在线取数规则。",
    ],
    loaderItems: ["CSV 和表格", "PDF 和文档", "图片", "API", "线上数据"],
    pipelineTitle: "Pipeline",
    pipelineBody:
      "Pipeline 可以挂在 scan、review、confirm 或 push 之后执行。例如在 loom push 阶段，把整理后的数据和 metadata 同步发送到外部平台，同时 Loom 继续保留本地数据卡作为索引。",
    pipelineExamples: [
      "push 时把审核后的能源数据同步发送到 Open Energy Platform",
      "把可复用的数据卡或数据产物发布到 Hugging Face",
      "把清洗后的数据发送到团队数据仓库或项目 API",
    ],
    pipelineSpotlight: {
      title: "Open Energy Platform",
      body:
        "OEP 是面向能源、气候和交通数据的研究数据基础设施和社区数据库。Loom 可以在 `loom push` 阶段，把已确认的数据集、metadata、license 信息和来源上下文同步发送到 OEP，同时保留本地数据卡供 Agent 检索。",
    },
    pipelineItems: [
      { label: "Open Energy Platform", href: "https://openenergyplatform.org/" },
      { label: "Hugging Face", href: "https://huggingface.co/" },
      { label: "团队数据仓库" },
      { label: "自定义工作流" },
    ],
  },
} satisfies Record<Locale, CapabilityCopy>;

export function ExtensionCapabilities() {
  const { locale } = useI18n();
  const copy = capabilityCopy[locale];

  return (
    <section className="extension-section">
      <div className="extension-heading">
        <p className="section-kicker">{copy.kicker}</p>
        <h2>{copy.title}</h2>
        <p>{copy.body}</p>
      </div>
      <div className="extension-grid">
        <CapabilityPanel
          body={copy.loadersBody}
          examples={copy.loaderExamples}
          items={copy.loaderItems.map((label) => ({ label }))}
          title={copy.loadersTitle}
        />
        <CapabilityPanel
          body={copy.pipelineBody}
          examples={copy.pipelineExamples}
          items={copy.pipelineItems}
          spotlight={copy.pipelineSpotlight}
          title={copy.pipelineTitle}
        />
      </div>
    </section>
  );
}

function CapabilityPanel({
  body,
  examples,
  items,
  spotlight,
  title,
}: {
  body: string;
  examples?: string[];
  items: { label: string; href?: string }[];
  spotlight?: { title: string; body: string };
  title: string;
}) {
  return (
    <article className="capability-panel">
      <h3>{title}</h3>
      <p>{body}</p>
      {examples ? (
        <ul className="capability-examples">
          {examples.map((example) => (
            <li key={example}>{example}</li>
          ))}
        </ul>
      ) : null}
      {spotlight ? (
        <div className="capability-spotlight">
          <h4>{spotlight.title}</h4>
          <p>{spotlight.body}</p>
        </div>
      ) : null}
      <div className="capability-tags">
        {items.map((item) =>
          item.href ? (
            <a href={item.href} key={item.label} rel="noreferrer" target="_blank">
              {item.label}
            </a>
          ) : (
            <span key={item.label}>{item.label}</span>
          ),
        )}
      </div>
    </article>
  );
}
