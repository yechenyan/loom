import type { Locale } from "./i18n";

export const agentTabs = ["Codex", "Claude", "Cursor"] as const;
export const packageTabs = ["direct", "uv", "pip", "conda"] as const;

export type AgentTab = (typeof agentTabs)[number];
export type PackageTab = (typeof packageTabs)[number];

const agentValues: Record<AgentTab, string> = {
  Codex: "codex",
  Claude: "claude",
  Cursor: "cursor",
};

const packageLabels: Record<Locale, Record<PackageTab, string>> = {
  en: { direct: "Direct install", uv: "uv", pip: "pip", conda: "conda" },
  de: { direct: "Direkt installieren", uv: "uv", pip: "pip", conda: "conda" },
  zh: { direct: "直接安装", uv: "uv", pip: "pip", conda: "conda" },
};

export function getPackageLabel(locale: Locale, value: PackageTab) {
  return packageLabels[locale][value];
}

export function getStepGuides(locale: Locale) {
  return {
    en: [
      { number: "01", title: "Install", description: "Copy the prompt and send it to your AI agent." },
      { number: "02", title: "Generate data cards", description: "Send `/loom-scan <path>` to build cards for your data." },
      { number: "03", title: "Use the data", description: "Describe the analysis, chart, or report you want. The agent uses Loom first." },
      { number: "04", title: "Verify data", description: "Check cards, summaries, fields, and sources against raw files." },
      { number: "05", title: "Share data", description: "Send `loom push` to sync cards to the cloud for the team." },
    ],
    de: [
      { number: "01", title: "Installieren", description: "Kopiere den Prompt und sende ihn an deinen KI-Agenten." },
      { number: "02", title: "Datenkarten erzeugen", description: "Sende `/loom-scan <path>`, um Karten fuer deine Daten zu bauen." },
      { number: "03", title: "Daten nutzen", description: "Beschreibe Analyse, Diagramm oder Bericht. Der Agent nutzt zuerst Loom." },
      { number: "04", title: "Daten pruefen", description: "Pruefe Karten, Zusammenfassungen, Felder und Quellen gegen Rohdateien." },
      { number: "05", title: "Daten teilen", description: "Sende `loom push`, um Karten fuer das Team in die Cloud zu synchronisieren." },
    ],
    zh: [
      { number: "01", title: "安装", description: "复制提示词发给 AI Agent。" },
      { number: "02", title: "生成数据卡片", description: "发给 Agent：`/loom-scan <path>` 生成数据卡片，`<path>` 是要扫描的数据。" },
      { number: "03", title: "使用数据", description: "直接描述你要做的分析、图表或报告，Agent 会先用 Loom 定位可信数据。" },
      { number: "04", title: "检验数据", description: "对照原始文件检查数据卡、摘要、字段和来源是否可信。" },
      { number: "05", title: "分享数据", description: "发给 Agent：`loom push`，把数据卡同步到云端，方便团队复用。" },
    ],
  }[locale];
}

export function getHighlights(locale: Locale) {
  return {
    en: [
      "Turn CSV files and supporting docs into index cards AI can scan quickly.",
      "Keep raw files as the fact source so answers stay traceable.",
      "Useful before analysis, modeling, reports, papers, or code generation.",
    ],
    de: [
      "Mach aus CSVs und Begleitdokumenten Indexkarten, die KI schnell durchsuchen kann.",
      "Behalte Rohdateien als Faktenquelle, damit Antworten nachvollziehbar bleiben.",
      "Sinnvoll vor Analyse, Modellierung, Berichten, Papers oder Codegenerierung.",
    ],
    zh: [
      "把 CSV 与说明文档变成 AI 能快速浏览的索引卡。",
      "保留原始文件作为事实来源，回答时可追溯。",
      "适合数据分析、建模、报告、论文和代码生成前的数据查证。",
    ],
  }[locale];
}

export function getUseCases(locale: Locale) {
  return {
    en: [
      "Avoid stuffing the whole data folder into context.",
      "Avoid re-explaining what each CSV means.",
      "Avoid AI citing tables it never inspected.",
    ],
    de: [
      "Du musst nicht den ganzen Datenordner in den Kontext stopfen.",
      "Du musst nicht jedes CSV immer wieder erklaeren.",
      "Du musst nicht fuerchten, dass KI ungesehene Tabellen zitiert.",
    ],
    zh: ["不用把整个数据目录塞进上下文。", "不用反复解释每个 CSV 是什么。", "不用担心 AI 引用没看过的表。"],
  }[locale];
}

