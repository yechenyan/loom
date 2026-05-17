你是一个全栈工程师，帮我实现：
在开发过程中你可以拆分 3-5 个子agent 做这个事情
先写测试，再写代码，需确保通过测试
# Loom

> Loom helps AI agents understand datasets before using them.

Loom 不是传统数据平台。

Loom 的目标：

不是让「人」搜索数据。

而是让 AI agent：

- 理解数据
- 判断数据是否适合任务
- 找到合适的数据
- 安全地使用数据
---

## 核心理念

传统 workflow：

```text
AI
 ↓
直接读取 raw data
 ↓
高 token 消耗
 ↓
无法理解数据质量
 ↓
容易 hallucination
```

Loom workflow：

```text
raw_data
    ↓
hook pipeline
    ↓
structured dataset context
    ↓
AI reasoning
    ↓
dataset cards
    ↓
human review
    ↓
loom_explore
```

## 核心思想：
AI 永远先读取 Dataset Cards， 而不是查看原始的 csv 数据

### 什么是 dataset card：

Dataset Card：

不是 metadata。

也不是 README。

而是：AI-readable dataset understanding

它描述：

- 数据适合什么任务
- 数据有哪些限制
- 数据质量如何
- 数据如何 join
- AI 使用时有哪些风险



## 数据分层

raw_data          本地的原始数据
preview_data      AI 初步生成的 data card
server data card  用户 reivew 后，把本地 data card 上传到服务器， 由 postgres 数据存储
server raw data   服务端存储的 raw data， 是 object dataset， 当前只需放在服务器本地目录即可







## 数据分层

| 层              | 作用                              |
| -------------- | ------------------------------- |
| raw_data       | 原始数据                            |
| preview_data   | scan 后生成的临时 semantic preview， 临时 dataset card    |
| semantic_index | server canonical semantic graph，存在数据库的  dataset card |
| loom_explore   | 本地同步下来的 semantic index， 本地通下来，后续 AI 进行探索的  dataset card          |

---

## 使用流程

### 第一步：安装 Loom
此步骤人做
安装：

```bash
uv tool install loom
```
只示范，可能不准

---

## 第二步：初始化 Workspace
此步骤人做

```bash
loom init berlin_energy
```

Loom 自动：

* 检测 Codex
* 自动生成 `.loom/config.yaml`
* 初始化 workspace
* 自动加入 hook 和 skill

例如：

```text
Detected:
✓ Claude Code
✓ Codex CLI

Using Claude Code
```

---

## 第三步：放入原始数据
此步骤人做
如果一个文件夹下有 `loom.md`， 则这个 文件就算作一个 dataset

---

### 示例

```text
raw_data/
└── germany_energy/
    ├── loom.md
    │
    ├── berlin_grid/
    │   ├── loom.md
    │   ├── load.csv
    │   └── weather.csv
    │
    ├── munich_grid/
    │   ├── loom.md
    │   └── load.csv
    │
    └── tmp_downloads/
        └── random.csv
```

---

### Dataset Detection

| 目录             | 类型                 |
| -------------- | ------------------ |
| germany_energy | dataset collection |
| berlin_grid    | dataset            |
| munich_grid    | dataset            |
| tmp_downloads  | 普通目录               |

---

### loom.md（人写）

此文件由人写，没有标准格式，单通常由来源

```
name: Berlin Grid Load 2023

source:
  organization: Berlin Open Energy Platform
  url: https://energy.berlin.de/open-data/grid-load-2023

description: |
  Hourly district-level electricity load data.

tags:
  - energy
  - forecasting

coverage:
  geo:
    - Berlin

  time:
    start: 2023-01-01
    end: 2023-12-31
```

---

### load.csv

```csv
timestamp,district,load_mw
2023-01-01 00:00,Mitte,142.3
2023-01-01 01:00,Mitte,138.8
```

---

## 第四步：扫描数据
此步骤人在 codex cli 或 code chat 中输入：

```AI chart
loom scan 
```
### 4.1 步：首先调取 hook pipeline

