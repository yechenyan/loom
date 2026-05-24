# Loom Manual

这个文档说明当前项目怎么使用，重点是 `loom scan` 相关流程。

## 项目目的

这个项目的目标是把 `test-project/loom/loom_raw` 里的原始数据，扫描并整理到 `test-project/loom/loom_explore`。

这样后续 agent 优先读取 `loom_explore` 下已经整理好的数据卡和摘要，而不是直接查看原始 CSV，可以节约 token，也能加快分析速度。

## 目录约定

- `test-project/loom/loom_raw/<topic>`
  原始数据目录。
- `test-project/loom/loom_explore/<topic>`
  扫描后生成的摘要目录。
- `packages/loom_scan`
  `loom scan` 的核心实现。
- `scripts/loom_scan.py`
  命令行入口。

## 数据集识别规则

- 如果某个目录下存在 `loom.md`，这个目录会被视为一个数据集根目录。
- 这个数据集包含该目录下及其子目录中的相关 CSV 文件。
- 如果子目录里还有新的 `loom.md`，子目录会被视为独立数据集，父级扫描时不会重复收进去。

## 安装

先执行一次安装命令：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py install
```

这个命令会安装本地 `loom-scan` skill，并自动把 `test-project/loom/loom_explore` 初始化成独立 git 仓库。这样扫描后就能直接看到变更，并支持 `loom confirm`。

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

### 3. 查看和确认变更

扫描完成后，可以先看本地改动：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py status energy
```

确认这些改动没有问题后，再执行：

```bash
uv run python /Users/maxiao/Documents/code2/loom/scripts/loom.py confirm energy
```

这会把 `loom_explore/energy` 下当前待确认的文件提交到 `loom_explore` 这个独立 git 仓库里，作为本地确认版本。

### 4. 检查聊天消息是否会触发扫描

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
- 安装后，`loom_explore` 会由独立 git 仓库跟踪。
- 扫描完成后，先看变更，再执行 `loom confirm <topic>`。
- 扫描完成后，后续 agent 优先读取 `loom_explore`。
- 除非 `loom_explore` 缺失或明显不完整，否则不要优先去看 `loom_raw`。
- 不要读取 `wiki/discard` 里的内容作为正式实现依据。

## 开发说明

相关代码位置：

- [chat.py](/Users/maxiao/Documents/code2/loom/packages/loom_scan/src/loom_scan/chat.py)
- [scanner.py](/Users/maxiao/Documents/code2/loom/packages/loom_scan/src/loom_scan/scanner.py)
- [csv_profile.py](/Users/maxiao/Documents/code2/loom/packages/loom_scan/src/loom_scan/csv_profile.py)
- [datacard.py](/Users/maxiao/Documents/code2/loom/packages/loom_scan/src/loom_scan/datacard.py)
- [cli.py](/Users/maxiao/Documents/code2/loom/packages/loom_scan/src/loom_scan/cli.py)
- [explore_repo.py](/Users/maxiao/Documents/code2/loom/packages/loom_scan/src/loom_scan/explore_repo.py)
- [scripts/loom_scan.py](/Users/maxiao/Documents/code2/loom/scripts/loom_scan.py)
- [scripts/loom.py](/Users/maxiao/Documents/code2/loom/scripts/loom.py)

常用测试命令：

```bash
PYTHONPATH=packages/loom_scan/src python -m unittest discover -s tests
```