export function buildInstallConversation(locale: Locale, agent: AgentTab, packageManager: PackageTab) {
  const agentValue = agentValues[agent];
  return sharedConversation(locale, agent, agentValue, packageManager);
}

function installPrompt(locale: Locale, agent: AgentTab, agentValue: string, packageManager: PackageTab) {
  const initStep = {
    en: `Run \`loomcli init --agent ${agentValue}\`. Do not enter interactive setup; this installs the Loom skill and tutorial for ${agent} directly.`,
    de: `Fuehre \`loomcli init --agent ${agentValue}\` aus. Starte keine interaktive Initialisierung; der Befehl installiert das Loom-Skill und Tutorial fuer ${agent} direkt.`,
    zh: `运行 \`loomcli init --agent ${agentValue}\`。不要进入交互式初始化；这条命令会直接安装 ${agent} 的 Loom skill 和 tutorial。`,
  }[locale];

  const sharedEnd = {
    en: `After install, run \`loomcli --help\` to confirm the command works directly. If it fails, fix PATH, activate the right environment, or switch to an install method that exposes CLI tools. After ${initStep} tell me only the short result.`,
    de: `Fuehre nach der Installation \`loomcli --help\` aus, um zu bestaetigen, dass der Befehl direkt verfuegbar ist. Wenn das fehlschlaegt, korrigiere PATH, aktiviere die richtige Umgebung oder wechsle zu einer Installationsart mit direktem CLI-Zugriff. Nach ${initStep} antworte mir nur mit dem kurzen Ergebnis.`,
    zh: `安装后必须运行 \`loomcli --help\` 验证命令可直接执行；如果失败，请修正 PATH、激活正确环境，或换用能安装命令行工具的方式。${initStep} 完成后只用简短结果告诉我。`,
  }[locale];

  if (packageManager === "uv") {
    return {
      en: `Execute directly with no planning or explanation. Install and initialize Loom in the current project using uv tool install, not \`uv add\` or \`uv run loomcli\`: 1. Run \`uv tool install loom-data\`. 2. ${sharedEnd}`,
      de: `Bitte direkt ausfuehren, ohne Plan oder Erklaerung. Installiere und initialisiere Loom im aktuellen Projekt mit uv tool install, nicht mit \`uv add\` oder \`uv run loomcli\`: 1. Fuehre \`uv tool install loom-data\` aus. 2. ${sharedEnd}`,
      zh: `请直接执行，不要先做计划或解释。在当前项目里安装并初始化 Loom。使用 uv 的工具安装方式，不要使用 \`uv add\` 或 \`uv run loomcli\`：1. 运行 \`uv tool install loom-data\`。2. ${sharedEnd}`,
    }[locale];
  }

  if (packageManager === "pip") {
    return {
      en: `Execute directly with no planning or explanation. Install and initialize Loom in the current project with Python/pip and make sure \`loomcli\` can run as a direct terminal command: 1. Run \`python -m pip install loom-data\`. 2. ${sharedEnd}`,
      de: `Bitte direkt ausfuehren, ohne Plan oder Erklaerung. Installiere und initialisiere Loom im aktuellen Projekt mit Python/pip und stelle sicher, dass \`loomcli\` direkt im Terminal aufrufbar ist: 1. Fuehre \`python -m pip install loom-data\` aus. 2. ${sharedEnd}`,
      zh: `请直接执行，不要先做计划或解释。在当前项目里安装并初始化 Loom。使用当前 Python/pip 安装，并确保 \`loomcli\` 能作为终端命令直接运行：1. 运行 \`python -m pip install loom-data\`。2. ${sharedEnd}`,
    }[locale];
  }

  if (packageManager === "conda") {
    return {
      en: `Execute directly with no planning or explanation. Install and initialize Loom in a conda environment, but Loom itself must still run as \`loomcli\`: 1. If needed, run \`conda create -n loom python=3.12\`. 2. Run \`conda activate loom\`. 3. Run \`python -m pip install loom-data\`. 4. ${sharedEnd}`,
      de: `Bitte direkt ausfuehren, ohne Plan oder Erklaerung. Installiere und initialisiere Loom in einer conda-Umgebung, aber Loom selbst muss weiterhin direkt als \`loomcli\` laufen: 1. Falls noetig, \`conda create -n loom python=3.12\` ausfuehren. 2. \`conda activate loom\`. 3. \`python -m pip install loom-data\`. 4. ${sharedEnd}`,
      zh: `请直接执行，不要先做计划或解释。在当前项目里安装并初始化 Loom。使用 conda 环境，但运行 Loom 时必须能直接输入 \`loomcli\`：1. 如果还没有合适环境，运行 \`conda create -n loom python=3.12\`。2. 运行 \`conda activate loom\`。3. 运行 \`python -m pip install loom-data\`。4. ${sharedEnd}`,
    }[locale];
  }

  return {
    en: `Execute directly with no planning or explanation. Install and initialize Loom in the current project with a direct CLI install and ensure \`loomcli\` works without \`uv run\`: 1. Prefer \`pipx install loom-data\`; if pipx is missing, install pipx first and run \`pipx ensurepath\`. 2. ${sharedEnd}`,
    de: `Bitte direkt ausfuehren, ohne Plan oder Erklaerung. Installiere und initialisiere Loom im aktuellen Projekt mit einer direkten CLI-Installation und stelle sicher, dass \`loomcli\` ohne \`uv run\` funktioniert: 1. Bevorzuge \`pipx install loom-data\`; falls pipx fehlt, installiere zuerst pipx und fuehre \`pipx ensurepath\` aus. 2. ${sharedEnd}`,
    zh: `请直接执行，不要先做计划或解释。在当前项目里安装并初始化 Loom。使用直接的 CLI 工具安装方式，并确保之后能在终端直接运行 \`loomcli\`，不要依赖 \`uv run\`：1. 优先运行 \`pipx install loom-data\`；如果没有 pipx，先安装 pipx 并运行 \`pipx ensurepath\`。2. ${sharedEnd}`,
  }[locale];
}

