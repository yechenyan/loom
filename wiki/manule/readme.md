# Loom Manual

这个文档说明当前项目怎么使用，覆盖 `loom scan`、同步服务器和原始数据读取缓存流程。

## 项目目的

这个项目的目标是把 `test-project/loom/loom_raw` 里的原始数据，扫描并整理到 `test-project/loom/loom_explore`。

这样后续 agent 优先读取 `loom_explore` 下已经整理好的数据卡和摘要，而不是直接查看原始 CSV，可以节约 token，也能加快分析速度。

## 目录约定

- `test-project/loom/loom_raw/<topic>`
  原始数据目录。
- `test-project/loom/loom_explore/<topic>`
  扫描后生成的摘要目录。
- `test-project/loom/.loom/raw/<workspace>`
  原始数据本地缓存目录。
- `packages/loom`
  当前 `loom` Python package 和 CLI 的核心实现。
- `packages/loom-server`
  当前同步服务端实现。
- `scripts/loom.py`
  当前命令行入口。
- `scripts/loom-server.py`
  当前服务端命令行入口。

## 数据集识别规则

- 如果某个目录下存在 `loom.md`，这个目录会被视为一个数据集根目录。
- 这个数据集包含该目录下及其子目录中的相关 CSV 文件。
- 如果子目录里还有新的 `loom.md`，子目录会被视为独立数据集，父级扫描时不会重复收进去。

## 安装

先同步依赖：

```bash
cd /Users/maxiao/Documents/code2/loom
uv sync
```

如果你希望直接在 shell 里使用 `loom` 命令和 `import loom`：

```bash
uv pip install -e .
```

如果你也要启动同步服务，额外安装服务端包：

```bash
uv pip install -e packages/loom-server
```

再执行一次安装命令：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py install
```

这个命令会安装本地 `loom-data` skill，并自动把 `test-project/loom/loom_explore` 初始化成独立 git 仓库。这样扫描后就能直接看到变更，并支持 `loom confirm`。

当前 skill 安装位置包括：

- Codex 全局：`$CODEX_HOME/skills/loom-data`
- Codex 工作区：`.agents/skills/loom-data`
- Claude：`.claude/skills/loom-data`
- Cursor：`.cursor/skills/loom-data`
- Copilot：`.copilot/skills/loom-data`

## 用法

### 1. 在聊天里触发

用户在 Codex chat 中输入类似下面的话：

```text
loom scan energy
```

或者：

```text
Please scan energy with loom for me
```

系统会识别出这是一个扫描请求，并执行 `energy` 主题的扫描。

注意：

- 这是聊天里的输入，不是 bash 命令。
- 标准格式 `loom scan <topic>` 会更快命中快路径。

### 2. 手动执行扫描

也可以直接在项目根目录执行：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py scan energy
```

这条命令不会调用 AI，只会运行本地 Python 逻辑：

- 扫描 `loom_raw/energy`
- 识别 `loom.md`
- 读取 CSV
- 生成统计摘要
- 把结果写入 `loom_explore/energy`
- 输出当前 workspace 下有哪些文件发生了变化

### 3. 读取原始数据

项目提供了 Python API 和 CLI 来读取原始数据，并缓存到 `test-project/loom/.loom/raw`。

推荐 agent 工作流：

1. 先读 `loom/loom_explore`
2. 搜索生成出来的 cards 和 summaries
3. 判断具体需要哪个 raw 文件
4. 再按需拉取，比如 `loom get energy/technology-data/costs.csv`

Python:

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
```

CLI:

```bash
loom get energy/technology-data/costs.csv
```

处理规则：

- 第一次读取时，先检查 `test-project/loom/.loom/raw/...` 是否已经有缓存。
- 如果本地 `test-project/loom/loom_raw/...` 或 `.raw_data/...` 里已经有同路径文件，就直接在 `.loom/raw` 下建立 link。
- 如果本地 link 或缓存不存在，再从 Loom sync server 下载最新文件。
- 第二次读取同一个文件时，直接复用本地缓存。

如果你想一次把一个 workspace 的原始数据缓存下来：

```python
import loom

loom.pull("energy")
```

或者：

```bash
loom pull-raw energy --server-url http://127.0.0.1:8765
```

`loom.pull(...)` / `loom pull-raw ...` 会按远端 raw manifest 的 `path + sha256` 增量检查 `.loom/raw` 是否最新，只刷新变更或删除的文件，不会下载历史版本。

### 4. 查看和确认变更

扫描完成后，可以先看本地改动：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py status energy
```

确认这些改动没有问题后，再执行：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py confirm energy
```

这会把 `loom_explore/energy` 下当前待确认的文件提交到 `loom_explore` 这个独立 git 仓库里，作为本地确认版本。

### 5. 运行同步服务器

服务端使用 FastAPI，版本元数据存在 PostgreSQL，文件快照存在服务器本地存储目录。

默认数据库连接是本地 PostgreSQL：

```text
postgresql+psycopg2://loom@127.0.0.1:5432/loom
```

如果本地 PostgreSQL 可连接，`loom-server init-db` 和 `loom-server run` 会自动创建 `loom` 这个数据库。

先初始化数据库表：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom-server.py init-db
```

然后启动服务：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom-server.py run --storage-root /tmp/loom-server-storage
```

默认 API 地址是：

```text
http://127.0.0.1:8765
```

### 6. Push / Pull workspace

把本地某个 workspace 推到服务器：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py push energy --server-url http://127.0.0.1:8765
```

