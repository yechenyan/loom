export const TUTORIAL_FILES = [
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