function sharedConversation(locale: Locale, agent: AgentTab, agentValue: string, packageManager: PackageTab) {
  return {
    en: [
      { heading: "install", role: "user", text: installPrompt(locale, agent, agentValue, packageManager) },
      { role: "assistant", text: `Loom is installed and initialized. The Loom skill and tutorial for ${agent} are ready.` },
      { heading: "scan", role: "user", text: "/loom-scan raw_data" },
      { role: "assistant", text: "The data folder has been scanned and Loom data cards were generated." },
      { heading: "ask", role: "user", text: "/loom-ask build a 24-hour German electricity data html demo" },
      { role: "assistant", text: "I will inspect the Loom data cards, locate the relevant raw files, and answer with sources." },
      { heading: "review", role: "user", text: "What data was used, and where did it come from?" },
      { role: "assistant", text: "I will list the data that was used, explain where each dataset came from, and cite raw files when needed." },
      { heading: "share", role: "user", text: "loom push" },
      { role: "assistant", text: "The push succeeded." },
    ],
    de: [
      { heading: "install", role: "user", text: installPrompt(locale, agent, agentValue, packageManager) },
      { role: "assistant", text: `Loom ist installiert und initialisiert. Das Loom-Skill und Tutorial fuer ${agent} sind bereit.` },
      { heading: "scan", role: "user", text: "/loom-scan raw_data" },
      { role: "assistant", text: "Das Datenverzeichnis wurde gescannt und Loom-Datenkarten wurden erzeugt." },
      { heading: "ask", role: "user", text: "/loom-ask baue eine 24-Stunden-Demo zur Visualisierung deutscher Stromdaten" },
      { role: "assistant", text: "Ich pruefe zuerst die Loom-Datenkarten, finde die passenden Rohdateien und antworte mit Quellen." },
      { heading: "review", role: "user", text: "Welche Daten wurden verwendet, und woher stammen sie?" },
      { role: "assistant", text: "Ich liste die verwendeten Daten auf, erklaere die Herkunft der einzelnen Datensaetze und nenne bei Bedarf die Rohdateien als Quelle." },
      { heading: "share", role: "user", text: "loom push" },
      { role: "assistant", text: "Der Push war erfolgreich." },
    ],
    zh: [
      { heading: "install", role: "user", text: installPrompt(locale, agent, agentValue, packageManager) },
      { role: "assistant", text: `已安装并初始化 Loom。${agent} 的 Loom skill 和 tutorial 已就绪。` },
      { heading: "scan", role: "user", text: "/loom-scan raw_data" },
      { role: "assistant", text: "已扫描数据目录，并生成 Loom 数据卡片。" },
      { heading: "ask", role: "user", text: "/loom-ask 做一个 24 小时德国电力数据可视化 demo" },
      { role: "assistant", text: "我会先查看 Loom 数据卡片，定位相关原始文件，再给出带来源的回答。" },
      { heading: "review", role: "user", text: "用了哪些数据，数据来自哪里？" },
      { role: "assistant", text: "我会梳理用到的数据、说明各项数据来源，并在必要时对照原始文件补充出处。" },
      { heading: "share", role: "user", text: "loom push" },
      { role: "assistant", text: "The push succeeded." },
    ],
  }[locale];
}
