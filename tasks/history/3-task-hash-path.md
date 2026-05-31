# Task: Incremental Scan And Hash-Based Sync

## Original Request

你可以先看下 `tasks/history` 前面的工作，然后继续：

- `loom scan` 不要每次全面扫，只对变更的地方做增量处理
- 记录方式要考虑：
  - 从 workspace 开始的 path
  - 文件 hash
- `push explore` 时也要像 git 一样做增量 push
- `pull` 的时候不需要 pull 到 raw data，只需要 pull explore

后续补充要求：

- scan 的状态记录在 `.loom/state`
- explore 里也要记录 `path + hash`
- 如果某个 csv 或 dataset 没了，不自动删除 explore 产物
- push 时把 raw data 也同步到服务器
- raw data 放对象存储，不做版本化
- raw data 用 hash 判断服务器上是否已有，相同内容跨 path 不重复上传
- 服务器除了存最新的 `raw path -> hash` 映射，也保留历史映射关系

## Completed Work

- Added incremental scan state under `test-project/loom/loom_explore/.loom/state/<topic>-scan.json`.
- Updated scan logic to compare dataset and CSV `path + sha256` manifests and only rebuild changed datasets.
- Added topic-level `scan-manifest.json` and dataset-level `scan_manifest` metadata into `profile.json`.
- Preserved old explore outputs for missing source datasets and marked them as `missing` instead of deleting them.
- Updated CLI scan output to show rebuilt, skipped, and kept-missing datasets.
- Changed explore sync from full snapshot push/pull to incremental delta sync based on `base_revision`, changed files, and deleted paths.
- Changed local pull apply logic from full workspace overwrite to delta application for explore files only.
- Kept pull behavior limited to `loom_explore`; it does not restore `loom_raw` files locally.
- Added raw object sync during push:
  - client computes raw file `path + sha256`
  - client asks server which hashes are missing
  - client uploads only missing raw objects
  - client then updates raw path mappings on the server
- Added content-addressed raw object storage on the server under:
  `storage_root/raw-blobs/<sha256-prefix>/<sha256>`
- Added server-side tables for raw sync:
  - `loom_raw_objects`
  - `loom_workspace_raw_current`
  - `loom_workspace_raw_history`
- Kept latest raw `path -> hash` mappings on the server and also recorded historical mapping changes.
- Updated sync status state to remember both explore and raw synced manifests.
- Added tests for:
  - scan incremental skip behavior
  - keeping missing dataset outputs
  - incremental push/pull for explore
  - raw object dedup upload by hash
  - raw path mapping current state and history persistence
- Restarted the local FastAPI server with the new code and verified a real local end-to-end flow:
  - `scan`
  - `confirm`
  - `push`
  - `pull`

## Result

The task is complete.

Loom now supports:

- incremental scan based on source file path and hash
- incremental explore push/pull
- pull of explore only, without restoring raw data locally
- raw data upload on push via hash-addressed object storage
- latest and historical raw path-to-hash mapping persistence on the server

Verified status:

- `python -m pytest tests`
  passed with 22 tests
- real local server verification against `http://127.0.0.1:8765`
  completed successfully after restarting the server with the updated code