1. dataset diff detection
2. schema extraction
3. statistical profiling
4. file sampling
5. time coverage analysis
6. null analysis
7. joinability detection
8. file relationship inference

这些步骤：不依赖 AI 而是：由本地 hooks + parsers 完成。

不同数据类型，使用不同的 hooks，当前只支持 csv

会生成 tructured Dataset Context，例如


```json
{
  "dataset": "berlin_grid",

  "files": [
    {
      "path": "load.csv",

      "columns": [
        {
          "name": "timestamp",
          "type": "datetime"
        },
        {
          "name": "district",
          "type": "string"
        },
        {
          "name": "load_mw",
          "type": "float"
        }
      ],

      "time_coverage": {
        "start": "2023-01-01",
        "end": "2023-12-31"
      },

      "missing_rate": 0.3,

      "join_candidates": [
        {
          "file": "weather.csv",
          "key": "timestamp"
        }
      ]
    }
  ]
}
```

### 4.2 步：AI Reasoning Layer
AI 再基于：

```text
structured dataset context
```

进行：

```text
1. dataset understanding
2. task suitability analysis
3. risk analysis
4. constraint analysis
5. join reasoning
6. use case generation
```

最终生成：

```text
dataset cards
```

生成的 dataset cards 放在 preview_data 下：
如：

```text
preview_data/
└── germany_energy/
    └── berlin_grid/
        ├── dataset_card.md
        ├── dataset_card.json
        │
        └── asset_cards/
            ├── load.csv.md
            ├── load.csv.json
            └── weather.csv.md
```

---

# Dataset Card 示例

```markdown
# Berlin Grid Load 2023

## Overview

District-level hourly electricity load observations
covering Berlin during 2023.

This dataset is suitable for:

- short-term load forecasting
- anomaly detection
- district demand analysis

---

## AI Confidence

Task Suitability:
0.91

Joinability Confidence:
0.88

---

## Why This Dataset Fits Forecasting

This dataset contains:

- stable hourly intervals
- low missing rate
- district-level granularity
- full annual seasonal cycles

making it suitable for short-term
electricity demand forecasting.

---

## Coverage

### Geography

- Berlin
- 12 districts

### Time

Start:
2023-01-01

End:
2023-12-31

Resolution:
1 hour

---

## Dataset Shape

Rows:
8,760

Files:
2

Primary Assets:

- load.csv
- weather.csv

---

## Stable Facts

### Missing Rate

0.3%

### Duplicate Rows

None detected

### Timestamp Consistency

Valid hourly continuity.

---

## Joinability

Can join with:

- weather.csv via timestamp
- district_geojson via district
- public holiday datasets via timestamp

---

## Constraints

This dataset does not separate:

- industrial load
- residential load

which limits:

- sector-level forecasting
- policy analysis

---

## Risks

Potential future leakage if using
rolling aggregate features incorrectly.

Weather normalization not included.

---

## Agent Usage Notes

Before training:

- normalize weather features
- remove holiday anomalies
- avoid future leakage in rolling windows

---

## Suggested Tasks

Recommended tasks:

- next-hour forecasting
- district anomaly alerts
- peak demand estimation

---

## AI Generated Sections

Generated By:
Claude Sonnet 4

Reviewed:
YES

Reviewer:
Julian

Last Updated:
2026-05-17
```

---

# Asset Card 示例

```markdown
# load.csv

## Summary

Hourly district-level electricity load observations.

---

## Columns

| Column | Type | Meaning |
|---|---|---|
| timestamp | datetime | observation timestamp |
| district | string | Berlin district |
| load_mw | float | electricity load |

---

## Stable Facts

Rows:
8760

Missing Rate:
0.1%

---

## Joinability

Can join with:

- weather.csv via timestamp

---

## Risks

Potential leakage if future timestamps
are accidentally included in rolling windows.
```

---


## 第五步：Review preview_data

用户可以在当前 chat 聊天中继续 review：

