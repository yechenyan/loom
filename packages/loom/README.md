# loom-data

`loom-data` publishes the `loom` Python package and the `loom` CLI.

Loom is designed for large local datasets:

1. Keep raw source files under `raw_data/<workspace>` or any folder with `loom.md`.
2. Scan them into compact cards under `loom/<workspace>`.
3. Let agents search summaries first.
4. Download raw files only when they are actually needed.

## Install

Recommended with `uv`:

```bash
uv add loom-data
```

Then run the CLI with:

```bash
uv run loom --help
```

The package name is `loom-data`, but the Python import and CLI name are both `loom`.

## Initialize a project

```bash
uv run loom init
```

This creates and uses:

```text
loom/
  <workspace>/
  .loom/
raw_data/
  <workspace>/
```

`loom init` asks which assistant you use, which default workspace name you want, and whether to install the tutorial dataset.
It installs the helper skill only for the assistant you choose.
For Codex, Loom writes both `$CODEX_HOME/skills/loom-data` and the workspace-local `.agents/skills/loom-data`.

## Common commands

Scan the default raw-data layout:

```bash
uv run loom scan raw_data/energy
```

Scan a source directory into an explicit workspace:

```bash
uv run loom scan raw_data/energy to energy
```

Confirm one workspace:

```bash
uv run loom confirm energy
```

Confirm all pending explore changes:

```bash
uv run loom confirm
```

Push:

```bash
uv run loom push [workspace]
```

Pull:

```bash
uv run loom pull [workspace]
```

Pull raw files:

```bash
uv run loom pull-raw [workspace]
```

Set the default API endpoint:

```bash
uv run loom set-api https://loom-api-free.onrender.com
```

## Python API

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

`loom.get(...)` prefers local cache and fetches only the file you ask for.

## Workflow recommendation

- Put source data into any directory with `loom.md` and CSV files.
- Run `loom scan <path> [to <workspace>]` to generate cards.
- Read `loom/` first.
- Search the generated cards and summaries.
- Decide which exact raw file is needed.
- Use `loom.get(...)` only for the raw files you really need.
- Or fetch a single file on demand with `loom get energy/technology-data/costs.csv`.
- If a user writes `loom ask <question>` or `loom <question>`, inspect `loom/` first before touching raw files.

If you omit `to <workspace>`, Loom reuses the most recently scanned or created workspace. If there is no history yet, it creates `temporary`. One workspace can track multiple source directories, but dataset paths inside that workspace must stay unique.

Scan state is incremental per workspace and per source directory. Generated cards and manifests store source-relative raw paths such as `technology-data` and `technology-data/costs.csv`, so moving or copying the project does not force a rebuild of unchanged datasets just because the absolute filesystem path changed.

`loom ask <question>` now performs a real local lookup:

```bash
uv run loom ask OCGT cost
uv run loom OCGT cost
```

Loom searches `loom/`, fetches the best matching raw file if needed, and prints matching rows plus a `Likely answer` when the best hit is unambiguous.

## Web app

Explore data online at [https://loom-web.onrender.com](https://loom-web.onrender.com).