从服务器拉回某个 workspace：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py pull energy --server-url http://127.0.0.1:8765
```

如果不写 workspace，`push` 会推送本地所有一级 workspace，`pull` 会拉取服务器当前所有 workspace。

当前 `push/pull` 已经改成接近 git 的 rebase 语义：

- `push` 时如果本地 workspace 还有待确认文件，会先自动做一次本地 confirm。
- 如果远端已经比本地同步基线更新，`push` 会先自动执行一次 workspace rebase，再继续增量 push。
- `pull` 时如果本地自上次同步后没有新的 confirm 提交，会直接 fast-forward 并自动 confirm。
- `pull` 时如果本地已经有新的 confirm 提交，会把这些本地提交 rebase 到最新远端 revision 之上，而不是直接覆盖。
- 如果 `pull` 或 `push` 过程中发生 rebase 冲突，命令会返回非 0，保留冲突标记，并提示用户先解决冲突，再执行 `loom confirm <workspace>` 和 `loom push <workspace>`。
- `loom status <workspace>` 会显示 `Pending rebase revision`，方便识别当前 workspace 还处在冲突解决阶段。

如果还要同步原始数据缓存：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py pull-raw energy --server-url http://127.0.0.1:8765
```

这条命令只会把最新 raw 文件同步到 `test-project/loom/.loom/raw/energy/...`，不会拉历史数据。

补充说明：

- 普通 `loom pull <workspace>` / `loom push <workspace>` 之后触发的 raw 刷新，只会更新 `.loom/raw` 里已经存在的文件，不会把远端所有 raw 全部下载下来。
- 如果想主动把整个 workspace 的 raw 缓存补齐，继续使用 `loom.pull(...)` 或 `loom pull-raw <workspace>`。
- 如果本地 `test-project/loom/loom_raw/<workspace>/...` 和远端 raw manifest 冲突，Loom 不会覆盖本地源文件，而是会在对应 `loom.md` 旁生成 `loom.raw-conflict.md` 提示文件。

### 7. Web 查看数据

项目里已经有一个 React web app，可以直接浏览 `loom_explore` 的 workspace、dataset 和 CSV profile。

前提：

- Loom FastAPI server 运行在 `http://127.0.0.1:8765`
- 前端使用 `pnpm`

启动前端：

```bash
cd /Users/maxiao/Documents/code2/loom/web
pnpm install
pnpm dev --host 127.0.0.1
```

打开：

```text
http://127.0.0.1:4173
```

前端会通过 Vite proxy 把 `/api` 请求转发到 `http://127.0.0.1:8765`。

### 8. 检查聊天消息是否会触发扫描

如果想测试某条聊天消息会不会触发：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py route "loom scan energy" --workspace-root /Users/maxiao/Documents/code2/loom
```

## 当前输出内容

扫描后会在 `loom_explore/<topic>/<dataset>` 下生成：

- `overview.md`
  数据集总览。
- `profile.json`
  数据集级别的机器可读摘要。
- `*.card.md`
  单个 CSV 的数据卡。
- `*.profile.json`
  单个 CSV 的机器可读摘要。
- `README.md`
  topic 级别入口文件。

## CSV 摘要包含什么

对于每个 CSV，当前会提取：

- 列名
- 总行数
- 前 10 行样本
- 后 10 行样本
- 空值情况
- 字段类型分布
- 数值列的基础统计
- 高频值样本

如果 CSV 文件本身是空的，就按空文件如实写出，不额外做 AI 推断。

## 推荐使用方式

- 在聊天中优先使用 `loom scan <topic>` 这种标准格式。
- 如果只想读原始数据，优先用 `loom.get(...)` 或 `loom pull-raw ...`，不要手动维护 `.loom/raw`。
- 安装后，`loom_explore` 会由独立 git 仓库跟踪。
- 扫描完成后，先看变更，再执行 `loom confirm <topic>`。
- `push` 前要求当前 workspace 没有待确认改动。
- `pull` 前要求当前 workspace 没有本地未同步改动。
- 扫描完成后，后续 agent 优先读取 `loom_explore`。
- 除非 `loom_explore` 缺失或明显不完整，否则不要优先去看 `loom_raw`。
- 不要读取 `wiki/discard` 里的内容作为正式实现依据。

## 开发说明

相关代码位置：

- [chat.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/chat.py)
- [scanner.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/scanner.py)
- [csv_profile.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/csv_profile.py)
- [datacard.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/datacard.py)
- [data.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/data.py)
- [raw_cache.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/raw_cache.py)
- [cli.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/cli.py)
- [explore_repo.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/explore_repo.py)
- [sync_client.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/sync_client.py)
- [sync_server.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/sync_server.py)
- [sync_service.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/sync_service.py)
- [sync_state.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/sync_state.py)
- [workspace_snapshot.py](/Users/maxiao/Documents/code2/loom/packages/loom/src/loom/workspace_snapshot.py)
- [scripts/loom.py](/Users/maxiao/Documents/code2/loom/scripts/loom.py)
- [web/src/App.jsx](/Users/maxiao/Documents/code2/loom/web/src/App.jsx)
- [web/src/styles.css](/Users/maxiao/Documents/code2/loom/web/src/styles.css)

常用测试命令：

```bash
python -m pytest tests/test_raw_access.py tests/test_sync_workflow.py tests/test_cli_workflow.py
```
