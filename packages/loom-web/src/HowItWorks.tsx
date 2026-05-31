import type { ReactNode } from "react";
import { useI18n, type Locale } from "./i18n";

type WorkflowCopy = {
  kicker: string;
  title: string;
  body: string;
  scanLabel: string;
  scanCommand: string;
  askLabel: string;
  askCommand: string;
  sourceTitle: string;
  sourceHint: string;
  loaderTitle: string;
  loaderRaw: string;
  loaderStructured: string;
  loaderCard: string;
  loaderKinds: string;
  agentGenerate: string;
  cardTitle: string;
  cardHint: string;
  lookupTitle: string;
  lookupCards: string;
  lookupVectors: string;
  lookupPathAgent: string;
  lookupPathVector: string;
  accessTitle: string;
  accessLocal: string;
  accessRemote: string;
  rawTitle: string;
  rawHint: string;
  supportNote: string;
};

const workflowCopy = {
  en: {
    kicker: "How Loom works",
    title: "How it works",
    body:
      "The scan layer turns source files into searchable cards. The ask layer starts from the task, searches those cards, then fetches exact raw data only when needed.",
    scanLabel: "Scan layer",
    scanCommand: "/loom-scan <path>",
    askLabel: "Ask layer",
    askCommand: "/loom-ask",
    sourceTitle: "Source data",
    sourceHint: "raw_data",
    loaderTitle: "Loom loader extracts data",
    loaderRaw: "raw data",
    loaderStructured: "structured data",
    loaderCard: "data card",
    loaderKinds: "csv loader, pdf loader, ...",
    agentGenerate: "AI agent generates by skill",
    cardTitle: "Data cards",
    cardHint: "cards and profiles created by scan",
    lookupTitle: "Find suitable data",
    lookupCards: "search data cards first",
    lookupVectors: "use vector search when needed",
    lookupPathAgent: "agent grep",
    lookupPathVector: "vector database",
    accessTitle: "Get exact raw data",
    accessLocal: "use local file when available",
    accessRemote: "download from server otherwise",
    rawTitle: "Raw data",
    rawHint: "fetch only what the task needs",
    supportNote: "Current release supports CSV. PDF, images, API docs, Markdown loaders, and richer source types are in development.",
  },
  de: {
    kicker: "So funktioniert Loom",
    title: "Wie es funktioniert",
    body:
      "Die Scan-Ebene macht aus Quelldateien durchsuchbare Karten. Die Ask-Ebene startet bei der Aufgabe, sucht in Karten und holt exakte Rohdaten nur bei Bedarf.",
    scanLabel: "Scan-Ebene",
    scanCommand: "/loom-scan <path>",
    askLabel: "Ask-Ebene",
    askCommand: "/loom-ask",
    sourceTitle: "Quelldaten",
    sourceHint: "raw_data",
    loaderTitle: "Loom Loader extrahiert Daten",
    loaderRaw: "Rohdaten",
    loaderStructured: "strukturierte Daten",
    loaderCard: "Datenkarte",
    loaderKinds: "csv loader, pdf loader, ...",
    agentGenerate: "KI-Agent erzeugt mit Skill",
    cardTitle: "Datenkarten",
    cardHint: "Karten und Profile aus dem Scan",
    lookupTitle: "Passende Daten finden",
    lookupCards: "zuerst Datenkarten suchen",
    lookupVectors: "bei Bedarf Vektorsuche nutzen",
    lookupPathAgent: "agent grep",
    lookupPathVector: "Vektordatenbank",
    accessTitle: "Exakte Rohdaten holen",
    accessLocal: "lokale Datei nutzen, wenn vorhanden",
    accessRemote: "sonst vom Server laden",
    rawTitle: "Rohdaten",
    rawHint: "nur holen, was die Aufgabe braucht",
    supportNote:
      "Aktuell wird CSV unterstuetzt. PDF, Bilder, API-Dokumente, Markdown-Loader und weitere Quelltypen sind in Entwicklung.",
  },
  zh: {
    kicker: "Loom 是如何运行的",
    title: "如何工作",
    body: "上层是 /loom-scan：从 raw_data 生成数据卡。下层是 /loom-ask：从任务出发，先在数据卡里找合适数据，再按需取原始数据。",
    scanLabel: "扫描层",
    scanCommand: "/loom-scan <path>",
    askLabel: "提问层",
    askCommand: "/loom-ask",
    sourceTitle: "用户提交原始数据",
    sourceHint: "raw_data",
    loaderTitle: "loom loader 提炼数据",
    loaderRaw: "raw data",
    loaderStructured: "structure data",
    loaderCard: "data card",
    loaderKinds: "csv loader, pdf loader 等",
    agentGenerate: "AI agent 根据 skill 生成",
    cardTitle: "数据卡片",
    cardHint: "scan 后生成的 cards 和 profiles",
    lookupTitle: "找到合适的数据",
    lookupCards: "先检索数据卡片",
    lookupVectors: "必要时向量查寻",
    lookupPathAgent: "agent grep",
    lookupPathVector: "向量数据库",
    accessTitle: "获取精确原始数据",
    accessLocal: "本地有用本地",
    accessRemote: "本地无从服务器下载",
    rawTitle: "原始数据",
    rawHint: "只取任务需要的文件或片段",
    supportNote: "当前版本只支持 CSV。PDF、图片、API 文档、Markdown loader 和更多数据格式正在开发中。",
  },
} satisfies Record<Locale, WorkflowCopy>;