* 修正 AI 理解
* 删除错误 relationships
* 补充 use cases

---

## 第六步：Push
人reivew 后，在chat 或bash 中输入下面的命令，表示 review完成，进行下一步：
```bash
loom push
```
并行做下面4件事情：
1. 将 preview_data 的数据移动到 loom_explore 中
2. 将 prview_data 的数据存到 loom server 的 postgres 中
3. 将 raw_data 上传到 loom server 的 object data 中
4. 之后清理掉 prview_data， 把其中的内容移动到 .loom/history 中



## 第七步 查找数据
AI 在写代码时，需要什么数据去 loom_explore 中查找， 不要查 raw data

例如：

```text
find datasets for hourly load forecasting
```

或：

```text
search loom explore for forecasting datasets
```

Loom skill：

会自动：

```text
1. 搜索 loom_explore
2. 找到适合的数据
3. 给出 suitability reasoning
4. 推荐最佳 datasets
```

Loom 的目标：

不是 keyword search。

而是：agent dataset discovery


## 第八步 使用数据


```bash
loom get germany_energy/berlin_grid
```

下载单个文件：

```bash
loom get germany_energy/berlin_grid/load.csv
```

生成：

```text
loom_usage_data/
└── germany_energy/
    └── berlin_grid/
        ├── load.csv
        └── weather.csv
```


或者直接在代码中使用：


```python
import loom

data = loom.get(
    "germany_energy/berlin_grid/load.csv"
)
```
会自动下载数据到 loom_usage_data  中

## 附加功能

可选命令同步本地 explore 数据
```bash
loom pull <工作区>
```
同步服务器的 explore data


如果下载的数据发现无需使用，直接删除

```bash
loom delete germany_energy/berlin_grid/load.csv
```

或：

```bash
loom delete germany_energy/berlin_grid
```

删除：

```text
loom_usage_data/
```

中的本地数据，不会删除服务器中的数据


```bash
loom usage 
```

列出 data usage 都有哪些数据，来源是什么


## 最终完整目录结构

```text
/loom
│
├── loom_explore/
│   └── germany_energy/
│       └── berlin_grid/
│           ├── dataset_card.md
│           ├── relationships.md
│           ├── quality_report.md
│           ├── metadata.yaml
│           │
│           └── asset_summaries/
│               ├── load.csv.md
│               └── weather.csv.md
│
├── loom_usage_data/
│   └── germany_energy/
│       └── berlin_grid/
│           ├── load.csv
│           └── weather.csv
│
├── berlin_energy/
│   ├── raw_data/
│   │   └── germany_energy/
│   │       ├── loom.md
│   │       │
│   │       ├── berlin_grid/
│   │       │   ├── loom.md
│   │       │   ├── load.csv
│   │       │   └── weather.csv
│   │       │
│   │       └── munich_grid/
│   │           ├── loom.md
│   │           └── load.csv
│   │
│   └── preview_data/
│       └── germany_energy/
│           └── berlin_grid/
│               ├── dataset_card.md
│               ├── relationships.md
│               ├── quality_report.md
│               ├── metadata.yaml
│               │
│               └── asset_summaries/
│                   ├── load.csv.md
│                   └── weather.csv.md
│
└── .loom/
    ├── history/
    │   └── germany_energy/
    │       └── berlin_grid/
    │           ├── 2026-05-17/
    │           └── 2026-06-01/
    │
    ├── query_cache/
    └── config.yaml
```

## 最后总的目录结构：
/test-data
   /loom 同上面的loom ，模拟测试
/packages
  /server 后端服务
  /cli    cli 工具




## 技术架构

CLI： typer
server： fastAPI
dataset: postgres + pydantic
用python 使用 uv 安装并创建独立的 workspace


## Loom 的真正价值

Loom 的价值：

不是存储数据。

而是： 帮助 AI 理解数据

这是传统 data catalog
从未真正解决的问题。


> Loom helps AI agents understand datasets before using them.
>
> AI reads Dataset Cards first —
> not raw data.
> 