# loom-data

`loom-data` publishes the `loom` Python package and the `loom` CLI.

Loom is designed for large local datasets:

1. Keep raw source files under `loom/loom_raw`.
2. Scan them into compact cards under `loom/loom_explore`.
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
uv run loom install
```

This creates and uses:

```text
loom/
  loom_raw/
  loom_explore/
  .loom/
```

It also installs helper skill files for Codex, Claude, Cursor, and Copilot.
For Codex, Loom writes both `$CODEX_HOME/skills/loom-data` and the workspace-local `.agents/skills/loom-data`.

## Common commands

Scan one workspace:

```bash
uv run loom scan energy
```

Scan all workspaces:

```bash
uv run loom scan
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

- Put source data into `loom/loom_raw/<workspace>/`.
- Run `loom scan` to generate cards.
- Read `loom/loom_explore` first.
- Search the generated cards and summaries.
- Decide which exact raw file is needed.
- Use `loom.get(...)` only for the raw files you really need.
- Or fetch a single file on demand with `loom get energy/technology-data/costs.csv`.

## Web app

Explore data online at [https://loom-web.onrender.com](https://loom-web.onrender.com).