const sourceFiles = ["CSV table", "PDF document", "Image file", "API usage", "loom.md context"];

const dataCards = ["csv.card.md", "pdf.card.md", "image.card.md", "api-usage.card.md", "overview.md"];

export function HowItWorks() {
  const { locale } = useI18n();
  const copy = workflowCopy[locale];

  return (
    <section className="how-section" id="how">
      <div className="how-heading">
        <p className="section-kicker">{copy.kicker}</p>
        <h2>{copy.title}</h2>
        <p>{copy.body}</p>
      </div>
      <div className="aligned-flow" aria-label={copy.kicker}>
        <LayerCommand className="scan-command" label={copy.scanLabel} command={copy.scanCommand} />
        <FlowArrow className="scan-arrow scan-arrow-start" />
        <FlowPanel className="raw-column raw-scan" title={copy.rawTitle} hint={`${copy.sourceTitle} · ${copy.sourceHint}`}>
          <SourceFiles />
        </FlowPanel>
        <FlowArrow className="scan-arrow raw-to-loader" />
        <FlowPanel className="loader-panel" title={copy.loaderTitle}>
          <div className="loader-box">
            <span>{copy.loaderRaw}</span>
            <DownArrow />
            <p>{copy.loaderKinds}</p>
            <DownArrow />
            <span>{copy.loaderStructured}</span>
            <DownArrow />
            <p>{copy.agentGenerate}</p>
            <DownArrow />
            <span>{copy.loaderCard}</span>
          </div>
        </FlowPanel>
        <FlowArrow className="scan-arrow loader-to-card" />
        <FlowPanel className="card-column card-scan" title={copy.cardTitle} hint={copy.cardHint}>
          <CardList />
        </FlowPanel>
        <LayerCommand className="ask-command" label={copy.askLabel} command={copy.askCommand} />
        <FlowArrow className="ask-arrow ask-to-card" reverse />
        <FlowPanel className="card-column card-ask" title={copy.cardTitle} hint={copy.lookupTitle}>
          <p>{copy.lookupCards}</p>
          <p>{copy.lookupVectors}</p>
          <PathList items={[copy.lookupPathAgent, copy.lookupPathVector]} />
        </FlowPanel>
        <FlowArrow className="ask-arrow card-to-access" reverse />
        <FlowPanel className="raw-access-panel" title={copy.accessTitle}>
          <p>{copy.accessLocal}</p>
          <p>{copy.accessRemote}</p>
          <PathList items={[copy.accessLocal, copy.accessRemote]} />
        </FlowPanel>
        <FlowArrow className="ask-arrow access-to-raw" reverse />
        <FlowPanel className="raw-column raw-ask" title={copy.rawTitle} hint={copy.rawHint} />
      </div>
      <p className="support-note">{copy.supportNote}</p>
    </section>
  );
}

function LayerCommand({ className = "", command, label }: { className?: string; command: string; label: string }) {
  return (
    <div className={`layer-command ${className}`}>
      <span>{label}</span>
      <strong>{command}</strong>
    </div>
  );
}

function FlowPanel({ children, className = "", hint, title }: { children?: ReactNode; className?: string; hint?: string; title: string }) {
  return (
    <article className={`flow-panel ${className}`}>
      <h3>{title}</h3>
      {hint ? <p className="panel-hint">{hint}</p> : null}
      {children}
    </article>
  );
}

function CardList({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`card-files${compact ? " compact" : ""}`}>
      {(compact ? dataCards.slice(0, 2) : dataCards).map((item, index) => (
        <span key={`${item}-${index}`}>{item}</span>
      ))}
    </div>
  );
}

function PathList({ items }: { items: string[] }) {
  return (
    <div className="path-list">
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

function SourceFiles() {
  return (
    <div className="source-files">
      {sourceFiles.map((file) => (
        <span className="file-chip" key={file}>
          <strong>{file}</strong>
        </span>
      ))}
    </div>
  );
}

function FlowArrow({ className = "", reverse = false }: { className?: string; reverse?: boolean }) {
  return <span className={`flow-arrow-line${reverse ? " reverse" : ""} ${className}`} aria-hidden="true" />;
}

function DownArrow() {
  return <span className="down-arrow" aria-hidden="true" />;
}
