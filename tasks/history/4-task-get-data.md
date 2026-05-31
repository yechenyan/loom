# Task: Raw Data Get And Cache Flow

## Original Request

提供 python package，

使用方法

```python
import loom

data = loom.get("<workspace>/<path>")
```

第一次运行时候：

- 自动把数据下载下来，放到 `.loom/raw` 里
- 如果本地 raw_data 有，就自动建立一个 `.loom` 和 `.raw_data` 的文件 link，不需要从远端下载
- 如果 link 失效再从远端下载

第二次运行的时候，就直接读取缓存。

每次运行 `loom pull` 根据增量检查下 `.loom` 的是不是最新。

同时 cli 也支持用一个命令下载数据。

`.loom/raw` 按原文件路径排列，只下载最新的版本，不下载历史数据。

## Completed Work

- Added the installable `loom` Python package under [packages/loom](/Users/user/Documents/code2/loom/packages/loom).
- Exposed a Python API:
  - `loom.get("workspace/path/to/file")`
  - `loom.pull("workspace")`
- Added CLI support:
  - `loom get energy/technology-data/costs.csv`
  - `loom pull-raw energy`
- Added local raw cache management under:
  `test-project/loom/.loom/raw/<workspace>/...`
- Implemented local-source fast path:
  - first try cache reuse
  - then try linking from `test-project/loom/loom_raw` or `.raw_data`
  - finally fetch from the sync server if the file is still missing
- Kept cache layout aligned to original raw relative paths instead of flattening files.
- Limited downloads to the latest raw manifest only; no historical raw versions are downloaded into `.loom/raw`.
- Added raw cache state tracking under:
  `test-project/loom/.loom/state/raw-<workspace>.json`
- Fixed incremental raw refresh so `loom.pull(...)` / `loom pull-raw ...` now compare remote `path + sha256` entries and refresh changed or deleted cached files instead of only checking file existence.
- Added tests covering:
  - linking an existing local raw file without remote download
  - downloading a missing raw file and reusing cache on the second read
  - pulling a workspace raw cache through the CLI
  - incrementally refreshing changed and deleted raw cache files through `loom.pull(...)`

## Result

The raw data access workflow is complete.

Verified behavior:

- first read can link local raw files or download from the sync server
- repeated reads reuse local `.loom/raw` cache
- `loom.pull(...)` and `loom pull-raw ...` incrementally refresh `.loom/raw`
- cached raw files stay organized by original relative path
- only latest raw files are downloaded; history stays on the server side
