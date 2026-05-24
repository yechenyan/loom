# Task: Client/Server Refactor And Codebase Cleanup

## Original Request

先看下 `wiki/history` 的逻辑。 

只后把 `packages/loom` 分成两部分：
第一部分 cli + package
第二部分 服务

后续补充要求：

- review 下代码，并重新整理和进行重构，包括对项目架构和功能
- 一个文件的代码行数不能超过 200 个
- 不用的文件直接删除
- 把这两个规则写到 `agent.md`
- `agent.md` 中同时增加：`wiki/history` 中的内容只做参考，如果与代码不一致以代码为准

## Completed Work

- 把原本耦合在 `packages/loom` 里的服务端逻辑拆到独立包：
  - `packages/loom-server/src/loom_server`
  - 保留了兼容入口 `loom.sync_server` / `loom.sync_service`
- 把客户端逻辑继续保留在 `packages/loom/src/loom`，并进一步按职责拆分：
  - `cli_app/`
  - `scan_support/`
  - `raw_cache_support/`
  - `sync_ops/`
  - `datacard_parts/`
- 保留原有外部使用方式：
  - `loom` Python API
  - `loom` CLI
  - `loom server-init-db`
  - `loom server-run`
  - 新增独立服务端入口 `scripts/loom-server.py`
- 删除了不用或不应入库的文件：
  - 未使用的 `packages/loom/src/loom/explore_catalog.py`
  - `__pycache__`
  - `loom.egg-info`
  - 被拆分替代的大测试文件
- 把大测试拆成多个小测试文件，并新增共享测试辅助：
  - `tests/support.py`
  - `tests/test_raw_access_cache.py`
  - `tests/test_raw_access_refresh.py`
  - `tests/test_sync_push_pull.py`
  - `tests/test_sync_raw_history.py`
  - `tests/test_sync_rebase.py`
  - `tests/test_sync_conflicts.py`
- 更新了 `agent.md` 规则：
  - 单个代码文件不能超过 200 行
  - 不用的文件直接删除
  - `wiki/history` 只做参考，如与代码不一致，以代码为准
- 清理并校验当前代码文件大小，确保代码文件均不超过 200 行。

## Result

这次重构任务已完成。

当前代码库已经从结构上拆分为：

- 客户端/CLI/包：`packages/loom`
- 服务端：`packages/loom-server`

并且完成了以下目标：

- 降低客户端与服务端耦合
- 让主要实现按职责分层
- 清理未使用和生成文件
- 将大文件拆到 200 行以内
- 保留现有主要功能和兼容入口

## Verification

执行：

```bash
pytest -q
```

结果：

```text
31 passed
```
