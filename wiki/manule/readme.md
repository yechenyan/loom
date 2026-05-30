# Loom Manual

这个文档定义当前仓库里的 Loom 工作方式，并固定区分 chat、CLI 和内部脚本。

## 命名约定

- `loom ...`
  用户在 agent 聊天里发送的消息。
- `loomcli ...`
  用户、开发者或 agent 实际执行的命令入口。
- `import loom`
  Python 包导入名，保持不变。

这四层不要再混用。

## 职责图

```text
用户
  -> chat: `loom ...`
     -> agent
        -> `loomcli ...`
           -> 生成/更新 `loom/<workspace>`

用户
  -> terminal: `loomcli ...`
     -> 对 Loom workspace 或 raw cache 执行显式本地操作
```

推荐理解方式：

- `loom`
  用户在聊天里让 agent 帮自己做事。
- `loomcli`
  用户自己在终端执行明确命令，或 agent 在理解聊天意图后实际调用的执行入口。

例子：

1. 用户在 chat 里说 `loom scan raw_data/cost to cost`
2. agent 把它识别成聊天扫描意图
3. agent 内部执行 `loomcli scan-index raw_data/cost to cost`
4. Loom 在 `loom/cost` 下生成 cards
5. review 完成后，人或 agent 才考虑执行 `loomcli confirm cost`

## 目标

Loom 的目标是把原始数据扫描成 `loom/` 下的轻量卡片和摘要，让 agent 先读卡片，再按需拉取 raw 文件。

如果希望第一版卡片更像人工整理的结果，建议在原始数据目录的 `loom.md` 里写一段数据集说明，并补一个 `Columns:` 小节，例如 `- technology: ...`。扫描时这些列说明会被带进生成的 overview 和 CSV card。

目录约定：

- `raw_data/<workspace>`
  原始数据目录。
- `loom/<workspace>`
  扫描后生成的数据卡目录。
- `loom/.loom/raw/<workspace>`
  原始数据本地缓存。
- [scripts/loomcli.py](/Users/maxiao/Documents/code2/loom/scripts/loomcli.py)
  仓库内 CLI 启动脚本。

## 什么时候用什么

### 1. 聊天里用 `loom`

下面这些是发给 agent 的聊天消息，不是 bash 命令：

```text
loom scan raw_data/energy to energy
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
loom confirm energy
loom push energy
```

解释：

- `loom scan ...`
  表示一个聊天扫描意图。agent 应该调用 `loomcli scan-index ...` 生成第一版卡片，然后继续在聊天里补充和整理，最后给用户结果。这个 review 不能只看文件是否生成，还要读对应的 `loom.md`、检查 `overview.md` 和 card 是否把数据集用途、关键维度、年份或场景字段、单位、每一列的作用讲清楚；没有完成这些时，不应把扫描说成已经 review 完，也不应急着建议 `loomcli confirm`。
- `loom ask ...` / `loom <问题>`
  表示一个聊天查询意图。agent 不应该去跑 `ask` 脚本，而是应该先查 `loom/`，必要时再用 `loomcli get ...` 拉具体 raw 文件。
- `loom confirm ...` / `loom push ...`
  表示一个聊天操作意图。agent 可以选择执行对应的 `loomcli` 命令。

### 2. 终端里用 `loomcli`

这些是给 shell 跑的正式命令：

```bash
uv run loomcli init
uv run loomcli scan-index raw_data/energy to energy
uv run loomcli status energy
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
uv run loomcli get energy/technology-data/costs.csv
uv run loomcli set-api https://loom-api-free.onrender.com
```

约束：

- `loomcli` 的显式扫描命令现在叫 `scan-index`。
- `loomcli` 不再承担 `ask`。
- `loom scan` 是 chat 扫描语义，agent 内部执行 `loomcli scan-index`。
- 如果用户坚持要一个 terminal scan 命令，用 `loomcli scan-index ...`。
- `ask` 是 chat + agent 自主查 `loom/` 的流程。

## 推荐工作流

### 初始化

