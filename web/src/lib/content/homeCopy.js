export const AGENT_INSTALL_PROMPTS = [
  { key: "chatgpt", label: "ChatGPT", assistant: "ChatGPT", cliAgent: "codex", skillLabel: "Codex" },
  { key: "claude", label: "Claude", assistant: "Claude", cliAgent: "claude", skillLabel: "Claude" },
  { key: "cursor", label: "Cursor", assistant: "Cursor", cliAgent: "cursor", skillLabel: "Cursor" },
];

export const HOME_FLOW = [
  { step: "01", title: "整理原始数据", body: "把 CSV、目录说明和原始资料放进 raw_data/<workspace>/...，Loom 识别带 loom.md 的数据集根目录。" },
  { step: "02", title: "生成轻量数据卡", body: "loom scan 会生成 overview、CSV 摘要、字段画像和统计信息。" },
  { step: "03", title: "按需取回原始文件", body: "loom ask 先检索卡片；只有真的需要原始文件时，才继续用 loomcli get 精确读取。" },
];

export const HOME_OUTPUTS = [
  { title: "给 AI 的入口更轻", body: "从直接打开大 CSV，变成先读 overview.md 和每个 CSV 卡片。" },
  { title: "问题定位更快", body: "AI 先知道哪个 workspace、哪个 dataset、哪张表更相关，再决定要不要继续取 raw file。" },
  { title: "团队可复用", body: "扫描结果写进 loom/，后来的同事或 agent 可以复用同一套摘要。" },
];

export const HOME_USE_CASES = [
  "分析师先问问题，再下钻到准确的原始表",
  "工程师写脚本前先确认字段和分布",
  "报告生成时避免把大文件整份塞给 AI",
  "多数据源项目里，为每个 workspace 留下可搜索的数据说明",
];
