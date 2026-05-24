# Task 1

## Original Request

你是一个全栈工程师，帮我实现一个功能。
当用户在 codex chat 聊天中输入：
“
loom scan energy
” 后
记住这个是在聊天中输入这个或类似的话，而不是在 bash中输入命令。


能自动扫描 test-project/loom/loom_raw/energy 这个文件夹
然后在 test-project/loom/loom_explore/energy 里生成 类似 huggingface 的 datacard， 这样后续 agent 直接读 loom_explore 下的文件就能知道有哪些数据了，不用去看 loom_raw 的原始数据，这样能节约 token 和加快时间。

对于 csv 文件可以先用脚本或者一些现有的库读取 csv 的摘要，比如列有什么，有多少行， 取前10 行，后 10 行数据后，各列的数据分布情况（数字、字符，有无空等等）， 之后再由 AI agent 分析做后生成出 data card

test-project/loom/loom_raw/energy/technology-data/loom.md 这类 loom.md 文件会识别出当前文件夹下以及子文件夹下是相关的一个数据集

代码可以放在 packages 里面
不要开 wiki/discard 里的文件
对这个你有问题么？

## Completed Work

- Added the `packages/loom_scan` package to parse chat messages like `loom scan energy` and route them into a scan flow.
- Implemented dataset discovery based on `loom.md`, including parent-child dataset boundary handling.
- Implemented CSV profiling with row counts, column lists, head/tail samples, null handling, inferred type counts, numeric stats, and top values.
- Implemented generation of `loom_explore` outputs including topic-level README, dataset overview, CSV cards, and machine-readable profile JSON files.
- Added a fast-path parser for the standard `loom scan <topic>` chat format so it can be recognized without broad repo exploration first.
- Added a local install command and CLI entrypoint:
  `uv run python /Users/maxiao/Documents/code2/loom/scripts/loom_scan.py install`
- Added manual scan and route commands:
  `uv run python /Users/maxiao/Documents/code2/loom/scripts/loom_scan.py scan energy`
  `uv run python /Users/maxiao/Documents/code2/loom/scripts/loom_scan.py route "loom scan energy" --workspace-root /Users/maxiao/Documents/code2/loom`
- Added and updated tests for chat parsing, CSV profiling, scanner behavior, and install flow.
- Documented the project usage in `wiki/manule/readme.md`.

## Result

The task is complete. The Loom scan flow now supports scanning raw topic data into `loom_explore`, and the project includes both install instructions and local command-line entrypoints for the workflow.