```bash
uv run loomcli init --agent codex
```

推荐把这条当成 AI onboarding 的默认入口。
当传入 `--agent` 时，`loomcli init` 会直接进入非交互快速流程：

- 安装对应 agent 的 Loom skill
- 创建 `./loom/` 和 `./raw_data/`
- 用当前用户名作为默认 workspace
- 自动安装 tutorial dataset
- 结束时明确提示后续哪些该在聊天里用 `loom ...`，哪些该在终端里用 `uv run loomcli ...`

如果需要手动选择 agent、workspace 或是否安装教程，再使用交互版：

```bash
uv run loomcli init
```

`loomcli init` 会创建 `./loom/`、`./raw_data/`，并安装对应 agent 的 skill。
`loomcli init --agent codex` 不再进入交互问题，而是直接完成 tutorial-ready 初始化。

如果启用教程，结束时应该引导用户发这种聊天消息：

```text
loom scan raw_data/cost to cost
loom ask "What is the capex for OCGT?"
What is the capex for OCGT?
```

### 扫描

标准聊天消息：

```text
loom scan raw_data/energy to energy
```

agent 内部执行：

```bash
uv run loomcli scan-index raw_data/energy to energy
```

规则：

- `<path>` 必填。
- `to <workspace>` 可选。
- 如果省略 workspace，Loom 复用最近一次 workspace；没有历史时使用 `temporary`。
- 同一个 workspace 可以跟踪多个 source path。
- 如果两个 source 会生成相同 dataset path，Loom 会报冲突并停止。

### 查询

标准聊天消息：

```text
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
```

agent 的默认行为：

1. 先查看 `loom/`
2. 搜索 cards 和 summaries
3. 判断需要哪个 raw 文件
4. 用 `loomcli get ...` 精确拉取
5. 回答用户问题

不要把 `loom ask` 解释成“运行一个 CLI 问答脚本”。

### 确认和同步

终端里：

```bash
uv run loomcli status energy
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
```

聊天里如果用户说：

```text
loom confirm energy
loom push energy
```

agent 可以执行对应的 `loomcli` 命令。

## Python API

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
```

`loom.get(...)` 会优先复用本地缓存，只在需要时下载最新 raw 文件。

## 仓库维护说明

- 行为变化后，要同步更新根目录 [README.md](/Users/maxiao/Documents/code2/loom/README.md) 和 [wiki/manule/readme.md](/Users/maxiao/Documents/code2/loom/wiki/manule/readme.md)。
- 代码里不要再把 `loom` 和 `loomcli` 混成同一层语义。
- 如果用户说“在聊天里输入 `loom ...`”，那不是 shell 命令。

### CLI 发布 skill

仓库内现在约定用 [.agents/skills/loom-cli-release/SKILL.md](/Users/maxiao/Documents/code2/loom/.agents/skills/loom-cli-release/SKILL.md) 处理 `loom-data` 的发布。

这个 skill 的要求是：

- 先读根目录 `pyproject.toml` 和 `git status --short`
- 先确认 PyPI 当前最新版本，再决定 `patch` 还是显式版本号
- 统一通过 `uv run python scripts/release_pypi.py ...` 发布
- 如果 lint 或最小测试失败，先修阻塞问题再重跑
- 上传成功后继续回查 PyPI；如果公开索引没及时刷新，要明确告诉用户是索引延迟，不要误报发布失败

### Render 发布 skill

仓库内现在约定用 [.agents/skills/loom-render-deploy/SKILL.md](/Users/maxiao/Documents/code2/loom/.agents/skills/loom-render-deploy/SKILL.md) 处理当前仓库的前后端上线。

标准命令：

```bash
uv run python scripts/deploy_render.py
```

这个脚本默认会：

- 要求当前工作区干净
- 要求 `HEAD` 已经 push 到当前分支对应的 `origin/<branch>`
- 先执行 `render blueprints validate`
- 再依次部署 `loom-api-free` 和 `loom-web`
- 最后验证线上 API 和 Web 地址
